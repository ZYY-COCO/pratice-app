import base64
import datetime as dt
import hashlib
import hmac
import io
import json
import re
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from urllib import error, request
from xml.etree import ElementTree

from pypdf import PdfReader

from app.config import get_settings
from app.services.logic_question_quality import LOGIC_SUBJECT, normalize_logic_classification


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
EXCEL_REQUIRED_HEADERS = (
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
)
EXCEL_HEADER_ALIASES = {
    "exam_code": ("exam_code", "examcode", "考试代码", "试卷代码", "科目代码"),
    "subject": ("subject", "科目", "学科"),
    "module": ("module", "模块", "题型模块"),
    "submodule": ("submodule", "子模块", "考点", "知识点", "细分模块"),
    "stem": ("stem", "题干", "问题", "题目", "题干内容"),
    "option_a": ("option_a", "optiona", "a", "选项a", "选项a项", "a选项"),
    "option_b": ("option_b", "optionb", "b", "选项b", "选项b项", "b选项"),
    "option_c": ("option_c", "optionc", "c", "选项c", "选项c项", "c选项"),
    "option_d": ("option_d", "optiond", "d", "选项d", "选项d项", "d选项"),
    "answer": ("answer", "答案", "正确答案", "答案选项"),
    "explanation": ("explanation", "解析", "答案解析", "题目解析"),
    "difficulty": ("difficulty", "难度", "难度等级"),
    "source_type": ("source_type", "sourcetype", "来源类型", "来源类别"),
    "source_year": ("source_year", "sourceyear", "来源年份", "年份", "真题年份"),
}
MAX_EXCEL_QUESTION_ROWS = 200
MAX_HEADER_SCAN_ROWS = 10
XLSX_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_RELATIONSHIPS_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_RELATIONSHIPS_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"

SUBJECT_ALIASES = {
    "逻辑": "逻辑推理",
    "逻辑推理": "逻辑推理",
    "英文": "英语运用",
    "英语": "英语运用",
}
MODULE_ALIASES = {
    "概念": "概念",
    "判断": "判断",
    "概念判断": "概念判断",
    "推理": "推理",
    "推理规则": "推理",
    "论证": "论证",
    "削弱加强": "论证",
    "加强削弱": "论证",
}
SUBMODULE_ALIASES = {
    "概念": "概念种类",
    "概念种类": "概念种类",
    "概念关系": "概念关系",
    "判断种类": "判断种类",
    "判断关系": "判断关系",
    "定义": "定义",
    "划分": "划分",
    "加强": "加强",
    "加强论证": "加强",
    "支持": "加强",
    "削弱": "削弱",
    "削弱论证": "削弱",
    "质疑": "削弱",
    "反驳": "削弱",
    "假设": "假设",
    "前提": "假设",
    "隐含前提": "假设",
    "必要假设": "假设",
    "解释": "解释",
    "推论": "推论",
    "结论": "推论",
    "论证结构": "论证结构",
    "形式相似": "论证结构",
    "谬误": "谬误识别",
    "谬误识别": "谬误识别",
    "演绎": "演绎推理",
    "演绎推理": "演绎推理",
    "归纳": "归纳推理",
    "归纳推理": "归纳推理",
    "类比": "类比推理",
    "类比推理": "类比推理",
    "综合": "综合推理",
    "综合推理": "综合推理",
}
SOURCE_TYPE_ALIASES = {
    "manual": "manual",
    "手工录入": "manual",
    "手工": "manual",
    "人工": "manual",
    "自编": "manual",
    "source_extracted": "source_extracted",
    "sourceextracted": "source_extracted",
    "资料整理": "source_extracted",
    "抽取": "source_extracted",
    "整理": "source_extracted",
    "real_exam": "real_exam",
    "realexam": "real_exam",
    "真题": "real_exam",
    "历年真题": "real_exam",
}


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

    questions, warnings = _extract_xlsx_questions(content, filename)
    if not questions:
        warnings.append("已识别表头，但没有可导入的数据行。请从表头下一行开始填写题目。")

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


def _extract_xlsx_questions(content: bytes, filename: str) -> tuple[list[dict], list[str]]:
    with _validate_zip(content) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        selection = _xlsx_discover_import_sheet(archive, shared_strings)

    questions: list[dict] = []
    rows: list[ElementTree.Element] = selection["rows"]
    header_index: int = selection["header_index"]
    columns: dict[str, int] = selection["columns"]
    for offset, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        row_number = _xlsx_row_number(row, offset)
        values = _xlsx_row_values(row, shared_strings)
        raw_question = {
            field: values[column] if column < len(values) else ""
            for field, column in columns.items()
        }
        if not any(_clean_excel_cell(value) for value in raw_question.values()):
            continue
        question = _normalize_excel_question(raw_question)
        question["excel_row"] = row_number
        question["image_name"] = Path(filename).name
        question["image_index"] = len(questions)
        questions.append(question)
        if len(questions) > MAX_EXCEL_QUESTION_ROWS:
            raise FileRecognitionError(
                f"单次 Excel 最多导入 {MAX_EXCEL_QUESTION_ROWS} 道题，请拆分文件后重新上传。"
            )
    return questions, _xlsx_recognition_warnings(selection)


