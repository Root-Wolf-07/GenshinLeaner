"""Dedicated Citation Verification Engine.
Validates that generated citations correspond to real database chunks, permitted documents,
and actual source content without fabrication.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from backend.db.session import Session

from backend.models.document import Document, DocumentChunk
from backend.schemas.chat import Citation

logger = logging.getLogger(__name__)


class CitationValidator:
    """Verifies citation references against database ground truth."""

    @staticmethod
    def validate_citation(
        citation_data: Dict[str, Any],
        user_id: str,
        db: Session,
        allowed_document_ids: Optional[List[str]] = None,
    ) -> Optional[Citation]:
        """Validate a single citation reference.
        Returns a verified Citation object or None if invalid or fabricated.
        """
        citation_id = citation_data.get("citation_id") or citation_data.get("chunk_id")
        if not citation_id:
            logger.debug("Rejected citation: missing citation_id")
            return None

        # 1. Look up chunk in database enforcing user ownership
        chunk = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.id == citation_id,
                DocumentChunk.owner_id == user_id,
            )
            .first()
        )

        if not chunk:
            logger.warning(f"Rejected citation {citation_id}: chunk not found or unauthorized")
            return None

        # 2. Check document permissions
        if allowed_document_ids and chunk.document_id not in allowed_document_ids:
            logger.warning(f"Rejected citation {citation_id}: document {chunk.document_id} not in allowed list")
            return None

        # 3. Look up document
        doc = db.query(Document).filter(Document.id == chunk.document_id, Document.owner_id == user_id).first()
        if not doc:
            return None

        # 4. Validate or produce excerpt
        claimed_excerpt = citation_data.get("excerpt", "").strip()
        if claimed_excerpt:
            # Check if claimed excerpt is present in chunk content (case-insensitive substring)
            clean_chunk = " ".join(chunk.content.lower().split())
            clean_claimed = " ".join(claimed_excerpt.lower().split())
            if clean_claimed not in clean_chunk:
                # If claimed excerpt is fabricated or hallucinated, replace with genuine beginning of chunk
                claimed_excerpt = chunk.content[:220].strip() + ("..." if len(chunk.content) > 220 else "")
        else:
            claimed_excerpt = chunk.content[:220].strip() + ("..." if len(chunk.content) > 220 else "")

        # 5. Build verified citation preserving genuine location metadata (no invented locations)
        return Citation(
            citation_id=chunk.id,
            document_id=doc.id,
            document_title=doc.title or doc.original_filename,
            source_type=chunk.source_type,
            page_number=chunk.page_number,
            slide_number=chunk.slide_number,
            start_timestamp_seconds=chunk.start_timestamp_seconds,
            end_timestamp_seconds=chunk.end_timestamp_seconds,
            excerpt=claimed_excerpt,
        )

    @classmethod
    def validate_citations_list(
        cls,
        raw_citations: List[Dict[str, Any]],
        user_id: str,
        db: Session,
        allowed_document_ids: Optional[List[str]] = None,
    ) -> List[Citation]:
        """Validate a list of raw citations, filtering out invalid or fabricated entries."""
        verified: List[Citation] = []
        seen_ids = set()

        for raw in raw_citations:
            citation = cls.validate_citation(raw, user_id, db, allowed_document_ids)
            if citation and citation.citation_id not in seen_ids:
                verified.append(citation)
                seen_ids.add(citation.citation_id)

        return verified


# Global instance
citation_validator = CitationValidator()
