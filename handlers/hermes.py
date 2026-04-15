"""Hermes Agent handlers: /hermes /hermes-search /hermes-delegate /hermes-tools /hermes-smoke.

Hermes Agent (nousresearch/hermes-agent) is a self-improving AI agent with:
- Tool registry with 10+ named toolsets (terminal, file, web, browser, delegate, etc.)
- SQLite/FTS5 session memory for cross-session recall
- Delegate subagents for parallel task execution
- Skills system for procedural memory

This handler bridges Hermes's synchronous AIAgent into swarm-bot's async aiogram loop.
"""

from __future__ import annotations

import asyncio
import html as html_mod
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .shared import (
    _keep_typing,
    is_allowed,
    send_chunked,
)

logger = logging.getLogger(__name__)
router = Router()

# ─────────────────────────────────────────────────────────────────────────────
# Hermes Agent wrapper helpers
# ─────────────────────────────────────────────────────────────────────────────


def _format_hermes_result(result: Any) -> str:
    """Format Hermes agent result for Telegram display."""
    if isinstance(result, dict):
        final = result.get("final_response", "")
        if final:
            return str(final)
        # Fallback: dump non-empty fields
        for key in ("response", "output", "result", "message"):
            if key in result and result[key]:
                return str(result[key])
        return str(result)
    return str(result) if result else "(empty response)"


def _escape_html(text: str) -> str:
    return html_mod.escape(str(text))


# ─────────────────────────────────────────────────────────────────────────────
# /hermes — run Hermes agent on a task
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("hermes"))
async def cmd_hermes(msg: Message) -> None:
    """Handle /hermes <task> — run Hermes agent on a task.

    Hermes is nousresearch's self-improving agent with persistent session
    memory, delegate subagents, and a skills system. Use this when a task
    needs deep multi-step reasoning with tool use.

    Examples:
        /hermes write a Python script to download all PDFs from this arxiv link
        /hermes search for recent papers on Mamba and summarize the key findings
        /hermes analyze the git log and find the most impactful commits
    """
    if not is_allowed(msg):
        return

    raw = (msg.text or "").removeprefix("/hermes").strip()
    if not raw:
        await msg.answer(
            "<b>Hermes Agent</b> — nousresearch's self-improving agent\n\n"
            "Usage: <code>/hermes &lt;task&gt;</code>\n\n"
            "Hermes has:\n"
            "• Terminal, file, web, and browser tools\n"
            "• FTS5 session memory across conversations\n"
            "• Delegate subagents for parallel work\n"
            "• Skills system for procedural memory\n\n"
            "Subcommands:\n"
            "<code>/hermes-search &lt;query&gt;</code> — search past sessions\n"
            "<code>/hermes-delegate &lt;goal&gt;</code> — spawn a subagent\n"
            "<code>/hermes-tools</code> — list available toolsets\n"
            "<code>/hermes-smoke</code> — run health check",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("🧠 Hermes activating…")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from core.hermes_adapter import (
            create_hermes_agent,
            get_hermes_bridge,
            get_hermes_session_manager,
        )

        # Generate a session ID for this conversation
        session_id = f"legion-{uuid.uuid4().hex[:12]}"
        user_id = str(msg.from_user.id) if msg.from_user else None

        # Create Hermes agent with terminal + file + web tools
        agent = create_hermes_agent(
            enabled_toolsets=["terminal", "file", "web", "browser"],
            session_id=session_id,
            platform="legion",
            user_id=user_id,
            max_iterations=90,
        )

        bridge = get_hermes_bridge()

        # Prepare session
        session_mgr = get_hermes_session_manager()
        await session_mgr.create_session(
            session_id=session_id,
            source="legion",
            model=agent.model,
            user_id=user_id,
        )

        # Run the conversation
        result = await bridge.run_conversation(
            agent=agent,
            user_message=raw,
            session_id=session_id,
        )

        typing_task.cancel()
        await status_msg.delete()

        formatted = _format_hermes_result(result)
        await send_chunked(msg, formatted, model_used="hermes")

    except ImportError as e:
        typing_task.cancel()
        await status_msg.edit_text(
            f"❌ Hermes not available: <code>{_escape_html(str(e))}</code>\n"
            "Set HERMES_REPO_PATH or clone hermes-agent to ~/hermes-agent",
            parse_mode="HTML",
        )
    except Exception as e:
        typing_task.cancel()
        logger.exception("Hermes /hermes error")
        await status_msg.edit_text(
            f"❌ Hermes error: <code>{_escape_html(str(e)[:300])}</code>",
            parse_mode="HTML",
        )


# ─────────────────────────────────────────────────────────────────────────────
# /hermes-search — FTS5 session recall
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("hermes-search"))
async def cmd_hermes_search(msg: Message) -> None:
    """Handle /hermes-search <query> — search past Hermes sessions via FTS5.

    Uses Hermes's SessionDB (SQLite + FTS5) to search across all past
    sessions and return focused summaries of matching conversations.

    Examples:
        /hermes-search Mamba SSM architecture
        /hermes-search docker networking setup
        /hermes-search paper review framework
    """
    if not is_allowed(msg):
        return

    query = (msg.text or "").removeprefix("/hermes-search").strip()
    if not query:
        await msg.answer(
            "Usage: <code>/hermes-search &lt;query&gt;</code>\n"
            "Searches Hermes's long-term session memory via FTS5.",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer(f"🔍 Searching sessions for: <b>{_escape_html(query)}</b>…", parse_mode="HTML")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from core.hermes_adapter import hermes_session_search

        result = await hermes_session_search(
            query=query,
            source_filter=["legion", "telegram"],
            limit=5,
        )

        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="hermes/session-search")

    except ImportError:
        typing_task.cancel()
        await status_msg.edit_text(
            "❌ Hermes session search not available.\n"
            "Ensure hermes_state module is accessible.",
            parse_mode="HTML",
        )
    except Exception as e:
        typing_task.cancel()
        logger.exception("Hermes session search error")
        await status_msg.edit_text(
            f"❌ Search error: <code>{_escape_html(str(e)[:300])}</code>",
            parse_mode="HTML",
        )


