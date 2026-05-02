"""
tools/browser_task_router.py
Routes browser tasks to browser-use or crawl4ai based on content type analysis.
MiniMax-only. Used by ruflo task routing and direct API calls.
"""

from __future__ import annotations

import json
import sys

_INTERACTIVE_SIGNALS = {
    "click",
    "fill",
    "login",
    "sign in",
    "form",
    "submit",
    "scroll",
    "type",
    "wait",
    "interactive",
    "session",
    "auth",
    "select",
    "dropdown",
    "checkbox",
    "radio",
    "mouse",
    "hover",
    "drag",
    "upload",
}

_SEARCH_SIGNALS = {
    "search for",
    "look up",
    "find information",
    "research",
    "google ",
    "duckduckgo",
    "bing ",
    "search the web",
    "find on ",
    "get info",
    "get details",
    "get contact",
    "list of",
    "all results",
    "what is",
    "who is",
    "site:",
    "domain:",
    "linkedin.com",
    "instagram.com",
}


def decide_strategy(task: str) -> str:
    """Return 'browser-use' or 'crawl4ai' based on task signals."""
    task_lower = task.lower()
    if any(s in task_lower for s in _INTERACTIVE_SIGNALS):
        return "browser-use"
    if any(s in task_lower for s in _SEARCH_SIGNALS):
        return "crawl4ai"
    return "crawl4ai"


def route(url: str, task: str, force: str | None = None) -> dict:
    """
    Route a browser task to the appropriate tool.

    Args:
        url: Target URL
        task: Natural language task description
        force: Force strategy ('browser-use' or 'crawl4ai')

    Returns:
        dict with keys: success, strategy, result/error, artifacts
    """
    strategy = force or decide_strategy(task)

    if strategy == "browser-use":
        return _run_browser_use(url, task)
    elif strategy == "crawl4ai":
        return _run_crawl4ai(url, task)

    return {
        "success": False,
        "strategy": strategy,
        "error": f"Unknown strategy: {strategy}",
    }


def _run_browser_use(url: str, task: str) -> dict:
    """Run task via browser-use runner."""
    try:
        import asyncio

        from scripts.browser_use_runner import run_browser_task

        result = asyncio.run(
            run_browser_task(
                task=f"Navigate to {url}. {task}",
                max_steps=20,
                headless=True,
                save_screenshot=True,
            )
        )
        return {
            "success": result.get("success", False),
            "strategy": "browser-use",
            "result": result.get("result"),
            "error": result.get("error"),
            "screenshot_path": result.get("screenshot_path"),
            "elapsed_ms": result.get("elapsed_ms"),
        }
    except Exception as e:
        return {
            "success": False,
            "strategy": "browser-use",
            "error": str(e)[:500],
        }


def _run_crawl4ai(url: str, task: str) -> dict:
    """Run task via crawl4ai using in-process async."""
    try:
        import asyncio

        from crawl4ai import AsyncWebCrawler

        async def _crawl():
            async with AsyncWebCrawler(verbose=False) as c:
                r = await c.arun(url=url)
                links = [
                    (lnk.get("href", ""), lnk.get("text", ""))
                    for lnk in (
                        r.links.get("external", []) if isinstance(r.links, dict) else []
                    )[:15]
                ]
                return (r.markdown[:8000] if r.markdown else ""), links

        markdown, links = asyncio.run(_crawl())
        return {
            "success": True,
            "strategy": "crawl4ai",
            "result": markdown,
            "links": links,
        }
    except Exception as e:
        return {
            "success": False,
            "strategy": "crawl4ai",
            "error": str(e)[:500],
        }


def remember_task(task: str, result: dict, user_id: str = "legion") -> None:
    """Store browser task outcome in mem0ai for cross-session recall."""
    try:
        from mem0 import Memory

        m = Memory()
        summary = (
            f"Browser task: '{task}' | "
            f"Strategy: {result.get('strategy', 'unknown')} | "
            f"Success: {result.get('success', False)} | "
            f"Result: {str(result.get('result', ''))[:500]}"
        )
        m.add(summary, user_id=user_id)
    except Exception:
        pass


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    task = sys.argv[2] if len(sys.argv) > 2 else "Extract main content"
    result = route(url, task)
    print(json.dumps(result, indent=2))
