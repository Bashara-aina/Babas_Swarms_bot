"""Persistent user profile memory."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROFILE_PATH = Path.home() / ".legionswarm" / "memory" / "user_profile.json"

DEFAULT_PROFILE: dict[str, Any] = {
    "name": "Bashara",
    "location": "Tokyo, Japan (Koto City)",
    "timezone": "Asia/Tokyo",
    "hardware": "RTX 3060 12GB, 64GB RAM, 5TB storage, Ubuntu 22.04",
    "occupation": "Data Science Master's student / AI researcher",
    "primary_languages": ["Python", "TypeScript"],
    "expertise": [
        "pose estimation",
        "activity recognition",
        "multi-agent AI",
        "ML model training",
        "VPS deployment",
    ],
    "current_projects": [],
    "preferences": {
        "response_style": "direct, technical, concise — not verbose",
        "code_style": "Python 3.10+, type hints, async-first",
        "ai_models": "prefers local when possible, free-tier API as fallback",
    },
    "known_facts": [],
    "interaction_patterns": [],
    "last_updated": None,
}


class UserProfile:
    def __init__(self) -> None:
        self._profile: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if PROFILE_PATH.exists():
            self._profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        else:
            self._profile = dict(DEFAULT_PROFILE)
            self._save()

    def _save(self) -> None:
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._profile["last_updated"] = datetime.now().isoformat()
        PROFILE_PATH.write_text(json.dumps(self._profile, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self._profile.get(key, default)

    def update(self, key: str, value: Any) -> None:
        self._profile[key] = value
        self._save()

    def add_known_fact(self, fact: str) -> None:
        facts = self._profile.setdefault("known_facts", [])
        if fact not in facts:
            facts.append(fact)
            self._save()

    def add_pattern(self, pattern: str) -> None:
        patterns = self._profile.setdefault("interaction_patterns", [])
        if pattern not in patterns:
            patterns.append(pattern)
            if len(patterns) > 50:
                patterns.pop(0)
            self._save()

    def to_prompt_block(self) -> str:
        p = self._profile
        facts = "\n".join(f"  - {fact}" for fact in p.get("known_facts", [])[-20:])
        patterns = "\n".join(f"  - {pat}" for pat in p.get("interaction_patterns", [])[-10:])
        prefs = "\n".join(f"  {k}: {v}" for k, v in p.get("preferences", {}).items())
        return f"""[USER PROFILE — permanent knowledge about this person]
Name: {p.get("name")}
Location: {p.get("location")} | Timezone: {p.get("timezone")}
Hardware: {p.get("hardware")}
Occupation: {p.get("occupation")}
Languages: {", ".join(p.get("primary_languages", []))}
Expertise: {", ".join(p.get("expertise", []))}
Preferences:
{prefs}
Known facts about them:
{facts if facts else "  (none yet — learn as you go)"}
Observed patterns:
{patterns if patterns else "  (none yet — observe and update)"}"""

    def full(self) -> dict[str, Any]:
        return dict(self._profile)
