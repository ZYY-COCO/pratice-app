import base64
import datetime as dt
import hashlib
import hmac
import io
import json
import re
import zipfile
from pathlib import Path
from urllib import error, request
from xml.etree import ElementTree

from pypdf import PdfReader

from app.config import get_settings


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_OCR_BYTES = 7 * 1024 * 1024
MAX_EXTRACTED_TEXT_LENGTH = 200_000
MAX_ZIP_EXPANDED_BYTES = 50 * 1024 * 1024

TEXT_EXTENSIONS = {"txt", "csv", "json"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS | {"pdf", "docx", "xlsx"}


class FileRecognitionError(RuntimeError):
    pass


def recognize_question_file(filename: str, content: bytes) -> dict:
    extension = Path(filename or "").suffix.lower().lstrip(".")
    if extension not in SUPPORTED_EXTENSIONS:
        raise FileRecognitionError(f"Unsupported file type: {extension or 'unknown'}")
    if not content:
        raise FileRecognitionError("Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileRecognitionError("File exceeds the 20MB upload limit")

    warnings: list[str] = []
    if extension in TEXT_EXTENSIONS:
        text = _decode_text(content)
        provider = "text"
    elif extension == "docx":
        text = _extract_docx_text(content)
        provider = "docx"
    elif extension == "xlsx":
        text = _extract_xlsx_text(content)
        provider = "xlsx"
    elif extension == "pdf":
        text = _extract_pdf_text(content)
        provider = "pdf"
        if not _has_meaningful_text(text):
            text = _tencent_general_basic_ocr(content)
            provider = "tencent_ocr"
            warnings.append("PDF did not contain extractable text, so OCR was used.")
    else:
        text = _tencent_general_basic_ocr(content)
        provider = "tencent_ocr"

    text = _normalize_text(text)
    if not text:
        warnings.append("No readable text was found in the uploaded file.")

    return {
        "filename": filename,
        "extension": extension,
        "provider": provider,
        "text": text,
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


def _extract_xlsx_text(content: bytes) -> str:
    with _validate_zip(content) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        sheet_names = sorted(
            name for name in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name)
        )
        rows: list[str] = []
        namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for sheet_name in sheet_names:
            root = ElementTree.fromstring(archive.read(sheet_name))
            for row in root.findall(".//x:row", namespace):
                values: list[str] = []
                for cell in row.findall("x:c", namespace):
                    cell_type = cell.attrib.get("t", "")
                    value_node = cell.find("x:v", namespace)
                    inline_nodes = cell.findall(".//x:is/x:t", namespace)
                    value = "".join(node.text or "" for node in inline_nodes)
                    if value_node is not None and value_node.text is not None:
                        value = value_node.text
                        if cell_type == "s":
                            try:
                                value = shared_strings[int(value)]
                            except (IndexError, ValueError):
                                pass
                    values.append(value.strip())
                if any(values):
                    rows.append("\t".join(values))
    return "\n".join(rows)


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
