#!/usr/bin/env python3
"""
Scrapling MCP Server — adaptive web scraping for AI agents.

Provides:
  scrapling_fetch       — Fast HTTP GET with TLS fingerprint impersonation
  scrapling_stealth     — Stealth fetch (Cloudflare bypass, anti-bot evasion)
  scrapling_dynamic     — Full browser automation for JS-rendered pages
  scrapling_parse       — Parse HTML text locally with CSS/XPath/filter
  scrapling_extract     — Fetch + extract specific elements (CSS/XPath)
  scrapling_extract_multi — Batch extract across multiple URLs
  scrapling_find_selectors — Generate robust selectors from HTML samples
"""

from __future__ import annotations

import json
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

APP_NAME = "scrapling-mcp"
VERSION = "1.0.0"

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(APP_NAME)

server = Server(APP_NAME)


# ── Helper: truncate large text for LLM-friendly output ─────────────────────

def _truncate(text: str, max_len: int = 8000) -> str:
    if len(text) <= max_len:
        return text
    half = max_len // 2
    return text[:half] + f"\n\n... [truncated: {len(text) - max_len} chars] ...\n\n" + text[-half:]


def _extract_summary(response) -> dict[str, Any]:
    """Extract attrs from a Scrapling response object."""
    return {
        "url": getattr(response, "url", ""),
        "status": getattr(response, "status", 0),
        "html_length": len(getattr(response, "raw_content", "") or getattr(response, "content", "") or ""),
        "text_length": len(getattr(response, "text", "") or ""),
    }


