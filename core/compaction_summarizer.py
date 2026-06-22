"""Real LLM-based conversation compactor.

Replaces the lightweight `compact-manual` / `compact-auto` JS hooks with an
actual LLM summarization step. Called from `.claude/helpers/hook-handler.cjs`
via the `compact-summarize` command, fired from `PreCompact` in
`.claude/settings.json`.

Flow:
  1. Pick the most recent user in CONVERSATION_HISTORY (or accept --user-id).
  2. Pull last N turns (default 20) from in-RAM cache (no DB hit needed).
  3. Build a summarization prompt: task, decisions, pending actions, critical facts.
  4. Call litellm acompletion with max_tokens=500 to bound output.
  5. Persist result to llm_client.compaction_store with MD5 dedup.
  6. Return JSON {status, user_id, summary, chars_saved, id}.

Idempotency: identical conversation window -> same cache_key -> stored once.
A second call within the same session returns status="dedup" without an LLM hit.

Token cost: 1 LLM call per compaction, output <= 500 tokens.
Compared to compact-manual/compact-auto (which only call session.end() and
intelligence.consolidate(), both local Node no-ops), this is the FIRST step
that actually reduces input tokens on the next LLM turn by replacing the
raw conversation history with a 500-token summary block.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

# Ensure repo root is importable when invoked as `python3 -m core.compaction_summarizer`
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.conversation_interface import (  # noqa: E402
    CONVERSATION_HISTORY,
    get_conversation_history,
)
from llm_client.compaction_store import get_compaction_store  # noqa: E402

logger = logging.getLogger("compaction_summarizer")

# ── Configuration ────────────────────────────────────────────────────────────
DEFAULT_MODEL = "opencode-go/deepseek-v4-pro"
SUMMARY_TARGET_TOKENS = 500
SUMMARY_MAX_TURNS = 20
MAX_TURN_CHARS = 1500  # cap each turn in the prompt to keep input small
MAX_PROMPT_CHARS = 12000  # hard ceiling on input to the summarizer LLM


SYSTEM_PROMPT = (
    "You are a conversation compactor. Produce a single concise summary under "
    "500 tokens covering:\n"
    "1. The user's current task or goal\n"
    "2. Key decisions made so far\n"
    "3. Pending action items\n"
    "4. Critical facts (file paths, function names, error messages, commands) needed to continue\n\n"
    "Omit pleasantries, social noise, and verbose explanations. Preserve exact code, "
    "file paths, error strings, and URLs verbatim. Use bullet points. Output ONLY the "
    "summary — no preamble, no closing remarks."
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _pick_most_recent_user() -> Optional[str]:
    """Return the user_id with the most recent turn timestamp, or None."""
    if not CONVERSATION_HISTORY:
        return None
    latest_user: Optional[str] = None
    latest_ts = 0.0
    for uid, turns in CONVERSATION_HISTORY.items():
        if not turns:
            continue
        last_ts = turns[-1].get("ts", 0.0) or 0.0
        if last_ts > latest_ts:
            latest_user = uid
            latest_ts = last_ts
    return latest_user


def _build_messages(user_id: str, prior_context: str = "") -> list[dict[str, Any]]:
    """Build litellm messages: [system, prior_ctx?, user=turns]."""
    turns = get_conversation_history(user_id, last_n=SUMMARY_MAX_TURNS)
    if not turns:
        return []

    body_lines: list[str] = []
    total = 0
    for t in turns:
        role = t.get("role", "user")
        content = (t.get("content") or "")[:MAX_TURN_CHARS]
        if not content:
            continue
        line = f"[{role.upper()}]: {content}"
        if total + len(line) > MAX_PROMPT_CHARS:
            break
        body_lines.append(line)
        total += len(line)

    if not body_lines:
        return []

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if prior_context:
        messages.append({"role": "system", "content": prior_context})
    messages.append({"role": "user", "content": "\n\n".join(body_lines)})
    return messages


def _compute_cache_key(turns: list[dict[str, Any]]) -> str:
    """Stable MD5 of the conversation window for dedup."""
    payload = json.dumps(
        [{"role": t.get("role"), "content": t.get("content", "")} for t in turns],
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


# ── Core async path ──────────────────────────────────────────────────────────


async def _summarize_async(
    user_id: str,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Async: read history, call LLM, persist, return result dict."""
    turns = get_conversation_history(user_id, last_n=SUMMARY_MAX_TURNS)
    if not turns:
        return {"status": "no_history", "user_id": user_id, "summary": "", "chars_saved": 0}

    original_chars = sum(len(t.get("content") or "") for t in turns)
    cache_key = _compute_cache_key(turns)
    store = get_compaction_store()

    # Dedup: identical window already compacted
    existing = store.find_similar(cache_key=cache_key, session_id=user_id)
    if existing:
        return {
            "status": "dedup",
            "user_id": user_id,
            "summary": existing.get("summary", ""),
            "chars_saved": int(existing.get("chars_saved") or 0),
            "id": int(existing.get("id") or 0),
            "message_count": int(existing.get("message_count") or 0),
        }

    # Prior context: surface relevant past summaries (bounded)
    last_turn_text = (turns[-1].get("content") or "")[:200]
    prior_context = ""
    try:
        prior_context = store.get_context_for_compaction(
            query=last_turn_text,
            session_id=user_id,
            limit=3,
        )
    except Exception as e:  # pragma: no cover — defensive
        logger.debug("prior context fetch failed (non-fatal): %s", e)

    messages = _build_messages(user_id, prior_context=prior_context)
    if not messages:
        return {"status": "empty_input", "user_id": user_id, "summary": "", "chars_saved": 0}

    # Lazy import to avoid loading litellm at module import (speeds up hook startup)
    try:
        from litellm import acompletion
    except ImportError as e:
        return {"status": "error", "user_id": user_id, "error": f"litellm import failed: {e}"}

    try:
        response = await acompletion(
            model=model,
            messages=messages,
            max_tokens=SUMMARY_TARGET_TOKENS,
            temperature=0.0,
        )
    except Exception as e:
        return {"status": "error", "user_id": user_id, "error": f"acompletion failed: {e}"}

    # Extract content — tolerate both Pydantic and dict-style responses
    summary = ""
    try:
        summary = response.choices[0].message.content or ""
    except Exception:
        try:
            summary = response["choices"][0]["message"]["content"] or ""
        except Exception as e:
            return {"status": "error", "user_id": user_id, "error": f"response parse: {e}"}

    summary = (summary or "").strip()
    if not summary:
        return {"status": "empty_output", "user_id": user_id, "summary": "", "chars_saved": 0}

    compacted_chars = len(summary)
    chars_saved = max(0, original_chars - compacted_chars)

    row_id = store.store(
        cache_key=cache_key,
        summary=summary,
        message_count=len(turns),
        model_used=model,
        session_id=user_id,
        chars_saved=chars_saved,
        original_size=original_chars,
        compacted_size=compacted_chars,
        topic_tags=None,
        quality_score=None,
    )

    return {
        "status": "ok",
        "user_id": user_id,
        "summary": summary,
        "chars_saved": chars_saved,
        "original_size": original_chars,
        "compacted_size": compacted_chars,
        "message_count": len(turns),
        "id": row_id,
        "model": model,
    }


