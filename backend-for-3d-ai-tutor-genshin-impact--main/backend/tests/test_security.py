"""Automated tests for security, authorization, error envelopes, and data isolation.
"""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.dependencies import hash_password, verify_password
from backend.models.document import Document
from backend.models.user import User


def test_password_hashing_security():
    password = "SuperSecretPassword#2026"
    hashed = hash_password(password)

    # Must not store plaintext password
    assert hashed != password
    # Verification should succeed with correct password
    assert verify_password(password, hashed) is True
    # Verification must fail with wrong password
    assert verify_password("WrongPassword123", hashed) is False


def test_standard_error_response_format_on_404(client: TestClient):
    response = client.get("/api/v1/documents/non-existent-uuid-999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "request_id" in data["error"]


def test_cross_user_document_access_prevented(client: TestClient, db_session: Session, other_user: User):
    # Create document owned by other_user
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        owner_id=other_user.id,
        original_filename="confidential_research.pdf",
        safe_storage_name=f"{doc_id}.pdf",
        file_type="pdf",
        file_size=2048,
        title="Other Student Research",
        status="ready",
    )
    db_session.add(doc)
    db_session.commit()

    # The client is authenticated as test_user. Attempting to access other_user's document:
    res = client.get(f"/api/v1/documents/{doc_id}")
    # Must return 404 (or 403) to prevent unauthorized enumeration
    assert res.status_code == 404