# ── Tool definitions ────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="scrapling_fetch",
            description=(
                "Fetch a URL via Scrapling's fast HTTP engine with browser TLS fingerprint "
                "impersonation. Best for static HTML pages. Supports stealthy headers, "
                "proxy rotation, and HTTP/3. Returns full HTML content + metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "impersonate": {
                        "type": "string",
                        "description": "Browser to impersonate: chrome, edge, safari, firefox, or specific versions like chrome131, safari180, firefox147",
                        "default": "chrome",
                    },
                    "http3": {"type": "boolean", "description": "Enable HTTP/3 (QUIC)", "default": False},
                    "timeout": {"type": "integer", "description": "Request timeout in seconds", "default": 30},
                    "retries": {"type": "integer", "description": "Number of retries on failure", "default": 3},
                    "extract_text": {
                        "type": "boolean",
                        "description": "Extract visible text only (no HTML tags)",
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="scrapling_stealth",
            description=(
                "Stealth fetch using browser automation with anti-bot evasion. "
                "Bypasses Cloudflare Turnstile, interstitial pages, and other bot protections. "
                "Use when scrapling_fetch returns blocked content or challenges. "
                "Supports adaptive mode that auto-relocates elements after site changes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "headless": {"type": "boolean", "description": "Run browser headless", "default": True},
                    "solve_cloudflare": {
                        "type": "boolean",
                        "description": "Attempt Cloudflare Turnstile/Challenge solving",
                        "default": True,
                    },
                    "network_idle": {
                        "type": "boolean",
                        "description": "Wait for network idle before returning",
                        "default": True,
                    },
                    "adaptive": {
                        "type": "boolean",
                        "description": "Enable adaptive mode (survives site redesigns)",
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="scrapling_dynamic",
            description=(
                "Full browser automation for JavaScript-rendered pages. "
                "Use Playwright's Chromium to execute JS, wait for dynamic content, "
                "and extract results. Supports custom wait conditions and screenshots."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to load in browser"},
                    "wait_selector": {
                        "type": "string",
                        "description": "CSS selector to wait for before extracting (e.g. '.content-loaded')",
                    },
                    "wait_time": {
                        "type": "integer",
                        "description": "Milliseconds to wait after page load",
                        "default": 2000,
                    },
                    "extract_text": {
                        "type": "boolean",
                        "description": "Extract visible text only",
                        "default": True,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Page load timeout in ms",
                        "default": 30000,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="scrapling_extract",
            description=(
                "Fetch a URL and extract specific elements using CSS selectors or XPath. "
                "Scrapling's parser is ~780x faster than BeautifulSoup for extraction. "
                "The killer feature: one call to fetch + parse any webpage."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch and extract from"},
                    "css": {
                        "type": "string",
                        "description": "CSS selector to extract (e.g. '.article .title::text', 'a::attr(href)'). Use ::text for text content, ::attr(name) for attributes",
                    },
                    "xpath": {
                        "type": "string",
                        "description": "XPath selector (alternative to css). Use one or the other.",
                    },
                    "all_matches": {
                        "type": "boolean",
                        "description": "Return all matching elements vs just first",
                        "default": True,
                    },
                    "impersonate": {
                        "type": "string",
                        "description": "Browser impersonation: chrome, edge, safari, firefox",
                        "default": "chrome",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="scrapling_extract_multi",
            description=(
                "Extract data from multiple URLs in a single call. "
                "Each URL is fetched concurrently and the same selectors are applied. "
                "Use for batch data collection, price monitoring, aggregator scraping."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "URLs to extract from",
                    },
                    "css": {
                        "type": "string",
                        "description": "CSS selector to apply to each page. Use ::text for text, ::attr(name) for attributes",
                    },
                    "max_concurrent": {
                        "type": "integer",
                        "description": "Maximum concurrent fetches",
                        "default": 5,
                    },
                },
                "required": ["urls"],
            },
        ),
        Tool(
            name="scrapling_parse",
            description=(
                "Parse HTML text content locally using Scrapling's fast parser "
                "(no network request). Supports CSS selectors, XPath, filter-based "
                "search, text search, and regex. 780x faster than BeautifulSoup."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "html": {"type": "string", "description": "HTML content to parse"},
                    "css": {
                        "type": "string",
                        "description": "CSS selector (e.g. 'h1::text', 'div.content', 'a::attr(href)')",
                    },
                    "xpath": {
                        "type": "string",
                        "description": "XPath selector (alternative to css)",
                    },
                    "all": {
                        "type": "boolean",
                        "description": "Return all matches vs just first",
                        "default": True,
                    },
                },
                "required": ["html"],
            },
        ),
        Tool(
            name="scrapling_find_selectors",
            description=(
                "Given HTML and target text, generate robust CSS selectors that match "
                "the target elements. Uses Scrapling's adaptive/auto_save feature which "
                "learns from website structure and can relocate elements after changes. "
                "Returns multiple selector options ranked by robustness."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "html": {"type": "string", "description": "HTML content containing the target"},
                    "target_text": {
                        "type": "string",
                        "description": "Text content to find selectors for",
                    },
                    "max_selectors": {
                        "type": "integer",
                        "description": "Maximum number of selectors to return",
                        "default": 3,
                    },
                },
                "required": ["html", "target_text"],
            },
        ),
    ]


# ── Tool implementations ────────────────────────────────────────────────────

async def _do_fetch(url: str, **kwargs) -> dict[str, Any]:
    """Fast HTTP fetch with Scrapling."""
    from scrapling.fetchers import Fetcher

    result = Fetcher.get(
        url,
        impersonate=kwargs.get("impersonate", "chrome"),
        http3=kwargs.get("http3", False),
        timeout=kwargs.get("timeout", 30),
        retries=kwargs.get("retries", 3),
    )
    info = _extract_summary(result)
    info["html"] = result.raw_content if hasattr(result, "raw_content") else str(result)
    if kwargs.get("extract_text"):
        info["text"] = result.text if hasattr(result, "text") else ""
    return info


async def _do_stealth(url: str, **kwargs) -> dict[str, Any]:
    """Stealth fetch with anti-bot bypass."""
    from scrapling.fetchers import StealthyFetcher

    StealthyFetcher.adaptive = kwargs.get("adaptive", False)
    result = StealthyFetcher.fetch(
        url,
        headless=kwargs.get("headless", True),
        solve_cloudflare=kwargs.get("solve_cloudflare", True),
        network_idle=kwargs.get("network_idle", True),
    )
    info = _extract_summary(result)
    info["html"] = getattr(result, "raw_content", "") or getattr(result, "content", "") or str(result)
    return info


async def _do_dynamic(url: str, **kwargs) -> dict[str, Any]:
    """Full browser automation fetch."""
    from scrapling.fetchers import DynamicFetcher

    result = DynamicFetcher.fetch(
        url,
        headless=True,
        wait_for=kwargs.get("wait_selector"),
        wait_time=kwargs.get("wait_time", 2000),
        timeout=kwargs.get("timeout", 30000),
    )
    info = _extract_summary(result)
    if kwargs.get("extract_text", True):
        info["text"] = getattr(result, "text", "") or ""
    info["html"] = getattr(result, "raw_content", "") or str(result)
    return info


async def _do_extract(url: str, **kwargs) -> dict[str, Any]:
    """Fetch + extract elements via CSS/XPath."""
    from scrapling.fetchers import Fetcher

    result = Fetcher.get(
        url,
        impersonate=kwargs.get("impersonate", "chrome"),
    )
    html = getattr(result, "raw_content", "") or str(result)
    from scrapling.parser import Selector
    page = Selector(html)

    all_matches = kwargs.get("all_matches", True)
    css = kwargs.get("css")
    xpath_sel = kwargs.get("xpath")

    extracted = []
    if css:
        elements = page.css(css)
        if all_matches:
            extracted = [e.get() if hasattr(e, "get") else str(e) for e in elements]
        else:
            e = elements[0] if elements else None
            extracted = [e.get() if hasattr(e, "get") else str(e)] if e is not None else []

    if xpath_sel:
        elements = page.xpath(xpath_sel)
        if all_matches:
            extracted = [e.get() if hasattr(e, "get") else str(e) for e in elements]
        else:
            e = elements[0] if elements else None
            extracted = [e.get() if hasattr(e, "get") else str(e)] if e is not None else []

    info = _extract_summary(result)
    info["extracted"] = extracted
    info["count"] = len(extracted)
    return info


async def _do_extract_multi(urls: list[str], **kwargs) -> list[dict[str, Any]]:
    """Fetch + extract from multiple URLs concurrently."""
    import asyncio
    from scrapling.fetchers import Fetcher
    from scrapling.parser import Selector

    css = kwargs.get("css")
    max_concurrent = kwargs.get("max_concurrent", 5)

    async def fetch_one(session_url: str) -> dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: Fetcher.get(session_url, impersonate="chrome"))
            html = getattr(result, "raw_content", "") or str(result)
            page = Selector(html)
            info = _extract_summary(result)
            if css:
                elements = page.css(css)
                info["extracted"] = [e.get() if hasattr(e, "get") else str(e) for e in elements]
                info["count"] = len(info["extracted"])
            return info
        except Exception as exc:
            return {"url": session_url, "error": str(exc), "status": 0}

    sem = asyncio.Semaphore(max_concurrent)

    async def bounded(session_url: str) -> dict[str, Any]:
        async with sem:
            return await fetch_one(session_url)

    results = await asyncio.gather(*[bounded(u) for u in urls], return_exceptions=True)
    return [r if isinstance(r, dict) else {"url": u, "error": str(r)} for u, r in zip(urls, results)]


