"""
lib/legiona/tools/registry.py
M2.7 native tool registry — defines every tool available to the tool-calling loop.
Each entry maps a tool name -> (function, JSON schema).
Schemas are OpenAI-compatible (tool_calls format).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from lib.legiona.tools import desktop_control as _deskctl
from lib.legiona.tools import fs_control as _fsctl
from lib.legiona.tools import log_reader as _logrd
from lib.legiona.tools import system_monitor as _sysmon
from lib.legiona.tools.mmx_tools import mmx_search, mmx_speech, mmx_vision

# ── Tool function signatures ─────────────────────────────────────────────────

def _supabase_query(query: str, table: str | None = None) -> str:
    """
    Query Supabase using the supabase-py client.
    Args:
        query: SQL query string or table name to SELECT from
        table: Optional explicit table name (falls back to parsing from query)
    """
    try:
        from supabase import Supabase, create_client
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if not url or not key:
            return "ERROR: SUPABASE_URL or SUPABASE_KEY not set"
        client: Supabase = create_client(url, key)
        if table:
            result = client.table(table).select("*").execute()
        else:
            result = client.table(query).select("*").limit(10).execute()
        return json.dumps(result.data, indent=2, default=str)
    except ImportError:
        return "ERROR: supabase-py not installed"
    except Exception as exc:
        return f"ERROR: {exc}"


def _rag_retrieve(query: str, top_k: int = 5) -> str:
    """
    Retrieve context from the local RAG knowledge base (BM25 + vector hybrid).
    Args:
        query: The search query string
        top_k: Number of results to return (default 5)
    """
    try:
        from lib.legiona.rag_retriever import retrieve_context
        results = retrieve_context(query, top_k=top_k)
        if not results:
            return "No RAG results found for query."
        return "\n\n---\n".join(results)
    except Exception as exc:
        return f"ERROR: RAG retrieval failed: {exc}"


def _shell_exec(command: str, timeout: int = 30) -> str:
    """
    Execute a shell command and return stdout/stderr.
    SECURITY: Only use for read-only or explicitly authorized commands.
    Args:
        command: The shell command to execute
        timeout: Max seconds before kill (default 30)
    """
    try:
        proc = asyncio.run(
            asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        )
        try:
            stdout, stderr = asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return f"ERROR: Command timed out after {timeout}s"
        result_parts = []
        if stdout:
            result_parts.append(stdout.decode())
        if stderr:
            result_parts.append(f"STDERR:\n{stderr.decode()}")
        return "\n".join(result_parts) or "(no output)"
    except Exception as exc:
        return f"ERROR: {exc}"


def _file_read(path: str) -> str:
    """
    Read and return the contents of a file.
    Args:
        path: Absolute or relative path to the file
    SECURITY: Only read files within the project directory.
    """
    try:
        file_path = Path(path).resolve()
        project_root = Path("/home/newadmin/swarm-bot").resolve()
        if not str(file_path).startswith(str(project_root)):
            return f"ERROR: Path '{path}' is outside the project directory."
        if not file_path.exists():
            return f"ERROR: File '{path}' does not exist."
        content = file_path.read_text(errors="replace")
        return content
    except Exception as exc:
        return f"ERROR: {exc}"


def _web_search(query: str) -> str:
    """
    PLACEHOLDER - web search not yet wired. USE RAG INSTEAD.
    For general web queries, integrate tavily-mcp or exa-mcp in .opencode/opencode.json.
    """
    return (
        "USE RAG INSTEAD OF WEB SEARCH for project-specific knowledge.\n"
        "For general web search, wire up tavily-mcp or exa-mcp in .opencode/opencode.json.\n"
        f"Query received: {query}"
    )


# ── System monitor wrappers ───────────────────────────────────────────────────

def _list_processes(sort_by: str = "cpu", top_n: int = 20, user: str | None = None) -> str:
    try:
        return asyncio.run(_sysmon.list_processes(sort_by=sort_by, top_n=top_n, user=user))
    except Exception as exc:
        return f"ERROR: {exc}"

def _kill_process(pid: int, signal: str = "TERM", confirm: bool = False) -> str:
    try:
        return asyncio.run(_sysmon.kill_process(pid=pid, signal=signal, confirm=confirm))
    except Exception as exc:
        return f"ERROR: {exc}"

def _process_tree(pid: int = 1) -> str:
    try:
        return asyncio.run(_sysmon.process_tree(pid=pid))
    except Exception as exc:
        return f"ERROR: {exc}"

def _system_stats() -> str:
    try:
        return asyncio.run(_sysmon.system_stats())
    except Exception as exc:
        return f"ERROR: {exc}"

def _cpu_usage_per_core() -> str:
    try:
        return asyncio.run(_sysmon.cpu_usage_per_core())
    except Exception as exc:
        return f"ERROR: {exc}"

def _memory_usage() -> str:
    try:
        return asyncio.run(_sysmon.memory_usage())
    except Exception as exc:
        return f"ERROR: {exc}"

def _running_services() -> str:
    try:
        return asyncio.run(_sysmon.running_services())
    except Exception as exc:
        return f"ERROR: {exc}"

def _service_status(service_name: str) -> str:
    try:
        return asyncio.run(_sysmon.service_status(service_name=service_name))
    except Exception as exc:
        return f"ERROR: {exc}"

def _failed_services() -> str:
    try:
        return asyncio.run(_sysmon.failed_services())
    except Exception as exc:
        return f"ERROR: {exc}"

def _network_connections() -> str:
    try:
        return asyncio.run(_sysmon.network_connections())
    except Exception as exc:
        return f"ERROR: {exc}"

def _listening_ports() -> str:
    try:
        return asyncio.run(_sysmon.listening_ports())
    except Exception as exc:
        return f"ERROR: {exc}"

def _who_is_logged_in() -> str:
    try:
        return asyncio.run(_sysmon.who_is_logged_in())
    except Exception as exc:
        return f"ERROR: {exc}"

def _network_stats() -> str:
    try:
        return asyncio.run(_sysmon.network_stats())
    except Exception as exc:
        return f"ERROR: {exc}"

def _disk_io() -> str:
    try:
        return asyncio.run(_sysmon.disk_io())
    except Exception as exc:
        return f"ERROR: {exc}"


# ── Filesystem control wrappers ────────────────────────────────────────────────

def _fs_read_file(path: str, offset: int = 0, limit: int = 500) -> str:
    try:
        return asyncio.run(_fsctl.read_file(path=path, offset=offset, limit=limit))
    except Exception as exc:
        return f"ERROR: {exc}"

def _fs_write_file(path: str, content: str, confirm: bool = False) -> str:
    try:
        return asyncio.run(_fsctl.write_file(path=path, content=content, confirm=confirm))
    except Exception as exc:
        return f"ERROR: {exc}"

def _fs_list_dir(path: str = ".", depth: int = 1) -> str:
    try:
        return asyncio.run(_fsctl.list_dir(path=path, depth=depth))
    except Exception as exc:
        return f"ERROR: {exc}"

def _fs_search_files(pattern: str, path: str = ".", filetype: str = "f") -> str:
    try:
        return asyncio.run(_fsctl.search_files(pattern=pattern, path=path, filetype=filetype))
    except Exception as exc:
        return f"ERROR: {exc}"

def _fs_grep_files(pattern: str, path: str = ".", context: int = 2) -> str:
    try:
        return asyncio.run(_fsctl.grep_files(pattern=pattern, path=path, context=context))
    except Exception as exc:
        return f"ERROR: {exc}"

def _fs_disk_usage(path: str = "/") -> str:
    try:
        return asyncio.run(_fsctl.disk_usage(path=path))
    except Exception as exc:
        return f"ERROR: {exc}"


# ── Log reader wrappers ───────────────────────────────────────────────────────

def _tail_log(log_name: str, num_lines: int = 50, pattern: str | None = None) -> str:
    try:
        return asyncio.run(_logrd.tail_log(log_name=log_name, num_lines=num_lines, pattern=pattern))
    except Exception as exc:
        return f"ERROR: {exc}"

def _grep_log(log_name: str, pattern: str, context: int = 3) -> str:
    try:
        return asyncio.run(_logrd.grep_log(log_name=log_name, pattern=pattern, context=context))
    except Exception as exc:
        return f"ERROR: {exc}"

def _count_log_entries(log_name: str, pattern: str) -> str:
    try:
        return asyncio.run(_logrd.count_log_entries(log_name=log_name, pattern=pattern))
    except Exception as exc:
        return f"ERROR: {exc}"

def _list_all_logs() -> str:
    try:
        return asyncio.run(_logrd.list_all_logs())
    except Exception as exc:
        return f"ERROR: {exc}"

def _watch_log_live(log_name: str, pattern: str | None = None, duration_seconds: int = 10) -> str:
    try:
        return asyncio.run(_logrd.watch_log_live(log_name=log_name, pattern=pattern, duration_seconds=duration_seconds))
    except Exception as exc:
        return f"ERROR: {exc}"

def _get_recent_errors(log_name: str, num_lines: int = 30) -> str:
    try:
        return asyncio.run(_logrd.get_recent_errors(log_name=log_name, num_lines=num_lines))
    except Exception as exc:
        return f"ERROR: {exc}"

def _follow_journal(unit: str, num_lines: int = 50) -> str:
    try:
        return asyncio.run(_logrd.follow_journal(unit=unit, num_lines=num_lines))
    except Exception as exc:
        return f"ERROR: {exc}"


# ── Desktop control wrappers ──────────────────────────────────────────────────

def _take_screenshot(output_path: str | None = None) -> str:
    try:
        return asyncio.run(_deskctl.take_screenshot(output_path=output_path))
    except Exception as exc:
        return f"ERROR: {exc}"

def _take_screenshot_base64() -> str:
    try:
        return asyncio.run(_deskctl.take_screenshot_base64())
    except Exception as exc:
        return f"ERROR: {exc}"

def _list_windows() -> str:
    try:
        return asyncio.run(_deskctl.list_windows())
    except Exception as exc:
        return f"ERROR: {exc}"

def _get_active_window() -> str:
    try:
        return asyncio.run(_deskctl.get_active_window())
    except Exception as exc:
        return f"ERROR: {exc}"

def _switch_window(window_id: str) -> str:
    try:
        return asyncio.run(_deskctl.switch_window(window_id=window_id))
    except Exception as exc:
        return f"ERROR: {exc}"

def _close_window(window_id: str) -> str:
    try:
        return asyncio.run(_deskctl.close_window(window_id=window_id))
    except Exception as exc:
        return f"ERROR: {exc}"

def _minimize_window(window_id: str) -> str:
    try:
        return asyncio.run(_deskctl.minimize_window(window_id=window_id))
    except Exception as exc:
        return f"ERROR: {exc}"

def _switch_tab_next() -> str:
    try:
        return asyncio.run(_deskctl.switch_tab_next())
    except Exception as exc:
        return f"ERROR: {exc}"

def _switch_tab_prev() -> str:
    try:
        return asyncio.run(_deskctl.switch_tab_prev())
    except Exception as exc:
        return f"ERROR: {exc}"

def _open_app(app_name: str) -> str:
    try:
        return asyncio.run(_deskctl.open_app(app_name=app_name))
    except Exception as exc:
        return f"ERROR: {exc}"

def _type_text(text: str) -> str:
    try:
        return asyncio.run(_deskctl.type_text(text=text))
    except Exception as exc:
        return f"ERROR: {exc}"

def _key_press(key_combo: str) -> str:
    try:
        return asyncio.run(_deskctl.key_press(key_combo=key_combo))
    except Exception as exc:
        return f"ERROR: {exc}"

def _mouse_click(x: int, y: int, button: str = "1") -> str:
    try:
        return asyncio.run(_deskctl.mouse_click(x=x, y=y, button=button))
    except Exception as exc:
        return f"ERROR: {exc}"

def _get_window_info() -> str:
    try:
        return asyncio.run(_deskctl.get_window_info())
    except Exception as exc:
        return f"ERROR: {exc}"

def _get_clipboard() -> str:
    try:
        return asyncio.run(_deskctl.get_clipboard())
    except Exception as exc:
        return f"ERROR: {exc}"

def _set_clipboard(text: str) -> str:
    try:
        return asyncio.run(_deskctl.set_clipboard(text=text))
    except Exception as exc:
        return f"ERROR: {exc}"

def _get_desktop_info() -> str:
    try:
        return asyncio.run(_deskctl.get_desktop_info())
    except Exception as exc:
        return f"ERROR: {exc}"

def _switch_desktop(desktop: str) -> str:
    try:
        return asyncio.run(_deskctl.switch_desktop(desktop=desktop))
    except Exception as exc:
        return f"ERROR: {exc}"

def _get_screen_resolution() -> str:
    try:
        return asyncio.run(_deskctl.get_screen_resolution())
    except Exception as exc:
        return f"ERROR: {exc}"


# ── Registry ─────────────────────────────────────────────────────────────────

LEGIONA_TOOLS: list[dict[str, Any]] = [
    {
        "name": "supabase_query",
        "description": "Query the Supabase PostgreSQL database. Use for structured data lookups.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL SELECT query or table name"},
                "table": {"type": "string", "description": "Optional explicit table name"},
            },
            "required": ["query"],
        },
        "fn": _supabase_query,
    },
    {
        "name": "rag_retrieve",
        "description": "Retrieve relevant context from the local RAG knowledge base. Use for project-specific questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query string"},
                "top_k": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
        "fn": _rag_retrieve,
    },
    {
        "name": "shell_exec",
        "description": "Execute a shell command and return stdout/stderr. Use for git, file ops, or running scripts.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "timeout": {"type": "integer", "description": "Max seconds before kill (default 30)", "default": 30},
            },
            "required": ["command"],
        },
        "fn": _shell_exec,
    },
    {
        "name": "file_read",
        "description": "Read the full contents of a file. Security-restricted to project directory only.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative path to the file to read"},
            },
            "required": ["path"],
        },
        "fn": _file_read,
    },
    {
        "name": "web_search",
        "description": "PLACEHOLDER - returns instructions to use RAG instead.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
            },
            "required": ["query"],
        },
        "fn": _web_search,
    },
    # ── MMX-CLI tools (MiniMax multimodality) ───────────────────────────────
    {
        "name": "mmx_vision",
        "description": "Describe or analyze an image using MiniMax VLM (vision modality). Use this before shell_exec for screenshot analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Absolute or relative path to the image file to analyze",
                },
                "prompt": {
                    "type": "string",
                    "description": "Question or instruction about the image (e.g. 'What does this screenshot show?')",
                },
            },
            "required": ["image_path", "prompt"],
        },
        "fn": mmx_vision,
    },
    {
        "name": "mmx_search",
        "description": "Search the web via MiniMax search modality. Use for fresh data when RAG doesn't have the answer.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string",
                },
            },
            "required": ["query"],
        },
        "fn": mmx_search,
    },
    {
        "name": "mmx_speech",
        "description": "Synthesize speech from text using MiniMax TTS. Returns path to the audio file.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to synthesize into speech",
                },
                "voice": {
                    "type": "string",
                    "description": "Voice name from mmx speech voices list (default: English_Expressive_narrator)",
                },
            },
            "required": ["text"],
        },
        "fn": mmx_speech,
    },
    # ── System monitor tools ────────────────────────────────────────────────
    {
        "name": "list_processes",
        "description": "List top processes by CPU or memory usage. Security: unrestricted for owner.",
        "parameters": {
            "type": "object",
            "properties": {
                "sort_by": {"type": "string", "enum": ["cpu", "mem", "pid", "time", "rss"], "description": "Sort field (default cpu)"},
                "top_n": {"type": "integer", "description": "Number of processes (default 20)"},
                "user": {"type": "string", "description": "Filter by username"},
            },
        },
        "fn": _list_processes,
    },
    {
        "name": "kill_process",
        "description": "Kill a process by PID. SECURITY: destructive — requires confirm=True to send signal.",
        "parameters": {
            "type": "object",
            "properties": {
                "pid": {"type": "integer", "description": "Process ID to kill"},
                "signal": {"type": "string", "enum": ["TERM", "KILL", "HUP", "INT", "QUIT"], "description": "Signal to send (default TERM)"},
                "confirm": {"type": "boolean", "description": "Must be True to actually send signal"},
            },
            "required": ["pid", "confirm"],
        },
        "fn": _kill_process,
    },
    {
        "name": "process_tree",
        "description": "Show process tree starting from a PID (default: init/1).",
        "parameters": {
            "type": "object",
            "properties": {
                "pid": {"type": "integer", "description": "Root PID (default 1)"},
            },
        },
        "fn": _process_tree,
    },
    {
        "name": "system_stats",
        "description": "Report CPU model, load averages, memory, uptime, and disk usage.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _system_stats,
    },
    {
        "name": "cpu_usage_per_core",
        "description": "Report per-core CPU usage from /proc/stat or top.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _cpu_usage_per_core,
    },
    {
        "name": "memory_usage",
        "description": "Report detailed memory usage (free + /proc/meminfo).",
        "parameters": {"type": "object", "properties": {}},
        "fn": _memory_usage,
    },
    {
        "name": "running_services",
        "description": "List running systemd services.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _running_services,
    },
    {
        "name": "service_status",
        "description": "Get detailed status of a specific systemd service.",
        "parameters": {
            "type": "object",
            "properties": {"service_name": {"type": "string", "description": "Service name (without .service)"}},
            "required": ["service_name"],
        },
        "fn": _service_status,
    },
    {
        "name": "failed_services",
        "description": "List failed systemd services.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _failed_services,
    },
    {
        "name": "network_connections",
        "description": "Show active network connections (ss -tunap).",
        "parameters": {"type": "object", "properties": {}},
        "fn": _network_connections,
    },
    {
        "name": "listening_ports",
        "description": "Show listening ports and their processes.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _listening_ports,
    },
    {
        "name": "who_is_logged_in",
        "description": "Show who is currently logged in and their activity.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _who_is_logged_in,
    },
    {
        "name": "network_stats",
        "description": "Show network interface statistics (ip -s link, /proc/net/dev).",
        "parameters": {"type": "object", "properties": {}},
        "fn": _network_stats,
    },
    {
        "name": "disk_io",
        "description": "Show disk I/O statistics using iostat or /proc/diskstats.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _disk_io,
    },
    # ── Filesystem control tools ───────────────────────────────────────────
    {
        "name": "fs_read_file",
        "description": "Read a file's contents with optional offset/limit. SECURITY: project directory only.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative path"},
                "offset": {"type": "integer", "description": "Line offset (default 0)"},
                "limit": {"type": "integer", "description": "Max lines (default 500)"},
            },
            "required": ["path"],
        },
        "fn": _fs_read_file,
    },
    {
        "name": "fs_write_file",
        "description": "Write content to a file. SECURITY: requires confirm=True to write.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Target file path"},
                "content": {"type": "string", "description": "Content to write"},
                "confirm": {"type": "boolean", "description": "Must be True to actually write"},
            },
            "required": ["path", "content", "confirm"],
        },
        "fn": _fs_write_file,
    },
    {
        "name": "fs_list_dir",
        "description": "List directory contents with file sizes. SECURITY: project directory only.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default .)"},
                "depth": {"type": "integer", "description": "Depth (default 1)"},
            },
        },
        "fn": _fs_list_dir,
    },
    {
        "name": "fs_search_files",
        "description": "Find files matching a name pattern using find.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Filename pattern (find -name)"},
                "path": {"type": "string", "description": "Search directory (default .)"},
                "filetype": {"type": "string", "description": "Type: f=file, d=dir, ''=all (default f)"},
            },
            "required": ["pattern"],
        },
        "fn": _fs_search_files,
    },
    {
        "name": "fs_grep_files",
        "description": "Grep for a regex pattern in project files (py, ts, js, md, yaml, json, txt).",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "Directory to search (default .)"},
                "context": {"type": "integer", "description": "Lines of context (default 2)"},
            },
            "required": ["pattern"],
        },
        "fn": _fs_grep_files,
    },
    {
        "name": "fs_disk_usage",
        "description": "Report disk usage for a path (df + du).",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path (default /)"}},
        },
        "fn": _fs_disk_usage,
    },
    # ── Log reader tools ─────────────────────────────────────────────────
    {
        "name": "tail_log",
        "description": "Tail the last N lines from a named log. Known logs: auth, syslog, kern, nginx_access, nginx_error, docker, telegram_bot, boot, apt, dpkg.",
        "parameters": {
            "type": "object",
            "properties": {
                "log_name": {"type": "string", "description": "Log name from WATCHED_LOGS or a file path"},
                "num_lines": {"type": "integer", "description": "Number of lines (default 50)"},
                "pattern": {"type": "string", "description": "Optional regex filter"},
            },
            "required": ["log_name"],
        },
        "fn": _tail_log,
    },
    {
        "name": "grep_log",
        "description": "Grep a regex pattern in a log with N lines of context.",
        "parameters": {
            "type": "object",
            "properties": {
                "log_name": {"type": "string", "description": "Log name or path"},
                "pattern": {"type": "string", "description": "Regex pattern"},
                "context": {"type": "integer", "description": "Context lines before/after (default 3)"},
            },
            "required": ["log_name", "pattern"],
        },
        "fn": _grep_log,
    },
    {
        "name": "count_log_entries",
        "description": "Count how many lines in a log match a pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "log_name": {"type": "string", "description": "Log name or path"},
                "pattern": {"type": "string", "description": "Regex pattern"},
            },
            "required": ["log_name", "pattern"],
        },
        "fn": _count_log_entries,
    },
    {
        "name": "list_all_logs",
        "description": "List all known WATCHED_LOGS and their existence status. Includes project logs.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _list_all_logs,
    },
    {
        "name": "watch_log_live",
        "description": "Stream log entries live for N seconds using tail -f.",
        "parameters": {
            "type": "object",
            "properties": {
                "log_name": {"type": "string", "description": "Log name or path"},
                "pattern": {"type": "string", "description": "Optional regex filter"},
                "duration_seconds": {"type": "integer", "description": "Stream duration (default 10)"},
            },
            "required": ["log_name"],
        },
        "fn": _watch_log_live,
    },
    {
        "name": "get_recent_errors",
        "description": "Extract ERROR, WARN, CRIT, FATAL, exception lines from a log.",
        "parameters": {
            "type": "object",
            "properties": {
                "log_name": {"type": "string", "description": "Log name or path"},
                "num_lines": {"type": "integer", "description": "Max error lines (default 30)"},
            },
            "required": ["log_name"],
        },
        "fn": _get_recent_errors,
    },
    {
        "name": "follow_journal",
        "description": "Follow a systemd journal unit's recent logs via journalctl.",
        "parameters": {
            "type": "object",
            "properties": {
                "unit": {"type": "string", "description": "Systemd unit name"},
                "num_lines": {"type": "integer", "description": "Number of lines (default 50)"},
            },
            "required": ["unit"],
        },
        "fn": _follow_journal,
    },
    # ── Desktop control tools ─────────────────────────────────────────────
    {
        "name": "take_screenshot",
        "description": "Take a screenshot using scrot. Returns the image file path.",
        "parameters": {
            "type": "object",
            "properties": {"output_path": {"type": "string", "description": "Optional output path"}},
        },
        "fn": _take_screenshot,
    },
    {
        "name": "take_screenshot_base64",
        "description": "Take a screenshot and return it as a base64-encoded PNG string.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _take_screenshot_base64,
    },
    {
        "name": "list_windows",
        "description": "List all open windows using xdotool (visible windows only).",
        "parameters": {"type": "object", "properties": {}},
        "fn": _list_windows,
    },
    {
        "name": "get_active_window",
        "description": "Get the currently active/focused window ID and name.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _get_active_window,
    },
    {
        "name": "switch_window",
        "description": "Switch to a window by its ID (from list_windows).",
        "parameters": {
            "type": "object",
            "properties": {"window_id": {"type": "string", "description": "Window ID"}},
            "required": ["window_id"],
        },
        "fn": _switch_window,
    },
    {
        "name": "close_window",
        "description": "Close a window by its ID (SIGTERM).",
        "parameters": {
            "type": "object",
            "properties": {"window_id": {"type": "string", "description": "Window ID"}},
            "required": ["window_id"],
        },
        "fn": _close_window,
    },
    {
        "name": "minimize_window",
        "description": "Minimize a window by its ID.",
        "parameters": {
            "type": "object",
            "properties": {"window_id": {"type": "string", "description": "Window ID"}},
            "required": ["window_id"],
        },
        "fn": _minimize_window,
    },
    {
        "name": "switch_tab_next",
        "description": "Switch to the next tab in the current window (Alt+Tab behavior).",
        "parameters": {"type": "object", "properties": {}},
        "fn": _switch_tab_next,
    },
    {
        "name": "switch_tab_prev",
        "description": "Switch to the previous tab in the current window.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _switch_tab_prev,
    },
    {
        "name": "open_app",
        "description": "Open an application by name using xdg-open.",
        "parameters": {
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "App name or URL"}},
            "required": ["app_name"],
        },
        "fn": _open_app,
    },
    {
        "name": "type_text",
        "description": "Type a string using xdotool type. WARNING: visible in process args — avoid sensitive text.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to type"}},
            "required": ["text"],
        },
        "fn": _type_text,
    },
    {
        "name": "key_press",
        "description": "Press a key combination (e.g. 'Ctrl+c', 'Alt+F4', 'Super+d').",
        "parameters": {
            "type": "object",
            "properties": {"key_combo": {"type": "string", "description": "Key combination"}},
            "required": ["key_combo"],
        },
        "fn": _key_press,
    },
    {
        "name": "mouse_click",
        "description": "Click at screen coordinates (x, y). button: 1=left, 2=middle, 3=right.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate"},
                "y": {"type": "integer", "description": "Y coordinate"},
                "button": {"type": "string", "description": "Mouse button (default 1)"},
            },
            "required": ["x", "y"],
        },
        "fn": _mouse_click,
    },
    {
        "name": "get_window_info",
        "description": "Get information about the currently active window: PID, geometry, name, desktop.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _get_window_info,
    },
    {
        "name": "get_clipboard",
        "description": "Get current clipboard text using xclip.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _get_clipboard,
    },
    {
        "name": "set_clipboard",
        "description": "Set clipboard text using xclip.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to set"}},
            "required": ["text"],
        },
        "fn": _set_clipboard,
    },
    {
        "name": "get_desktop_info",
        "description": "Get current desktop number, total desktops, and desktop names.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _get_desktop_info,
    },
    {
        "name": "switch_desktop",
        "description": "Switch to a desktop by number (0-indexed).",
        "parameters": {
            "type": "object",
            "properties": {"desktop": {"type": "string", "description": "Desktop number (0-indexed)"}},
            "required": ["desktop"],
        },
        "fn": _switch_desktop,
    },
    {
        "name": "get_screen_resolution",
        "description": "Get current screen resolution using xdotool or xdpyinfo.",
        "parameters": {"type": "object", "properties": {}},
        "fn": _get_screen_resolution,
    },
]


def get_tool_schema(name: str) -> dict[str, Any] | None:
    """Return the OpenAI-format tool schema for a named tool (no fn field)."""
    for tool in LEGIONA_TOOLS:
        if tool["name"] == name:
            return {k: v for k, v in tool.items() if k != "fn"}
    return None


def get_tool_function(name: str) -> Callable[..., str] | None:
    """Return the callable function for a named tool."""
    for tool in LEGIONA_TOOLS:
        if tool["name"] == name:
            return tool["fn"]
    return None


def list_tool_names() -> list[str]:
    """Return all registered tool names."""
    return [t["name"] for t in LEGIONA_TOOLS]


# OpenAI-format tool schemas for API calls
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {k: v for k, v in t.items() if k != "fn"}
    for t in LEGIONA_TOOLS
]
