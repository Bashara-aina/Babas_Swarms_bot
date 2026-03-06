# /home/newadmin/swarm-bot/memory/memory_manager.py
"""Persistent hybrid memory: short-term (in-memory/Redis) + long-term (ChromaDB).

Backends:
- ChromaDB (local persistent file) — semantic vector store
- Redis (optional) — fast short-term cache with TTL
- In-memory dict — fallback when Redis is unavailable

Usage:
    from memory.memory_manager import MemoryManager
    mem = MemoryManager()
    await mem.store("thread_id", "coding", "my task", "the result")
    chunks = await mem.recall("similar task query", thread_id="thread_id")
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MEMORY_DB_PATH = str(Path(__file__).parent.parent / "memory_db")
COLLECTION_NAME = "swarm_memory"
MAX_RESULT_CHARS = 500          # Truncate stored results to save space
SHORT_TERM_TTL = 3600           # 1 hour in-memory TTL
MAX_IN_MEMORY = 500             # Max short-term entries without Redis


@dataclass
class MemoryChunk:
    """A recalled memory fragment.

    Attributes:
        thread_id: Source thread.
        agent: Agent that produced this.
        task: Original task (truncated).
        result: Agent result (truncated).
        timestamp: Unix timestamp of storage.
        distance: Similarity distance (lower = more similar).
    """

    thread_id: str
    agent: str
    task: str
    result: str
    timestamp: float
    distance: float = 0.0


class MemoryManager:
    """Hybrid persistent memory manager.

    Initialises lazily — ChromaDB and Redis clients are created on first use.
    Gracefully degrades if either backend is unavailable.
    """

    def __init__(self) -> None:
        self._chroma: object = None
        self._collection: object = None
        self._redis: object = None
        self._short_term: dict[str, dict] = {}   # Fallback in-memory store
        self._initialized = False

    def _init_chroma(self) -> None:
        """Initialise ChromaDB persistent client."""
        try:
            import chromadb
            Path(MEMORY_DB_PATH).mkdir(parents=True, exist_ok=True)
            self._chroma = chromadb.PersistentClient(path=MEMORY_DB_PATH)
            self._collection = self._chroma.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB initialized at %s", MEMORY_DB_PATH)
        except ImportError:
            logger.warning("chromadb not installed — long-term memory disabled")
        except Exception as exc:
            logger.warning("ChromaDB init failed: %s — long-term memory disabled", exc)

    def _init_redis(self) -> None:
        """Initialise Redis client (optional)."""
        try:
            import redis as redis_lib
            r = redis_lib.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True,
                socket_connect_timeout=2,
            )
            r.ping()
            self._redis = r
            logger.info("Redis connected for short-term memory")
        except Exception as exc:
            logger.info("Redis unavailable (%s) — using in-memory fallback", exc)

    def _ensure_init(self) -> None:
        """Lazy initialisation on first use."""
        if not self._initialized:
            self._init_chroma()
            self._init_redis()
            self._initialized = True

    # ── Short-Term Memory ──────────────────────────────────────────────────

    def _st_key(self, thread_id: str) -> str:
        return f"swarm:thread:{thread_id}"

    def _st_store(self, thread_id: str, turn: dict) -> None:
        """Store a turn in short-term memory (Redis or dict)."""
        if self._redis:
            key = self._st_key(thread_id)
            existing = self._redis.get(key)
            turns = json.loads(existing) if existing else []
            turns.append(turn)
            turns = turns[-10:]   # Keep last 10 per thread
            self._redis.setex(key, SHORT_TERM_TTL, json.dumps(turns))
        else:
            if thread_id not in self._short_term:
                self._short_term[thread_id] = []
            self._short_term[thread_id].append(turn)
            self._short_term[thread_id] = self._short_term[thread_id][-10:]

            # Evict oldest thread if over limit
            if len(self._short_term) > MAX_IN_MEMORY:
                oldest = min(self._short_term, key=lambda k: self._short_term[k][-1]["ts"])
                del self._short_term[oldest]

    def _st_get(self, thread_id: str, last_n: int = 5) -> list[dict]:
        """Retrieve recent turns from short-term memory."""
        if self._redis:
            key = self._st_key(thread_id)
            raw = self._redis.get(key)
            turns = json.loads(raw) if raw else []
        else:
            turns = self._short_term.get(thread_id, [])
        return turns[-last_n:]

    # ── Long-Term Memory (ChromaDB) ────────────────────────────────────────

    def _make_doc_id(self, thread_id: str, task: str) -> str:
        """Generate a stable document ID from thread + task."""
        payload = f"{thread_id}:{task}:{time.time()}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    # ── Public API ─────────────────────────────────────────────────────────

    async def store(
        self,
        thread_id: str,
        agent: str,
        task: str,
        result: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Store a conversation turn in both short-term and long-term memory.

        Args:
            thread_id: Conversation thread identifier.
            agent: Agent key that produced the result.
            task: User task (will be stored verbatim).
            result: Agent output (truncated to MAX_RESULT_CHARS).
            metadata: Optional extra metadata dict.
        """
        self._ensure_init()

        turn = {
            "agent": agent,
            "task": task[:300],
            "result": result[:MAX_RESULT_CHARS],
            "ts": time.time(),
        }
        self._st_store(thread_id, turn)

        if self._collection is None:
            return

        doc_text = f"Task: {task}\nResult: {result[:MAX_RESULT_CHARS]}"
        meta = {
            "thread_id": thread_id,
            "agent": agent,
            "timestamp": time.time(),
        }
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        doc_id = self._make_doc_id(thread_id, task)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._collection.add(
                documents=[doc_text],
                metadatas=[meta],
                ids=[doc_id],
            ),
        )
        logger.debug("Stored memory %s in thread %s", doc_id, thread_id)

    async def recall(
        self,
        query: str,
        thread_id: Optional[str] = None,
        top_k: int = 3,
    ) -> list[MemoryChunk]:
        """Semantic recall: find memory chunks similar to a query.

        Args:
            query: Natural language query to search for.
            thread_id: Optional filter to a specific thread.
            top_k: Maximum number of results.

        Returns:
            List of MemoryChunk sorted by similarity.
        """
        self._ensure_init()

        if self._collection is None:
            return []

        where = {"thread_id": thread_id} if thread_id else None

        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(
                None,
                lambda: self._collection.query(
                    query_texts=[query],
                    n_results=min(top_k, 10),
                    where=where,
                ),
            )
        except Exception as exc:
            logger.warning("ChromaDB recall failed: %s", exc)
            return []

        chunks: list[MemoryChunk] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            # Parse task/result back from document
            parts = doc.split("\nResult: ", 1)
            task_part = parts[0].removeprefix("Task: ")
            result_part = parts[1] if len(parts) > 1 else ""

            chunks.append(
                MemoryChunk(
                    thread_id=meta.get("thread_id", ""),
                    agent=meta.get("agent", ""),
                    task=task_part,
                    result=result_part,
                    timestamp=float(meta.get("timestamp", 0)),
                    distance=dist,
                )
            )

        return chunks

    def get_short_term_context(self, thread_id: str, last_n: int = 5) -> str:
        """Get recent conversation turns as formatted string.

        Args:
            thread_id: Thread to retrieve.
            last_n: Number of recent turns to include.

        Returns:
            Formatted context string for injection into prompts.
        """
        self._ensure_init()
        turns = self._st_get(thread_id, last_n)
        if not turns:
            return ""

        lines = ["## Previous conversation in this thread:\n"]
        for t in turns:
            import datetime
            ts = datetime.datetime.fromtimestamp(t["ts"]).strftime("%H:%M")
            lines.append(f"[{ts}] {t['agent'].upper()}: {t['task'][:120]}")
            lines.append(f"Response: {t['result']}\n")
        return "\n".join(lines)

    async def get_semantic_context(self, query: str, thread_id: Optional[str] = None) -> str:
        """Retrieve semantically relevant past exchanges for a query.

        Args:
            query: Current task to find similar history for.
            thread_id: Optional thread filter.

        Returns:
            Formatted context string, empty if nothing relevant.
        """
        chunks = await self.recall(query, thread_id=thread_id, top_k=3)
        if not chunks:
            return ""

        lines = ["## Relevant past context (semantic recall):\n"]
        for chunk in chunks:
            if chunk.distance < 0.5:   # Only include close matches
                lines.append(f"[{chunk.agent}] {chunk.task[:100]}")
                lines.append(f"→ {chunk.result[:200]}\n")
        return "\n".join(lines) if len(lines) > 1 else ""

    def thread_stats(self) -> dict[str, int]:
        """Return thread turn counts from short-term memory.

        Returns:
            Dict mapping thread_id → turn count.
        """
        self._ensure_init()
        if self._redis:
            pattern = "swarm:thread:*"
            keys = self._redis.keys(pattern)
            stats = {}
            for key in keys:
                tid = key.removeprefix("swarm:thread:")
                raw = self._redis.get(key)
                turns = json.loads(raw) if raw else []
                stats[tid] = len(turns)
            return stats
        return {k: len(v) for k, v in self._short_term.items()}


# Singleton instance
_memory: MemoryManager | None = None


def get_memory() -> MemoryManager:
    """Return the global MemoryManager singleton."""
    global _memory
    if _memory is None:
        _memory = MemoryManager()
    return _memory
