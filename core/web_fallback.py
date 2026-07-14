"""
core/web_fallback.py — Automatic web tool fallback when API credits exhausted.

Detects credit exhaustion, rate limiting, and quota errors from primary
web tools (Firecrawl, Exa) and auto-reroutes to free/local alternatives
(Jina Reader, Crawl4AI, Scrapling, SearXNG).

Fallback chains (in priority order):
  SEARCH:  firecrawl_search → searxng_web_search → jina_search → exa_web_search
  FETCH:   firecrawl_scrape → crawl4ai_crawl → jina_read → scrapling_fetch
  CRAWL:   firecrawl_crawl  → crawl4ai_crawl → searxng_web_search
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── Credit exhaustion detection patterns ──────────────────────────────────────
# These patterns are matched against tool result strings (lowercase).
# When ANY pattern matches, we trigger fallback to avoid aborting the task.

CREDIT_EXHAUSTED_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"api\s*credits?\s*(are\s*)?exhausted",
        r"insufficient\s*(api\s*)?credits?",
        r"credit\s*limit\s*reached",
        r"quota\s*exceeded",
        r"rate\s*limit\s*exceeded",
        r"too\s*many\s*requests",
        r"429\s*(too\s*many\s*requests|rate\s*limit)",
        r"upgrade\s*your\s*plan",
        r"payment\s*required",
        r"billing\s*(required|threshold)",
        r"account\s*.*suspended",
        r"free\s*tier\s*limit",
        r"monthly\s*quota",
        r"request\s*limit\s*reached",
        r"api\s*key\s*.*(exhausted|depleted|limit)",
        r"insufficient.*quota",
    ]
]

# ── Tool family classification ───────────────────────────────────────────────

# Maps a tool name to its family: "search", "fetch", or "crawl"
TOOL_FAMILY: dict[str, str] = {
    # Firecrawl
    "firecrawl_search": "search",
    "firecrawl_scrape": "fetch",
    "firecrawl_crawl": "crawl",
    "firecrawl_map": "crawl",
    "firecrawl_agent": "search",
    "firecrawl_extract": "fetch",
    "firecrawl_parse": "fetch",
    # Exa
    "exa_web_search_exa": "search",
    "exa_web_fetch_exa": "fetch",
    # Crawl4AI
    "crawl4ai_crawl4ai_crawl": "crawl",
    "crawl4ai_crawl4ai_scrape": "fetch",
    # Jina Reader
    "jina_jina_search": "search",
    "jina_jina_read": "fetch",
    "jina_jina_read_json": "fetch",
    "jina_jina_batch": "fetch",
    # Scrapling
    "scrapling_scrapling_fetch": "fetch",
    "scrapling_scrapling_scrape": "fetch",
    "scrapling_scrapling_crawl": "crawl",
    # SearXNG
    "searxng_web_search": "search",
    "searxng_deep_crawl": "crawl",
}

# ── Fallback chains ───────────────────────────────────────────────────────────
# Ordered: primary → fallback1 → fallback2 → ...
# Each fallback includes: (tool_name, arg_mapping_fn_key)

FALLBACK_CHAINS: dict[str, list[str]] = {
    "search": [
        "jina_jina_search",         # Free tier, s.jina.ai
        "searxng_web_search",       # Free, local metasearch engine
    ],
    "fetch": [
        "jina_jina_read",           # Free URL→markdown converter
        "crawl4ai_crawl4ai_crawl",  # Local browser-based crawler
        "scrapling_scrapling_fetch",  # TLS-impersonated HTTP fetch
    ],
    "crawl": [
        "jina_jina_read",           # Free URL→markdown converter (single-page)
        "crawl4ai_crawl4ai_crawl",  # Local browser-based crawler
        "searxng_web_search",       # Free metasearch fallback
    ],
}

# ── Argument mapping: translate args from one tool to another ─────────────────
# Each function takes the original tool_name and args dict, returns
# a (fallback_tool_name, mapped_args) tuple or None if mapping impossible.


def _map_search_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Map search tool args to a standard format."""
    mapped: dict[str, Any] = {}
    # Extract query from various search tool arg shapes
    query = args.get("query") or args.get("q") or args.get("search_query") or ""
    if not query and "prompt" in args:
        query = args["prompt"]
    mapped["query"] = query
    return mapped


