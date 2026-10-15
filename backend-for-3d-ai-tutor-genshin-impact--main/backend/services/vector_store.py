"""Vector store service with per-user index isolation.
Prevents cross-user data leakage and supports FAISS and pure-Python persistence.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.config import settings

logger = logging.getLogger(__name__)

# Check for FAISS
try:
    import faiss
    import numpy as np
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class UserVectorIndex:
    """Manages an isolated vector index for a single user."""

    def __init__(self, user_id: str, dimension: int = 384):
        self.user_id = user_id
        self.dimension = dimension
        self.metadata_file = settings.VECTOR_INDEX_DIR / f"{user_id}_meta.json"
        self.index_file = settings.VECTOR_INDEX_DIR / f"{user_id}.faiss"

        # Chunk entries: list of dicts with {"chunk_id", "document_id", "vector"}
        self.entries: List[Dict[str, Any]] = []
        self._faiss_index = None
        self._load()

    def _load(self) -> None:
        """Load stored metadata and vector index from disk."""
        if self.metadata_file.exists():
            try:
                data = json.loads(self.metadata_file.read_text(encoding="utf-8"))
                self.entries = data.get("entries", [])
            except Exception as e:
                logger.error(f"Error loading vector metadata for user {self.user_id}: {e}")

        if HAS_FAISS and self.index_file.exists():
            try:
                self._faiss_index = faiss.read_index(str(self.index_file))
            except Exception as e:
                logger.error(f"Error loading FAISS index for user {self.user_id}: {e}")

    def save(self) -> None:
        """Persist entries and index to disk."""
        settings.VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        try:
            self.metadata_file.write_text(
                json.dumps({"user_id": self.user_id, "entries": self.entries}, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Error saving vector metadata for user {self.user_id}: {e}")

        if HAS_FAISS and self._faiss_index is not None:
            try:
                faiss.write_index(self._faiss_index, str(self.index_file))
            except Exception as e:
                logger.error(f"Error saving FAISS index for user {self.user_id}: {e}")

    def add_vectors(
        self,
        chunk_ids: List[str],
        document_id: str,
        vectors: List[List[float]],
    ) -> None:
        """Add vectors and their associated chunk identifiers to the index."""
        for cid, vec in zip(chunk_ids, vectors):
            self.entries.append({
                "chunk_id": cid,
                "document_id": document_id,
                "vector": vec,
            })

        if HAS_FAISS and vectors:
            try:
                np_vecs = np.array(vectors, dtype=np.float32)
                # Ensure L2 normalized for cosine inner product
                faiss.normalize_L2(np_vecs)
                if self._faiss_index is None:
                    self._faiss_index = faiss.IndexFlatIP(self.dimension)
                self._faiss_index.add(np_vecs)
            except Exception as e:
                logger.warning(f"FAISS add failed: {e}")

        self.save()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        allowed_document_ids: Optional[List[str]] = None,
        min_similarity: float = 0.35,
    ) -> List[Tuple[str, float]]:
        """Search for top_k nearest chunks.
        Returns list of (chunk_id, similarity_score).
        """
        if not self.entries:
            return []

        results: List[Tuple[str, float]] = []

        # Cosine similarity calculation
        q_norm = math.sqrt(sum(x * x for x in query_vector))
        if q_norm == 0:
            return []

        for entry in self.entries:
            doc_id = entry["document_id"]
            if allowed_document_ids and doc_id not in allowed_document_ids:
                continue

            vec = entry["vector"]
            # Dot product (since normalized)
            dot = sum(q * v for q, v in zip(query_vector, vec))
            v_norm = math.sqrt(sum(v * v for v in vec))
            sim = dot / (q_norm * v_norm) if (q_norm * v_norm) > 0 else 0.0

            if sim >= min_similarity:
                results.append((entry["chunk_id"], float(sim)))

        # Sort descending by similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def delete_document(self, document_id: str) -> None:
        """Purge all vector entries belonging to a deleted document."""
        self.entries = [e for e in self.entries if e["document_id"] != document_id]
        # Rebuild FAISS index if present
        if HAS_FAISS:
            self._faiss_index = None
            if self.entries:
                vecs = [e["vector"] for e in self.entries]
                np_vecs = np.array(vecs, dtype=np.float32)
                faiss.normalize_L2(np_vecs)
                self._faiss_index = faiss.IndexFlatIP(self.dimension)
                self._faiss_index.add(np_vecs)
        self.save()


class VectorStoreService:
    """Multi-tenant vector store service providing strict user isolation."""

    def __init__(self):
        self._user_indices: Dict[str, UserVectorIndex] = {}

    def get_user_index(self, user_id: str) -> UserVectorIndex:
        """Get or initialize the isolated vector index for a user."""
        if user_id not in self._user_indices:
            self._user_indices[user_id] = UserVectorIndex(user_id)
        return self._user_indices[user_id]

    def add_chunks(
        self,
        user_id: str,
        document_id: str,
        chunk_ids: List[str],
        vectors: List[List[float]],
    ) -> None:
        """Store vectors under the user's isolated index."""
        index = self.get_user_index(user_id)
        index.add_vectors(chunk_ids, document_id, vectors)

    def search(
        self,
        user_id: str,
        query_vector: List[float],
        top_k: int = 5,
        allowed_document_ids: Optional[List[str]] = None,
        min_similarity: float = 0.35,
    ) -> List[Tuple[str, float]]:
        """Search chunks only within the specified user's index."""
        index = self.get_user_index(user_id)
        return index.search(
            query_vector=query_vector,
            top_k=top_k,
            allowed_document_ids=allowed_document_ids,
            min_similarity=min_similarity,
        )

    def delete_document_vectors(self, user_id: str, document_id: str) -> None:
        """Delete document vectors from user's isolated index."""
        index = self.get_user_index(user_id)
        index.delete_document(document_id)


# Global singleton instance
vector_store = VectorStoreService()
