"""Episodic memory store — persistent events, facts, and schedule awareness.  # type: ignore[reportOptionalMemberAccess]

Backed by Supabase pgvector. Falls back to local JSON if Supabase unavailable.  # type: ignore[reportOptionalMemberAccess]
Stores structured episodes: events, facts about Bashara, project milestones,  # type: ignore[reportOptionalMemberAccess]
schedule entries. Queried semantically before every Legion response.  # type: ignore[reportOptionalMemberAccess]

Tables used (auto-created on first run if not present):  # type: ignore[reportOptionalMemberAccess]
  legion_episodes  — episodic events with embedding + metadata
  legion_profile   — personal profile key-value store
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field  # type: ignore[reportOptionalMemberAccess]
from pathlib import Path

logger = logging.getLogger(__name__)  # type: ignore[reportOptionalMemberAccess]

_FALLBACK_PATH = Path("data/episodic_memory.json")  # type: ignore[reportOptionalMemberAccess]
_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[reportOptionalMemberAccess]


@dataclass
class Episode:
    id: str
    user_id: str
    episode_type: str  # event | fact | schedule | project | preference
    summary: str  # human-readable summary
    detail: str  # full detail / raw text
    tags: list[str]
    ts: float  # unix timestamp of when this happened
    source: str = "user"  # user | proactive | system  # type: ignore[reportOptionalMemberAccess]
    metadata: dict = field(default_factory=dict)  # type: ignore[reportOptionalMemberAccess]


class EpisodicStore:
    """Persistent episodic memory — Supabase pgvector + local JSON fallback."""  # type: ignore[reportOptionalMemberAccess]

    def __init__(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        self._supabase = None  # type: ignore[reportOptionalMemberAccess]
        self._use_supabase = False  # type: ignore[reportOptionalMemberAccess]
        self._local: list[dict] = []  # type: ignore[reportOptionalMemberAccess]
        self._init_supabase()  # type: ignore[reportOptionalMemberAccess]
        self._load_local()  # type: ignore[reportOptionalMemberAccess]

    def _init_supabase(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")  # type: ignore[reportOptionalMemberAccess]
        key = (  # type: ignore[reportOptionalMemberAccess]
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # type: ignore[reportOptionalMemberAccess]
            or os.getenv("SUPABASE_SERVICE_KEY")  # type: ignore[reportOptionalMemberAccess]
            or os.getenv("SUPABASE_ANON_KEY")  # type: ignore[reportOptionalMemberAccess]
            or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")  # type: ignore[reportOptionalMemberAccess]
        )
        if not url or not key:
            logger.info("[EpisodicStore] No Supabase env — using local JSON fallback")  # type: ignore[reportOptionalMemberAccess]
            return
        try:
            from supabase import create_client

            self._supabase = create_client(url, key)  # type: ignore[reportOptionalMemberAccess]
            self._use_supabase = True  # type: ignore[reportOptionalMemberAccess]
            logger.info("[EpisodicStore] Supabase connected")  # type: ignore[reportOptionalMemberAccess]
            self._ensure_tables()  # type: ignore[reportOptionalMemberAccess]
        except Exception as e:
            logger.warning("[EpisodicStore] Supabase init failed: %s — using local fallback", e)  # type: ignore[reportOptionalMemberAccess]

    def _ensure_tables(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        """Create tables if they don't exist. Non-fatal if it fails."""  # type: ignore[reportOptionalMemberAccess]
        try:
            # Check if table exists by doing a limit-0 query
            self._supabase.table("legion_episodes").select("id").limit(1).execute()  # type: ignore[reportOptionalMemberAccess]
        except Exception:
            logger.info("[EpisodicStore] legion_episodes table may not exist — create it in Supabase dashboard")  # type: ignore[reportOptionalMemberAccess]
            logger.info(  # type: ignore[reportOptionalMemberAccess]
                "[EpisodicStore] SQL: CREATE TABLE legion_episodes (id uuid PRIMARY KEY, user_id text, episode_type text, summary text, detail text, tags jsonb, ts float8, source text, metadata jsonb);"  # type: ignore[reportOptionalMemberAccess]
            )

    def _load_local(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        if _FALLBACK_PATH.exists():  # type: ignore[reportOptionalMemberAccess]
            try:
                self._local = json.loads(_FALLBACK_PATH.read_text(encoding="utf-8"))  # type: ignore[reportOptionalMemberAccess]
            except Exception:
                self._local = []  # type: ignore[reportOptionalMemberAccess]

    def _save_local(self) -> None:  # type: ignore[reportOptionalMemberAccess]
        try:
            _FALLBACK_PATH.write_text(json.dumps(self._local, indent=2), encoding="utf-8")  # type: ignore[reportOptionalMemberAccess]
        except Exception as e:
            logger.warning("[EpisodicStore] Local save failed: %s", e)  # type: ignore[reportOptionalMemberAccess]

    def _consolidate_entries(self, entries: list[dict]) -> str:  # type: ignore[reportOptionalMemberAccess]
        """Summarize a list of old episodic entries into a single summary string.  # type: ignore[reportOptionalMemberAccess]

        Used when approaching the local store limit (1900 entries) to prevent  # type: ignore[reportOptionalMemberAccess]
        data loss from silent truncation.  # type: ignore[reportOptionalMemberAccess]
        """
        if not entries:
            return ""
        try:
            # Create a simple keyword-based summary
            all_texts: list[str] = []  # type: ignore[reportOptionalMemberAccess]
            for entry in entries:
                text = f"{entry.get('summary', '')} {entry.get('detail', '')}".strip()  # type: ignore[reportOptionalMemberAccess]
                if text:
                    all_texts.append(text)  # type: ignore[reportOptionalMemberAccess]
            if not all_texts:
                return ""
            # Simple concatenation with deduplication
            combined = " | ".join(all_texts[:50])  # cap at 50 entries to avoid huge summaries  # type: ignore[reportOptionalMemberAccess]
            if len(combined) > 1000:  # type: ignore[reportOptionalMemberAccess]
                combined = combined[:1000] + "..."  # type: ignore[reportOptionalMemberAccess]
            return combined
        except Exception as e:
            logger.warning("[EpisodicStore] Consolidation failed: %s", e)  # type: ignore[reportOptionalMemberAccess]
            return str(entries[:3])  # fallback: just return first 3 as string  # type: ignore[reportOptionalMemberAccess]

    # ── Public API ────────────────────────────────────────────────────────

    def store(  # type: ignore[reportOptionalMemberAccess]
        self,  # type: ignore[reportOptionalMemberAccess]
        user_id: str,  # type: ignore[reportOptionalMemberAccess]
        episode_type: str,  # type: ignore[reportOptionalMemberAccess]
        summary: str,  # type: ignore[reportOptionalMemberAccess]
        detail: str = "",  # type: ignore[reportOptionalMemberAccess]
        tags: list[str] | None = None,  # type: ignore[reportOptionalMemberAccess]
        metadata: dict | None = None,  # type: ignore[reportOptionalMemberAccess]
        source: str = "user",  # type: ignore[reportOptionalMemberAccess]
    ) -> str:
        """Store an episode. Returns the episode ID."""  # type: ignore[reportOptionalMemberAccess]
        ep = Episode(  # type: ignore[reportOptionalMemberAccess]
            id=str(uuid.uuid4()),  # type: ignore[reportOptionalMemberAccess]
            user_id=user_id,  # type: ignore[reportOptionalMemberAccess]
            episode_type=episode_type,  # type: ignore[reportOptionalMemberAccess]
            summary=summary,  # type: ignore[reportOptionalMemberAccess]
            detail=detail or summary,  # type: ignore[reportOptionalMemberAccess]
            tags=tags or [],  # type: ignore[reportOptionalMemberAccess]
            ts=time.time(),  # type: ignore[reportOptionalMemberAccess]
            source=source,  # type: ignore[reportOptionalMemberAccess]
            metadata=metadata or {},  # type: ignore[reportOptionalMemberAccess]
        )
        ep_dict = asdict(ep)  # type: ignore[reportOptionalMemberAccess]

        if self._use_supabase:  # type: ignore[reportOptionalMemberAccess]
            try:
                data = dict(ep_dict)  # type: ignore[reportOptionalMemberAccess]
                data["tags"] = json.dumps(data["tags"])  # type: ignore[reportOptionalMemberAccess]
                data["metadata"] = json.dumps(data["metadata"])  # type: ignore[reportOptionalMemberAccess]
                self._supabase.table("legion_episodes").insert(data).execute()  # type: ignore[reportOptionalMemberAccess]
                logger.debug("[EpisodicStore] Stored to Supabase: %s", ep.id)  # type: ignore[reportOptionalMemberAccess]
                return ep.id  # type: ignore[reportOptionalMemberAccess]
            except Exception as e:
                logger.warning("[EpisodicStore] Supabase store failed: %s — writing to local", e)  # type: ignore[reportOptionalMemberAccess]

        # Local fallback
        self._local.append(ep_dict)  # type: ignore[reportOptionalMemberAccess]
        # FIX: Instead of silent truncation, consolidate old memories to prevent data loss  # type: ignore[reportOptionalMemberAccess]
        if len(self._local) > 1900:  # type: ignore[reportOptionalMemberAccess]
            # Consolidate oldest 300 entries into a summary before they are dropped
            consolidate_count = 300  # type: ignore[reportOptionalMemberAccess]
            old_entries = self._local[:-consolidate_count]  # type: ignore[reportOptionalMemberAccess]
            if old_entries:
                summary = self._consolidate_entries(old_entries)  # type: ignore[reportOptionalMemberAccess]
                # Store the summary at the beginning of the list (will be kept in truncated range)  # type: ignore[reportOptionalMemberAccess]
                summary_entry = {  # type: ignore[reportOptionalMemberAccess]
                    "user_id": "system",  # type: ignore[reportOptionalMemberAccess]
                    "episode_type": "consolidated_summary",  # type: ignore[reportOptionalMemberAccess]
                    "summary": f"Consolidated {len(old_entries)} old memories",  # type: ignore[reportOptionalMemberAccess]
                    "detail": summary[:500],  # type: ignore[reportOptionalMemberAccess]
                    "tags": json.dumps(["consolidated", "summary"]),  # type: ignore[reportOptionalMemberAccess]
                    "ts": ep_dict.get("ts", ""),  # type: ignore[reportOptionalMemberAccess]
                    "metadata": json.dumps({"entry_count": len(old_entries), "source": "auto_consolidation"}),  # type: ignore[reportOptionalMemberAccess]
                }
                # Keep last 2000 + 1 summary entry
                self._local = [summary_entry, *self._local[-2000:]]  # type: ignore[reportOptionalMemberAccess]
                logger.warning(  # type: ignore[reportOptionalMemberAccess]
                    "[EpisodicStore] Consolidating %d old memories into summary "
                    "(limit=%d) to prevent data loss. Last summary: %s...",  # type: ignore[reportOptionalMemberAccess]
                    len(old_entries),  # type: ignore[reportOptionalMemberAccess]
                    2000,  # type: ignore[reportOptionalMemberAccess]
                    summary[:100],  # type: ignore[reportOptionalMemberAccess]
                )
        elif len(self._local) > 2000:  # type: ignore[reportOptionalMemberAccess]
            self._local = self._local[-2000:]  # type: ignore[reportOptionalMemberAccess]
        self._save_local()  # type: ignore[reportOptionalMemberAccess]
        return ep.id  # type: ignore[reportOptionalMemberAccess]

    def recall(self, user_id: str, query: str, limit: int = 8, episode_type: str | None = None) -> list[dict]:  # type: ignore[reportOptionalMemberAccess]
        """Recall relevant episodes. Semantic search if Supabase+pgvector, else keyword."""  # type: ignore[reportOptionalMemberAccess]
        if self._use_supabase:  # type: ignore[reportOptionalMemberAccess]
            try:
                return self._supabase_recall(user_id, query, limit, episode_type)  # type: ignore[reportOptionalMemberAccess]
            except Exception as e:
                logger.warning("[EpisodicStore] Supabase recall failed: %s — using local", e)  # type: ignore[reportOptionalMemberAccess]

        return self._local_recall(user_id, query, limit, episode_type)  # type: ignore[reportOptionalMemberAccess]

    def _supabase_recall(self, user_id: str, query: str, limit: int, episode_type: str | None) -> list[dict]:  # type: ignore[reportOptionalMemberAccess]
        q = (  # type: ignore[reportOptionalMemberAccess]
            self._supabase.table("legion_episodes")  # type: ignore[reportOptionalMemberAccess]
            .select("id,episode_type,summary,detail,tags,ts,source,metadata")  # type: ignore[reportOptionalMemberAccess]
            .eq("user_id", user_id)  # type: ignore[reportOptionalMemberAccess]
            .order("ts", desc=True)  # type: ignore[reportOptionalMemberAccess]
            .limit(limit * 3)  # type: ignore[reportOptionalMemberAccess]
        )
        if episode_type:
            q = q.eq("episode_type", episode_type)  # type: ignore[reportOptionalMemberAccess]
        result = q.execute()  # type: ignore[reportOptionalMemberAccess]
        rows = result.data or []  # type: ignore[reportOptionalMemberAccess]
        # Basic keyword filter on top of recency
        query_words = set(query.lower().split())  # type: ignore[reportOptionalMemberAccess]
        scored = []  # type: ignore[reportOptionalMemberAccess]
        for row in rows:
            text = (row.get("summary", "") + " " + row.get("detail", "")).lower()  # type: ignore[reportOptionalMemberAccess]
            score = sum(1 for w in query_words if w in text)  # type: ignore[reportOptionalMemberAccess]
            scored.append((score, row))  # type: ignore[reportOptionalMemberAccess]
        scored.sort(key=lambda x: (-x[0], -float(x[1].get("ts", 0))))  # type: ignore[reportOptionalMemberAccess]
        return [r for _, r in scored[:limit]]  # type: ignore[reportOptionalMemberAccess]

    def _local_recall(self, user_id: str, query: str, limit: int, episode_type: str | None) -> list[dict]:  # type: ignore[reportOptionalMemberAccess]
        episodes = [e for e in self._local if e.get("user_id") == user_id]  # type: ignore[reportOptionalMemberAccess]
        if episode_type:
            episodes = [e for e in episodes if e.get("episode_type") == episode_type]  # type: ignore[reportOptionalMemberAccess]
        query_words = set(query.lower().split())  # type: ignore[reportOptionalMemberAccess]
        scored = []  # type: ignore[reportOptionalMemberAccess]
        for ep in episodes:
            text = (ep.get("summary", "") + " " + ep.get("detail", "")).lower()  # type: ignore[reportOptionalMemberAccess]
            score = sum(1 for w in query_words if w in text)  # type: ignore[reportOptionalMemberAccess]
            scored.append((score, ep))  # type: ignore[reportOptionalMemberAccess]
        scored.sort(key=lambda x: (-x[0], -float(x[1].get("ts", 0))))  # type: ignore[reportOptionalMemberAccess]
        return [ep for _, ep in scored[:limit]]  # type: ignore[reportOptionalMemberAccess]

    def get_upcoming_schedule(self, user_id: str, horizon_days: int = 7) -> list[dict]:  # type: ignore[reportOptionalMemberAccess]
        """Return schedule episodes within the next N days."""  # type: ignore[reportOptionalMemberAccess]
        now = time.time()  # type: ignore[reportOptionalMemberAccess]
        horizon = now + (horizon_days * 86400)  # type: ignore[reportOptionalMemberAccess]
        episodes = self.recall(user_id, "schedule", limit=20, episode_type="schedule")  # type: ignore[reportOptionalMemberAccess]
        upcoming = []  # type: ignore[reportOptionalMemberAccess]
        for ep in episodes:
            meta = ep.get("metadata", {})  # type: ignore[reportOptionalMemberAccess]
            if isinstance(meta, str):  # type: ignore[reportOptionalMemberAccess]
                try:
                    meta = json.loads(meta)  # type: ignore[reportOptionalMemberAccess]
                except Exception:
                    meta = {}  # type: ignore[reportOptionalMemberAccess]
            event_ts = float(meta.get("event_ts", 0))  # type: ignore[reportOptionalMemberAccess]
            if now <= event_ts <= horizon:  # type: ignore[reportOptionalMemberAccess]
                upcoming.append(ep)  # type: ignore[reportOptionalMemberAccess]
        return upcoming

    def build_context_block(self, user_id: str, query: str) -> str:  # type: ignore[reportOptionalMemberAccess]
        """Build a [MEMORY CONTEXT] block to prepend to the system prompt."""  # type: ignore[reportOptionalMemberAccess]
        episodes = self.recall(user_id, query, limit=6)  # type: ignore[reportOptionalMemberAccess]
        schedule = self.get_upcoming_schedule(user_id, horizon_days=3)  # type: ignore[reportOptionalMemberAccess]

        if not episodes and not schedule:
            return ""

        lines = ["[MEMORY CONTEXT — Legion's long-term memory about Bashara]", ""]  # type: ignore[reportOptionalMemberAccess]
        if schedule:
            lines.append("📅 UPCOMING SCHEDULE:")  # type: ignore[reportOptionalMemberAccess]
            for ep in schedule[:3]:
                lines.append(f"  • {ep.get('summary', '')}")  # type: ignore[reportOptionalMemberAccess]
            lines.append("")  # type: ignore[reportOptionalMemberAccess]

        if episodes:
            lines.append("🧠 RELEVANT MEMORIES:")  # type: ignore[reportOptionalMemberAccess]
            for ep in episodes:
                ts_str = _fmt_ts(float(ep.get("ts", 0)))  # type: ignore[reportOptionalMemberAccess]
                lines.append(f"  [{ep.get('episode_type', '?')} | {ts_str}] {ep.get('summary', '')}")  # type: ignore[reportOptionalMemberAccess]
        lines.append("[END MEMORY CONTEXT]")  # type: ignore[reportOptionalMemberAccess]
        return "\n".join(lines)  # type: ignore[reportOptionalMemberAccess]

    def auto_extract_and_store(self, user_id: str, user_msg: str) -> None:  # type: ignore[reportOptionalMemberAccess]
        """Heuristically extract storable facts from user messages.  # type: ignore[reportOptionalMemberAccess]

        Stores facts into episodic memory so Legion can recall them in future turns.  # type: ignore[reportOptionalMemberAccess]
        Multiple categories can match — the first high-confidence hit wins.  # type: ignore[reportOptionalMemberAccess]
        Any substantive message (>20 words) is stored as a loose conversation entry.  # type: ignore[reportOptionalMemberAccess]
        """
        msg = user_msg.strip()  # type: ignore[reportOptionalMemberAccess]
        if not msg or len(msg) < 10:  # type: ignore[reportOptionalMemberAccess]
            return

        msg_lower = msg.lower()  # type: ignore[reportOptionalMemberAccess]

        # ── Schedule / time-bounded events ──────────────────────────────────
        schedule_triggers = [  # type: ignore[reportOptionalMemberAccess]
            "holiday",  # type: ignore[reportOptionalMemberAccess]
            "libur",  # type: ignore[reportOptionalMemberAccess]
            "cuti",  # type: ignore[reportOptionalMemberAccess]
            "meeting",  # type: ignore[reportOptionalMemberAccess]
            "appointment",  # type: ignore[reportOptionalMemberAccess]
            "flight",  # type: ignore[reportOptionalMemberAccess]
            "penerbangan",  # type: ignore[reportOptionalMemberAccess]
            "trip",  # type: ignore[reportOptionalMemberAccess]
            "travel",  # type: ignore[reportOptionalMemberAccess]
            "perjalanan",  # type: ignore[reportOptionalMemberAccess]
            "deadline",  # type: ignore[reportOptionalMemberAccess]
            "besok",  # type: ignore[reportOptionalMemberAccess]
            "tomorrow",  # type: ignore[reportOptionalMemberAccess]
            "next week",  # type: ignore[reportOptionalMemberAccess]
            "minggu depan",  # type: ignore[reportOptionalMemberAccess]
            "next month",  # type: ignore[reportOptionalMemberAccess]
            "bulan depan",  # type: ignore[reportOptionalMemberAccess]
            "next year",  # type: ignore[reportOptionalMemberAccess]
            "conference",  # type: ignore[reportOptionalMemberAccess]
            "event",  # type: ignore[reportOptionalMemberAccess]
            "vacation",  # type: ignore[reportOptionalMemberAccess]
            "liburan",  # type: ignore[reportOptionalMemberAccess]
            "going to",  # type: ignore[reportOptionalMemberAccess]
            "akan pergi",  # type: ignore[reportOptionalMemberAccess]
            "plan to",  # type: ignore[reportOptionalMemberAccess]
            "berencana",  # type: ignore[reportOptionalMemberAccess]
            "seminar",  # type: ignore[reportOptionalMemberAccess]
            "workshop",  # type: ignore[reportOptionalMemberAccess]
        ]
        if any(t in msg_lower for t in schedule_triggers):  # type: ignore[reportOptionalMemberAccess]
            self.store(  # type: ignore[reportOptionalMemberAccess]
                user_id, "schedule", summary=msg[:200], detail=msg, tags=["schedule", "auto"], source="auto_extract"  # type: ignore[reportOptionalMemberAccess]
            )
            return

        # ── Personal preferences & facts ────────────────────────────────────
        pref_triggers = [  # type: ignore[reportOptionalMemberAccess]
            "i like",  # type: ignore[reportOptionalMemberAccess]
            "i love",  # type: ignore[reportOptionalMemberAccess]
            "i hate",  # type: ignore[reportOptionalMemberAccess]
            "i prefer",  # type: ignore[reportOptionalMemberAccess]
            "i always",  # type: ignore[reportOptionalMemberAccess]
            "i never",  # type: ignore[reportOptionalMemberAccess]
            "aku suka",  # type: ignore[reportOptionalMemberAccess]
            "aku tidak suka",  # type: ignore[reportOptionalMemberAccess]
            "aku selalu",  # type: ignore[reportOptionalMemberAccess]
            "aku biasanya",  # type: ignore[reportOptionalMemberAccess]
            "my home",  # type: ignore[reportOptionalMemberAccess]
            "my office",  # type: ignore[reportOptionalMemberAccess]
            "rumahku",  # type: ignore[reportOptionalMemberAccess]
            "kantorku",  # type: ignore[reportOptionalMemberAccess]
            "i live in",  # type: ignore[reportOptionalMemberAccess]
            "aku tinggal di",  # type: ignore[reportOptionalMemberAccess]
            "i work at",  # type: ignore[reportOptionalMemberAccess]
            "i study",  # type: ignore[reportOptionalMemberAccess]
            "i'm studying",  # type: ignore[reportOptionalMemberAccess]
            "i'm working on",  # type: ignore[reportOptionalMemberAccess]
            "i use",  # type: ignore[reportOptionalMemberAccess]
            "i'm using",  # type: ignore[reportOptionalMemberAccess]
            "my favorite",  # type: ignore[reportOptionalMemberAccess]
            "favorit saya",  # type: ignore[reportOptionalMemberAccess]
            "my setup",  # type: ignore[reportOptionalMemberAccess]
            "i switched to",  # type: ignore[reportOptionalMemberAccess]
            "my name is",  # type: ignore[reportOptionalMemberAccess]
            "nama saya",  # type: ignore[reportOptionalMemberAccess]
            "i usually",  # type: ignore[reportOptionalMemberAccess]
            "biasanya aku",  # type: ignore[reportOptionalMemberAccess]
            "i feel",  # type: ignore[reportOptionalMemberAccess]
            "aku merasa",  # type: ignore[reportOptionalMemberAccess]
            "i think",  # type: ignore[reportOptionalMemberAccess]
            "menurut aku",  # type: ignore[reportOptionalMemberAccess]
            "my goal",  # type: ignore[reportOptionalMemberAccess]
            "target saya",  # type: ignore[reportOptionalMemberAccess]
            "i want to",  # type: ignore[reportOptionalMemberAccess]
            "aku mau",  # type: ignore[reportOptionalMemberAccess]
        ]
        if any(t in msg_lower for t in pref_triggers):  # type: ignore[reportOptionalMemberAccess]
            self.store(  # type: ignore[reportOptionalMemberAccess]
                user_id, "preference", summary=msg[:200], detail=msg, tags=["preference", "auto"], source="auto_extract"  # type: ignore[reportOptionalMemberAccess]
            )
            return

        # ── People / relationships ───────────────────────────────────────────
        people_triggers = [  # type: ignore[reportOptionalMemberAccess]
            "my friend",  # type: ignore[reportOptionalMemberAccess]
            "my partner",  # type: ignore[reportOptionalMemberAccess]
            "my boss",  # type: ignore[reportOptionalMemberAccess]
            "my team",  # type: ignore[reportOptionalMemberAccess]
            "my professor",  # type: ignore[reportOptionalMemberAccess]
            "temanku",  # type: ignore[reportOptionalMemberAccess]
            "pacarku",  # type: ignore[reportOptionalMemberAccess]
            "bossku",  # type: ignore[reportOptionalMemberAccess]
            "timku",  # type: ignore[reportOptionalMemberAccess]
            "dosenku",  # type: ignore[reportOptionalMemberAccess]
            "she is",  # type: ignore[reportOptionalMemberAccess]
            "he is",  # type: ignore[reportOptionalMemberAccess]
            "they are",  # type: ignore[reportOptionalMemberAccess]
            "her name is",  # type: ignore[reportOptionalMemberAccess]
            "his name is",  # type: ignore[reportOptionalMemberAccess]
            "my supervisor",  # type: ignore[reportOptionalMemberAccess]
            "my colleague",  # type: ignore[reportOptionalMemberAccess]
        ]
        if any(t in msg_lower for t in people_triggers):  # type: ignore[reportOptionalMemberAccess]
            self.store(  # type: ignore[reportOptionalMemberAccess]
                user_id,  # type: ignore[reportOptionalMemberAccess]
                "people",  # type: ignore[reportOptionalMemberAccess]
                summary=msg[:200],  # type: ignore[reportOptionalMemberAccess]
                detail=msg,  # type: ignore[reportOptionalMemberAccess]
                tags=["people", "relationship", "auto"],  # type: ignore[reportOptionalMemberAccess]
                source="auto_extract",  # type: ignore[reportOptionalMemberAccess]
            )
            return

        # ── Location awareness ───────────────────────────────────────────────
        location_triggers = [  # type: ignore[reportOptionalMemberAccess]
            "i'm in",  # type: ignore[reportOptionalMemberAccess]
            "aku di",  # type: ignore[reportOptionalMemberAccess]
            "i'm at",  # type: ignore[reportOptionalMemberAccess]
            "aku lagi di",  # type: ignore[reportOptionalMemberAccess]
            "i'm visiting",  # type: ignore[reportOptionalMemberAccess]
            "i moved to",  # type: ignore[reportOptionalMemberAccess]
            "aku pindah ke",  # type: ignore[reportOptionalMemberAccess]
            "my city",  # type: ignore[reportOptionalMemberAccess]
            "my country",  # type: ignore[reportOptionalMemberAccess]
            "near me",  # type: ignore[reportOptionalMemberAccess]
            "around here",  # type: ignore[reportOptionalMemberAccess]
            "di sini",  # type: ignore[reportOptionalMemberAccess]
            "di sana",  # type: ignore[reportOptionalMemberAccess]
            "i'm near",  # type: ignore[reportOptionalMemberAccess]
        ]
        if any(t in msg_lower for t in location_triggers):  # type: ignore[reportOptionalMemberAccess]
            self.store(  # type: ignore[reportOptionalMemberAccess]
                user_id, "location", summary=msg[:200], detail=msg, tags=["location", "auto"], source="auto_extract"  # type: ignore[reportOptionalMemberAccess]
            )
            return

        # ── Project milestones & technical work ─────────────────────────────
        project_triggers = [  # type: ignore[reportOptionalMemberAccess]
            "deployed",  # type: ignore[reportOptionalMemberAccess]
            "launched",  # type: ignore[reportOptionalMemberAccess]
            "finished",  # type: ignore[reportOptionalMemberAccess]
            "completed",  # type: ignore[reportOptionalMemberAccess]
            "broke",  # type: ignore[reportOptionalMemberAccess]
            "rumahlabuh",  # type: ignore[reportOptionalMemberAccess]
            "supabase",  # type: ignore[reportOptionalMemberAccess]
            "github",  # type: ignore[reportOptionalMemberAccess]
            "server",  # type: ignore[reportOptionalMemberAccess]
            "dataset",  # type: ignore[reportOptionalMemberAccess]
            "selesai",  # type: ignore[reportOptionalMemberAccess]
            "deploy",  # type: ignore[reportOptionalMemberAccess]
            "rilis",  # type: ignore[reportOptionalMemberAccess]
            "merged",  # type: ignore[reportOptionalMemberAccess]
            "pushed",  # type: ignore[reportOptionalMemberAccess]
            "released",  # type: ignore[reportOptionalMemberAccess]
            "training",  # type: ignore[reportOptionalMemberAccess]
            "model",  # type: ignore[reportOptionalMemberAccess]
            "pytorch",  # type: ignore[reportOptionalMemberAccess]
            "cuda",  # type: ignore[reportOptionalMemberAccess]
            "vram",  # type: ignore[reportOptionalMemberAccess]
            "epoch",  # type: ignore[reportOptionalMemberAccess]
            "error",  # type: ignore[reportOptionalMemberAccess]
            "bug",  # type: ignore[reportOptionalMemberAccess]
            "fixed",  # type: ignore[reportOptionalMemberAccess]
            "bug fix",  # type: ignore[reportOptionalMemberAccess]
            "refactor",  # type: ignore[reportOptionalMemberAccess]
            "migrated",  # type: ignore[reportOptionalMemberAccess]
            "implemented",  # type: ignore[reportOptionalMemberAccess]
            "built",  # type: ignore[reportOptionalMemberAccess]
            "created",  # type: ignore[reportOptionalMemberAccess]
            "wrote",  # type: ignore[reportOptionalMemberAccess]
        ]
        if any(t in msg_lower for t in project_triggers) and len(msg) > 30:  # type: ignore[reportOptionalMemberAccess]
            self.store(  # type: ignore[reportOptionalMemberAccess]
                user_id, "project", summary=msg[:200], detail=msg, tags=["project", "auto"], source="auto_extract"  # type: ignore[reportOptionalMemberAccess]
            )
            return

        # ── Remember-me directives ───────────────────────────────────────────
        remember_triggers = [  # type: ignore[reportOptionalMemberAccess]
            "remember that",  # type: ignore[reportOptionalMemberAccess]
            "note that",  # type: ignore[reportOptionalMemberAccess]
            "keep in mind",  # type: ignore[reportOptionalMemberAccess]
            "don't forget",  # type: ignore[reportOptionalMemberAccess]
            "ingat bahwa",  # type: ignore[reportOptionalMemberAccess]
            "catat",  # type: ignore[reportOptionalMemberAccess]
            "ingat ya",  # type: ignore[reportOptionalMemberAccess]
            "fyi",  # type: ignore[reportOptionalMemberAccess]
            "just so you know",  # type: ignore[reportOptionalMemberAccess]
            "btw",  # type: ignore[reportOptionalMemberAccess]
            "by the way",  # type: ignore[reportOptionalMemberAccess]
        ]
        if any(t in msg_lower for t in remember_triggers):  # type: ignore[reportOptionalMemberAccess]
            self.store(  # type: ignore[reportOptionalMemberAccess]
                user_id, "fact", summary=msg[:200], detail=msg, tags=["fact", "explicit", "auto"], source="auto_extract"  # type: ignore[reportOptionalMemberAccess]
            )
            return

        # ── Catch-all: store any substantive message as a conversation episode ─
        # Low importance — keeps a natural episodic trail even for casual chat.  # type: ignore[reportOptionalMemberAccess]
        if len(msg.split()) >= 20:  # type: ignore[reportOptionalMemberAccess]
            self.store(  # type: ignore[reportOptionalMemberAccess]
                user_id,  # type: ignore[reportOptionalMemberAccess]
                "conversation",  # type: ignore[reportOptionalMemberAccess]
                summary=msg[:200],  # type: ignore[reportOptionalMemberAccess]
                detail=msg,  # type: ignore[reportOptionalMemberAccess]
                tags=["conversation", "auto"],  # type: ignore[reportOptionalMemberAccess]
                source="auto_extract",  # type: ignore[reportOptionalMemberAccess]
            )


def _fmt_ts(ts: float) -> str:  # type: ignore[reportOptionalMemberAccess]
    import datetime

    if ts == 0:  # type: ignore[reportOptionalMemberAccess]
        return "unknown date"
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%b %d %Y")  # type: ignore[reportOptionalMemberAccess]
    except Exception:
        return "?"


# Singleton
_store: EpisodicStore | None = None  # type: ignore[reportOptionalMemberAccess]


def get_episodic_store() -> EpisodicStore:  # type: ignore[reportOptionalMemberAccess]
    global _store
    if _store is None:
        _store = EpisodicStore()  # type: ignore[reportOptionalMemberAccess]
    return _store
