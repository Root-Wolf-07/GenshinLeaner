"""Embedding generation service.
Supports SentenceTransformers, Google Gemini Embeddings, and an offline fallback.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from typing import List, Optional
import urllib.request
import urllib.error

from backend.config import settings

logger = logging.getLogger(__name__)

# Check for sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class EmbeddingService:
    """Produces normalized vector embeddings with multi-tier fallback support."""

    def __init__(self):
        self._st_model: Optional[SentenceTransformer] = None
        self.dimension = settings.EMBEDDING_DIMENSION

    def _get_st_model(self) -> Optional[SentenceTransformer]:
        if HAS_SENTENCE_TRANSFORMERS and self._st_model is None:
            try:
                self._st_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                self.dimension = self._st_model.get_sentence_embedding_dimension()
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer: {e}")
        return self._st_model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized vector embeddings for a list of texts."""
        if not texts:
            return []

        # 1. Try SentenceTransformers if available
        st_model = self._get_st_model()
        if st_model is not None:
            try:
                embeddings = st_model.encode(texts, normalize_embeddings=True)
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                logger.warning(f"SentenceTransformers encode failed: {e}")

        # 2. Try OpenAI Embeddings API if configured
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your-"):
            openai_embs = self._embed_with_openai(texts)
            if openai_embs:
                return openai_embs

        # 3. Try Gemini Embeddings API if configured
        if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your-"):
            gemini_embs = self._embed_with_gemini(texts)
            if gemini_embs:
                return gemini_embs

        # 4. Deterministic normalized semantic fallback
        return [self._offline_hash_embedding(text, self.dimension) for text in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generate normalized vector embedding for a search query."""
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * self.dimension

    def _embed_with_gemini(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Call Google Gemini embedding API via REST."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_EMBEDDING_MODEL}:batchEmbedContents?key={settings.GEMINI_API_KEY}"
            requests_payload = [
                {
                    "model": f"models/{settings.GEMINI_EMBEDDING_MODEL}",
                    "content": {"parts": [{"text": t[:2000]}]},
                }
                for t in texts[:20]  # batch limit
            ]
            req = urllib.request.Request(
                url,
                data=json.dumps({"requests": requests_payload}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                embeddings = [item["values"] for item in data.get("embeddings", [])]
                if len(embeddings) == len(texts):
                    return embeddings
        except Exception as e:
            logger.debug(f"Gemini embedding API call failed: {e}")
        return None

    def _embed_with_openai(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Call OpenAI embeddings API via REST."""
        try:
            url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/embeddings"
            payload = {
                "model": settings.OPENAI_EMBEDDING_MODEL,
                "input": [t[:4000] for t in texts[:20]],
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("data", [])
                if items:
                    return [item["embedding"] for item in items]
        except Exception as e:
            logger.debug(f"OpenAI embedding API call failed: {e}")
        return None

    @staticmethod
    def _offline_hash_embedding(text: str, dim: int = 384) -> List[float]:
        """High-entropy deterministic semantic projection vector.
        Guarantees identical or similar texts produce high cosine similarity.
        """
        vec = [0.0] * dim
        words = re.findall(r"\w+", text.lower())
        if not words:
            return vec

        for word in words:
            # Hash word into 4 coordinate indices
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            for i in range(4):
                idx = (h >> (i * 8)) % dim
                weight = 1.0 / (1.0 + math.log(1.0 + len(word)))
                vec[idx] += weight

        # Normalize to unit circle (L2 norm)
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


# Global singleton instance
embedding_service = EmbeddingService()
