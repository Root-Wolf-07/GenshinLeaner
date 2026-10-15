"""TutorSession and TutorSessionMessage database models.
Tracks character-driven interactive tutoring sessions, active characters, subjects,
animation instructions, and conversation history.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from backend.db.compat import (
    String, Text, JSON, ForeignKey, Index, Mapped, mapped_column, relationship
)
from backend.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.audio_asset import AudioAsset


class TutorSession(Base, TimestampMixin):
    __tablename__ = "tutor_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tutor_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="Tutor Session", nullable=False)
    interaction_mode: Mapped[str] = mapped_column(
        String(50), default="multimodal", nullable=False
    )  # text_only, voice_only, multimodal
    student_level: Mapped[str] = mapped_column(
        String(50), default="undergraduate", nullable=False
    )
    difficulty: Mapped[str] = mapped_column(
        String(50), default="intermediate", nullable=False
    )
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False
    )  # active, completed, cancelled
    source_mode: Mapped[str] = mapped_column(
        String(50), default="both", nullable=False
    )  # uploaded, general, both
    selected_document_ids: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    preferences: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    session_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tutor_sessions")
    messages: Mapped[List["TutorSessionMessage"]] = relationship(
        "TutorSessionMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TutorSessionMessage.created_at",
    )
    audio_assets: Mapped[List["AudioAsset"]] = relationship(
        "AudioAsset",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_tutor_session_user_status", "user_id", "status"),
        Index("idx_tutor_session_user_tutor", "user_id", "tutor_id"),
    )


class TutorSessionMessage(Base, TimestampMixin):
    __tablename__ = "tutor_session_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tutor_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(
        String(50), default="ask_question", nullable=False
    )
    citations: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    animation_state: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    audio_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    message_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationships
    session: Mapped["TutorSession"] = relationship("TutorSession", back_populates="messages")

    __table_args__ = (
        Index("idx_tutor_message_session_created", "session_id", "created_at"),
    )
