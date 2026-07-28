from functools import lru_cache

from supabase import Client, ClientOptions, create_client

from app.config import get_settings


@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    """Return a Supabase client using service role permissions for server writes."""

    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_anon() -> Client:
    """Return an isolated anon client for one server-side auth flow.

    Supabase auth clients keep an in-memory session and start background token
    refresh timers by default. Reusing one cached instance across API requests
    lets concurrent users overwrite each other's session state.
    """

    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
        ),
    )
