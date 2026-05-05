"""Memory skills using memory_manager and obsidian integration."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from pathlib import Path

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def _remember_handler(text: str) -> str:
    """Store a memory note using memory_manager."""
    # Extract the memory content - remove trigger keywords
    content = text
    for kw in ["remember", "note that", "save this", "remember that", "catat", "ingatkan"]:
        content = re.sub(rf"\b{kw}\b", "", content, flags=re.IGNORECASE).strip()

    if not content:
        return "What would you like me to remember?"

    try:
        from tools.memoryos_client import get_memoryos

        mos = get_memoryos("bashara")
        if mos:
            # Store with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            memory_text = f"[{timestamp}] {content}"
            await mos.add_memory(memory_text, {"type": "user_note", "source": "telegram"})  # type: ignore[reportArgumentType]
            return f"✅ Memory saved: {content[:100]}..."
        return "⚠️ MemoryOS not available. Memory not saved."
    except Exception as exc:
        logger.warning("[MemorySkill] remember failed: %s", exc)
        return f"⚠️ Failed to save memory: {exc}"


async def _recall_handler(text: str) -> str:
    """Search memory using memory_manager."""
    # Extract query
    query = text
    for kw in ["recall", "remember", "search memory", "find memory", "what do you remember"]:
        query = re.sub(rf"\b{kw}\b", "", query, flags=re.IGNORECASE).strip()

    if not query:
        return "What would you like me to recall?"

    try:
        from tools.memoryos_client import get_memoryos

        mos = get_memoryos("bashara")
        if mos:
            results = await mos.search_memories(query, limit=5)  # type: ignore[reportAttributeAccessIssue]
            if results:
                lines = ["🔍 Memory recall:\n"]
                for r in results[:5]:
                    content = r.get("content", r.get("text", str(r)))[:200]
                    lines.append(f"• {content}")
                return "\n".join(lines)
            return f"No memories found for: {query}"
        return "⚠️ MemoryOS not available."
    except Exception as exc:
        logger.warning("[MemorySkill] recall failed: %s", exc)
        return f"⚠️ Failed to recall memory: {exc}"


async def _obsidian_write_handler(text: str) -> str:
    """Write content to an Obsidian vault note."""
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "")
    if not vault_path:
        return "⚠️ Obsidian vault not configured (OBSIDIAN_VAULT_PATH env var needed)."

    vault = Path(vault_path)
    if not vault.exists():
        return f"❌ Obsidian vault not found: {vault_path}"

    # Try to extract filename and content
    # Pattern: "note: filename.md" or "filename.md" or just use a default
    filename_match = re.search(r"(?:note|file)[:\s]+([\w\-\s]+\.md)", text, re.IGNORECASE)
    if filename_match:
        filename = filename_match.group(1).strip()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"note_{timestamp}.md"

    # Content is everything after the filename or trigger phrase
    content = text
    for kw in [
        "obsidian",
        "write note",
        "save to obsidian",
        "note to obsidian",
        filename_match.group(1) if filename_match else "",
    ]:
        content = re.sub(rf"\b{kw}\b", "", content, flags=re.IGNORECASE).strip()
    content = re.sub(r"(?:note|file)[:\s]+[\w\-\s]+\.md", "", content, flags=re.IGNORECASE).strip()

    if not content:
        return "What content would you like me to write to the note?"

    note_path = vault / filename
    try:
        with open(note_path, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            f.write(f"\n\n---\n[{timestamp}]\n{content}\n")
        return f"✅ Note appended to Obsidian: {filename}"
    except Exception as exc:
        return f"❌ Failed to write to Obsidian: {exc}"


def _register_memory_skills() -> None:
    SKILL_REGISTRY.register(
        Skill(
            name="remember",
            description="Save a note or fact to persistent memory",
            trigger_keywords=["remember", "note that", "save this", "remember that", "ingat", "catat"],
            handler=_remember_handler,
            required_env_keys=[],
            category="memory",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="recall",
            description="Search and recall information from memory",
            trigger_keywords=[
                "recall",
                "what do you remember",
                "search memory",
                "find memory",
                "remember anything about",
            ],
            handler=_recall_handler,
            required_env_keys=[],
            category="memory",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="obsidian_write",
            description="Write content to a note in Obsidian vault",
            trigger_keywords=["obsidian", "write note", "save to obsidian", "note to obsidian", "obsidian note"],
            handler=_obsidian_write_handler,
            required_env_keys=["OBSIDIAN_VAULT_PATH"],
            category="memory",
        )
    )


_register_memory_skills()
