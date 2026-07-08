import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_supabase_admin, get_supabase_anon
from app.dependencies import get_current_user_id
from app.schemas.auth import (
    AuthResponse,
    AuthUser,
    ChangeEmailRequest,
    LoginRequest,
    MessageResponse,
    PhoneCodeResponse,
    PhoneLoginRequest,
    PhoneRegisterRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendEmailCodeRequest,
    SendPhoneCodeRequest,
    WechatAuthUrlResponse,
    WechatLoginRequest,
)
from app.services.auth_codes import (
    check_send_cooldown,
    generate_verification_code,
    normalize_email,
    store_verification_code,
    verify_code_or_raise,
)
from app.services.phone_auth import (
    check_phone_send_cooldown,
    make_phone_email,
    make_phone_password,
    normalize_phone,
    store_phone_code,
    verify_phone_code_or_raise,
)
from app.services.wechat_auth import (
    build_wechat_auth_url,
    exchange_wechat_code,
    make_wechat_email,
    make_wechat_password,
)
from app.utils.email_sender import send_email_code
from app.utils.sms_sender import send_sms_code

router = APIRouter(prefix="/auth", tags=["认证"])
logger = logging.getLogger(__name__)
MEMBERSHIP_FIELDS = (
    "membership_status",
    "membership_plan",
    "membership_started_at",
    "membership_expires_at",
    "membership_updated_at",
)
PROFILE_ADMIN_FIELDS = ("role", "disabled_at")
FREE_MEMBERSHIP_EXPIRES_AT = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
FREE_MEMBERSHIP_PLAN = "free_until_2099"


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


def _get_profile_by_phone(phone: str) -> dict | None:
    supabase_admin = get_supabase_admin()
    response = (
        supabase_admin.table("users")
        .select("*")
        .eq("phone", normalize_phone(phone))
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _get_profile_by_wechat_openid(openid: str) -> dict | None:
    supabase_admin = get_supabase_admin()
    response = (
        supabase_admin.table("users")
        .select("*")
        .eq("wechat_openid", openid)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _merge_profile_data(profile: dict, db_profile: dict) -> dict:
    merged = {
        **profile,
        "email": db_profile.get("email") or profile.get("email"),
        "phone": db_profile.get("phone") or profile.get("phone"),
        "auth_provider": db_profile.get("auth_provider") or profile.get("auth_provider"),
        "wechat_openid": db_profile.get("wechat_openid") or profile.get("wechat_openid"),
        "nickname": db_profile.get("nickname") or profile.get("nickname"),
        "avatar_url": db_profile.get("avatar_url") or profile.get("avatar_url"),
        "gender": db_profile.get("gender") or profile.get("gender"),
        "exam_target": db_profile.get("exam_target") or profile.get("exam_target"),
    }
    for field in MEMBERSHIP_FIELDS:
        if field in db_profile:
            merged[field] = db_profile.get(field)
    for field in PROFILE_ADMIN_FIELDS:
        if field in db_profile:
            merged[field] = db_profile.get(field)
    return merged


def _new_user_trial_membership_fields() -> dict:
    current = datetime.now(timezone.utc)
    return {
        "membership_status": "active",
        "membership_plan": FREE_MEMBERSHIP_PLAN,
        "membership_started_at": current.isoformat(),
        "membership_expires_at": FREE_MEMBERSHIP_EXPIRES_AT.isoformat(),
        "membership_updated_at": current.isoformat(),
    }


def _send_code(email: str, purpose: str) -> None:
    supabase_admin = get_supabase_admin()
    normalized_email = normalize_email(email)
    check_send_cooldown(supabase_admin, normalized_email, purpose)
    code = generate_verification_code()
    store_verification_code(supabase_admin, normalized_email, purpose, code)
    send_email_code(normalized_email, code, purpose)


def _send_phone_code(phone: str, purpose: str) -> str | None:
    supabase_admin = get_supabase_admin()
    normalized_phone = normalize_phone(phone)
    check_phone_send_cooldown(supabase_admin, normalized_phone, purpose)
    code = generate_verification_code()
    store_phone_code(supabase_admin, normalized_phone, purpose, code)
    return send_sms_code(normalized_phone, code, purpose)


def _auth_response_from_profile(profile: dict, password: str) -> AuthResponse:
    supabase_auth = get_supabase_anon()
    try:
        auth_response = supabase_auth.auth.sign_in_with_password(
            {"email": profile["email"], "password": password}
        )
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Phone auth sign in failed for user_id=%s: %s", profile.get("id"), error_summary)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Phone login failed: {error_summary}",
        ) from exc

    session = auth_response.session
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phone login failed")

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user=AuthUser(**profile),
    )


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


