"""tools/recallmax.py — Long-context memory compression and semantic recall injection.

Inspired by the antigravity-awesome-skills recallmax SKILL.md.
Provides:
  - compress_history(): prune + summarise conversation history >N turns
  - build_memory_context(): retrieve relevant memories and format for injection
  - should_store(): decide whether a turn should be persisted to memory
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_MAX_TURNS_VERBATIM = 6   # keep last N turns verbatim
_SUMMARY_THRESHOLD = 10   # compress when history exceeds this many turns


# ---------------------------------------------------------------------------
# Conversation compression
# ---------------------------------------------------------------------------

def compress_history(
    messages: list[dict[str, str]],
    keep_last: int = _MAX_TURNS_VERBATIM,
) -> list[dict[str, str]]:
    """If messages exceed threshold, replace early turns with a summary stub.

    The summary is a synthetic 'assistant' message that compresses dropped turns.
    Actual LLM-based summarisation happens in llm_client if available; otherwise
    a keyword-extraction fallback is used here.

    Returns a (potentially shorter) message list.
    """
    if len(messages) <= _SUMMARY_THRESHOLD:
        return messages

    # Separate system messages (always keep) from conversation turns
    system_msgs = [m for m in messages if m.get("role") == "system"]
    conv_msgs = [m for m in messages if m.get("role") != "system"]

    if len(conv_msgs) <= keep_last:
        return messages

    to_compress = conv_msgs[:-keep_last]
    to_keep = conv_msgs[-keep_last:]

    summary_text = _keyword_summary(to_compress)
    summary_msg = {
        "role": "assistant",
        "content": f"[SUMMARY turns 1-{len(to_compress)}]: {summary_text}",
    }

    compressed = system_msgs + [summary_msg] + to_keep
    logger.debug(
        "[recallmax] compressed %d → %d messages (kept last %d)",
        len(messages), len(compressed), keep_last,
    )
    return compressed


def _keyword_summary(messages: list[dict[str, str]]) -> str:
    """Fallback keyword-extraction summary when no LLM summariser is available."""
    lines: list[str] = []
    for m in messages:
        content = m.get("content", "")[:300]
        role = m.get("role", "?")
        if content:
            lines.append(f"[{role}] {content}")
    combined = " | ".join(lines)
    # Truncate to ~400 chars
    return combined[:400] + ("…" if len(combined) > 400 else "")


# ---------------------------------------------------------------------------
# Memory relevance & storage decisions
# ---------------------------------------------------------------------------

_STORE_PATTERNS = [
    r"\bremember\b", r"\bprefer\b", r"\balways\b", r"\bnever\b",
    r"\bmy (name|project|stack|preference|bot|api|key)\b",
    r"\bI (use|prefer|want|need|am)\b",
    r"\bfixed\b", r"\bsolved\b", r"\berror was\b",
    r"\bdecided\b", r"\bchose\b", r"\bwe agreed\b",
]
_STORE_RE = re.compile("|".join(_STORE_PATTERNS), re.IGNORECASE)

_SKIP_PATTERNS = [
    r"^(ok|okay|thanks|thank you|got it|sure|yes|no|yep|nope)\.?$",
    r"^\d+[\s\+\-\*\/\d]*$",  # pure arithmetic
]
_SKIP_RE = re.compile("|".join(_SKIP_PATTERNS), re.IGNORECASE)


def should_store(text: str) -> bool:
    """Return True if the text is worth persisting to long-term memory."""
    text = text.strip()
    if len(text) < 15:
        return False
    if _SKIP_RE.match(text):
        return False
    if _STORE_RE.search(text):
        return True
    return False


def extract_memory_tags(text: str) -> list[str]:
    """Heuristically assign memory tags to a piece of text."""
    tags: list[str] = []
    tl = text.lower()
    if any(w in tl for w in ["prefer", "always use", "never use", "my style"]):
        tags.append("#preference")
    if any(w in tl for w in ["project", "repo", "codebase", "stack", "bot"]):
        tags.append("#project")
    if any(w in tl for w in ["fixed", "solved", "error was", "bug", "traceback"]):
        tags.append("#error_fix")
    if any(w in tl for w in ["decided", "chose", "agreed", "will use", "going with"]):
        tags.append("#decision")
    if not tags:
        tags.append("#general")
    return tags


# ---------------------------------------------------------------------------
# Memory context builder (for injection into system prompt)
# ---------------------------------------------------------------------------

def build_memory_context(memories: list[dict[str, Any]], query: str = "") -> str:
    """Format a list of memory dicts into an injectable context block.

    Args:
        memories: list of dicts with at least 'content' key; optionally 'tags', 'created_at'
        query: the current user query (used for relevance sorting if embeddings unavailable)

    Returns:
        A formatted string block to prepend to the system prompt, or "" if no memories.
    """
    if not memories:
        return ""

    lines: list[str] = ["[MEMORY CONTEXT]"]
    for m in memories[:8]:  # cap at 8 memories to control context size
        content = m.get("content", "").strip()
        tags = m.get("tags") or extract_memory_tags(content)
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = [tags]
        tag_str = " ".join(tags) if tags else ""
        lines.append(f"- {content} {tag_str}")
    lines.append("[END MEMORY]")
    return "\n".join(lines) + "\n"


def memory_hash(text: str) -> str:
    """Short hash for deduplication of near-identical memories."""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()[:12]