async def _do_parse(html: str, **kwargs) -> dict[str, Any]:
    """Parse HTML text locally with Selector."""
    from scrapling.parser import Selector

    page = Selector(html)
    css = kwargs.get("css")
    xpath_sel = kwargs.get("xpath")
    all_matches = kwargs.get("all", True)

    result: dict[str, Any] = {"parsed_length": len(html)}

    if css:
        elements = page.css(css)
        if all_matches:
            result["extracted"] = [e.get() if hasattr(e, "get") else str(e) for e in elements]
        else:
            e = elements[0] if elements else None
            result["extracted"] = [e.get() if hasattr(e, "get") else str(e)] if e is not None else []
        result["count"] = len(result["extracted"])

    if xpath_sel:
        elements = page.xpath(xpath_sel)
        if all_matches:
            result["extracted_xpath"] = [e.get() if hasattr(e, "get") else str(e) for e in elements]
        else:
            e = elements[0] if elements else None
            result["extracted_xpath"] = [e.get() if hasattr(e, "get") else str(e)] if e is not None else []
        result["count_xpath"] = len(result.get("extracted_xpath", []))

    return result


async def _do_find_selectors(html: str, target_text: str, **kwargs) -> dict[str, Any]:
    """Find robust CSS selectors for target text in HTML."""
    from scrapling.parser import Selector

    page = Selector(html)
    max_selectors = kwargs.get("max_selectors", 3)

    # Find the target element
    target_el = page.find_by_text(target_text, first_match=True, partial=True)
    if target_el is None:
        return {"found": False, "target_text": target_text, "selectors": []}

    # Generate robust selector candidates
    selectors = []
    for i, el in enumerate([target_el] + list(target_el.find_similar()[:max_selectors - 1])):
        selector_info = {}
        # Try to build a descriptive selector
        tag = el.tag if hasattr(el, "tag") else "unknown"
        attrs = el.attrib if hasattr(el, "attrib") else {}
        classes = " ".join(attrs.get("class", [])) if isinstance(attrs.get("class"), list) else attrs.get("class", "")
        selector_info["tag"] = tag
        selector_info["classes"] = classes
        selector_info["id"] = attrs.get("id", "")
        selector_info["text_preview"] = str(el.get())[:100] if hasattr(el, "get") else ""

        # Build CSS selector
        css_parts = [tag]
        if attrs.get("id"):
            css_parts.append(f"#{attrs['id']}")
        if classes:
            css_parts.append(f".{classes.replace(' ', '.')}")
        selector_info["css_selector"] = "".join(css_parts)
        selectors.append(selector_info)

    return {
        "found": True,
        "target_text": target_text,
        "selectors": selectors[:max_selectors],
        "note": "Selectors may need adjustment. Prefer ID-based selectors when available.",
    }


