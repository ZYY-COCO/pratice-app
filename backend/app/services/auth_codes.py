from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from supabase import Client

CODE_EXPIRE_MINUTES = 10
SEND_COOLDOWN_SECONDS = 60


def normalize_email(email: str) -> str:
    return email.strip().lower()


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_verification_code(email: str, purpose: str, code: str) -> str:
    raw = f"{normalize_email(email)}:{purpose}:{code}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_send_cooldown(supabase: Client, email: str, purpose: str) -> None:
    response = (
        supabase.table("auth_email_codes")
        .select("created_at")
        .eq("email", normalize_email(email))
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


def store_verification_code(supabase: Client, email: str, purpose: str, code: str) -> None:
    normalized_email = normalize_email(email)
    now_iso = datetime.now(timezone.utc).isoformat()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=CODE_EXPIRE_MINUTES)).isoformat()

    (
        supabase.table("auth_email_codes")
        .update({"consumed_at": now_iso})
        .eq("email", normalized_email)
        .eq("purpose", purpose)
        .is_("consumed_at", "null")
        .execute()
    )

    supabase.table("auth_email_codes").insert(
        {
            "email": normalized_email,
            "purpose": purpose,
            "code_hash": hash_verification_code(normalized_email, purpose, code),
            "expires_at": expires_at,
        }
    ).execute()


def verify_code_or_raise(
    supabase: Client,
    email: str,
    purpose: str,
    code: str,
    *,
    consume: bool = True,
) -> None:
    normalized_email = normalize_email(email)
    response = (
        supabase.table("auth_email_codes")
        .select("id, code_hash, expires_at, consumed_at")
        .eq("email", normalized_email)
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

    expected_hash = hash_verification_code(normalized_email, purpose, code)
    if expected_hash != row["code_hash"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    if consume:
        consume_response = (
            supabase.table("auth_email_codes")
            .update({"consumed_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", row["id"])
            .is_("consumed_at", "null")
            .execute()
        )
        if not consume_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code already used",
            )
