"""AudioAsset database model.
Tracks generated and uploaded audio files, playback metadata, expiration, and status.
Never exposes filesystem paths directly to clients.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from backend.db.compat import (
    String, Integer, Text, JSON, DateTime, ForeignKey, Index, Mapped, mapped_column, relationship
)
from backend.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.tutor_session import TutorSession


class AudioAsset(Base, TimestampMixin):
    __tablename__ = "audio_assets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("tutor_sessions.id", ondelete="CASCADE"), index=True, nullable=True
    )
    tutor_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    asset_type: Mapped[str] = mapped_column(
        String(50), default="tts_output", nullable=False
    )  # tts_output, stt_input
    status: Mapped[str] = mapped_column(
        String(50), default="ready", nullable=False
    )  # pending, ready, failed, cancelled
    file_format: Mapped[str] = mapped_column(String(20), default="mp3", nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timing_data: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audio_assets")
    session: Mapped[Optional["TutorSession"]] = relationship("TutorSession", back_populates="audio_assets")

    __table_args__ = (
        Index("idx_audio_user_session", "user_id", "session_id"),
        Index("idx_audio_status_expires", "status", "expires_at"),
    )
