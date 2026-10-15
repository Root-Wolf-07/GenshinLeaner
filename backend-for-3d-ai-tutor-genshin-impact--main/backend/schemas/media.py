"""Multimodal student media generation schemas (Gemini image/video generation).
"""

from typing import Any, Dict, List, Literal, Optional
from backend.schemas.compat import BaseModel, Field


class MediaGenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="Visual description of study concept, diagram, or student avatar")
    style: Optional[str] = "educational_diagram"  # educational_diagram, student_avatar, concept_infographic
    aspect_ratio: Optional[Literal["1:1", "16:9", "4:3", "9:16"]] = "1:1"
    subject: Optional[str] = None


class MediaGenerateVideoRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    prompt: str = Field(..., min_length=3)
    script_style: Optional[str] = "micro_lesson"  # micro_lesson, animated_explainer, lecture_recap
    duration_seconds: Optional[int] = Field(default=60, ge=15, le=300)


class MediaGenerateResponse(BaseModel):
    media_type: Literal["image", "video_script", "animation_storyboard"]
    status: str
    title: str
    url: Optional[str] = None
    base64_data: Optional[str] = None
    storyboard: Optional[List[Dict[str, Any]]] = None
    narration_script: Optional[str] = None
    prompt: str
    model_used: str