def _xlsx_discover_import_sheet(archive: zipfile.ZipFile, shared_strings: list[str]) -> dict:
    candidates: list[dict] = []
    namespace = {"x": XLSX_NAMESPACE}
    for sheet_name, sheet_path in _xlsx_sheet_entries(archive):
        root = ElementTree.fromstring(archive.read(sheet_path))
        rows = root.findall(".//x:sheetData/x:row", namespace)
        header = _xlsx_find_header_row(rows, shared_strings)
        if header is not None:
            candidates.append(
                {
                    "name": sheet_name,
                    "path": sheet_path,
                    "rows": rows,
                    **header,
                }
            )

    if not candidates:
        required = "、".join(EXCEL_REQUIRED_HEADERS)
        raise FileRecognitionError(
            f"未找到可识别的题目表头。请保留题干、A-D 选项、答案、解析等字段。必填字段：{required}"
        )

    candidates.sort(key=lambda item: (item["name"] != EXCEL_TEMPLATE_SHEET_NAME, item["name"]))
    if len(candidates) > 1 and candidates[0]["name"] != EXCEL_TEMPLATE_SHEET_NAME:
        names = "、".join(item["name"] for item in candidates)
        raise FileRecognitionError(
            f"发现多个可识别的题目工作表（{names}）。请仅保留一个，或将目标工作表命名为“{EXCEL_TEMPLATE_SHEET_NAME}”。"
        )
    return candidates[0]


