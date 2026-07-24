import base64
import datetime as dt
import hashlib
import hmac
import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from urllib import error, request
from xml.etree import ElementTree

from pypdf import PdfReader

from app.config import get_settings


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_OCR_BYTES = 7 * 1024 * 1024
MAX_EXTRACTED_TEXT_LENGTH = 200_000
MAX_ZIP_EXPANDED_BYTES = 50 * 1024 * 1024

SUPPORTED_EXTENSIONS = {"xlsx"}
EXCEL_TEMPLATE_SHEET_NAME = "题目"
EXCEL_TEMPLATE_HEADERS = (
    "exam_code",
    "subject",
    "module",
    "submodule",
    "stem",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "answer",
    "explanation",
    "difficulty",
    "source_type",
    "source_year",
)
MAX_EXCEL_QUESTION_ROWS = 100
XLSX_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_RELATIONSHIPS_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_RELATIONSHIPS_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"


class FileRecognitionError(RuntimeError):
    pass


def recognize_question_file(filename: str, content: bytes) -> dict:
    extension = Path(filename or "").suffix.lower().lstrip(".")
    if extension not in SUPPORTED_EXTENSIONS:
        raise FileRecognitionError("仅支持 .xlsx Excel 题库模板文件")
    if not content:
        raise FileRecognitionError("Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileRecognitionError("File exceeds the 20MB upload limit")

    questions = _extract_xlsx_questions(content, filename)
    warnings: list[str] = []
    if not questions:
        warnings.append("题目工作表中没有可导入的数据行。请从 Excel 第 2 行开始填写题目。")

    return {
        "filename": filename,
        "extension": extension,
        "provider": "xlsx",
        "text": f"已读取 {len(questions)} 道题目",
        "questions": questions,
        "warnings": warnings,
    }


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "big5"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise FileRecognitionError("Unable to decode the text file")


def _validate_zip(content: bytes) -> zipfile.ZipFile:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise FileRecognitionError("The uploaded Office file is invalid") from exc
    expanded_size = sum(item.file_size for item in archive.infolist())
    if expanded_size > MAX_ZIP_EXPANDED_BYTES:
        archive.close()
        raise FileRecognitionError("The expanded Office file is too large")
    return archive


def _extract_docx_text(content: bytes) -> str:
    with _validate_zip(content) as archive:
        try:
            document = archive.read("word/document.xml")
        except KeyError as exc:
            raise FileRecognitionError("DOCX document.xml is missing") from exc

    root = ElementTree.fromstring(document)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    lines: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)).strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def _extract_xlsx_questions(content: bytes, filename: str) -> list[dict]:
    with _validate_zip(content) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        sheet_path = _xlsx_sheet_path(archive, EXCEL_TEMPLATE_SHEET_NAME)
        root = ElementTree.fromstring(archive.read(sheet_path))

    namespace = {"x": XLSX_NAMESPACE}
    rows = root.findall(".//x:sheetData/x:row", namespace)
    if not rows:
        raise FileRecognitionError("Excel 模板缺少表头。请使用“下载模板”获取标准文件。")

    headers = _xlsx_row_values(rows[0], shared_strings)
    headers = [value.replace("\ufeff", "").strip() for value in headers]
    if headers != list(EXCEL_TEMPLATE_HEADERS):
        expected = "、".join(EXCEL_TEMPLATE_HEADERS)
        actual = "、".join(headers) or "（空）"
        raise FileRecognitionError(
            f"Excel 首行字段与模板不一致。请保持字段顺序不变。期望：{expected}；当前：{actual}"
        )

    questions: list[dict] = []
    for offset, row in enumerate(rows[1:], start=2):
        row_number = _xlsx_row_number(row, offset)
        values = _xlsx_row_values(row, shared_strings)
        if len(values) > len(EXCEL_TEMPLATE_HEADERS) and any(values[len(EXCEL_TEMPLATE_HEADERS) :]):
            raise FileRecognitionError(f"Excel 第 {row_number} 行包含模板以外的内容，请删除多余列后重新上传。")
        row_values = (values + [""] * len(EXCEL_TEMPLATE_HEADERS))[: len(EXCEL_TEMPLATE_HEADERS)]
        if not any(value.strip() for value in row_values):
            continue
        question = dict(zip(EXCEL_TEMPLATE_HEADERS, row_values, strict=True))
        question["answer"] = question["answer"].strip().upper()
        question["source_type"] = question["source_type"].strip() or "manual"
        question["source_year"] = question["source_year"].strip() or None
        question["excel_row"] = row_number
        question["image_name"] = Path(filename).name
        question["image_index"] = len(questions)
        questions.append(question)
        if len(questions) > MAX_EXCEL_QUESTION_ROWS:
            raise FileRecognitionError(
                f"单次 Excel 最多导入 {MAX_EXCEL_QUESTION_ROWS} 道题，请拆分文件后重新上传。"
            )
    return questions