def _map_fetch_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Map fetch/scrape tool args to a standard format."""
    mapped: dict[str, Any] = {}
    # Extract URL from various fetch tool arg shapes
    url = args.get("url") or args.get("urls") or ""
    if isinstance(url, list):
        url = url[0] if url else ""
    if not url and "link" in args:
        url = args["link"]
    mapped["url"] = url
    # Copy over optional params
    for k in ("max_length", "maxChars", "maxCharacters", "timeout", "word_count_threshold"):
        if k in args:
            mapped["max_length"] = args[k]
    return mapped


def _map_jina_read_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Map args specifically for jina_read."""
    mapped = _map_fetch_args(tool_name, args)
    # jina_read uses 'url' key
    return mapped


def _map_crawl_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Map crawl tool args."""
    mapped = _map_fetch_args(tool_name, args)
    if "max_pages" in args:
        mapped["max_pages"] = args["max_pages"]
    if "depth" in args or "maxDepth" in args or "max_depth" in args:
        mapped["depth"] = args.get("depth") or args.get("maxDepth") or args.get("max_depth")
    return mapped


def map_args_for_fallback(
    original_tool: str, fallback_tool: str, args: dict[str, Any]
) -> dict[str, Any] | None:
    """Map arguments from original_tool to fallback_tool.

    Returns None if the mapping is impossible (e.g., missing required fields).
    """
    family = TOOL_FAMILY.get(original_tool)

    if fallback_tool.startswith("jina_"):
        if family == "search":
            return _map_search_args(original_tool, args)
        return _map_jina_read_args(original_tool, args)

    if fallback_tool.startswith("crawl4ai_"):
        if family == "search":
            return _map_search_args(original_tool, args)
        return _map_crawl_args(original_tool, args)

    if fallback_tool.startswith("scrapling_"):
        return _map_fetch_args(original_tool, args)

    if fallback_tool.startswith("searxng_"):
        return _map_search_args(original_tool, args)

    # Generic fallback
    if family == "search":
        return _map_search_args(original_tool, args)
    return _map_fetch_args(original_tool, args)


# ── Detection ─────────────────────────────────────────────────────────────────


def is_credit_exhausted(result: str) -> bool:
    """Check if a tool result indicates API credit exhaustion.

    Args:
        result: Tool result string (JSON or plain text).

    Returns:
        True if the result indicates credit exhaustion.
    """
    if not result:
        return False

    result_lower = result.lower()

    # Try parsing as JSON first — check error fields
    try:
        data = json.loads(result)
        if isinstance(data, dict):
            error_msg = data.get("error", "") or data.get("message", "") or ""
            if error_msg:
                result_lower = f"{result_lower} {error_msg.lower()}"
    except (json.JSONDecodeError, TypeError):
        pass

    return any(pattern.search(result_lower) for pattern in CREDIT_EXHAUSTED_PATTERNS)


def is_web_tool(tool_name: str) -> bool:
    """Check if a tool is a web tool that has fallback alternatives."""
    # Strip mcp__ prefix if present (Claude Code adds this)
    clean_name = tool_name.replace("mcp__", "", 1)
    # Also strip the server prefix to get the base tool name
    for prefix in ("firecrawl_", "exa_", "crawl4ai_", "jina_", "scrapling_", "searxng_"):
        if clean_name.startswith(prefix):
            return True
    return False


def get_fallback_chain(tool_name: str) -> list[str]:
    """Get the fallback chain for a web tool.

    Returns:
        Ordered list of alternative tool names to try.
    """
    clean_name = tool_name.replace("mcp__", "", 1)
    family = TOOL_FAMILY.get(clean_name)
    if not family:
        # Try matching by prefix — look for exact prefix match
        for known, fam in TOOL_FAMILY.items():
            known_prefix = known.split("_")[0]
            if clean_name.startswith(known_prefix):
                # Double-check: the second segment often disambiguates (search vs fetch)
                # For exa_*, check if the second word is in clean_name
                parts = known.split("_")
                if len(parts) > 1 and parts[1] in ("search", "fetch", "crawl"):
                    if parts[1] in clean_name:
                        family = fam
                        break
                else:
                    family = fam
                    break
    if not family:
        # Default: try fetch chain
        family = "fetch"

    chain = FALLBACK_CHAINS.get(family, FALLBACK_CHAINS["fetch"])
    # Log which chain we're using
    logger.info(
        "Web fallback: %s (family=%s) → chain: %s",
        tool_name, family, " → ".join(chain)
    )
    return list(chain)  # Return a copy
