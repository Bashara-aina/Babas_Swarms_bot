"""Context enricher for the Autonomy Layer.

Implements Part VII of the Autonomy Layer master prompt v2:
  - Pre-flight enrichment for every task
  - Runs in < 5 seconds total
  - Runs calls in parallel where possible
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

ruflo_available = True
_mcp_client = None
gitnexus_available = True

try:
    from core.mcp_client import MCPClient
    _mcp_client = MCPClient()
except Exception:
    ruflo_available = False

try:
    from core.mcp_client import MCPClient
except Exception:
    gitnexus_available = False


async def _call_mcp(server: str, tool: str, args: dict | None = None) -> dict:
    if _mcp_client is None:
        return {}
    try:
        result = await _mcp_client.call_tool(server, tool, args or {})
        # call_tool returns str (JSON text or error message), not a list
        if isinstance(result, str) and result.startswith("{"):
            import json
            return json.loads(result)
        return {}
    except Exception:
        return {}


def extract_symbols(text: str) -> list[str]:
    """Extract code symbol / function names from message."""
    patterns = [
        r'\b([A-Z][a-zA-Z0-9_]+)\s*\(',
        r'def\s+([a-zA-Z_][a-zA-Z0-9_]+)\s*\(',
        r'class\s+([A-Z][a-zA-Z0-9_]+)\b',
        r'([a-z_]+)\s*\.\s*([a-zA-Z_][a-zA-Z0-9_]+)\s*\(',
    ]
    symbols = []
    for pat in patterns:
        symbols.extend(re.findall(pat, text))
    return list(dict.fromkeys(symbols))


async def enrich_for_symbols(symbols: list[str], repo: str = "swarm-bot") -> dict[str, Any]:
    """gitnexus context + impact for code symbols."""
    results = {}
    if not gitnexus_available:
        return results
    tasks = []
    for sym in symbols[:3]:
        tasks.append(_call_mcp("gitnexus", "gitnexus_context", {"name": sym, "repo": repo}))
        tasks.append(_call_mcp("gitnexus", "gitnexus_impact", {"target": sym, "direction": "upstream"}))
    ctx_results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, sym in enumerate(symbols[:3]):
        results[sym] = {
            "context": ctx_results[i * 2] if i * 2 < len(ctx_results) else None,
            "impact": ctx_results[i * 2 + 1] if i * 2 + 1 < len(ctx_results) else None,
        }
    return results


async def enrich_for_existing_files(file_paths: list[str]) -> dict[str, Any]:
    """Read existing files (if < 500 lines) and detect changes."""
    results = {}
    for path in file_paths[:5]:
        try:
            from pathlib import Path
            p = Path(path)
            if p.exists() and p.stat().st_size < 500 * 1024:
                content = p.read_text(errors="ignore")
                results[path] = {"exists": True, "size": p.stat().st_size, "preview": content[:200]}
            else:
                results[path] = {"exists": p.exists(), "skipped": "too large" if p.exists() else False}
        except Exception as e:
            results[path] = {"exists": False, "error": str(e)}
    return results


async def enrich_for_external_service(service: str) -> dict[str, Any]:
    """Web search for latest docs on external service."""
    try:
        result = await _call_mcp("exa", "exa_web_search_exa", {
            "query": f"{service} latest docs 2026",
            "numResults": 3,
        })
        return {"query": service, "result": result}
    except Exception:
        return {}


async def enrich_for_indonesian_regulation(regulation: str) -> dict[str, Any]:
    """Web search + graphrag for Indonesian regulations."""
    try:
        search_task = _call_mcp("exa", "exa_web_search_exa", {
            "query": f"{regulation} PMK OR PP 2024 2025",
            "numResults": 5,
        })
        graphrag_task = _call_mcp("ruflo", "query_wiki_graph", {
            "question": regulation,
            "mode": "global",
        })
        search_res, graphrag_res = await asyncio.gather(search_task, graphrag_task)
        return {"regulation": regulation, "search": search_res, "graphrag": graphrag_res}
    except Exception:
        return {}


async def enrich_for_continuation(namespace: str = "general") -> dict[str, Any]:
    """Restore session and retrieve recent memories for continuation."""
    try:
        session_task = _call_mcp("ruflo", "session_restore", {"name": "latest"})
        memory_task = _call_mcp("ruflo", "memory_retrieve", {
            "namespace": namespace,
            "key": "latest",
        })
        session_res, memory_res = await asyncio.gather(session_task, memory_task)
        return {"session": session_res, "memory": memory_res}
    except Exception:
        return {}


async def enrich_for_new_files(subdir: str) -> dict[str, Any]:
    """Directory tree for new files in existing codebase."""
    try:
        result = await _call_mcp("filesystem", "directory_tree", {"path": subdir})
        return {"subdir": subdir, "tree": result}
    except Exception:
        return {}


async def enrich_for_codebase_concept(concept: str) -> dict[str, Any]:
    """gitnexus query for code concepts."""
    try:
        result = await _call_mcp("gitnexus", "gitnexus_query", {
            "query": concept,
            "limit": 5,
        })
        return {"concept": concept, "query_result": result}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def enrich_context(user_message: str) -> dict[str, Any]:
    """Enrich context for a task. Runs matching enrichments in parallel.

    Takes < 5 seconds total.
    """
    tasks: list[tuple[str, asyncio.Task]] = []

    symbols = extract_symbols(user_message)
    if symbols:
        tasks.append(("symbols", asyncio.create_task(enrich_for_symbols(symbols))))

    file_paths = re.findall(r'[\w/.\-]+\.(py|js|ts|jsx|tsx|md|yaml|json)', user_message)
    if file_paths:
        tasks.append(("files", asyncio.create_task(enrich_for_existing_files(file_paths))))

    service_kw = re.search(r'(?:use|integrate|call|api for|sdk|library) (\w+)', user_message, re.I)
    if service_kw:
        service = service_kw.group(1)
        tasks.append(("service", asyncio.create_task(enrich_for_external_service(service))))

    regulation_kw = re.search(r'(?:tax|salary|employment|property|PMK|PP)\s*[\w\s]+', user_message, re.I)
    if regulation_kw:
        tasks.append(("regulation", asyncio.create_task(enrich_for_indonesian_regulation(regulation_kw.group()))))

    if any(kw in user_message.lower() for kw in ["continue", "resume", "keep working", "same task"]):
        tasks.append(("continuation", asyncio.create_task(enrich_for_continuation())))

    results = {}
    for name, task in tasks:
        try:
            results[name] = await task
        except Exception as e:
            logger.debug("enrich_context[%s] failed: %s", name, e)
            results[name] = {}

    return results