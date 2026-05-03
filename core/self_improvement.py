"""Self-improvement loop — Legion audits its own responses and updates SOUL.md autonomously.

Runs every 50 conversations OR when explicitly triggered.
Uses a lightweight LLM call to extract learnings and update SOUL.md.

Never modifies Core Values section of SOUL.md.
Only updates: Current Opinions, Things Legion Remembers, Relationship section.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

SOUL_PATH = Path(os.path.expanduser("~/swarm-bot/SOUL.md"))
SELF_REVIEW_LOG = Path(os.path.expanduser("~/.legion/self_review_log.json"))
SELF_REVIEW_LOG.parent.mkdir(parents=True, exist_ok=True)

_conversation_buffer: list[dict[str, str]] = []
_REVIEW_EVERY_N = 5  # TEMP for testing — revert to 50 after validating self-review loop works


def buffer_conversation(user_msg: str, legion_response: str) -> None:
    _conversation_buffer.append(
        {
            "user": user_msg[:200],
            "legion": legion_response[:300],
            "ts": time.time(),
        }
    )


async def maybe_run_self_review() -> None:
    if len(_conversation_buffer) < _REVIEW_EVERY_N:
        return
    try:
        await _run_self_review()
    except Exception as e:
        logger.warning("Self-review failed (non-fatal): %s", e)
    finally:
        _conversation_buffer.clear()


async def _run_self_review() -> None:
    if not SOUL_PATH.exists():
        return

    soul_content = await asyncio.to_thread(SOUL_PATH.read_text)
    recent_convs = _conversation_buffer[-20:]
    conv_text = "\n".join(f"User: {c['user']}\nLegion: {c['legion']}" for c in recent_convs)

    review_prompt = f"""You are Legion reviewing your own recent conversations.
Analyze the conversations below and extract:

1. NEW_OPINION: Did you form any new stances or update existing ones?
2. BASHARA_FACT: Did you learn a new fact about Bashara?
3. BEHAVIOR_FIX: Did you notice a recurring pattern where you could have been better?
4. SOUL_UPDATE: Specific text to ADD to the "Current Opinions" or "Things Legion Remembers" section of SOUL.md.
   Only update these two sections. NEVER change Core Values.
   Format: {{"section": "Current Opinions", "new_line": "- On X: Y"}}

Current SOUL.md (for context):
{soul_content[:2000]}

Recent conversations:
{conv_text}

Respond in JSON only:
{{
  "new_opinions": [...],
  "bashara_facts": [...],
  "behavior_fixes": [...],
  "soul_updates": [...]
}}"""

    try:
        from llm_client import chat

        result = await chat(
            task=review_prompt,
            agent_key="general",
            task_context="You are a strict code reviewer. Skip memory and wiki lookups. Be concise.",
        )

        import re

        json_match = re.search(r"\{.*\}", result, re.DOTALL)
        if not json_match:
            return
        data = json.loads(json_match.group())

        soul_updates = data.get("soul_updates", [])
        if soul_updates:
            await _apply_soul_updates(soul_content, soul_updates)

        log = []
        if SELF_REVIEW_LOG.exists():
            try:
                log_json = await asyncio.to_thread(SELF_REVIEW_LOG.read_text)
                log = json.loads(log_json)
            except Exception:
                pass
        log.append(
            {
                "ts": time.time(),
                "conversations_reviewed": len(recent_convs),
                "updates_applied": len(soul_updates),
                "data": data,
            }
        )
        await asyncio.to_thread(
            SELF_REVIEW_LOG.write_text, json.dumps(log[-20:], indent=2)
        )

        if soul_updates:
            logger.info("Self-review: applied %d SOUL.md updates", len(soul_updates))

    except Exception as e:
        logger.warning("Self-review LLM call failed: %s", e)


async def _apply_soul_updates(soul_content: str, updates: list[dict[str, str]]) -> None:
    protected_sections = ["## Core Values", "## Identity", "## How Legion Grows"]
    modified = soul_content

    for update in updates:
        section = update.get("section", "")
        new_line = update.get("new_line", "").strip()

        if not new_line or not section:
            continue

        if any(protected in section for protected in protected_sections):
            logger.warning("Self-review tried to modify protected section: %s", section)
            continue

        section_header = f"## {section}"
        if section_header in modified:
            idx = modified.index(section_header)
            next_section = modified.find("\n## ", idx + 1)
            if next_section == -1:
                next_section = len(modified)
            insert_pos = next_section
            if not new_line.startswith("-"):
                new_line = f"- {new_line}"
            modified = modified[:insert_pos] + f"\n{new_line}" + modified[insert_pos:]

    await asyncio.to_thread(SOUL_PATH.write_text, modified)