@router.post("/send-phone-code", response_model=PhoneCodeResponse)
def send_phone_code(payload: SendPhoneCodeRequest) -> PhoneCodeResponse:
    normalized_phone = normalize_phone(payload.phone)
    profile = _get_profile_by_phone(normalized_phone)
    if payload.purpose == "register" and profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already registered")
    if payload.purpose == "login" and not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone not registered")

    try:
        debug_code = _send_phone_code(normalized_phone, payload.purpose)
    except HTTPException:
        raise
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Send phone code failed for phone=%s: %s", normalized_phone, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Send phone code failed: {error_summary}",
        ) from exc

    return PhoneCodeResponse(detail="Phone verification code sent", debug_code=debug_code)


@router.get("/wechat-auth-url", response_model=WechatAuthUrlResponse)
def wechat_auth_url(
    redirect_uri: str = Query(min_length=8),
) -> WechatAuthUrlResponse:
    auth_url, state = build_wechat_auth_url(redirect_uri)
    return WechatAuthUrlResponse(auth_url=auth_url, state=state)


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


@router.post("/phone-register", response_model=AuthResponse)
def phone_register(payload: PhoneRegisterRequest) -> AuthResponse:
    supabase_admin = get_supabase_admin()
    normalized_phone = normalize_phone(payload.phone)

    if _get_profile_by_phone(normalized_phone):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already registered")

    verify_phone_code_or_raise(
        supabase=supabase_admin,
        phone=normalized_phone,
        purpose="register",
        code=payload.verification_code,
    )

    phone_email = make_phone_email(normalized_phone)
    phone_password = make_phone_password(normalized_phone)
    try:
        create_response = supabase_admin.auth.admin.create_user(
            {
                "email": phone_email,
                "password": phone_password,
                "email_confirm": True,
                "user_metadata": {
                    "phone": normalized_phone,
                    "nickname": payload.nickname,
                    "exam_target": payload.exam_target,
                    "auth_provider": "phone",
                },
            }
        )
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Phone register failed for phone=%s: %s", normalized_phone, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phone register failed: {error_summary}",
        ) from exc

    user = create_response.user
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone register failed")

    profile = {
        "id": user.id,
        "email": phone_email,
        "phone": normalized_phone,
        "auth_provider": "phone",
        "nickname": payload.nickname,
        "exam_target": payload.exam_target,
        **_new_user_trial_membership_fields(),
    }
    supabase_admin.table("users").upsert(profile).execute()
    return _auth_response_from_profile(profile, phone_password)


@router.post("/phone-login", response_model=AuthResponse)
def phone_login(payload: PhoneLoginRequest) -> AuthResponse:
    supabase_admin = get_supabase_admin()
    normalized_phone = normalize_phone(payload.phone)
    profile = _get_profile_by_phone(normalized_phone)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone not registered")

    verify_phone_code_or_raise(
        supabase=supabase_admin,
        phone=normalized_phone,
        purpose="login",
        code=payload.verification_code,
    )

    phone_password = make_phone_password(normalized_phone)
    try:
        supabase_admin.auth.admin.update_user_by_id(
            profile["id"],
            {
                "password": phone_password,
                "user_metadata": {
                    "phone": normalized_phone,
                    "nickname": profile.get("nickname"),
                    "avatar_url": profile.get("avatar_url"),
                    "gender": profile.get("gender"),
                    "exam_target": profile.get("exam_target"),
                    "auth_provider": profile.get("auth_provider") or "phone",
                },
            },
        )
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Phone login password refresh failed for phone=%s: %s", normalized_phone, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phone login failed: {error_summary}",
        ) from exc

    return _auth_response_from_profile(profile, phone_password)


