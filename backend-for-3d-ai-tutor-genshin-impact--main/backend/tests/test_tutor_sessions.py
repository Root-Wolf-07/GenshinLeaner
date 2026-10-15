"""Automated tests for Tutor Sessions and Interactive Messaging.
Verifies session creation, subject qualification, Socratic intents, RAG citations, and access control.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.user import User


def test_create_tutor_session_success(client: TestClient):
    """Test creating an interactive session with Raiden for Mathematics."""
    payload = {
        "tutor_id": "raiden_shogun",
        "subject": "Mathematics",
        "title": "Calculus Foundations",
        "interaction_mode": "multimodal",
        "student_level": "undergraduate",
    }
    res = client.post("/api/v1/tutor-sessions", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["tutor_id"] == "raiden_shogun"
    assert data["subject"] == "Mathematics"
    assert data["status"] == "active"


def test_create_tutor_session_unsupported_subject_fails(client: TestClient):
    """Requirement 4: Tutor cannot teach an unassigned subject."""
    payload = {
        "tutor_id": "raiden_shogun",
        "subject": "Biology",  # Barbara teaches Biology, not Raiden
    }
    res = client.post("/api/v1/tutor-sessions", json=payload)
    assert res.status_code == 400
    assert "does not specialize in" in res.json()["error"]["message"]


def test_tutor_session_interaction_intents(client: TestClient):
    """Requirement 8 & 10: Test sending messages with various Socratic intents."""
    # 1. Create session with Keqing for Computer Science
    session_res = client.post(
        "/api/v1/tutor-sessions",
        json={"tutor_id": "keqing", "subject": "Computer Science"},
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]

    # 2. General question
    msg_res1 = client.post(
        f"/api/v1/tutor-sessions/{session_id}/messages",
        json={"content": "What is the Big-O time complexity of merge sort?", "intent": "ask_question"},
    )
    assert msg_res1.status_code == 200
    data1 = msg_res1.json()
    assert data1["role"] == "assistant"
    assert "animation" in data1
    assert data1["animation"]["state"] in ("explaining", "speaking")
    assert "speech" in data1  # multimodal generated speech

    # 3. Request progressive hint
    msg_res2 = client.post(
        f"/api/v1/tutor-sessions/{session_id}/messages",
        json={"content": "I'm stuck on implementing merge sort base case.", "intent": "give_hint", "hint_level": 1},
    )
    assert msg_res2.status_code == 200
    data2 = msg_res2.json()
    assert data2["animation"]["state"] == "giving_hint"
    assert "hint" in data2["pedagogical_mode"]

    # 4. Check student answer
    msg_res3 = client.post(
        f"/api/v1/tutor-sessions/{session_id}/messages",
        json={
            "content": "Is the base case if len(arr) <= 1 return arr?",
            "intent": "check_my_answer",
            "user_answer_submission": "if len(arr) <= 1: return arr",
        },
    )
    assert msg_res3.status_code == 200
    data3 = msg_res3.json()
    assert data3["animation"]["state"] == "waiting_for_answer"


def test_tutor_session_cancel(client: TestClient):
    """Requirement 12: Cancel an active tutor session."""
    session_res = client.post(
        "/api/v1/tutor-sessions",
        json={"tutor_id": "furina", "subject": "Music"},
    )
    session_id = session_res.json()["id"]

    cancel_res = client.post(f"/api/v1/tutor-sessions/{session_id}/cancel")
    assert cancel_res.status_code == 200
    data = cancel_res.json()
    assert data["status"] == "cancelled"
    assert data["audio_cancelled"] is True


def test_session_ownership_isolation(client: TestClient, test_user: User, other_user: User):
    """Requirement 14: Students cannot view or message another student's tutor sessions."""
    # Create as test_user
    session_res = client.post(
        "/api/v1/tutor-sessions",
        json={"tutor_id": "ganyu", "subject": "Physics"},
    )
    session_id = session_res.json()["id"]

    # Switch to other_user
    from backend.dependencies import get_current_user
    from backend.main import app

    app.dependency_overrides[get_current_user] = lambda: other_user
    try:
        denied_get = client.get(f"/api/v1/tutor-sessions/{session_id}")
        assert denied_get.status_code == 404

        denied_msg = client.post(
            f"/api/v1/tutor-sessions/{session_id}/messages",
            json={"content": "Can I access this?", "intent": "ask_question"},
        )
        assert denied_msg.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = lambda: test_user
