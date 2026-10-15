"""Database compatibility layer providing graceful fallback for SQLAlchemy types and decorators.
"""

from __future__ import annotations

from typing import Any

try:
    from sqlalchemy import (
        String,
        Integer,
        Float,
        Text,
        JSON,
        ForeignKey,
        Index,
        DateTime,
        Boolean,
    )
    from sqlalchemy.orm import Mapped, mapped_column, relationship
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

    def relationship(*args, **kwargs):
        return []

    def Index(*args, **kwargs):
        return None

    def ForeignKey(*args, **kwargs):
        return None

    def _type_stub(*args, **kwargs):
        return None

    String = _type_stub
    Integer = _type_stub
    Float = _type_stub
    Text = _type_stub
    JSON = _type_stub
    DateTime = _type_stub
    Boolean = _type_stub

    from backend.db.base import Mapped, mapped_column
