"""Voice Service coordinating TTS synthesis, STT transcription, audio asset storage,
playback authorization, cancellation, and capability discovery.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.audio_asset import AudioAsset
from backend.schemas.voice import (
    SpeechRequest,
    SpeechResponse,
    SpeechTimingSegment,
    TranscriptionResponse,
    VoiceCapabilities,
)
from backend.services.speech_to_text import stt_service
from backend.services.text_to_speech import tts_service
from backend.services.tutor_profiles import tutor_registry

logger = logging.getLogger(__name__)


class VoiceService:
    """Orchestrates end-to-end voice interactions and authorized media storage."""

    @classmethod
    def synthesize_response(
        cls,
        text: str,
        tutor_id: str,
        user_id: str,
        db: Session,
        session_id: Optional[str] = None,
        speed: float = 1.0,
    ) -> SpeechResponse:
        """Synthesize educational audio for a tutor response."""
        # 1. Retrieve character profile and voice settings
        tutor = tutor_registry.get_tutor_by_id(tutor_id)
        voice_profile = tutor.voice_profile if tutor else None
        voice_id = voice_profile.voice_id if voice_profile else "default_voice"
        locale = voice_profile.locale if voice_profile else "en-US"

        # 2. Prepare speech-friendly text (strip KaTeX & markdown)
        spoken_text = tts_service.prepare_speech_friendly_text(text)
        if not spoken_text:
            spoken_text = "Here is the explanation."

        # 3. Synthesize via provider
        provider = tts_service.get_provider()
        audio_bytes, duration_ms, timing_segments = provider.synthesize(
            clean_text=spoken_text,
            voice_id=voice_id,
            speed=speed,
            character_id=tutor_id,
        )

        # 4. Save to secure storage directory
        audio_id = str(uuid.uuid4())
        settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{audio_id}.mp3"
        storage_path = settings.AUDIO_DIR / filename
        with open(storage_path, "wb") as f:
            f.write(audio_bytes)

        # 5. Persist AudioAsset record in database
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.AUDIO_RETENTION_HOURS)
        audio_asset = AudioAsset(
            id=audio_id,
            user_id=user_id,
            session_id=session_id,
            tutor_id=tutor_id,
            asset_type="tts_output",
            status="ready",
            file_format="mp3",
            file_size_bytes=len(audio_bytes),
            duration_ms=duration_ms,
            storage_path=str(storage_path),
            transcript=spoken_text,
            timing_data=[seg.model_dump() for seg in timing_segments],
            expires_at=expires_at,
        )
        db.add(audio_asset)
        db.commit()
        db.refresh(audio_asset)

        audio_url = f"{settings.API_V1_PREFIX}/voice/speech/{audio_id}"

        return SpeechResponse(
            audio_id=audio_id,
            session_id=session_id,
            character_id=tutor_id,
            audio_url=audio_url,
            duration_ms=duration_ms,
            transcript=spoken_text,
            language=locale,
            voice_provider=settings.TTS_PROVIDER,
            voice_id=voice_id,
            segments=timing_segments,
            is_final_segment=True,
            expires_at=expires_at,
            created_at=audio_asset.created_at,
        )

    @classmethod
    def get_audio_asset(cls, audio_id: str, user_id: str, db: Session) -> AudioAsset:
        """Retrieve authorized audio asset metadata, enforcing user ownership."""
        asset = (
            db.query(AudioAsset)
            .filter(AudioAsset.id == audio_id, AudioAsset.user_id == user_id)
            .first()
        )
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio asset not found or access denied.",
            )
        return asset

    @classmethod
    def get_audio_file_path(cls, audio_id: str, user_id: str, db: Session) -> tuple[Path, str]:
        """Retrieve verified path and mime-type for streaming playback."""
        asset = cls.get_audio_asset(audio_id, user_id, db)
        if not asset.storage_path or not os.path.exists(asset.storage_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file has expired or was removed from storage.",
            )
        return Path(asset.storage_path), f"audio/{asset.file_format}"

    @classmethod
    def cancel_speech(cls, audio_id: str, user_id: str, db: Session) -> None:
        """Cancel audio playback, marking asset cancelled and registering cancellation token."""
        asset = cls.get_audio_asset(audio_id, user_id, db)
        asset.status = "cancelled"
        db.commit()
        tts_service.cancel_speech(audio_id=audio_id)

    @classmethod
    def get_capabilities(cls) -> VoiceCapabilities:
        """Report active voice capabilities without exposing API secrets."""
        tts_provider = tts_service.get_provider()
        stt_provider = stt_service.get_provider()

        return VoiceCapabilities(
            tts_enabled=tts_provider.is_available(),
            stt_enabled=stt_provider.is_available(),
            active_tts_provider=settings.TTS_PROVIDER,
            active_stt_provider=settings.STT_PROVIDER,
            streaming_supported=False,
            cancellation_supported=True,
            supported_audio_formats=["webm", "wav", "mp3", "ogg", "m4a"],
            max_upload_size_mb=settings.MAX_AUDIO_UPLOAD_SIZE_MB,
            audio_retention_hours=settings.AUDIO_RETENTION_HOURS,
        )


# Global singleton instance
voice_service = VoiceService()
