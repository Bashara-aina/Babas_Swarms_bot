"""
Browser task runner using browser-use Agent with MiniMax-only LLM.

Usage:
    from tools.browser_runner import run_browser_task

    result = await run_browser_task(
        task="Click login, fill credentials, submit",
        max_steps=20,
        headless=False,
    )
    # result = {"success": True, "result": "...", "steps": [...], "elapsed_ms": ...}
"""

import json
import sys
import time
from contextlib import suppress
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from browser_use.browser import BrowserProfile, BrowserSession
from browser_use.cli import Agent
from browser_use.controller import Controller
from browser_use.llm.litellm import ChatLiteLLM


def get_minimax_llm() -> ChatLiteLLM:
    import os
    model = "minimax-coding-plan/MiniMax-M3"
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    api_base = "https://api.minimax.io/v1"
    return ChatLiteLLM(
        model=model,
        api_key=api_key,
        api_base=api_base,
        temperature=0.3,
        max_tokens=4096,
        max_retries=3,
    )


def run_browser_task(
    task: str,
    max_steps: int = 30,
    headless: bool = True,
    agent_id: str | None = None,
    initial_actions: list | None = None,
) -> dict:
    """
    Run a browser task synchronously using browser-use Agent + MiniMax LLM.

    Returns:
        {
            "success": bool,
            "result": str,          # final result text
            "steps": int,           # steps taken
            "elapsed_ms": float,
            "url": str,             # final URL
            "error": str | None,
        }
    """
    llm = get_minimax_llm()
    controller = Controller()

    profile = BrowserProfile(
        headless=headless,
        extra_chromium_args=["--disable-blink-features=AutomationDetected"] if not headless else [],
    )
    session = BrowserSession(browser_profile=profile)

    agent = Agent(
        task=task,
        llm=llm,
        browser=session,
        controller=controller,
        use_vision=True,
        max_steps=max_steps,
        initial_actions=initial_actions or [],
        step_timeout=120,
        use_thinking=True,
        enable_planning=True,
    )

    start = time.monotonic()
    try:
        history = agent.run_sync(max_steps=max_steps)
        elapsed = (time.monotonic() - start) * 1000

        final_state = history[-1] if history else None
        url = ""
        result_text = ""
        if final_state:
            url = final_state.url or ""
            result_text = final_state.result or ""

        return {
            "success": True,
            "result": result_text,
            "steps": len(history),
            "elapsed_ms": round(elapsed, 1),
            "url": url,
            "error": None,
        }
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return {
            "success": False,
            "result": "",
            "steps": 0,
            "elapsed_ms": round(elapsed, 1),
            "url": "",
            "error": str(e),
        }
    finally:
        with suppress(Exception):
            session.close()


async def run_browser_task_async(
    task: str,
    max_steps: int = 30,
    headless: bool = True,
    initial_actions: list | None = None,
) -> dict:
    """Async version of run_browser_task."""
    return run_browser_task(task, max_steps, headless, initial_actions=initial_actions)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Browser task runner via browser-use + MiniMax")
    parser.add_argument("task", help="Task description")
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--visible", action="store_true", help="Show browser (not headless)")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    result = run_browser_task(
        task=args.task,
        max_steps=args.max_steps,
        headless=not args.visible,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"OK | {result['steps']} steps | {result['elapsed_ms']:.0f}ms | {result['url']}")
            print(f"Result: {result['result'][:300]}")
        else:
            print(f"FAILED: {result['error']}", file=sys.stderr)
            sys.exit(1)
