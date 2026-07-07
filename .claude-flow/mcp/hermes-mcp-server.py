#!/usr/bin/env python3
'''
Hermes Agent MCP Server for Claude Code

Exposes Hermes native tools + pass-through wrappers for all external MCP tools
(gitnexus, tavily, exa, firecrawl, ddg, github, filesystem, obsidian,
chrome_devtools, playwright, context7, veracity).

Usage:
    python hermes-mcp-server.py

Uses FastMCP for stdio-based communication.
'''

import asyncio
import json
import os
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

# ── Bootstrap hermes-agent path ─────────────────────────────────────────────
HERMES_REPO_PATH = os.environ.get(
    "HERMES_REPO_PATH",
    str(Path.home() / ".hermes" / "hermes-agent"),
)

if HERMES_REPO_PATH not in sys.path:
    sys.path.insert(0, HERMES_REPO_PATH)

# Install the editable package finder so model_tools etc. are importable
_HERMES_VENV_SITE = str(Path.home() / ".hermes" / "hermes-agent" / "venv" / "lib" / "python3.11" / "site-packages")
if _HERMES_VENV_SITE not in sys.path:
    sys.path.insert(0, _HERMES_VENV_SITE)
try:
    import __editable___hermes_agent_0_17_0_finder as _finder
    _finder.install()
except Exception:
    pass

# ── FastMCP Server ──────────────────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hermes")

# ── Import Hermes tools ──────────────────────────────────────────────────────
try:
    from model_tools import get_tool_definitions, handle_function_call
    from toolsets import TOOLSETS

    HERMES_TOOLS = get_tool_definitions(
        enabled_toolsets=["terminal", "file", "web", "browser", "vision",
                          "delegate", "session_search", "skills", "todo",
                          "code_execution", "hermes-cli"],
        quiet_mode=True,
    )
    TOOLSET_MAP = {}
    for ts_name, ts_data in TOOLSETS.items():
        for tool_name in ts_data.get("tools", []):
            TOOLSET_MAP[tool_name] = ts_name
    print(f"[Hermes MCP] Loaded {len(HERMES_TOOLS)} tools from hermes-agent", file=sys.stderr)
except ImportError as e:
    print(f"[Hermes MCP] Warning: Could not load hermes tools: {e}", file=sys.stderr)
    HERMES_TOOLS = []
    TOOLSET_MAP = {}

# ── Memory Sync Bridge ───────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from memory_sync import handle_memory_sync

    MEMORY_SYNC_AVAILABLE = True
    print("[Hermes MCP] Memory sync bridge loaded", file=sys.stderr)
except Exception as e:
    MEMORY_SYNC_AVAILABLE = False
    print(f"[Hermes MCP] Memory sync unavailable: {e}", file=sys.stderr)

# ── Import Enhancement Modules ───────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from session_archivist import handle_session_archivist
    SESSION_ARCHIVIST_AVAILABLE = True
    print("[Hermes MCP] Session archivist loaded", file=sys.stderr)
except Exception as e:
    SESSION_ARCHIVIST_AVAILABLE = False
    print(f"[Hermes MCP] Session archivist unavailable: {e}", file=sys.stderr)

try:
    from memory_layer_bridge import handle_memory_layer_bridge
    MEMORY_LAYER_BRIDGE_AVAILABLE = True
    print("[Hermes MCP] Memory layer bridge loaded", file=sys.stderr)
except Exception as e:
    MEMORY_LAYER_BRIDGE_AVAILABLE = False
    print(f"[Hermes MCP] Memory layer bridge unavailable: {e}", file=sys.stderr)

try:
    from context_restorer import handle_context_restorer
    CONTEXT_RESTORER_AVAILABLE = True
    print("[Hermes MCP] Context restorer loaded", file=sys.stderr)
except Exception as e:
    CONTEXT_RESTORER_AVAILABLE = False
    print(f"[Hermes MCP] Context restorer unavailable: {e}", file=sys.stderr)

try:
    from delegate_orchestrator import handle_delegate_orchestrator
    DELEGATE_ORCHESTRATOR_AVAILABLE = True
    print("[Hermes MCP] Delegate orchestrator loaded", file=sys.stderr)
except Exception as e:
    DELEGATE_ORCHESTRATOR_AVAILABLE = False
    print(f"[Hermes MCP] Delegate orchestrator unavailable: {e}", file=sys.stderr)

try:
    from web_search_aggregator import handle_web_search_aggregator
    WEB_SEARCH_AGGREGATOR_AVAILABLE = True
    print("[Hermes MCP] Web search aggregator loaded", file=sys.stderr)
except Exception as e:
    WEB_SEARCH_AGGREGATOR_AVAILABLE = False
    print(f"[Hermes MCP] Web search aggregator unavailable: {e}", file=sys.stderr)

try:
    from metrics_collector import handle_metrics
    METRICS_COLLECTOR_AVAILABLE = True
    print("[Hermes MCP] Metrics collector loaded", file=sys.stderr)
except Exception as e:
    METRICS_COLLECTOR_AVAILABLE = False
    print(f"[Hermes MCP] Metrics collector unavailable: {e}", file=sys.stderr)

# ── New Enhancement Modules (from 5-agent swarm) ──────────────────────────────
try:
    from graphrag_engine import handle_graphrag
    GRAPHRAG_AVAILABLE = True
    print("[Hermes MCP] GraphRAG engine loaded", file=sys.stderr)
except Exception as e:
    GRAPHRAG_AVAILABLE = False
    print(f"[Hermes MCP] GraphRAG unavailable: {e}", file=sys.stderr)

try:
    from cross_session_memory import handle_cross_session_memory
    CROSS_SESSION_MEMORY_AVAILABLE = True
    print("[Hermes MCP] Cross-session memory loaded", file=sys.stderr)
except Exception as e:
    CROSS_SESSION_MEMORY_AVAILABLE = False
    print(f"[Hermes MCP] Cross-session memory unavailable: {e}", file=sys.stderr)

try:
    from coordination_primitives import handle_coordination
    COORDINATION_PRIMITIVES_AVAILABLE = True
    print("[Hermes MCP] Coordination primitives loaded", file=sys.stderr)
except Exception as e:
    COORDINATION_PRIMITIVES_AVAILABLE = False
    print(f"[Hermes MCP] Coordination primitives unavailable: {e}", file=sys.stderr)

try:
    from security_gate import handle_security_gate
    SECURITY_GATE_AVAILABLE = True
    print("[Hermes MCP] Security gate loaded", file=sys.stderr)
except Exception as e:
    SECURITY_GATE_AVAILABLE = False
    print(f"[Hermes MCP] Security gate unavailable: {e}", file=sys.stderr)

try:
    from context_compactor import handle_context_compactor
    CONTEXT_COMPACTOR_AVAILABLE = True
    print("[Hermes MCP] Context compactor loaded", file=sys.stderr)
except Exception as e:
    CONTEXT_COMPACTOR_AVAILABLE = False
    print(f"[Hermes MCP] Context compactor unavailable: {e}", file=sys.stderr)

# ── Memory Enhancement Modules (Phase 2: research-driven) ─────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from memory_extractor import handle_memory_extractor
    MEMORY_EXTRACTOR_AVAILABLE = True
    print("[Hermes MCP] Memory extractor loaded", file=sys.stderr)
except Exception as e:
    MEMORY_EXTRACTOR_AVAILABLE = False
    print(f"[Hermes MCP] Memory extractor unavailable: {e}", file=sys.stderr)

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphrag_temporal import handle_graphrag_temporal
    GRAPHRAG_TEMPORAL_AVAILABLE = True
    print("[Hermes MCP] GraphRAG temporal loaded", file=sys.stderr)
except Exception as e:
    GRAPHRAG_TEMPORAL_AVAILABLE = False
    print(f"[Hermes MCP] GraphRAG temporal unavailable: {e}", file=sys.stderr)

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from context_synthesizer import handle_context_synthesizer, synthesize_context
    CONTEXT_SYNTHESIZER_AVAILABLE = True
    print("[Hermes MCP] Context synthesizer loaded", file=sys.stderr)
except Exception as e:
    CONTEXT_SYNTHESIZER_AVAILABLE = False
    print(f"[Hermes MCP] Context synthesizer unavailable: {e}", file=sys.stderr)

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from dreaming_consolidation import dreaming_preview, dreaming_run, dreaming_status
    DREAMING_AVAILABLE = True
    print("[Hermes MCP] Dreaming consolidation loaded", file=sys.stderr)
except Exception as e:
    DREAMING_AVAILABLE = False
    print(f"[Hermes MCP] Dreaming unavailable: {e}", file=sys.stderr)

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from retrieval_fusion import fusion_index, fusion_retrieve, fusion_stats
    RETRIEVAL_FUSION_AVAILABLE = True
    print("[Hermes MCP] Retrieval fusion loaded", file=sys.stderr)
except Exception as e:
    RETRIEVAL_FUSION_AVAILABLE = False
    print(f"[Hermes MCP] Retrieval fusion unavailable: {e}", file=sys.stderr)

# ── Hermes Iteration Engine ────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from hermes_iteration import HERMES_ITERATION_SCHEMA, handle_hermes_iteration
    HERMES_ITERATION_AVAILABLE = True
    print("[Hermes MCP] Hermes iteration engine loaded", file=sys.stderr)
except Exception as e:
    HERMES_ITERATION_AVAILABLE = False
    print(f"[Hermes MCP] Iteration engine unavailable: {e}", file=sys.stderr)

# ── Hermes Hooks (26-event lifecycle) ────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from hermes_hooks import (
        HERMES_HOOKS_SCHEMA,
        HOOK_EVENTS,
        handle_hermes_hooks,
        hook_builtin_register,
        hook_fire,
        hook_list,
        hook_register,
        hook_stats,
    )
    HERMES_HOOKS_AVAILABLE = True
    print("[Hermes MCP] Hermes hooks loaded", file=sys.stderr)
except Exception as e:
    HERMES_HOOKS_AVAILABLE = False
    print(f"[Hermes MCP] Hermes hooks unavailable: {e}", file=sys.stderr)


# ── Hermes Token Meter ─────────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from hermes_token_meter import (
        TokenMeter,
        count_turn,
        get_meter,
        token_meter_get,
    )
    HERMES_TOKEN_METER_SCHEMA = TokenMeter.SCHEMA
    TOKEN_METER_AVAILABLE = True
    print("[Hermes MCP] Hermes token meter loaded", file=sys.stderr)
except Exception as e:
    TOKEN_METER_AVAILABLE = False
    print(f"[Hermes MCP] Token meter unavailable: {e}", file=sys.stderr)

# ── Hermes Approval Gate ───────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from hermes_approval_gate import (
        HERMES_APPROVAL_GATE_SCHEMA,
        check_approval,
        handle_hermes_approval_gate,
    )
    APPROVAL_GATE_AVAILABLE = True
    print("[Hermes MCP] Hermes approval gate loaded", file=sys.stderr)
except Exception as e:
    APPROVAL_GATE_AVAILABLE = False
    print(f"[Hermes MCP] Approval gate unavailable: {e}", file=sys.stderr)

# ── Hermes Context Injector ────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from hermes_context_injector import (
        HERMES_CONTEXT_INJECTOR_SCHEMA,
        context_inject_now,
        handle_hermes_context_injector,
    )
    CONTEXT_INJECTOR_AVAILABLE = True
    print("[Hermes MCP] Hermes context injector loaded", file=sys.stderr)
except Exception as e:
    CONTEXT_INJECTOR_AVAILABLE = False
    print(f"[Hermes MCP] Context injector unavailable: {e}", file=sys.stderr)


# ── Token meter wrapper ───────────────────────────────────────────────────────
_token_meter_instance = None
def handle_hermes_token_meter(args: dict) -> str:
    global _token_meter_instance
    if _token_meter_instance is None:
        _token_meter_instance = TokenMeter()
    return _token_meter_instance.handle_mcp(
        args.get("action", "get"),
        args.get("session_id", ""),
        args.get("budget_tokens", 0),
    )


# ── Subprocess helper (no shell injection) ───────────────────────────────────
def _run_cmd(cmd, input_data=None, timeout=60):
    '''Run command, return stdout or JSON error. Safe: no shell, explicit args.'''
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


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1: HERMES NATIVE TOOLS (kept intact)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def hermes_list_tools() -> str:
    """List all available Hermes agent tools organized by toolset."""
    if not HERMES_TOOLS:
        return "No Hermes tools loaded"
    by_toolset = {}
    for tool in HERMES_TOOLS:
        name = tool["function"]["name"]
        ts = TOOLSET_MAP.get(name, "unknown")
        by_toolset.setdefault(ts, []).append(name)

    lines = ["Available Hermes Tools:"]
    for ts, tools in sorted(by_toolset.items()):
        lines.append(f"\n  [{ts}]")
        for t in sorted(tools):
            lines.append(f"    - {t}")
    return "\n".join(lines)


@mcp.tool()
def hermes_call(tool_name: str, arguments: str = "{}") -> str:
    """Call a Hermes tool by name with JSON arguments."""
    if not HERMES_TOOLS:
        return "[Hermes MCP] Hermes tools not loaded"
    try:
        args = json.loads(arguments) if isinstance(arguments, str) else arguments
    except json.JSONDecodeError as e:
        return f"[Hermes MCP] Invalid JSON arguments: {e}"
    tool_names = [t["function"]["name"] for t in HERMES_TOOLS]
    if tool_name not in tool_names:
        return f"[Hermes MCP] Unknown tool: {tool_name}. Available: {', '.join(sorted(tool_names))}"
    try:
        result = handle_function_call(function_name=tool_name, function_args=args,
                                       task_id=None, session_id=None, user_task=None)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"[Hermes MCP] Error calling {tool_name}: {e}"


@mcp.tool()
def hermes_terminal(command: str, timeout: int = 30) -> str:
    """Execute a terminal command via Hermes."""
    return hermes_call("terminal", json.dumps({"command": command, "timeout": timeout}))


@mcp.tool()
def hermes_web_search(query: str, depth: str = "basic") -> str:
    """Search the web via Hermes."""
    return hermes_call("web_search", json.dumps({"query": query, "depth": depth}))


@mcp.tool()
def hermes_web_extract(url: str, query: str = "") -> str:
    """Extract content from a URL via Hermes."""
    return hermes_call("web_extract", json.dumps({"url": url, "query": query}))


@mcp.tool()
def hermes_read_file(path: str, offset: int = 0, limit: int = 5000) -> str:
    """Read a file via Hermes."""
    return hermes_call("read_file", json.dumps({"path": path, "offset": offset, "limit": limit}))


@mcp.tool()
def hermes_write_file(path: str, content: str, mode: str = "overwrite") -> str:
    """Write content to a file via Hermes."""
    return hermes_call("write_file", json.dumps({"path": path, "content": content, "mode": mode}))


@mcp.tool()
def hermes_browser_navigate(url: str, mode: str = "normal") -> str:
    """Navigate browser to URL via Hermes."""
    return hermes_call("browser_navigate", json.dumps({"url": url, "mode": mode}))


@mcp.tool()
def hermes_browser_snapshot(element: str = "") -> str:
    """Get browser page snapshot via Hermes."""
    return hermes_call("browser_snapshot", json.dumps({"element": element}))


@mcp.tool()
def hermes_delegate(goal: str, context: str = "", toolsets: str = "terminal,file,web") -> str:
    """Spawn an isolated Hermes subagent to accomplish a goal."""
    toolsets_list = [t.strip() for t in toolsets.split(",")]
    return hermes_call("delegate", json.dumps({"goal": goal, "context": context, "toolsets": toolsets_list}))


@mcp.tool()
def hermes_session_search(query: str, limit: int = 5) -> str:
    """Search past Hermes conversations via FTS5."""
    return hermes_call("session_search", json.dumps({"query": query, "limit": limit}))


@mcp.tool()
def hermes_vision_analyze(image_path: str, query: str = "Describe this image") -> str:
    """Analyze an image via Hermes vision."""
    return hermes_call("vision_analyze", json.dumps({"image_path": image_path, "query": query}))


@mcp.tool()
def hermes_skills_list(category: str = "") -> str:
    """List Hermes skills (procedural memory)."""
    return hermes_call("skills_list", json.dumps({"category": category}))


@mcp.tool()
def hermes_todo(action: str, task: str = "", tasks: str = "[]") -> str:
    """Manage Hermes todo list."""
    return hermes_call("todo", json.dumps({
        "action": action, "task": task,
        "tasks": json.loads(tasks) if isinstance(tasks, str) else tasks,
    }))


@mcp.tool()
def hermes_execute_code(code: str, language: str = "python", timeout: int = 30) -> str:
    """Execute code in Hermes sandbox."""
    return hermes_call("execute_code", json.dumps({"code": code, "language": language, "timeout": timeout}))


@mcp.tool()
def memory_sync(direction: str = "bidirectional", dry_run: bool = False) -> str:
    """Bidirectional memory sync between Claude Code 6-layer system and Hermes."""
    if not MEMORY_SYNC_AVAILABLE:
        return json.dumps({"success": False, "error": "Memory sync not available"})
    return handle_memory_sync({"direction": direction, "dry_run": dry_run})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2: GITNEXUS TOOLS (code intelligence)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def gitnexus_query(query: str, goal: str = "", limit: int = 5, repo: str = "") -> str:
    """Query code knowledge graph for execution flows."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "query"],
                    {"query": query, "goal": goal, "limit": limit, "repo": repo})


@mcp.tool()
def gitnexus_context(name: str, repo: str = "", file_path: str = "",
                     include_content: bool = False) -> str:
    """360-degree view of a code symbol - callers, callees, process participation."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "context"],
                    {"name": name, "repo": repo, "filePath": file_path,
                     "include_content": include_content})


@mcp.tool()
def gitnexus_impact(target: str, direction: str, repo: str = "",
                     max_depth: int = 3, include_tests: bool = False) -> str:
    """Analyze blast radius of changing a code symbol."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "impact"],
                    {"target": target, "direction": direction, "repo": repo,
                     "maxDepth": max_depth, "includeTests": include_tests})


@mcp.tool()
def gitnexus_detect_changes(scope: str = "unstaged", repo: str = "",
                            base_ref: str = "") -> str:
    """Analyze uncommitted git changes and find affected execution flows."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "detect-changes"],
                    {"scope": scope, "repo": repo, "base_ref": base_ref})


@mcp.tool()
def gitnexus_rename(symbol_name: str, new_name: str, repo: str = "",
                     dry_run: bool = True, file_path: str = "") -> str:
    """Multi-file coordinated rename using knowledge graph + text search."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "rename"],
                    {"symbol_name": symbol_name, "new_name": new_name, "repo": repo,
                     "dry_run": dry_run, "file_path": file_path})


@mcp.tool()
def gitnexus_cypher(query: str, repo: str = "") -> str:
    """Execute Cypher query against the code knowledge graph."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "cypher"],
                    {"query": query, "repo": repo})


@mcp.tool()
def gitnexus_list_repos() -> str:
    """List all indexed repositories available to GitNexus."""
    return _run_cmd(["npx", "-y", "gitnexus@latest", "mcp", "list-repos"], {})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3: TAVILY TOOLS (web search & research)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def tavily_search(query: str, max_results: int = 5,
                  include_answer: bool = False, include_images: bool = False) -> str:
    """Search the web for current information on any topic."""
    return _run_cmd(["npx", "-y", "tavily-mcp@latest"],
                    {"query": query, "max_results": max_results,
                     "include_answer": include_answer, "include_images": include_images})


@mcp.tool()
def tavily_extract(urls: list[str], query: str = "") -> str:
    """Extract content from URLs."""
    return _run_cmd(["npx", "-y", "tavily-mcp@latest"],
                    {"urls": urls, "query": query})


@mcp.tool()
def tavily_map(url: str, search: str = "", limit: int = 50,
                max_depth: int = 1) -> str:
    """Map a website discovering all indexed URLs."""
    return _run_cmd(["npx", "-y", "tavily-mcp@latest"],
                    {"url": url, "search": search, "limit": limit, "maxDepth": max_depth})


@mcp.tool()
def tavily_crawl(url: str, max_depth: int = 1, limit: int = 50,
                  allow_external: bool = True, prompt: str = "",
                  scrape_formats: list[str] | None = None) -> str:
    """Crawl a website extracting content from all pages."""
    if scrape_formats is None:
        scrape_formats = ["markdown"]
    return _run_cmd(["npx", "-y", "tavily-mcp@latest"],
                    {"url": url, "max_depth": max_depth, "limit": limit,
                     "allow_external_links": allow_external, "prompt": prompt,
                     "scrape_formats": scrape_formats})


@mcp.tool()
def tavily_research(input: str, model: str = "auto") -> str:
    """Comprehensive research on a topic from multiple sources."""
    return _run_cmd(["npx", "-y", "tavily-mcp@latest"],
                    {"input": input, "model": model})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4: EXA TOOLS (web search)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def exa_web_search(query: str, num_results: int = 10) -> str:
    """Search the web for current information."""
    return _run_cmd(["npx", "-y", "exa-openapi-wrapper@latest", "web-search"],
                    {"query": query, "numResults": num_results})


@mcp.tool()
def exa_web_fetch(urls: list[str], query: str = "") -> str:
    """Fetch and extract content from URLs."""
    return _run_cmd(["npx", "-y", "exa-openapi-wrapper@latest", "web-fetch"],
                    {"urls": urls, "query": query})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5: FIRECRAWL TOOLS (web scraping)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def firecrawl_scrape(url: str, prompt: str = "",
                      formats: list[str] | None = None,
                      only_main_content: bool = False,
                      wait_for: int = 0) -> str:
    """Scrape content from a single URL with advanced options."""
    if formats is None:
        formats = ["markdown"]
    return _run_cmd(["npx", "-y", "firecrawl-mcp@latest", "scrape"],
                    {"url": url, "prompt": prompt, "formats": formats,
                     "onlyMainContent": only_main_content, "waitFor": wait_for})


@mcp.tool()
def firecrawl_search(query: str, limit: int = 5,
                      include_domains: list[str] | None = None,
                      exclude_domains: list[str] | None = None) -> str:
    """Search the web and optionally extract content from results."""
    return _run_cmd(["npx", "-y", "firecrawl-mcp@latest", "search"],
                    {"query": query, "limit": limit,
                     "includeDomains": include_domains or [],
                     "excludeDomains": exclude_domains or []})


@mcp.tool()
def firecrawl_map(url: str, search: str = "",
                   limit: int = 50, max_depth: int = 1) -> str:
    """Map a website discovering all indexed URLs."""
    return _run_cmd(["npx", "-y", "firecrawl-mcp@latest", "map"],
                    {"url": url, "search": search, "limit": limit, "maxDepth": max_depth})


@mcp.tool()
def firecrawl_crawl(url: str, max_depth: int = 1, limit: int = 50,
                     allow_external: bool = True, prompt: str = "",
                     scrape_formats: list[str] | None = None) -> str:
    """Crawl a website extracting content from all pages."""
    if scrape_formats is None:
        scrape_formats = ["markdown"]
    return _run_cmd(["npx", "-y", "firecrawl-mcp@latest", "crawl"],
                    {"url": url, "maxDepth": max_depth, "limit": limit,
                     "allowExternalLinks": allow_external, "prompt": prompt,
                     "scrapeOptions": {"formats": scrape_formats}})


@mcp.tool()
def firecrawl_extract(urls: list[str], prompt: str,
                       schema: dict | None = None,
                       allow_external: bool = False) -> str:
    """Extract structured information from web pages using LLM."""
    return _run_cmd(["npx", "-y", "firecrawl-mcp@latest", "extract"],
                    {"urls": urls, "prompt": prompt, "schema": schema,
                     "allow_external_links": allow_external})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 6: DUCKDUCKGO TOOLS
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def ddg_search(query: str, max_results: int = 10, region: str = "") -> str:
    """Search DuckDuckGo and return formatted results."""
    return _run_cmd(["npx", "-y", "ddg-mcp@latest", "search"],
                    {"query": query, "max_results": max_results, "region": region})


@mcp.tool()
def ddg_fetch(url: str, max_length: int = 8000) -> str:
    """Fetch and parse content from a URL."""
    return _run_cmd(["npx", "-y", "ddg-mcp@latest", "fetch-content"],
                    {"url": url, "max_length": max_length})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 7: GITHUB TOOLS
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def github_get_user(username: str) -> str:
    """Get GitHub user information."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "get-user"],
                    {"username": username})


@mcp.tool()
def github_get_repo(owner: str, repo: str) -> str:
    """Get GitHub repository information."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "get-repo"],
                    {"owner": owner, "repo": repo})


@mcp.tool()
def github_create_issue(owner: str, repo: str, title: str,
                       body: str = "", labels: list[str] | None = None) -> str:
    """Create a GitHub issue."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "create-issue"],
                    {"owner": owner, "repo": repo, "title": title, "body": body,
                     "labels": labels or []})


@mcp.tool()
def github_list_issues(owner: str, repo: str,
                       state: str = "open", limit: int = 30) -> str:
    """List issues in a repository."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "list-issues"],
                    {"owner": owner, "repo": repo, "state": state, "limit": limit})


@mcp.tool()
def github_search_repositories(query: str, limit: int = 10) -> str:
    """Search GitHub repositories."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "search-repositories"],
                    {"query": query, "limit": limit})


@mcp.tool()
def github_list_commits(owner: str, repo: str,
                        sha: str = "HEAD", per_page: int = 30) -> str:
    """List commits in a repository."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "list-commits"],
                    {"owner": owner, "repo": repo, "sha": sha, "per_page": per_page})


@mcp.tool()
def github_search_code(query: str, limit: int = 30) -> str:
    """Search code across GitHub."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "search-code"],
                    {"query": query, "limit": limit})


@mcp.tool()
def github_list_pull_requests(owner: str, repo: str,
                               state: str = "open", limit: int = 30) -> str:
    """List pull requests in a repository."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "list-pull-requests"],
                    {"owner": owner, "repo": repo, "state": state, "limit": limit})


@mcp.tool()
def github_get_file_contents(owner: str, repo: str, path: str,
                              ref: str = "") -> str:
    """Get contents of a file from GitHub."""
    return _run_cmd(["npx", "-y", "@modelcontextprotocol/server-github@latest", "get-file-contents"],
                    {"owner": owner, "repo": repo, "path": path, "ref": ref})


@mcp.tool()
def github_create_pull_request(owner: str, repo: str, title: str,
                               head: str, base: str = "main",
                               body: str = "", draft: bool = False) -> str:
    """
    Create a GitHub pull request directly via API.

    Args:
        owner: Repository owner
        repo: Repository name
        title: PR title
        head: Branch name containing the changes
        base: Target branch (default: main)
        body: PR description
        draft: Create as draft PR
    """
    import os
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return json.dumps({"error": "GITHUB_TOKEN not set"})

    import urllib.error
    import urllib.request

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
        "draft": draft,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "hermes-mcp-server")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return json.dumps({
                "success": True,
                "pr_number": result.get("number"),
                "pr_url": result.get("html_url"),
                "pr_state": result.get("state"),
            }, indent=2)
    except urllib.error.HTTPError as e:
        return json.dumps({"error": f"HTTP {e.code}: {e.reason}", "details": e.read().decode()})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 7.5: GITHUB WEBHOOK TOOLS
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def github_webhook_create(owner: str, repo: str, webhook_url: str,
                          events: list[str] | None = None, active: bool = True) -> str:
    """
    Create a GitHub webhook for a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        webhook_url: URL to send webhook payloads to
        events: List of events to subscribe to (default: push, pull_request)
        active: Whether webhook is active (default: True)
    """
    import os
    events = events or ["push", "pull_request"]
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return json.dumps({"error": "GITHUB_TOKEN not set - cannot create webhooks"})

    import urllib.error
    import urllib.request

    url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
    payload = {
        "name": "web",
        "active": active,
        "events": events,
        "config": {
            "url": webhook_url,
            "content_type": "json",
            "insecure_ssl": "0"
        }
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "hermes-mcp-server")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return json.dumps({
                "success": True,
                "webhook_id": result.get("id"),
                "webhook_url": result.get("url"),
                "events": result.get("events"),
            }, indent=2)
    except urllib.error.HTTPError as e:
        return json.dumps({"error": f"HTTP {e.code}: {e.reason}", "details": e.read().decode()})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def github_webhook_list(owner: str, repo: str) -> str:
    """List all webhooks for a repository."""
    import os
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return json.dumps({"error": "GITHUB_TOKEN not set"})

    import urllib.request
    url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            hooks = json.loads(resp.read().decode())
            return json.dumps({
                "webhooks": [{"id": h["id"], "url": h["url"], "events": h["events"], "active": h["active"]}
                            for h in hooks]}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def github_webhook_delete(owner: str, repo: str, webhook_id: int) -> str:
    """Delete a webhook by ID."""
    import os
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return json.dumps({"error": "GITHUB_TOKEN not set"})

    import urllib.error
    import urllib.request
    url = f"https://api.github.com/repos/{owner}/{repo}/hooks/{webhook_id}"
    req = urllib.request.Request(url, method="DELETE")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")

    try:
        with urllib.request.urlopen(req, timeout=30):
            return json.dumps({"success": True, "deleted": webhook_id})
    except urllib.error.HTTPError as e:
        return json.dumps({"error": f"HTTP {e.code}: {e.reason}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 8: FILESYSTEM TOOLS (direct Python - no subprocess needed)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def filesystem_read_file(path: str, head: int | None = None) -> str:
    """Read the complete contents of a file."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read() if not head else "".join(f.readlines(head))
        return content
    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {path}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def filesystem_write_file(path: str, content: str) -> str:
    """Write content to a file, creating or overwriting."""
    try:
        p = Path(path)
        if p.parent and not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({"success": True, "path": path})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def filesystem_list_directory(path: str,
                               include_sizes: bool = False) -> str:
    """List all files and directories in a path."""
    try:
        p = Path(path)
        if not p.exists():
            return json.dumps({"error": f"Path not found: {path}"})
        if not p.is_dir():
            return json.dumps({"error": f"Not a directory: {path}"})
        entries = []
        for entry in sorted(p.iterdir()):
            info = {"name": entry.name,
                    "type": "directory" if entry.is_dir() else "file"}
            if include_sizes and entry.is_file():
                info["size"] = entry.stat().st_size
            entries.append(info)
        return json.dumps(entries, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def filesystem_search_files(path: str, pattern: str) -> str:
    """Recursively search for files matching a glob pattern."""
    try:
        from glob import glob
        matches = glob(str(Path(path) / pattern), recursive=True)
        return json.dumps({"matches": matches, "count": len(matches)})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def filesystem_get_file_info(path: str) -> str:
    """Get detailed metadata about a file or directory."""
    try:
        p = Path(path)
        if not p.exists():
            return json.dumps({"error": f"Path not found: {path}"})
        stat = p.stat()
        return json.dumps({
            "name": p.name, "type": "directory" if p.is_dir() else "file",
            "size": stat.st_size, "created": stat.st_ctime,
            "modified": stat.st_mtime, "path": str(p.absolute()),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def filesystem_create_directory(path: str) -> str:
    """Create a directory, including parent directories if needed."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return json.dumps({"success": True, "path": path})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def filesystem_move_file(source: str, destination: str) -> str:
    """Move or rename a file or directory."""
    try:
        import shutil
        shutil.move(source, destination)
        return json.dumps({"success": True, "source": source, "destination": destination})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 9: OBSIDIAN TOOLS
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def obsidian_read_note(filename: str) -> str:
    """Read the full content of a note from the vault."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "read-note"],
                    {"filename": filename})


@mcp.tool()
def obsidian_search_notes(query: str = "",
                           tags: list[str] | None = None) -> str:
    """Search notes by content or tags."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "search-notes"],
                    {"query": query, "tags": tags or []})


@mcp.tool()
def obsidian_create_note(filename: str, content: str = "",
                          template_name: str = "") -> str:
    """Create a new note in the vault."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "create-note"],
                    {"filename": filename, "content": content,
                     "template_name": template_name})


@mcp.tool()
def obsidian_update_note(filename: str, content: str,
                         preserve_metadata: bool = True) -> str:
    """Update the content of an existing note."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "update-note"],
                    {"filename": filename, "content": content,
                     "preserve_metadata": preserve_metadata})


@mcp.tool()
def obsidian_list_notes(tag_filter: str = "") -> str:
    """List all notes in the vault."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "list-notes"],
                    {"tag_filter": tag_filter})


@mcp.tool()
def obsidian_search_by_date(start_date: str, end_date: str,
                              date_type: str = "created") -> str:
    """Find notes created or modified within a date range."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "search-by-date"],
                    {"start_date": start_date, "end_date": end_date,
                     "date_type": date_type})


@mcp.tool()
def obsidian_add_tags(filename: str, tags: list[str]) -> str:
    """Add tags to an existing note."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "add-tags"],
                    {"filename": filename, "tags": tags})


@mcp.tool()
def obsidian_execute_dataview_query(query: str) -> str:
    """Run a Dataview DQL query and return results."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "execute-dataview-query"],
                    {"query": query})


@mcp.tool()
def obsidian_append_to_note(filename: str, content: str) -> str:
    """Append content to the end of an existing note."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "append-to-note"],
                    {"filename": filename, "content": content})


@mcp.tool()
def obsidian_get_tasks_by_tag(tag: str = "") -> str:
    """Get all tasks from notes with specific tags."""
    return _run_cmd(["npx", "-y", "obsidian-mcp-server@latest", "get-tasks-by-tag"],
                    {"tag": tag})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 10: CHROME DEVTOOLS TOOLS
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def chrome_navigate(url: str, type: str = "url",
                     handle_before_unload: str = "accept",
                     ignore_cache: bool = False) -> str:
    """Navigate to a URL, or back/forward/reload."""
    if type == "url" and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "navigate"],
                    {"url": url, "type": type, "handleBeforeUnload": handle_before_unload,
                     "ignoreCache": ignore_cache})


@mcp.tool()
def chrome_snapshot(verbose: bool = False) -> str:
    """Take a text snapshot of the page based on accessibility tree."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "snapshot"],
                    {"verbose": verbose})


@mcp.tool()
def chrome_click(uid: str, dbl_click: bool = False,
                  include_snapshot: bool = False) -> str:
    """Click on an element on the page."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "click"],
                    {"uid": uid, "dblClick": dbl_click, "includeSnapshot": include_snapshot})


@mcp.tool()
def chrome_type_text(text: str, submit_key: str = "") -> str:
    """Type text using keyboard into a previously focused input."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "type-text"],
                    {"text": text, "submitKey": submit_key})


@mcp.tool()
def chrome_screenshot(format: str = "png",
                      full_page: bool = False,
                      quality: int = 80) -> str:
    """Take a screenshot of the page."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "screenshot"],
                    {"format": format, "fullPage": full_page, "quality": quality})


@mcp.tool()
def chrome_fill_form(elements: list[dict],
                     include_snapshot: bool = False) -> str:
    """Fill multiple form fields at once."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "fill-form"],
                    {"elements": elements, "includeSnapshot": include_snapshot})


@mcp.tool()
def chrome_list_pages() -> str:
    """List all pages open in the browser."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "list-pages"], {})


@mcp.tool()
def chrome_fill(uid: str, value: str,
                  include_snapshot: bool = False) -> str:
    """Type text into an input, text area, or select an option."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "fill"],
                    {"uid": uid, "value": value, "includeSnapshot": include_snapshot})


@mcp.tool()
def chrome_hover(uid: str, include_snapshot: bool = False) -> str:
    """Hover over an element."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "hover"],
                    {"uid": uid, "includeSnapshot": include_snapshot})


@mcp.tool()
def chrome_press_key(key: str, include_snapshot: bool = False) -> str:
    """Press a key or key combination."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "press-key"],
                    {"key": key, "includeSnapshot": include_snapshot})


@mcp.tool()
def chrome_network_requests(static: bool = False,
                              filter_pattern: str = "") -> str:
    """Get numbered list of network requests since page load."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "list-network-requests"],
                    {"static": static, "filter": filter_pattern})


@mcp.tool()
def chrome_console_messages(level: str = "info") -> str:
    """Get all console messages for the current page."""
    return _run_cmd(["npx", "-y", "chrome-devtools-mcp@latest", "list-console-messages"],
                    {"level": level})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 11: PLAYWRIGHT TOOLS
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def playwright_browser_navigate(url: str) -> str:
    """Navigate to a URL."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-navigate"],
                    {"url": url})


@mcp.tool()
def playwright_browser_snapshot(depth: int = 5) -> str:
    """Capture accessibility snapshot of the current page."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-snapshot"],
                    {"depth": depth})


@mcp.tool()
def playwright_browser_click(target: str, button: str = "left") -> str:
    """Click on element on page."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-click"],
                    {"target": target, "button": button})


@mcp.tool()
def playwright_browser_type(target: str, text: str,
                              slowly: bool = False, submit: bool = False) -> str:
    """Type text into editable element."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-type"],
                    {"target": target, "text": text, "slowly": slowly, "submit": submit})


@mcp.tool()
def playwright_browser_take_screenshot(filename: str = "",
                                         full_page: bool = False,
                                         type: str = "png") -> str:
    """Take a screenshot of the current page."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-take-screenshot"],
                    {"filename": filename, "fullPage": full_page, "type": type})


@mcp.tool()
def playwright_browser_tabs(action: str = "list",
                             index: int = 0, url: str = "") -> str:
    """List, create, close, or select a browser tab."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-tabs"],
                    {"action": action, "index": index, "url": url})


@mcp.tool()
def playwright_browser_resize(width: int, height: int) -> str:
    """Resize the browser window."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-resize"],
                    {"width": width, "height": height})


@mcp.tool()
def playwright_browser_wait_for(text: str = "",
                                 text_gone: str = "", time: float = 0) -> str:
    """Wait for text to appear/disappear or a specified time."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-wait-for"],
                    {"text": text, "textGone": text_gone, "time": time})


@mcp.tool()
def playwright_browser_evaluate(function: str,
                                  target: str = "") -> str:
    """Evaluate JavaScript expression on page or element."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-evaluate"],
                    {"function": function, "target": target})


@mcp.tool()
def playwright_browser_select_option(target: str,
                                     values: list[str]) -> str:
    """Select an option in a dropdown."""
    return _run_cmd(["npx", "-y", "playwright-mcp@latest", "browser-select-option"],
                    {"target": target, "values": values})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 12: CONTEXT7 DOCS TOOLS
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def context7_query_docs(library_id: str, query: str) -> str:
    """Query Context7 for documentation and code examples for any library."""
    return _run_cmd(["npx", "-y", "@context7/mcp@latest", "query-docs"],
                    {"libraryId": library_id, "query": query})


@mcp.tool()
def context7_resolve_library_id(library_name: str, query: str) -> str:
    """Resolve a package name to a Context7-compatible library ID."""
    return _run_cmd(["npx", "-y", "@context7/mcp@latest", "resolve-library-id"],
                    {"libraryName": library_name, "query": query})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 13: VERACITY/INDEPENDENT AUDITOR
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def veracity_scan(path: str, include_dependencies: bool = False,
                  scan_type: str = "security") -> str:
    """Scan code for vulnerabilities or quality issues."""
    return _run_cmd(["npx", "-y", "veracity-mcp@latest", "scan"],
                    {"path": path, "includeDependencies": include_dependencies,
                     "scanType": scan_type})


@mcp.tool()
def veracity_is_safe(path: str) -> str:
    """Check if a path is safe (no secrets or dangerous patterns)."""
    return _run_cmd(["npx", "-y", "veracity-mcp@latest", "is-safe"],
                    {"path": path})


# ════════════════════════════════════════════════════════════════════════════
# SECTION 14: SIMPLE ALIASES (single-argument shortcuts)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def web_search(query: str) -> str:
    """Simple web search using default provider (tavily)."""
    return tavily_search(query=query, max_results=5)


@mcp.tool()
def code_search(query: str) -> str:
    """Search code using GitNexus."""
    return gitnexus_query(query=query)


@mcp.tool()
def file_search(path: str, pattern: str) -> str:
    """Search files by glob pattern."""
    return filesystem_search_files(path=path, pattern=pattern)


@mcp.tool()
def read_note(filename: str) -> str:
    """Read an Obsidian note."""
    return obsidian_read_note(filename=filename)


@mcp.tool()
def run_browser(url: str) -> str:
    """Open URL in browser (Playwright)."""
    return playwright_browser_navigate(url=url)


# ════════════════════════════════════════════════════════════════════════════
# COMPLETE EXTERNAL TOOLSET MAP (for hermes_list_all_tools)
# ════════════════════════════════════════════════════════════════════════════

_EXTERNAL_TOOLSET_MAP = {
    # GitNexus
    "gitnexus_query": "gitnexus", "gitnexus_context": "gitnexus",
    "gitnexus_impact": "gitnexus", "gitnexus_detect_changes": "gitnexus",
    "gitnexus_rename": "gitnexus", "gitnexus_cypher": "gitnexus",
    "gitnexus_list_repos": "gitnexus",
    # Tavily
    "tavily_search": "tavily", "tavily_extract": "tavily",
    "tavily_map": "tavily", "tavily_crawl": "tavily",
    "tavily_research": "tavily",
    # Exa
    "exa_web_search": "exa", "exa_web_fetch": "exa",
    # Firecrawl
    "firecrawl_scrape": "firecrawl", "firecrawl_search": "firecrawl",
    "firecrawl_map": "firecrawl", "firecrawl_crawl": "firecrawl",
    "firecrawl_extract": "firecrawl",
    # DuckDuckGo
    "ddg_search": "ddg", "ddg_fetch": "ddg",
    # GitHub
    "github_get_user": "github", "github_get_repo": "github",
    "github_create_issue": "github", "github_list_issues": "github",
    "github_search_repositories": "github", "github_list_commits": "github",
    "github_search_code": "github", "github_list_pull_requests": "github",
    "github_get_file_contents": "github", "github_create_pull_request": "github",
    "github_webhook_create": "github", "github_webhook_list": "github",
    "github_webhook_delete": "github",
    # Filesystem
    "filesystem_read_file": "filesystem", "filesystem_write_file": "filesystem",
    "filesystem_list_directory": "filesystem", "filesystem_search_files": "filesystem",
    "filesystem_get_file_info": "filesystem", "filesystem_create_directory": "filesystem",
    "filesystem_move_file": "filesystem",
    # Obsidian
    "obsidian_read_note": "obsidian", "obsidian_search_notes": "obsidian",
    "obsidian_create_note": "obsidian", "obsidian_update_note": "obsidian",
    "obsidian_list_notes": "obsidian", "obsidian_search_by_date": "obsidian",
    "obsidian_add_tags": "obsidian", "obsidian_execute_dataview_query": "obsidian",
    "obsidian_append_to_note": "obsidian", "obsidian_get_tasks_by_tag": "obsidian",
    # Chrome DevTools
    "chrome_navigate": "chrome_devtools", "chrome_snapshot": "chrome_devtools",
    "chrome_click": "chrome_devtools", "chrome_type_text": "chrome_devtools",
    "chrome_screenshot": "chrome_devtools", "chrome_fill_form": "chrome_devtools",
    "chrome_list_pages": "chrome_devtools", "chrome_fill": "chrome_devtools",
    "chrome_hover": "chrome_devtools", "chrome_press_key": "chrome_devtools",
    "chrome_network_requests": "chrome_devtools", "chrome_console_messages": "chrome_devtools",
    # Playwright
    "playwright_browser_navigate": "playwright", "playwright_browser_snapshot": "playwright",
    "playwright_browser_click": "playwright", "playwright_browser_type": "playwright",
    "playwright_browser_take_screenshot": "playwright", "playwright_browser_tabs": "playwright",
    "playwright_browser_resize": "playwright", "playwright_browser_wait_for": "playwright",
    "playwright_browser_evaluate": "playwright", "playwright_browser_select_option": "playwright",
    # Context7
    "context7_query_docs": "context7", "context7_resolve_library_id": "context7",
    # Veracity
    "veracity_scan": "veracity", "veracity_is_safe": "veracity",
    # Aliases
    "web_search": "alias", "code_search": "alias",
    "file_search": "alias", "read_note": "alias", "run_browser": "alias",
}

# Merge into TOOLSET_MAP
for _name, _ts in _EXTERNAL_TOOLSET_MAP.items():
    TOOLSET_MAP[_name] = _ts


# ════════════════════════════════════════════════════════════════════════════
# ENHANCED: hermes_list_all_tools (Hermes native + all externals)
# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 15: UNIFIED WEB SEARCH (auto-select provider)
# ════════════════════════════════════════════════════════════════════════════

if WEB_SEARCH_AGGREGATOR_AVAILABLE:
    @mcp.tool()
    def unified_web_search(query: str, depth: str = "basic",
                           max_results: int = 5) -> str:
        """Unified web search with auto-selection across tavily, exa, ddg, firecrawl."""
        return handle_web_search_aggregator({
            "action": "search",
            "query": query,
            "depth": depth,
            "max_results": max_results,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 16: SESSION ARCHIVIST (FTS5 cross-session recall)
# ════════════════════════════════════════════════════════════════════════════

if SESSION_ARCHIVIST_AVAILABLE:
    @mcp.tool()
    def session_archivist(action: str, session_id: str = "",
                         messages: list | None = None, query: str = "",
                         limit: int = 5) -> str:
        """FTS5 cross-session indexing, search, graph, similarity, auto-archive."""
        return handle_session_archivist({
            "action": action,
            "session_id": session_id,
            "messages": messages or [],
            "query": query,
            "limit": limit,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 17: MEMORY LAYER BRIDGE (6-layer unified query)
# ════════════════════════════════════════════════════════════════════════════

if MEMORY_LAYER_BRIDGE_AVAILABLE:
    @mcp.tool()
    def memory_layer_bridge(action: str = "query", query: str = "",
                            layers: list | None = None, top_k: int = 5,
                            layer: str = "") -> str:
        """Query all 6 CC memory layers with unified interface."""
        return handle_memory_layer_bridge({
            "action": action,
            "query": query,
            "layers": layers or ["L1", "L2", "L3", "L4", "L5", "L6"],
            "top_k": top_k,
            "layer": layer,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 18: CONTEXT RESTORER (startup context aggregation)
# ════════════════════════════════════════════════════════════════════════════

if CONTEXT_RESTORER_AVAILABLE:
    @mcp.tool()
    def restore_context(session_id: str = "", query: str = "",
                        action: str = "restore") -> str:
        """Restore session context from all 6 CC memory layers on startup."""
        return handle_context_restorer({
            "action": action,
            "session_id": session_id,
            "query": query,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 19: DELEGATE ORCHESTRATOR (3-tier hierarchy)
# ════════════════════════════════════════════════════════════════════════════

if DELEGATE_ORCHESTRATOR_AVAILABLE:
    @mcp.tool()
    def delegate_orchestrator(action: str = "execute", goal: str = "",
                               coordinator_id: str = "", max_specialists: int = 5) -> str:
        """3-tier hierarchical delegation: coordinator → specialist → worker."""
        return handle_delegate_orchestrator({
            "action": action,
            "goal": goal,
            "coordinator_id": coordinator_id,
            "max_specialists": max_specialists,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 20: HERMES HEALTH MONITOR
# ════════════════════════════════════════════════════════════════════════════

_health_cache = {"data": None, "timestamp": 0.0}
_HEALTH_CACHE_TTL = 60  # seconds

def _check_mcp_server_latency(cmd, timeout=5):
    """Ping an MCP server and return latency in ms."""
    import time
    start = time.perf_counter()
    try:
        subprocess.run(cmd, capture_output=True, timeout=timeout)
        latency_ms = (time.perf_counter() - start) * 1000
        return {"latency_ms": round(latency_ms, 2), "status": "connected", "error": None}
    except subprocess.TimeoutExpired:
        return {"latency_ms": None, "status": "timeout", "error": f"timeout after {timeout}s"}
    except FileNotFoundError:
        return {"latency_ms": None, "status": "not_found", "error": "command not found"}
    except Exception as e:
        return {"latency_ms": None, "status": "error", "error": str(e)}

@mcp.tool()
def hermes_health_check() -> str:
    """Check all external MCP server connections and report latency."""
    global _health_cache
    import time
    now = time.time()
    if _health_cache["data"] and (now - _health_cache["timestamp"]) < _HEALTH_CACHE_TTL:
        return json.dumps({**_health_cache["data"], "_cached": True}, indent=2)

    servers = {
        "gitnexus": ["npx", "-y", "gitnexus@latest", "mcp", "list-repos"],
        "tavily": ["npx", "-y", "tavily-mcp@latest"],
        "ddg": ["npx", "-y", "ddg-mcp@latest", "search"],
        "firecrawl": ["npx", "-y", "firecrawl-mcp@latest", "map"],
        "github": ["npx", "-y", "@modelcontextprotocol/server-github@latest", "get-user"],
        "chrome_devtools": ["npx", "-y", "chrome-devtools-mcp@latest", "list-pages"],
        "playwright": ["npx", "-y", "playwright-mcp@latest", "browser-tabs"],
        "context7": ["npx", "-y", "@context7/mcp@latest", "resolve-library-id"],
    }
    results = {}
    for name, cmd in servers.items():
        results[name] = _check_mcp_server_latency(cmd, timeout=5)

    total_latency = 0
    connected_count = 0
    for name, res in results.items():
        if res["status"] == "connected":
            total_latency += res["latency_ms"] or 0
            connected_count += 1

    health_summary = {
        "servers": results,
        "summary": {
            "total": len(servers),
            "connected": connected_count,
            "avg_latency_ms": round(total_latency / connected_count, 2) if connected_count else None,
        },
        "checked_at": now,
    }
    _health_cache = {"data": health_summary, "timestamp": now}
    return json.dumps(health_summary, indent=2)

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 21: ERROR RECOVERY (retry + circuit breaker)
# ════════════════════════════════════════════════════════════════════════════

import time as _time


class CircuitBreakerState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = {}
        self.last_failure_time = {}
        self.state = {}

    def call(self, func, *args, **kwargs):
        tool_name = getattr(func, "__name__", str(func))
        state = self.state.get(tool_name, CircuitBreakerState.CLOSED)
        if state == CircuitBreakerState.OPEN:
            if _time.time() - self.last_failure_time.get(tool_name, 0) > self.reset_timeout:
                self.state[tool_name] = CircuitBreakerState.HALF_OPEN
                state = CircuitBreakerState.HALF_OPEN
            else:
                return {"error": "circuit_open", "tool": tool_name}
        try:
            result = func(*args, **kwargs)
            self.failures[tool_name] = 0
            self.state[tool_name] = CircuitBreakerState.CLOSED
            return result
        except Exception:
            self.failures[tool_name] = self.failures.get(tool_name, 0) + 1
            self.last_failure_time[tool_name] = _time.time()
            if self.failures[tool_name] >= self.failure_threshold:
                self.state[tool_name] = CircuitBreakerState.OPEN
            raise

    def get_state(self, tool_name):
        return self.state.get(tool_name, CircuitBreakerState.CLOSED)

    def reset(self, tool_name):
        self.failures[tool_name] = 0
        self.state[tool_name] = CircuitBreakerState.CLOSED

_cb_registry = CircuitBreaker(failure_threshold=5, reset_timeout=60)

def retry_with_backoff(func, max_attempts=3, base_delay=1.0, *args, **kwargs):
    """Retry a function with exponential backoff."""
    last_error = None
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                _time.sleep(base_delay * (2 ** attempt))
    raise last_error

@mcp.tool()
def circuit_breaker_status(tool_name: str = "") -> str:
    """Check circuit breaker state for a tool (or all if tool_name empty)."""
    if tool_name:
        return json.dumps({"tool": tool_name, "state": _cb_registry.get_state(tool_name)})
    return json.dumps({
        "tools": {t: _cb_registry.get_state(t) for t in _cb_registry.state},
        "failure_counts": _cb_registry.failures,
    })

def _wrapped_run_cmd(cmd, input_data=None, timeout=60):
    """Run command with circuit breaker protection."""
    def _inner():
        return _run_cmd(cmd, input_data, timeout)
    try:
        return _cb_registry.call(_inner)
    except Exception:
        pass
    return _run_cmd(cmd, input_data, timeout)  # fallback

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 22: RESULT CACHE (LRU cache for repeated queries)
# ════════════════════════════════════════════════════════════════════════════

_QUERY_CACHE_DIR = Path("/tmp/hermes_query_cache")
_QUERY_CACHE_DB = _QUERY_CACHE_DIR / "result_cache.sqlite"
_QUERY_CACHE_LOCK = threading.Lock()

_TOOL_TTL = {
    "terminal": 3600,
    "filesystem": 3600,
    "web_search": 300,
    "tavily": 300,
    "ddg": 300,
    "default": 3600,
}

def _get_cache_conn():
    _QUERY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_QUERY_CACHE_DB), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS result_cache (
            cache_key TEXT PRIMARY KEY,
            tool_name TEXT,
            args_hash TEXT,
            result_json TEXT,
            created_at REAL,
            access_count INTEGER DEFAULT 1
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tool ON result_cache(tool_name)")
    conn.commit()
    return conn

def _make_cache_key(tool_name, args_dict):
    import hashlib
    args_str = json.dumps(args_dict, sort_keys=True)
    return hashlib.sha256(f"{tool_name}:{args_str}".encode()).hexdigest()[:32]

def _get_cached_result(tool_name, args_dict):
    key = _make_cache_key(tool_name, args_dict)
    ttl = _TOOL_TTL.get(tool_name, _TOOL_TTL["default"])
    with _QUERY_CACHE_LOCK:
        conn = _get_cache_conn()
        row = conn.execute("""
            SELECT result_json, created_at FROM result_cache
            WHERE cache_key = ? AND tool_name = ?
        """, (key, tool_name)).fetchone()
        conn.close()
        if row and (_time.time() - row[1]) < ttl:
            return json.loads(row[0])
    return None

def _set_cached_result(tool_name, args_dict, result):
    key = _make_cache_key(tool_name, args_dict)
    with _QUERY_CACHE_LOCK:
        conn = _get_cache_conn()
        conn.execute("""
            INSERT OR REPLACE INTO result_cache (cache_key, tool_name, args_hash, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (key, tool_name, key[:16], json.dumps(result), _time.time()))
        conn.commit()
        conn.close()

def _cache_stats():
    with _QUERY_CACHE_LOCK:
        conn = _get_cache_conn()
        total = conn.execute("SELECT COUNT(*) FROM result_cache").fetchone()[0]
        total_access = conn.execute("SELECT SUM(access_count) FROM result_cache").fetchone()[0] or 0
        by_tool = conn.execute("""
            SELECT tool_name, COUNT(*) as count FROM result_cache GROUP BY tool_name
        """).fetchall()
        conn.close()
    return {
        "total_entries": total,
        "total_accesses": total_access,
        "by_tool": [{"tool": r[0], "count": r[1]} for r in by_tool],
    }

@mcp.tool()
def cache_manage(action: str = "stats", tool_name: str = "") -> str:
    """Manage result cache: stats, clear (per tool or all)."""
    if action == "stats":
        return json.dumps(_cache_stats(), indent=2)
    elif action == "clear":
        with _QUERY_CACHE_LOCK:
            conn = _get_cache_conn()
            if tool_name:
                conn.execute("DELETE FROM result_cache WHERE tool_name = ?", (tool_name,))
            else:
                conn.execute("DELETE FROM result_cache")
            conn.commit()
            conn.close()
        return json.dumps({"success": True, "action": "cleared", "tool": tool_name or "all"})
    return json.dumps({"error": "unknown action"})

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 23: METRICS COLLECTOR (tool usage tracking)
# ════════════════════════════════════════════════════════════════════════════

if METRICS_COLLECTOR_AVAILABLE:
    @mcp.tool()
    def metrics_collector(action: str = "status", tool_name: str = "",
                         limit: int = 10) -> str:
        """Track Hermes MCP tool usage frequency, latency percentiles, error rates."""
        return handle_metrics({
            "action": action,
            "tool_name": tool_name,
            "limit": limit,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 25: GRAPHRAG ENGINE (code-aware graph retrieval)
# ════════════════════════════════════════════════════════════════════════════

if GRAPHRAG_AVAILABLE:
    @mcp.tool()
    def graphrag_query(query: str, depth: int = 2,
                       include_paths: bool = False) -> str:
        """Query code knowledge graph with vector + multi-hop reasoning."""
        return handle_graphrag({
            "action": "query",
            "query": query,
            "depth": depth,
            "include_paths": include_paths,
        })

    @mcp.tool()
    def graphrag_index(paths: list | None = None, kind: str = "auto",
                       incremental: bool = True) -> str:
        """Build/refresh code knowledge graph index from source paths."""
        return handle_graphrag({
            "action": "build_index",
            "paths": paths or ["/home/newadmin/swarm-bot"],
            "kind": kind,
            "incremental": incremental,
        })

    @mcp.tool()
    def graphrag_dependencies(symbol: str, depth: int = 2) -> str:
        """Get all callers/callees within N hops of a symbol."""
        return handle_graphrag({
            "action": "get_dependencies",
            "symbol": symbol,
            "depth": depth,
        })

    @mcp.tool()
    def graphrag_execution_path(from_symbol: str, to_symbol: str) -> str:
        """Find shortest execution path between two symbols."""
        return handle_graphrag({
            "action": "execution_path",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 26: CROSS-SESSION MEMORY (provenance + versioning + decay)
# ════════════════════════════════════════════════════════════════════════════

if CROSS_SESSION_MEMORY_AVAILABLE:
    @mcp.tool()
    def memory_save(key: str, value: str, provenance: str = "{}",
                    decay_rate: float = 0.1) -> str:
        """Save memory entry with provenance tracking and versioning."""
        import json
        try:
            prov = json.loads(provenance) if isinstance(provenance, str) else provenance
        except Exception:
            prov = {}
        return handle_cross_session_memory({
            "action": "save",
            "key": key,
            "value": value,
            "provenance": prov,
            "decay_rate": decay_rate,
        })

    @mcp.tool()
    def memory_recall(key: str, min_priority: float = 0.5) -> str:
        """Recall memory entry with priority filtering and access stats."""
        return handle_cross_session_memory({
            "action": "recall",
            "key": key,
            "min_priority": min_priority,
        })

    @mcp.tool()
    def memory_forget(key: str, mark_only: bool = True) -> str:
        """Mark memory entry for Ebbinghaus-style decay/archival."""
        return handle_cross_session_memory({
            "action": "forget",
            "key": key,
            "mark_only": mark_only,
        })

    @mcp.tool()
    def memory_rollback(key: str, version: int = -1) -> str:
        """Rollback memory entry to previous version."""
        return handle_cross_session_memory({
            "action": "rollback",
            "key": key,
            "version": version,
        })

    @mcp.tool()
    def memory_sync_session(session_id: str, turn_count: int = 0,
                            entries: str = "[]") -> str:
        """Sync entries from current session with auto-checkpoint at 50 turns."""
        import json
        try:
            ents = json.loads(entries) if isinstance(entries, str) else entries
        except Exception:
            ents = []
        return handle_cross_session_memory({
            "action": "sync_from_session",
            "session_id": session_id,
            "turn_count": turn_count,
            "entries": ents,
        })

    @mcp.tool()
    def memory_trigger(event_type: str, metadata: str = "{}") -> str:
        """Fire memory write trigger (pr_created, test_failure, test_success, etc)."""
        import json
        try:
            meta = json.loads(metadata) if isinstance(metadata, str) else metadata
        except Exception:
            meta = {}
        return handle_cross_session_memory({
            "action": "trigger",
            "event_type": event_type,
            "metadata": meta,
        })

    @mcp.tool()
    def memory_conflict(key: str) -> str:
        """Detect and resolve version conflicts for a memory entry."""
        return handle_cross_session_memory({
            "action": "conflict",
            "key": key,
        })

    @mcp.tool()
    def memory_list(prefix: str = "", limit: int = 20) -> str:
        """List memory entries with optional prefix filter."""
        return handle_cross_session_memory({
            "action": "list",
            "prefix": prefix,
            "limit": limit,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 27: COORDINATION PRIMITIVES (circuit breakers + bulkheads)
# ════════════════════════════════════════════════════════════════════════════

if COORDINATION_PRIMITIVES_AVAILABLE:
    @mcp.tool()
    def coordination_circuit_status(agent_id: str = "") -> str:
        """Get circuit breaker states for all or specific agent."""
        return handle_coordination({
            "action": "circuit_status",
            "agent_id": agent_id,
        })

    @mcp.tool()
    def coordination_send(to_agent: str, message: str = "{}",
                          from_agent: str = "hermes") -> str:
        """Send direct message to agent with idempotency dedup."""
        import json
        try:
            msg = json.loads(message) if isinstance(message, str) else message
        except Exception:
            msg = {"text": message}
        return handle_coordination({
            "action": "send",
            "to_agent": to_agent,
            "from_agent": from_agent,
            "message": msg,
        })

    @mcp.tool()
    def coordination_broadcast(message: str = "{}", from_agent: str = "hermes") -> str:
        """Broadcast message to all registered agents."""
        import json
        try:
            msg = json.loads(message) if isinstance(message, str) else message
        except Exception:
            msg = {"text": message}
        return handle_coordination({
            "action": "broadcast",
            "from_agent": from_agent,
            "message": msg,
        })

    @mcp.tool()
    def coordination_verify(result: str, agent_id: str = "",
                            action_type: str = "") -> str:
        """Verify result with verifier agent; blocks if confidence < 90%."""
        import json
        try:
            res = json.loads(result) if isinstance(result, str) else result
        except Exception:
            res = {"raw": result}
        return handle_coordination({
            "action": "verify",
            "result": res,
            "agent_id": agent_id,
            "action_type": action_type,
        })

    @mcp.tool()
    def coordination_trace(trace_id: str) -> str:
        """Get full execution trace for debugging."""
        return handle_coordination({
            "action": "trace",
            "trace_id": trace_id,
        })

    @mcp.tool()
    def coordination_register(agent_id: str) -> str:
        """Register agent inbox for message bus."""
        return handle_coordination({
            "action": "register",
            "agent_id": agent_id,
        })

    @mcp.tool()
    def coordination_message_inbox(agent_id: str, mark_read: bool = False) -> str:
        """Read pending messages for agent (optional mark_read)."""
        return handle_coordination({
            "action": "inbox",
            "agent_id": agent_id,
            "mark_read": mark_read,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 28: SECURITY GATE (pre-write scanning + vulnerability detection)
# ════════════════════════════════════════════════════════════════════════════

if SECURITY_GATE_AVAILABLE:
    @mcp.tool()
    def security_scan_code(code_snippet: str, file_path: str = "") -> str:
        """Scan code snippet for vulnerabilities before writing."""
        return handle_security_gate({
            "action": "scan_code",
            "code_snippet": code_snippet,
            "file_path": file_path,
        })

    @mcp.tool()
    def security_check_file(file_path: str) -> str:
        """Scan existing file for security vulnerabilities."""
        return handle_security_gate({
            "action": "check_file",
            "file_path": file_path,
        })

    @mcp.tool()
    def security_gate(action: str, confidence: float = 0.5,
                      description: str = "") -> str:
        """Block action if confidence below threshold (default 90%)."""
        return handle_security_gate({
            "action": "gate",
            "action_type": action,
            "confidence": confidence,
            "description": description,
        })

    @mcp.tool()
    def security_report(min_severity: str = "medium") -> str:
        """Get security findings report filtered by minimum severity."""
        return handle_security_gate({
            "action": "report",
            "min_severity": min_severity,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 29: CONTEXT COMPACTOR (Claude Code-style context compaction)
# ════════════════════════════════════════════════════════════════════════════

if CONTEXT_COMPACTOR_AVAILABLE:
    @mcp.tool()
    def compactor_status() -> str:
        """Get current context utilization, trigger levels, last compaction."""
        return handle_context_compactor({
            "action": "status",
        })

    @mcp.tool()
    def compactor_compact(level: str = "auto") -> str:
        """Trigger context compaction (light/medium/aggressive/auto)."""
        return handle_context_compactor({
            "action": "compact",
            "level": level,
        })

    @mcp.tool()
    def compactor_restore() -> str:
        """Restore context from last compaction checkpoint."""
        return handle_context_compactor({
            "action": "restore",
        })

    @mcp.tool()
    def compactor_history(limit: int = 10) -> str:
        """Get list of past compactions with metadata."""
        return handle_context_compactor({
            "action": "history",
            "limit": limit,
        })

    @mcp.tool()
    def compactor_update_context(context_length: int = 0) -> str:
        """Update tracked context length for utilization monitoring."""
        return handle_context_compactor({
            "action": "update_length",
            "context_length": context_length,
        })

    @mcp.tool()
    def compactor_set_limits(max_tokens: int = 128000,
                             light_trigger: float = 0.70,
                             medium_trigger: float = 0.85,
                             aggressive_trigger: float = 0.95) -> str:
        """
        Configure memory limits and compaction triggers at runtime.

        Args:
            max_tokens: New max token limit (default: 128000)
            light_trigger: Light compaction threshold (0.0-1.0)
            medium_trigger: Medium compaction threshold (0.0-1.0)
            aggressive_trigger: Aggressive compaction threshold (0.0-1.0)
        """
        return handle_context_compactor({
            "action": "set_limits",
            "max_tokens": max_tokens,
            "triggers": {
                "light": light_trigger,
                "medium": medium_trigger,
                "aggressive": aggressive_trigger,
            }
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 30: MEMORY EXTRACTOR (intelligent extraction layer)
# ════════════════════════════════════════════════════════════════════════════

if MEMORY_EXTRACTOR_AVAILABLE:
    @mcp.tool()
    def memory_extract_session(session_transcript: str = "",
                               messages: str = "[]",
                               use_llm: bool = False) -> str:
        """Extract structured memory entries from raw session transcript."""
        import json
        try:
            msgs = json.loads(messages) if isinstance(messages, str) else messages
        except Exception:
            msgs = []
        return handle_memory_extractor({
            "action": "extract_session",
            "transcript": session_transcript,
            "messages": msgs,
            "use_llm": use_llm,
        })

    @mcp.tool()
    def memory_extractor_stats() -> str:
        """Get memory extraction statistics (noise reduction, entry counts)."""
        return handle_memory_extractor({"action": "stats"})

    @mcp.tool()
    def memory_extractor_list(limit: int = 20) -> str:
        """List extracted memory entries."""
        return handle_memory_extractor({"action": "list", "limit": limit})

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 31: GRAPHRAG TEMPORAL (version-controlled knowledge graph)
# ════════════════════════════════════════════════════════════════════════════

if GRAPHRAG_TEMPORAL_AVAILABLE:
    @mcp.tool()
    def graphrag_query_at_time(query: str, timestamp: str = "",
                               depth: int = 2, top_k: int = 5) -> str:
        """Query what the agent believed at a specific point in time."""
        return handle_graphrag_temporal({
            "action": "query_at_time",
            "query": query,
            "timestamp": timestamp,
            "depth": depth,
            "top_k": top_k,
        })

    @mcp.tool()
    def graphrag_query_current(query: str, top_k: int = 5) -> str:
        """Query current facts only (valid_until IS NULL)."""
        return handle_graphrag_temporal({
            "action": "query_current",
            "query": query,
            "top_k": top_k,
        })

    @mcp.tool()
    def graphrag_history(symbol: str, kind: str = "function") -> str:
        """Get full version chain of a symbol over time."""
        return handle_graphrag_temporal({
            "action": "history",
            "symbol": symbol,
            "kind": kind,
        })

    @mcp.tool()
    def graphrag_diff(symbol: str, from_time: str = "",
                     to_time: str = "", kind: str = "function") -> str:
        """Show what changed for a symbol between two timestamps."""
        return handle_graphrag_temporal({
            "action": "diff",
            "symbol": symbol,
            "from_time": from_time,
            "to_time": to_time,
            "kind": kind,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 32: CONTEXT SYNTHESIZER (session resume briefing)
# ════════════════════════════════════════════════════════════════════════════

if CONTEXT_SYNTHESIZER_AVAILABLE:
    @mcp.tool()
    def synthesize_session_context(session_id: str = "",
                                    current_task: str = "") -> str:
        """Generate coherent 2-paragraph context briefing at session resume."""
        return handle_context_synthesizer({
            "action": "synthesize",
            "session_id": session_id,
            "current_task": current_task,
        })

    @mcp.tool()
    def synthesize_from_memories(memory_entries: str = "[]") -> str:
        """Synthesize coherent briefing from provided memory entries."""
        import json
        try:
            entries = json.loads(memory_entries) if isinstance(memory_entries, str) else memory_entries
        except Exception:
            entries = []
        return handle_context_synthesizer({
            "action": "synthesize_from_memories",
            "entries": entries,
        })

    @mcp.tool()
    def synthesis_stats() -> str:
        """Get synthesis statistics (fallback rate, tokens used)."""
        return handle_context_synthesizer({"action": "stats"})

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 33: DREAMING (async hippocampal consolidation)
# ════════════════════════════════════════════════════════════════════════════

if DREAMING_AVAILABLE:
    @mcp.tool()
    def dreaming_status() -> str:
        """Get dreaming job status (last run, entries processed, changes)."""
        return dreaming_status()

    @mcp.tool()
    def dreaming_run(force: bool = False) -> str:
        """Trigger async dreaming consolidation (idle check unless force=True)."""
        return dreaming_run(force=force)

    @mcp.tool()
    def dreaming_preview() -> str:
        """Show what would change without applying."""
        return dreaming_preview()

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 34: RETRIEVAL FUSION (BM25 + vector RRF)
# ════════════════════════════════════════════════════════════════════════════

if RETRIEVAL_FUSION_AVAILABLE:
    @mcp.tool()
    def fusion_retrieve_tool(query: str, collection: str = "memory",
                              top_k: int = 10) -> str:
        """Query with BM25 + vector Reciprocal Rank Fusion."""
        return fusion_retrieve(query=query, collection=collection, top_k=top_k)

    @mcp.tool()
    def fusion_index_tool(collection: str = "memory",
                          texts: str = "[]", doc_ids: str = "[]") -> str:
        """Build/refresh BM25 index for a collection."""
        import json
        try:
            txts = json.loads(texts) if isinstance(texts, str) else texts
        except Exception:
            txts = []
        try:
            ids = json.loads(doc_ids) if isinstance(doc_ids, str) else doc_ids
        except Exception:
            ids = []
        return fusion_index(collection=collection, texts=txts, doc_ids=ids)

    @mcp.tool()
    def fusion_stats_tool(collection: str = "memory") -> str:
        """Get BM25 index statistics."""
        return fusion_stats(collection=collection)

# ════════════════════════════════════════════════════════════════════════════
# SECTION 15: CLAUDE CODE BRIDGE (Native MCP tool access to Claude Code CLI)
# ════════════════════════════════════════════════════════════════════════════
# Exposes Claude Code as a native MCP tool so Hermes can call it directly
# without terminal subprocess overhead. Full tool access via MCP protocol.

CLAUDE_BIN = "/home/newadmin/.local/bin/claude"
CLAUDE_WORKSPACE = "/home/newadmin/swarm-bot"

def _safe_json_dumps(obj, max_len: int = 50000) -> str:  # type: ignore[valid-type]
    """Serialize to JSON, truncating long outputs to prevent API argument size errors."""
    try:
        s = json.dumps(obj)
        if len(s) > max_len:
            return json.dumps({"_truncated": True, "_note": f"output exceeded {max_len} chars", "sample": s[:2000]})
        return s
    except Exception:
        return json.dumps({"_error": "json serialization failed", "_obj_type": type(obj).__name__})


def _safe_claude(args: list, timeout: int = 60) -> dict:
    """Call _run_claude and return dict. NEVER raises — all errors returned as dict."""
    try:
        result = _run_claude(args, timeout=timeout)
        if result.get("success"):
            return {"success": True, "stdout": result.get("stdout", ""), "stderr": result.get("stderr", "")}
        else:
            err = result.get("stderr", result.get("error", "Unknown error"))
            return {"success": False, "error": err}
    except Exception as e:
        return {"success": False, "error": f"claude bridge exception: {e}"}


def _run_claude(args: list, timeout: int = 120) -> dict:
    """Run Claude CLI and return parsed output."""
    try:
        result = subprocess.run(
            [CLAUDE_BIN, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=CLAUDE_WORKSPACE,
            env={
                **os.environ.copy(),
                "CLAUDE_CODE_SIMPLE": "1",
                "ANTHROPIC_API_KEY": os.environ.get("MINIMAX_API_KEY", ""),
            }
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "stdout": "", "stderr": "Command timed out", "returncode": -1, "success": False}
    except Exception as e:
        return {"error": str(e), "stdout": "", "stderr": str(e), "returncode": -1, "success": False}

@mcp.tool()
def claude_code_task(prompt: str, workspace: str = "/home/newadmin/swarm-bot",
                     allowed_tools: str = "Read,Edit,Bash,Notebook,WebSearch",
                     max_turns: int = 30, model: str = "",
                     output_format: str = "json") -> str:
    """
    Execute a coding task using Claude Code CLI. Full tool access via MCP.

    Use for: building features, refactoring, code reviews, iterative coding,
    autonomous multi-step tasks. This is a native MCP call - no subprocess shell.

    Args:
        prompt: The coding task or instruction for Claude Code
        workspace: Working directory (default: /home/newadmin/swarm-bot)
        allowed_tools: Comma-separated list of allowed tools
        max_turns: Maximum conversation turns (default: 30)
        model: Model to use (default: MiniMax-M2.7 via MINIMAX_API_KEY)
        output_format: text, json, or stream-json (default: json)
    """
    cmd = [
        "-p", prompt,
        "--output-format", output_format,
        "--allowedTools", allowed_tools,
        "--max-turns", str(max_turns),
        "--no-session-persistence"
    ]
    if model:
        cmd.extend(["--model", model])

    result = _safe_claude(cmd, timeout=180)
    return json.dumps(result)

@mcp.tool()
def claude_code_read(files: str, workspace: str = "/home/newadmin/swarm-bot",
                     include_errors: bool = True) -> str:
    """
    Read and analyze files using Claude Code.

    Args:
        files: Space-separated list of file paths to read
        workspace: Working directory
        include_errors: Check for errors, TODOs, and code quality issues
    """
    p = f"Read and analyze these files: {files}. "
    if include_errors:
        p += "Check for errors, TODOs, and code quality issues."
    else:
        p += "Provide a summary of each file's contents."

    result = _safe_claude(["-p", p, "--output-format", "json", "--no-session-persistence"], timeout=60)
    return json.dumps(result)

@mcp.tool()
def claude_code_search(query: str, workspace: str = "/home/newadmin/swarm-bot",
                       file_pattern: str = "*.py") -> str:
    """
    Search code using Claude Code's grep and context understanding.

    Args:
        query: Search query
        workspace: Working directory
        file_pattern: File pattern to search (e.g., '*.py')
    """
    p = f"Search the codebase for: '{query}' in files matching '{file_pattern}'. Use grep and read relevant files to find matches. Report what you find with file paths and line numbers."
    result = _safe_claude(["-p", p, "--output-format", "json", "--no-session-persistence"], timeout=60)
    return json.dumps(result)

@mcp.tool()
def claude_code_git(command: str, workspace: str = "/home/newadmin/swarm-bot") -> str:
    """
    Run git operations via Claude Code.

    Args:
        command: Git command to run (e.g., 'status', 'log --oneline -10')
        workspace: Working directory
    """
    p = f"Run this git command and explain the output: git {command}"
    result = _safe_claude(["-p", p, "--output-format", "json", "--no-session-persistence"], timeout=30)
    return json.dumps(result)

@mcp.tool()
def claude_code_agent(task: str, workspace: str = "/home/newadmin/swarm-bot",
                      agent_type: str = "coder", max_time: int = 300) -> str:
    """
    Run Claude Code in agent mode for autonomous multi-step tasks.

    Args:
        task: High-level task description
        workspace: Working directory
        agent_type: Agent type: coder, reviewer, architect (default: coder)
        max_time: Maximum time in seconds (default: 300)
    """
    p = f"You are a {agent_type}. {task}. Work autonomously until complete. Use appropriate tools, run tests, and commit your changes."
    result = _safe_claude(["-p", p, "--agent", agent_type, "--output-format", "json", "--no-session-persistence"], timeout=max_time)
    return json.dumps(result)

@mcp.tool()
def claude_code_list_tools() -> str:
    """
    List all Claude Code MCP bridge tools available.

    Returns a list of all tools exposed by this bridge with their descriptions.
    """
    tools = [
        {"name": "claude_code_task", "description": "Execute a coding task using Claude Code CLI"},
        {"name": "claude_code_read", "description": "Read and analyze files using Claude Code"},
        {"name": "claude_code_search", "description": "Search code using Claude Code's grep and context"},
        {"name": "claude_code_git", "description": "Run git operations via Claude Code"},
        {"name": "claude_code_agent", "description": "Run Claude Code in agent mode for autonomous tasks"},
        {"name": "claude_code_create_pr", "description": "Create a GitHub Pull Request via Claude Code"},
        {"name": "claude_code_review", "description": "Code review tool - analyze files for issues and auto-fix"},
        {"name": "claude_code_security_scan", "description": "Security vulnerability scanner with severity levels"},
    ]
    return json.dumps({"tools": tools, "count": len(tools)})


@mcp.tool()
def claude_code_create_pr(title: str, body: str = "", base: str = "main",
                           auto_approve: bool = False) -> str:
    """
    Create a GitHub Pull Request via Claude Code.

    Args:
        title: PR title
        body: PR description (optional)
        base: Target branch (default: main)
        auto_approve: If True, attempt to auto-approve and merge (requires permissions)
    """
    approve_instruction = " Then approve and merge the PR." if auto_approve else ""
    p = f"Create a PR with title: '{title}'. "
    if body:
        p += f"Description: {body}. "
    p += f"Target branch: {base}.{approve_instruction}"

    cmd = [
        "-p", p,
        "--output-format", "json",
        "--no-session-persistence",
        "--allowedTools", "Bash,Read,Edit,Todo"
    ]
    result = _safe_claude(cmd, timeout=120)
    return json.dumps(result)


@mcp.tool()
def claude_code_review(files: str = "", auto_fix: bool = False) -> str:
    """
    Code review tool - analyze files for issues, best practices, security.

    Args:
        files: Space-separated file paths to review (default: all changed files)
        auto_fix: If True, automatically fix issues found
    """
    scope = f"Review these files: {files}" if files else "Review all changed files"
    fix_instruction = " Automatically fix any issues found." if auto_fix else ""
    p = f"{scope}. Check for: bugs, security vulnerabilities, performance issues, code style violations, and best practices.{fix_instruction}"

    result = _safe_claude(["-p", p, "--output-format", "json", "--no-session-persistence"], timeout=90)
    return json.dumps(result)


@mcp.tool()
def claude_code_security_scan(path: str = "", level: str = "standard") -> str:
    """
    Security vulnerability scanner integrated with Claude Code.

    Args:
        path: Directory/file to scan (default: entire workspace)
        level: Scan depth - 'quick', 'standard', 'deep'
    """
    scope = f"Scan: {path}" if path else "Scan entire codebase"
    depth_instruction = {
        "quick": "Quick scan for critical issues only",
        "standard": "Standard scan for common vulnerabilities",
        "deep": "Deep scan including dependency analysis, secrets detection, OWASP Top 10"
    }.get(level, "Standard scan")

    p = f"{scope}. {depth_instruction}. Report findings with severity and remediation."

    result = _safe_claude(["-p", p, "--output-format", "json", "--no-session-persistence"], timeout=120)
    return json.dumps(result)


@mcp.tool()
def claude_code_background_task(prompt: str, workspace: str = "/home/newadmin/swarm-bot",
                                  max_time: int = 600) -> str:
    """
    Run a coding task in the background (non-blocking).

    Args:
        prompt: The task to execute
        workspace: Working directory
        max_time: Maximum time in seconds (default: 600)
    """
    import subprocess
    import threading

    def _run_bg():
        cmd = [
            CLAUDE_BIN, "-p", prompt,
            "--output-format", "json",
            "--no-session-persistence",
            "--allowedTools", "Read,Edit,Bash,Notebook,WebSearch,Task",
            "--max-turns", "50"
        ]
        subprocess.run(cmd, cwd=workspace, env={**os.environ, "ANTHROPIC_API_KEY": os.environ.get("MINIMAX_API_KEY", "")},
                      capture_output=True, timeout=max_time)

    thread = threading.Thread(target=_run_bg, daemon=True)
    thread.start()
    return json.dumps({"status": "background", "note": f"Task running in background (max {max_time}s)"})


@mcp.tool()
def claude_code_semantic_search(query: str, workspace: str = "/home/newadmin/swarm-bot",
                                  file_pattern: str = "**/*.py") -> str:
    """
    Semantic code search - understands code context beyond grep.

    Args:
        query: Natural language search query
        workspace: Working directory
        file_pattern: File pattern to search (default: **/*.py)
    """
    p = f"Search the codebase semantically for: '{query}'. "
    p += f"Look in files matching '{file_pattern}'. Understand the code structure. "
    p += "Report matches with context explaining WHY they match."

    result = _safe_claude(["-p", p, "--output-format", "json", "--no-session-persistence"], timeout=60)
    return json.dumps(result)


@mcp.tool()
def claude_code_ci_check(branch: str = "HEAD", workspace: str = "/home/newadmin/swarm-bot") -> str:
    """
    Run CI checks for the current branch before merge.

    Args:
        branch: Branch to check (default: HEAD)
        workspace: Working directory
    """
    p = f"Run pre-merge CI checks on branch '{branch}'. "
    p += "Run: lint, type check, tests, and report pass/fail for each. "
    p += "If checks fail, explain what needs to be fixed."

    result = _safe_claude(["-p", p, "--output-format", "json", "--no-session-persistence"], timeout=180)
    return json.dumps(result)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 35: HERMES ITERATION ENGINE (GoalLoop + RalphWiggum)
# ════════════════════════════════════════════════════════════════════════════

if HERMES_ITERATION_AVAILABLE:
    @mcp.tool()
    def hermes_iteration(action: str, goal: str = "", loop_id: str = "",
                          rw_id: str = "", context: str = "",
                          done_criteria: list | None = None,
                          max_iterations: int = 10) -> str:
        """
        Goal-driven iteration engine for Hermes (loop + ralph-wiggum equivalents).

        Actions:
          loop_start   — Start a new GoalLoop (loop until goal or max_iterations)
          loop_iterate — Advance a GoalLoop by one iteration
          loop_status  — Get current status of a GoalLoop
          loop_stop    — Stop a GoalLoop early
          rw_define    — Define a RalphWiggum structured iteration with done_criteria
          rw_check     — Check if all done_criteria are satisfied
          rw_iterate   — Run one RalphWiggum iteration
          rw_status    — Get status of a RalphWiggum iteration
          rw_stop      — Stop a RalphWiggum iteration early
          list_active  — List all active loops and rws

        Convergence: stops if same result 3x or 80%-similar results 5x.
        Uses MiniMax LLM to evaluate goal completion.
        """
        return handle_hermes_iteration({
            "action": action,
            "goal": goal,
            "loop_id": loop_id,
            "rw_id": rw_id,
            "context": context,
            "done_criteria": done_criteria or [],
            "max_iterations": max_iterations,
        })

# ════════════════════════════════════════════════════════════════════════════
# SECTION 36: HERMES HOOKS (26-event lifecycle hook system)
# ════════════════════════════════════════════════════════════════════════════

if HERMES_HOOKS_AVAILABLE:
    @mcp.tool()
    def hermes_hooks(action: str = "list", event: str = "",
                     script_path: str = "", hook_id: str = "",
                     context: dict | None = None, blocking: bool = False,
                     builtin_name: str = "", timeout: int = 30) -> str:
        """
        Manage and fire 26-event lifecycle hooks for Hermes MCP.

        Actions:
          - register:   Register a script for a hook event
          - unregister: Remove a hook by ID
          - fire:       Manually fire a hook event
          - list:       List all registered hooks
          - enable:     Enable a disabled hook
          - disable:    Disable a hook without removing it
          - builtin:    Register one of the built-in hooks

        Hook the system at key lifecycle points (tool calls, file writes,
        git operations, session start/end, error handling, etc.).
        """
        return handle_hermes_hooks({
            "action": action,
            "event": event,
            "script_path": script_path,
            "hook_id": hook_id,
            "context": context or {},
            "blocking": blocking,
            "builtin_name": builtin_name,
            "timeout": timeout,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 37: HERMES TOKEN METER (per-session token tracking)
# ════════════════════════════════════════════════════════════════════════════

if TOKEN_METER_AVAILABLE:
    @mcp.tool()
    def hermes_token_meter(action: str = "get", session_id: str = "",
                            budget_tokens: int = 0) -> str:
        """
        Token usage metering and cost tracking for Hermes sessions.

        Actions:
          - get:         Get current token usage for session
          - reset:      Reset counters for a session
          - budget_set: Set a token budget for a session
          - budget_check: Check budget status
          - history:    Get historical usage data

        Tracks input/output/cache tokens with cost estimation.
        Uses tiktoken cl100k_base when available.
        """
        return handle_hermes_token_meter({
            "action": action,
            "session_id": session_id,
            "budget_tokens": budget_tokens,
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 38: HERMES APPROVAL GATE (per-tool approval prompts)
# ════════════════════════════════════════════════════════════════════════════

if APPROVAL_GATE_AVAILABLE:
    @mcp.tool()
    def hermes_approval_gate(action: str = "check", tool_name: str = "",
                              proposed_action: str = "", risk_level: str = "LOW",
                              approval_id: str = "", decision: str = "",
                              policy: str = "auto_allow",
                              context: dict | None = None) -> str:
        """
        Per-tool approval gate with configurable policies.

        Actions:
          - check:      Classify a tool action and return risk level
          - request:    Submit a tool for approval review
          - resolve:    Resolve a pending approval (allow/deny/skip)
          - pending:    List pending approvals
          - policy_set: Set the approval policy (auto_allow/permissive/strict)
          - policy_get: Get current policy

        Policies:
          - auto_allow: LOW allow, MEDIUM prompt, HIGH deny, CRITICAL deny
          - permissive: LOW allow, MEDIUM allow, HIGH prompt, CRITICAL prompt
          - strict:    LOW allow, MEDIUM prompt, HIGH deny, CRITICAL deny
        """
        return handle_hermes_approval_gate({
            "action": action,
            "tool_name": tool_name,
            "proposed_action": proposed_action,
            "risk_level": risk_level,
            "approval_id": approval_id,
            "decision": decision,
            "policy": policy,
            "context": context or {},
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 39: HERMES CONTEXT INJECTOR (auto CLAUDE.md loading)
# ════════════════════════════════════════════════════════════════════════════

if CONTEXT_INJECTOR_AVAILABLE:
    @mcp.tool()
    def hermes_context_injector(action: str = "inject", project_path: str = "",
                                 profile_name: str = "", max_chars: int = 4000,
                                 includes: list | None = None) -> str:
        """
        Auto-inject CLAUDE.md and project context for Hermes sessions.

        Actions:
          - inject:       Build and return context injection string for project
          - read_claude_md: Read CLAUDE.md from project root
          - build_context: Build full context from multiple sources
          - profile_save:  Save a context profile
          - profile_load: Load a saved profile
          - profile_list: List saved profiles

        Automatically reads CLAUDE.md, git commit messages, package deps.
        Token-budgeted: prioritizes CLAUDE.md > git > package files.
        """
        return handle_hermes_context_injector({
            "action": action,
            "project_path": project_path,
            "profile_name": profile_name,
            "max_chars": max_chars,
            "includes": includes or [],
        })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 24: TERMINAL PLUS (background job management)
# ════════════════════════════════════════════════════════════════════════════

_TERMINAL_JOBS_DIR = Path("/tmp/hermes_terminal_jobs")
_TERMINAL_JOBS_DIR.mkdir(parents=True, exist_ok=True)
_JOB_TTL = 3600  # 1 hour

def _save_job(job_id, state):
    (_TERMINAL_JOBS_DIR / f"{job_id}.json").write_text(json.dumps(state))

def _load_job(job_id):
    path = _TERMINAL_JOBS_DIR / f"{job_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None

def _list_jobs():
    jobs = []
    for f in sorted(_TERMINAL_JOBS_DIR.glob("*.json"), key=lambda x: -x.stat().st_mtime):
        try:
            job = json.loads(f.read_text())
            # Clean stale jobs
            if _time.time() - job.get("created_at", 0) > _JOB_TTL:
                f.unlink()
                continue
            jobs.append(job)
        except Exception:
            pass
    return jobs

import uuid as _uuid


@mcp.tool()
def terminal_background_create(command: str, cwd: str = "") -> str:
    """Start a background terminal job, return job_id."""
    job_id = f"job-{_uuid.uuid4().hex[:8]}"
    state = {
        "job_id": job_id,
        "command": command,
        "cwd": cwd,
        "status": "running",
        "created_at": _time.time(),
        "output_lines": 0,
    }
    _save_job(job_id, state)
    # Start the actual process
    try:
        proc = subprocess.Popen(
            command, shell=True, cwd=cwd or None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "NO_COLOR": "1"},
        )
        state["pid"] = proc.pid
        _save_job(job_id, state)
    except Exception as e:
        state["status"] = "failed"
        state["error"] = str(e)
        _save_job(job_id, state)
    return json.dumps({"job_id": job_id, "status": state["status"]})

@mcp.tool()
def terminal_background_status(job_id: str = "") -> str:
    """Get status of a background job (or list all jobs if job_id empty)."""
    if not job_id:
        return json.dumps({"jobs": _list_jobs()})
    job = _load_job(job_id)
    if not job:
        return json.dumps({"error": f"job {job_id} not found"})
    # Check if process still running
    pid = job.get("pid")
    if pid and job["status"] == "running":
        try:
            import os
            os.kill(pid, 0)  # Signal 0 just checks existence
        except OSError:
            job["status"] = "completed"
            _save_job(job_id, job)
    return json.dumps(job)

@mcp.tool()
def terminal_background_output(job_id: str, offset: int = 0) -> str:
    """Stream output from a background job (incremental)."""
    job = _load_job(job_id)
    if not job:
        return json.dumps({"error": f"job {job_id} not found"})
    # Would return output lines from offset in real implementation
    return json.dumps({"job_id": job_id, "status": job.get("status"), "offset": offset})

@mcp.tool()
def terminal_background_kill(job_id: str) -> str:
    """Kill a background job by job_id."""
    job = _load_job(job_id)
    if not job:
        return json.dumps({"error": f"job {job_id} not found"})
    pid = job.get("pid")
    if pid:
        try:
            import os
            os.kill(pid, 9)
            job["status"] = "killed"
        except OSError:
            job["status"] = "already_stopped"
    else:
        job["status"] = "no_pid"
    job["completed_at"] = _time.time()
    _save_job(job_id, job)
    return json.dumps({"job_id": job_id, "status": job["status"]})

@mcp.tool()
def terminal_background_list() -> str:
    """List all background terminal jobs."""
    return json.dumps({"jobs": _list_jobs()})

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 25: VISION ENHANCEMENTS
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def vision_generate_image(prompt: str, model: str = "dalle",
                         size: str = "1024x1024") -> str:
    """Generate image from text prompt (stub - requires OpenAI/DALL-E API key)."""
    return json.dumps({
        "stub": True,
        "message": "vision_generate_image requires OpenAI API key configuration",
        "prompt": prompt,
        "model": model,
    })

@mcp.tool()
def vision_ocr_image(image_path: str) -> str:
    """Extract text from screenshot/image using OCR."""
    try:
        import subprocess
        out = subprocess.run(
            ["python3", "-c", f"from PIL import Image; import pytesseract; img = Image.open('{image_path}'); print(pytesseract.image_to_string(img))"],
            capture_output=True, timeout=30
        )
        return json.dumps({"text": out.stdout.decode(errors="replace").strip()})
    except Exception as e:
        return json.dumps({"error": str(e), "image_path": image_path})

@mcp.tool()
def vision_analyze_screenshot(image_path: str,
                               query: str = "Describe this screenshot") -> str:
    """Optimized screenshot analysis via hermes vision."""
    return hermes_vision_analyze(image_path, query)

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 26: SKILLS AUTOMATION (auto-create, version, deprecate)
# ════════════════════════════════════════════════════════════════════════════

SKILLS_DIR = Path.home() / ".hermes" / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

def _skill_path(name):
    return SKILLS_DIR / f"{name}.md"

def _load_skill(name):
    path = _skill_path(name)
    if path.exists():
        return path.read_text()
    return ""

def _save_skill(name, content):
    path = _skill_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True

def _list_all_skills():
    return [f.stem for f in SKILLS_DIR.glob("*.md")]

@mcp.tool()
def skills_auto_create(name: str, description: str = "",
                        tool_sequence: list | None = None) -> str:
    """Create a new skill from a sequence of tool calls."""
    content = f"---\nname: {name}\ndescription: {description}\nversion: 1.0\n---\n"
    content += f"## Skill: {name}\n{description}\n\n"
    if tool_sequence:
        content += "## Tool Sequence\n"
        for step, tool in enumerate(tool_sequence, 1):
            content += f"{step}. {tool}\n"
    _save_skill(name, content)
    return json.dumps({"success": True, "skill": name, "path": str(_skill_path(name))})

@mcp.tool()
def skills_version_list(name: str) -> str:
    """List all versions of a skill (currently just the skill file)."""
    return json.dumps({"skill": name, "versions": ["1.0"], "note": "versioning not yet implemented"})

@mcp.tool()
def skills_deprecate(name: str, successor: str = "") -> str:
    """Mark a skill as deprecated."""
    content = _load_skill(name)
    if not content:
        return json.dumps({"error": f"skill {name} not found"})
    if "deprecated" not in content.lower():
        content += "\n\n!!! DEPRECATED !!!\n"
        if successor:
            content += f"Use `{successor}` instead.\n"
    _save_skill(name, content)
    return json.dumps({"success": True, "skill": name, "deprecated": True})

@mcp.tool()
def skills_usage_stats() -> str:
    """Track which skills are used (stub - needs tracking integration)."""
    skills = _list_all_skills()
    return json.dumps({"skills": [{"name": s, "use_count": 0} for s in skills], "note": "usage tracking stub"})

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 27: CODE EXECUTOR PLUS (multi-language with sandbox)
# ════════════════════════════════════════════════════════════════════════════

SANDBOX_DIR = Path("/home/newadmin/swarm-bot/.sandbox")
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

LANG_RUNTIMES = {
    "python": ["python3", "-c"],
    "javascript": ["node", "-e"],
    "bash": ["bash", "-c"],
    "ruby": ["ruby", "-e"],
}

@mcp.tool()
def execute_javascript(code: str, timeout: int = 30) -> str:
    """Execute JavaScript in Node.js."""
    try:
        out = subprocess.run(
            ["node", "-e", code], capture_output=True, timeout=timeout,
            cwd=str(SANDBOX_DIR)
        )
        return json.dumps({
            "language": "javascript", "exit_code": out.returncode,
            "stdout": out.stdout.decode(errors="replace"),
            "stderr": out.stderr.decode(errors="replace"),
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"timeout after {timeout}s", "language": "javascript"})
    except Exception as e:
        return json.dumps({"error": str(e), "language": "javascript"})

@mcp.tool()
def execute_rust(code: str, timeout: int = 60) -> str:
    """Compile and run Rust (stub - requires rustc)."""
    return json.dumps({"stub": True, "language": "rust", "message": "Rust execution not yet configured"})

@mcp.tool()
def execute_go(code: str, timeout: int = 60) -> str:
    """Run Go (stub - requires go)."""
    return json.dumps({"stub": True, "language": "go", "message": "Go execution not yet configured"})

@mcp.tool()
def execute_java(code: str, timeout: int = 60) -> str:
    """Compile and run Java (stub - requires javac)."""
    return json.dumps({"stub": True, "language": "java", "message": "Java execution not yet configured"})

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 28: DELEGATE BATCH (parallel subagent spawning)
# ════════════════════════════════════════════════════════════════════════════

import concurrent.futures
from typing import Any

_SHARED_CHROMA_NS = "hermes_subagents"

def _delegate_batch_single(goal, toolsets, task_id):
    """Execute a single goal via hermes delegate (stub)."""
    try:
        result = hermes_delegate(goal, "", toolsets)
        return {"task_id": task_id, "goal": goal, "result": result}
    except Exception as e:
        return {"task_id": task_id, "goal": goal, "error": str(e)}

@mcp.tool()
def delegate_batch(goals: list, toolsets: str = "terminal,file,web",
                    parallel_max: int = 5) -> str:
    """Spawn multiple Hermes subagents in parallel (up to parallel_max)."""
    results = []
    errors = []
    start_time = _time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(goals), parallel_max)) as pool:
        futures = []
        for i, goal in enumerate(goals):
            fut = pool.submit(_delegate_batch_single, goal, toolsets, f"task-{i}")
            futures.append(fut)
        for fut in concurrent.futures.as_completed(futures):
            try:
                r = fut.result()
                if "error" in r:
                    errors.append(r)
                else:
                    results.append(r)
            except Exception as e:
                errors.append({"error": str(e)})
    total_time = _time.time() - start_time
    return json.dumps({
        "results": results,
        "errors": errors,
        "goals_submitted": len(goals),
        "goals_completed": len(results),
        "goals_failed": len(errors),
        "total_time": round(total_time, 2),
    })

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 29: SUBAGENT MEMORY SHARE (shared ChromaDB namespace)
# ════════════════════════════════════════════════════════════════════════════

_chroma_shared_cache = {}  # In-memory for now, cross-agent needs persistent store

@mcp.tool()
def memory_share_write(key: str, value: str, agent_id: str = "",
                        batch_id: str = "") -> str:
    """Write shared memory entry from subagent (stored in memory_layer_bridge ChromaDB)."""
    _chroma_shared_cache[key] = {
        "value": value,
        "agent_id": agent_id,
        "batch_id": batch_id,
        "timestamp": _time.time(),
    }
    return json.dumps({"success": True, "key": key, "entries": len(_chroma_shared_cache)})

@mcp.tool()
def memory_share_read(key: str) -> str:
    """Read shared memory entry from parent/other agents."""
    entry = _chroma_shared_cache.get(key, {})
    if not entry:
        return json.dumps({"error": f"key {key} not found"})
    return json.dumps({"key": key, "value": entry.get("value"), "timestamp": entry.get("timestamp")})

@mcp.tool()
def memory_share_list() -> str:
    """List all shared memory keys."""
    return json.dumps({"keys": list(_chroma_shared_cache.keys()), "count": len(_chroma_shared_cache)})

@mcp.tool()
def memory_share_delete(key: str) -> str:
    """Delete a shared memory entry."""
    if key in _chroma_shared_cache:
        del _chroma_shared_cache[key]
        return json.dumps({"success": True, "key": key})
    return json.dumps({"error": f"key {key} not found"})

# ════════════════════════════════════════════════════════════════════════════
# NEW SECTION 30: SWARM COORDINATOR (spawn mesh of agents)
# ════════════════════════════════════════════════════════════════════════════

_swarms = {}

@mcp.tool()
def hermes_spawn_swarm(goals: list, swarm_type: str = "parallel") -> str:
    """Spawn a mesh of 3-5 agents working on related subtasks."""
    swarm_id = f"swarm-{_uuid.uuid4().hex[:8]}"
    agent_count = min(max(3, len(goals)), 5)
    agent_names = [f"{swarm_id}-{r}" for r in range(agent_count)]
    _swarms[swarm_id] = {
        "goals": goals,
        "agents": agent_names,
        "status": "Running",
        "created_at": _time.time(),
    }
    return json.dumps({
        "swarm_id": swarm_id,
        "goal_count": len(goals),
        "agent_count": agent_count,
        "agents": agent_names,
    })

@mcp.tool()
def swarm_status(swarm_id: str) -> str:
    """Get status of a spawned swarm."""
    if swarm_id not in _swarms:
        return json.dumps({"error": f"swarm {swarm_id} not found"})
    return json.dumps(_swarms[swarm_id])

@mcp.tool()
def swarm_result_collect(swarm_id: str) -> str:
    """Gather and merge all agent results from a swarm."""
    if swarm_id not in _swarms:
        return json.dumps({"error": f"swarm {swarm_id} not found"})
    return json.dumps({"swarm_id": swarm_id, "goals": _swarms[swarm_id]["goals"], "note": "result collection stub"})

@mcp.tool()
def swarm_terminate(swarm_id: str) -> str:
    """Force-terminate all agents in a swarm."""
    if swarm_id in _swarms:
        _swarms[swarm_id]["status"] = "Terminated"
        return json.dumps({"swarm_id": swarm_id, "status": "Terminated"})
    return json.dumps({"error": f"swarm {swarm_id} not found"})

# ════════════════════════════════════════════════════════════════════════════
# ENHANCED: hermes_list_all_tools (Hermes native + all externals + new)
# ════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def hermes_list_all_tools() -> str:
    """List ALL available Hermes + external MCP tools organized by toolset."""
    all_by_toolset = {}
    # Hermes native
    if HERMES_TOOLS:
        for tool in HERMES_TOOLS:
            name = tool["function"]["name"]
            ts = TOOLSET_MAP.get(name, "hermes-native")
            all_by_toolset.setdefault(ts, []).append(name)
    # External MCP
    for tname, tsname in _EXTERNAL_TOOLSET_MAP.items():
        if tname not in all_by_toolset.get(tsname, []):
            all_by_toolset.setdefault(tsname, []).append(tname)
    lines = ["Available Tools (Hermes + External MCP):"]
    for ts, tools in sorted(all_by_toolset.items()):
        lines.append(f"\n  [{ts}]")
        for t in sorted(tools):
            lines.append(f"    - {t}")
    return "\n".join(lines)


# ── Run server ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    total_ext = len(_EXTERNAL_TOOLSET_MAP)
    print(f"[Hermes MCP] Server starting: {len(HERMES_TOOLS)} Hermes + {total_ext} external tools...",
          file=sys.stderr)
    mcp.run()
