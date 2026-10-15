"""TopicMastery and learning progress database models.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from backend.db.compat import (
    String, Integer, Float, ForeignKey, DateTime, Index, Mapped, mapped_column, relationship
)
from backend.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.user import User


class TopicMastery(Base, TimestampMixin):
    __tablename__ = "topic_mastery"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    total_questions_attempted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incorrect_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Mastery score is computed as an adaptive weighted estimate (0.0 - 100.0)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(String(50), default="intermediate", nullable=False)

    last_practiced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="topic_masteries")

    __table_args__ = (
        Index("idx_mastery_user_topic", "user_id", "topic", unique=True),
        Index("idx_mastery_user_score", "user_id", "mastery_score"),
    )
