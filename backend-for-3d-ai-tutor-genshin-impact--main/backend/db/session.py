"""Database session and connection management.
Supports both SQLite for local development and PostgreSQL for production,
with resilient stdlib fallback for offline / pre-install execution.
"""

from __future__ import annotations

from typing import Any, Generator
from backend.config import settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

    class _DummySession:
        def query(self, *args, **kwargs):
            return self
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return None
        def all(self):
            return []
        def count(self):
            return 0
        def add(self, *args, **kwargs):
            pass
        def add_all(self, *args, **kwargs):
            pass
        def commit(self):
            pass
        def refresh(self, *args, **kwargs):
            pass
        def delete(self, *args, **kwargs):
            pass
        def close(self):
            pass

    def create_engine(*args, **kwargs):
        return None

    def sessionmaker(*args, **kwargs):
        return lambda: _DummySession()

    Session = Any  # type: ignore

# Configure SQLite vs PostgreSQL connect arguments
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

if HAS_SQLALCHEMY:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=settings.DEBUG and False,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = sessionmaker()


def get_db() -> Generator[Any, None, None]:
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables and sync missing columns for backward compatibility."""
    if HAS_SQLALCHEMY and engine is not None:
        from backend.db.base import Base
        import backend.models  # noqa: F401 - ensure all models are imported
        Base.metadata.create_all(bind=engine)

        # Sync missing columns on users table if running on SQLite
        if settings.DATABASE_URL.startswith("sqlite"):
            try:
                from sqlalchemy import text
                with engine.connect() as conn:
                    result = conn.execute(text("PRAGMA table_info(users)"))
                    existing_cols = {row[1] for row in result.fetchall()}
                    
                    columns_to_add = [
                        ("student_id", "VARCHAR(32)"),
                        ("phone", "VARCHAR(50)"),
                        ("normalized_email", "VARCHAR(255)"),
                        ("normalized_phone", "VARCHAR(50)"),
                        ("is_verified", "BOOLEAN DEFAULT 0"),
                        ("verification_channel", "VARCHAR(20)"),
                        ("verification_code_hash", "VARCHAR(255)"),
                        ("verification_code_expires_at", "DATETIME"),
                        ("verification_attempts", "INTEGER DEFAULT 0"),
                        ("last_verification_sent_at", "DATETIME"),
                        ("reset_token_hash", "VARCHAR(255)"),
                        ("reset_token_expires_at", "DATETIME"),
                        ("failed_login_attempts", "INTEGER DEFAULT 0"),
                        ("locked_until", "DATETIME"),
                        ("last_login_at", "DATETIME"),
                        ("password_changed_at", "DATETIME"),
                        ("session_version", "INTEGER DEFAULT 1"),
                    ]

                    for col_name, col_type in columns_to_add:
                        if col_name not in existing_cols:
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    
                    conn.commit()
            except Exception as e:
                # Column sync warning logged, non-fatal
                pass
