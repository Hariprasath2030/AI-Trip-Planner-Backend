from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    settings = get_settings()
    settings.validate()
    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
    )


def get_user_client(access_token: str) -> Client:
    """A fresh client acting as the signed-in user (RLS applies)."""
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client
