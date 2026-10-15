"""Text-to-Speech (TTS) Provider abstraction, speech text segmentation,
and audio synthesis engine with mock and real provider support.
"""

from __future__ import annotations

import io
import json
import logging
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import urllib.request
import urllib.error

from backend.config import settings
from backend.schemas.voice import SpeechTimingSegment
from backend.services.tutor_profiles import tutor_registry

logger = logging.getLogger(__name__)

# In-memory cancellation registry
_CANCELLED_AUDIO_IDS: Set[str] = set()
_CANCELLED_SESSION_IDS: Set[str] = set()


class TTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers."""

    @abstractmethod
    def synthesize(
        self,
        clean_text: str,
        voice_id: str,
        speed: float = 1.0,
        character_id: Optional[str] = None,
    ) -> tuple[bytes, int, List[SpeechTimingSegment]]:
        """Synthesize audio bytes, return (audio_bytes, duration_ms, segments)."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is operational."""
        pass


class MockTTSProvider(TTSProvider):
    """Deterministic Mock TTS Provider for automated testing and offline environments.
    Produces valid minimal MP3 frames with realistic duration and sentence timing metadata.
    """

    # Minimal silent MP3 frame bytes (MPEG-1 Audio Layer III, 128 kbps, 44.1 kHz)
    SILENT_MP3_FRAME = b"\xff\xfb\x90d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" * 20

    def synthesize(
        self,
        clean_text: str,
        voice_id: str,
        speed: float = 1.0,
        character_id: Optional[str] = None,
    ) -> tuple[bytes, int, List[SpeechTimingSegment]]:
        segments = TextToSpeechService.segment_text_for_speech(clean_text)

        # Estimate duration: average speaking rate ~140 words per minute (~2.3 words/sec)
        words = clean_text.split()
        word_count = max(1, len(words))
        base_seconds = (word_count / 2.3) / max(0.5, speed)
        duration_ms = int(base_seconds * 1000)

        # Generate realistic segment timings
        timing_segments: List[SpeechTimingSegment] = []
        current_time = 0
        seg_duration = int(duration_ms / max(1, len(segments)))

        for idx, seg in enumerate(segments):
            start = current_time
            end = current_time + seg_duration
            timing_segments.append(
                SpeechTimingSegment(
                    segment_index=idx,
                    text=seg,
                    start_ms=start,
                    end_ms=end,
                    animation_hint="speaking",
                    word_timings=[
                        {"word": w, "start_ms": start + i * 200, "end_ms": start + (i + 1) * 200}
                        for i, w in enumerate(seg.split()[:5])
                    ],
                )
            )
            current_time = end

        # Generate mock MP3 content proportional to duration
        frame_count = max(1, int(base_seconds * 4))
        audio_bytes = self.SILENT_MP3_FRAME * frame_count

        return audio_bytes, duration_ms, timing_segments

    def is_available(self) -> bool:
        return True


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS Provider via HTTP REST API."""

    def __init__(self):
        self.mock_fallback = MockTTSProvider()

    def is_available(self) -> bool:
        return bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your-") and not settings.OPENAI_API_KEY.startswith("sk-proj-placeholder"))

    def synthesize(
        self,
        clean_text: str,
        voice_id: str,
        speed: float = 1.0,
        character_id: Optional[str] = None,
    ) -> tuple[bytes, int, List[SpeechTimingSegment]]:
        if not self.is_available():
            logger.info("OpenAI TTS not configured. Serving mock synthesis.")
            return self.mock_fallback.synthesize(clean_text, voice_id, speed, character_id)

        url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/audio/speech"
        mapped_voice = voice_id if voice_id in ("alloy", "echo", "fable", "onyx", "nova", "shimmer") else settings.OPENAI_TTS_VOICE

        payload = {
            "model": settings.OPENAI_TTS_MODEL,
            "input": clean_text[:4096],
            "voice": mapped_voice,
            "speed": max(0.25, min(4.0, speed)),
            "response_format": "mp3",
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=settings.SPEECH_GENERATION_TIMEOUT_SECONDS) as resp:
                audio_bytes = resp.read()
                words = clean_text.split()
                duration_ms = int((len(words) / 2.3 / speed) * 1000)
                segments = TextToSpeechService.segment_text_for_speech(clean_text)
                timing_segments = [
                    SpeechTimingSegment(
                        segment_index=i,
                        text=s,
                        start_ms=int(i * (duration_ms / len(segments))),
                        end_ms=int((i + 1) * (duration_ms / len(segments))),
                        animation_hint="speaking",
                    )
                    for i, s in enumerate(segments)
                ]
                return audio_bytes, duration_ms, timing_segments
        except Exception as e:
            logger.warning(f"OpenAI TTS synthesis failed: {e}. Falling back to mock audio.")
            return self.mock_fallback.synthesize(clean_text, voice_id, speed, character_id)


class TextToSpeechService:
    """Coordinates TTS synthesis, text clean-up, and audio persistence."""

    @classmethod
    def get_provider(cls) -> TTSProvider:
        """Retrieve the configured TTS provider."""
        provider_name = (settings.TTS_PROVIDER or "mock").lower()
        if provider_name == "openai":
            p = OpenAITTSProvider()
            if p.is_available():
                return p
            return MockTTSProvider()
        return MockTTSProvider()

    @classmethod
    def prepare_speech_friendly_text(cls, text: str) -> str:
        """Strip raw Markdown, KaTeX delimiters, and citation tags for natural speech synthesis."""
        # 1. Remove ```json_citations blocks
        cleaned = re.sub(r"```json_citations[\s\S]*?```", "", text)
        # 2. Remove code blocks
        cleaned = re.sub(r"```[\s\S]*?```", " [code example] ", cleaned)
        # 3. Clean KaTeX inline $...$ and block $$...$$
        cleaned = re.sub(r"\$\$([\s\S]*?)\$\$", r" \1 ", cleaned)
        cleaned = re.sub(r"\$([^$]+)\$", r" \1 ", cleaned)
        # 4. Clean Markdown headers (#), bold (**), italic (*), links [text](url)
        cleaned = re.sub(r"#+\s*", "", cleaned)
        cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
        cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        # 5. Clean citation markers like [1], [Page 4]
        cleaned = re.sub(r"\[(?:Page|Slide|Video|Chunk)?[^\]]*\]", "", cleaned)
        # 6. Normalize whitespace
        cleaned = " ".join(cleaned.split())
        return cleaned.strip()

    @classmethod
    def segment_text_for_speech(cls, text: str) -> List[str]:
        """Divide speech text into digestible sentence-level segments for UI synchronization."""
        # Split on sentence terminals (. ! ?) while keeping reasonable segment length
        sentences = re.split(r"(?<=[.!?])\s+", text)
        segments: List[str] = []
        for s in sentences:
            s_clean = s.strip()
            if s_clean:
                segments.append(s_clean)
        return segments if segments else [text]

    @classmethod
    def cancel_speech(cls, audio_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
        """Register audio or session cancellation to halt playback or scheduling."""
        if audio_id:
            _CANCELLED_AUDIO_IDS.add(audio_id)
        if session_id:
            _CANCELLED_SESSION_IDS.add(session_id)
        logger.info(f"Registered speech cancellation: audio_id={audio_id}, session_id={session_id}")

    @classmethod
    def is_cancelled(cls, audio_id: Optional[str] = None, session_id: Optional[str] = None) -> bool:
        """Check if audio or session has been marked cancelled."""
        if audio_id and audio_id in _CANCELLED_AUDIO_IDS:
            return True
        if session_id and session_id in _CANCELLED_SESSION_IDS:
            return True
        return False


# Global singleton instance
tts_service = TextToSpeechService()
