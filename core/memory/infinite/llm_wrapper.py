"""
Memory injection helper for llm_client.call_llm.
Surgically adds memory recall block to the system message.
"""
from __future__ import annotations

import threading

from ..store import MemoryStore

_store = MemoryStore()
_store_lock = threading.Lock()


def inject_memory_into_messages(
    messages: list[dict],
    agent_id: str = "shared",
    top_k: int = 10,
) -> list[dict]:
    """
    Prepend memory block as a system message to the messages list.
    Call this before call_llm() to inject recalled memories.
    """
    query = _extract_query_from_messages(messages)
    memory_block = _store.recall_formatted(query=query, agent_id=agent_id, top_k=top_k)

    if not memory_block:
        return messages

    return [{"role": "system", "content": memory_block}, *messages]


def store_response(
    response_text: str,
    agent_id: str = "shared",
) -> None:
    """Store LLM response as episodic memory (async, non-blocking)."""
    if not response_text or len(response_text) < 50:
        return

    def _inner():
        try:
            with _store_lock:
                _store.remember(
                    content=response_text,
                    agent_id=agent_id,
                    memory_type="episodic",
                )
        except Exception:
            pass

    t = threading.Thread(target=_inner, daemon=True)
    t.start()


def _extract_query_from_messages(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        return item.get("text", "")[:512]
            return str(content)[:512]
    return ""
