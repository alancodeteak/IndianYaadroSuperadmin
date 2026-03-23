from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text
from starlette import status

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.core.config import get_settings
from app.infrastructure.db.session import SessionLocal

router = APIRouter(tags=["internal"])


@router.get("/health")
async def health() -> dict:
    # Keep consistent contract even for internal endpoints.
    return {"data": {"status": "ok"}, "meta": None}


@router.get("/health/live")
async def health_live() -> dict:
    return {"data": {"status": "alive"}, "meta": None}


@router.get("/health/ready")
async def health_ready() -> dict:
    checks = {"database": _check_database()}
    ready = all(checks.values())
    return {
        "data": {"status": "ready" if ready else "not_ready", "checks": checks},
        "meta": None,
    }


@router.get("/health/full")
async def health_full() -> dict:
    settings = get_settings()
    env = settings.ENVIRONMENT.lower()
    is_prod = env in {"production", "prod"}
    if is_prod and not settings.ENABLE_DETAILED_HEALTH:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Detailed health endpoint is disabled",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    disk = shutil.disk_usage("/")
    checks = {
        "database": _check_database(),
        "redis_configured": bool(settings.REDIS_URL),
        "system": {
            "utc_time": datetime.now(timezone.utc).isoformat(),
            "disk_total_bytes": disk.total,
            "disk_free_bytes": disk.free,
            "disk_used_bytes": disk.used,
            "pid": os.getpid(),
        },
    }

    return {"data": {"status": "ok", "checks": checks}, "meta": None}


def _check_database() -> bool:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

