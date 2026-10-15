"""Main FastAPI application entry point for AI Study Companion.
Configures CORS, standardized error handling, database initialization, and API routes.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import api_router
from backend.config import settings, ensure_storage_dirs
from backend.db.session import init_db, SessionLocal
from backend.dependencies import get_or_create_demo_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # 1. Ensure storage directories exist
    ensure_storage_dirs(settings)

    # 2. Initialize database schema
    init_db()

    # 3. Seed demo student user for instant developer/frontend testing
    db = SessionLocal()
    try:
        get_or_create_demo_user(db)
    finally:
        db.close()

    yield


# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production backend for AI Study Companion — Personalized Tutoring, "
        "Verifiable Source Citations, RAG Learning Studio, and Adaptive Assessments."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS if settings.ALLOWED_CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Standard Error Response Format Middleware & Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTPExceptions to standardized JSON error format."""
    request_id = str(uuid.uuid4())
    error_code = f"HTTP_{exc.status_code}"
    if exc.status_code == 401:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        error_code = "FORBIDDEN"
    elif exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 409:
        error_code = "CONFLICT"
    elif exc.status_code == 413:
        error_code = "FILE_TOO_LARGE"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": exc.detail,
                "details": None,
                "request_id": request_id,
            }
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors to standardized format."""
    request_id = str(uuid.uuid4())
    # Format details safely
    formatted_errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        formatted_errors.append(f"{loc}: {err.get('msg', 'invalid value')}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The incoming request payload failed validation schema checks.",
                "details": formatted_errors,
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler preventing sensitive stack traces from leaking."""
    request_id = str(uuid.uuid4())
    # Log securely server-side without exposing to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please try again later.",
                "details": str(exc) if settings.DEBUG else None,
                "request_id": request_id,
            }
        },
    )


# Mount API V1 Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount Static Files for 3D Character Engine
import os
from fastapi.staticfiles import StaticFiles

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Root Endpoint
@app.get("/")
def root():
    """Root endpoint welcoming API consumers and linking to documentation."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
        "status": "online",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
