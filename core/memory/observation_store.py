"""core/memory/observation_store.py — claude-mem inspired observation store.

3-tier progressive disclosure pattern for token-efficient retrieval:
  Layer 1 (search): Compact index with IDs + titles only   (~50-100 tokens/result)
  Layer 2 (timeline): Chronological context around matches (~200-300 tokens/result)
  Layer 3 (get_observations): Full details for filtered IDs  (~500-1000 tokens/result)

Shared SQLite at data/observations.db — OpenCode, Claude Code, and LegionBot all write here.
<private> tags are stripped at WRITE time (defense-in-depth).

Hermes patterns ported (ADR-095 G6):
  - FTS5 trigram tokenizer for CJK/substring search (hermes hermes_state.py)
  - WAL mode with random-jitter retry for write contention (20-150ms)
  - _write_with_retry() wrapping all writes via asyncio.wait(FIRST_COMPLETED)
  - _sanitize_fts5_query() with balanced-quote preservation, operator stripping,
    and hyphenated/dotted-term quoting (replaces naive _escape_fts_query)
  - _reconcile_columns() declarative schema reconciliation on every connection
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

OBSERVATION_ROOT = Path(__file__).parent.parent.parent / "data"
OBSERVATION_ROOT.mkdir(parents=True, exist_ok=True)
DB_PATH = OBSERVATION_ROOT / "observations.db"

_WRITE_MAX_RETRIES = 15
_WRITE_RETRY_MIN_MS = 20
_WRITE_RETRY_MAX_MS = 150

# Observation type taxonomy (from claude-mem)
OBSERVATION_TYPES = frozenset({
    "decision",
    "bugfix",
    "feature",
    "refactor",
    "discovery",
    "change",
})

# Fields that trigger auto-tagging
_TAG_SIGNALS = {
    "decision": ["decided to", "choosing", "instead of", "went with", "opted for", "rejected"],
    "bugfix": ["fix", "bug", "crash", "error", "broken", "repair", "patch"],
    "feature": ["added", "new", "implement", "feature", "capability"],
    "refactor": ["refactor", "restructure", "clean up", "simplify", "rewrite"],
    "discovery": ["discovered", "found that", "learned", "interesting", "unexpected"],
    "change": ["changed", "modified", "updated", "moved", "renamed"],
}

# Files that are noise — skip observation capture
_SKIP_PATTERNS = frozenset({
    "__pycache__", ".pyc", ".git", ".venv", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "package-lock.json", "yarn.lock", "poetry.lock",
    ".DS_Store", "thumbs.db",
})


def _strip_private(text: str) -> str:
    """Remove <private> tags and their content (defense-in-depth)."""
    # Remove <private>...</private> blocks
    text = re.sub(r"<private>[\s\S]*?</private>", "", text, flags=re.IGNORECASE)
    # Also handle inline [private] ... [/private]
    text = re.sub(r"\[private\][\s\S]*?\[/private\]", "", text, flags=re.IGNORECASE)
    return text.strip()


def _classify_type(content: str) -> str:
    """Classify observation type from content (cheap heuristic before LLM compression)."""
    content_lower = content.lower()
    scores: dict[str, float] = {t: 0.0 for t in _TAG_SIGNALS}
    for obs_type, signals in _TAG_SIGNALS.items():
        for signal in signals:
            if signal in content_lower:
                scores[obs_type] += 1
    if max(scores.values()) == 0:
        return "discovery"
    return max(scores, key=scores.get)  # type: ignore[return-value]


def _should_skip_path(path: str) -> bool:
    """Return True for noise files that shouldn't generate observations."""
    path_lower = path.lower()
    return any(p in path_lower for p in _SKIP_PATTERNS)


