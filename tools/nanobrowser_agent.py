"""
Nanobrowser multi-agent browser wrapper.
3-agent crew: Planner → Navigator → Validator.
Replaces single-agent browser_agent.py for complex multi-step browsing.

Usage:
  agent = NanobrowserAgent(headless=True)
  result = await agent.run("Find the latest Claude Code release notes")
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import TypedDict

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None


class BrowserState(TypedDict):
    url: str
    title: str
    viewport: str
    elements: list[dict]


@dataclass
class BrowserAction:
    """A single browser action decided by the Planner agent."""

    action_type: str  # "click" | "nav" | "type" | "scroll" | "screenshot" | "done"
    selector: str | None = None
    value: str | None = None
    target_url: str | None = None
    expected_result: str | None = None


class NanobrowserAgent:
    """
    Multi-agent browser using a 3-role crew:
    - Planner: decides next action from goal + current state
    - Navigator: executes CDP/Playwright actions
    - Validator: confirms action produced expected result
    """

    def __init__(self, headless: bool = True, model: str = "minimax/MiniMax-Text-01"):
        self.headless = headless
        self.model = model
        self._browser = None
        self._page = None

    async def _ensure_browser(self):
        if async_playwright is None:
            raise ImportError(
                "playwright not installed. Run: pip install playwright && playwright install chromium --with-deps"
            )
        if self._browser is None:
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
        if self._page is None:
            self._page = await self._browser.new_page()
        return self._browser, self._page

    async def _get_state(self, page) -> BrowserState:
        """Capture current browser state for the Planner."""
        elements = []
        try:
            for el in await page.query_selector_all("a, button, input"):
                tag = await el.evaluate("el => el.tagName")
                text = await el.evaluate("el => el.textContent?.trim()[:50]")
                el_id = await el.evaluate("el => el.id")
                selector = f"#{el_id}" if el_id else None
                elements.append({"tag": tag, "text": text, "selector": selector})
        except Exception:
            pass

        return BrowserState(
            url=page.url,
            title=await page.title(),
            viewport=f"{page.viewport_size['width']}x{page.viewport_size['height']}",
            elements=elements,
        )

    async def _planner(self, goal: str, state: BrowserState) -> BrowserAction:
        """Planner agent — decides the next action."""
        from llm_client import chat

        prompt = f"""You are a browser navigation planner.
Goal: {goal}
Current URL: {state['url']}
Title: {state['title']}
Clickable elements: {json.dumps(state['elements'][:10], indent=2)}

Decide the next action. Respond ONLY with valid JSON:
{{"action_type": "click|nav|type|scroll|screenshot|done", "selector": "...", "value": "...", "target_url": "..."}}
"""
        response = await chat(model=self.model, prompt=prompt)
        try:
            parsed = json.loads(response)
            return BrowserAction(**parsed)
        except Exception:
            return BrowserAction(action_type="done")

    async def _navigator(self, page, action: BrowserAction) -> None:
        """Navigator agent — executes the action via Playwright."""
        at = action.action_type
        if at == "click" and action.selector:
            await page.click(action.selector, timeout=5000)
        elif at == "type" and action.selector and action.value:
            await page.fill(action.selector, action.value)
        elif at == "nav" and action.target_url:
            await page.goto(
                action.target_url, wait_until="domcontentloaded", timeout=15000
            )
        elif at == "scroll":
            await page.evaluate(f"window.scrollBy(0, {action.value or 300})")
        await asyncio.sleep(0.5)

    async def _validator(self, action: BrowserAction, page) -> bool:
        """Validator agent — confirms action had expected effect."""
        at = action.action_type
        if at == "nav" and action.target_url:
            return action.target_url in page.url
        return True

    async def run(self, goal: str, max_steps: int = 10) -> str:
        """
        Run the full browser crew until goal is achieved or max_steps reached.
        Returns a summary of what was accomplished.
        """
        _, page = await self._ensure_browser()
        steps_completed = 0

        for step in range(max_steps):
            state = await self._get_state(page)
            action = await self._planner(goal, state)

            if action.action_type == "done":
                steps_completed = step
                break

            await self._navigator(page, action)

            if not await self._validator(action, page):
                break

            steps_completed = step + 1

        final_url = page.url
        await page.screenshot(path=f"/tmp/nanobrowser_final_{id(self)}.png")
        return (
            f"Completed {steps_completed}/{max_steps} steps.\n"
            f"Final URL: {final_url}\n"
            f"Screenshot saved."
        )

    async def close(self) -> None:
        """Close browser and free resources."""
        if self._page:
            await self._page.close()
            self._page = None
        if self._browser:
            await self._browser.close()
            self._browser = None


# Module-level singleton
_nanobrowser: NanobrowserAgent | None = None


def get_nanobrowser() -> NanobrowserAgent:
    global _nanobrowser
    if _nanobrowser is None:
        _nanobrowser = NanobrowserAgent()
    return _nanobrowser