def _xlsx_sheet_path(archive: zipfile.ZipFile, sheet_name: str) -> str:
    try:
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    except KeyError as exc:
        raise FileRecognitionError("Excel 文件结构不完整。请使用“下载模板”创建文件。") from exc

    relationship_targets = {
        relationship.attrib.get("Id"): relationship.attrib.get("Target", "")
        for relationship in relationships.findall(f"{{{PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship")
    }
    for sheet in workbook.findall(f".//{{{XLSX_NAMESPACE}}}sheet"):
        if sheet.attrib.get("name") != sheet_name:
            continue
        relationship_id = sheet.attrib.get(f"{{{XLSX_RELATIONSHIPS_NAMESPACE}}}id")
        target = relationship_targets.get(relationship_id, "")
        if not target:
            break
        candidate = PurePosixPath(target.lstrip("/"))
        if not str(candidate).startswith("xl/"):
            candidate = PurePosixPath("xl") / candidate
        if ".." in candidate.parts:
            break
        path = str(candidate)
        if path in archive.namelist():
            return path
        break
    raise FileRecognitionError("Excel 模板缺少“题目”工作表。请使用“下载模板”获取标准文件。")


def _xlsx_row_values(row: ElementTree.Element, shared_strings: list[str]) -> list[str]:
    namespace = {"x": XLSX_NAMESPACE}
    cells: dict[int, str] = {}
    for fallback_index, cell in enumerate(row.findall("x:c", namespace)):
        reference = cell.attrib.get("r", "")
        column_index = _xlsx_column_index(reference) if reference else fallback_index
        cells[column_index] = _xlsx_cell_value(cell, shared_strings)
    if not cells:
        return []
    return [cells.get(index, "") for index in range(max(cells) + 1)]


def _xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    namespace = {"x": XLSX_NAMESPACE}
    cell_type = cell.attrib.get("t", "")
    inline_text = "".join(node.text or "" for node in cell.findall(".//x:is//x:t", namespace))
    if inline_text:
        return inline_text.strip()
    value_node = cell.find("x:v", namespace)
    value = value_node.text if value_node is not None and value_node.text is not None else ""
    if cell_type == "s" and value:
        try:
            value = shared_strings[int(value)]
        except (IndexError, ValueError):
            pass
    return str(value).strip()


def _xlsx_column_index(reference: str) -> int:
    letters = "".join(character for character in reference.upper() if "A" <= character <= "Z")
    if not letters:
        return 0
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    return index - 1


def _xlsx_row_number(row: ElementTree.Element, fallback: int) -> int:
    try:
        return int(row.attrib.get("r", fallback))
    except (TypeError, ValueError):
        return fallback


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        content = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ElementTree.fromstring(content)
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    return [
        "".join(node.text or "" for node in item.findall(".//x:t", namespace))
        for item in root.findall("x:si", namespace)
    ]


def _extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)
    except Exception as exc:
        raise FileRecognitionError("Unable to read the PDF file") from exc


def _has_meaningful_text(text: str) -> bool:
    return len(re.sub(r"\s+", "", text or "")) >= 20


def _normalize_text(text: str) -> str:
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{4,}", "\n\n\n", normalized).strip()
    return normalized[:MAX_EXTRACTED_TEXT_LENGTH]


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def _tencent_general_basic_ocr(content: bytes) -> str:
    settings = get_settings()
    if not settings.tencent_ocr_secret_id or not settings.tencent_ocr_secret_key:
        raise FileRecognitionError(
            "Tencent OCR is not configured. Set TENCENT_OCR_SECRET_ID and TENCENT_OCR_SECRET_KEY."
        )
    if len(content) > MAX_OCR_BYTES:
        raise FileRecognitionError("OCR files must not exceed 7MB")

    service = "ocr"
    host = settings.tencent_ocr_endpoint
    action = "GeneralBasicOCR"
    version = "2018-11-19"
    timestamp = int(dt.datetime.now(tz=dt.timezone.utc).timestamp())
    date = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).strftime("%Y-%m-%d")
    payload = {"ImageBase64": base64.b64encode(content).decode("ascii")}
    payload_text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    canonical_request = "\n".join(
        [
            "POST",
            "/",
            "",
            f"content-type:application/json; charset=utf-8\nhost:{host}\nx-tc-action:{action.lower()}\n",
            "content-type;host;x-tc-action",
            hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
        ]
    )
    credential_scope = f"{date}/{service}/tc3_request"
    string_to_sign = "\n".join(
        [
            "TC3-HMAC-SHA256",
            str(timestamp),
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )
    secret_date = _sign(("TC3" + settings.tencent_ocr_secret_key).encode("utf-8"), date)
    secret_service = _sign(secret_date, service)
    secret_signing = _sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = (
        "TC3-HMAC-SHA256 "
        f"Credential={settings.tencent_ocr_secret_id}/{credential_scope}, "
        "SignedHeaders=content-type;host;x-tc-action, "
        f"Signature={signature}"
    )

    req = request.Request(
        url=f"https://{host}",
        data=payload_text.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": version,
            "X-TC-Region": settings.tencent_ocr_region,
        },
    )
    try:
        with request.urlopen(req, timeout=settings.tencent_ocr_timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise FileRecognitionError(f"Tencent OCR request failed: {detail[:300]}") from exc
    except error.URLError as exc:
        raise FileRecognitionError(f"Tencent OCR is unavailable: {exc.reason}") from exc

    response_data = result.get("Response") or {}
    if response_data.get("Error"):
        error_data = response_data["Error"]
        raise FileRecognitionError(error_data.get("Message") or error_data.get("Code") or "Tencent OCR failed")
    detections = response_data.get("TextDetections") or []
    return "\n".join(str(item.get("DetectedText") or "").strip() for item in detections if item.get("DetectedText"))
