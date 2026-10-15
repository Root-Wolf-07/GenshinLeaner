"""Health and Readiness Check endpoints.
"""

import time
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.session import get_db
from backend.services.llm_provider import get_llm_provider

router = APIRouter(tags=["Health & Status"])
_START_TIME = time.time()


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Basic health check confirming the ASGI application is active."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime_seconds": round(time.time() - _START_TIME, 2),
    }


@router.get("/readiness")
def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Readiness probe reporting dependency status without revealing secrets."""
    # 1. Database check
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # 2. Storage check
    storage_ok = settings.UPLOAD_DIR.exists() and settings.VECTOR_INDEX_DIR.exists()

    # 3. LLM Provider check
    llm_info = get_llm_provider().health_check()

    is_ready = db_ok and storage_ok

    return {
        "ready": is_ready,
        "environment": settings.APP_ENV,
        "dependencies": {
            "database": "connected" if db_ok else "unreachable",
            "storage": "mounted" if storage_ok else "missing",
            "llm_provider": llm_info,
        },
    }
