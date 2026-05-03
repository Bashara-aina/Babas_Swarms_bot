"""User profile — persistent personal facts about Bashara.

Stored in Supabase (legion_profile table) with local JSON fallback.
This is what lets Legion say 'since you're in Koto City' or
'you mentioned rumahlabuh.com uses Supabase' without being told every time.

Profile keys (built-in defaults for Bashara, overridable at runtime):
  location        — current city / timezone
  home            — home address / area
  projects        — list of active projects
  preferences     — dict of preferences
  schedule        — recurring commitments
  contacts        — key people Legion should know
"""
from __future__ import annotations

import contextlib
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_FALLBACK_PATH = Path("data/user_profile.json")
_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Default profile for Bashara (bootstrapped on first run) ──────────────────
_DEFAULT_PROFILE: dict = {
    "name": "Bashara",
    "location": "Koto City, Tokyo, Japan",
    "timezone": "Asia/Tokyo",
    "home": "Koto City, Tokyo",
    "languages": ["Indonesian", "English", "Japanese (basic)"],
    "projects": [
        {
            "name": "rumahlabuh.com",
            "description": "Rental/hospitality business website",
            "stack": ["Next.js", "TypeScript", "Supabase"],
            "status": "active",
        },
        {
            "name": "Babas_Swarms_bot",
            "description": "Personal AI assistant Telegram bot",
            "stack": ["Python", "aiogram", "litellm", "Supabase"],
            "status": "active",
        },
    ],
    "workstation": {
        "os": "Linux (Ubuntu)",
        "gpu": "RTX 3060 12GB",
        "python": "3.13",
        "ml_frameworks": ["PyTorch", "CUDA"],
    },
    "preferences": {
        "response_style": "casual, direct, no fluff",
        "language_mix": "Indonesian + English code-switching",
        "humor": True,
        "debate": True,
    },
    "education": "Master's in Data Science / AI/ML",
    "interests": [
        "human pose estimation",
        "activity recognition",
        "multi-agent AI systems",
        "VPS/cloud infrastructure",
    ],
    "known_facts": [],
    "interaction_patterns": [],
    "schedule_notes": [],
    "contacts_highlight": [],
    "world": {
        "planned_travel": "",
        "business_priorities": [
            "rumahlabuh.com — bookings, site health, Supabase",
            "Legion bot — reliability, memory, routing",
        ],
        "quiet_hours_local": "00:00–07:00 (avoid non-urgent pings)",
    },
}


