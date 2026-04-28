import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_supabase_admin, get_supabase_anon
from app.dependencies import get_current_user_id
from app.schemas.auth import (
    AuthResponse,
    AuthUser,
    ChangeEmailRequest,
    LoginRequest,
    MessageResponse,
    ProfileUpdateRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendEmailCodeRequest,
)
from app.services.auth_codes import (
    check_send_cooldown,
    generate_verification_code,
    normalize_email,
    store_verification_code,
    verify_code_or_raise,
)
from app.utils.email_sender import send_email_code

router = APIRouter(prefix="/auth", tags=["认证"])
logger = logging.getLogger(__name__)
MEMBERSHIP_FIELDS = (
    "membership_status",
    "membership_plan",
    "membership_started_at",
    "membership_expires_at",
    "membership_updated_at",
)


def _safe_error_summary(exc: Exception) -> str:
    message = getattr(exc, "message", None)
    if isinstance(message, str) and message.strip():
        return message.strip()

    args = getattr(exc, "args", ())
    if args:
        first = args[0]
        if isinstance(first, str) and first.strip():
            return first.strip()
        if isinstance(first, dict):
            for key in ("message", "msg", "error_description", "error"):
                value = first.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    text = str(exc).strip()
    return text or "Unknown auth error"


def _get_profile_by_email(email: str) -> dict | None:
    supabase_admin = get_supabase_admin()
    response = (
        supabase_admin.table("users")
        .select("*")
        .eq("email", normalize_email(email))
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _merge_profile_data(profile: dict, db_profile: dict) -> dict:
    merged = {
        **profile,
        "email": db_profile.get("email") or profile.get("email"),
        "nickname": db_profile.get("nickname") or profile.get("nickname"),
        "avatar_url": db_profile.get("avatar_url") or profile.get("avatar_url"),
        "gender": db_profile.get("gender") or profile.get("gender"),
        "exam_target": db_profile.get("exam_target") or profile.get("exam_target"),
    }
    for field in MEMBERSHIP_FIELDS:
        if field in db_profile:
            merged[field] = db_profile.get(field)
    return merged


def _send_code(email: str, purpose: str) -> None:
    supabase_admin = get_supabase_admin()
    normalized_email = normalize_email(email)
    check_send_cooldown(supabase_admin, normalized_email, purpose)
    code = generate_verification_code()
    store_verification_code(supabase_admin, normalized_email, purpose, code)
    send_email_code(normalized_email, code, purpose)


@router.post("/send-register-code", response_model=MessageResponse)
def send_register_code(payload: SendEmailCodeRequest) -> MessageResponse:
    normalized_email = normalize_email(payload.email)
    if _get_profile_by_email(normalized_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    try:
        _send_code(normalized_email, "register")
    except HTTPException:
        raise
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Send register code failed for email=%s: %s", normalized_email, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Send register code failed: {error_summary}",
        ) from exc

    return MessageResponse(detail="Verification code sent")


@router.post("/send-reset-code", response_model=MessageResponse)
def send_reset_code(payload: SendEmailCodeRequest) -> MessageResponse:
    normalized_email = normalize_email(payload.email)
    if not _get_profile_by_email(normalized_email):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not registered")

    try:
        _send_code(normalized_email, "reset_password")
    except HTTPException:
        raise
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Send reset code failed for email=%s: %s", normalized_email, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Send reset code failed: {error_summary}",
        ) from exc

    return MessageResponse(detail="Reset code sent")


@router.post("/send-change-email-code", response_model=MessageResponse)
def send_change_email_code(
    payload: SendEmailCodeRequest,
    user_id: str = Depends(get_current_user_id),
) -> MessageResponse:
    supabase_admin = get_supabase_admin()
    normalized_email = normalize_email(payload.email)
    profile_response = supabase_admin.table("users").select("email").eq("id", user_id).limit(1).execute()
    current_email = normalize_email(profile_response.data[0]["email"]) if profile_response.data else ""
    if normalized_email == current_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email is the same as current email")
    if _get_profile_by_email(normalized_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    try:
        _send_code(normalized_email, "change_email")
    except HTTPException:
        raise
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Send change email code failed for user_id=%s email=%s: %s", user_id, normalized_email, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Send change email code failed: {error_summary}",
        ) from exc

    return MessageResponse(detail="Change email code sent")


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    supabase_auth = get_supabase_anon()
    supabase_admin = get_supabase_admin()
    normalized_email = normalize_email(payload.email)

    if _get_profile_by_email(normalized_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    verify_code_or_raise(
        supabase=supabase_admin,
        email=normalized_email,
        purpose="register",
        code=payload.verification_code,
    )

    try:
        create_response = supabase_admin.auth.admin.create_user(
            {
                "email": normalized_email,
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": {
                    "nickname": payload.nickname,
                    "exam_target": payload.exam_target,
                },
            }
        )
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Register failed for email=%s: %s", normalized_email, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Register failed: {error_summary}",
        ) from exc

    user = create_response.user
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Register failed")

    profile = {
        "id": user.id,
        "email": normalized_email,
        "nickname": payload.nickname,
        "exam_target": payload.exam_target,
    }
    supabase_admin.table("users").upsert(profile).execute()

    try:
        auth_response = supabase_auth.auth.sign_in_with_password(
            {"email": normalized_email, "password": payload.password}
        )
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Auto login after register failed for email=%s: %s", normalized_email, error_summary)
        return AuthResponse(
            access_token="",
            refresh_token=None,
            user=AuthUser(**profile),
        )

    session = auth_response.session
    return AuthResponse(
        access_token=session.access_token if session else "",
        refresh_token=session.refresh_token if session else None,
        user=AuthUser(**profile),
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest) -> MessageResponse:
    supabase_admin = get_supabase_admin()
    normalized_email = normalize_email(payload.email)
    profile = _get_profile_by_email(normalized_email)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not registered")

    verify_code_or_raise(
        supabase=supabase_admin,
        email=normalized_email,
        purpose="reset_password",
        code=payload.verification_code,
    )

    try:
        supabase_admin.auth.admin.update_user_by_id(
            profile["id"],
            {"password": payload.new_password},
        )
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Reset password failed for email=%s: %s", normalized_email, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reset password failed: {error_summary}",
        ) from exc

    return MessageResponse(detail="Password reset successful")


