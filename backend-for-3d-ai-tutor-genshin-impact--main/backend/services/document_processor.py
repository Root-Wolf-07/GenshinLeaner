"""Complete Document Ingestion and Processing Pipeline.
Handles validation, parsing, metadata tracking, chunking, embedding, and vector indexing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional
from backend.db.session import Session

from backend.config import settings
from backend.models.document import Document, DocumentChunk
from backend.services.chunking import TextChunker
from backend.services.document_parser import DocumentParser
from backend.services.embeddings import embedding_service
from backend.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates end-to-end document processing lifecycle."""

    def __init__(self):
        self.chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def process_document(self, document_id: str, db: Session) -> bool:
        """Run extraction, chunking, and vector indexing for a document."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Cannot process document: {document_id} not found")
            return False

        # Set status to processing
        doc.status = "processing"
        doc.error_message = None
        db.commit()

        storage_path = settings.UPLOAD_DIR / doc.safe_storage_name
        if not storage_path.exists():
            doc.status = "failed"
            doc.error_message = f"File not found in storage: {doc.safe_storage_name}"
            db.commit()
            return False

        try:
            # 1. Parse document
            parse_result = DocumentParser.parse(storage_path, doc.file_type)

            if not parse_result.sections or parse_result.char_count == 0:
                doc.status = "failed"
                doc.error_message = "Document is empty or no readable text could be extracted."
                db.commit()
                return False

            doc.page_count = parse_result.total_pages
            doc.slide_count = parse_result.total_slides

            # 2. Chunk text preserving page/slide coordinates
            processed_chunks = self.chunker.chunk_sections(
                sections=parse_result.sections,
                document_id=doc.id,
                owner_id=doc.owner_id,
                source_type=doc.file_type,
            )

            if not processed_chunks:
                doc.status = "failed"
                doc.error_message = "No valid text chunks produced."
                db.commit()
                return False

            # Clean out any old chunks if reprocessing
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            vector_store.delete_document_vectors(user_id=doc.owner_id, document_id=doc.id)

            # 3. Save chunks in database
            db_chunks: List[DocumentChunk] = []
            chunk_texts: List[str] = []
            chunk_ids: List[str] = []

            for p_chunk in processed_chunks:
                chunk_record = DocumentChunk(
                    id=p_chunk.chunk_id,
                    document_id=doc.id,
                    owner_id=doc.owner_id,
                    chunk_index=p_chunk.chunk_index,
                    content=p_chunk.content,
                    page_number=p_chunk.page_number,
                    slide_number=p_chunk.slide_number,
                    start_timestamp_seconds=p_chunk.start_timestamp,
                    end_timestamp_seconds=p_chunk.end_timestamp,
                    source_type=p_chunk.source_type,
                    token_count=p_chunk.token_count,
                    chunk_metadata=p_chunk.chunk_metadata,
                )
                db_chunks.append(chunk_record)
                chunk_texts.append(p_chunk.content)
                chunk_ids.append(p_chunk.chunk_id)

            db.add_all(db_chunks)
            doc.chunk_count = len(db_chunks)

            # 4. Generate embeddings
            vectors = embedding_service.embed_texts(chunk_texts)

            # 5. Add to user's isolated vector store
            vector_store.add_chunks(
                user_id=doc.owner_id,
                document_id=doc.id,
                chunk_ids=chunk_ids,
                vectors=vectors,
            )

            # 6. Mark document as ready
            doc.status = "ready"
            doc.error_message = None
            db.commit()
            db.refresh(doc)
            logger.info(f"Successfully processed document {doc.id} ({doc.chunk_count} chunks indexed)")
            return True

        except Exception as e:
            logger.exception(f"Error processing document {doc.id}: {e}")
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            return False

    def delete_document_artifacts(self, document_id: str, owner_id: str, db: Session) -> bool:
        """Purge document file, DB chunks, and vector index entries."""
        doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == owner_id).first()
        if not doc:
            return False

        # 1. Remove physical file
        file_path = settings.UPLOAD_DIR / doc.safe_storage_name
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")

        # 2. Remove vector index entries
        vector_store.delete_document_vectors(user_id=owner_id, document_id=document_id)

        # 3. Delete document record (cascade deletes chunks in DB)
        db.delete(doc)
        db.commit()
        return True


# Global instance
document_processor = DocumentProcessor()
