"""Progress, Dashboard, and Recommendations schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.schemas.compat import BaseModel, Field
from backend.schemas.documents import DocumentResponse
from backend.schemas.chat import ConversationResponse
from backend.schemas.materials import StudyMaterialResponse
from backend.schemas.quizzes import QuizResponse


class TopicMasteryResponse(BaseModel):
    id: str
    topic: str
    total_questions_attempted: int
    correct_answers: int
    incorrect_answers: int
    mastery_score: float  # 0.0 to 100.0
    difficulty_level: str
    last_practiced_at: datetime

    model_config = {"from_attributes": True}


class RecommendationItem(BaseModel):
    id: str
    action_type: str  # "review_topic", "revisit_document", "generate_flashcards", "retake_quiz", "advance_level"
    title: str
    description: str
    reasoning: str
    target_topic: Optional[str] = None
    target_document_id: Optional[str] = None
    target_page_number: Optional[int] = None
    target_quiz_id: Optional[str] = None
    priority: str = "high"  # high, medium, low


class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem] = Field(default_factory=list)


class ProgressResponse(BaseModel):
    overall_accuracy: float
    total_quizzes_taken: int
    total_questions_answered: int
    total_correct: int
    weakest_topics: List[TopicMasteryResponse]
    strongest_topics: List[TopicMasteryResponse]
    topic_breakdown: List[TopicMasteryResponse]
    recent_improvements: List[Dict[str, Any]]
    suggested_revision_targets: List[str]


class RecentActivityItem(BaseModel):
    id: str
    activity_type: str  # document_upload, quiz_attempt, material_created, chat_session
    title: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    student_name: str
    student_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    student_level: str
    total_documents: int
    total_study_materials: int
    total_quizzes_taken: int
    average_quiz_score: float
    enrolled_subjects: List[str] = Field(default_factory=list)
    assigned_tutors: List[Dict[str, Any]] = Field(default_factory=list)
    recent_conversations: List[ConversationResponse]
    recent_documents: List[DocumentResponse]
    recent_materials: List[StudyMaterialResponse]
    recent_quizzes: List[QuizResponse]
    top_mastery_topics: List[TopicMasteryResponse]
    weak_topics: List[TopicMasteryResponse]
    recommended_actions: List[RecommendationItem]
    recent_activities: List[RecentActivityItem]
