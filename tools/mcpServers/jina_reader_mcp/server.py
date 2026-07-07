#!/usr/bin/env python3
"""
Jina Reader MCP Server — LLM-optimized web content.

Converts any URL into clean markdown via https://r.jina.ai and provides
web search via https://s.jina.ai. Optimized for LLM consumption:
clean markdown, no ads, no navigation, just the content.

Provides:
  jina_read         — Convert URL → clean markdown (or HTML/text/screenshot)
  jina_search       — Search web → top 5 results as markdown
  jina_read_json    — Read URL → structured JSON (title, content, url, etc.)
  jina_batch        — Batch-read multiple URLs concurrently
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Sequence

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

APP_NAME = "jina-reader-mcp"
VERSION = "1.0.0"

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(APP_NAME)

server = Server(APP_NAME)

# Default endpoints — can override with env vars for self-hosted instances
R_JINA_AI = os.environ.get("JINA_READER_URL", "https://r.jina.ai")
S_JINA_AI = os.environ.get("JINA_SEARCH_URL", "https://s.jina.ai")

# Optional API key for auth'd requests (higher quotas, proxy access)
API_KEY = os.environ.get("JINA_API_KEY", "")


def _headers(**overrides: str) -> dict[str, str]:
    """Build request headers, merging defaults with overrides."""
    hdrs: dict[str, str] = {
        "Accept": "text/markdown",
        "X-Retain-Images": "none",
        "X-Retain-Links": "none",
        "X-No-Cache": "false",
    }
    if API_KEY:
        hdrs["Authorization"] = f"Bearer {API_KEY}"
    hdrs.update({k: v for k, v in overrides.items() if v is not None})
    return hdrs


def _truncate(text: str, max_len: int = 10000) -> str:
    if len(text) <= max_len:
        return text
    half = max_len // 2
    return text[:half] + f"\n\n... [truncated: {len(text) - max_len} chars] ...\n\n" + text[-half:]


# ── Tool definitions ────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="jina_read",
            description=(
                "Convert a URL into LLM-friendly clean markdown. "
                "Strips ads, navigation, and clutter — returns only the content. "
                "Supports web pages, PDFs, and Office documents. "
                "Use for: research, fact-checking, reading articles, documentation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to read and convert to markdown"},
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "html", "text", "screenshot", "frontmatter"],
                        "description": "Output format",
                        "default": "markdown",
                    },
                    "engine": {
                        "type": "string",
                        "enum": ["auto", "browser", "curl"],
                        "description": "Rendering engine: auto (default), browser (headless Chrome), curl (lightweight)",
                        "default": "auto",
                    },
                    "no_cache": {
                        "type": "boolean",
                        "description": "Bypass cached response",
                        "default": False,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max wait in seconds (max 180)",
                        "default": 30,
                    },
                    "target_selector": {
                        "type": "string",
                        "description": "CSS selector to scope content extraction (e.g. 'article.main', '#content')",
                    },
                    "wait_for_selector": {
                        "type": "string",
                        "description": "Wait for this CSS selector before returning (for SPA/dynamic content)",
                    },
                    "retain_images": {
                        "type": "string",
                        "enum": ["all", "none", "alt"],
                        "description": "Control image output: none (default), all, or alt (alt text only)",
                        "default": "none",
                    },
                    "retain_links": {
                        "type": "string",
                        "enum": ["all", "none", "text"],
                        "description": "Control link output: none (default), all, or text (keep link text)",
                        "default": "none",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Trim response to this many tokens",
                    },
                    "preset": {
                        "type": "string",
                        "enum": ["reader", "index", "research", "agent", "spider"],
                        "description": "Pre-packaged config bundle for different use cases",
                    },
                    "proxy": {
                        "type": "string",
                        "description": "Use hosted proxy pool: 'auto' (requires API key), or a custom proxy URL",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="jina_search",
            description=(
                "Search the web and return top results as clean markdown. "
                "Each result is fetched through the same Reader pipeline — "
                "so you get full page content, not just snippets. "
                "Use for: web research, finding sources, fact verification."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "site": {
                        "type": "string",
                        "description": "Restrict search to a domain (e.g. 'arxiv.org')",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "html", "text"],
                        "description": "Output format",
                        "default": "markdown",
                    },
                    "no_cache": {
                        "type": "boolean",
                        "description": "Bypass cached results",
                        "default": False,
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Trim each result to this many tokens",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="jina_read_json",
            description=(
                "Convert a URL into structured JSON. Returns title, content, url, "
                "and metadata in a machine-parseable format. "
                "Use when you need programmatic access to the extracted content."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to read"},
                    "engine": {
                        "type": "string",
                        "enum": ["auto", "browser", "curl"],
                        "default": "auto",
                    },
                    "no_cache": {"type": "boolean", "default": False},
                    "timeout": {"type": "integer", "default": 30},
                    "retain_images": {
                        "type": "string",
                        "enum": ["all", "none", "alt"],
                        "default": "none",
                    },
                    "retain_links": {
                        "type": "string",
                        "enum": ["all", "none", "text"],
                        "default": "none",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="jina_batch",
            description=(
                "Read multiple URLs in a single call. Each URL is fetched "
                "concurrently through the Reader pipeline. "
                "Use for batch research, comparing multiple sources, documentation scraping."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "URLs to read (max 10)",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "text"],
                        "default": "markdown",
                    },
                    "no_cache": {"type": "boolean", "default": False},
                    "max_concurrent": {
                        "type": "integer",
                        "description": "Maximum concurrent fetches",
                        "default": 5,
                    },
                },
                "required": ["urls"],
            },
        ),
    ]


# ── HTTP helpers ───────────────────────────────────────────────────────────

def _normalize_url(target: str) -> str:
    """Ensure the URL has a scheme."""
    target = target.strip()
    if not target.startswith(("http://", "https://")):
        target = "https://" + target
    return target


async def _read_url(url: str, **kwargs) -> str:
    """Call r.jina.ai and return the response."""
    target = _normalize_url(url)
    headers = _headers(
        X_Respond_With=kwargs.get("format"),
        X_Engine=kwargs.get("engine"),
        X_No_Cache="true" if kwargs.get("no_cache") else None,
        X_Timeout=str(kwargs.get("timeout", 30)),
        X_Target_Selector=kwargs.get("target_selector"),
        X_Wait_For_Selector=kwargs.get("wait_for_selector"),
        X_Retain_Images=kwargs.get("retain_images"),
        X_Retain_Links=kwargs.get("retain_links"),
        X_Max_Tokens=str(kwargs.get("max_tokens")) if kwargs.get("max_tokens") else None,
        X_Preset=kwargs.get("preset"),
        X_Proxy=kwargs.get("proxy"),
    )

    async with httpx.AsyncClient(timeout=kwargs.get("timeout", 30) + 5, follow_redirects=True) as client:
        try:
            r = await client.get(f"{R_JINA_AI}/{target}", headers=headers)
            r.raise_for_status()
            return r.text
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500] if exc.response.text else ""
            return f"Error {exc.response.status_code} from Reader: {body}"
        except httpx.TimeoutException:
            return f"Timeout reading {target} (>{kwargs.get('timeout', 30)}s)"
        except Exception as exc:
            return f"Reader error: {exc}"


async def _read_url_json(url: str, **kwargs) -> dict[str, Any]:
    """Call r.jina.ai with JSON accept header."""
    target = _normalize_url(url)
    headers = _headers(
        Accept="application/json",
        X_Engine=kwargs.get("engine"),
        X_No_Cache="true" if kwargs.get("no_cache") else None,
        X_Timeout=str(kwargs.get("timeout", 30)),
        X_Retain_Images=kwargs.get("retain_images"),
        X_Retain_Links=kwargs.get("retain_links"),
    )

    async with httpx.AsyncClient(timeout=kwargs.get("timeout", 30) + 5, follow_redirects=True) as client:
        try:
            r = await client.get(f"{R_JINA_AI}/{target}", headers=headers)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            return {"url": target, "error": str(exc)}


async def _search(query: str, **kwargs) -> str:
    """Call s.jina.ai and return the response."""
    site = kwargs.get("site")
    query_str = f"site:{site} {query}" if site else query

    headers = _headers(
        X_Respond_With=kwargs.get("format"),
        X_No_Cache="true" if kwargs.get("no_cache") else None,
        X_Max_Tokens=str(kwargs.get("max_tokens")) if kwargs.get("max_tokens") else None,
    )

    from urllib.parse import quote
    encoded = quote(query_str)

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        try:
            r = await client.get(f"{S_JINA_AI}/{encoded}", headers=headers)
            r.raise_for_status()
            return r.text
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500] if exc.response.text else ""
            return f"Error {exc.response.status_code} from Search: {body}"
        except httpx.TimeoutException:
            return f"Timeout searching '{query}' (>{60}s)"
        except Exception as exc:
            return f"Search error: {exc}"


# ── Call dispatcher ────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    try:
        if name == "jina_read":
            url = arguments["url"]
            result = await _read_url(url, **arguments)
            result = _truncate(result, 10000)
            meta = f"# Jina Reader: {url}\n\n"
            return [TextContent(type="text", text=meta + result)]

        elif name == "jina_search":
            query = arguments["query"]
            result = await _search(query, **arguments)
            result = _truncate(result, 15000)
            site_part = f" (site: {arguments.get('site')})" if arguments.get("site") else ""
            meta = f"# Jina Search: {query}{site_part}\n\n"
            return [TextContent(type="text", text=meta + result)]

        elif name == "jina_read_json":
            url = arguments["url"]
            result = await _read_url_json(url, **arguments)
            # Truncate content field if present
            if isinstance(result, dict) and "content" in result:
                result["content"] = _truncate(result["content"], 8000)
            meta = {"tool": "jina_read_json", "url": url}
            if "error" in result:
                meta["error"] = result["error"]
            output = {"meta": meta, "data": result}
            return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

        elif name == "jina_batch":
            urls = arguments["urls"][:10]
            max_concurrent = arguments.get("max_concurrent", 5)
            sem = asyncio.Semaphore(max_concurrent)

            async def bounded(u: str) -> dict[str, Any]:
                async with sem:
                    text = await _read_url(u, format=arguments.get("format", "markdown"), no_cache=arguments.get("no_cache", False))
                    return {"url": u, "content": _truncate(text, 5000), "length": len(text)}

            results = await asyncio.gather(*[bounded(u) for u in urls], return_exceptions=True)
            parts = [f"# Batch Read: {len(urls)} URLs\n"]
            for item in results:
                if isinstance(item, dict):
                    parts.append(f"\n## {item['url']}\n\n{item['content']}\n")
                elif isinstance(item, BaseException):
                    parts.append(f"\n## Error\n\n{str(item)}\n")
            return [TextContent(type="text", text="\n".join(parts))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "tool": name}))]


# ── Entry point ─────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
