from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import get_settings
from app.db import get_supabase_admin


def get_bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return token


def get_current_user_id(token: Annotated[str, Depends(get_bearer_token)]) -> str:
    """Validate Supabase access token and return the auth user id."""

    supabase = get_supabase_admin()
    try:
        user_response = supabase.auth.get_user(token)
    except Exception as exc:  # Supabase SDK raises provider-specific exceptions.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    user = getattr(user_response, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user.id


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
    response = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return response.data[0]


def is_admin_profile(profile: dict) -> bool:
    settings = get_settings()
    role = str(profile.get("role") or "user").strip().lower()
    email = str(profile.get("email") or "").strip().lower()
    return role == "admin" or email in settings.admin_email_set


def require_admin_user(profile: Annotated[dict, Depends(get_current_user_profile)]) -> dict:
    if profile.get("disabled_at"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    if not is_admin_profile(profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required")
    return profile


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

    supabase = get_supabase_admin()
    try:
        response = (
            supabase.table("question_admin_access")
            .select("user_id")
            .eq("user_id", profile.get("id"))
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Question portal permission storage is not configured",
        ) from exc

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Question portal permission required",
        )
    return profile
