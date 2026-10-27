import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from .config import get_settings


def require_admin(
    x_admin_key: Annotated[
        str | None,
        Header(alias="X-Admin-Key"),
    ] = None,
) -> None:
    settings = get_settings()

    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured.",
        )

    if not x_admin_key or not secrets.compare_digest(
        x_admin_key,
        settings.admin_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key.",
        )