"""XPTransaction and UserAchievement database models.
Provides transparent, idempotent, non-manipulative learning gamification.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING
from backend.db.compat import (
    String, Integer, Float, Text, JSON, DateTime, ForeignKey, Index, Mapped, mapped_column, relationship
)
from backend.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.user import User


class XPTransaction(Base, TimestampMixin):
    __tablename__ = "xp_transactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # quiz_completed, question_answered, socratic_checkpoint, study_material_created
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(120), unique=True, index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), default="Learning XP Award", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="xp_transactions")

    __table_args__ = (
        Index("idx_xp_user_category", "user_id", "category"),
    )


class UserAchievement(Base, TimestampMixin):
    __tablename__ = "user_achievements"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    achievement_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), default="mastery", nullable=False
    )  # mastery, curiosity, persistence, collaboration
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    achievement_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements")

    __table_args__ = (
        Index("idx_user_achievement_unique", "user_id", "achievement_key", unique=True),
    )
