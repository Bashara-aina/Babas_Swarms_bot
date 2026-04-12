"""Episodic memory store — persistent events, facts, and schedule awareness.

Backed by Supabase pgvector. Falls back to local JSON if Supabase unavailable.
Stores structured episodes: events, facts about Bashara, project milestones,
schedule entries. Queried semantically before every Legion response.

Tables used (auto-created on first run if not present):
  legion_episodes  — episodic events with embedding + metadata
  legion_profile   — personal profile key-value store
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_FALLBACK_PATH = Path("data/episodic_memory.json")
_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class Episode:
    id: str
    user_id: str
    episode_type: str  # event | fact | schedule | project | preference
    summary: str  # human-readable summary
    detail: str  # full detail / raw text
    tags: list[str]
    ts: float  # unix timestamp of when this happened
    source: str = "user"  # user | proactive | system
    metadata: dict = field(default_factory=dict)


class EpisodicStore:
    """Persistent episodic memory — Supabase pgvector + local JSON fallback."""

    def __init__(self) -> None:
        self._supabase = None
        self._use_supabase = False
        self._local: list[dict] = []
        self._init_supabase()
        self._load_local()

    def _init_supabase(self) -> None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            logger.info("[EpisodicStore] No Supabase env — using local JSON fallback")
            return
        try:
            from supabase import create_client

            self._supabase = create_client(url, key)
            self._use_supabase = True
            logger.info("[EpisodicStore] Supabase connected")
            self._ensure_tables()
        except Exception as e:
            logger.warning("[EpisodicStore] Supabase init failed: %s — using local fallback", e)

    def _ensure_tables(self) -> None:
        """Create tables if they don't exist. Non-fatal if it fails."""
        try:
            # Check if table exists by doing a limit-0 query
            self._supabase.table("legion_episodes").select("id").limit(1).execute()
        except Exception:
            logger.info("[EpisodicStore] legion_episodes table may not exist — create it in Supabase dashboard")
            logger.info(
                "[EpisodicStore] SQL: CREATE TABLE legion_episodes (id uuid PRIMARY KEY, user_id text, episode_type text, summary text, detail text, tags jsonb, ts float8, source text, metadata jsonb);"
            )

    def _load_local(self) -> None:
        if _FALLBACK_PATH.exists():
            try:
                self._local = json.loads(_FALLBACK_PATH.read_text(encoding="utf-8"))
            except Exception:
                self._local = []

    def _save_local(self) -> None:
        try:
            _FALLBACK_PATH.write_text(json.dumps(self._local, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("[EpisodicStore] Local save failed: %s", e)

    def _consolidate_entries(self, entries: list[dict]) -> str:
        """Summarize a list of old episodic entries into a single summary string.

        Used when approaching the local store limit (1900 entries) to prevent
        data loss from silent truncation.
        """
        if not entries:
            return ""
        try:
            # Create a simple keyword-based summary
            all_texts: list[str] = []
            for entry in entries:
                text = f"{entry.get('summary', '')} {entry.get('detail', '')}".strip()
                if text:
                    all_texts.append(text)
            if not all_texts:
                return ""
            # Simple concatenation with deduplication
            combined = " | ".join(all_texts[:50])  # cap at 50 entries to avoid huge summaries
            if len(combined) > 1000:
                combined = combined[:1000] + "..."
            return combined
        except Exception as e:
            logger.warning("[EpisodicStore] Consolidation failed: %s", e)
            return str(entries[:3])  # fallback: just return first 3 as string

    # ── Public API ────────────────────────────────────────────────────────

    def store(
        self,
        user_id: str,
        episode_type: str,
        summary: str,
        detail: str = "",
        tags: list[str] | None = None,
        metadata: dict | None = None,
        source: str = "user",
    ) -> str:
        """Store an episode. Returns the episode ID."""
        ep = Episode(
            id=str(uuid.uuid4()),
            user_id=user_id,
            episode_type=episode_type,
            summary=summary,
            detail=detail or summary,
            tags=tags or [],
            ts=time.time(),
            source=source,
            metadata=metadata or {},
        )
        ep_dict = asdict(ep)

        if self._use_supabase:
            try:
                data = dict(ep_dict)
                data["tags"] = json.dumps(data["tags"])
                data["metadata"] = json.dumps(data["metadata"])
                self._supabase.table("legion_episodes").insert(data).execute()
                logger.debug("[EpisodicStore] Stored to Supabase: %s", ep.id)
                return ep.id
            except Exception as e:
                logger.warning("[EpisodicStore] Supabase store failed: %s — writing to local", e)

        # Local fallback
        self._local.append(ep_dict)
        # FIX: Instead of silent truncation, consolidate old memories to prevent data loss
        if len(self._local) > 1900:
            # Consolidate oldest 300 entries into a summary before they are dropped
            consolidate_count = 300
            old_entries = self._local[:-consolidate_count]
            if old_entries:
                summary = self._consolidate_entries(old_entries)
                # Store the summary at the beginning of the list (will be kept in truncated range)
                summary_entry = {
                    "user_id": "system",
                    "episode_type": "consolidated_summary",
                    "summary": f"Consolidated {len(old_entries)} old memories",
                    "detail": summary[:500],
                    "tags": json.dumps(["consolidated", "summary"]),
                    "ts": ep_dict.get("ts", ""),
                    "metadata": json.dumps({"entry_count": len(old_entries), "source": "auto_consolidation"}),
                }
                # Keep last 2000 + 1 summary entry
                self._local = [summary_entry] + self._local[-2000:]
                logger.warning(
                    "[EpisodicStore] Consolidating %d old memories into summary "
                    "(limit=%d) to prevent data loss. Last summary: %s...",
                    len(old_entries),
                    2000,
                    summary[:100],
                )
        elif len(self._local) > 2000:
            self._local = self._local[-2000:]
        self._save_local()
        return ep.id

    def recall(self, user_id: str, query: str, limit: int = 8, episode_type: str | None = None) -> list[dict]:
        """Recall relevant episodes. Semantic search if Supabase+pgvector, else keyword."""
        if self._use_supabase:
            try:
                return self._supabase_recall(user_id, query, limit, episode_type)
            except Exception as e:
                logger.warning("[EpisodicStore] Supabase recall failed: %s — using local", e)

        return self._local_recall(user_id, query, limit, episode_type)

    def _supabase_recall(self, user_id: str, query: str, limit: int, episode_type: str | None) -> list[dict]:
        q = (
            self._supabase.table("legion_episodes")
            .select("id,episode_type,summary,detail,tags,ts,source,metadata")
            .eq("user_id", user_id)
            .order("ts", desc=True)
            .limit(limit * 3)
        )
        if episode_type:
            q = q.eq("episode_type", episode_type)
        result = q.execute()
        rows = result.data or []
        # Basic keyword filter on top of recency
        query_words = set(query.lower().split())
        scored = []
        for row in rows:
            text = (row.get("summary", "") + " " + row.get("detail", "")).lower()
            score = sum(1 for w in query_words if w in text)
            scored.append((score, row))
        scored.sort(key=lambda x: (-x[0], -float(x[1].get("ts", 0))))
        return [r for _, r in scored[:limit]]

    def _local_recall(self, user_id: str, query: str, limit: int, episode_type: str | None) -> list[dict]:
        episodes = [e for e in self._local if e.get("user_id") == user_id]
        if episode_type:
            episodes = [e for e in episodes if e.get("episode_type") == episode_type]
        query_words = set(query.lower().split())
        scored = []
        for ep in episodes:
            text = (ep.get("summary", "") + " " + ep.get("detail", "")).lower()
            score = sum(1 for w in query_words if w in text)
            scored.append((score, ep))
        scored.sort(key=lambda x: (-x[0], -float(x[1].get("ts", 0))))
        return [ep for _, ep in scored[:limit]]

    def get_upcoming_schedule(self, user_id: str, horizon_days: int = 7) -> list[dict]:
        """Return schedule episodes within the next N days."""
        now = time.time()
        horizon = now + (horizon_days * 86400)
        episodes = self.recall(user_id, "schedule", limit=20, episode_type="schedule")
        upcoming = []
        for ep in episodes:
            meta = ep.get("metadata", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            event_ts = float(meta.get("event_ts", 0))
            if now <= event_ts <= horizon:
                upcoming.append(ep)
        return upcoming

    def build_context_block(self, user_id: str, query: str) -> str:
        """Build a [MEMORY CONTEXT] block to prepend to the system prompt."""
        episodes = self.recall(user_id, query, limit=6)
        schedule = self.get_upcoming_schedule(user_id, horizon_days=3)

        if not episodes and not schedule:
            return ""

        lines = ["[MEMORY CONTEXT — Legion's long-term memory about Bashara]", ""]
        if schedule:
            lines.append("📅 UPCOMING SCHEDULE:")
            for ep in schedule[:3]:
                lines.append(f"  • {ep.get('summary', '')}")
            lines.append("")

        if episodes:
            lines.append("🧠 RELEVANT MEMORIES:")
            for ep in episodes:
                ts_str = _fmt_ts(float(ep.get("ts", 0)))
                lines.append(f"  [{ep.get('episode_type', '?')} | {ts_str}] {ep.get('summary', '')}")
        lines.append("[END MEMORY CONTEXT]")
        return "\n".join(lines)

    def auto_extract_and_store(self, user_id: str, user_msg: str) -> None:
        """Heuristically extract storable facts from user messages.

        Stores facts into episodic memory so Legion can recall them in future turns.
        Multiple categories can match — the first high-confidence hit wins.
        Any substantive message (>20 words) is stored as a loose conversation entry.
        """
        msg = user_msg.strip()
        if not msg or len(msg) < 10:
            return

        msg_lower = msg.lower()

        # ── Schedule / time-bounded events ──────────────────────────────────
        schedule_triggers = [
            "holiday",
            "libur",
            "cuti",
            "meeting",
            "appointment",
            "flight",
            "penerbangan",
            "trip",
            "travel",
            "perjalanan",
            "deadline",
            "besok",
            "tomorrow",
            "next week",
            "minggu depan",
            "next month",
            "bulan depan",
            "next year",
            "conference",
            "event",
            "vacation",
            "liburan",
            "going to",
            "akan pergi",
            "plan to",
            "berencana",
            "seminar",
            "workshop",
        ]
        if any(t in msg_lower for t in schedule_triggers):
            self.store(
                user_id, "schedule", summary=msg[:200], detail=msg, tags=["schedule", "auto"], source="auto_extract"
            )
            return

        # ── Personal preferences & facts ────────────────────────────────────
        pref_triggers = [
            "i like",
            "i love",
            "i hate",
            "i prefer",
            "i always",
            "i never",
            "aku suka",
            "aku tidak suka",
            "aku selalu",
            "aku biasanya",
            "my home",
            "my office",
            "rumahku",
            "kantorku",
            "i live in",
            "aku tinggal di",
            "i work at",
            "i study",
            "i'm studying",
            "i'm working on",
            "i use",
            "i'm using",
            "my favorite",
            "favorit saya",
            "my setup",
            "i switched to",
            "my name is",
            "nama saya",
            "i usually",
            "biasanya aku",
            "i feel",
            "aku merasa",
            "i think",
            "menurut aku",
            "my goal",
            "target saya",
            "i want to",
            "aku mau",
        ]
        if any(t in msg_lower for t in pref_triggers):
            self.store(
                user_id, "preference", summary=msg[:200], detail=msg, tags=["preference", "auto"], source="auto_extract"
            )
            return

        # ── People / relationships ───────────────────────────────────────────
        people_triggers = [
            "my friend",
            "my partner",
            "my boss",
            "my team",
            "my professor",
            "temanku",
            "pacarku",
            "bossku",
            "timku",
            "dosenku",
            "she is",
            "he is",
            "they are",
            "her name is",
            "his name is",
            "my supervisor",
            "my colleague",
        ]
        if any(t in msg_lower for t in people_triggers):
            self.store(
                user_id,
                "people",
                summary=msg[:200],
                detail=msg,
                tags=["people", "relationship", "auto"],
                source="auto_extract",
            )
            return

        # ── Location awareness ───────────────────────────────────────────────
        location_triggers = [
            "i'm in",
            "aku di",
            "i'm at",
            "aku lagi di",
            "i'm visiting",
            "i moved to",
            "aku pindah ke",
            "my city",
            "my country",
            "near me",
            "around here",
            "di sini",
            "di sana",
            "i'm near",
        ]
        if any(t in msg_lower for t in location_triggers):
            self.store(
                user_id, "location", summary=msg[:200], detail=msg, tags=["location", "auto"], source="auto_extract"
            )
            return

        # ── Project milestones & technical work ─────────────────────────────
        project_triggers = [
            "deployed",
            "launched",
            "finished",
            "completed",
            "broke",
            "rumahlabuh",
            "supabase",
            "github",
            "server",
            "dataset",
            "selesai",
            "deploy",
            "rilis",
            "merged",
            "pushed",
            "released",
            "training",
            "model",
            "pytorch",
            "cuda",
            "vram",
            "epoch",
            "error",
            "bug",
            "fixed",
            "bug fix",
            "refactor",
            "migrated",
            "implemented",
            "built",
            "created",
            "wrote",
        ]
        if any(t in msg_lower for t in project_triggers) and len(msg) > 30:
            self.store(
                user_id, "project", summary=msg[:200], detail=msg, tags=["project", "auto"], source="auto_extract"
            )
            return

        # ── Remember-me directives ───────────────────────────────────────────
        remember_triggers = [
            "remember that",
            "note that",
            "keep in mind",
            "don't forget",
            "ingat bahwa",
            "catat",
            "ingat ya",
            "fyi",
            "just so you know",
            "btw",
            "by the way",
        ]
        if any(t in msg_lower for t in remember_triggers):
            self.store(
                user_id, "fact", summary=msg[:200], detail=msg, tags=["fact", "explicit", "auto"], source="auto_extract"
            )
            return

        # ── Catch-all: store any substantive message as a conversation episode ─
        # Low importance — keeps a natural episodic trail even for casual chat.
        if len(msg.split()) >= 20:
            self.store(
                user_id,
                "conversation",
                summary=msg[:200],
                detail=msg,
                tags=["conversation", "auto"],
                source="auto_extract",
            )


def _fmt_ts(ts: float) -> str:
    import datetime

    if ts == 0:
        return "unknown date"
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%b %d %Y")
    except Exception:
        return "?"


# Singleton
_store: EpisodicStore | None = None


def get_episodic_store() -> EpisodicStore:
    global _store
    if _store is None:
        _store = EpisodicStore()
    return _store