@router.post("/wechat-login", response_model=AuthResponse)
def wechat_login(payload: WechatLoginRequest) -> AuthResponse:
    supabase_admin = get_supabase_admin()
    wechat_profile = exchange_wechat_code(payload.code or "", payload.state)
    openid = wechat_profile["openid"]
    profile = _get_profile_by_wechat_openid(openid)
    password = make_wechat_password(openid)

    if profile:
        profile_updates = {}
        if not profile.get("nickname") and wechat_profile.get("nickname"):
            profile_updates["nickname"] = wechat_profile.get("nickname")
        if not profile.get("avatar_url") and wechat_profile.get("avatar_url"):
            profile_updates["avatar_url"] = wechat_profile.get("avatar_url")
        if profile.get("auth_provider") != "wechat":
            profile_updates["auth_provider"] = "wechat"
        if profile_updates:
            supabase_admin.table("users").update(profile_updates).eq("id", profile["id"]).execute()
            profile.update(profile_updates)

        try:
            supabase_admin.auth.admin.update_user_by_id(
                profile["id"],
                {
                    "password": password,
                    "user_metadata": {
                        "wechat_openid": openid,
                        "nickname": profile.get("nickname") or wechat_profile.get("nickname"),
                        "avatar_url": profile.get("avatar_url") or wechat_profile.get("avatar_url"),
                        "exam_target": profile.get("exam_target"),
                        "auth_provider": "wechat",
                    },
                },
            )
        except Exception as exc:
            error_summary = _safe_error_summary(exc)
            logger.exception("WeChat login password refresh failed for openid=%s: %s", openid, error_summary)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"WeChat login failed: {error_summary}",
            ) from exc
        return _auth_response_from_profile(profile, password)

    wechat_email = make_wechat_email(openid)
    nickname = wechat_profile.get("nickname") or "微信用户"
    try:
        create_response = supabase_admin.auth.admin.create_user(
            {
                "email": wechat_email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "wechat_openid": openid,
                    "nickname": nickname,
                    "avatar_url": wechat_profile.get("avatar_url"),
                    "exam_target": "Z001",
                    "auth_provider": "wechat",
                },
            }
        )
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("WeChat register failed for openid=%s: %s", openid, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"WeChat login failed: {error_summary}",
        ) from exc

    user = create_response.user
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WeChat login failed")

    profile = {
        "id": user.id,
        "email": wechat_email,
        "auth_provider": "wechat",
        "wechat_openid": openid,
        "nickname": nickname,
        "avatar_url": wechat_profile.get("avatar_url"),
        "exam_target": "Z001",
        **_new_user_trial_membership_fields(),
    }
    supabase_admin.table("users").upsert(profile).execute()
    return _auth_response_from_profile(profile, password)


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
        **_new_user_trial_membership_fields(),
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


@router.delete("/account", response_model=MessageResponse)
def delete_account(user_id: str = Depends(get_current_user_id)) -> MessageResponse:
    supabase_admin = get_supabase_admin()
    profile_response = supabase_admin.table("users").select("id").eq("id", user_id).limit(1).execute()
    if not profile_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

    delete_user = getattr(supabase_admin.auth.admin, "delete_user", None)
    if not callable(delete_user):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Account deletion is not available")

    try:
        delete_user(user_id)
    except Exception as exc:
        error_summary = _safe_error_summary(exc)
        logger.exception("Delete auth account failed for user_id=%s: %s", user_id, error_summary)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delete account failed: {error_summary}",
        ) from exc

    try:
        supabase_admin.table("users").delete().eq("id", user_id).execute()
    except Exception as exc:
        logger.warning("Delete public user cleanup skipped for user_id=%s: %s", user_id, _safe_error_summary(exc))

    return MessageResponse(detail="Account deleted")


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
