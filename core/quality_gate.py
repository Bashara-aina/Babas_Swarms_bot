"""core/quality_gate.py — Response Quality Gate for Legion.

Intercepts shallow/vague/wrong LLM responses before they reach the user.
One retry max — latency matters.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityResult:
    """Result of a quality gate check."""

    issues: list[str]
    should_retry: bool


class QualityGate:
    """Checks LLM responses against quality heuristics and retries if needed."""

    MAX_RETRIES = 1  # never retry more than once — latency matters

    # Issue 1: Shallow responses (too short for complex question)
    # Issue 2: Explicit uncertainty without search trigger
    # Issue 3: LLM identity artifacts

    UNCERTAINTY_SIGNALS = [
        "I don't know",
        "I'm not sure",
        "gw ga tau",
        "tidak yakin",
        "mungkin",
        "I think but am not certain",
    ]

    FORBIDDEN_ARTIFACTS = [
        "As an AI",
        "I cannot",
        "I'm unable to",
        "As a language model",
    ]

    async def check(self, user_message: str, response: str, intent: str) -> QualityResult:
        """Evaluate response quality against known failure patterns.

        Args:
            user_message: The original user message.
            response: The LLM response to check.
            intent: The detected intent/agent key.

        Returns:
            QualityResult with list of issues and whether retry is needed.
        """
        issues: list[str] = []

        # Issue 1: Too short for complex question
        user_words = len(user_message.split())
        response_words = len(response.split())
        if user_words > 20 and response_words < 30:
            issues.append(f"SHALLOW: complex question ({user_words} words) got only {response_words} word response")

        # Issue 2: Explicit uncertainty without search trigger
        response_lower = response.lower()
        if any(signal.lower() in response_lower for signal in self.UNCERTAINTY_SIGNALS):
            # Only flag if there's no indication a search was already attempted
            if "search" not in response_lower and "web" not in response_lower:
                issues.append("UNCERTAIN: response contains uncertainty without search")

        # Issue 3: Forbidden LLM artifacts
        if any(artifact.lower() in response_lower for artifact in self.FORBIDDEN_ARTIFACTS):
            issues.append("ARTIFACT: LLM identity artifact in response")

        return QualityResult(issues=issues, should_retry=len(issues) > 0)

    async def retry(self, messages: list[dict], issues: list[str]) -> str:
        """One retry with explicit instruction to fix the issues."""
        retry_instruction = (
            "Your previous response had these issues: "
            + ", ".join(issues)
            + ". Fix them. Be concrete, specific and stay in Legion's voice."
        )
        retry_messages = messages + [{"role": "user", "content": retry_instruction}]
        from llm_client import call_llm

        return await call_llm(messages=retry_messages)