def _xlsx_sheet_entries(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    try:
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    except KeyError as exc:
        raise FileRecognitionError("Excel 文件结构不完整。请使用“下载模板”创建文件。") from exc

    relationship_targets = {
        relationship.attrib.get("Id"): relationship.attrib.get("Target", "")
        for relationship in relationships.findall(f"{{{PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship")
    }
    entries: list[tuple[str, str]] = []
    for sheet in workbook.findall(f".//{{{XLSX_NAMESPACE}}}sheet"):
        sheet_name = _clean_excel_cell(sheet.attrib.get("name", ""))
        relationship_id = sheet.attrib.get(f"{{{XLSX_RELATIONSHIPS_NAMESPACE}}}id")
        target = relationship_targets.get(relationship_id, "")
        if not target:
            raise FileRecognitionError("Excel 工作表关系缺失。请重新另存为 .xlsx 后再上传。")
        candidate = PurePosixPath(target.lstrip("/"))
        if not str(candidate).startswith("xl/"):
            candidate = PurePosixPath("xl") / candidate
        if ".." in candidate.parts:
            raise FileRecognitionError("Excel 工作表路径无效。请重新另存为 .xlsx 后再上传。")
        path = str(candidate)
        if path in archive.namelist():
            entries.append((sheet_name, path))
    if not entries:
        raise FileRecognitionError("Excel 中没有可读取的工作表。请重新另存为 .xlsx 后再上传。")
    return entries


def _xlsx_find_header_row(rows: list[ElementTree.Element], shared_strings: list[str]) -> dict | None:
    for header_index, row in enumerate(rows[:MAX_HEADER_SCAN_ROWS]):
        mapping = _xlsx_header_mapping(_xlsx_row_values(row, shared_strings))
        if not mapping["missing_required"]:
            if mapping["duplicate_fields"]:
                fields = "、".join(sorted(set(mapping["duplicate_fields"])))
                raise FileRecognitionError(f"Excel 表头存在重复字段：{fields}。请保留其中一列。")
            return {
                "header_index": header_index,
                "columns": mapping["columns"],
                "aliases": mapping["aliases"],
                "ignored_headers": mapping["ignored_headers"],
            }
    return None


def _xlsx_header_mapping(headers: list[str]) -> dict:
    columns: dict[str, int] = {}
    aliases: list[str] = []
    ignored_headers: list[str] = []
    duplicate_fields: list[str] = []
    for index, header in enumerate(headers):
        label = _clean_excel_cell(header)
        if not label:
            continue
        field = _canonical_excel_header(label)
        if not field:
            ignored_headers.append(label)
            continue
        if field in columns:
            duplicate_fields.append(field)
            continue
        columns[field] = index
        if _normalize_excel_header(label) != _normalize_excel_header(field):
            aliases.append(label)
    return {
        "columns": columns,
        "aliases": aliases,
        "ignored_headers": ignored_headers,
        "duplicate_fields": duplicate_fields,
        "missing_required": [field for field in EXCEL_REQUIRED_HEADERS if field not in columns],
    }


def _canonical_excel_header(label: str) -> str | None:
    normalized = _normalize_excel_header(label)
    for field, aliases in EXCEL_HEADER_ALIASES.items():
        if any(normalized == _normalize_excel_header(alias) for alias in aliases):
            return field
    return None


def _xlsx_recognition_warnings(selection: dict) -> list[str]:
    warnings: list[str] = []
    if selection["name"] != EXCEL_TEMPLATE_SHEET_NAME:
        warnings.append(
            f"已从工作表“{selection['name']}”识别题目。建议后续统一命名为“{EXCEL_TEMPLATE_SHEET_NAME}”。"
        )
    if selection["header_index"] > 0:
        warnings.append(
            f"已自动跳过前 {selection['header_index']} 行说明文字，从第 {selection['header_index'] + 1} 行识别表头。"
        )
    if selection["aliases"]:
        warnings.append("已兼容中文或别名表头，并自动转换为系统字段。")
    if selection["ignored_headers"]:
        warnings.append(f"已忽略 {len(selection['ignored_headers'])} 个备注/辅助列。")
    return warnings


def _normalize_excel_question(raw_question: dict[str, str]) -> dict:
    question = {field: _clean_excel_cell(raw_question.get(field, "")) for field in EXCEL_TEMPLATE_HEADERS}
    question["exam_code"] = question["exam_code"].upper()
    question["subject"] = _normalize_catalog_value(question["subject"], SUBJECT_ALIASES)
    question["module"] = _normalize_catalog_value(question["module"], MODULE_ALIASES)
    question["submodule"] = _normalize_catalog_value(question["submodule"], SUBMODULE_ALIASES)
    if question["subject"] == LOGIC_SUBJECT:
        question["module"], question["submodule"] = normalize_logic_classification(
            question["module"], question["submodule"]
        )
    question["option_a"] = _normalize_option(question["option_a"], "A")
    question["option_b"] = _normalize_option(question["option_b"], "B")
    question["option_c"] = _normalize_option(question["option_c"], "C")
    question["option_d"] = _normalize_option(question["option_d"], "D")
    question["answer"] = _normalize_answer(question["answer"])
    question["difficulty"] = _normalize_difficulty(question["difficulty"])
    question["source_type"] = _normalize_source_type(question["source_type"])
    question["source_year"] = question["source_year"] or None
    return question


def _normalize_catalog_value(value: str, aliases: dict[str, str]) -> str:
    normalized = _normalize_excel_header(value)
    for alias, canonical in aliases.items():
        if normalized == _normalize_excel_header(alias):
            return canonical
    return _clean_excel_cell(value)


def _normalize_answer(value: str) -> str:
    cleaned = _clean_excel_cell(value)
    match = re.fullmatch(r"(?:(?:正确)?答案|answer|选项)?\s*[:：]?\s*([A-D])(?:\s*项)?[.、。)）]?\s*", cleaned, re.I)
    return match.group(1).upper() if match else cleaned.upper()


def _normalize_option(value: str, option_letter: str) -> str:
    cleaned = _clean_excel_cell(value)
    return re.sub(rf"^(?:选项\s*)?{option_letter}\s*(?:[.、。:：）)])\s*", "", cleaned, flags=re.I)


def _normalize_difficulty(value: str) -> int | str:
    cleaned = _clean_excel_cell(value)
    if not cleaned:
        return 2
    mapping = {"简单": 1, "易": 1, "easy": 1, "中等": 2, "适中": 2, "medium": 2, "困难": 3, "难": 3, "hard": 3}
    if cleaned.lower() in mapping:
        return mapping[cleaned.lower()]
    try:
        numeric = float(cleaned)
    except ValueError:
        return cleaned
    return int(numeric) if numeric.is_integer() else cleaned


def _normalize_source_type(value: str) -> str:
    cleaned = _clean_excel_cell(value)
    return _normalize_catalog_value(cleaned, SOURCE_TYPE_ALIASES) or "manual"


def _normalize_excel_header(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", _clean_excel_cell(value)).lower()
    return re.sub(r"[\s_—–\-:：()（）\[\]【】.。]", "", normalized)


def _clean_excel_cell(value: object) -> str:
    return str(value or "").replace("\ufeff", "", 1).replace("\r\n", "\n").strip()


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