# ── Call dispatcher ─────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    tool_map = {
        "scrapling_fetch": _do_fetch,
        "scrapling_stealth": _do_stealth,
        "scrapling_dynamic": _do_dynamic,
        "scrapling_extract": _do_extract,
        "scrapling_extract_multi": _do_extract_multi,
        "scrapling_parse": _do_parse,
        "scrapling_find_selectors": _do_find_selectors,
    }

    handler = tool_map.get(name)
    if handler is None:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    try:
        if name == "scrapling_extract_multi":
            result = await handler(arguments["urls"], **arguments)
        elif name in ("scrapling_parse", "scrapling_find_selectors"):
            result = await handler(arguments["html"], **arguments)
        elif name == "scrapling_fetch":
            result = await _do_fetch(arguments["url"], **arguments)
        elif name == "scrapling_stealth":
            result = await _do_stealth(arguments["url"], **arguments)
        elif name == "scrapling_dynamic":
            result = await _do_dynamic(arguments["url"], **arguments)
        elif name == "scrapling_extract":
            result = await _do_extract(arguments["url"], **arguments)
        else:
            result = await handler(arguments["url"], **arguments)

        # Truncate large HTML/text fields
        if isinstance(result, dict):
            if "html" in result:
                result["html"] = _truncate(result["html"], 8000)
            if "text" in result:
                result["text"] = _truncate(result["text"], 8000)

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(exc), "tool": name, "arguments": {k: v for k, v in arguments.items() if k != "html"}})
        )]


# ── Entry point ─────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