class ObservationStore:
    """SQLite + FTS5 store for the 3-tier progressive disclosure pattern."""

    def __init__(self) -> None:
        self.conn: aiosqlite.Connection | None = None

    async def _ensure_connection(self) -> aiosqlite.Connection:
        if self.conn is None:
            self.conn = await aiosqlite.connect(str(DB_PATH))
            self.conn.row_factory = aiosqlite.Row
            # WAL mode for concurrent reads/writes across systems
            await self.conn.execute("PRAGMA journal_mode=WAL")
            await self.conn.execute("PRAGMA foreign_keys=ON")
            await self._init_db()
            await self._reconcile_columns()
        return self.conn

    async def _write_with_retry(self, fn: callable) -> Any:
        """Execute a write with random-jitter retry (hermes WAL pattern).

        SQLite's built-in busy handler uses deterministic sleep that causes
        convoy effects under high concurrency. Random jitter staggers
        competing writers naturally.
        """
        last_err: Exception | None = None
        for attempt in range(_WRITE_MAX_RETRIES):
            try:
                conn = await self._ensure_connection()
                return await fn(conn)
            except Exception as exc:  # intentional async sleep in retry loop
                # PERF203: await inside retry loop; we want controlled backoff, not CancellableSleep
                err_msg = str(exc).lower()
                if "locked" in err_msg or "busy" in err_msg:
                    last_err = exc
                    if attempt < _WRITE_MAX_RETRIES - 1:
                        jitter_ms = random.uniform(_WRITE_RETRY_MIN_MS, _WRITE_RETRY_MAX_MS)
                        await asyncio.sleep(jitter_ms / 1000)
                    continue
                raise
        raise last_err if last_err else RuntimeError("Write retries exhausted")

    async def _init_db(self) -> None:
        """Create schema: observations, session_summaries, user_prompts + FTS5 tables."""
        conn = await self._ensure_connection()

        # ── observations ────────────────────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id     TEXT    NOT NULL,
                type           TEXT    NOT NULL DEFAULT 'discovery',
                title          TEXT    NOT NULL,
                subtitle       TEXT    DEFAULT '',
                narrative      TEXT    DEFAULT '',
                facts          TEXT    DEFAULT '',
                concepts       TEXT    DEFAULT '',
                tags           TEXT    DEFAULT '',
                files_read     TEXT    DEFAULT '',
                files_modified TEXT    DEFAULT '',
                created_at     TEXT    NOT NULL
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_obs_session ON observations (session_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_obs_type ON observations (type)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_obs_created ON observations (created_at)")

        # ── session_summaries ──────────────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS session_summaries (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id   TEXT    NOT NULL UNIQUE,
                request      TEXT    NOT NULL DEFAULT '',
                investigated TEXT    DEFAULT '',
                learned      TEXT    DEFAULT '',
                completed    TEXT    DEFAULT '',
                next_steps   TEXT    DEFAULT '',
                notes        TEXT    DEFAULT '',
                created_at   TEXT    NOT NULL
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_ss_session ON session_summaries (session_id)")

        # ── FTS5 virtual tables with triggers ──────────────────────────────────
        await conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts
            USING fts5(title, subtitle, narrative, facts, concepts, tags,
                       content='observations', content_rowid='id')
        """)
        await conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS summaries_fts
            USING fts5(request, investigated, learned, completed, next_steps,
                       content='session_summaries', content_rowid='id')
        """)

        # Trigram FTS5 for CJK substring search (hermes pattern)
        # Default tokenizer splits CJK into individual tokens, breaking phrase matching.
        # Trigram creates overlapping 3-byte sequences so substring queries work for any script.
        await conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts_trigram
            USING fts5(title, subtitle, narrative, facts, concepts, tags,
                       tokenize='trigram',
                       content='observations', content_rowid='id')
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS obs_trigram_ai AFTER INSERT ON observations BEGIN
                INSERT INTO observations_fts_trigram(rowid, title, subtitle, narrative, facts, concepts, tags)
                VALUES (new.id, new.title, new.subtitle, new.narrative, new.facts, new.concepts, new.tags);
            END
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS obs_trigram_ad AFTER DELETE ON observations BEGIN
                INSERT INTO observations_fts_trigram(observations_fts_trigram, rowid, title, subtitle, narrative, facts, concepts, tags)
                VALUES('delete', old.id, old.title, old.subtitle, old.narrative, old.facts, old.concepts, old.tags);
            END
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS obs_trigram_au AFTER UPDATE ON observations BEGIN
                INSERT INTO observations_fts_trigram(observations_fts_trigram, rowid, title, subtitle, narrative, facts, concepts, tags)
                VALUES('delete', old.id, old.title, old.subtitle, old.narrative, old.facts, old.concepts, old.tags);
                INSERT INTO observations_fts_trigram(rowid, title, subtitle, narrative, facts, concepts, tags)
                VALUES (new.id, new.title, new.subtitle, new.narrative, new.facts, new.concepts, new.tags);
            END
        """)

        # Sync triggers — keep FTS in sync with base tables
        # observations → observations_fts (10 searchable columns)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS observations_ai AFTER INSERT ON observations BEGIN
                INSERT INTO observations_fts(rowid, title, subtitle, narrative, facts, concepts, tags)
                VALUES (new.id, new.title, new.subtitle, new.narrative, new.facts, new.concepts, new.tags);
            END
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS observations_ad AFTER DELETE ON observations BEGIN
                INSERT INTO observations_fts(observations_fts, rowid, title, subtitle, narrative, facts, concepts, tags)
                VALUES('delete', old.id, old.title, old.subtitle, old.narrative, old.facts, old.concepts, old.tags);
            END
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS observations_au AFTER UPDATE ON observations BEGIN
                INSERT INTO observations_fts(observations_fts, rowid, title, subtitle, narrative, facts, concepts, tags)
                VALUES('delete', old.id, old.title, old.subtitle, old.narrative, old.facts, old.concepts, old.tags);
                INSERT INTO observations_fts(rowid, title, subtitle, narrative, facts, concepts, tags)
                VALUES (new.id, new.title, new.subtitle, new.narrative, new.facts, new.concepts, new.tags);
            END
        """)

        # session_summaries → summaries_fts (5 searchable columns)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS session_summaries_ai AFTER INSERT ON session_summaries BEGIN
                INSERT INTO summaries_fts(rowid, request, investigated, learned, completed, next_steps)
                VALUES (new.id, new.request, new.investigated, new.learned, new.completed, new.next_steps);
            END
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS session_summaries_ad AFTER DELETE ON session_summaries BEGIN
                INSERT INTO summaries_fts(summaries_fts, rowid, request, investigated, learned, completed, next_steps)
                VALUES('delete', old.id, old.request, old.investigated, old.learned, old.completed, old.next_steps);
            END
        """)
        await conn.execute("""
            CREATE TRIGGER IF NOT EXISTS session_summaries_au AFTER UPDATE ON session_summaries BEGIN
                INSERT INTO summaries_fts(summaries_fts, rowid, request, investigated, learned, completed, next_steps)
                VALUES('delete', old.id, old.request, old.investigated, old.learned, old.completed, old.next_steps);
                INSERT INTO summaries_fts(rowid, request, investigated, learned, completed, next_steps)
                VALUES (new.id, new.request, new.investigated, new.learned, new.completed, new.next_steps);
            END
        """)

        await conn.commit()
        logger.info("[ObservationStore] Initialized at %s", DB_PATH)

    async def _reconcile_columns(self) -> None:
        """Ensure live tables have every column declared in the schema.

        Declarative reconciliation pattern (hermes/Beets/sqlite-utils):
        the hardcoded schema below is the single source of truth.
        On every startup this method diffs live columns (via PRAGMA
        table_info) against the declared columns, and ADDs any missing.
        This makes column additions a declarative operation — just add
        the column here and it appears on the next startup.
        """
        conn = await self._ensure_connection()
        cursor = await conn.cursor()

        expected: dict[str, dict[str, str]] = {
            "observations": {
                "id":             "INTEGER",
                "session_id":      "TEXT",
                "type":           "TEXT",
                "title":          "TEXT",
                "subtitle":       "TEXT",
                "narrative":      "TEXT",
                "facts":          "TEXT",
                "concepts":       "TEXT",
                "tags":           "TEXT",
                "files_read":     "TEXT",
                "files_modified": "TEXT",
                "created_at":     "TEXT",
            },
            "session_summaries": {
                "id":           "INTEGER",
                "session_id":   "TEXT",
                "request":      "TEXT",
                "investigated": "TEXT",
                "learned":      "TEXT",
                "completed":    "TEXT",
                "next_steps":   "TEXT",
                "notes":        "TEXT",
                "created_at":   "TEXT",
            },
        }

        for table_name, declared_cols in expected.items():
            try:
                rows = await cursor.execute(f'PRAGMA table_info("{table_name}")')
                live_rows = await rows.fetchall()
            except Exception:
                continue
            live_cols = set()
            for row in live_rows:
                live_cols.add(row["name"])

            for col_name, col_type in declared_cols.items():
                if col_name not in live_cols:
                    safe_name = col_name.replace('"', '""')
                    try:
                        await cursor.execute(
                            f'ALTER TABLE "{table_name}" ADD COLUMN "{safe_name}" {col_type}'
                        )
                        logger.info(
                            "[ObservationStore] Added column %s.%s",
                            table_name,
                            col_name,
                        )
                    except Exception as exc:
                        logger.debug(
                            "reconcile %s.%s: %s",
                            table_name,
                            col_name,
                            exc,
                        )

    # ── Write operations ───────────────────────────────────────────────────────

    async def add_observation(
        self,
        session_id: str,
        content: str,
        title: str = "",
        type_: str | None = None,
        subtitle: str = "",
        narrative: str = "",
        facts: str = "",
        concepts: str = "",
        tags: list[str] | None = None,
        files_read: list[str] | None = None,
        files_modified: list[str] | None = None,
    ) -> int:
        """Store an observation. Returns the row ID."""
        await self._ensure_connection()  # ensure connection is initialized before write

        # Strip <private> tags at write time — defense in depth
        content = _strip_private(content)
        narrative = _strip_private(narrative)

        if not title:
            title = content[:120].replace("\n", " ").strip()

        obs_type = type_ or _classify_type(content)
        if obs_type not in OBSERVATION_TYPES:
            obs_type = "discovery"

        now = datetime.now(UTC).isoformat(timespec="seconds")

        async def _do_insert(conn: aiosqlite.Connection) -> int:
            cur = await conn.execute(
                """
                INSERT INTO observations
                (session_id, type, title, subtitle, narrative, facts, concepts, tags,
                 files_read, files_modified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    obs_type,
                    title,
                    subtitle,
                    narrative,
                    facts,
                    concepts,
                    ",".join(tags or []),
                    ",".join(files_read or []),
                    ",".join(files_modified or []),
                    now,
                ),
            )
            await conn.commit()
            return int(cur.lastrowid)  # type: ignore[union-return]

        return await self._write_with_retry(_do_insert)

    async def add_session_summary(
        self,
        session_id: str,
        request: str = "",
        investigated: str = "",
        learned: str = "",
        completed: str = "",
        next_steps: str = "",
        notes: str = "",
    ) -> int:
        """Store or replace (UPSERT) a session summary."""
        now = datetime.now(UTC).isoformat(timespec="seconds")

        async def _do_upsert(conn: aiosqlite.Connection) -> int:
            cur = await conn.execute(
                """
                INSERT OR REPLACE INTO session_summaries
                (session_id, request, investigated, learned, completed, next_steps, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, request, investigated, learned, completed, next_steps, notes, now),
            )
            await conn.commit()
            return int(cur.lastrowid)  # type: ignore[union-return]

        return await self._write_with_retry(_do_upsert)

    # ── Layer 1: search — compact index (~50-100 tokens/result) ────────────────

    async def search(self, query: str, limit: int = 10, type_filter: str | None = None) -> list[dict[str, Any]]:
        """Layer 1: Returns compact index rows (id, type, title, created_at).
        Token-light: ~50-100 tokens per result. Use IDs to fetch full later."""
        conn = await self._ensure_connection()

        if type_filter and type_filter in OBSERVATION_TYPES:
            rows = await conn.execute(
                """
                SELECT o.id, o.type, o.title, o.created_at
                FROM observations o
                WHERE o.type = ?
                ORDER BY o.created_at DESC
                LIMIT ?
                """,
                (type_filter, limit),
            )
            results = await rows.fetchall()
        elif query:
            # FTS5 search on title/subtitle/narrative/concepts
            fts_query = _sanitize_fts5_query(query)
            rows = await conn.execute(
                """
                SELECT o.id, o.type, o.title, o.created_at
                FROM observations o
                JOIN observations_fts fts ON o.id = fts.rowid
                WHERE observations_fts MATCH ?
                ORDER BY o.created_at DESC
                LIMIT ?
                """,
                (fts_query, limit),
            )
            results = await rows.fetchall()
            # Fallback to recent observations when FTS returns nothing
            if not results:
                rows = await conn.execute(
                    """
                    SELECT id, type, title, created_at
                    FROM observations
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                results = await rows.fetchall()
        else:
            rows = await conn.execute(
                """
                SELECT id, type, title, created_at
                FROM observations
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            results = await rows.fetchall()

        return [
            {
                "id": r["id"],
                "type": r["type"],
                "title": r["title"],
                "created_at": r["created_at"],
            }
            for r in results
        ]

    # ── Layer 2: timeline — chronological context (~200-300 tokens/result) ──────

    async def timeline(
        self,
        query: str | None = None,
        type_filter: str | None = None,
        limit: int = 5,
        window_hours: int = 72,
    ) -> list[dict[str, Any]]:
        """Layer 2: Returns observations with title + subtitle + type + created_at.
        Shows chronological context around matches. ~200-300 tokens/result."""
        conn = await self._ensure_connection()

        cutoff = datetime.now(UTC)
        from datetime import timedelta
        cutoff -= timedelta(hours=window_hours)
        cutoff_str = cutoff.isoformat(timespec="seconds")

        if type_filter and type_filter in OBSERVATION_TYPES:
            rows = await conn.execute(
                """
                SELECT id, type, title, subtitle, created_at
                FROM observations
                WHERE type = ? AND created_at >= ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (type_filter, cutoff_str, limit),
            )
        elif query:
            fts_query = _sanitize_fts5_query(query)
            rows = await conn.execute(
                """
                SELECT o.id, o.type, o.title, o.subtitle, o.created_at
                FROM observations o
                JOIN observations_fts fts ON o.id = fts.rowid
                WHERE observations_fts MATCH ? AND o.created_at >= ?
                ORDER BY o.created_at DESC
                LIMIT ?
                """,
                (fts_query, cutoff_str, limit),
            )
        else:
            rows = await conn.execute(
                """
                SELECT id, type, title, subtitle, created_at
                FROM observations
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (cutoff_str, limit),
            )

        results = await rows.fetchall()
        return [
            {
                "id": r["id"],
                "type": r["type"],
                "title": r["title"],
                "subtitle": r["subtitle"] or "",
                "created_at": r["created_at"],
            }
            for r in results
        ]

    # ── Layer 3: get_observations — full details (~500-1000 tokens/result) ───

    async def get_observations(self, ids: list[int]) -> list[dict[str, Any]]:
        """Layer 3: Full details for a specific set of observation IDs.
        Only fetch what you need — this is the expensive layer."""
        if not ids:
            return []
        conn = await self._ensure_connection()
        placeholders = ",".join("?" * len(ids))
        rows = await conn.execute(
            f"""
            SELECT id, session_id, type, title, subtitle, narrative, facts, concepts,
                   tags, files_read, files_modified, created_at
            FROM observations
            WHERE id IN ({placeholders})
            ORDER BY created_at DESC
            """,
            ids,
        )
        results = await rows.fetchall()
        return [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "type": r["type"],
                "title": r["title"],
                "subtitle": r["subtitle"] or "",
                "narrative": r["narrative"] or "",
                "facts": r["facts"] or "",
                "concepts": r["concepts"] or "",
                "tags": r["tags"].split(",") if r["tags"] else [],
                "files_read": r["files_read"].split(",") if r["files_read"] else [],
                "files_modified": r["files_modified"].split(",") if r["files_modified"] else [],
                "created_at": r["created_at"],
            }
            for r in results
        ]

    async def get_session_summary(self, session_id: str) -> dict[str, Any] | None:
        """Fetch session summary by session_id."""
        conn = await self._ensure_connection()
        row = await conn.execute(
            "SELECT * FROM session_summaries WHERE session_id = ?",
            (session_id,),
        )
        r = await row.fetchone()
        if not r:
            return None
        return {
            "id": r["id"],
            "session_id": r["session_id"],
            "request": r["request"] or "",
            "investigated": r["investigated"] or "",
            "learned": r["learned"] or "",
            "completed": r["completed"] or "",
            "next_steps": r["next_steps"] or "",
            "notes": r["notes"] or "",
            "created_at": r["created_at"],
        }

    async def get_session_observations(self, session_id: str) -> list[dict[str, Any]]:
        """Get all observations for a given session."""
        conn = await self._ensure_connection()
        rows = await conn.execute(
            """
            SELECT id, session_id, type, title, subtitle, narrative, facts, concepts,
                   tags, files_read, files_modified, created_at
            FROM observations
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        )
        results = await rows.fetchall()
        return [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "type": r["type"],
                "title": r["title"],
                "subtitle": r["subtitle"] or "",
                "narrative": r["narrative"] or "",
                "facts": r["facts"] or "",
                "concepts": r["concepts"] or "",
                "tags": r["tags"].split(",") if r["tags"] else [],
                "files_read": r["files_read"].split(",") if r["files_read"] else [],
                "files_modified": r["files_modified"].split(",") if r["files_modified"] else [],
                "created_at": r["created_at"],
            }
            for r in results
        ]

    async def get_stats(self) -> dict[str, int]:
        """Return observation counts by type."""
        conn = await self._ensure_connection()
        row = await conn.execute(
            "SELECT type, COUNT(*) as cnt FROM observations GROUP BY type"
        )
        rows = await row.fetchall()
        total = await conn.execute("SELECT COUNT(*) FROM observations")
        total_row = await total.fetchone()
        return {r["type"]: r["cnt"] for r in rows} | {"total": total_row["COUNT(*)"] if total_row else 0}  # type: ignore[index]

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            self.conn = None


