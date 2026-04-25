from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

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
