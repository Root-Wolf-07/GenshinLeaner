"""Automated tests for Citation Verification Engine.
"""

import uuid
from sqlalchemy.orm import Session
from backend.models.document import Document, DocumentChunk
from backend.models.user import User
from backend.services.citation_validator import citation_validator


def test_citation_validator_accepts_valid_chunk(db_session: Session, test_user: User):
    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    doc = Document(
        id=doc_id,
        owner_id=test_user.id,
        original_filename="graphs.pdf",
        safe_storage_name=f"{doc_id}.pdf",
        file_type="pdf",
        file_size=1024,
        title="Graph Theory Lecture",
        status="ready",
    )
    chunk = DocumentChunk(
        id=chunk_id,
        document_id=doc_id,
        owner_id=test_user.id,
        chunk_index=0,
        content="Dijkstra's algorithm finds the shortest path in non-negative weighted graphs.",
        page_number=14,
        source_type="pdf",
        token_count=12,
    )
    db_session.add(doc)
    db_session.add(chunk)
    db_session.commit()

    # Valid citation reference
    raw = {
        "citation_id": chunk_id,
        "excerpt": "Dijkstra's algorithm finds the shortest path",
    }
    validated = citation_validator.validate_citation(
        citation_data=raw,
        user_id=test_user.id,
        db=db_session,
        allowed_document_ids=[doc_id],
    )

    assert validated is not None
    assert validated.citation_id == chunk_id
    assert validated.document_id == doc_id
    assert validated.document_title == "Graph Theory Lecture"
    assert validated.page_number == 14
    assert validated.source_type == "pdf"


def test_citation_validator_rejects_nonexistent_id(db_session: Session, test_user: User):
    raw = {"citation_id": "fabricated-fake-uuid", "excerpt": "Some made up text"}
    validated = citation_validator.validate_citation(
        citation_data=raw,
        user_id=test_user.id,
        db=db_session,
    )
    assert validated is None


def test_citation_validator_rejects_other_user_chunk(db_session: Session, test_user: User, other_user: User):
    doc_id = str(uuid.uuid4())
    chunk_id = str(uuid.uuid4())

    # Chunk belongs to other_user
    doc = Document(
        id=doc_id,
        owner_id=other_user.id,
        original_filename="private.pdf",
        safe_storage_name=f"{doc_id}.pdf",
        file_type="pdf",
        file_size=500,
        title="Private Notes",
        status="ready",
    )
    chunk = DocumentChunk(
        id=chunk_id,
        document_id=doc_id,
        owner_id=other_user.id,
        chunk_index=0,
        content="Confidential proprietary information.",
        page_number=1,
        source_type="pdf",
        token_count=5,
    )
    db_session.add(doc)
    db_session.add(chunk)
    db_session.commit()

    # test_user attempts to cite other_user's chunk
    raw = {"citation_id": chunk_id, "excerpt": "Confidential"}
    validated = citation_validator.validate_citation(
        citation_data=raw,
        user_id=test_user.id,  # requesting as test_user
        db=db_session,
    )
    # Must reject unauthorized cross-user citations!
    assert validated is None
