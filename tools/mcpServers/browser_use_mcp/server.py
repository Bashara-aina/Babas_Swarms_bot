#!/usr/bin/env python3
"""
browser-use MCP Server — MiniMax-native browser automation via browser-use.

Exposes stable browser operations to OpenCode's MCP layer:
  open, click, fill, scroll, wait, screenshot, get_text, get_html, close, run_task

All LLM calls route through ChatLiteLLM (browser-use native) → LiteLLM proxy → minimax/MiniMax-M2.7 only.
Forbidden models (Claude, OpenAI, Gemini, etc.) are rejected at startup.

Usage:
    python -m tools.mcpServers.browser_use_mcp.server
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    print("ERROR: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

APP_NAME = "browser-use-mcp"
VERSION = "1.0.0"
server = Server(APP_NAME)

# ── MiniMax-only LLM enforcement ────────────────────────────────────────────

LITELLM_PROXY = os.environ.get("AI_GATEWAY_URL", "http://localhost:4000")
LITELLM_KEY = os.environ.get("AI_GATEWAY_API_KEY", "legion-proxy-key")
MINIMAX_MODEL = os.environ.get("AI_GATEWAY_MODEL", "minimax-primary")

_FORBIDDEN = {"claude", "anthropic", "gpt-4", "gpt-5", "openai", "gemini", "groq", "together"}
if any(k in MINIMAX_MODEL.lower() for k in _FORBIDDEN):
    raise RuntimeError(
        f"[browser_use_mcp] Forbidden model: {MINIMAX_MODEL!r}. "
        "This MCP server is locked to MiniMax only. Aborting."
    )


def _make_llm():
    from browser_use.llm.litellm import ChatLiteLLM

    return ChatLiteLLM(
        model=MINIMAX_MODEL,
        api_key=LITELLM_KEY,
        api_base=LITELLM_PROXY,
        temperature=0.0,
    )


# ── BrowserSession wrapper (thin layer on browser_use BrowserSession) ─────

class BrowserSessionWrapper:
    """Thin wrapper around browser-use's BrowserSession for MCP tool exposure."""

    def __init__(self, name: str = "default", headless: bool = True):
        self.name = name
        self.headless = headless
        self._session = None
        self._agent = None
        self._initialized = False

    async def _ensure(self):
        if self._initialized:
            return
        from browser_use import Agent
        from browser_use.browser.profile import BrowserProfile
        from browser_use.browser.session import BrowserSession

        bp = BrowserProfile(
            headless=self.headless,
            disable_security=False,
            extra_chromium_args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self._session = BrowserSession(browser_profile=bp, is_local=True)
        llm = _make_llm()
        self._agent = Agent(
            task="placeholder",
            llm=llm,
            browser=self._session,
            max_actions_per_step=5,
            enable_planning=True,
            use_thinking=True,
            max_failures=3,
        )
        self._initialized = True

    async def open(self, url: str) -> dict[str, Any]:
        await self._ensure()
        await self._session.connect()
        page = await self._session.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return {"url": page.url, "title": await page.title()}

    async def click(self, selector: str) -> dict[str, Any]:
        await self._ensure()
        page = self._session.get_current_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        await page.click(selector, timeout=5000)
        return {"success": True, "selector": selector}

    async def fill(self, selector: str, value: str) -> dict[str, Any]:
        await self._ensure()
        page = self._session.get_current_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        await page.fill(selector, value)
        return {"success": True, "selector": selector, "value": value}

    async def scroll(self, pixels: int = 300) -> dict[str, Any]:
        await self._ensure()
        page = self._session.get_current_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        await page.evaluate(f"window.scrollBy(0, {pixels})")
        return {"success": True, "pixels": pixels}

    async def wait(self, seconds: float = 1.0) -> dict[str, Any]:
        await asyncio.sleep(seconds)
        return {"success": True, "waited": seconds}

    async def screenshot(self, path: str) -> dict[str, Any]:
        await self._ensure()
        page = self._session.get_current_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        await page.screenshot(path=path)
        return {"success": True, "path": path}

    async def get_text(self, selector: str = "body") -> dict[str, Any]:
        await self._ensure()
        page = self._session.get_current_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        el = page.query_selector(selector)
        text = await el.text_content() if el else ""
        return {"text": text, "selector": selector}

    async def get_html(self, selector: str = "body") -> dict[str, Any]:
        await self._ensure()
        page = self._session.get_current_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        el = page.query_selector(selector)
        html = await el.inner_html() if el else ""
        return {"html": html, "selector": selector}

    async def close(self) -> dict[str, Any]:
        if self._session:
            with contextlib.suppress(Exception):
                await self._session.close_page()
            self._session = None
        self._initialized = False
        return {"success": True, "session": self.name}

    async def run_task(self, task: str, max_steps: int = 20) -> dict[str, Any]:
        await self._ensure()
        self._agent.task = task
        result = await self._agent.run(max_steps=max_steps)
        fr = result.final_result() if hasattr(result, "final_result") else str(result)
        return {"success": True, "result": fr or "Task completed", "steps": max_steps}


# ── Session registry ───────────────────────────────────────────────────────

_sessions: dict[str, BrowserSessionWrapper] = {}


def _get_session(name: str = "default") -> BrowserSessionWrapper:
    if name not in _sessions:
        _sessions[name] = BrowserSessionWrapper(name=name)
    return _sessions[name]


# ── MCP Tools ───────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="browser_open",
            description="Open a URL in the browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "session": {"type": "string", "default": "default"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="browser_click",
            description="Click an element by CSS selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "session": {"type": "string", "default": "default"},
                },
                "required": ["selector"],
            },
        ),
        Tool(
            name="browser_fill",
            description="Fill an input field by CSS selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "value": {"type": "string"},
                    "session": {"type": "string", "default": "default"},
                },
                "required": ["selector", "value"],
            },
        ),
        Tool(
            name="browser_scroll",
            description="Scroll the page by pixels",
            inputSchema={
                "type": "object",
                "properties": {
                    "pixels": {"type": "integer", "default": 300},
                    "session": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="browser_wait",
            description="Wait for seconds",
            inputSchema={
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "default": 1.0},
                    "session": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="browser_screenshot",
            description="Take a screenshot and save to path",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "session": {"type": "string", "default": "default"},
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="browser_get_text",
            description="Get text from element or body",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "default": "body"},
                    "session": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="browser_get_html",
            description="Get inner HTML from element or body",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "default": "body"},
                    "session": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="browser_close",
            description="Close the browser session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session": {"type": "string", "default": "default"},
                },
            },
        ),
        Tool(
            name="browser_run_task",
            description="Run autonomous browser task powered by MiniMax",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "max_steps": {"type": "integer", "default": 20},
                    "session": {"type": "string", "default": "default"},
                },
                "required": ["task"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    session_name = arguments.pop("session", "default")
    session = _get_session(session_name)

    try:
        if name == "browser_open":
            result = await session.open(arguments["url"])
        elif name == "browser_click":
            result = await session.click(arguments["selector"])
        elif name == "browser_fill":
            result = await session.fill(arguments["selector"], arguments["value"])
        elif name == "browser_scroll":
            result = await session.scroll(arguments.get("pixels", 300))
        elif name == "browser_wait":
            result = await session.wait(arguments.get("seconds", 1.0))
        elif name == "browser_screenshot":
            result = await session.screenshot(arguments["path"])
        elif name == "browser_get_text":
            result = await session.get_text(arguments.get("selector", "body"))
        elif name == "browser_get_html":
            result = await session.get_html(arguments.get("selector", "body"))
        elif name == "browser_close":
            result = await session.close()
        elif name == "browser_run_task":
            result = await session.run_task(arguments["task"], arguments.get("max_steps", 20))
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]


# ── Main ────────────────────────────────────────────────────────────────────

async def main():
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


if __name__ == "__main__":
    asyncio.run(main())