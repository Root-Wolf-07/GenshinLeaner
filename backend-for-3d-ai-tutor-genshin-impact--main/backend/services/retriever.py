"""Retrieval service combining vector search with database metadata lookup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from backend.db.session import Session

from backend.config import settings
from backend.models.document import Document, DocumentChunk
from backend.services.embeddings import embedding_service
from backend.services.vector_store import vector_store


@dataclass
class RetrievedPassage:
    chunk_id: str
    document_id: str
    document_title: str
    source_type: str
    content: str
    similarity_score: float
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    start_timestamp_seconds: Optional[float] = None
    end_timestamp_seconds: Optional[float] = None


class RetrieverService:
    """Retrieves relevant document passages while enforcing ownership and permissions."""

    @staticmethod
    def retrieve(
        user_id: str,
        query: str,
        db: Session,
        allowed_document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_similarity: Optional[float] = None,
    ) -> List[RetrievedPassage]:
        """Perform semantic retrieval and enrich with document metadata."""
        if min_similarity is None:
            min_similarity = settings.SIMILARITY_THRESHOLD

        # 1. Embed query
        query_vector = embedding_service.embed_query(query)

        # 2. Search isolated vector index
        matches = vector_store.search(
            user_id=user_id,
            query_vector=query_vector,
            top_k=top_k,
            allowed_document_ids=allowed_document_ids,
            min_similarity=min_similarity,
        )

        if not matches:
            return []

        chunk_ids = [m[0] for m in matches]
        score_map = {m[0]: m[1] for m in matches}

        # 3. Fetch chunks from database enforcing ownership
        chunks = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.id.in_(chunk_ids),
                DocumentChunk.owner_id == user_id,
            )
            .all()
        )

        # 4. Fetch document titles
        doc_ids = list({c.document_id for c in chunks})
        docs = db.query(Document).filter(Document.id.in_(doc_ids), Document.owner_id == user_id).all()
        doc_title_map = {d.id: d.title or d.original_filename for d in docs}

        # 5. Build structured passages
        passages: List[RetrievedPassage] = []
        for chunk in chunks:
            passages.append(
                RetrievedPassage(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=doc_title_map.get(chunk.document_id, "Document"),
                    source_type=chunk.source_type,
                    content=chunk.content,
                    similarity_score=score_map.get(chunk.id, 0.0),
                    page_number=chunk.page_number,
                    slide_number=chunk.slide_number,
                    start_timestamp_seconds=chunk.start_timestamp_seconds,
                    end_timestamp_seconds=chunk.end_timestamp_seconds,
                )
            )

        # Order passages by similarity score
        passages.sort(key=lambda p: p.similarity_score, reverse=True)
        return passages


# Global instance
retriever_service = RetrieverService()
