#!/usr/bin/env python3
"""
Hermes-Lite MCP Server — 35 essential tools (down from 194).
Reduces context floor by ~135K tokens while maintaining capability.
"""
import asyncio
import json
import os
import subprocess
import sys
import time as _time
from pathlib import Path

# ── Bootstrap hermes-agent path ─────────────────────────────────────────────
HERMES_REPO_PATH = os.environ.get(
    "HERMES_REPO_PATH",
    str(Path.home() / "hermes-agent"),
)
if HERMES_REPO_PATH not in sys.path:
    sys.path.insert(0, HERMES_REPO_PATH)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hermes-lite")

# ── Import Hermes tools ──────────────────────────────────────────────────────
try:
    from model_tools import get_tool_definitions, handle_function_call
    from toolsets import TOOLSETS
    # Only load essential toolsets
    HERMES_TOOLS = get_tool_definitions(
        enabled_toolsets=["terminal", "file", "web", "browser", "vision",
                          "delegate", "session_search", "skills",
                          "code_execution"],
        quiet_mode=True,
    )
    TOOLSET_MAP = {}
    for ts_name, ts_data in TOOLSETS.items():
        for tool_name in ts_data.get("tools", []):
            TOOLSET_MAP[tool_name] = ts_name
except ImportError as e:
    print(f"[Hermes-Lite] Warning: hermes-agent tools not loaded: {e}", file=sys.stderr)
    HERMES_TOOLS = []
    TOOLSET_MAP = {}

# ── Import enhancement modules ──────────────────────────────────────────────
_HANDLERS = {}

_MODULES = {
    "memory_sync": ("memory_sync", "handle_memory_sync"),
    "memory_layer_bridge": ("memory_layer_bridge", "handle_memory_layer_bridge"),
    "context_restorer": ("context_restorer", "handle_context_restorer"),
    "security_gate": ("security_gate", "handle_security_gate"),
    "context_compactor": ("context_compactor", "handle_context_compactor"),
    "coordination": ("coordination_primitives", "handle_coordination"),
    "cross_session_memory": ("cross_session_memory", "handle_cross_session_memory"),
    "hermes_context_injector": ("hermes_context_injector", "handle_hermes_context_injector"),
}

for _name, (_mod, _func) in _MODULES.items():
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        mod = __import__(_mod, fromlist=[_func])
        _HANDLERS[_name] = getattr(mod, _func)
    except Exception as e:
        print(f"[Hermes-Lite] {_name} unavailable: {e}", file=sys.stderr)
        _HANDLERS[_name] = None

# Token meter
try:
    from hermes_token_meter import TokenMeter
    _token_meter = TokenMeter()
    TOKEN_METER_AVAILABLE = True
except Exception:
    TOKEN_METER_AVAILABLE = False

# ── Subprocess helper ───────────────────────────────────────────────────────
def _run_cmd(cmd, input_data=None, timeout=60):
    try:
        payload = json.dumps(input_data).encode() if input_data else None
        r = subprocess.run(
            cmd, input=payload, capture_output=True, timeout=timeout,
            env={**os.environ, "NO_COLOR": "1", "CLICOLOR": "0"},
        )
        out = r.stdout.decode(errors="replace") or "{}"
        if r.returncode != 0:
            return json.dumps({"error": f"exit {r.returncode}", "stderr": r.stderr.decode(errors="replace")})
        return out
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"timeout after {timeout}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def _hermes_call(tool_name: str, args: dict = None) -> str:
    """Call a hermes-agent tool by name."""
    if not HERMES_TOOLS:
        return json.dumps({"error": "hermes-agent tools not loaded", "tool": tool_name})
    try:
        result = handle_function_call(
            function_name=tool_name, function_args=args or {},
            task_id=None, session_id=None, user_task=None,
        )
        return json.dumps(result, indent=2) if not isinstance(result, str) else result
    except Exception as e:
        return json.dumps({"error": str(e), "tool": tool_name})

# ════════════════════════════════════════════════════════════════════════════
# CORE (8 tools)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def hermes_read_file(path: str, offset: int = 0, limit: int = 5000) -> str:
    """Read a file via Hermes."""
    return _hermes_call("read_file", {"path": path, "offset": offset, "limit": limit})

@mcp.tool()
def hermes_write_file(path: str, content: str, mode: str = "overwrite") -> str:
    """Write content to a file."""
    return _hermes_call("write_file", {"path": path, "content": content, "mode": mode})

@mcp.tool()
def hermes_terminal(command: str, timeout: int = 30) -> str:
    """Execute a terminal command."""
    return _hermes_call("terminal", {"command": command, "timeout": timeout})

@mcp.tool()
def hermes_delegate(goal: str, context: str = "", toolsets: str = "terminal,file,web") -> str:
    """Spawn a subagent to accomplish a goal."""
    return _hermes_call("delegate", {"goal": goal, "context": context, "toolsets": [t.strip() for t in toolsets.split(",")]})

@mcp.tool()
def hermes_web_search(query: str, depth: str = "basic") -> str:
    """Search the web via Hermes."""
    return _hermes_call("web_search", {"query": query, "depth": depth})

@mcp.tool()
def hermes_web_extract(url: str, query: str = "") -> str:
    """Extract content from a URL."""
    return _hermes_call("web_extract", {"url": url, "query": query})

@mcp.tool()
def hermes_execute_code(code: str, language: str = "python", timeout: int = 30) -> str:
    """Execute code in Hermes sandbox."""
    return _hermes_call("execute_code", {"code": code, "language": language, "timeout": timeout})

@mcp.tool()
def hermes_session_search(query: str, limit: int = 5) -> str:
    """Search past sessions via FTS5."""
    return _hermes_call("session_search", {"query": query, "limit": limit})

# ════════════════════════════════════════════════════════════════════════════
# CODE INTELLIGENCE (3 tools)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def gitnexus_query(query: str, goal: str = "", limit: int = 5, repo: str = "") -> str:
    """Query code knowledge graph for execution flows."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "query"], {"query": query, "goal": goal, "limit": limit, "repo": repo})

@mcp.tool()
def gitnexus_context(name: str, repo: str = "", file_path: str = "", include_content: bool = False) -> str:
    """360-degree view: callers, callees, process participation."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "context"], {"name": name, "repo": repo, "filePath": file_path, "include_content": include_content})

@mcp.tool()
def gitnexus_impact(target: str, direction: str, repo: str = "", max_depth: int = 3, include_tests: bool = False) -> str:
    """Analyze blast radius of changing a code symbol."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "impact"], {"target": target, "direction": direction, "repo": repo, "maxDepth": max_depth, "includeTests": include_tests})

# ════════════════════════════════════════════════════════════════════════════
# MEMORY (4 tools)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def memory_save(key: str, value: str, provenance: str = "{}", decay_rate: float = 0.1) -> str:
    """Save memory entry with provenance and versioning."""
    if not _HANDLERS["cross_session_memory"]:
        return json.dumps({"error": "cross-session memory not available"})
    return _HANDLERS["cross_session_memory"]({"action": "save", "key": key, "value": value, "provenance": json.loads(provenance) if isinstance(provenance, str) else provenance, "decay_rate": decay_rate})

@mcp.tool()
def memory_recall(key: str, min_priority: float = 0.5) -> str:
    """Recall memory with priority filtering."""
    if not _HANDLERS["cross_session_memory"]:
        return json.dumps({"error": "cross-session memory not available"})
    return _HANDLERS["cross_session_memory"]({"action": "recall", "key": key, "min_priority": min_priority})

@mcp.tool()
def memory_layer_bridge(action: str = "query", query: str = "", layers: list = None, top_k: int = 5, layer: str = "") -> str:
    """Query all 6 CC memory layers with unified interface."""
    if not _HANDLERS["memory_layer_bridge"]:
        return json.dumps({"error": "memory layer bridge not available"})
    return _HANDLERS["memory_layer_bridge"]({"action": action, "query": query, "layers": layers or ["L1", "L2", "L3", "L4", "L5", "L6"], "top_k": top_k, "layer": layer})

@mcp.tool()
def memory_sync(direction: str = "bidirectional", dry_run: bool = False) -> str:
    """Bidirectional memory sync between CC and Hermes."""
    if not _HANDLERS["memory_sync"]:
        return json.dumps({"error": "memory sync not available"})
    return _HANDLERS["memory_sync"]({"direction": direction, "dry_run": dry_run})

# ════════════════════════════════════════════════════════════════════════════
# BROWSER (4 tools)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def hermes_browser_navigate(url: str, mode: str = "normal") -> str:
    """Navigate browser to URL."""
    return _hermes_call("browser_navigate", {"url": url, "mode": mode})

@mcp.tool()
def hermes_browser_snapshot(element: str = "") -> str:
    """Get browser page snapshot."""
    return _hermes_call("browser_snapshot", {"element": element})

@mcp.tool()
def playwright_browser_click(target: str, button: str = "left") -> str:
    """Click on element on page."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-click"], {"target": target, "button": button})

@mcp.tool()
def playwright_browser_type(target: str, text: str, slowly: bool = False, submit: bool = False) -> str:
    """Type text into editable element."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-type"], {"target": target, "text": text, "slowly": slowly, "submit": submit})

# ════════════════════════════════════════════════════════════════════════════
# SECURITY (2 tools)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def security_scan_code(code_snippet: str, file_path: str = "") -> str:
    """Scan code snippet for vulnerabilities."""
    if not _HANDLERS["security_gate"]:
        return json.dumps({"error": "security gate not available"})
    return _HANDLERS["security_gate"]({"action": "scan_code", "code_snippet": code_snippet, "file_path": file_path})

@mcp.tool()
def security_check_file(file_path: str) -> str:
    """Scan existing file for security issues."""
    if not _HANDLERS["security_gate"]:
        return json.dumps({"error": "security gate not available"})
    return _HANDLERS["security_gate"]({"action": "check_file", "file_path": file_path})

# ════════════════════════════════════════════════════════════════════════════
# OBSIDIAN (5 tools)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def obsidian_search_notes(query: str = "", tags: list = None) -> str:
    """Search notes by content or tags."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "search-notes"], {"query": query, "tags": tags or []})

@mcp.tool()
def obsidian_read_note(filename: str) -> str:
    """Read full content of a note from vault."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "read-note"], {"filename": filename})

@mcp.tool()
def obsidian_list_notes(tag_filter: str = "") -> str:
    """List all notes in vault."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "list-notes"], {"tag_filter": tag_filter})

@mcp.tool()
def obsidian_create_note(filename: str, content: str = "", template_name: str = "") -> str:
    """Create a new note in vault."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "create-note"], {"filename": filename, "content": content, "template_name": template_name})

@mcp.tool()
def obsidian_append_to_note(filename: str, content: str) -> str:
    """Append content to an existing note."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "append-to-note"], {"filename": filename, "content": content})

# ════════════════════════════════════════════════════════════════════════════
# MISC (9 tools)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def hermes_vision_analyze(image_path: str, query: str = "Describe this image") -> str:
    """Analyze an image via Hermes vision."""
    return _hermes_call("vision_analyze", {"image_path": image_path, "query": query})

@mcp.tool()
def hermes_skills_list(category: str = "") -> str:
    """List Hermes skills (procedural memory)."""
    return _hermes_call("skills_list", {"category": category})

@mcp.tool()
def hermes_token_meter(action: str = "get", session_id: str = "", budget_tokens: int = 0) -> str:
    """Track token usage and cost for Hermes sessions."""
    if not TOKEN_METER_AVAILABLE:
        return json.dumps({"error": "token meter not available"})
    return _token_meter.handle_mcp(action, session_id, budget_tokens)

@mcp.tool()
def hermes_health_check() -> str:
    """Check external MCP connections and report latency."""
    servers = {
        "gitnexus": ["npx", "-y", "gitnexus@latest", "mcp", "list-repos"],
        "playwright": ["npx", "-y", "playwright-mcp@latest", "browser-tabs"],
    }
    results = {}
    for name, cmd in servers.items():
        try:
            start = _time.perf_counter()
            subprocess.run(cmd, capture_output=True, timeout=5)
            results[name] = {"latency_ms": round((_time.perf_counter() - start) * 1000, 2), "status": "connected"}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)[:100]}
    return json.dumps({"servers": results, "summary": {"total": len(servers), "connected": sum(1 for r in results.values() if r.get("status") == "connected")}}, indent=2)

@mcp.tool()
def hermes_context_injector(action: str = "inject", project_path: str = "", profile_name: str = "", max_chars: int = 4000, includes: list = None) -> str:
    """Auto-inject CLAUDE.md and project context."""
    if not _HANDLERS["hermes_context_injector"]:
        return json.dumps({"error": "context injector not available"})
    return _HANDLERS["hermes_context_injector"]({"action": action, "project_path": project_path, "profile_name": profile_name, "max_chars": max_chars, "includes": includes or []})

@mcp.tool()
def compactor_status() -> str:
    """Get context utilization and compaction status."""
    if not _HANDLERS["context_compactor"]:
        return json.dumps({"error": "compactor not available"})
    return _HANDLERS["context_compactor"]({"action": "status"})

@mcp.tool()
def coordination_send(to_agent: str, message: str = "{}", from_agent: str = "hermes") -> str:
    """Send direct message to agent."""
    if not _HANDLERS["coordination"]:
        return json.dumps({"error": "coordination not available"})
    return _HANDLERS["coordination"]({"action": "send", "to_agent": to_agent, "from_agent": from_agent, "message": json.loads(message) if isinstance(message, str) else message})

@mcp.tool()
def coordination_broadcast(message: str = "{}", from_agent: str = "hermes") -> str:
    """Broadcast message to all registered agents."""
    if not _HANDLERS["coordination"]:
        return json.dumps({"error": "coordination not available"})
    return _HANDLERS["coordination"]({"action": "broadcast", "from_agent": from_agent, "message": json.loads(message) if isinstance(message, str) else message})

# ── Strip tool schema verbosity (Phase 3 optimization) ─────────────────────
def _strip_schemas():
    """Post-process tool schemas to reduce context footprint.

    Strips: redundant titles, default values, long descriptions.
    Keeps: function names, parameter names, types, required fields.
    """
    tm = mcp._tool_manager
    stripped = 0
    for tool in tm._tools.values():
        # Trim description to first sentence, max 40 chars
        desc = (tool.description or "").strip()
        if "." in desc:
            desc = desc.split(".")[0] + "."
        if len(desc) > 43:
            desc = desc[:40] + "..."
        tool.description = desc

        # Strip verbosity from parameter properties
        props = tool.parameters.get("properties", {})
        for p_schema in props.values():
            p_schema.pop("title", None)   # redundant with property name
            # p_schema.pop("default", None)  # keep defaults, they're useful

        # Remove redundant title from the parameters obj itself
        tool.parameters.pop("title", None)
        stripped += 1
    return stripped

# ── Server entry ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    n = _strip_schemas()
    print(f"[Hermes-Lite MCP] Starting: {len(HERMES_TOOLS)} hermes-agent + {n} tools (schemas stripped)", file=sys.stderr)
    mcp.run()
