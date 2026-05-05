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


def _memory_success_callback(kwargs: dict, response_obj: litellm.types.utils.ModelResponse | dict) -> None:
    """
    LiteLLM success callback. Fires AFTER every successful LLM call.
    Stores the response as episodic memory in a background thread.
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