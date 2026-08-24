import base64
import hashlib
import json
import logging
from collections import OrderedDict
from threading import Lock
from time import monotonic, time
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.db import get_supabase_admin
from app.services.supabase_resilience import call_supabase, is_authentication_error


logger = logging.getLogger(__name__)

# A question list request verifies the same access token immediately before a
# learner submits an answer.  Keeping only the successful verification for a
# short window removes a redundant round trip on that critical interaction.
# The cache key is a digest, never the raw bearer token.
_RECENT_AUTH_TTL_SECONDS = 5 * 60.0
_RECENT_AUTH_MAX_ENTRIES = 2048
_recent_auth_users: OrderedDict[str, tuple[str, float]] = OrderedDict()
_recent_auth_lock = Lock()

# Account suspension must also stop an already-issued access token.  A short
# status cache keeps that check inexpensive while still allowing the admin
# endpoint to invalidate the local worker immediately.
_USER_ACCESS_STATUS_TTL_SECONDS = 15.0
_USER_ACCESS_STATUS_MAX_ENTRIES = 4096
_user_access_status: OrderedDict[str, tuple[bool, float]] = OrderedDict()
_user_access_status_lock = Lock()


def _auth_cache_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _access_token_remaining_seconds(token: str) -> float | None:
    """Read JWT expiry only to cap a recently validated cache entry."""

    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        expires_at = float(claims["exp"])
        return max(0.0, expires_at - time())
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _get_recent_authenticated_user(token: str) -> str | None:
    key = _auth_cache_key(token)
    now = monotonic()
    with _recent_auth_lock:
        cached = _recent_auth_users.get(key)
        if not cached:
            return None

        user_id, expires_at = cached
        if expires_at <= now:
            _recent_auth_users.pop(key, None)
            return None

        _recent_auth_users.move_to_end(key)
        return user_id


def _remember_authenticated_user(token: str, user_id: str) -> None:
    key = _auth_cache_key(token)
    token_remaining_seconds = _access_token_remaining_seconds(token)
    ttl_seconds = min(_RECENT_AUTH_TTL_SECONDS, token_remaining_seconds) if token_remaining_seconds is not None else _RECENT_AUTH_TTL_SECONDS
    if ttl_seconds <= 0:
        return

    with _recent_auth_lock:
        _recent_auth_users[key] = (user_id, monotonic() + ttl_seconds)
        _recent_auth_users.move_to_end(key)
        while len(_recent_auth_users) > _RECENT_AUTH_MAX_ENTRIES:
            _recent_auth_users.popitem(last=False)


def _get_cached_user_disabled(user_id: str) -> bool | None:
    now = monotonic()
    with _user_access_status_lock:
        cached = _user_access_status.get(user_id)
        if not cached:
            return None
        disabled, expires_at = cached
        if expires_at <= now:
            _user_access_status.pop(user_id, None)
            return None
        _user_access_status.move_to_end(user_id)
        return disabled


def _remember_user_disabled(user_id: str, disabled: bool) -> None:
    with _user_access_status_lock:
        _user_access_status[user_id] = (
            disabled,
            monotonic() + _USER_ACCESS_STATUS_TTL_SECONDS,
        )
        _user_access_status.move_to_end(user_id)
        while len(_user_access_status) > _USER_ACCESS_STATUS_MAX_ENTRIES:
            _user_access_status.popitem(last=False)


def invalidate_user_access_cache(user_id: str) -> None:
    """Forget cached auth/status entries after an administrator changes access."""

    normalized_user_id = str(user_id or "")
    if not normalized_user_id:
        return
    with _user_access_status_lock:
        _user_access_status.pop(normalized_user_id, None)
    with _recent_auth_lock:
        stale_keys = [
            key
            for key, (cached_user_id, _) in _recent_auth_users.items()
            if cached_user_id == normalized_user_id
        ]
        for key in stale_keys:
            _recent_auth_users.pop(key, None)


def _ensure_user_is_active(user_id: str) -> None:
    disabled = _get_cached_user_disabled(user_id)
    if disabled is None:
        supabase = get_supabase_admin()
        try:
            response = call_supabase(
                lambda: (
                    supabase.table("users")
                    .select("disabled_at")
                    .eq("id", user_id)
                    .limit(1)
                    .execute()
                ),
                operation_name="current-user access status lookup",
            )
        except Exception as exc:
            logger.warning("Current-user access lookup unavailable (error_type=%s)", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User access service temporarily unavailable",
            ) from exc
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
        disabled = bool(response.data[0].get("disabled_at"))
        _remember_user_disabled(user_id, disabled)
    if disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号已停用")


def get_bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return token


def get_current_user_id(token: Annotated[str, Depends(get_bearer_token)]) -> str:
    """Validate Supabase access token and return the auth user id."""

    cached_user_id = _get_recent_authenticated_user(token)
    if cached_user_id:
        _ensure_user_is_active(cached_user_id)
        return cached_user_id

    supabase = get_supabase_admin()
    try:
        user_response = call_supabase(
            lambda: supabase.auth.get_user(token),
            operation_name="access-token validation",
        )
    except Exception as exc:  # Supabase SDK raises provider-specific exceptions.
        if is_authentication_error(exc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
        logger.warning("Access-token validation unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        ) from exc

    user = getattr(user_response, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = str(user.id)
    _ensure_user_is_active(user_id)
    _remember_authenticated_user(token, user_id)
    return user_id


def get_optional_current_user_id(authorization: Annotated[str | None, Header()] = None) -> str | None:
    """Return the current user id when a bearer token exists, otherwise allow public access."""

    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    return get_current_user_id(token)


def get_current_user_profile(user_id: Annotated[str, Depends(get_current_user_id)]) -> dict:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: supabase.table("users").select("*").eq("id", user_id).limit(1).execute(),
            operation_name="current-user profile lookup",
        )
    except Exception as exc:
        logger.warning("Current-user profile lookup unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User profile service temporarily unavailable",
        ) from exc
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return response.data[0]


def is_admin_profile(profile: dict) -> bool:
    role = str(profile.get("role") or "user").strip().lower()
    return role == "admin"


def require_admin_user(profile: Annotated[dict, Depends(get_current_user_profile)]) -> dict:
    if profile.get("disabled_at"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if not is_admin_profile(profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required")
    return profile


def _require_question_portal_access(profile: dict) -> dict:
    supabase = get_supabase_admin()
    try:
        response = call_supabase(
            lambda: (
                supabase.table("question_admin_access")
                .select("user_id")
                .eq("user_id", profile.get("id"))
                .eq("is_active", True)
                .limit(1)
                .execute()
            ),
            operation_name="question-portal permission lookup",
        )
    except Exception as exc:
        logger.warning("Question-portal permission lookup unavailable (error_type=%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Question portal permission service temporarily unavailable",
        ) from exc

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Question portal permission required",
        )
    return profile


def require_question_admin_portal_user(
    profile: Annotated[dict, Depends(get_current_user_profile)],
) -> dict:
    """Allow only users explicitly enabled in the question portal access table."""

    if profile.get("disabled_at"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return _require_question_portal_access(profile)


def require_question_admin_user(
    profile: Annotated[dict, Depends(get_current_user_profile)],
) -> dict:
    """Allow existing admins or users explicitly enabled for the question portal."""

    if profile.get("disabled_at"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    # Keep the existing mobile admin flow working without requiring a migration
    # to be applied before deployment.
    if is_admin_profile(profile):
        return profile

    return _require_question_portal_access(profile)
