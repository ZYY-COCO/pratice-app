import datetime as dt
import hashlib
import hmac
import json
import logging
from urllib import request

from app.config import get_settings
from app.services.auth_codes import CODE_EXPIRE_MINUTES

logger = logging.getLogger(__name__)


def _format_sms_phone(phone: str) -> str:
    value = (phone or "").strip()
    if value.startswith("+"):
        return value
    if value.startswith("00"):
        return f"+{value[2:]}"
    if len(value) == 11 and value.startswith("1"):
        return f"+86{value}"
    raise RuntimeError("Phone number must include country code")


def _build_template_params(code: str) -> list[str]:
    settings = get_settings()
    params: list[str] = []
    for item in (settings.tencent_sms_template_params or "code").split(","):
        key = item.strip().lower()
        if key == "code":
            params.append(code)
        elif key in {"minute", "minutes", "ttl"}:
            params.append(str(CODE_EXPIRE_MINUTES))
    return params or [code]


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def _send_tencent_sms(phone: str, code: str) -> None:
    settings = get_settings()
    required = {
        "TENCENT_SMS_SECRET_ID": settings.tencent_sms_secret_id,
        "TENCENT_SMS_SECRET_KEY": settings.tencent_sms_secret_key,
        "TENCENT_SMS_SDK_APP_ID": settings.tencent_sms_sdk_app_id,
        "TENCENT_SMS_SIGN_NAME": settings.tencent_sms_sign_name,
        "TENCENT_SMS_TEMPLATE_ID": settings.tencent_sms_template_id,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Tencent SMS is not configured: {', '.join(missing)}")

    service = "sms"
    host = settings.tencent_sms_endpoint
    action = "SendSms"
    version = "2021-01-11"
    region = settings.tencent_sms_region
    timestamp = int(dt.datetime.now(tz=dt.timezone.utc).timestamp())
    date = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).strftime("%Y-%m-%d")
    payload = {
        "PhoneNumberSet": [_format_sms_phone(phone)],
        "SmsSdkAppId": settings.tencent_sms_sdk_app_id,
        "SignName": settings.tencent_sms_sign_name,
        "TemplateId": settings.tencent_sms_template_id,
        "TemplateParamSet": _build_template_params(code),
    }
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
    secret_date = _sign(("TC3" + settings.tencent_sms_secret_key).encode("utf-8"), date)
    secret_service = _sign(secret_date, service)
    secret_signing = _sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = (
        "TC3-HMAC-SHA256 "
        f"Credential={settings.tencent_sms_secret_id}/{credential_scope}, "
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
            "X-TC-Region": region,
        },
    )
    with request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))

    send_status = (result.get("Response") or {}).get("SendStatusSet") or []
    if not send_status:
        raise RuntimeError(f"Tencent SMS returned empty status: {result}")
    first_status = send_status[0]
    if first_status.get("Code") != "Ok":
        raise RuntimeError(first_status.get("Message") or first_status.get("Code") or "Tencent SMS failed")


def send_sms_code(phone: str, code: str, purpose: str) -> str | None:
    """Send a phone verification code.

    Real SMS providers should be wired here. For local/internal testing, set
    SMS_PROVIDER=mock and optionally SMS_MOCK_RETURN_CODE=true.
    """

    settings = get_settings()
    provider = (settings.sms_provider or "disabled").strip().lower()

    if provider == "mock":
        logger.warning("Mock SMS code for phone=%s purpose=%s code=%s", phone, purpose, code)
        return code if settings.sms_mock_return_code else None

    if provider == "tencent":
        _send_tencent_sms(phone, code)
        return None

    raise RuntimeError("SMS provider is not configured")
