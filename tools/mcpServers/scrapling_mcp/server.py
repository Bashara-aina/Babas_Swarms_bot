#!/usr/bin/env python3
"""Scrapling MCP Server — adaptive web scraping for AI agents."""

from __future__ import annotations

import json
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

APP_NAME = "scrapling-mcp"
VERSION = "1.1.0"

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(APP_NAME)

server = Server(APP_NAME)


def _truncate(text: str, max_len: int = 8000) -> str:
    if len(text) <= max_len:
        return text
    half = max_len // 2
    return text[:half] + f"\n\n... [truncated: {len(text) - max_len} chars] ...\n\n" + text[-half:]


def _extract_summary(response) -> dict[str, Any]:
    """Extract attrs from a Scrapling v0.4.9 Response object."""
    body = getattr(response, "body", b"")
    return {
        "url": getattr(response, "url", ""),
        "status": getattr(response, "status", 0),
        "html_length": len(body),
        "text_length": len(getattr(response, "get_all_text", lambda: "")()),
    }


def _get_html(response) -> str:
    """Get HTML string from a Scrapling v0.4.9 Response object."""
    html_content = getattr(response, "html_content", None)
    if html_content:
        return str(html_content)
    body = getattr(response, "body", None)
    if body:
        return body.decode("utf-8", errors="replace")
    return str(response)


def _get_text(response) -> str:
    """Get visible text from a Scrapling v0.4.9 Response object."""
    text = getattr(response, "text", None)
    if text:
        return str(text)
    return getattr(response, "get_all_text", lambda: "")()



@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="scrapling_fetch",
            description="Fast HTTP GET with TLS impersonation. Use for static pages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "impersonate": {
                        "type": "string",
                        "description": "Browser to impersonate",
                        "default": "chrome",
                    },
                    "http3": {"type": "boolean", "description": "Enable HTTP/3", "default": False},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                    "retries": {"type": "integer", "description": "Retry count", "default": 3},
                    "extract_text": {
                        "type": "boolean",
                        "description": "Extract visible text only",
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="scrapling_stealth",
            description="Stealth fetch with Cloudflare bypass. Use when scrapling_fetch gets blocked.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "headless": {"type": "boolean", "description": "Run headless", "default": True},
                    "solve_cloudflare": {
                        "type": "boolean",
                        "description": "Solve Cloudflare challenge",
                        "default": True,
                    },
                    "network_idle": {
                        "type": "boolean",
                        "description": "Wait for network idle",
                        "default": True,
                    },
                    "adaptive": {
                        "type": "boolean",
                        "description": "Adaptive mode for site redesigns",
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="scrapling_dynamic",
            description="Browser automation for JS-rendered pages. Waits for dynamic content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "wait_selector": {
                        "type": "string",
                        "description": "CSS selector to wait for",
                    },
                    "wait_time": {
                        "type": "integer",
                        "description": "Wait after page load (ms)",
                        "default": 2000,
                    },
                    "extract_text": {
                        "type": "boolean",
                        "description": "Extract visible text only",
                        "default": True,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Page load timeout (ms)",
                        "default": 30000,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="scrapling_extract",
            description="Fetch URL + extract with CSS/XPath. One-call fetch-and-parse.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "css": {
                        "type": "string",
                        "description": "CSS selector (::text, ::attr(name) syntax)",
                    },
                    "xpath": {
                        "type": "string",
                        "description": "XPath selector (alternative to css)",
                    },
                    "all_matches": {
                        "type": "boolean",
                        "description": "Return all matches vs first only",
                        "default": True,
                    },
                    "impersonate": {
                        "type": "string",
                        "description": "Browser to impersonate",
                        "default": "chrome",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="scrapling_extract_multi",
            description="Batch extract across multiple URLs concurrently. Same CSS/XPath applied to all.",
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of target URLs",
                    },
                    "css": {
                        "type": "string",
                        "description": "CSS selector (::text, ::attr(name) syntax)",
                    },
                    "max_concurrent": {
                        "type": "integer",
                        "description": "Max concurrent fetches",
                        "default": 5,
                    },
                },
                "required": ["urls"],
            },
        ),
        Tool(
            name="scrapling_parse",
            description="Parse HTML locally (no network) with CSS/XPath. Offline extraction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "html": {"type": "string", "description": "HTML content"},
                    "css": {
                        "type": "string",
                        "description": "CSS selector (::text, ::attr(name) syntax)",
                    },
                    "xpath": {
                        "type": "string",
                        "description": "XPath selector (alternative to css)",
                    },
                    "all": {
                        "type": "boolean",
                        "description": "Return all matches vs first only",
                        "default": True,
                    },
                },
                "required": ["html"],
            },
        ),
        Tool(
            name="scrapling_find_selectors",
            description="Generate CSS selectors from HTML + target text. Ranked by robustness.",
            inputSchema={
                "type": "object",
                "properties": {
                    "html": {"type": "string", "description": "HTML content"},
                    "target_text": {
                        "type": "string",
                        "description": "Text to find selectors for",
                    },
                    "max_selectors": {
                        "type": "integer",
                        "description": "Max selectors to return",
                        "default": 3,
                    },
                },
                "required": ["html", "target_text"],
            },
        ),
    ]



async def _do_fetch(url: str, **kwargs) -> dict[str, Any]:
    from scrapling.fetchers import Fetcher

    result = Fetcher.get(
        url,
        impersonate=kwargs.get("impersonate", "chrome"),
        http3=kwargs.get("http3", False),
        timeout=kwargs.get("timeout", 30),
        retries=kwargs.get("retries", 3),
    )
    info = _extract_summary(result)
    info["html"] = _get_html(result)
    if kwargs.get("extract_text"):
        info["text"] = _get_text(result)
    return info


