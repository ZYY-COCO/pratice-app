from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from supabase import Client

from app.config import get_settings
from app.services.auth_codes import CODE_EXPIRE_MINUTES, SEND_COOLDOWN_SECONDS

PHONE_PURPOSES = {"login", "register", "bind_phone"}


def normalize_phone(phone: str) -> str:
    value = re.sub(r"[\s\-()]", "", phone or "")
    if value.startswith("00"):
        value = f"+{value[2:]}"
    if not re.fullmatch(r"\+?\d{8,15}", value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone number")
    return value


def make_phone_email(phone: str) -> str:
    digest = hashlib.sha256(normalize_phone(phone).encode("utf-8")).hexdigest()[:24]
    return f"phone_{digest}@phone.gangyantong.local"


def make_phone_password(phone: str) -> str:
    settings = get_settings()
    secret = settings.phone_auth_password_secret or settings.supabase_service_role_key
    raw = f"{normalize_phone(phone)}:{secret}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_phone_code(phone: str, purpose: str, code: str) -> str:
    raw = f"{normalize_phone(phone)}:{purpose}:{code}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_phone_send_cooldown(supabase: Client, phone: str, purpose: str) -> None:
    normalized_phone = normalize_phone(phone)
    response = (
        supabase.table("auth_phone_codes")
        .select("created_at")
        .eq("phone", normalized_phone)
        .eq("purpose", purpose)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        return

    latest = datetime.fromisoformat(response.data[0]["created_at"].replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - latest
    if delta.total_seconds() < SEND_COOLDOWN_SECONDS:
        wait_seconds = SEND_COOLDOWN_SECONDS - int(delta.total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {wait_seconds} seconds before requesting another code",
        )


def store_phone_code(supabase: Client, phone: str, purpose: str, code: str) -> None:
    normalized_phone = normalize_phone(phone)
    if purpose not in PHONE_PURPOSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone code purpose")

    now_iso = datetime.now(timezone.utc).isoformat()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=CODE_EXPIRE_MINUTES)).isoformat()

    (
        supabase.table("auth_phone_codes")
        .update({"consumed_at": now_iso})
        .eq("phone", normalized_phone)
        .eq("purpose", purpose)
        .is_("consumed_at", "null")
        .execute()
    )

    supabase.table("auth_phone_codes").insert(
        {
            "phone": normalized_phone,
            "purpose": purpose,
            "code_hash": hash_phone_code(normalized_phone, purpose, code),
            "expires_at": expires_at,
        }
    ).execute()


def verify_phone_code_or_raise(supabase: Client, phone: str, purpose: str, code: str) -> None:
    normalized_phone = normalize_phone(phone)
    response = (
        supabase.table("auth_phone_codes")
        .select("id, code_hash, expires_at, consumed_at")
        .eq("phone", normalized_phone)
        .eq("purpose", purpose)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code not found")

    row = response.data[0]
    if row.get("consumed_at"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code already used")

    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")

    expected_hash = hash_phone_code(normalized_phone, purpose, code)
    if expected_hash != row["code_hash"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    (
        supabase.table("auth_phone_codes")
        .update({"consumed_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", row["id"])
        .execute()
    )
