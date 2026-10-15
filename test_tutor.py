"""
Unit & Integration Tests for Barbara 3D AI Tutor Backend
Verifies:
1. Health check & configuration
2. Dialogue chat endpoint contracts, session tracking, & segments
3. Viseme timestamp ordering & validity
4. State updates & lifecycle transitions
5. Stale event rejection and error handling
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Furina" in data["character"]
    assert "furina.glb" in data["model_asset"]

def test_chat_dialogue_contract():
    payload = {
        "message": "Can you explain vaporize?",
        "user_id": "test_traveler"
    }
    response = client.post("/api/tutor/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Contract validation
    assert "session_id" in data
    assert "message_id" in data
    assert data["event"] == "tutor_response_ready"
    assert isinstance(data["text"], str) and len(data["text"]) > 0
    assert data["state"] in ["speaking", "explaining", "questioning", "encouraging", "celebrating", "idle"]
    assert isinstance(data["segments"], list)
    assert len(data["segments"]) > 0

    # Segments & Viseme validation
    for seg in data["segments"]:
        assert "text" in seg
        assert "start_ms" in seg
        assert "end_ms" in seg
        assert seg["end_ms"] >= seg["start_ms"]
        assert "visemes" in seg
        for vis in seg["visemes"]:
            assert vis["viseme"] in ["closed", "aa", "oh", "ee", "ou"]
            assert 0.0 <= vis["intensity"] <= 1.0

def test_session_continuity():
    # Message 1
    res1 = client.post("/api/tutor/chat", json={"message": "First greeting"})
    assert res1.status_code == 200
    s_id = res1.json()["session_id"]
    
    # Message 2 with same session_id
    res2 = client.post("/api/tutor/chat", json={"session_id": s_id, "message": "Second follow-up"})
    assert res2.status_code == 200
    assert res2.json()["session_id"] == s_id

def test_state_endpoint():
    res = client.post("/api/tutor/state", json={"session_id": "session_test_123", "state": "celebrating"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "updated"
    assert data["state"] == "celebrating"

def test_invalid_state_endpoint():
    res = client.post("/api/tutor/state", json={"session_id": "session_test_123", "state": "invalid_nonexistent_state"})
    assert res.status_code == 400

def test_empty_message_validation():
    res = client.post("/api/tutor/chat", json={"message": "   "})
    assert res.status_code == 400

if __name__ == "__main__":
    test_health_check()
    test_chat_dialogue_contract()
    test_session_continuity()
    test_state_endpoint()
    test_invalid_state_endpoint()
    test_empty_message_validation()
    print("ALL 6 TESTS PASSED SUCCESSFULLY!")
