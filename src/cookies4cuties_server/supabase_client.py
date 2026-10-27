from functools import lru_cache

from fastapi import HTTPException
from supabase import Client, create_client

from .config import get_settings


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=503,
            detail=("Supabase is not configured. Set SUPABASE_URL and "
                    "SUPABASE_SERVICE_ROLE_KEY in your .env file."),
        )
    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not initialize Supabase.") from exc