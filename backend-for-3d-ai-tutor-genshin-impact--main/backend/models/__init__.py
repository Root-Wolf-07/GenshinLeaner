"""Database models package.
Exports all SQLAlchemy models for Alembic metadata tracking and application use.
"""

from backend.db.base import Base
from backend.models.user import User
from backend.models.document import Document, DocumentChunk
from backend.models.conversation import Conversation, Message
from backend.models.material import StudyMaterial
from backend.models.quiz import Quiz, QuizAttempt
from backend.models.learning import TopicMastery
from backend.models.job import BackgroundJob
from backend.models.tutor_session import TutorSession, TutorSessionMessage
from backend.models.audio_asset import AudioAsset
from backend.models.learning_event import XPTransaction, UserAchievement

__all__ = [
    "Base",
    "User",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    "StudyMaterial",
    "Quiz",
    "QuizAttempt",
    "TopicMastery",
    "BackgroundJob",
    "TutorSession",
    "TutorSessionMessage",
    "AudioAsset",
    "XPTransaction",
    "UserAchievement",
]
