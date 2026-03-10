"""
tools/deep_think.py

6-step extended thinking pipeline inspired by Claude Opus deep reasoning.
Each step uses a different agent/temperature to simulate genuine deliberation:
  1. Frame the problem
  2. Generate competing hypotheses
  3. Steel-man each hypothesis
  4. Find the fatal flaw in each
  5. Bayesian update (assign probabilities)
  6. Final answer with calibrated uncertainty
"""
from __future__ import annotations
import asyncio
import logging
import re

logger = logging.getLogger(__name__)


class DeepThinkPipeline:
    """6-step extended thinking pipeline."""

    def __init__(self):
        pass

    async def _call(self, llm_client, prompt: str, agent: str, temperature: float = 0.7) -> str:
        """Call LLM with agent routing and return text."""
        try:
            from agents import AGENT_MODELS, FALLBACK_CHAIN, PERSONALITY_WRAPPER
            model = AGENT_MODELS.get(agent, AGENT_MODELS["general"])
            system = PERSONALITY_WRAPPER + f"\n\n[Role: {agent} agent]"
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: llm_client.complete(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    system=system,
                    temperature=temperature,
                    max_tokens=1024,
                )
            )
            return result.strip() if result else "[no response]"
        except Exception as e:
            logger.error("DeepThink step error (%s): %s", agent, e)
            return f"[error in {agent} step: {e}]"

    async def run(self, question: str, llm_client) -> dict:
        """
        Run the full 6-step deep thinking pipeline.
        Returns dict with all intermediate steps and final answer.
        """
        logger.info("DeepThink: starting for question: %s", question[:80])

        # STEP 1: Frame the problem
        frame_prompt = (
            f"Question: {question}\n\n"
            "What is this question REALLY asking? What are the hidden assumptions? "
            "What would need to be true for different possible answers? "
            "Be concise and sharp — 3-5 sentences max."
        )
        frame = await self._call(llm_client, frame_prompt, "debug", 0.6)

        # STEP 2: Generate competing hypotheses
        hyp_prompt = (
            f"Question: {question}\n\nFraming: {frame}\n\n"
            "Generate 4-6 completely different ways to answer this question. "
            "Include contrarian, unconventional, and minority-view answers. "
            "Number each hypothesis clearly: 1. ... 2. ... etc."
        )
        hypotheses_raw = await self._call(llm_client, hyp_prompt, "general", 0.9)
        hypotheses = _parse_numbered_list(hypotheses_raw)

        # STEP 3: Steel-man each hypothesis
        steelman_prompt = (
            f"Question: {question}\n\nHypotheses:\n{hypotheses_raw}\n\n"
            "For each hypothesis, write the STRONGEST possible argument in its favor — "
            "even if you personally disagree. This is a steel-man exercise. "
            "Be intellectually honest. Number your responses to match."
        )
        steelman = await self._call(llm_client, steelman_prompt, "architect", 0.7)

        # STEP 4: Find fatal flaw
        flaw_prompt = (
            f"Question: {question}\n\nHypotheses:\n{hypotheses_raw}\n\n"
            "For each hypothesis, identify the single most devastating counterargument "
            "or fatal flaw. Be merciless. One flaw per hypothesis, numbered to match."
        )
        fatal_flaw = await self._call(llm_client, flaw_prompt, "debug", 0.6)

        # STEP 5: Bayesian update
        bayes_prompt = (
            f"Question: {question}\n\n"
            f"Hypotheses: {hypotheses_raw}\n\n"
            f"Steel-man arguments: {steelman}\n\n"
            f"Fatal flaws: {fatal_flaw}\n\n"
            "Given all of the above, assign a probability (0-100%) to each hypothesis. "
            "Which hypothesis survives? Which collapses under scrutiny? "
            "Output as: Hypothesis 1: X% — [one sentence why]. Then declare the winner."
        )
        bayesian = await self._call(llm_client, bayes_prompt, "analyst", 0.5)

        # STEP 6: Final answer with calibrated uncertainty
        final_prompt = (
            f"Question: {question}\n\n"
            f"After deep analysis, the most probable answer is: {bayesian}\n\n"
            "Write the final answer. Structure it as:\n"
            "1. The core answer (confident claim)\n"
            "2. What remains uncertain\n"
            "3. What new information would change this answer\n\n"
            "Be direct. Speak like a sharp expert, not a textbook."
        )
        final_answer = await self._call(llm_client, final_prompt, "general", 0.3)

        # Extract uncertainty and what-would-change from final answer
        uncertainty = _extract_section(final_answer, "uncertain", fallback="Not specified")
        what_would_change = _extract_section(final_answer, "would change", fallback="Not specified")

        return {
            "question": question,
            "frame": frame,
            "hypotheses": hypotheses,
            "hypotheses_raw": hypotheses_raw,
            "steelman": steelman,
            "fatal_flaw": fatal_flaw,
            "bayesian": bayesian,
            "final_answer": final_answer,
            "uncertainty": uncertainty,
            "what_would_change": what_would_change,
        }


def _parse_numbered_list(text: str) -> list[str]:
    """Parse numbered list from LLM output into a Python list."""
    pattern = re.compile(r'^\d+[.):]\s+(.+)', re.MULTILINE)
    matches = pattern.findall(text)
    return matches if matches else [text]


def _extract_section(text: str, keyword: str, fallback: str = "") -> str:
    """Try to extract a section containing keyword from the text."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if keyword.lower() in line.lower():
            # Return that line + next line
            snippet = ' '.join(lines[i:i+2]).strip()
            return snippet[:400]
    return fallback


def format_think_for_telegram(result: dict) -> list[str]:
    """
    Format DeepThink result as Telegram messages.
    Uses spoiler tags for internal monologue.
    Returns list of message strings (split if needed).
    """
    from tools.telegram_formatter import split_message

    question = result.get("question", "")[:80]
    frame = result.get("frame", "")[:300]
    bayesian = result.get("bayesian", "")[:400]
    final_answer = result.get("final_answer", "")
    uncertainty = result.get("uncertainty", "Not specified")[:200]
    what_would_change = result.get("what_would_change", "Not specified")[:200]

    # Internal monologue summary for spoiler
    monologue_summary = f"Framing: {frame[:150]} | Probability analysis: {bayesian[:150]}"

    text = (
        f"\ud83d\udcad **THINKING PROCESS** ||{monologue_summary}||\n\n"
        f"\ud83c\udfaf **FINAL ANSWER**\n{final_answer}\n\n"
        f"\u26a0\ufe0f **UNCERTAINTY**: {uncertainty}\n\n"
        f"\ud83d\udd04 **WHAT WOULD CHANGE THIS**: {what_would_change}"
    )

    return split_message(text)
