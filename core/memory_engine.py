"""Memory Engine v2 — Three-tier memory wrapper.

Architecture:
  Tier 1 — Working Memory (deque, last 20 exchanges)
    └─ auto-summarize at 15k tokens → compressed summary

  Tier 2 — Episodic Memory (SQLite at data/memory.db)
    └─ stores: timestamp, tags, sentiment, importance, content
    └─ query by time range, sentiment, tags

  Tier 3 — Permanent Memory (chromadb vector store)
    └─ auto-extract facts about Bashara
    └─ semantic search by meaning, not keywords

All methods are async. Use MemoryEngine() as the single interface.
"""

from __future__ import annotations

import logging
import re
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiosqlite
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MEMORY_DB = DATA_DIR / "memory.db"
CHROMA_DIR = DATA_DIR / "legion_chroma"

# ── Constants ──────────────────────────────────────────────────────────────

WORKING_MAX = 20  # Last 20 exchanges before auto-summarize
TOKEN_THRESHOLD = 15_000  # Auto-summarize when tokens > this
EMBED_MODEL = "sentence-transformers/all-mpnet-base-v2"  # Unified with agent_registry


# ── Helpers ─────────────────────────────────────────────────────────────────


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars/token."""
    return len(text) // 4


def _jst_now() -> datetime:
    """Current time in JST."""
    import pytz

    return datetime.now(pytz.timezone("Asia/Tokyo"))


# ── Tier 1 — Working Memory ──────────────────────────────────────────────────


class WorkingMemory:
    """In-memory deque — last 20 exchanges, auto-summarize at 15k tokens."""

    def __init__(self) -> None:
        self._buffer: deque[dict[str, Any]] = deque(maxlen=WORKING_MAX)
        self._summary: str = ""
        self._total_tokens: int = 0

    def push(self, turn: dict[str, Any]) -> None:
        """Add a turn (user/assistant exchange)."""
        self._buffer.append(turn)
        self._total_tokens += _estimate_tokens(f"{turn.get('user', '')} {turn.get('assistant', '')}")

    def get_recent(self, n: int = 10) -> list[dict[str, Any]]:
        """Return last N turns."""
        return list(self._buffer)[-n:]

    def should_summarize(self) -> bool:
        """Check if total tokens exceed threshold."""
        return self._total_tokens > TOKEN_THRESHOLD and not self._summary

    def get_context_window(self, last_n: int = 10) -> list[dict[str, Any]]:
        """Return recent context for injection."""
        if self._summary:
            return [{"role": "system", "content": f"[SUMMARY]\n{self._summary}"}] + [
                {"role": "user", "content": t.get("user", "")} for t in list(self._buffer)[-last_n:]
            ]
        return [{"role": "user", "content": t.get("user", "")} for t in list(self._buffer)[-last_n:]]

    def summarize(self, summary: str) -> None:
        """Store compressed summary, clear buffer."""
        self._summary = summary
        self._buffer.clear()
        self._total_tokens = 0
        logger.info("[WorkingMemory] Summary stored (%d chars)", len(summary))

    def get_stats(self) -> dict[str, Any]:
        return {
            "tier": "working",
            "buffer_size": len(self._buffer),
            "total_tokens": self._total_tokens,
            "has_summary": bool(self._summary),
        }


# ── Tier 2 — Episodic Memory (SQLite) ──────────────────────────────────────


class EpisodicMemory:
    """SQLite-backed episodic memory — searchable by time, tags, sentiment."""

    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        user_id TEXT,
        content TEXT NOT NULL,
        sentiment TEXT,
        importance INTEGER DEFAULT 5,
        tags TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_episodes_timestamp ON episodes(timestamp);
    CREATE INDEX IF NOT EXISTS idx_episodes_user_id ON episodes(user_id);
    CREATE INDEX IF NOT EXISTS idx_episodes_sentiment ON episodes(sentiment);
    """

    INSERT_SQL = """
    INSERT INTO episodes (timestamp, user_id, content, sentiment, importance, tags)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    SEARCH_SQL = """
    SELECT * FROM episodes
    WHERE timestamp >= ? AND timestamp <= ?
    ORDER BY timestamp DESC
    LIMIT ?
    """

    SEARCH_TAGS_SQL = """
    SELECT * FROM episodes
    WHERE tags LIKE ? AND timestamp >= ? AND timestamp <= ?
    ORDER BY timestamp DESC
    LIMIT ?
    """

    def __init__(self, db_path: Path = MEMORY_DB) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: aiosqlite.Connection | None = None
        self._init_done = False

    async def _ensure_init(self) -> None:
        if self._init_done:
            return
        conn = await aiosqlite.connect(str(self.db_path))
        await conn.executescript(self.CREATE_TABLE)
        await conn.commit()
        self._conn = conn
        self._init_done = True

    @asynccontextmanager
    async def _get_conn(self):
        await self._ensure_init()
        yield self._conn

    async def store(
        self,
        content: str,
        user_id: str | None = None,
        sentiment: str = "neutral",
        importance: int = 5,
        tags: list[str] | None = None,
        timestamp: str | None = None,
    ) -> int:
        """Store an episode. Returns row id."""
        await self._ensure_init()
        ts = timestamp or _jst_now().isoformat()
        tag_str = ",".join(tags) if tags else ""
        async with self._get_conn() as conn:
            cursor = await conn.execute(
                self.INSERT_SQL,
                (ts, user_id, content, sentiment, importance, tag_str),
            )
            await conn.commit()
            return cursor.lastrowid or 0

    async def search(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search episodes by time range and/or tags."""
        await self._ensure_init()
        start = (start_time or _jst_now() - timedelta(days=7)).isoformat()
        end = (end_time or _jst_now()).isoformat()

        async with self._get_conn() as conn:
            if tags:
                tag_pattern = f"%{','.join(tags)}%"
                cursor = await conn.execute(self.SEARCH_TAGS_SQL, (tag_pattern, start, end, limit))
            else:
                cursor = await conn.execute(self.SEARCH_SQL, (start, end, limit))
            rows = await cursor.fetchall()
            cols = [desc[0] for desc in cursor.description or []]
            return [dict(zip(cols, row, strict=False)) for row in rows]

    async def get_recent(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent episodes for a specific user."""
        await self._ensure_init()
        async with self._get_conn() as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM episodes
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
            cols = [desc[0] for desc in cursor.description or []]
            return [dict(zip(cols, row, strict=False)) for row in rows]

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._init_done = False

    def get_stats(self) -> dict[str, Any]:
        return {
            "tier": "episodic",
            "db_path": str(self.db_path),
            "db_exists": self.db_path.exists(),
        }


# ── Tier 3 — Permanent Memory (ChromaDB) ────────────────────────────────────


class PermanentMemory:
    """ChromaDB-backed semantic memory — auto-extract facts about Bashara."""

    COLLECTION_NAME = "legion_permanent"

    def __init__(self, persist_dir: Path = CHROMA_DIR) -> None:
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client: chromadb.PersistentClient | None = None
        self._collection: chromadb.Collection | None = None

    def _get_collection(self) -> chromadb.Collection:
        if self._collection is None:
            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Legion's permanent memory about Bashara"},
            )
        return self._collection

    async def store_fact(
        self,
        fact: str,
        user_id: str = "bashara",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a fact about Bashara in vector store."""
        collection = self._get_collection()
        doc_id = f"{user_id}_{int(time.time() * 1000)}"
        meta = {**(metadata or {}), "user_id": user_id}
        collection.add(
            ids=[doc_id],
            documents=[fact],
            metadatas=[meta],
        )
        logger.debug("[PermanentMemory] Fact stored: %s", fact[:60])
        return doc_id

    async def search_facts(
        self,
        query: str,
        user_id: str = "bashara",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Semantic search for facts."""
        collection = self._get_collection()
        try:
            results = collection.query(
                query_texts=[query],
                where={"user_id": user_id},
                n_results=limit,
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]
            return [{"id": ids[i], "content": docs[i], "metadata": metas[i]} for i in range(len(docs))]
        except Exception as exc:
            logger.warning("[PermanentMemory] Search failed: %s", exc)
            return []

    async def extract_and_store_facts(
        self,
        text: str,
        user_id: str = "bashara",
    ) -> list[str]:
        """Use LLM to extract facts from text and store them.

        This is called after LLM responses to capture new facts about Bashara.
        Returns list of extracted fact strings.
        """
        # Simple extraction — split on sentences, store each as a fact
        # In production, this would use MiniMax to extract structured facts
        facts: list[str] = []
        sentences = re.split(r"[.!?]+", text)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 20 and len(sent) < 500 and any(keyword in sent.lower() for keyword in ["i ", "i'm ", "i am ", "my ", "i've ", "i'll "]):
                    await self.store_fact(
                        sent,
                        user_id=user_id,
                        metadata={"source": "conversation", "type": "bashara_fact"},
                    )
                    facts.append(sent)
        return facts

    def get_stats(self) -> dict[str, Any]:
        collection = self._get_collection()
        return {
            "tier": "permanent",
            "collection": self.COLLECTION_NAME,
            "persist_dir": str(self.persist_dir),
            "approx_count": collection.count(),
        }


# ── Unified Memory Engine ────────────────────────────────────────────────────


class MemoryEngine:
    """
    Three-tier memory wrapper.

    Interface:
        async store(turn: dict) -> None
        async search(query: str, tier: str = "all", limit: int = 5) -> list[dict]
        async get_context_window(user_id: str, last_n: int = 10) -> list[dict]
        async auto_summarize_if_needed() -> str
        def get_stats() -> dict
    """

    def __init__(self) -> None:
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.permanent = PermanentMemory()
        self._user_id: str = "bashara"

    def set_user_id(self, user_id: str) -> None:
        self._user_id = user_id

    async def store(self, turn: dict[str, Any]) -> None:
        """Store a conversation turn in all applicable tiers."""
        # Tier 1 — Working Memory
        self.working.push(turn)

        # Tier 2 — Episodic Memory (store if has content)
        content = f"User: {turn.get('user', '')} | Assistant: {turn.get('assistant', '')}"
        if len(content) > 10:
            await self.episodic.store(
                content=content,
                user_id=turn.get("user_id") or self._user_id,
                sentiment=turn.get("emotion_state", "neutral"),
                importance=turn.get("importance", 5),
            )

        # Tier 3 — Permanent Memory (extract facts from assistant response)
        assistant_msg = turn.get("assistant", "")
        if assistant_msg and len(assistant_msg) > 30:
            await self.permanent.extract_and_store_facts(
                assistant_msg,
                user_id=turn.get("user_id") or self._user_id,
            )

    async def search(
        self,
        query: str,
        tier: str = "all",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search memory across tiers.

        Args:
            query: Search query string
            tier: "working" | "episodic" | "permanent" | "all"
            limit: Max results per tier
        """
        results: list[dict[str, Any]] = []

        if tier in ("working", "all"):
            # Working memory: simple text match on recent messages
            for turn in self.working.get_recent(limit):
                content = f"{turn.get('user', '')} {turn.get('assistant', '')}"
                if query.lower() in content.lower():
                    results.append({**turn, "tier": "working"})

        if tier in ("episodic", "all"):
            # Episodic: semantic-like search via SQL
            try:
                eps = await self.episodic.search(limit=limit)
                for ep in eps:
                    if query.lower() in ep.get("content", "").lower():
                        results.append({**ep, "tier": "episodic"})
            except Exception as exc:
                logger.warning("[MemoryEngine] Episodic search failed: %s", exc)

        if tier in ("permanent", "all"):
            # Permanent: actual vector search
            try:
                facts = await self.permanent.search_facts(query, limit=limit)
                results.extend([{**f, "tier": "permanent"} for f in facts])
            except Exception as exc:
                logger.warning("[MemoryEngine] Permanent search failed: %s", exc)

        return results[:limit]

    async def get_context_window(
        self,
        user_id: str,
        last_n: int = 10,
    ) -> list[dict[str, Any]]:
        """Get recent context window for injection into LLM prompt."""
        self.set_user_id(user_id)

        # Start with working memory
        context = self.working.get_context_window(last_n)

        # Add episodic memory
        try:
            eps = await self.episodic.get_recent(user_id, limit=5)
            for ep in eps:
                context.append(
                    {
                        "role": "system",
                        "content": f"[EPISODIC] {ep.get('content', '')}",
                    }
                )
        except Exception as exc:
            logger.warning("[MemoryEngine] Episodic context fetch failed: %s", exc)

        return context

    async def auto_summarize_if_needed(self) -> str:
        """Check if working memory needs summarization, do it."""
        if not self.working.should_summarize():
            return ""

        # Build a summary prompt for MiniMax
        recent = self.working.get_recent(WORKING_MAX)
        if not recent:
            return ""

        summary_prompt = (
            "Summarize the following conversation concisely, preserving key facts, "
            "decisions, and follow-up items. Keep it under 500 tokens:\n\n"
            + "\n".join(f"User: {t.get('user', '')}\nAssistant: {t.get('assistant', '')}" for t in recent)
        )
        # In production, this would call MiniMax to actually summarize
        # For now, store a placeholder
        self.working.summarize(f"[AUTO-SUMMARY PLACEHOLDER]\n{summary_prompt[:500]}")
        return summary_prompt[:200]

    def get_stats(self) -> dict[str, Any]:
        return {
            "working": self.working.get_stats(),
            "episodic": self.episodic.get_stats(),
            "permanent": self.permanent.get_stats(),
        }


# ── Module-level convenience wrappers ────────────────────────────────────────
# These provide a simple read_memory(user_id, query) / write_memory(user_id, content)
# interface expected by callers, delegating to a shared MemoryEngine instance.

_engine_instance: MemoryEngine | None = None


def _get_engine() -> MemoryEngine:
    """Get or create the shared MemoryEngine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MemoryEngine()
    return _engine_instance


async def read_memory(user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search memory for a user. Convenience wrapper around MemoryEngine.search().

    Args:
        user_id: Telegram user ID string.
        query: Search query string.
        limit: Maximum results to return.

    Returns:
        List of memory result dicts with 'tier' field indicating source.
    """
    engine = _get_engine()
    engine.set_user_id(user_id)
    return await engine.search(query, tier="all", limit=limit)


async def write_memory(user_id: str, content: str, **kwargs: Any) -> None:
    """
    Store a memory entry for a user. Convenience wrapper around MemoryEngine.store().

    Args:
        user_id: Telegram user ID string.
        content: The content to store (will be stored as a conversation turn).
        **kwargs: Additional fields passed to the turn dict (e.g., sentiment, importance).
    """
    engine = _get_engine()
    turn: dict[str, Any] = {"user": content, "assistant": "", "user_id": user_id, **kwargs}
    await engine.store(turn)