# ── Sync entry (for hook subprocess) ─────────────────────────────────────────


def summarize_recent(
    user_id: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Sync wrapper. Pick most recent user if user_id is None; run async summarize.

    Returns a JSON-serializable dict. Never raises.
    """
    start = time.time()
    if not user_id:
        user_id = _pick_most_recent_user()
    if not user_id:
        return {
            "status": "no_users",
            "summary": "",
            "chars_saved": 0,
            "elapsed_ms": int((time.time() - start) * 1000),
        }

    try:
        # If we're already inside an event loop (e.g. aiosqlite-driven bot),
        # run the coroutine in a worker thread to avoid "loop is running" errors.
        running_loop = None
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if running_loop is not None:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(asyncio.run, _summarize_async(user_id, model))
                result = future.result(timeout=20)
        else:
            result = asyncio.run(_summarize_async(user_id, model))
    except Exception as e:
        return {
            "status": "error",
            "user_id": user_id,
            "error": f"{type(e).__name__}: {e}",
            "elapsed_ms": int((time.time() - start) * 1000),
        }

    result["elapsed_ms"] = int((time.time() - start) * 1000)
    return result


# ── CLI entry ────────────────────────────────────────────────────────────────


def main() -> int:
    p = argparse.ArgumentParser(description="Summarize recent conversation for a user.")
    p.add_argument("--user-id", default=None, help="User ID; if omitted, pick most recent.")
    p.add_argument("--model", default=DEFAULT_MODEL, help="LLM model to use.")
    p.add_argument("--quiet", action="store_true", help="Print result JSON only.")
    args = p.parse_args()

    logging.basicConfig(
        level=os.environ.get("COMPACTION_LOG_LEVEL", "WARNING"),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    result = summarize_recent(user_id=args.user_id, model=args.model)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0 if result.get("status") not in ("error",) else 1


if __name__ == "__main__":
    sys.exit(main())
