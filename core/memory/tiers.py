from __future__ import annotations

import aiosqlite
import json
from pathlib import Path
from typing import Any

MEMORY_ROOT = Path.home() / ".legionswarm" / "memory"
MEMORY_ROOT.mkdir(parents=True, exist_ok=True)


class CoreMemory:
    """Always-in-context high-priority memory (small and editable)."""

    MAX_CHARS = 4000
    path = MEMORY_ROOT / "core_memory.json"

    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

    def _save(self) -> None:
        # Enforce a rough cap by truncating values if total chars grows too large.
        total_chars = sum(len(k) + len(v) for k, v in self._data.items())
        if total_chars >= self.MAX_CHARS:
            trimmed: dict[str, str] = {}
            running = 0
            for key, value in self._data.items():
                remaining = self.MAX_CHARS - running
                if remaining <= 0:
                    break
                clipped = value[: max(0, remaining - len(key))]
                trimmed[key] = clipped
                running += len(key) + len(clipped)
            self._data = trimmed
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value
        self._save()

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
        self._save()

    def to_prompt_block(self) -> str:
        if not self._data:
            return ""
        lines = ["[CORE MEMORY — always remember these]"]
        for key, value in self._data.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    def all(self) -> dict[str, str]:
        return dict(self._data)


class ArchivalMemory:
    """Long-term searchable memory backed by SQLite + FTS5."""

    db_path = MEMORY_ROOT / "archival.db"

    def __init__(self) -> None:
        self.conn: aiosqlite.Connection | None = None

    async def _ensure_connection(self) -> aiosqlite.Connection:
        if self.conn is None:
            self.conn = await aiosqlite.connect(str(self.db_path))
        return self.conn

    async def _init_db(self) -> None:
        conn = await self._ensure_connection()
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                summary TEXT,
                tags TEXT,
                importance REAL DEFAULT 0.5,
                created_at TEXT DEFAULT (datetime('now')),
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                source TEXT
            )
            """
        )
        await conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
            USING fts5(content, summary, tags, content='memories', content_rowid='id')
            """
        )
        await conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content, summary, tags)
                VALUES (new.id, new.content, new.summary, new.tags);
            END
            """
        )
        await conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content, summary, tags)
                VALUES('delete', old.id, old.content, old.summary, old.tags);
            END
            """
        )
        await conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content, summary, tags)
                VALUES('delete', old.id, old.content, old.summary, old.tags);
                INSERT INTO memories_fts(rowid, content, summary, tags)
                VALUES (new.id, new.content, new.summary, new.tags);
            END
            """
        )
        await conn.commit()

    async def store(
        self,
        content: str,
        summary: str = "",
        tags: list[str] | None = None,
        importance: float = 0.5,
        source: str = "conversation",
    ) -> int:
        conn = await self._ensure_connection()
        tags_str = ",".join(tags or [])
        cur = await conn.execute(
            """
            INSERT INTO memories (content, summary, tags, importance, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (content, summary, tags_str, importance, source),
        )
        await conn.commit()
        return int(cur.lastrowid)

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        conn = await self._ensure_connection()
        rows = await conn.execute(
            """
            SELECT m.id, m.content, m.summary, m.tags, m.importance,
                   m.created_at, m.access_count
            FROM memories m
            JOIN memories_fts fts ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY m.importance DESC, m.last_accessed DESC
            LIMIT ?
            """,
            (query, limit),
        )
        rows_data = await rows.fetchall()

        for row in rows_data:
            await conn.execute(
                """
                UPDATE memories
                SET access_count = access_count + 1,
                    last_accessed = datetime('now')
                WHERE id = ?
                """,
                (row[0],),
            )
        await conn.commit()

        return [
            {
                "id": row[0],
                "content": row[1],
                "summary": row[2] or "",
                "tags": (row[3] or "").split(",") if row[3] else [],
                "importance": float(row[4] or 0.5),
                "created_at": row[5] or "",
                "access_count": int(row[6] or 0),
            }
            for row in rows_data
        ]

    async def get_recent(self, n: int = 20) -> list[dict[str, Any]]:
        conn = await self._ensure_connection()
        rows = await conn.execute(
            """
            SELECT id, content, summary, tags, importance, created_at
            FROM memories
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (n,),
        )
        rows_data = await rows.fetchall()
        return [
            {
                "id": row[0],
                "content": row[1],
                "summary": row[2] or "",
                "tags": (row[3] or "").split(",") if row[3] else [],
                "importance": float(row[4] or 0.5),
                "created_at": row[5] or "",
            }
            for row in rows_data
        ]

    async def total_count(self) -> int:
        conn = await self._ensure_connection()
        row = await conn.execute("SELECT COUNT(*) FROM memories").fetchone()
        return int(row[0]) if row else 0

    async def close(self) -> None:
        """Close the SQLite connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None


class RecallMemory:
    """Permanent conversation history for context and pattern analysis."""

    db_path = MEMORY_ROOT / "recall.db"

    def __init__(self) -> None:
        self.conn: aiosqlite.Connection | None = None

    async def _ensure_connection(self) -> aiosqlite.Connection:
        if self.conn is None:
            self.conn = await aiosqlite.connect(str(self.db_path))
        return self.conn

    async def _init_db(self) -> None:
        conn = await self._ensure_connection()
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_used TEXT,
                emotion_state TEXT,
                timestamp TEXT DEFAULT (datetime('now')),
                session_id TEXT,
                importance REAL DEFAULT 0.5
            )
            """
        )
        await conn.commit()

    async def add(
        self,
        role: str,
        content: str,
        agent_used: str | None = None,
        emotion_state: dict[str, Any] | None = None,
        session_id: str | None = None,
        importance: float = 0.5,
    ) -> None:
        conn = await self._ensure_connection()
        await conn.execute(
            """
            INSERT INTO conversations
            (role, content, agent_used, emotion_state, session_id, importance)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                role,
                content,
                agent_used,
                json.dumps(emotion_state, ensure_ascii=False) if emotion_state else None,
                session_id,
                importance,
            ),
        )
        await conn.commit()

    async def get_recent(self, n: int = 50, session_id: str | None = None) -> list[dict[str, Any]]:
        conn = await self._ensure_connection()
        if session_id:
            rows = await conn.execute(
                """
                SELECT role, content, agent_used, timestamp
                FROM conversations
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, n),
            )
        else:
            rows = await conn.execute(
                """
                SELECT role, content, agent_used, timestamp
                FROM conversations
                ORDER BY id DESC
                LIMIT ?
                """,
                (n,),
            )
        rows_data = await rows.fetchall()
        rows_data = list(reversed(rows_data))
        return [
            {
                "role": row[0],
                "content": row[1],
                "agent": row[2],
                "timestamp": row[3] or "",
            }
            for row in rows_data
        ]

    async def get_patterns(self, n_sessions: int = 30) -> str:
        conn = await self._ensure_connection()
        rows = await conn.execute(
            """
            SELECT content
            FROM conversations
            WHERE role = 'user'
            ORDER BY id DESC
            LIMIT ?
            """,
            (n_sessions * 10,),
        )
        rows_data = await rows.fetchall()
        contents = [row[0] for row in rows_data]
        return "\n".join(contents[-50:])

    async def close(self) -> None:
        """Close the SQLite connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None
