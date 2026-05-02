"""
tools/browser_task_router.py
Routes browser tasks to browser-use or crawl4ai based on content type analysis.
MiniMax-only. Used by ruflo task routing and direct API calls.
"""
from __future__ import annotations

import json
import subprocess
import sys

_INTERACTIVE_SIGNALS = {
    "click", "fill", "login", "sign in", "form", "submit",
    "scroll", "type", "wait", "interactive", "session", "auth",
    "select", "dropdown", "checkbox", "radio",
    "mouse", "hover", "drag", "upload",
}


def decide_strategy(task: str) -> str:
    """Return 'browser-use' or 'crawl4ai' based on task complexity."""
    task_lower = task.lower()
    if any(s in task_lower for s in _INTERACTIVE_SIGNALS):
        return "browser-use"
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

    return {"success": False, "strategy": strategy, "error": f"Unknown strategy: {strategy}"}


def _run_browser_use(url: str, task: str) -> dict:
    """Run task via browser-use runner."""
    try:
        import asyncio

        from scripts.browser_use_runner import run_browser_task
        result = asyncio.run(run_browser_task(
            task=f"Navigate to {url}. {task}",
            max_steps=20,
            headless=True,
            save_screenshot=True,
        ))
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
    """Run task via crawl4ai."""
    try:
        result = subprocess.run(
            [
                "/home/newadmin/miniconda3/bin/python3", "-c",
                f"import asyncio; from crawl4ai import AsyncWebCrawler; "
                f"async def m(): async with AsyncWebCrawler() as c: r = await c.arun(url='{url}'); print(r.markdown[:5000]); "
                f"asyncio.run(m())"
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return {
                "success": True,
                "strategy": "crawl4ai",
                "result": result.stdout,
            }
        return {
            "success": False,
            "strategy": "crawl4ai",
            "error": result.stderr[:500] if result.stderr else "Unknown error",
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