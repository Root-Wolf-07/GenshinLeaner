"""Tutor session and interactive messaging schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from backend.schemas.compat import BaseModel, Field
from backend.schemas.chat import Citation
from backend.schemas.animation import AnimationInstruction
from backend.schemas.voice import SpeechResponse
from backend.schemas.rig import CharacterPerformanceCommand


InteractionIntent = Literal[
    "ask_question",
    "explain_simply",
    "explain_in_detail",
    "show_example",
    "give_hint",
    "check_my_answer",
    "practice_question",
    "summarize_topic",
    "revise_topic",
    "start_quiz",
    "generate_flashcards",
    "generate_notes",
    "change_difficulty",
    "repeat_explanation",
    "switch_to_text",
    "switch_to_voice",
]


class TutorSessionCreateRequest(BaseModel):
    """Request to initialize an interactive tutor session."""
    tutor_id: str = Field(..., description="Chosen character ID")
    subject: str = Field(..., description="Subject for the session (must be supported by character)")
    title: Optional[str] = None
    interaction_mode: Optional[Literal["text_only", "voice_only", "multimodal"]] = "multimodal"
    student_level: Optional[str] = "undergraduate"
    difficulty: Optional[str] = "intermediate"
    language: Optional[str] = "en"
    source_mode: Optional[Literal["uploaded", "general", "both"]] = "both"
    selected_document_ids: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None


class TutorSessionUpdateRequest(BaseModel):
    """Update ongoing session preferences or state."""
    title: Optional[str] = None
    interaction_mode: Optional[Literal["text_only", "voice_only", "multimodal"]] = None
    difficulty: Optional[str] = None
    language: Optional[str] = None
    source_mode: Optional[Literal["uploaded", "general", "both"]] = None
    selected_document_ids: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None


class TutorMessageRequest(BaseModel):
    """Student message or interaction intent."""
    content: str = Field(..., min_length=1, max_length=10000, description="Student's message or prompt")
    intent: InteractionIntent = Field(default="ask_question", description="Typed interaction intent")
    hint_level: Optional[int] = Field(default=None, ge=1, le=3, description="Requested hint level (1=subtle, 2=guiding, 3=step breakdown)")
    request_voice: Optional[bool] = Field(default=None, description="Explicitly request or suppress voice audio generation")
    user_answer_submission: Optional[str] = Field(default=None, description="Answer string when intent is 'check_my_answer'")


class TutorMessageResponse(BaseModel):
    """Tutor response accompanied by animation state, citations, and optional voice audio."""
    message_id: str
    session_id: str
    role: str = "assistant"
    content: str
    intent: str
    tutor_id: str
    character_name: str
    animation: AnimationInstruction
    performance: Optional[CharacterPerformanceCommand] = None
    speech: Optional[SpeechResponse] = None
    citations: List[Citation] = Field(default_factory=list)
    suggested_follow_ups: List[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
    pedagogical_mode: Optional[str] = "adaptive_scaffolding"
    created_at: datetime

    model_config = {"from_attributes": True}


class TutorSessionSummaryResponse(BaseModel):
    """Session summary for listing."""
    id: str
    user_id: str
    tutor_id: str
    subject: str
    title: str
    interaction_mode: str
    status: str
    difficulty: str
    language: str
    source_mode: str
    selected_document_ids: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TutorSessionDetailResponse(TutorSessionSummaryResponse):
    """Full session details with message history."""
    messages: List[TutorMessageResponse] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class SessionCancelResponse(BaseModel):
    """Response returned when an active session or audio playback is cancelled."""
    session_id: str
    status: str = "cancelled"
    message: str = "Tutor interaction cancelled successfully."
    audio_cancelled: bool = True
