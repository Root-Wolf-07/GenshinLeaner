"""Document management and upload endpoints.
"""

import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.document import Document, DocumentChunk
from backend.models.user import User
from backend.schemas.documents import (
    DocumentResponse,
    DocumentStatusResponse,
    DocumentChunkResponse,
    ReprocessResponse,
)
from backend.services.document_processor import document_processor
from backend.services.job_queue import job_queue

router = APIRouter(tags=["Document Management"])


@router.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a course document (PDF, PPTX, DOCX, TXT, MD) and initiate ingestion."""
    # 1. Validate file extension
    orig_filename = file.filename or "uploaded_document.txt"
    ext = Path(orig_filename).suffix.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # 2. Generate secure storage identifier
    safe_storage_name = f"{uuid.uuid4().hex}{ext}"
    destination = settings.UPLOAD_DIR / safe_storage_name

    # 3. Stream upload and validate size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    bytes_written = 0

    try:
        with open(destination, "wb") as buffer:
            while chunk := await file.read(1024 * 64):
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    buffer.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # 4. Create Document record in DB
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        owner_id=current_user.id,
        original_filename=orig_filename,
        safe_storage_name=safe_storage_name,
        file_type=ext.lstrip("."),
        file_size=bytes_written,
        title=title or Path(orig_filename).stem.replace("_", " ").title(),
        subject=subject,
        status="uploaded",
        doc_metadata={"original_size": bytes_written},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 5. Process document
    document_processor.process_document(doc.id, db)
    db.refresh(doc)

    return doc


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all documents owned by the current student."""
    return (
        db.query(Document)
        .filter(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve document details and processing summary."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check processing status of a document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        error_message=doc.error_message,
        page_count=doc.page_count,
        slide_count=doc.slide_count,
        chunk_count=doc.chunk_count,
    )


@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(
    document_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve paginated text chunks belonging to a document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    offset = (page - 1) * page_size
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id, DocumentChunk.owner_id == current_user.id)
        .order_by(DocumentChunk.chunk_index.asc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return chunks


@router.post("/documents/{document_id}/reprocess", response_model=ReprocessResponse)
def reprocess_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger reprocessing and re-indexing of an uploaded document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Create background job
    job = job_queue.create_job(owner_id=current_user.id, job_type="document_reprocess", resource_id=doc.id, db=db)
    job_queue.submit_task(job.id, document_processor.process_document, doc.id, db)

    return ReprocessResponse(
        document_id=doc.id,
        job_id=job.id,
        status="processing",
        message="Reprocessing initiated in the background.",
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document, removing stored files, chunks, and vector index entries."""
    success = document_processor.delete_document_artifacts(document_id, current_user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return None
