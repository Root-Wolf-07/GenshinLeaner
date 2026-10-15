"""Voice and Speech Interaction API endpoints (TTS synthesis, STT transcription, audio streaming).
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user, decode_access_token, get_or_create_demo_user
from backend.config import settings
from backend.models.user import User
from backend.schemas.voice import (
    SpeechRequest,
    SpeechResponse,
    TranscriptionResponse,
    VoiceCapabilities,
)
from backend.services.speech_to_text import stt_service
from backend.services.voice_service import voice_service

router = APIRouter(tags=["Voice & Speech"])


def get_user_from_token_or_query(
    token: Optional[str] = Query(default=None),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Helper enabling audio streaming via browser <audio> tags with query param token fallback."""
    if current_user:
        return current_user
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()  # noqa: E712
            if user:
                return user
    if settings.DEBUG or settings.APP_ENV == "development":
        return get_or_create_demo_user(db)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for audio streaming.")


@router.post("/voice/transcriptions", response_model=TranscriptionResponse)
def transcribe_audio(
    file: UploadFile = File(..., description="Audio recording file (webm, wav, mp3, ogg, m4a)"),
    session_id: Optional[str] = Form(default=None),
    language: Optional[str] = Form(default="en"),
    current_user: User = Depends(get_current_user),
):
    """Transcribe student spoken inquiry into text with confidence metric."""
    return stt_service.process_audio_upload(
        upload_file=file,
        session_id=session_id,
        language=language,
    )


@router.post("/voice/speech", response_model=SpeechResponse)
def synthesize_speech(
    request: SpeechRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Synthesize speech audio for given text using character voice configuration."""
    character_id = request.character_id or "raiden_shogun"
    return voice_service.synthesize_response(
        text=request.text,
        tutor_id=character_id,
        user_id=current_user.id,
        db=db,
        session_id=request.session_id,
        speed=request.speed or 1.0,
    )


@router.get("/voice/speech/{audio_id}")
def stream_audio(
    audio_id: str,
    token: Optional[str] = Query(default=None, description="Optional bearer token for HTML5 <audio> elements"),
    current_user: User = Depends(get_user_from_token_or_query),
    db: Session = Depends(get_db),
):
    """Stream authorized audio file bytes for browser playback."""
    file_path, media_type = voice_service.get_audio_file_path(
        audio_id=audio_id, user_id=current_user.id, db=db
    )
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=f"tutor_speech_{audio_id}.mp3",
    )


@router.post("/voice/speech/{audio_id}/cancel")
def cancel_speech(
    audio_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel active speech playback and notify audio engine."""
    voice_service.cancel_speech(audio_id=audio_id, user_id=current_user.id, db=db)
    return {
        "audio_id": audio_id,
        "status": "cancelled",
        "message": "Speech playback cancelled successfully.",
    }


@router.get("/voice/capabilities", response_model=VoiceCapabilities)
def get_voice_capabilities() -> VoiceCapabilities:
    """Discover active voice engine capabilities, format support, and upload bounds."""
    return voice_service.get_capabilities()