# ─────────────────────────────────────────────────────────────────────────────
# /hermes-delegate — spawn a subagent
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("hermes-delegate"))
async def cmd_hermes_delegate(msg: Message) -> None:
    """Handle /hermes-delegate <goal> — spawn an isolated Hermes subagent.

    Delegates a task to a fresh Hermes subagent with restricted toolsets
    and isolated workspace. The subagent runs in a ThreadPoolExecutor and
    returns its final summary.

    Use for tasks that are:
    - Independent and parallelizable
    - Risky (isolated workspace — can't touch main files)
    - CPU-intensive (runs in thread pool)

    Examples:
        /hermes-delegate review this code for security issues
        /hermes-delegate write tests for the new API endpoints
        /hermes-delegate research alternatives to Redis for our caching layer
    """
    if not is_allowed(msg):
        return

    raw = (msg.text or "").removeprefix("/hermes-delegate").strip()
    if not raw:
        await msg.answer(
            "Usage: <code>/hermes-delegate &lt;goal&gt;</code>\n\n"
            "Spawns an isolated Hermes subagent for the task.\n"
            "The subagent has its own workspace and toolset restrictions.\n\n"
            "Example: <code>/hermes-delegate find all TODO comments in the codebase</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("🚀 Spawning Hermes subagent…")
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        from core.hermes_adapter import hermes_delegate

        session_id = f"legion-delegate-{uuid.uuid4().hex[:8]}"

        result = await hermes_delegate(
            goal=raw,
            toolsets=["terminal", "file", "web"],
            max_iterations=50,
            session_id=session_id,
        )

        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(msg, result, model_used="hermes/delegate")

    except ImportError:
        typing_task.cancel()
        await status_msg.edit_text(
            "❌ Hermes delegate not available.\n"
            "Ensure hermes-agent is cloned and HERMES_REPO_PATH is set.",
            parse_mode="HTML",
        )
    except Exception as e:
        typing_task.cancel()
        logger.exception("Hermes delegate error")
        await status_msg.edit_text(
            f"❌ Delegate error: <code>{_escape_html(str(e)[:300])}</code>",
            parse_mode="HTML",
        )


# ─────────────────────────────────────────────────────────────────────────────
# /hermes-tools — list available toolsets and tools
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("hermes-tools"))
async def cmd_hermes_tools(msg: Message) -> None:
    """Handle /hermes-tools — list all available Hermes toolsets and their tools."""
    if not is_allowed(msg):
        return

    try:
        from core.hermes_adapter import (
            HERMES_LEGION_TOOLSETS,
            get_hermes_tool_definitions,
        )

        definitions = get_hermes_tool_definitions(quiet_mode=True)

        # Group tools by toolset
        toolset_tools: Dict[str, List[str]] = {}
        for ts_name, ts_meta in HERMES_LEGION_TOOLSETS.items():
            toolset_tools[ts_name] = list(ts_meta.get("tools", []))

        lines = [
            "<b>🛠 Hermes Tool Registry</b>\n",
            f"<i>{len(definitions)} tools across {len(HERMES_LEGION_TOOLSETS)} toolsets</i>\n\n",
        ]

        for ts_name, ts_meta in HERMES_LEGION_TOOLSETS.items():
            tools = ts_meta.get("tools", [])
            desc = ts_meta.get("description", "")
            includes = ts_meta.get("includes", [])
            included_str = f" → includes: {', '.join(includes)}" if includes else ""
            lines.append(
                f"<b>{ts_name}</b> — {desc}\n"
                f"  Tools: {', '.join(tools)}{included_str}\n\n"
            )

        await msg.answer("".join(lines), parse_mode="HTML")

    except ImportError:
        await msg.answer(
            "❌ Hermes tool registry not available.\n"
            "Ensure hermes-agent is accessible.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Hermes tools error")
        await msg.answer(
            f"❌ Error: <code>{_escape_html(str(e)[:300])}</code>",
            parse_mode="HTML",
        )


