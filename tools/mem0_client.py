"""Mem0-compatible semantic memory client with safe local fallbacks."""

from __future__ import annotations

import logging
import os
from typing import Any

from config.memory_config import mem0_vector_store_config
from tools import memory as legacy_memory

logger = logging.getLogger(__name__)

try:
    from mem0 import Memory  # type: ignore
except Exception:
    Memory = None  # type: ignore[assignment]

_mem0_instance: Any | None = None


def reset_mem0_instance() -> None:
    """Clear cached Mem0 client (tests / config reload)."""
    global _mem0_instance
    _mem0_instance = None


def _build_mem0_config() -> dict[str, Any]:
    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return {
        "vector_store": mem0_vector_store_config(),
        "llm": {
            "provider": "litellm",
            "config": {
                "model": os.getenv("MEM0_LLM_MODEL", "groq/llama-3.3-70b-versatile"),
                "api_key": os.getenv("GROQ_API_KEY", ""),
                "temperature": 0.1,
                "max_tokens": 2000,
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text",
                "ollama_base_url": ollama_base,
            },
        },
        "history_db_path": str(os.path.expanduser("~/.legion/mem0_history.db")),
    }


def get_mem0() -> Any | None:
    """Return the Mem0 client when available, else None."""
    global _mem0_instance
    if _mem0_instance is not None:
        return _mem0_instance
    if Memory is None:
        logger.warning("mem0 not available — using legacy memory fallback")
        return None
    try:
        _mem0_instance = Memory.from_config(_build_mem0_config())
        logger.info("Mem0 initialized with local Ollama embeddings")
    except Exception as exc:
        logger.warning("Mem0 init failed: %s", exc)
        _mem0_instance = None
    return _mem0_instance


async def mem0_add(user_id: str, content: str, metadata: dict[str, Any] | None = None) -> None:
    """Add a memory item; falls back to the legacy memory store."""
    try:
        mem = get_mem0()
        if mem is not None:
            mem.add(content, user_id=user_id, metadata=metadata or {})
            return
    except Exception as exc:
        logger.warning("mem0_add failed: %s", exc)
    try:
        await legacy_memory.add_memory(content, tags=[f"user:{user_id}"], source="mem0-fallback")
    except Exception as exc:
        logger.warning("legacy memory fallback failed: %s", exc)


async def mem0_search(user_id: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search memory semantically."""
    try:
        mem = get_mem0()
        if mem is not None:
            results = mem.search(query, user_id=user_id, limit=limit)
            if isinstance(results, dict):
                return list(results.get("results", []) or [])
            return list(results or [])
    except Exception as exc:
        logger.warning("mem0_search failed: %s", exc)
    try:
        legacy = await legacy_memory.search_memory(query, top_k=limit, user_id=user_id)
        out: list[dict[str, Any]] = []
        for item in legacy:
            out.append({
                "memory": item.get("text", ""),
                "score": float(item.get("score", 0.0) or 0.0),
                "metadata": {"source": item.get("source", "legacy")},
            })
        return out
    except Exception as exc:
        logger.warning("legacy memory search fallback failed: %s", exc)
        return []


async def mem0_get_all(user_id: str) -> list[dict[str, Any]]:
    """Return all memories for a user."""
    try:
        mem = get_mem0()
        if mem is not None:
            results = mem.get_all(user_id=user_id)
            if isinstance(results, dict):
                return list(results.get("results", []) or [])
            return list(results or [])
    except Exception as exc:
        logger.warning("mem0_get_all failed: %s", exc)
    return []


async def mem0_delete(user_id: str, memory_id: str) -> None:
    """Delete a memory by id."""
    try:
        mem = get_mem0()
        if mem is not None:
            mem.delete(memory_id)
            return
    except Exception as exc:
        logger.warning("mem0_delete failed: %s", exc)


def build_mem0_context(memories: list[dict[str, Any]], query: str, max_chars: int = 3000) -> str:
    """Render memory search results into a prompt block."""
    _ = query
    if not memories:
        return ""
    lines = ["[Legion Memory — relevant context from past interactions:]"]
    total = 0
    for item in memories:
        content = item.get("memory", "") or item.get("content", "") or item.get("text", "")
        score = float(item.get("score", 0.0) or 0.0)
        if not content:
            continue
        line = f"- (relevance {score:.2f}) {content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    lines.append("[End of memory context]")
    return "\n".join(lines)
