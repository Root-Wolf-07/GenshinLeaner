"""Automated tests for AI Tutor Chat and conversation history.
"""

from fastapi.testclient import TestClient


def test_chat_general_mode(client: TestClient):
    payload = {
        "message": "Explain binary search trees and their time complexity.",
        "source_mode": "general",
        "response_depth": "detailed",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert data["role"] == "assistant"
    assert "conversation_id" in data
    assert len(data["content"]) > 10

    conv_id = data["conversation_id"]

    # Verify conversation history
    conv_res = client.get(f"/api/v1/conversations/{conv_id}")
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert conv_data["id"] == conv_id
    assert len(conv_data["messages"]) >= 2  # user + assistant


def test_chat_uploaded_mode_insufficient_evidence(client: TestClient):
    # In uploaded mode with no matching documents, the tutor must acknowledge lack of evidence
    payload = {
        "message": "What did the professor say about question 4 on page 99 of the syllabus?",
        "source_mode": "uploaded",
        "selected_document_ids": ["non-existent-doc-id-123"],
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["insufficient_evidence"] is True
    assert "could not find sufficient evidence" in data["content"].lower()