async def _do_stealth(url: str, **kwargs) -> dict[str, Any]:
    from scrapling.fetchers import StealthyFetcher

    result = StealthyFetcher.fetch(
        url,
        headless=kwargs.get("headless", True),
        solve_cloudflare=kwargs.get("solve_cloudflare", True),
        network_idle=kwargs.get("network_idle", True),
    )
    info = _extract_summary(result)
    info["html"] = _get_html(result)
    return info


async def _do_dynamic(url: str, **kwargs) -> dict[str, Any]:
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
        info["text"] = _get_text(result)
    info["html"] = _get_html(result)
    return info


async def _do_extract(url: str, **kwargs) -> dict[str, Any]:
    from scrapling.fetchers import Fetcher
    from scrapling.parser import Selector

    result = Fetcher.get(url, impersonate=kwargs.get("impersonate", "chrome"))
    html = _get_html(result)
    page = Selector(html)

    all_matches = kwargs.get("all_matches", True)
    css = kwargs.get("css")
    xpath_sel = kwargs.get("xpath")

    extracted = []
    if css:
        elements = page.css(css)
        if all_matches:
            extracted = [str(e.get()) if hasattr(e, "get") else str(e) for e in elements]
        else:
            e = elements[0] if elements else None
            extracted = [str(e.get()) if e is not None and hasattr(e, "get") else ""] if e is not None else []

    if xpath_sel:
        elements = page.xpath(xpath_sel)
        names = []
        for e in elements:
            val = str(e.get()) if hasattr(e, "get") else str(e)
            names.append(val)
        extracted = names if all_matches else (names[:1] if names else [])

    info = _extract_summary(result)
    info["extracted"] = extracted
    info["count"] = len(extracted)
    return info


async def _do_extract_multi(urls: list[str], **kwargs) -> list[dict[str, Any]]:
    import asyncio
    from scrapling.fetchers import Fetcher
    from scrapling.parser import Selector

    css = kwargs.get("css")
    max_concurrent = kwargs.get("max_concurrent", 5)

    async def fetch_one(session_url: str) -> dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: Fetcher.get(session_url, impersonate="chrome"))
            info = _extract_summary(result)
            if css:
                page = Selector(_get_html(result))
                elements = page.css(css)
                info["extracted"] = [str(e.get()) if hasattr(e, "get") else str(e) for e in elements]
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
    from scrapling.parser import Selector

    page = Selector(html)
    css = kwargs.get("css")
    xpath_sel = kwargs.get("xpath")
    all_matches = kwargs.get("all", True)

    result: dict[str, Any] = {"parsed_length": len(html)}

    if css:
        elements = page.css(css)
        if all_matches:
            result["extracted"] = [str(e.get()) if hasattr(e, "get") else str(e) for e in elements]
        else:
            e = elements[0] if elements else None
            result["extracted"] = [str(e.get()) if e is not None and hasattr(e, "get") else ""] if e is not None else []
        result["count"] = len(result["extracted"])

    if xpath_sel:
        elements = page.xpath(xpath_sel)
        vals = []
        for e in elements:
            val = str(e.get()) if hasattr(e, "get") else str(e)
            vals.append(val)
        result["extracted_xpath"] = vals if all_matches else (vals[:1] if vals else [])
        result["count_xpath"] = len(result["extracted_xpath"])

    return result


async def _do_find_selectors(html: str, target_text: str, **kwargs) -> dict[str, Any]:
    from scrapling.parser import Selector

    page = Selector(html)
    max_selectors = kwargs.get("max_selectors", 3)

    target_el = page.find_by_text(target_text, first_match=True, partial=True)
    if target_el is None:
        return {"found": False, "target_text": target_text, "selectors": []}

    selectors = []
    candidates = [target_el]
    for i, el in enumerate(candidates[:max_selectors]):
        selector_info = {}
        tag = el.tag if hasattr(el, "tag") else "unknown"
        attrs = el.attrib if hasattr(el, "attrib") else {}
        classes = attrs.get("class", "")
        selector_info["tag"] = tag
        selector_info["classes"] = classes
        selector_info["id"] = attrs.get("id", "")
        selector_info["text_preview"] = str(el.get_all_text())[:100] if hasattr(el, "get_all_text") else str(el.text)[:100]

        css_sel = getattr(el, "generate_css_selector", None)
        if css_sel:
            selector_info["css_selector"] = css_sel
        else:
            css_parts = [tag]
            if attrs.get("id"):
                css_parts.append(f"#{attrs['id']}")
            if classes:
                css_parts.append(f".{classes.replace(' ', '.')}" if isinstance(classes, str) else "".join(f".{c}" for c in classes))
            selector_info["css_selector"] = "".join(css_parts)
        selectors.append(selector_info)

    return {
        "found": True,
        "target_text": target_text,
        "selectors": selectors[:max_selectors],
        "note": "Selectors may need adjustment. Prefer ID-based selectors when available.",
    }



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
        args = dict(arguments)
        if name == "scrapling_extract_multi":
            urls = args.pop("urls")
            result = await handler(urls, **args)
        elif name in ("scrapling_parse", "scrapling_find_selectors"):
            html = args.pop("html")
            result = await handler(html, **args)
        elif name in ("scrapling_fetch", "scrapling_stealth", "scrapling_dynamic", "scrapling_extract"):
            url = args.pop("url")
            result = await handler(url, **args)
        else:
            url = args.pop("url", "")
            result = await handler(url, **args)

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


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