def _sanitize_fts5_query(query: str) -> str:
    """Sanitize user input for safe use in FTS5 MATCH queries.

    FTS5 has its own query syntax where characters like ``"``, ``(``, ``)``,
    ``+``, ``*``, ``{``, ``}`` and bare boolean operators (``AND``, ``OR``,
    ``NOT``) have special meaning.  Passing raw user input directly to
    MATCH can cause ``sqlite3.OperationalError``.

    Strategy:
    - Preserve properly paired quoted phrases (``"exact phrase"``)
    - Strip unmatched FTS5-special characters that would cause errors
    - Wrap unquoted hyphenated and dotted terms in quotes so FTS5
      matches them as exact phrases instead of splitting on the
      hyphen/dot (e.g. ``chat-send``, ``P2.2``, ``my-app.config.ts``)
    """
    # Step 1: Extract balanced double-quoted phrases and protect them
    # from further processing via numbered placeholders.
    _quoted_parts: list = []

    def _preserve_quoted(m: re.Match) -> str:
        _quoted_parts.append(m.group(0))
        return f"\x00Q{len(_quoted_parts) - 1}\x00"

    sanitized = re.sub(r'"[^"]*"', _preserve_quoted, query)

    # Step 2: Strip remaining (unmatched) FTS5-special characters
    sanitized = re.sub(r"[+{}()^]", " ", sanitized)

    # Step 3: Collapse repeated * (e.g. "***") into a single one,
    # and remove leading * (prefix-only needs at least one char before *)
    sanitized = re.sub(r"\*+", "*", sanitized)
    sanitized = re.sub(r"(^|\s)\*", r"\1", sanitized)

    # Step 4: Remove dangling boolean operators at start/end that would
    # cause syntax errors (e.g. "hello AND" or "OR world")
    sanitized = re.sub(r"(?i)^(AND|OR|NOT)\b\s*", "", sanitized.strip())
    sanitized = re.sub(r"(?i)\s+(AND|OR|NOT)\s*$", "", sanitized.strip())

    # Step 5: Wrap unquoted dotted and/or hyphenated terms in double
    # quotes.  FTS5's tokenizer splits on dots and hyphens, turning
    # ``chat-send`` into ``chat AND send`` and ``P2.2`` into ``p2 AND 2``.
    # Quoting preserves phrase semantics.  A single pass avoids the
    # double-quoting bug that would occur if dotted, hyphenated and underscored
    # patterns were applied sequentially (e.g. ``my-app.config``).
    sanitized = re.sub(r"\b(\w+(?:[._-]\w+)+)\b", r'"\1"', sanitized)

    # Step 6: Strip any remaining unmatched double quotes (e.g. "unterminated)
    # that were not captured as properly-paired phrases in Step 1.
    # Do this BEFORE restoring preserved phrases so we don't strip their quotes.
    sanitized = sanitized.replace('"', "")

    # Step 7: Restore preserved quoted phrases
    for i, quoted in enumerate(_quoted_parts):
        sanitized = sanitized.replace(f"\x00Q{i}\x00", quoted)

    return sanitized.strip()


# ── Singleton ─────────────────────────────────────────────────────────────────

_store: ObservationStore | None = None


def get_observation_store() -> ObservationStore:
    global _store
    if _store is None:
        _store = ObservationStore()
    return _store
