"""Animation state schemas and gesture contracts.
Engine-independent, predictable animation instructions for frontend character renderers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from backend.schemas.compat import BaseModel, Field


class AnimationStateName(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    EXPLAINING = "explaining"
    SPEAKING = "speaking"
    HAPPY = "happy"
    EXCITED = "excited"
    ENCOURAGING = "encouraging"
    CURIOUS = "curious"
    CONFUSED_GENTLY = "confused_gently"
    SURPRISED = "surprised"
    CELEBRATING = "celebrating"
    GIVING_HINT = "giving_hint"
    DEMONSTRATING = "demonstrating"
    WAITING_FOR_ANSWER = "waiting_for_answer"
    CORRECT_ANSWER = "correct_answer"
    INCORRECT_ANSWER_SUPPORTIVE = "incorrect_answer_supportive"
    CONCERNED = "concerned"
    RESTING = "resting"
    ERROR = "error"


class ExpressionType(str, Enum):
    NEUTRAL = "neutral"
    FOCUSED = "focused"
    SMILE = "smile"
    CONFIDENT = "confident"
    PENSIVE = "pensive"
    EMPATHETIC = "empathetic"
    SURPRISED = "surprised"
    EXCITED = "excited"
    REASSURING = "reassuring"
    GENTLE_CONCERN = "gentle_concern"


class GestureType(str, Enum):
    NONE = "none"
    FRIENDLY_WAVE = "friendly_wave"
    GENTLE_NOD = "gentle_nod"
    THINKING_POSE = "thinking_pose"
    POINT_FORWARD = "point_forward"
    CELEBRATING_GESTURE = "celebrating_gesture"
    ENCOURAGING_THUMBS_UP = "encouraging_thumbs_up"
    CURIOUS_HEAD_TILT = "curious_head_tilt"
    DEMONSTRATION_GESTURE = "demonstration_gesture"
    LISTENING_ATTENTIVELY = "listening_attentively"
    GENTLE_ACKNOWLEDGMENT = "gentle_acknowledgment"


class AnimationInstruction(BaseModel):
    """Engine-independent animation instruction payload for character rendering."""
    state: str = Field(default="idle", description="Validated character animation state")
    character_id: str = Field(..., description="Target character identifier")
    expression: str = Field(default="neutral", description="Facial expression")
    gesture: str = Field(default="none", description="Bodily gesture")
    animation_key: str = Field(default="idle_default", description="Frontend asset reference key with guaranteed safe fallback")
    intensity: float = Field(default=0.8, ge=0.0, le=1.0, description="Animation intensity (calibrated for accessibility)")
    transition: Literal["smooth", "immediate", "fade"] = "smooth"
    duration_ms: Optional[int] = Field(default=3000, description="Duration in ms before returning to baseline/idle")
    is_looping: bool = Field(default=False, description="Whether the animation loops until interrupted")
    priority: int = Field(default=2, ge=1, le=5, description="Priority level 1 (lowest) to 5 (highest interrupt)")
    reason: Optional[str] = Field(default=None, description="Contextual reason for the state transition")
    session_id: Optional[str] = Field(default=None, description="Tutor session correlation ID")
    event_id: str = Field(default="", description="Unique event correlation identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"from_attributes": True}


class AnimationProfile(BaseModel):
    """Character-specific animation capability mapping and asset keys."""
    default_idle_key: str
    explaining_keys: List[str]
    listening_keys: List[str]
    thinking_keys: List[str]
    celebrating_keys: List[str]
    hint_keys: List[str]
    supportive_keys: List[str]
    fallback_key: str = "idle_default"
    supports_gestures: bool = True
    default_intensity: float = 0.8
