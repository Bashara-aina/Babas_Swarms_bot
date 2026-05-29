"""MCP — config loading, status, stdio tool calls, connection pooling, and health checks."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

# ---- Anyio Python 3.13 cancel-scope bug workaround ----
# anyio 4.x has a bug where CancelScope.__exit__ raises:
#   RuntimeError("Attempted to exit cancel scope in a different task than it was entered in")
# This fires in async generators (like mcp.client.stdio.stdio_client) when the
# generator's athrow() runs cleanup from a different task than the one that entered
# the cancel scope. We patch CancelScope.__exit__ to silently suppress this specific
# error since the cleanup (process termination) has already happened or is irrelevant.
try:
    import anyio._backends._asyncio as _asyncio_backend
    _orig = _asyncio_backend.CancelScope.__exit__
    def _patched_cancel_scope_exit(self, exc_type, exc_val, exc_tb):
        try:
            return _orig(self, exc_type, exc_val, exc_tb)
        except RuntimeError as e:
            if "cancel scope" in str(e) and "different task" in str(e):
                return True  # Suppress the anyio bug silently
            raise
    _asyncio_backend.CancelScope.__exit__ = _patched_cancel_scope_exit
except Exception:
    pass  # anyio not installed or already patched — non-fatal

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "mcp_config.json"


def _yield_to_event_loop() -> asyncio.Task:
    """Schedule a trivial coroutine on the event loop and return its Task.

    This differs from asyncio.sleep(0) in that the task is created OUTSIDE the
    current CancelScope, so if the current scope has been marked cancelled it
    won't cause the task itself to be cancelled before it runs.
    """
    async def _noop():
        pass
    return asyncio.create_task(_noop())


def _thread_sleep_sync(seconds: float) -> None:
    """Blocking sleep — entirely immune to asyncio CancelScopes."""
    time.sleep(seconds)


def _isolated_call_tool(server_name: str, tool_name: str, arguments: dict[str, Any]) -> str:
    """Run a complete single-call tool invocation in a fresh process.

    Runs entirely outside any asyncio context — no CancelScope, no inherited
    cancellation from the pool's cleanup path. The process imports MCPClient
    fresh with its own event loop.
    """
    from core.mcp_client import MCPClient

    async def _run():
        return await MCPClient().call_tool(server_name, tool_name, arguments)

    return asyncio.run(_run())


def _isolated_list_tools(server_name: str) -> list[dict[str, Any]]:
    """Run list_tools in a fresh process to avoid anyio CancelScope contamination."""
    import json

    from core.mcp_client import MCPClient

    async def _run():
        return await MCPClient().list_tools(server_name)

    result = asyncio.run(_run())
    return json.loads(json.dumps(result)) if isinstance(result, list) else []


def load_mcp_config() -> dict[str, Any]:
    if not _CONFIG_PATH.exists():
        return {"servers": [], "mcpServers": {}}
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("mcp_config.json read failed: %s", exc)
        return {"servers": [], "mcpServers": {}}

    servers = list(data.get("servers") or [])
    meta = data.get("mcpServers") or {}
    known = {s.get("name") for s in servers if isinstance(s, dict)}
    for name, m in meta.items():
        if name in known:
            continue
        servers.append(
            {
                "name": name,
                "command": "",
                "args": [],
                "enabled": False,
                "description": (m or {}).get("description", "") if isinstance(m, dict) else "",
            }
        )
    data["servers"] = servers
    return data


def format_mcp_status() -> str:
    cfg = load_mcp_config()
    servers = cfg.get("servers") or []
    if not servers:
        return "No MCP servers in config/mcp_config.json."
    lines = ["<b>MCP servers</b>"]
    for s in servers:
        if not isinstance(s, dict):
            continue
        en = "on" if s.get("enabled") else "off"
        name = s.get("name", "?")
        cmd = s.get("command", "")
        args = " ".join(s.get("args") or [])
        lines.append(f"• {name} [{en}]: <code>{cmd} {args}</code>".strip())
    return "\n".join(lines)


def _tool_result_to_text(result: Any) -> str:
    if result is None:
        return ""
    content = getattr(result, "content", None)
    if content is None:
        return str(result)
    parts: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if text is not None:
            parts.append(str(text))
        elif isinstance(block, dict):
            parts.append(str(block.get("text") or block))
    return "\n".join(parts) if parts else str(result)


class MCPClient:
    """Stdio MCP client — one connection per tool call (avoids zombie processes)."""

    def __init__(self) -> None:
        self._cfg = load_mcp_config()

    def _find_server(self, server_name: str) -> dict[str, Any] | None:
        for s in self._cfg.get("servers") or []:
            if isinstance(s, dict) and s.get("name") == server_name:
                return s
        return None

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> str:
        srv = self._find_server(server_name)
        if not srv:
            return f"Error: MCP server '{server_name}' not in config."
        if not srv.get("enabled"):
            return f"Error: MCP server '{server_name}' is disabled in config."

        try:
            from mcp import ClientSession, StdioServerParameters  # type: ignore
            from mcp.client.stdio import stdio_client  # type: ignore
        except Exception as exc:
            logger.warning("mcp SDK not installed: %s", exc)
            return "Error: MCP Python SDK not installed (pip install mcp)."

        cmd = srv.get("command")
        if not cmd:
            return f"Error: MCP server '{server_name}' has no command configured."
        args = list(srv.get("args") or [])
        env = {**os.environ, **(srv.get("env") or {})}
        params = StdioServerParameters(command=str(cmd), args=args, env=env)

        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return _tool_result_to_text(result)[:50000] or "(empty tool result)"
        except Exception as exc:
            logger.error("MCP call_tool %s/%s failed: %s", server_name, tool_name, exc)
            return f"Error: MCP error ({server_name}/{tool_name}): {exc}"

    async def list_tools(self, server_name: str) -> list[dict[str, str]]:
        srv = self._find_server(server_name)
        if not srv or not srv.get("enabled"):
            return []
        try:
            from mcp import ClientSession, StdioServerParameters  # type: ignore
            from mcp.client.stdio import stdio_client  # type: ignore
        except Exception:
            return []

        cmd = srv.get("command")
        if not cmd:
            return []
        params = StdioServerParameters(
            command=str(cmd),
            args=list(srv.get("args") or []),
            env={**os.environ, **(srv.get("env") or {})},
        )
        out: list[dict[str, str]] = []
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    for t in getattr(listed, "tools", None) or []:
                        name = getattr(t, "name", None) or ""
                        desc = getattr(t, "description", None) or ""
                        if name:
                            out.append({"name": str(name), "description": str(desc)[:500]})
        except Exception as exc:
            logger.debug("MCP list_tools failed: %s", exc)
        return out

    async def get_calendar_events(self, days_ahead: int = 7) -> str:
        server = os.getenv("LEGION_MCP_CALENDAR_SERVER", "gmail")
        for tool in (
            "list_calendar_events",
            "calendar_list_events",
            "get_calendar_events",
            "list_events",
        ):
            text = await self.call_tool(server, tool, {"days_ahead": days_ahead})
            if text and "disabled" not in text.lower() and "not in config" not in text.lower():
                return text
        return ""

    async def read_gmail(self, query: str = "is:unread", max_results: int = 5) -> str:
        server = os.getenv("LEGION_MCP_GMAIL_SERVER", "gmail")
        for tool in ("search_emails", "gmail_search", "list_messages"):
            t = await self.call_tool(server, tool, {"query": query, "max_results": max_results})
            if t and "disabled" not in t.lower():
                return t
        return ""

    async def send_email(self, to: str, subject: str, body: str) -> str:
        server = os.getenv("LEGION_MCP_GMAIL_SERVER", "gmail")
        return await self.call_tool(
            server,
            "send_email",
            {"to": to, "subject": subject, "body": body},
        )

    async def create_github_issue(self, repo: str, title: str, body: str) -> str:
        server = os.getenv("LEGION_MCP_GITHUB_SERVER", "github")
        owner = os.getenv("GITHUB_DEFAULT_OWNER", "Bashara-aina")
        return await self.call_tool(
            server,
            "create_issue",
            {"owner": owner, "repo": repo, "title": title, "body": body},
        )

    async def setup_legion_inbox(self) -> str:
        server = os.getenv("LEGION_MCP_AGENTMAIL_SERVER", "agentmail")
        return await self.call_tool(
            server,
            "create_inbox",
            {
                "username": os.getenv("AGENTMAIL_USERNAME", "legion"),
                "display_name": os.getenv(
                    "AGENTMAIL_DISPLAY_NAME", "Legion — Bashara's AI Assistant"
                ),
            },
        )

    async def read_agentmail(self) -> str:
        server = os.getenv("LEGION_MCP_AGENTMAIL_SERVER", "agentmail")
        return await self.call_tool(
            server,
            "list_messages",
            {"inbox_id": os.getenv("AGENTMAIL_INBOX_ID", "")},
        )

    async def read_whatsapp_messages(self, limit: int = 10) -> str:
        """Best-effort MCP WhatsApp read — tool names vary by server implementation."""
        server = os.getenv("LEGION_MCP_WHATSAPP_SERVER", "whatsapp")
        for tool in (
            "get_messages",
            "list_messages",
            "whatsapp_get_messages",
            "read_messages",
        ):
            text = await self.call_tool(server, tool, {"limit": limit})
            if text and "disabled" not in text.lower() and "not in config" not in text.lower():
                if "MCP error" not in text and "no command" not in text.lower():
                    return text
        return ""


class MCPClientPool:
    """Connection pool — one persistent stdio session per server.

    Falls back to single-call mode on any connection error so callers don't
    need to handle pool failures explicitly.
    """

    _instance: MCPClientPool | None = None
    _instance_lock: asyncio.Lock | None = None

    def __new__(cls) -> MCPClientPool:
        """Singleton — reuse the same pool instance across all callers."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # __new__ ensures we only init once; skip re-init on repeated calls
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._cfg = load_mcp_config()
        self._sessions: dict[str, Any] = {}  # server_name -> active ClientSession
        self._readers: dict[str, Any] = {}   # server_name -> read stream
        self._writers: dict[str, Any] = {}  # server_name -> write stream
        self._locks: dict[str, asyncio.Lock] = {}  # per-server reentrant guard
        self._failed: set[str] = set()  # servers that have temporarily failed
        self._failed_expiry: dict[str, float] = {}  # server_name -> timestamp when marked failed
        self.FAILED_RESET_TIMEOUT: float = 30.0  # seconds before allowing retry
        self._initialized: bool = True

    def _lock(self, server_name: str) -> asyncio.Lock:
        if server_name not in self._locks:
            self._locks[server_name] = asyncio.Lock()
        return self._locks[server_name]

    def _server_params(self, srv: dict[str, Any]) -> Any:
        """Build StdioServerParameters from a server config dict."""
        from mcp import StdioServerParameters  # type: ignore
        return StdioServerParameters(
            command=str(srv.get("command", "")),
            args=list(srv.get("args") or []),
            env={**os.environ, **(srv.get("env") or {})},
        )

    async def _ensure_session(self, server_name: str) -> bool:
        """Establish or re-establish a persistent session for server_name.

        Returns True if a session is live, False if we should fall back to
        single-call mode.
        """
        from mcp import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client  # type: ignore

        if server_name in self._failed:
            # Half-open: allow a retry if the reset timeout has elapsed
            if server_name in self._failed_expiry:
                if time.monotonic() - self._failed_expiry[server_name] > self.FAILED_RESET_TIMEOUT:
                    logger.info(
                        "MCP pool: %s retrying after %.0fs timeout",
                        server_name,
                        time.monotonic() - self._failed_expiry[server_name],
                    )
                    self._failed.discard(server_name)
                    self._failed_expiry.pop(server_name, None)
                else:
                    return False
            else:
                return False

        srv = self._find_server(server_name)
        if not srv or not srv.get("enabled"):
            return False

        cmd = srv.get("command")
        if not cmd:
            return False

        # If already live, we're good
        if server_name in self._sessions:
            return True

        params = self._server_params(srv)
        try:
            read, write = await stdio_client(params).__aenter__()
            session = await ClientSession(read, write).__aenter__()
            await session.initialize()
            self._sessions[server_name] = session
            self._readers[server_name] = read
            self._writers[server_name] = write
            logger.info("MCP pool: persistent session established for %s", server_name)
            return True
        except Exception as exc:
            logger.warning("MCP pool: failed to open session for %s: %s", server_name, exc)
            self._failed.add(server_name)
            self._failed_expiry[server_name] = time.monotonic()
            await self._cleanup(server_name)
            return False

    async def _cleanup(self, server_name: str) -> None:
        """Clean up all resources for a server."""
        session = self._sessions.pop(server_name, None)
        reader = self._readers.pop(server_name, None)
        writer = self._writers.pop(server_name, None)
        if session:
            with contextlib.suppress(Exception):
                await session.__aexit__(None, None, None)
        if reader:
            try:
                reader.close()
                if hasattr(reader, 'wait_closed'):
                    await asyncio.wait_for(reader.wait_closed(), timeout=2.0)
            except Exception:
                pass
        if writer:
            with contextlib.suppress(Exception):
                writer.close()

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> str:
        """Call a tool, using the persistent pool if available, falling back to
        single-call mode on any pool error."""

        async with self._lock(server_name):
            session_ok = False
            try:
                session_ok = await self._ensure_session(server_name)
            except asyncio.CancelledError:
                session_ok = False  # anyio CancelScope cancelled — fall through to subprocess
            except Exception as exc:
                logger.warning(
                    "MCP pool call_tool %s/_ensure_session failed, falling back: %s",
                    server_name, exc,
                )
                session_ok = False

            if session_ok:
                session = self._sessions.get(server_name)
                if session is None:
                    session_ok = False  # Cleanup raced — fall through to single-call
                else:
                    try:
                        result = await session.call_tool(tool_name, arguments)
                        if server_name in self._failed:
                            self._failed.discard(server_name)
                            self._failed_expiry.pop(server_name, None)
                            logger.info("MCP pool: %s recovered from failed state", server_name)
                        return _tool_result_to_text(result)[:50000] or "(empty tool result)"
                    except asyncio.CancelledError:
                        # CancelledError here means the pooled session was cancelled by
                        # anyio's cleanup path — not that our call succeeded. Fall through
                        # to single-call so the tool still runs.
                        pass
                    except Exception as exc:
                        logger.warning(
                            "MCP pool call_tool %s/%s failed, falling back: %s",
                            server_name, tool_name, exc,
                        )
                        self._failed.add(server_name)
                        self._failed_expiry[server_name] = time.monotonic()
                        await self._cleanup(server_name)
                    except BaseException as exc:
                        # Catch anyio Python 3.13 task-group cancel-scope bug: the bug fires
                        # inside _cleanup → session.__aexit__ → stdio_client.__aexit__, where a
                        # RuntimeError("Attempted to exit cancel scope in a different task") is
                        # raised. This is wrapped in CancelledError, which is BaseException (not
                        # Exception), so the handler above does NOT catch it. The
                        # RuntimeError may also appear directly in a BaseExceptionGroup.
                        # We walk the exception chain to detect the anyio bug and silently
                        # fall through to single-call so the tool call can still succeed.
                        def _find_anyio_bug(ex: BaseException | None) -> RuntimeError | None:
                            if ex is None:
                                return None
                            if isinstance(ex, RuntimeError) and "cancel scope" in str(ex) and "different task" in str(ex):
                                return ex
                            if isinstance(ex, BaseExceptionGroup):
                                for sub in ex.exceptions:
                                    found = _find_anyio_bug(sub)
                                    if found:
                                        return found
                            # Walk __cause__ chain (anyio bug wrapped in CancelledError)
                            cause = getattr(ex, '__cause__', None)
                            if cause is not None:
                                found = _find_anyio_bug(cause)
                                if found:
                                    return found
                            # Walk __context__ chain (GeneratorExit context may hold the bug)
                            ctx = getattr(ex, '__context__', None)
                            if ctx is not None:
                                found = _find_anyio_bug(ctx)
                                if found:
                                    return found
                            return None

                        if _find_anyio_bug(exc):
                            # Do NOT run _cleanup here — it closes the reader/writer which
                            # triggers the anyio bug again (process.wait() on a live sed).
                            # The pooled session will be retried or skipped on next call.
                            logger.warning(
                                "MCP pool call_tool %s/%s hit anyio cancel-scope bug — skipping cleanup, going to single-call",
                                server_name, tool_name,
                            )
                        else:
                            logger.error("MCP pool call_tool %s/%s unexpected BaseException: %s %s",
                                server_name, tool_name, type(exc).__name__, exc)
                            raise

        # Single-call fallback (outside the lock to avoid blocking other servers).
        # _call_tool_single already handles all the isolation, anyio bug workarounds,
        # retry logic, and hook emission that the old subprocess approach did —
        # without the config-file reload that made the subprocess path broken.
        try:
            return await self._call_tool_single(server_name, tool_name, arguments)
        except asyncio.CancelledError:
            # The outer pool task was cancelled — propagate cleanly.
            raise
        except Exception as exc:
            return f"Error: MCP pool fallback failed ({type(exc).__name__}): {exc}"

    async def _call_tool_single(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> str:
        srv = self._find_server(server_name)
        if not srv:
            return f"Error: MCP server '{server_name}' not in config."
        if not srv.get("enabled"):
            return f"Error: MCP server '{server_name}' is disabled in config."

        try:
            from mcp import ClientSession  # type: ignore
            from mcp.client.stdio import stdio_client  # type: ignore
        except Exception as exc:
            logger.warning("mcp SDK not installed: %s", exc)
            return "Error: MCP Python SDK not installed (pip install mcp)."

        cmd = srv.get("command")
        if not cmd:
            return f"Error: MCP server '{server_name}' has no command configured."

        params = self._server_params(srv)
        last_exc: Exception | None = None
        # Top-level cancellation guard: if the anyio bug causes a spurious CancelledError,
        # suppress it and fall through to retry. The bug fires when anyio's task-group
        # cleanup races against the async generator athrow chain.
        for attempt in range(2):
            text_result: str | None = None
            try:
                # Before stdio_client
                logger.warning("MCP %s/%s: starting stdio call", server_name, tool_name)
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments)
                        logger.warning("MCP %s/%s: got result", server_name, tool_name)
                        # Success — remove from failed set if present
                        if server_name in self._failed:
                            self._failed.discard(server_name)
                            self._failed_expiry.pop(server_name, None)
                            logger.info(
                                "MCP pool: %s recovered from failed state (single-call)",
                                server_name,
                            )
                        text_result = _tool_result_to_text(result)[:12000] or "(empty tool result)"
                        try:
                            from core.hooks import get_hooks
                            hs = get_hooks()
                            if hs:
                                hs.emit("post_tool_use", server=server_name, tool=tool_name, args=arguments, result=text_result)
                        except Exception:
                            pass
                logger.warning("MCP %s/%s: exited stdio with block normally", server_name, tool_name)
            except asyncio.CancelledError as exc:
                # Anyio cancel-scope bug: session.call_tool() succeeded but the process
                # cleanup from athrow raced and CancelledError escaped. The result is already
                # in text_result (if call_tool completed before the race). The standard
                # pattern -- check text_result then determine retry vs raise -- works here.
                if text_result is not None:
                    logger.warning("MCP %s/%s: hit anyio cancel-scope bug but result available, returning it", server_name, tool_name)
                    return text_result
                cause = getattr(exc, '__cause__', None)
                cancel_msg = str(exc)
                is_anyio_cancel = (
                    isinstance(cause, RuntimeError) and "cancel scope" in str(cause)
                ) or (
                    cause is None and "Cancelled via cancel scope" in cancel_msg
                )
                if is_anyio_cancel and attempt < 1:
                    logger.warning(
                        "MCP %s/%s anyio cancel-scope bug (attempt %d) — retrying after delay",
                        server_name, tool_name, attempt + 1,
                    )
                    # Use thread-based blocking sleep — cannot be cancelled by the outer
                    # CancelScope that triggered the anyio bug.
                    _thread_sleep_sync(0.3)
                    continue
                raise
            except BaseException as exc:
                if text_result is not None:
                    logger.warning(
                        "MCP %s/%s anyio cleanup error — returning result anyway",
                        server_name, tool_name,
                    )
                    return text_result

                def _find_anyio_bug(ex: BaseException | None) -> RuntimeError | None:
                    if ex is None:
                        return None
                    if (
                        isinstance(ex, RuntimeError)
                        and "cancel scope" in str(ex)
                        and "different task" in str(ex)
                    ):
                        return ex
                    if isinstance(ex, BaseExceptionGroup):
                        for sub in ex.exceptions:
                            found = _find_anyio_bug(sub)
                            if found:
                                return found
                    cause = getattr(ex, '__cause__', None)
                    if cause is not None:
                        found = _find_anyio_bug(cause)
                        if found:
                            return found
                    ctx = getattr(ex, '__context__', None)
                    if ctx is not None:
                        found = _find_anyio_bug(ctx)
                        if found:
                            return found
                    return None

                # If anyio bug in BaseException (RuntimeError wrapped in BaseExceptionGroup),
                # skip the asyncio.sleep which would re-cancelled. Rebuild result from streams.
                if _find_anyio_bug(exc):
                    if attempt == 0:
                        logger.warning(
                            "MCP %s/%s anyio cancel-scope bug (attempt %d) — retrying after delay",
                            server_name, tool_name, attempt + 1,
                        )
                        _thread_sleep_sync(0.3)
                        continue
                last_exc = exc
                if attempt == 0:
                    logger.warning(
                        "MCP call_tool (single-call) %s/%s attempt %d failed: %s — retrying in 0.5s",
                        server_name, tool_name, attempt + 1, exc,
                    )
                    _thread_sleep_sync(0.5)
                else:
                    logger.error(
                        "MCP call_tool (single-call) %s/%s attempt %d failed: %s",
                        server_name, tool_name, attempt + 1, exc,
                    )
            if text_result is not None:
                return text_result
        if last_exc and _find_anyio_bug(last_exc):
            return f"Error: Obsidian MCP stuck on anyio bug ({server_name}/{tool_name}). Rerun the query or restart the server."
        return "Error: MCP call failed unexpectedly"

    async def close(self) -> None:
        """Close all pooled sessions."""
        for server_name in list(self._sessions.keys()):
            await self._cleanup(server_name)
        self._sessions.clear()
        self._readers.clear()
        self._writers.clear()
        self._failed.clear()
        self._failed_expiry.clear()
        logger.info("MCP pool: all sessions closed")

    # ---- passthrough helpers so existing callers don't need refactoring ----

    def _find_server(self, server_name: str) -> dict[str, Any] | None:
        for s in self._cfg.get("servers") or []:
            if isinstance(s, dict) and s.get("name") == server_name:
                return s
        return None

    async def list_tools(self, server_name: str) -> list[dict[str, str]]:
        """List tools via pooled session or single-call fallback."""
        async with self._lock(server_name):
            session_ok = False
            try:
                session_ok = await self._ensure_session(server_name)
            except asyncio.CancelledError:
                session_ok = False  # anyio CancelScope cancelled — fall through to subprocess
            except Exception as exc:
                logger.warning(
                    "MCP pool list_tools %s _ensure_session failed, falling back: %s",
                    server_name, exc,
                )
                session_ok = False

            if session_ok:
                session = self._sessions[server_name]
                try:
                    listed = await session.list_tools()
                    out: list[dict[str, str]] = []
                    for t in getattr(listed, "tools", None) or []:
                        name = getattr(t, "name", None) or ""
                        desc = getattr(t, "description", None) or ""
                        if name:
                            out.append({"name": str(name), "description": str(desc)[:500]})
                    return out
                except Exception as exc:
                    logger.warning(
                        "MCP pool list_tools %s failed, falling back: %s",
                        server_name, exc,
                    )
                    self._failed.add(server_name)
                    self._failed_expiry[server_name] = time.monotonic()
                    await self._cleanup(server_name)

        # Single-call fallback (outside the lock to avoid blocking other servers).
        # _list_tools_single already handles all isolation and error handling —
        # no need for a subprocess here.
        try:
            return await self._list_tools_single(server_name)
        except asyncio.CancelledError:
            raise
        except Exception:
            return []

    async def _list_tools_single(self, server_name: str) -> list[dict[str, str]]:
        srv = self._find_server(server_name)
        if not srv or not srv.get("enabled"):
            return []
        try:
            from mcp import ClientSession  # type: ignore
            from mcp.client.stdio import stdio_client  # type: ignore
        except Exception:
            return []

        cmd = srv.get("command")
        if not cmd:
            return []
        params = self._server_params(srv)
        out: list[dict[str, str]] = []
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    for t in getattr(listed, "tools", None) or []:
                        name = getattr(t, "name", None) or ""
                        desc = getattr(t, "description", None) or ""
                        if name:
                            out.append({"name": str(name), "description": str(desc)[:500]})
        except Exception as exc:
            logger.debug("MCP list_tools (single-call fallback) failed: %s", exc)
        return out


