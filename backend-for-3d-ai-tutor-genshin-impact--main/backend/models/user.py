"""User database model.
"""

import uuid
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
from backend.db.compat import String, Integer, DateTime, Boolean, JSON, Mapped, mapped_column, relationship
from backend.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.document import Document
    from backend.models.conversation import Conversation
    from backend.models.material import StudyMaterial
    from backend.models.quiz import Quiz, QuizAttempt
    from backend.models.learning import TopicMastery
    from backend.models.tutor_session import TutorSession
    from backend.models.audio_asset import AudioAsset
    from backend.models.learning_event import XPTransaction, UserAchievement


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Permanent unique public Student ID (e.g. STU-B84D20E6)
    student_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    normalized_email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    normalized_phone: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    student_level: Mapped[str] = mapped_column(
        String(50), default="undergraduate", nullable=False
    )
    preferences: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=lambda: {
            "learning_goals": [],
            "preferred_depth": "detailed",
            "study_language": "English",
            "theme": "dark",
            "katex_enabled": True,
            "neutral_mode": False,
        },
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Verification & Account Status
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verification_channel: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "email" or "phone"
    verification_code_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_verification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Password Recovery
    reset_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Security Throttling & Session Versioning
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    session_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="owner", cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="owner", cascade="all, delete-orphan"
    )
    materials: Mapped[List["StudyMaterial"]] = relationship(
        "StudyMaterial", back_populates="owner", cascade="all, delete-orphan"
    )
    quizzes: Mapped[List["Quiz"]] = relationship(
        "Quiz", back_populates="owner", cascade="all, delete-orphan"
    )
    quiz_attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt", back_populates="user", cascade="all, delete-orphan"
    )
    topic_masteries: Mapped[List["TopicMastery"]] = relationship(
        "TopicMastery", back_populates="user", cascade="all, delete-orphan"
    )
    tutor_sessions: Mapped[List["TutorSession"]] = relationship(
        "TutorSession", back_populates="user", cascade="all, delete-orphan"
    )
    audio_assets: Mapped[List["AudioAsset"]] = relationship(
        "AudioAsset", back_populates="user", cascade="all, delete-orphan"
    )
    xp_transactions: Mapped[List["XPTransaction"]] = relationship(
        "XPTransaction", back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[List["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )
