"""Browser-based scraping with CDP (browser-harness) and HTTP fallback.

Primary: browser-harness via CDP (headless Chrome with remote debugging).
Fallback: httpx + BeautifulSoup for simple pages.
Always uses the user's running Chrome — no separate browser process needed.

No firecrawl dependency. Replaces firecrawl-based scraping with pure CDP.
"""
from __future__ import annotations

import asyncio
import gzip
import logging
import os
import urllib.request
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── CDP browser-harness fallback chain ────────────────────────────────────────


async def _scrape_via_cdp(url: str, max_chars: int = 10000) -> tuple[str, str]:
    """Scrape using browser-harness CDP (user's running Chrome).

    Returns (content, source).
    """
    try:
        from tools.browser_harness.admin import ensure_daemon
        ensure_daemon()

        # Use the sync helpers via socket — run in thread to not block async
        import concurrent.futures

        def _sync_scrape() -> tuple[str, str]:
            import json
            import socket

            SOCK = f"/tmp/bu-{os.environ.get('BU_NAME', 'default')}.sock"

            def _send(req: dict) -> dict:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(SOCK)
                s.sendall((json.dumps(req) + "\n").encode())
                data = b""
                while not data.endswith(b"\n"):
                    chunk = s.recv(1 << 20)
                    if not chunk:
                        break
                    data += chunk
                s.close()
                r = json.loads(data)
                if "error" in r:
                    raise RuntimeError(r["error"])
                return r

            # Get current session (verifies daemon is running)
            _send({"meta": "session"}).get("session_id")

            # Create new tab for scraping
            tid = _send({"method": "Target.createTarget", "params": {"url": "about:blank"}})["result"]["targetId"]
            _send({"method": "Target.activateTarget", "params": {"targetId": tid}})
            new_sid = _send({"method": "Target.attachToTarget", "params": {"targetId": tid, "flatten": True}})["result"]["sessionId"]
            _send({"meta": "set_session", "session_id": new_sid})

            # Navigate
            _send({"method": "Page.navigate", "params": {"url": url}, "session_id": new_sid})

            # Wait for load
            for _ in range(50):
                r = _send({"method": "Runtime.evaluate", "params": {"expression": "document.readyState", "returnByValue": True}, "session_id": new_sid})
                if r.get("result", {}).get("result", {}).get("value") == "complete":
                    break
                import time
                time.sleep(0.3)

            # Extract content
            result = _send({
                "method": "Runtime.evaluate",
                "params": {
                    "expression": (
                        "(() => {"
                        "const el = document.querySelector('main, article, [role=main], body');"
                        "const text = el ? el.innerText : document.body.innerText;"
                        "return JSON.stringify({title: document.title, text: text.slice(0, " + str(max_chars) + ")});"
                        "})()"
                    ),
                    "returnByValue": True,
                },
                "session_id": new_sid,
            })
            data = json.loads(result.get("result", {}).get("result", {}).get("value", "{}"))
            title = data.get("title", "")
            text = data.get("text", "")
            content = f"# {title}\n\n{text}" if title else text
            return content[:max_chars], "cdp"

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_sync_scrape)
            return future.result(timeout=30)

    except Exception as exc:
        logger.debug("CDP scrape failed: %s", exc)
        return "", "cdp_error"


# ── HTTP fallback ──────────────────────────────────────────────────────────────


async def _scrape_via_http(url: str, max_chars: int = 10000) -> tuple[str, str]:
    """Fallback: plain HTTP via httpx + BeautifulSoup."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "LegionSwarmBot/1.0"})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return text[:max_chars], "httpx"
    except Exception as exc:
        logger.warning("HTTP scrape fallback failed: %s", exc)
        return f"Scrape error: {exc}", "error"


# ── public API ────────────────────────────────────────────────────────────────


async def scrape_url(
    url: str,
    max_chars: int = 10000,
    prefer_fallback: bool = False,
) -> tuple[str, str]:
    """Scrape URL via browser-harness CDP with HTTP fallback.

    Returns:
        Tuple of (content, source) where source is one of:
        - "cdp": Scraped via browser-harness (user's Chrome via CDP)
        - "httpx": Scraped via HTTP fallback
        - "error": Failed to scrape

    No firecrawl dependency. Uses user's running Chrome if available,
    falls back to plain HTTP if CDP fails.
    """
    # Try CDP (browser-harness) first — handles JS-rendered pages
    if not prefer_fallback:
        content, source = await _scrape_via_cdp(url, max_chars)
        if content and source == "cdp":
            return content, source

    # Fallback to plain HTTP
    return await _scrape_via_http(url, max_chars)


async def scrape_url_with_fallbacks(url: str, max_chars: int = 10000) -> dict:
    """Scrape URL trying all available methods.

    Returns dict with keys:
        - content: scraped content or error message
        - source: "cdp", "httpx", or "error"
        - cdp_available: bool indicating CDP/browser-harness was attempted
    """
    result = {
        "url": url,
        "content": "",
        "source": "error",
        "cdp_available": True,
    }

    # Try CDP first
    content, source = await _scrape_via_cdp(url, max_chars)
    result["content"] = content
    result["source"] = source

    if content and source == "cdp":
        return result

    # Try HTTP fallback
    if source in ("cdp_error", "error"):
        http_content, http_source = await _scrape_via_http(url, max_chars)
        result["content"] = http_content
        result["source"] = http_source

    return result


def suggest_fallback_tools(url: str) -> list[dict]:
    """Suggest alternative tools when primary scraping fails.

    Returns list of dicts with tool suggestions and usage hints.
    """
    suggestions = []

    suggestions.append({
        "tool": "browser_harness",
        "reason": "CDP-based browser control via user's running Chrome",
        "usage": "from tools.browser_harness.helpers import goto_url, wait_for_load, js, capture_screenshot",
    })

    suggestions.append({
        "tool": "webfetch",
        "reason": "Simple URL content fetcher",
        "usage": "webfetch(url=<url>, format=\"markdown\")",
    })

    suggestions.append({
        "tool": "exa_web_search_exa",
        "reason": "Web search with content extraction",
        "usage": "exa_web_search_exa(query=\"<query>\")",
    })

    return suggestions
