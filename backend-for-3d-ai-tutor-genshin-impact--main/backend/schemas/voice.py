"""Voice interaction and speech synthesis schemas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.schemas.compat import BaseModel, Field


class VoiceProfile(BaseModel):
    """Character voice configuration."""
    voice_provider: str = "mock"  # mock, edge_tts, openai, gemini
    voice_id: str = "default_voice"
    locale: str = "en-US"
    pitch: Optional[str] = "+0Hz"
    rate: Optional[str] = "+0%"
    volume: Optional[str] = "+0%"
    supported_locales: List[str] = Field(default_factory=lambda: ["en-US"])
    pronunciation_preferences: Dict[str, str] = Field(default_factory=dict)


class SpeechTimingSegment(BaseModel):
    """Segment-level or sentence-level timing information for visual sync."""
    segment_index: int
    text: str
    start_ms: int
    end_ms: int
    animation_hint: Optional[str] = "speaking"
    word_timings: Optional[List[Dict[str, Any]]] = None


class SpeechRequest(BaseModel):
    """Request payload to synthesize speech for a tutor response."""
    text: str = Field(..., min_length=1, max_length=10000, description="Response text to synthesize")
    session_id: Optional[str] = Field(default=None, description="Active tutor session ID")
    character_id: Optional[str] = Field(default=None, description="Character voice configuration to use")
    language: Optional[str] = Field(default="en", description="Target spoken language code")
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Speech playback speed multiplier")
    stream: Optional[bool] = Field(default=False, description="Whether client requests streaming chunks if supported")


class SpeechResponse(BaseModel):
    """Structured response containing audio metadata and synchronization cues."""
    audio_id: str
    session_id: Optional[str] = None
    character_id: str
    audio_url: str = Field(..., description="Authorized media streaming endpoint for playback")
    duration_ms: Optional[int] = None
    transcript: str
    language: str
    voice_provider: str
    voice_id: str
    segments: List[SpeechTimingSegment] = Field(default_factory=list)
    is_final_segment: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TranscriptionResponse(BaseModel):
    """Response payload for transcribed student voice recordings."""
    transcript: str
    language: str = "en"
    confidence: Optional[float] = None
    status: str = "completed"  # completed, failed
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoiceCapabilities(BaseModel):
    """Operational status and provider capabilities for audio interactions."""
    tts_enabled: bool
    stt_enabled: bool
    active_tts_provider: str
    active_stt_provider: str
    streaming_supported: bool
    cancellation_supported: bool
    supported_audio_formats: List[str]
    max_upload_size_mb: int
    audio_retention_hours: int
