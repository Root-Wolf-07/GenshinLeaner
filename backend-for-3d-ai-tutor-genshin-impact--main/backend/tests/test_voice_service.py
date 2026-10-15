"""Automated tests for Voice Interaction Service (TTS synthesis, STT transcription, audio streaming).
Verifies speech generation, cancellation, text segmentation, bounds checking, and security isolation.
"""

import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.services.text_to_speech import tts_service
from backend.services.voice_service import voice_service


def test_speech_text_cleaner_and_segmenter():
    """Text cleaner removes KaTeX and Markdown artifacts so spoken speech sounds natural."""
    raw_markdown = (
        "# Linear Transformations\n\n"
        "A transformation is linear if $$T(u + v) = T(u) + T(v)$$ and $T(cu) = cT(u)$.\n"
        "Refer to [Page 12].\n"
        "```json_citations\n"
        '[{"citation_id": "chunk_1", "excerpt": "text"}]\n'
        "```"
    )
    cleaned = tts_service.prepare_speech_friendly_text(raw_markdown)
    assert "#" not in cleaned
    assert "$$" not in cleaned
    assert "```" not in cleaned
    assert "json_citations" not in cleaned
    assert "Linear Transformations" in cleaned

    # Verify sentence segmentation
    segments = tts_service.segment_text_for_speech("First point. Second point! Third point?")
    assert len(segments) == 3


def test_speech_synthesis_with_mock_provider(client: TestClient, db_session: Session, test_user: User):
    """Requirement 10: Speech generation synthesizes audio bytes and records AudioAsset."""
    payload = {
        "text": "Welcome to our calculus exploration. We will analyze limits and continuity.",
        "character_id": "raiden_shogun",
        "speed": 1.0,
    }
    res = client.post("/api/v1/voice/speech", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "audio_id" in data
    assert data["character_id"] == "raiden_shogun"
    assert "/api/v1/voice/speech/" in data["audio_url"]
    assert data["duration_ms"] > 0
    assert len(data["segments"]) > 0

    audio_id = data["audio_id"]

    # Stream the synthesized audio
    stream_res = client.get(f"/api/v1/voice/speech/{audio_id}")
    assert stream_res.status_code == 200
    assert stream_res.headers["content-type"] == "audio/mp3"
    assert len(stream_res.content) > 0


def test_speech_cancellation(client: TestClient, db_session: Session, test_user: User):
    """Requirement 12: Speech cancellation registers token and halts playback."""
    # Generate speech
    synth_res = client.post(
        "/api/v1/voice/speech",
        json={"text": "This audio will be cancelled by the student.", "character_id": "zhongli"},
    )
    assert synth_res.status_code == 200
    audio_id = synth_res.json()["audio_id"]

    # Cancel speech
    cancel_res = client.post(f"/api/v1/voice/speech/{audio_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Verify cancellation registered in service
    assert tts_service.is_cancelled(audio_id=audio_id) is True


def test_audio_ownership_isolation(client: TestClient, db_session: Session, test_user: User, other_user: User):
    """Requirement 14: Students cannot stream or access another student's audio assets."""
    # Synthesize as test_user
    synth_res = client.post(
        "/api/v1/voice/speech",
        json={"text": "Private student voice recording.", "character_id": "nahida"},
    )
    assert synth_res.status_code == 200
    audio_id = synth_res.json()["audio_id"]

    # Attempt to stream as other_user
    from backend.dependencies import get_current_user
    from backend.main import app

    app.dependency_overrides[get_current_user] = lambda: other_user
    try:
        denied_res = client.get(f"/api/v1/voice/speech/{audio_id}")
        assert denied_res.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = lambda: test_user


def test_transcription_mock_service(client: TestClient):
    """Requirement 10 & 13: Transcription accepts valid audio file and returns recognized text."""
    fake_audio = io.BytesIO(b"RIFF....WAVEfmt ....data....fake_audio_pcm_bytes")
    files = {"file": ("test_recording.wav", fake_audio, "audio/wav")}
    res = client.post("/api/v1/voice/transcriptions", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert len(data["transcript"]) > 5
    assert data["confidence"] > 0.9


def test_transcription_unsupported_format(client: TestClient):
    """Requirement 13: Unsupported file formats are rejected with 415."""
    fake_doc = io.BytesIO(b"not an audio file")
    files = {"file": ("notes.exe", fake_doc, "application/octet-stream")}
    res = client.post("/api/v1/voice/transcriptions", files=files)
    assert res.status_code == 415
    assert "unsupported" in res.json()["error"]["message"].lower()


def test_voice_capabilities_endpoint(client: TestClient):
    """Voice capabilities endpoint reports provider status accurately."""
    res = client.get("/api/v1/voice/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["tts_enabled"] is True
    assert data["stt_enabled"] is True
    assert data["cancellation_supported"] is True
    assert "mp3" in data["supported_audio_formats"]