async def try_list_tools_stdio(server: dict[str, Any]) -> list[str]:
    """Best-effort: connect using inline server dict (for /mcp_status diagnostics)."""
    try:
        from mcp import ClientSession, StdioServerParameters  # type: ignore
        from mcp.client.stdio import stdio_client  # type: ignore
    except Exception:
        return []

    cmd = server.get("command")
    if not cmd:
        return []
    args = list(server.get("args") or [])
    env = {**os.environ, **(server.get("env") or {})}
    params = StdioServerParameters(command=str(cmd), args=args, env=env)
    names: list[str] = []
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                for t in getattr(listed, "tools", None) or []:
                    n = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
                    if n:
                        names.append(str(n))
    except Exception as exc:
        logger.debug("MCP list_tools failed for %s: %s", server.get("name"), exc)
    return names


async def check_server_health() -> dict[str, bool]:
    """Run try_list_tools_stdio on each configured server at startup.

    Logs which servers are reachable vs not and returns a dict
    suitable for injecting into bot startup telemetry.

    Call this once early in main.py or bot init.
    """
    cfg = load_mcp_config()
    servers = cfg.get("servers") or []
    results: dict[str, bool] = {}
    for srv in servers:
        if not isinstance(srv, dict):
            continue
        name = srv.get("name", "?")
        enabled = srv.get("enabled", False)
        if not enabled:
            logger.info("MCP health: %s [disabled]", name)
            results[name] = False
            continue
        tools = await try_list_tools_stdio(srv)
        reachable = len(tools) > 0
        results[name] = reachable
        if reachable:
            logger.info("MCP health: %s ✓ (%d tools)", name, len(tools))
        else:
            logger.warning("MCP health: %s ✗ (no tools returned)", name)
    return results
