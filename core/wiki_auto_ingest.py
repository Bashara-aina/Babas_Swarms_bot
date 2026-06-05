"""
Wiki Auto-Ingest — Karpathy LLM Wiki pattern for Legion.

Hooks:
  - on_conversation_turn(): lightweight per-turn check (LLM decides if worth filing)
  - on_turn_deep_ingest(): deep ingest across recent turns (fires every turn, thresholds internally)
  - lint_wiki(): periodic health check (orphaned links, stale claims)

All wiki writes go through WikiManager to keep INDEX.md in sync.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / ".wiki"
WIKI_LOG = WIKI_DIR / "logs" / "auto-ingest.md"
QUALITY_THRESHOLD = 0.65
SESSION_TURN_THRESHOLD = 3


def _now_jst() -> str:
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M JST")


# ── Per-turn lightweight check ─────────────────────────────────────────────

QUALITY_CHECK_PROMPT = """Is this Q&A worth adding to a personal knowledge wiki?
Answer JSON only: {{"worthy": true/false, "reason": "one line"}}

Worthy = concrete solution, confirmed fact, established workflow, or decision with reasoning.
Not worthy =闲聊, uncorroborated opinion, or generic explanation.

Q: {q}
A: {a}
"""


def is_worthy_turn(q: str, a: str) -> tuple[bool, str]:
    """Lightweight blocking check — avoid LLM call on every message."""
    short_q = len(q.strip()) < 10
    short_a = len(a.strip()) < 15
    if short_q or short_a:
        return False, "too short"

    code_block_count = a.count("```")
    if code_block_count >= 4:
        return True, "code-heavy solution worth preserving"

    cmd_patterns = ("pip ", "npm ", "git ", "python", "bash", "sudo", "export ", "source ")
    if any(p in a for p in cmd_patterns) and "error" in (q + a).lower():
        return True, "solved command/error"

    url_pattern = re.compile(r"https?://\S+")
    if url_pattern.search(a):
        return True, "links to reference"

    return False, "default skip"


async def _llm_quality_check(q: str, a: str) -> tuple[bool, float]:
    """Call LLM to score quality. Returns (worthy, score)."""
    try:
        from llm_client import chat

        prompt = QUALITY_CHECK_PROMPT.format(q=q[:300], a=a[:500])
        raw, _model = await chat(task=prompt, agent_key="general", model_override="minimax-coding-plan/MiniMax-M3")
        data = json.loads(raw)
        return bool(data.get("worthy", False)), float(data.get("score", 0.0))
    except Exception as exc:
        logger.warning("LLM quality check failed: %s", exc)
        return False, 0.0


# ── Main ingest ───────────────────────────────────────────────────────────

EXTRACT_PROMPT = """You are a wiki maintainer for Legion, a personal AI agent.

Given this conversation, extract knowledge worth permanent filing.

Return JSON only:
{{
  "worth_filing": true/false,
  "quality_score": 0.0-1.0,
  "pages": [
    {{
      "filename": "topic-name.md",
      "action": "create|update|append",
      "content": "# Title\\n\\nContent...",
      "reason": "why this is worth filing"
    }}
  ],
  "log_entry": "one-line summary of what was learned"
}}

ONLY file if quality_score >= 0.65 AND content is:
- A solved problem with a concrete solution
- A confirmed fact/finding with evidence
- A workflow or procedure that was established
- A decision made with reasoning

