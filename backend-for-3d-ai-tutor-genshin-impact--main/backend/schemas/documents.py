"""Document schemas for uploads, processing status, and chunks.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.schemas.compat import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    owner_id: str
    original_filename: str
    file_type: str
    file_size: int
    title: Optional[str] = None
    subject: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    page_count: int
    slide_count: int
    chunk_count: int
    doc_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    error_message: Optional[str] = None
    page_count: int
    slide_count: int
    chunk_count: int


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    start_timestamp_seconds: Optional[float] = None
    end_timestamp_seconds: Optional[float] = None
    source_type: str
    token_count: int
    chunk_metadata: Dict[str, Any]

    model_config = {"from_attributes": True}


class ReprocessResponse(BaseModel):
    document_id: str
    job_id: str
    status: str
    message: str
