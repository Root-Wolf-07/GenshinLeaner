"""Quiz and Assessment Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from backend.schemas.compat import BaseModel, Field
from backend.schemas.chat import Citation

QuestionTypeEnum = Literal["multiple_choice", "true_false", "short_answer", "fill_in_the_blank"]


class QuestionPublic(BaseModel):
    """Question schema returned to students BEFORE submission (correct answer hidden)."""
    id: str
    prompt: str
    question_type: QuestionTypeEnum
    options: Optional[List[str]] = None  # None for short_answer / fill_in_the_blank
    topic_tag: str
    difficulty: str
    points: float = 1.0


class QuestionInternal(QuestionPublic):
    """Full question schema with answer key and citations stored on the backend."""
    correct_answer: Union[str, bool]
    explanation: str
    citations: List[Citation] = Field(default_factory=list)


class QuizGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=255)
    document_ids: Optional[List[str]] = Field(default_factory=list)
    question_count: int = Field(default=5, ge=1, le=25)
    difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    student_level: Optional[str] = "undergraduate"
    source_mode: Literal["uploaded", "general", "both"] = "both"
    question_types: Optional[List[QuestionTypeEnum]] = None
    character_id: Optional[str] = None
    subject: Optional[str] = None


class QuizResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    topic: str
    difficulty: str
    student_level: str
    source_mode: str
    document_ids: List[str]
    total_questions: int
    questions: List[QuestionPublic]
    character_presentation: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizSubmitRequest(BaseModel):
    # Mapping of question_id -> user answer string or boolean
    answers: Dict[str, Union[str, bool]] = Field(..., description="Map of question_id to student's answer")


class QuizGradedItem(BaseModel):
    question_id: str
    prompt: str
    question_type: str
    user_answer: Optional[Union[str, bool]]
    correct_answer: Union[str, bool]
    is_correct: bool
    score: float
    points_possible: float
    explanation: str
    feedback: str
    citations: List[Citation] = Field(default_factory=list)


class QuizResultResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: float  # Percentage 0.0 to 100.0
    earned_points: float
    total_points: float
    passed: bool
    summary_feedback: str
    graded_items: List[QuizGradedItem]
    completed_at: datetime


class AttemptResponse(BaseModel):
    id: str
    quiz_id: str
    user_id: str
    score: float
    total_points: float
    earned_points: float
    graded_results: List[QuizGradedItem]
    completed_at: datetime

    model_config = {"from_attributes": True}
