# /home/newadmin/swarm-bot/memory/semantic_cache.py
"""Semantic cache for LLM responses using sentence-transformers.

Cache LLM responses based on semantic similarity, not exact string match.
Queries with >92% cosine similarity return cached response instantly.

Expected impact:
- 60-80% hit rate for common/repeated questions
- 95% latency reduction on cache hits (10s → <0.5s)
- 70% cost savings on API calls
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_SIMILARITY_THRESHOLD = 0.92
MAX_CACHE_SIZE = 1000


@dataclass
class CacheEntry:
    """A cached query-response pair.

    Attributes:
        query: Original query text.
        response: Cached response.
        agent: Agent that produced the response.
        embedding: Numpy embedding vector.
        created_at: Unix timestamp.
        hits: Number of times this entry was returned.
    """

    query: str
    response: str
    agent: str
    embedding: np.ndarray
    created_at: float
    hits: int = 0


class SemanticCache:
    """Semantic similarity cache for LLM responses.

    Uses sentence-transformers (all-MiniLM-L6-v2, ~80MB) for embeddings.
    Model is loaded lazily on first use.
    """

    def __init__(self, similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> None:
        self.threshold = similarity_threshold
        self._entries: list[CacheEntry] = []
        self._model: object = None
        self._total_queries = 0
        self._total_hits = 0

    def _load_model(self) -> None:
        """Lazy-load sentence-transformers model."""
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Semantic cache: sentence-transformers model loaded")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed — semantic cache disabled. "
                "Install: pip install sentence-transformers"
            )

    def _embed(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a text string.

        Args:
            text: Text to embed.

        Returns:
            Numpy array embedding, or None if model unavailable.
        """
        self._load_model()
        if self._model is None:
            return None
        try:
            emb = self._model.encode(text, normalize_embeddings=True)
            return np.array(emb, dtype=np.float32)
        except Exception as exc:
            logger.warning("Embedding failed: %s", exc)
            return None

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two normalized vectors.

        Args:
            a: First embedding (normalized).
            b: Second embedding (normalized).

        Returns:
            Similarity score in [0, 1].
        """
        # Vectors are already normalized by SentenceTransformer
        return float(np.dot(a, b))

    def _evict_oldest(self, target_size: int) -> None:
        """Evict oldest entries down to target_size.

        Args:
            target_size: Maximum entries after eviction.
        """
        if len(self._entries) <= target_size:
            return
        self._entries.sort(key=lambda e: e.created_at)
        removed = len(self._entries) - target_size
        self._entries = self._entries[removed:]
        logger.debug("Cache evicted %d old entries", removed)

    def get(self, query: str, agent: str) -> Optional[str]:
        """Check if a semantically similar query was cached.

        Args:
            query: Current query to look up.
            agent: Agent key — only match same-agent responses.

        Returns:
            Cached response string if similarity ≥ threshold, else None.
        """
        self._total_queries += 1

        query_emb = self._embed(query)
        if query_emb is None:
            return None

        best_score = 0.0
        best_entry: Optional[CacheEntry] = None

        for entry in self._entries:
            if entry.agent != agent:
                continue
            score = self._cosine_similarity(query_emb, entry.embedding)
            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry is not None and best_score >= self.threshold:
            best_entry.hits += 1
            self._total_hits += 1
            logger.info(
                "Cache HIT agent=%s similarity=%.3f hits=%d",
                agent, best_score, best_entry.hits,
            )
            return best_entry.response

        logger.debug("Cache MISS agent=%s best_similarity=%.3f", agent, best_score)
        return None

    def set(self, query: str, agent: str, response: str) -> None:
        """Store a query-response pair in the cache.

        Args:
            query: The query to cache.
            agent: Agent that produced the response.
            response: Response to cache.
        """
        query_emb = self._embed(query)
        if query_emb is None:
            return

        # Don't cache errors
        if response.startswith("Error:") or "failed" in response.lower()[:50]:
            return

        entry = CacheEntry(
            query=query,
            response=response,
            agent=agent,
            embedding=query_emb,
            created_at=time.time(),
        )
        self._entries.append(entry)

        if len(self._entries) > MAX_CACHE_SIZE:
            self._evict_oldest(MAX_CACHE_SIZE * 3 // 4)

        logger.debug("Cache SET agent=%s query=%s", agent, query[:60])

    def invalidate_agent(self, agent: str) -> int:
        """Remove all cached entries for a specific agent.

        Args:
            agent: Agent key to invalidate.

        Returns:
            Number of entries removed.
        """
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.agent != agent]
        removed = before - len(self._entries)
        logger.info("Invalidated %d cache entries for agent=%s", removed, agent)
        return removed

    def clear(self) -> None:
        """Clear the entire cache."""
        self._entries.clear()
        self._total_queries = 0
        self._total_hits = 0
        logger.info("Semantic cache cleared")

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a fraction [0, 1].

        Returns:
            Hit rate, or 0.0 if no queries yet.
        """
        if self._total_queries == 0:
            return 0.0
        return self._total_hits / self._total_queries

    def stats(self) -> dict:
        """Return cache statistics.

        Returns:
            Dict with total_queries, total_hits, hit_rate, size, threshold.
        """
        return {
            "total_queries": self._total_queries,
            "total_hits": self._total_hits,
            "hit_rate": round(self.hit_rate, 3),
            "size": len(self._entries),
            "max_size": MAX_CACHE_SIZE,
            "threshold": self.threshold,
        }


# Singleton instance
_cache: SemanticCache | None = None


def get_cache() -> SemanticCache:
    """Return the global SemanticCache singleton."""
    global _cache
    if _cache is None:
        _cache = SemanticCache()
    return _cache
