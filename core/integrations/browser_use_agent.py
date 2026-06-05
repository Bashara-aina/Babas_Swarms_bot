"""core/integrations/browser_use_agent.py — Browser-use autonomous browsing.

browser-use provides AI-driven browser automation.
This integrates it with SwarmBot for autonomous web tasks.

Usage:
    agent = BrowserUseAgent()
    result = await agent.run(task="Find the latest AI research on arxiv")
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

BROWSER_USE_AVAILABLE = False
try:
    from browser_use import Agent as BrowserUseAgentClass
    from browser_use.agent.views import AgentHistoryList

    BROWSER_USE_AVAILABLE = True
except ImportError:
    BrowserUseAgentClass = None
    AgentHistoryList = None


def _build_browser_llm(model: str | None = None) -> Any:
    """Build a ChatOpenAI-compatible LLM for MiniMax browser tasks.

    browser-use requires a chat model implementing the BaseChatModel interface.
    We use langchain_openai's ChatOpenAI with MiniMax's OpenAI-compatible endpoint.
    """
    from langchain_openai import ChatOpenAI

    minimax_model = model or os.getenv("BROWSER_USE_MODEL", "minimax-coding-plan/MiniMax-M3")
    if "/" in minimax_model:
        minimax_model = "gpt-4o-mini"

    api_key = os.getenv("MINIMAX_API_KEY", "dummy")
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = "https://api.minimax.io/v1"

    return ChatOpenAI(
        model=minimax_model,
        openai_api_key=api_key,  # type: ignore[reportCallIssue]
        base_url="https://api.minimax.io/v1",
        temperature=0.7,
        timeout=60.0,
    )


class BrowserUseAgent:
    """Autonomous browser agent using browser-use + MiniMax."""

    def __init__(
        self,
        model: str | None = None,
        headless: bool = True,
        max_steps: int = 10,
    ) -> None:
        self.model = model or os.getenv("BROWSER_USE_MODEL", "minimax-coding-plan/MiniMax-M3")
        self.headless = headless
        self.max_steps = max_steps
        self._agent = None

    def _get_llm(self) -> Any:
        """Build the LLM for browser tasks."""
        return _build_browser_llm(self.model)

    async def run(self, task: str) -> str:
        """Run browser agent on a task."""
        if not BROWSER_USE_AVAILABLE:
            return "[browser-use not installed — pip install browser-use]"

        try:
            llm = self._get_llm()
            agent = BrowserUseAgentClass(  # type: ignore[reportOptionalCall]
                task=task,
                llm=llm,
                headless=self.headless,
                max_steps=self.max_steps,
            )
            result = await agent.run()
            return self._parse_result(result)
        except Exception as exc:
            logger.error("browser-use agent failed: %s", exc)
            return f"[browser-use error: {exc}]"

    def _parse_result(self, result: Any) -> str:
        """Parse browser-use result into text."""
        if hasattr(result, "history"):
            history: AgentHistoryList = result.history  # type: ignore[reportInvalidTypeForm]
            if history and len(history) > 0:
                last = history[-1]
                if hasattr(last, "result"):
                    return str(last.result)
        return str(result) if result else "(empty result)"


async def browse_web_async(task: str, headless: bool = True) -> str:
    """Convenience function for one-off browser tasks."""
    agent = BrowserUseAgent(headless=headless)
    return await agent.run(task)
