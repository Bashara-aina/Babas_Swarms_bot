"""
Memory injection via LiteLLM callbacks.

Every LiteLLM call (from any source — main.py, hermes, anything that uses litellm.acompletion)
goes through these callbacks automatically.

Input callback:  intercepts kwargs BEFORE the LLM call, injects memory as a system message.
Success callback: stores the response as episodic memory (async, non-blocking).
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path

import litellm

from core.memory.store import MemoryStore

logger = logging.getLogger(__name__)

_store = MemoryStore()
_store_lock = threading.Lock()
_callbacks_registered = False


def _memory_input_callback(kwargs: dict) -> dict:
    """
    LiteLLM input callback. Fires BEFORE every LLM call.
    Injects recalled memories as a system message block.

    - Finds the system message (first with role="system")
    - Or prepends a new system message if none exists
    - Extracts query from user message for semantic memory search
    - Injects up to top_k memories as formatted block
    """
    try:
        messages = kwargs.get("messages", [])

        if not messages:
            return kwargs

        query = _extract_query(messages)
        if not query:
            return kwargs

        memories = _recall_memories(query, top_k=10)
        if not memories:
            return kwargs

        memory_block = _format_memory_block(memories)

        existing_idx = next(
            (i for i, m in enumerate(messages) if m.get("role") == "system"),
            None,
        )

        if existing_idx is not None:
            existing = messages[existing_idx]
            content = existing.get("content", "")
            if isinstance(content, list):
                content_str = "\n".join(
                    c.get("text", "") if isinstance(c, dict) else str(c)
                    for c in content
                )
            else:
                content_str = str(content)
            messages[existing_idx] = {
                **existing,
                "content": f"{memory_block}\n\n{content_str}",
            }
        else:
            messages.insert(0, {"role": "system", "content": memory_block})

        kwargs["messages"] = messages

    except Exception as e:
        logger.debug("Memory input callback error: %s", e)

    return kwargs


def _bridge_to_session_state(kwargs: dict, response_obj: litellm.types.utils.ModelResponse | dict) -> None:
    """
    Bridge LiteLLM call outcomes to .session_state/ so session_watcher
    can pick them up as memory sources.

    Writes two files atomically via temp+rename:
    - .session_state/current.json  — used by session_watcher as its state source
    - .session_state/llm_events.log — append-only event log for LLM call patterns

    Does NOT call mem0/langmem directly (those are managed by session_watcher).
    """
    try:
        # Build current state snapshot
        content = _extract_response_content(response_obj) or ""
        query = _extract_query(kwargs.get("messages", []))

        import json
        import os
        import tempfile
        import time
        # Use swarm-bot as base dir, not cwd (cwd may be /home/newadmin after os.chdir)
        swarm_dir = Path(__file__).parent.parent.parent  # .../swarm-bot
        session_dir = swarm_dir / ".session_state"
        os.makedirs(session_dir, exist_ok=True)

        # Read existing current.json to preserve checkpoint list
        current_path = os.path.join(session_dir, "current.json")
        prev_state = {}
        if os.path.exists(current_path):
            try:
                with open(current_path) as f:
                    prev_state = json.load(f)
            except Exception:
                prev_state = {}

        # Merge session metrics from SessionMetrics (live tracker of files/decisions/accomplishments)
        try:
            from core.legion_session import get_session_metrics
            metrics = get_session_metrics()
            session_name = metrics.accomplished[-1] if metrics.accomplished else ""
            files_changed = list(metrics.files_changed) if metrics.files_changed else prev_state.get("files_changed", [])
            decisions = list(metrics.decisions) if metrics.decisions else prev_state.get("decisions", [])
        except Exception:
            session_name = prev_state.get("session_name", "")
            files_changed = prev_state.get("files_changed", [])
            decisions = prev_state.get("decisions", [])

        new_state = {
            **prev_state,
            "last_llm_call": int(time.time()),
            "last_query": query[:256] if query else "",
            "last_response_len": len(content),
            # session_watcher reads "phase" from current.json to determine what to save
            "phase": "llm_call_complete",
            # Enriched fields from SessionMetrics
            "session_name": session_name or prev_state.get("session_name", ""),
            "files_changed": files_changed,
            "decisions": decisions,
        }

        # Atomic write to current.json
        tmp = tempfile.NamedTemporaryFile(mode="w", dir=session_dir, delete=False, suffix=".tmp")
        json.dump(new_state, tmp)
        tmp.close()
        os.rename(tmp.name, current_path)

        # Append to llm_events.log
        log_path = os.path.join(session_dir, "llm_events.log")
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        entry = json.dumps({"ts": ts, "query_len": len(query), "response_len": len(content), "content_preview": content[:80]})
        with open(log_path, "a") as f:
            f.write(entry + "\n")

    except Exception as e:
        logger.debug("Bridge to session_state error: %s", e)


def _memory_success_callback(kwargs: dict, response_obj: litellm.types.utils.ModelResponse | dict) -> None:
    """
    LiteLLM success callback. Fires AFTER every successful LLM call.
    Stores the response as episodic memory in a background thread.
    Bridges the call to .session_state/ for session_watcher.
    """
    try:
        content = _extract_response_content(response_obj)
        if not content or len(content) < 50:
            return

        def _store():
            try:
                with _store_lock:
                    _store.remember(
                        content=content,
                        agent_id="shared",
                        memory_type="episodic",
                    )
            except Exception:
                pass

        t = threading.Thread(target=_store, daemon=True)
        t.start()

        # Bridge this LLM call to session_state (non-blocking)
        _bridge_to_session_state(kwargs, response_obj)

    except Exception as e:
        logger.debug("Memory success callback error: %s", e)


def _extract_query(messages: list[dict]) -> str:
    """Extract query text from user messages for semantic search."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        return item.get("text", "")[:512]
            return str(content)[:512]
    return ""


def _recall_memories(query: str, top_k: int = 10) -> list[str]:
    """Recall top_k memories semantically matching the query."""
    try:
        return _store.recall(query=query, agent_id=None, top_k=top_k, min_score=0.25)
    except Exception:
        return []


def _format_memory_block(memories: list[str]) -> str:
    """Format memories as a styled block for system prompt injection."""
    lines = [
        "━━━ LONG-TERM MEMORY (recalled from persistent store) ━━━",
    ]
    for i, m in enumerate(memories, 1):
        lines.append(f"{i}. {m}")
    lines.append("━━━ END MEMORY — treat as reliable prior context ━━━")
    return "\n".join(lines)


def _extract_response_content(response_obj: litellm.utils.ModelResponse | dict) -> str:
    """Extract text content from a LiteLLM response object."""
    try:
        if isinstance(response_obj, dict):
            choices = response_obj.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "") or ""
            return ""

        if hasattr(response_obj, "choices"):
            choices = response_obj.choices
            if choices and len(choices) > 0:
                choice = choices[0]
                if hasattr(choice, "message"):
                    return choice.message.content or ""
        return ""
    except Exception:
        return ""


def register_memory_callbacks() -> None:
    """
    Register memory callbacks with LiteLLM.
    Safe to call multiple times — checks if already registered.
    """
    global _callbacks_registered

    if _callbacks_registered:
        return

    litellm.input_callback.append(_memory_input_callback)
    litellm.success_callback.append(_memory_success_callback)
    _callbacks_registered = True
    logger.info("Memory callbacks registered with LiteLLM (input + success)")


register_memory_callbacks()
