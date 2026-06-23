"""Memory router for the Autonomy Layer.

Implements Part VI of the Autonomy Layer master prompt v2:
  - Auto-routes memory writes to ruflo / mem0 / obsidian
  - Handles DIRECT / LITE / SWARM write rules
  - Project namespace detection
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

ruflo_available = True
_mcp_client = None

try:
    from core.mcp_client import MCPClient
    _mcp_client = MCPClient()
except Exception:
    ruflo_available = False


PROJECT_PATTERNS = [
    (re.compile(r'cekwajar|wajar|gaji|slip|tanah|hidup|kabur'), "cekwajar"),
    (re.compile(r'rumahlabuh|boarding|rental|kos'), "rumahlabuh"),
    (re.compile(r'swarm-bot|agent|telegram.*bot'), "swarm-bot"),
    (re.compile(r'ml|model|pose|action.*recognition|tensor'), "research"),
]


def detect_project_namespace(text: str | None = None, file_paths: list[str] | None = None) -> str:
    """Detect project namespace from message text or file paths."""
    combined = ""
    if text:
        combined += text.lower()
    if file_paths:
        combined += " " + " ".join(file_paths)

    for pattern, namespace in PROJECT_PATTERNS:
        if pattern.search(combined):
            return namespace
    return "general"


async def _ruflo_store(namespace: str, key: str, value: str, tags: list[str] | None = None, metadata: dict | None = None) -> bool:
    if not ruflo_available or _mcp_client is None:
        return False
    try:
        result = await _mcp_client.call_tool("ruflo", "memory_store", {
            "namespace": namespace,
            "key": key,
            "value": value,
            "tags": tags or [],
            "metadata": metadata or {},
        })
        return bool(result)
    except Exception as e:
        logger.debug("ruflo memory_store failed: %s", e)
        return False


async def _mem0_add(user_id: str, content: str, metadata: dict | None = None) -> bool:
    try:
        from tools.mem0_client import mem0_add
        await mem0_add(user_id, content, metadata or {})
        return True
    except Exception as e:
        logger.debug("mem0_add failed: %s", e)
        return False


async def _obsidian_append(session_note: str) -> bool:
    try:
        from core.mcp_client import MCPClient
        client = MCPClient()
        today = datetime.now().strftime("%Y-%m-%d")
        content = f"## Session {datetime.now().strftime('%H:%M')}\n{session_note}\n"
        await client.call_tool("obsidian", "append_to_note", {
            "filename": f"Sessions/{today}.md",
            "content": content,
        })
        return True
    except Exception as e:
        logger.debug("obsidian append failed: %s", e)
        return False


async def _obsidian_create_session_note(title: str, content: str) -> bool:
    try:
        from core.mcp_client import MCPClient
        client = MCPClient()
        datetime.now().strftime("%Y%m%d-%H%M")
        re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
        await client.call_tool("obsidian", "create_daily_note", {
            "template_content": f"# Session: {title}\n\n{content}",
        })
        return True
    except Exception as e:
        logger.debug("obsidian create_session_note failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Public API — called by AutonomyEngine after each task
# ---------------------------------------------------------------------------

async def route_direct_task(task_summary: str, tool_used: str, outcome: str, namespace: str = "direct-ops") -> None:
    """After DIRECT task: store summary in ruflo only, skip obsidian."""
    key = f"direct-{int(datetime.now().timestamp())}"
    value = f"{task_summary} | tool={tool_used} | outcome={outcome}"
    tags = ["direct", tool_used]
    await _ruflo_store(namespace, key, value, tags)


async def route_lite_task(
    task: str,
    approach: str,
    files_changed: list[str],
    is_first_time: bool = False,
    namespace: str | None = None,
) -> None:
    """After LITE task: ruflo + obsidian daily note, neural_train if first time."""
    if namespace is None:
        namespace = f"project/{detect_project_namespace(file_paths=files_changed)}"

    key = f"lite-{int(datetime.now().timestamp())}"
    value = f"{task} | approach={approach} | files={','.join(files_changed)}"
    tags = ["lite", "task"]
    await _ruflo_store(namespace, key, value, tags)

    session_note = f"- {task}: {approach} ({len(files_changed)} files)"
    await _obsidian_append(session_note)

    if is_first_time:
        await _ruflo_store(namespace, f"pattern-{key}", value, tags=["neural", "first-time"])


async def route_swarm_task(
    task: str,
    full_context: str,
    decisions: list[str],
    files_affected: int,
    domains: list[str],
    namespace: str | None = None,
) -> None:
    """After SWARM task: ruflo + obsidian session note + mem0 + always neural_train."""
    if namespace is None:
        namespace = f"project/{detect_project_namespace(file_paths=[task])}"

    key = f"swarm-{int(datetime.now().timestamp())}"
    value = f"{task}\n\nContext: {full_context}\nDecisions:\n" + "\n".join(f"  - {d}" for d in decisions)
    tags = ["swarm", "task", *domains]
    await _ruflo_store(namespace, key, value, tags)

    slug = re.sub(r'[^a-z0-9]+', '-', task.lower())[:40]
    date_str = datetime.now().strftime("%Y%m%d-%H%M")
    session_content = (
        f"Task: {task}\n"
        f"Files affected: {files_affected}\n"
        f"Domains: {', '.join(domains)}\n"
        f"Key decisions:\n" + "\n".join(f"  - {d}" for d in decisions)
    )
    await _obsidian_create_session_note(f"{date_str}-{slug}", session_content)

    mem0_meta = {
        "type": "session",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "projects": [namespace.split("/")[-1]],
        "domains": domains,
    }
    await _mem0_add("bashara", f"{task}: {', '.join(decisions)}", mem0_meta)
