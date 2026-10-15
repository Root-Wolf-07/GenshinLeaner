"""Multimodal Media Generation API endpoints (Gemini student diagrams and video scripts).
"""

from fastapi import APIRouter, Depends
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.media import (
    MediaGenerateImageRequest,
    MediaGenerateVideoRequest,
    MediaGenerateResponse,
)
from backend.services.gemini_service import gemini_service

router = APIRouter(tags=["Multimodal Media Generation (Gemini)"])


@router.post("/media/generate-image", response_model=MediaGenerateResponse)
def generate_study_image(
    request: MediaGenerateImageRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate educational visual diagrams, concept illustrations, or student avatars using Google Gemini."""
    result = gemini_service.generate_image(
        prompt=request.prompt,
        aspect_ratio=request.aspect_ratio or "1:1",
        style=request.style or "educational_diagram",
    )
    return MediaGenerateResponse(
        media_type="image",
        status=result.get("status", "success"),
        title=f"Visual Diagram: {request.prompt[:30]}",
        base64_data=result.get("base64_data"),
        url=result.get("url"),
        prompt=result.get("prompt", request.prompt),
        model_used=result.get("model_used", "gemini-imagen"),
    )


@router.post("/media/generate-video", response_model=MediaGenerateResponse)
def generate_study_video_script(
    request: MediaGenerateVideoRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an educational video lesson storyboard, narration script, and visual cues using Google Gemini."""
    result = gemini_service.generate_video_storyboard(
        topic=request.topic,
        prompt=request.prompt,
        style=request.script_style or "micro_lesson",
        duration_seconds=request.duration_seconds or 60,
    )
    return MediaGenerateResponse(
        media_type="video_script",
        status=result.get("status", "success"),
        title=result.get("title", f"Video Lesson: {request.topic}"),
        storyboard=result.get("storyboard"),
        narration_script=result.get("narration_script"),
        prompt=request.prompt,
        model_used=result.get("model_used", "gemini-2.5-flash"),
    )
