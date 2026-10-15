"""Quiz and QuizAttempt database models.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from backend.db.compat import (
    String, Integer, Float, JSON, ForeignKey, DateTime, Index, Mapped, mapped_column, relationship
)
from backend.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.user import User


class Quiz(Base, TimestampMixin):
    __tablename__ = "quizzes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="intermediate", nullable=False)
    student_level: Mapped[str] = mapped_column(String(50), default="undergraduate", nullable=False)
    source_mode: Mapped[str] = mapped_column(String(50), default="both", nullable=False)
    document_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # List of Question objects:
    # [{
    #   "id": "q_1",
    #   "prompt": "What is...",
    #   "question_type": "multiple_choice"|"true_false"|"short_answer"|"fill_in_the_blank",
    #   "options": ["A", "B", "C", "D"], # null for short answer
    #   "correct_answer": "...", # STORED PRIVATELY ON BACKEND
    #   "explanation": "...",
    #   "topic_tag": "...",
    #   "difficulty": "...",
    #   "citations": [...]
    # }]
    questions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="quizzes")
    attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizAttempt.completed_at.desc()"
    )

    __table_args__ = (
        Index("idx_quiz_owner_topic", "owner_id", "topic"),
    )


class QuizAttempt(Base, TimestampMixin):
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    quiz_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Map of question_id -> user answer
    submitted_answers: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Detailed grading breakdown revealed only after submission
    graded_results: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0 to 100 percentage
    total_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    earned_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="attempts")
    user: Mapped["User"] = relationship("User", back_populates="quiz_attempts")

    __table_args__ = (
        Index("idx_attempt_user_quiz", "user_id", "quiz_id"),
        Index("idx_attempt_user_completed", "user_id", "completed_at"),
    )
