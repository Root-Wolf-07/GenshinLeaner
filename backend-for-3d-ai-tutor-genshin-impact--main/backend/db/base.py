"""Database declarative base configuration for SQLAlchemy 2.x with zero-dependency fallback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    from sqlalchemy import DateTime
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

    class DeclarativeBase:
        metadata = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class _MappedIndexer:
        def __getitem__(self, item):
            return Any

    Mapped = _MappedIndexer()

    def mapped_column(*args, **kwargs):
        default = kwargs.get("default")
        if callable(default):
            try:
                return default()
            except Exception:
                return None
        return default

    def DateTime(*args, **kwargs):
        return None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps to models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
