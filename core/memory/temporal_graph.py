"""Temporal knowledge graph memory."""

from __future__ import annotations

import sqlite3
from pathlib import Path

GRAPH_DB = Path.home() / ".legionswarm" / "memory" / "temporal_graph.db"


class TemporalKnowledgeGraph:
    """Bi-temporal graph-like fact store backed by SQLite."""

    def __init__(self) -> None:
        GRAPH_DB.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(GRAPH_DB), check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                entity_type TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER REFERENCES entities(id),
                predicate TEXT NOT NULL,
                object_text TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                valid_from TEXT DEFAULT (datetime('now')),
                valid_until TEXT,
                source TEXT,
                UNIQUE(subject_id, predicate, object_text, valid_until)
            );
            CREATE INDEX IF NOT EXISTS idx_rel_subject ON relationships(subject_id);
            CREATE INDEX IF NOT EXISTS idx_rel_pred ON relationships(predicate);
            """
        )
        self.conn.commit()
        self._seed_user()

    def _seed_user(self) -> None:
        try:
            self._ensure_entity("Bashara", "person")
            self._ensure_entity("LegionSwarm", "system")
            self._ensure_entity("RTX 3060", "hardware")
            known = [
                ("Bashara", "lives_in", "Tokyo, Japan"),
                ("Bashara", "uses_system", "LegionSwarm"),
                ("Bashara", "studies", "Data Science / AI"),
                ("Bashara", "uses_hardware", "RTX 3060 12GB"),
                ("LegionSwarm", "runs_on", "Ubuntu 22.04"),
                ("LegionSwarm", "uses_local_model", "gemma4:e4b"),
            ]
            for subject, predicate, obj in known:
                self.add_fact(subject, predicate, obj, confidence=1.0, source="seed")
        except Exception:
            pass

    def _ensure_entity(self, name: str, entity_type: str = "general") -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO entities (name, entity_type) VALUES (?, ?)",
            (name, entity_type),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT id FROM entities WHERE name = ?", (name,)).fetchone()
        return int(row[0])

    def add_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = "conversation",
    ) -> None:
        subject_id = self._ensure_entity(subject)
        self.conn.execute(
            """
            UPDATE relationships
            SET valid_until = datetime('now')
            WHERE subject_id = ?
              AND predicate = ?
              AND valid_until IS NULL
              AND object_text != ?
            """,
            (subject_id, predicate, obj),
        )
        self.conn.execute(
            """
            INSERT OR IGNORE INTO relationships
            (subject_id, predicate, object_text, confidence, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (subject_id, predicate, obj, confidence, source),
        )
        self.conn.commit()

    def get_current_facts(self, subject: str) -> list[dict]:
        row = self.conn.execute("SELECT id FROM entities WHERE name = ?", (subject,)).fetchone()
        if not row:
            return []
        rows = self.conn.execute(
            """
            SELECT predicate, object_text, confidence, valid_from
            FROM relationships
            WHERE subject_id = ? AND valid_until IS NULL
            ORDER BY confidence DESC
            """,
            (row[0],),
        ).fetchall()
        return [
            {"predicate": r[0], "object": r[1], "confidence": r[2], "since": r[3]}
            for r in rows
        ]

    def get_history(self, subject: str, predicate: str) -> list[dict]:
        row = self.conn.execute("SELECT id FROM entities WHERE name = ?", (subject,)).fetchone()
        if not row:
            return []
        rows = self.conn.execute(
            """
            SELECT object_text, valid_from, valid_until, confidence
            FROM relationships
            WHERE subject_id = ? AND predicate = ?
            ORDER BY valid_from ASC
            """,
            (row[0], predicate),
        ).fetchall()
        return [
            {"value": r[0], "from": r[1], "until": r[2] or "now", "confidence": r[3]}
            for r in rows
        ]

    def to_prompt_block(self) -> str:
        facts = self.get_current_facts("Bashara")
        if not facts:
            return ""
        lines = ["[KNOWLEDGE GRAPH — verified facts about user]"]
        for fact in facts:
            lines.append(f"  Bashara {fact['predicate'].replace('_', ' ')} {fact['object']}")
        return "\n".join(lines)
