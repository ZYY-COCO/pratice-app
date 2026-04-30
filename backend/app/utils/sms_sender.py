import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


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

    raise RuntimeError("SMS provider is not configured")
