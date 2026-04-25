from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    """Return a Supabase client using service role permissions for server writes."""

    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache(maxsize=1)
def get_supabase_anon() -> Client:
    """Return a Supabase client using anon permissions for auth flows."""

    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)
