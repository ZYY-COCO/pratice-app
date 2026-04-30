import base64
import hashlib
import hmac
import json
import secrets
import time
from urllib import parse, request

from fastapi import HTTPException, status

from app.config import get_settings

WECHAT_STATE_MAX_AGE_SECONDS = 600


def _secret() -> str:
    settings = get_settings()
    return (
        settings.wechat_auth_password_secret
        or settings.phone_auth_password_secret
        or settings.supabase_service_role_key
    )


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def _state_signature(payload: str) -> str:
    digest = hmac.new(_secret().encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def create_wechat_state() -> str:
    payload = _base64url_encode(
        json.dumps(
            {
                "nonce": secrets.token_urlsafe(16),
                "ts": int(time.time()),
            },
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return f"{payload}.{_state_signature(payload)}"


def verify_wechat_state(state: str | None) -> None:
    if not state or "." not in state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid WeChat state")
    payload, signature = state.rsplit(".", maxsplit=1)
    if not hmac.compare_digest(_state_signature(payload), signature):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid WeChat state")
    try:
        data = json.loads(_base64url_decode(payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid WeChat state") from exc
    ts = int(data.get("ts") or 0)
    if int(time.time()) - ts > WECHAT_STATE_MAX_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WeChat state expired")


def make_wechat_email(openid: str) -> str:
    digest = hashlib.sha256(openid.encode("utf-8")).hexdigest()[:24]
    return f"wechat_{digest}@wechat.gangyantong.local"


def make_wechat_password(openid: str) -> str:
    raw = f"{openid}:{_secret()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_wechat_auth_url(redirect_uri: str) -> tuple[str, str]:
    settings = get_settings()
    if not settings.wechat_oauth_app_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WeChat login is not configured",
        )
    if not redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing WeChat redirect uri")

    state = create_wechat_state()
    query = parse.urlencode(
        {
            "appid": settings.wechat_oauth_app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": settings.wechat_oauth_scope or "snsapi_userinfo",
            "state": state,
        },
        quote_via=parse.quote,
    )
    return f"https://open.weixin.qq.com/connect/oauth2/authorize?{query}#wechat_redirect", state


def _get_json(url: str) -> dict:
    with request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def exchange_wechat_code(code: str, state: str | None = None) -> dict:
    settings = get_settings()
    if not settings.wechat_oauth_app_id or not settings.wechat_oauth_app_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WeChat login is not configured",
        )
    verify_wechat_state(state)
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing WeChat code")

    token_query = parse.urlencode(
        {
            "appid": settings.wechat_oauth_app_id,
            "secret": settings.wechat_oauth_app_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
    )
    token_data = _get_json(f"https://api.weixin.qq.com/sns/oauth2/access_token?{token_query}")
    if token_data.get("errcode"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"WeChat token exchange failed: {token_data.get('errmsg') or token_data.get('errcode')}",
        )

    profile = {
        "openid": token_data.get("openid"),
        "unionid": token_data.get("unionid"),
        "nickname": None,
        "avatar_url": None,
    }
    if not profile["openid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WeChat openid missing")

    scope = str(token_data.get("scope") or "")
    if "snsapi_userinfo" in scope and token_data.get("access_token"):
        userinfo_query = parse.urlencode(
            {
                "access_token": token_data.get("access_token"),
                "openid": profile["openid"],
                "lang": "zh_CN",
            }
        )
        userinfo = _get_json(f"https://api.weixin.qq.com/sns/userinfo?{userinfo_query}")
        if not userinfo.get("errcode"):
            profile["nickname"] = userinfo.get("nickname")
            profile["avatar_url"] = userinfo.get("headimgurl")
            profile["unionid"] = userinfo.get("unionid") or profile["unionid"]

    return profile