Conversation (last {turn_n} turns):
{conversation}
"""


async def on_conversation_turn(
    user_id: str,
    user_message: str,
    assistant_message: str,
) -> dict[str, Any]:
    """
    Called after every LLM response.
    Lightweight check — skip if not worth filing.
    Heavy LLM extraction only if first-pass looks promising.
    """
    worthy, reason = is_worthy_turn(user_message, assistant_message)
    if not worthy:
        return {"filed": False, "reason": reason, "score": 0.0}

    try:
        from core.wiki_manager import get_wiki_manager

        src = f"User: {user_message}\nLegion: {assistant_message}"
        pages = await get_wiki_manager().ingest(
            source=src,
            source_type="conversation",
            context=f"auto-ingest from chat (user_id={user_id})",
        )
        if pages:
            await _log_ingest(pages, 0.75, reason, src)
            return {"filed": True, "pages": pages, "score": 0.75, "reason": reason}
        return {"filed": False, "reason": "no pages returned", "score": 0.75}
    except Exception as exc:
        logger.warning("on_conversation_turn ingest failed: %s", exc)
        return {"filed": False, "reason": str(exc), "score": 0.75}


async def on_turn_deep_ingest(
    user_id: str,
    conversation: list[dict[str, str]],
    llm_client: Any = None,
) -> dict[str, Any]:
    """
    Deep ingest across recent conversation turns.

    NOTE: This fires every turn (not just at session end). Internal threshold
    (SESSION_TURN_THRESHOLD=3) gates whether heavy LLM extraction actually runs.
    """
    if len(conversation) < SESSION_TURN_THRESHOLD:
        return {"filed": False, "reason": f"only {len(conversation)} turns"}

    formatted = "\n".join(
        f"{m.get('role', 'unknown').upper()}: {m.get('content', '')[:500]}" for m in conversation[-10:]
    )

    prompt = EXTRACT_PROMPT.format(
        turn_n=min(len(conversation), 10),
        conversation=formatted,
    )

    try:
        if llm_client is None:
            from llm_client import chat

            raw, _model = await chat(task=prompt, agent_key="general", model_override="minimax-coding-plan/MiniMax-M3")
        else:
            raw = await llm_client.complete(prompt)

        data = json.loads(raw)
    except Exception as exc:
        logger.warning("on_turn_deep_ingest LLM call failed: %s", exc)
        return {"filed": False, "reason": f"LLM error: {exc}"}

    if not data.get("worth_filing") or data.get("quality_score", 0) < QUALITY_THRESHOLD:
        return {
            "filed": False,
            "reason": "below quality threshold",
            "score": data.get("quality_score", 0),
        }

    filed = []
    try:
        from core.wiki_manager import get_wiki_manager

        wm = get_wiki_manager()
        for page in data.get("pages", []):
            page_path = page.get("filename", "")
            if not page_path.endswith(".md"):
                page_path += ".md"
            action = page.get("action", "update")
            content = page.get("content", "")
            if action == "create":
                existing = await wm.read_page(page_path)
                if "does not exist" not in existing:
                    content = f"# Update: {page_path}\n\n{content}"
                    action = "update"
            resolved = wm._resolve(page_path)
            if resolved is None:
                logger.warning("wiki auto-ingest: unsafe path rejected: %s", page_path)
                continue
            await wm.write_page(page_path, content)
            filed.append(page_path)

        if filed:
            await _log_ingest(filed, data.get("quality_score", 0), data.get("log_entry", ""), formatted[:200])
    except Exception as exc:
        logger.warning("on_turn_deep_ingest wiki write failed: %s", exc)
        return {"filed": False, "reason": str(exc)}

    return {
        "filed": True,
        "pages": filed,
        "score": data.get("quality_score", 0),
        "log_entry": data.get("log_entry", ""),
    }


# ── Periodic lint ─────────────────────────────────────────────────────────


async def lint_wiki() -> dict[str, Any]:
    """Weekly health check: orphaned links, stale claims, missing cross-refs."""
    try:
        from core.wiki_manager import get_wiki_manager

        wm = get_wiki_manager()
        report = await wm.lint()
        return {"ok": True, "report": report}
    except Exception as exc:
        logger.warning("lint_wiki failed: %s", exc)
        return {"ok": False, "error": str(exc)}


# ── Logging ───────────────────────────────────────────────────────────────


async def _log_ingest(
    pages: list[str],
    score: float,
    reason: str,
    src_preview: str,
) -> None:
    """Append auto-ingest entry to WIKI_LOG."""
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    log_path = WIKI_DIR / "logs" / "auto-ingest.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    stamp = _now_jst()
    entry = f"""## [{stamp}] auto-ingest | score={score:.2f} | {reason}

- pages: {", ".join(pages)}
- src: {src_preview[:120]}
"""
    try:
        await _write_file_async(log_path, entry)
    except Exception as exc:
        logger.warning("log_ingest write failed: %s", exc)


async def _write_file_async(path: Path, content: str) -> None:
    import aiofiles

    async with aiofiles.open(path, mode="a", encoding="utf-8") as f:
        await f.write(content + "\n")
