"""Long-Term Memory — Semantic vector search layer for Legion.

Provides semantic (embedding-based) memory retrieval as an alternative to keyword FTS.
Uses sentence-transformers for embeddings + ChromaDB for vector storage.

Single retrieval entry point: LongTermMemory.search(query, user_id)

Target: 2-tier memory system
  Tier 1 — Working Memory (session, in-process): Core + Recall + Profile
  Tier 2 — Long-Term Memory (persistent, semantic): this module

All functions are async. All calls wrapped in try/except.
Graceful degradation: falls back to FTS-only if ChromaDB unavailable.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Dataclasses ────────────────────────────────────────────────────────────────


@dataclass
class MemoryHit:
    """A single memory retrieval result."""

    text: str
    source: str  # "archival", "episodic", "semantic_cache"
    score: float  # similarity score (0-1, higher = more relevant)
    metadata: dict | None = None


# ── Embedding Model ────────────────────────────────────────────────────────────

_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
_embedder_cache: object | None = None


async def _get_embedder():
    """Lazy-load the embedding model. Returns None if unavailable."""
    global _embedder_cache
    if _embedder_cache is not None:
        return _embedder_cache

    try:
        from sentence_transformers import SentenceTransformer

        _embedder_cache = SentenceTransformer(_EMBEDDING_MODEL)
        logger.info("[LongTermMemory] Embedder loaded: %s", _EMBEDDING_MODEL)
        return _embedder_cache
    except ImportError:
        logger.warning("[LongTermMemory] sentence-transformers not installed — semantic search disabled")
        return None
    except Exception as e:
        logger.warning("[LongTermMemory] Embedder load failed: %s", e)
        return None


# ── ChromaDB Client ───────────────────────────────────────────────────────────

_chroma_client: object | None = None


async def _get_chroma_client():
    """Get or create ChromaDB client. Returns None if unavailable."""
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        data_dir = os.path.expanduser("~/swarm-bot/data/legion_chroma")
        os.makedirs(data_dir, exist_ok=True)

        _chroma_client = chromadb.Client(
            ChromaSettings(
                persist_directory=data_dir,
                anonymized_telemetry=False,
            )
        )
        _chroma_client.heartbeat()
        logger.info("[LongTermMemory] ChromaDB connected: %s", data_dir)
        return _chroma_client
    except ImportError:
        logger.warning("[LongTermMemory] chromadb not installed — semantic search disabled")
        return None
    except Exception as e:
        logger.warning("[LongTermMemory] ChromaDB connect failed: %s", e)
        return None


# ── Collection Helpers ─────────────────────────────────────────────────────────

_COLLECTION_NAME = "legion_long_term_memory"


async def _get_or_create_collection(client):
    """Get or create the memory collection."""
    try:
        coll = client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"description": "Legion long-term semantic memory"},
        )
        return coll
    except Exception as e:
        logger.warning("[LongTermMemory] Collection get/create failed: %s", e)
        return None


# ── Semantic Search ────────────────────────────────────────────────────────────


async def _semantic_search(query: str, user_id: str, limit: int = 5) -> list[MemoryHit]:
    """Search using vector embeddings."""
    results: list[MemoryHit] = []

    embedder = await _get_embedder()
    client = await _get_chroma_client()
    if not embedder or not client:
        return results

    try:
        coll = await _get_or_create_collection(client)
        if not coll:
            return results

        # Embed the query

        query_embedding = embedder.encode(query).tolist()

        # Search
        search_results = coll.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"user_id": str(user_id)},
        )

        if search_results and search_results.get("documents"):
            for doc, metadata, distance in zip(
                search_results["documents"][0],
                search_results.get("metadatas", [[{}]])[0],
                search_results.get("distances", [1.0])[0], strict=False,
            ):
                # ChromaDB returns L2 distance; convert to similarity (0-1, higher = better)
                similarity = max(0.0, 1.0 - (distance / 2.0)) if distance else 0.0
                results.append(
                    MemoryHit(
                        text=doc,
                        source=str(metadata.get("source", "semantic") if metadata else "semantic"),
                        score=similarity,
                        metadata=metadata,
                    )
                )

        logger.debug("[LongTermMemory] Semantic search '%s' -> %d hits", query, len(results))
    except Exception as e:
        logger.warning("[LongTermMemory] Semantic search failed: %s", e)

    return results


# ── FTS Fallback ──────────────────────────────────────────────────────────────


async def _fts_search(query: str, user_id: str, limit: int = 5) -> list[MemoryHit]:
    """Fallback keyword FTS search using MemoryManager."""
    results: list[MemoryHit] = []

    try:
        from core.memory.memory_manager import MemoryManager

        mm = MemoryManager()
        fts_results = await mm.search(query, limit=limit)
        for row in fts_results:
            content = str(row.get("content", "") or row.get("summary", ""))[:320]
            if content.strip():
                results.append(
                    MemoryHit(
                        text=content,
                        source="archival",
                        score=0.5,  # FTS doesn't give similarity scores
                        metadata={"created_at": row.get("created_at", "")},
                    )
                )
    except Exception as e:
        logger.debug("[LongTermMemory] FTS fallback failed: %s", e)

    return results


# ── Episodic Search ───────────────────────────────────────────────────────────


async def _episodic_search(query: str, user_id: str, limit: int = 3) -> list[MemoryHit]:
    """Search episodic store."""
    results: list[MemoryHit] = []

    try:
        from core.memory.episodic_store import get_episodic_store

        store = get_episodic_store()
        episodes = store.recall(str(user_id), query, limit=limit)
        for ep in episodes:
            content = str(ep.get("summary", "") or ep.get("detail", ""))[:320]
            if content.strip():
                results.append(
                    MemoryHit(
                        text=content,
                        source="episodic",
                        score=0.5,
                        metadata={"ts": ep.get("ts", ""), "episode_type": ep.get("episode_type", "")},
                    )
                )
    except Exception as e:
        logger.debug("[LongTermMemory] Episodic search failed: %s", e)

    return results


# ── Main Class ────────────────────────────────────────────────────────────────


async def search_long_term_memory(
    query: str,
    user_id: str,
    limit: int = 5,
    include_episodic: bool = True,
) -> list[MemoryHit]:
    """Search long-term memory using semantic similarity.

    This is the primary entry point for Tier-2 (long-term) memory retrieval.

    Strategy:
    1. Try semantic (vector) search first — better quality matches
    2. Fall back to FTS if semantic fails or embedder unavailable
    3. Include episodic memories if requested

    Args:
        query: The search query (natural language)
        user_id: User ID for per-user isolation
        limit: Maximum number of results to return
        include_episodic: Whether to also search episodic store

    Returns:
        List of MemoryHit objects, sorted by score descending
    """
    logger.debug("[LongTermMemory] search: query='%s', user_id=%s, limit=%d", query[:50], user_id, limit)

    if not query or not user_id:
        return []

    all_hits: list[MemoryHit] = []

    # Primary: semantic search
    semantic_hits = await _semantic_search(query, user_id, limit=limit)
    all_hits.extend(semantic_hits)

    # Secondary: FTS fallback (ensure we have results even if semantic failed)
    if len(all_hits) < limit:
        fts_hits = await _fts_search(query, user_id, limit=limit)
        # Deduplicate against semantic results
        existing_texts = {hit.text[:100] for hit in all_hits}
        for hit in fts_hits:
            if hit.text[:100] not in existing_texts and len(all_hits) < limit:
                all_hits.append(hit)

    # Tertiary: episodic (optional)
    if include_episodic and len(all_hits) < limit:
        episodic_hits = await _episodic_search(query, user_id, limit=limit)
        existing_texts = {hit.text[:100] for hit in all_hits}
        for hit in episodic_hits:
            if hit.text[:100] not in existing_texts and len(all_hits) < limit:
                all_hits.append(hit)

    # Sort by score descending, then trim to limit
    all_hits.sort(key=lambda h: h.score, reverse=True)
    results = all_hits[:limit]

    logger.debug("[LongTermMemory] Returning %d results (from %d total hits)", len(results), len(all_hits))
    return results


# ── Store Memory (for future semantic retrieval) ──────────────────────────────


async def store_long_term_memory(
    text: str,
    user_id: str,
    source: str = "agent",
    metadata: dict | None = None,
) -> bool:
    """Store a memory in the long-term semantic store.

    Call this after important interactions to enable future semantic retrieval.

    Args:
        text: The memory text to store
        user_id: User ID for per-user isolation
        source: Source label (e.g., "archival", "episodic", "manual")
        metadata: Additional metadata dict

    Returns:
        True if stored successfully, False otherwise
    """
    try:
        embedder = await _get_embedder()
        client = await _get_chroma_client()
        if not embedder or not client:
            return False

        coll = await _get_or_create_collection(client)
        if not coll:
            return False


        embedding = embedder.encode(text).tolist()
        meta = {
            "user_id": str(user_id),
            "source": source,
            **(metadata or {}),
        }

        coll.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta],
            ids=[f"{user_id}_{source}_{hash(text) % 1000000}"],
        )

        logger.debug("[LongTermMemory] Stored: %s... (source=%s)", text[:50], source)
        return True

    except Exception as e:
        logger.warning("[LongTermMemory] store failed: %s", e)
        return False


# ── Deduplicate utility ───────────────────────────────────────────────────────


def deduplicate_hits(hits: list[MemoryHit], body_length: int = 100) -> list[MemoryHit]:
    """Deduplicate hits by first N characters of text."""
    seen: set[str] = set()
    result: list[MemoryHit] = []
    for hit in hits:
        key = hit.text[:body_length]
        if key not in seen:
            seen.add(key)
            result.append(hit)
    return result


# ── Convenience wrapper class ─────────────────────────────────────────────────


class LongTermMemory:
    """Shorthand class for semantic memory search.

    Usage:
        hits = await LongTermMemory().search("what's my main project", "bashara")
    """

    async def search(self, query: str, user_id: str = "bashara", limit: int = 5) -> list[MemoryHit]:
        """Search long-term memory using semantic similarity."""
        return await search_long_term_memory(query, user_id, limit)

    async def store(self, text: str, user_id: str = "bashara", source: str = "agent") -> bool:
        """Store a memory for future semantic retrieval."""
        return await store_long_term_memory(text, user_id, source)