class UserProfileStore:
    """Persistent user profile — Supabase + local JSON fallback."""

    def __init__(self, user_id: str = "bashara") -> None:
        self.user_id = user_id
        self._supabase = None
        self._use_supabase = False
        self._profile: dict = {}
        self._init_supabase()
        self._load()

    def _init_supabase(self) -> None:
        url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_SERVICE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        )
        if not url or not key:
            return
        try:
            from supabase import create_client
            self._supabase = create_client(url, key)
            self._use_supabase = True
        except Exception as e:
            logger.warning("[UserProfile] Supabase init failed: %s", e)

    def _load(self) -> None:
        """Load profile from Supabase or local file. Bootstrap defaults if empty."""
        loaded = None

        if self._use_supabase:
            try:
                result = (
                    self._supabase.table("legion_profile")
                    .select("data")
                    .eq("user_id", self.user_id)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    raw = result.data[0].get("data", "{}")
                    loaded = json.loads(raw) if isinstance(raw, str) else raw
            except Exception as e:
                logger.warning("[UserProfile] Supabase load failed: %s", e)

        if not loaded and _FALLBACK_PATH.exists():
            with contextlib.suppress(Exception):
                loaded = json.loads(_FALLBACK_PATH.read_text(encoding="utf-8"))

        # Merge with defaults (defaults fill in any missing keys)
        self._profile = {**_DEFAULT_PROFILE, **(loaded or {})}
        if not loaded:
            self._save()  # bootstrap
            logger.info("[UserProfile] Bootstrapped default profile for %s", self.user_id)

    def _save(self) -> None:
        data_str = json.dumps(self._profile, indent=2, ensure_ascii=False)

        if self._use_supabase:
            try:
                self._supabase.table("legion_profile").upsert(
                    {"user_id": self.user_id, "data": data_str}
                ).execute()
                return
            except Exception as e:
                logger.warning("[UserProfile] Supabase save failed: %s — saving locally", e)

        _FALLBACK_PATH.write_text(data_str, encoding="utf-8")

    # ── Public API ────────────────────────────────────────────────────────

    def get(self, key: str, default: object = None) -> object:
        return self._profile.get(key, default)

    def set(self, key: str, value: object) -> None:
        self._profile[key] = value
        self._save()

    def update(self, updates: dict) -> None:
        self._profile.update(updates)
        self._save()

    def build_context_block(self) -> str:
        """Build a compact profile block for system prompt injection."""
        p = self._profile
        projects = p.get("projects", [])
        proj_str = ", ".join(pr.get("name", "") for pr in projects) if projects else "none"
        interests = p.get("interests", [])
        ws = p.get("workstation", {})

        lines = [
            "[BASHARA'S PROFILE — know this, don't repeat it back]",
            f"Name: {p.get('name', 'Bashara')} | "
            f"Location: {p.get('location', 'Tokyo')} | "
            f"Timezone: {p.get('timezone', 'Asia/Tokyo')}",
            f"Home / base: {p.get('home', '')}",
            f"Active projects: {proj_str}",
            f"Workstation: {ws.get('os', 'Linux')}, "
            f"{ws.get('gpu', 'RTX 3060')}, Python {ws.get('python', '3.x')}",
            f"Interests: {', '.join(interests[:6])}",
            f"Preferences: {p.get('preferences', {}).get('response_style', 'casual')}",
        ]
        sched = p.get("schedule_notes") or []
        if sched:
            lines.append("Schedule notes: " + "; ".join(str(s) for s in sched[:5]))
        ch = p.get("contacts_highlight") or []
        if ch:
            lines.append("Key people: " + "; ".join(str(c) for c in ch[:5]))
        facts = p.get("known_facts") or []
        if facts:
            lines.append("Known facts: " + "; ".join(str(f) for f in facts[:6]))
        world = p.get("world") if isinstance(p.get("world"), dict) else {}
        if world:
            if world.get("planned_travel"):
                lines.append(f"Planned travel: {world.get('planned_travel')}")
            bp = world.get("business_priorities") or []
            if bp:
                lines.append("Business priorities: " + "; ".join(str(x) for x in bp[:4]))
            if world.get("quiet_hours_local"):
                lines.append(f"Quiet hours: {world.get('quiet_hours_local')}")
        lines.append("[END PROFILE]")
        return "\n".join(lines)


# Singleton
_profile_store: UserProfileStore | None = None


def get_user_profile(user_id: str = "bashara") -> UserProfileStore:
    global _profile_store
    if _profile_store is None:
        _profile_store = UserProfileStore(user_id)
    return _profile_store


class UserProfile(UserProfileStore):
    """:class:`core.memory.memory_manager.MemoryManager` expects ``to_prompt_block``,
    ``add_known_fact``, and ``add_pattern`` — this subclass maps them onto the store.
    """

    def to_prompt_block(self) -> str:
        return self.build_context_block()

    def add_known_fact(self, fact: str) -> None:
        facts = list(self.get("known_facts") or [])
        if fact not in facts:
            facts.append(fact)
            self.set("known_facts", facts)

    def add_pattern(self, pattern: str) -> None:
        patterns = list(self.get("interaction_patterns") or [])
        if pattern not in patterns:
            patterns.append(pattern)
            self.set("interaction_patterns", patterns)
