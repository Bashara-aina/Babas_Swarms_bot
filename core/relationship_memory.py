"""Relationship memory — tracks the Legion-Bashara working relationship over time.

Persists to ~/.legionswarm/relationship.json and injects a concise context block
into every system prompt so Legion knows:
  - How long we've been working together
  - How many conversations total
  - What topics/projects recur most
  - What the last few sessions focused on
  - What language and response style Bashara prefers

All operations are synchronous and lightweight — this is called before every LLM call.
Never raises. Falls back gracefully if the file is missing or corrupt.
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_MEMORY_DIR = Path(os.path.expanduser("~/.legionswarm"))
_RELATIONSHIP_FILE = _MEMORY_DIR / "relationship.json"

# Topics we track — each maps to keyword triggers
_TOPIC_MAP = {
    "thesis / pose estimation": [
        "thesis", "pose", "activity", "workernet", "ikea asm", "resnet",
        "epoch", "loss", "training", "dataset", "annotation",
    ],
    "rumahlabuh / property": [
        "rumahlabuh", "booking", "property", "villa", "supabase", "rls",
        "guest", "reservation", "payment",
    ],
    "system admin / devops": [
        "server", "ssh", "docker", "deploy", "nginx", "systemd", "service",
        "cron", "backup", "disk", "cpu", "ram", "gpu",
    ],
    "coding / debugging": [
        "bug", "error", "fix", "code", "function", "class", "import",
        "module", "python", "typescript", "git", "branch", "pull request",
    ],
    "research / papers": [
        "paper", "arxiv", "research", "study", "literature", "citation",
        "method", "experiment", "benchmark",
    ],
    "automation / scraping": [
        "scrape", "playwright", "automation", "schedule", "cron", "webhook",
        "api", "endpoint", "fetch",
    ],
    "AI / ML infrastructure": [
        "model", "inference", "ollama", "litellm", "groq", "cerebras",
        "agent", "llm", "swarm", "legion",
    ],
    "email / communication": [
        "email", "imap", "smtp", "whatsapp", "telegram", "message", "reply",
    ],
}


def _load() -> dict:
    """Load relationship data from disk. Returns empty dict if missing/corrupt."""
    try:
        if _RELATIONSHIP_FILE.exists():
            return json.loads(_RELATIONSHIP_FILE.read_text(encoding="utf-8"))
    except Exception as _e:
        logger.warning("relationship_memory: load failed: %s", _e)
    return {}


def _save(data: dict) -> None:
    """Save relationship data to disk. Never raises."""
    try:
        _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        _RELATIONSHIP_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as _e:
        logger.warning("relationship_memory: save failed: %s", _e)


def _detect_topics(message: str) -> list[str]:
    """Return list of topic keys that match keywords in the message."""
    if not message:
        return []
    msg_lower = message.lower()
    matched = []
    for topic, keywords in _TOPIC_MAP.items():
        if any(kw in msg_lower for kw in keywords):
            matched.append(topic)
    return matched


def _detect_language(message: str) -> str:
    """Heuristic: detect if message is Indonesian or English."""
    indonesian_words = [
        "aku", "gue", "kamu", "dia", "kita", "kami", "mereka", "yang", "dan",
        "atau", "tapi", "untuk", "dari", "ke", "di", "pada", "dengan", "bisa",
        "tidak", "sudah", "belum", "mau", "ada", "ini", "itu", "juga", "seperti",
        "bagaimana", "kenapa", "apa", "gimana", "gak", "nih", "deh", "dong",
        "coba", "tolong", "bantu", "cek", "lihat", "buat",
    ]
    words = re.findall(r'\b\w+\b', message.lower())
    if not words:
        return "english"
    id_hits = sum(1 for w in words if w in indonesian_words)
    ratio = id_hits / len(words)
    return "indonesian" if ratio > 0.1 else "english"


def record_interaction(user_message: str, response_length: int = 0) -> None:
    """Update relationship data after each interaction.

    Call this after each user message. Tracks:
    - Total conversation count
    - Topic frequency
    - Recent session topics (last 5 sessions rolling)
    - Language preference
    - First interaction date
    """
    data = _load()
    now_iso = datetime.now(UTC).isoformat()

    # First interaction date
    if "first_interaction" not in data:
        data["first_interaction"] = now_iso

    # Conversation counter
    data["conversation_count"] = data.get("conversation_count", 0) + 1

    # Topic tracking
    topics_counter = Counter(data.get("topic_counts", {}))
    matched = _detect_topics(user_message)
    for topic in matched:
        topics_counter[topic] += 1
    data["topic_counts"] = dict(topics_counter)

    # Recent topics (rolling last 10 interactions)
    recent = data.get("recent_topics", [])
    recent.extend(matched)
    data["recent_topics"] = recent[-20:]  # keep last 20 topic hits

    # Language preference (rolling vote)
    lang_counts = Counter(data.get("language_counts", {}))
    detected_lang = _detect_language(user_message)
    lang_counts[detected_lang] += 1
    data["language_counts"] = dict(lang_counts)

    # Response length preference signal (short vs long preference)
    length_history = data.get("response_length_history", [])
    length_history.append(response_length)
    data["response_length_history"] = length_history[-50:]  # keep last 50

    # Last interaction timestamp
    data["last_interaction"] = now_iso

    _save(data)


def get_relationship_context() -> str | None:
    """Build a concise relationship context block for injection into the system prompt.

    Returns None if no relationship data exists yet (first ever interaction).
    Always returns a compact block (< 300 chars) when data is available.
    """
    data = _load()
    if not data:
        return None

    lines: list[str] = []

    # How long we've been working together
    first_str = data.get("first_interaction", "")
    if first_str:
        try:
            first_dt = datetime.fromisoformat(first_str)
            now_dt = datetime.now(UTC)
            delta = now_dt - first_dt
            days = delta.days
            if days == 0:
                duration = "first session today"
            elif days < 7:
                duration = f"{days} days"
            elif days < 30:
                weeks = days // 7
                duration = f"{weeks} week{'s' if weeks > 1 else ''}"
            elif days < 365:
                months = days // 30
                duration = f"{months} month{'s' if months > 1 else ''}"
            else:
                years = days // 365
                months = (days % 365) // 30
                duration = f"{years}yr {months}mo" if months else f"{years} year{'s' if years > 1 else ''}"
            lines.append(f"Working together: {duration}")
        except Exception:
            pass

    # Conversation count
    count = data.get("conversation_count", 0)
    if count > 1:
        lines.append(f"Total exchanges: {count}")

    # Top recurring topics (max 3)
    topic_counts = data.get("topic_counts", {})
    if topic_counts:
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        topic_str = ", ".join(t for t, _ in top_topics)
        lines.append(f"Most discussed: {topic_str}")

    # Recent session focus (from recent_topics, last 10 hits)
    recent = data.get("recent_topics", [])
    if recent:
        recent_counts = Counter(recent[-10:])
        top_recent = [t for t, _ in recent_counts.most_common(2)]
        if top_recent:
            lines.append(f"Recent focus: {', '.join(top_recent)}")

    # Language preference
    lang_counts = data.get("language_counts", {})
    if lang_counts:
        dominant = max(lang_counts, key=lang_counts.get)
        total = sum(lang_counts.values())
        pct = int(lang_counts[dominant] / total * 100)
        if pct >= 70:
            lines.append(f"Preferred language: {dominant} ({pct}% of messages)")
        else:
            lines.append("Language: mixed Indonesian/English")

    # Response length preference
    lengths = data.get("response_length_history", [])
    if len(lengths) >= 5:
        avg_len = sum(lengths) / len(lengths)
        if avg_len < 200:
            lines.append("Prefers: concise answers")
        elif avg_len > 800:
            lines.append("Prefers: detailed explanations")

    if not lines:
        return None

    return "[RELATIONSHIP CONTEXT]\n" + "\n".join(lines)