# ─────────────────────────────────────────────────────────────────────────────
# /hermes-smoke — health check
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("hermes-smoke"))
async def cmd_hermes_smoke(msg: Message) -> None:
    """Handle /hermes-smoke — run Hermes smoke test.

    Verifies:
    - AIAgent can be imported
    - Tool definitions load
    - SessionDB initializes
    - Toolset resolution works
    """
    if not is_allowed(msg):
        return

    status_msg = await msg.answer("🔬 Running Hermes smoke test…")

    try:
        from core.hermes_adapter import hermes_smoke_test

        results = await hermes_smoke_test()

        lines = ["<b>🔬 Hermes Smoke Test</b>\n\n"]
        for check, result in results.items():
            lines.append(f"• <b>{check}:</b> {result}\n")

        await status_msg.edit_text("".join(lines), parse_mode="HTML")

    except ImportError:
        await status_msg.edit_text(
            "❌ Hermes smoke test not available.\n"
            "HERMES_REPO_PATH may not be set or hermes-agent not cloned.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Hermes smoke test error")
        await status_msg.edit_text(
            f"❌ Smoke test error: <code>{_escape_html(str(e)[:300])}</code>",
            parse_mode="HTML",
        )


# ─────────────────────────────────────────────────────────────────────────────
# /hermes-sessions — list recent Hermes sessions
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("hermes-sessions"))
async def cmd_hermes_sessions(msg: Message) -> None:
    """Handle /hermes-sessions — list recent Hermes sessions."""
    if not is_allowed(msg):
        return

    raw = (msg.text or "").removeprefix("/hermes-sessions").strip()
    try:
        limit = min(int(raw), 10) if raw else 5
    except ValueError:
        limit = 5

    status_msg = await msg.answer("📜 Loading recent Hermes sessions…")

    try:
        from core.hermes_adapter import get_hermes_session_manager

        mgr = get_hermes_session_manager()
        sessions = await mgr.list_sessions(source="legion", limit=limit)

        if not sessions:
            await status_msg.edit_text("No Hermes sessions found.")
            return

        lines = [f"<b>📜 Recent Hermes Sessions</b> ({len(sessions)} total)\n\n"]
        for s in sessions:
            sid = s.get("session_id", "?")
            started = s.get("started_at", "?")
            message_count = s.get("message_count", 0)
            title = s.get("title", "")
            preview = (s.get("preview") or "")[:80]

            lines.append(
                f"<b>Session:</b> <code>{sid[-12:]}</code>\n"
                f"<b>Started:</b> {started} | <b>Messages:</b> {message_count}\n"
            )
            if title:
                lines.append(f"<b>Title:</b> {_escape_html(title)}\n")
            if preview:
                lines.append(f"<i>{_escape_html(preview)}</i>\n")
            lines.append("\n")

        await status_msg.edit_text("".join(lines), parse_mode="HTML")

    except ImportError:
        await status_msg.edit_text(
            "❌ Hermes session manager not available.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Hermes sessions error")
        await status_msg.edit_text(
            f"❌ Error: <code>{_escape_html(str(e)[:300])}</code>",
            parse_mode="HTML",
        )