@router.patch("/profile", response_model=AuthUser)
def update_profile(
    payload: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
) -> AuthUser:
    supabase_admin = get_supabase_admin()
    update_data = {}
    if payload.nickname is not None:
        update_data["nickname"] = payload.nickname.strip() or None
    if payload.avatar_url is not None:
        update_data["avatar_url"] = payload.avatar_url.strip() or None
    if payload.gender is not None:
        update_data["gender"] = payload.gender
    if payload.exam_target is not None:
        update_data["exam_target"] = payload.exam_target

    if not update_data:
        profile_response = supabase_admin.table("users").select("*").eq("id", user_id).limit(1).execute()
        if not profile_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
        return AuthUser(**profile_response.data[0])

    try:
        (
            supabase_admin.table("users")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )
        profile_response = supabase_admin.table("users").select("*").eq("id", user_id).limit(1).execute()
        if not profile_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

        profile = profile_response.data[0]
        supabase_admin.auth.admin.update_user_by_id(
            user_id,
            {
                "user_metadata": {
                    "nickname": profile.get("nickname"),
                    "avatar_url": profile.get("avatar_url"),
                    "gender": profile.get("gender"),
                    "exam_target": profile.get("exam_target"),
                }
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Update profile failed for user_id=%s: %s", user_id, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update profile failed: {error_summary}",
        ) from exc

    return AuthUser(**profile)


@router.post("/change-email", response_model=AuthUser)
def change_email(
    payload: ChangeEmailRequest,
    user_id: str = Depends(get_current_user_id),
) -> AuthUser:
    supabase_admin = get_supabase_admin()
    normalized_email = normalize_email(payload.email)
    profile_response = supabase_admin.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not profile_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    profile = profile_response.data[0]
    current_email = normalize_email(profile.get("email") or "")
    if normalized_email == current_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email is the same as current email")
    if _get_profile_by_email(normalized_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    verify_code_or_raise(
        supabase=supabase_admin,
        email=normalized_email,
        purpose="change_email",
        code=payload.verification_code,
    )

    try:
        supabase_admin.auth.admin.update_user_by_id(
            user_id,
            {
                "email": normalized_email,
                "email_confirm": True,
                "user_metadata": {
                    "nickname": profile.get("nickname"),
                    "avatar_url": profile.get("avatar_url"),
                    "gender": profile.get("gender"),
                    "exam_target": profile.get("exam_target"),
                },
            },
        )
        supabase_admin.table("users").update({"email": normalized_email}).eq("id", user_id).execute()
        updated_response = supabase_admin.table("users").select("*").eq("id", user_id).limit(1).execute()
        if not updated_response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    except HTTPException:
        raise
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Change email failed for user_id=%s email=%s: %s", user_id, normalized_email, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Change email failed: {error_summary}",
        ) from exc

    return AuthUser(**updated_response.data[0])


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    supabase_auth = get_supabase_anon()
    normalized_email = normalize_email(payload.email)

    try:
        auth_response = supabase_auth.auth.sign_in_with_password(
            {"email": normalized_email, "password": payload.password}
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password") from exc

    user = auth_response.user
    session = auth_response.session
    if not user or not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user_metadata = getattr(user, "user_metadata", {}) or {}
    profile = {
        "id": user.id,
        "email": user.email,
        "nickname": user_metadata.get("nickname"),
        "avatar_url": user_metadata.get("avatar_url"),
        "gender": user_metadata.get("gender"),
        "exam_target": user_metadata.get("exam_target"),
        "membership_status": "inactive",
    }

    supabase_admin = get_supabase_admin()
    try:
        profile_response = supabase_admin.table("users").select("*").eq("id", user.id).limit(1).execute()
        if profile_response.data:
            profile = _merge_profile_data(profile, profile_response.data[0])
    except Exception as exc:
        logger.warning("Read profile after login failed for user_id=%s: %s", user.id, _safe_error_summary(exc))

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user=AuthUser(**profile),
    )
