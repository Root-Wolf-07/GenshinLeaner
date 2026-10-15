"""Schemas package root.
Exports all Pydantic request and response models.
"""

from backend.schemas.common import ErrorDetail, ErrorResponse, PaginationMeta, PaginatedResponse
from backend.schemas.auth import UserRegister, UserLogin, UserResponse, Token, ProfileUpdate
from backend.schemas.documents import DocumentResponse, DocumentStatusResponse, DocumentChunkResponse, ReprocessResponse
from backend.schemas.chat import Citation, ChatRequest, ChatResponse, ConversationResponse, MessageResponse, DiagnosticCheckpoint
from backend.schemas.materials import (
    StudyMaterialGenerateRequest,
    StudyMaterialResponse,
    StudyMaterialUpdateRequest,
    SectionRegenerateRequest,
    MaterialExportRequest,
    MaterialExportResponse,
)
from backend.schemas.quizzes import (
    QuestionPublic,
    QuestionInternal,
    QuizGenerateRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizGradedItem,
    QuizResultResponse,
    AttemptResponse,
)
from backend.schemas.progress import (
    TopicMasteryResponse,
    RecommendationItem,
    RecommendationsResponse,
    ProgressResponse,
    DashboardResponse,
    RecentActivityItem,
)
from backend.schemas.media import MediaGenerateImageRequest, MediaGenerateVideoRequest, MediaGenerateResponse
from backend.schemas.jobs import JobResponse
from backend.schemas.tutor import TutorProfile, TutorSummary, AgeAppropriateRules
from backend.schemas.animation import AnimationInstruction, AnimationProfile, AnimationStateName, ExpressionType, GestureType
from backend.schemas.voice import VoiceProfile, SpeechRequest, SpeechResponse, SpeechTimingSegment, TranscriptionResponse, VoiceCapabilities
from backend.schemas.tutor_session import (
    TutorSessionCreateRequest,
    TutorSessionUpdateRequest,
    TutorSessionSummaryResponse,
    TutorSessionDetailResponse,
    TutorMessageRequest,
    TutorMessageResponse,
    SessionCancelResponse,
)
from backend.schemas.gamification import (
    XPTransactionResponse,
    AchievementResponse,
    QuestResponse,
    GamificationSummaryResponse,
    XPRewardRequest,
)
from backend.schemas.events import EventEnvelope
from backend.schemas.rig import (
    RigType,
    FacialControlType,
    EyeControlType,
    JawMouthControlType,
    VisemeCue,
    CharacterRigCapability,
    CharacterPerformanceCommand,
)

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "PaginationMeta",
    "PaginatedResponse",
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "Token",
    "ProfileUpdate",
    "DocumentResponse",
    "DocumentStatusResponse",
    "DocumentChunkResponse",
    "ReprocessResponse",
    "Citation",
    "ChatRequest",
    "ChatResponse",
    "ConversationResponse",
    "MessageResponse",
    "DiagnosticCheckpoint",
    "StudyMaterialGenerateRequest",
    "StudyMaterialResponse",
    "StudyMaterialUpdateRequest",
    "SectionRegenerateRequest",
    "MaterialExportRequest",
    "MaterialExportResponse",
    "QuestionPublic",
    "QuestionInternal",
    "QuizGenerateRequest",
    "QuizResponse",
    "QuizSubmitRequest",
    "QuizGradedItem",
    "QuizResultResponse",
    "AttemptResponse",
    "TopicMasteryResponse",
    "RecommendationItem",
    "RecommendationsResponse",
    "ProgressResponse",
    "DashboardResponse",
    "RecentActivityItem",
    "MediaGenerateImageRequest",
    "MediaGenerateVideoRequest",
    "MediaGenerateResponse",
    "JobResponse",
    "TutorProfile",
    "TutorSummary",
    "AgeAppropriateRules",
    "AnimationInstruction",
    "AnimationProfile",
    "AnimationStateName",
    "ExpressionType",
    "GestureType",
    "VoiceProfile",
    "SpeechRequest",
    "SpeechResponse",
    "SpeechTimingSegment",
    "TranscriptionResponse",
    "VoiceCapabilities",
    "TutorSessionCreateRequest",
    "TutorSessionUpdateRequest",
    "TutorSessionSummaryResponse",
    "TutorSessionDetailResponse",
    "TutorMessageRequest",
    "TutorMessageResponse",
    "SessionCancelResponse",
    "XPTransactionResponse",
    "AchievementResponse",
    "QuestResponse",
    "GamificationSummaryResponse",
    "XPRewardRequest",
    "EventEnvelope",
]
