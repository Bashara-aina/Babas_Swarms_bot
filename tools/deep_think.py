"""deep_think.py — 6-step extended thinking pipeline.

Models Claude Opus-style deep thinking:
  Step 1: Frame the problem
  Step 2: Generate competing hypotheses
  Step 3: Steel-man each hypothesis
  Step 4: Find the fatal flaw in each
  Step 5: Bayesian update — which survives?
  Step 6: Final answer with explicit uncertainty

Designed for the /think command.
"""

from __future__ import annotations
import asyncio
import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)


async def run_deep_think(
    question: str,
    llm_call: Callable[[str, str, str], Coroutine[Any, Any, str]],
    progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
) -> dict:
    """Run the full 6-step deep thinking pipeline.

    Args:
        question: The user's original question.
        llm_call: async fn(model, system_prompt, user_message) -> str
        progress_fn: Optional async callback for Telegram status updates.

    Returns:
        dict with keys: framing, hypotheses, steelmans, flaws,
                        surviving_hypothesis, final_answer, uncertainty,
                        what_would_change
    """
    from agents import AGENT_MODELS, build_system_prompt

    async def _progress(msg: str):
        if progress_fn:
            await progress_fn(msg)
        logger.info("[DeepThink] %s", msg)

    await _progress("🧠 Step 1/6 — Framing the real question...")

    # ── STEP 1: Frame the problem ─────────────────────────────────────────────
    framing_prompt = build_system_prompt(
        "You are a philosopher-scientist. Your job is to dissect what a question"
        " is REALLY asking. Expose hidden assumptions. Identify what would need to"
        " be true for each possible answer. Be concise and sharp — 3-5 sentences."
    )
    framing = await llm_call(
        AGENT_MODELS["debug"],
        framing_prompt,
        f"What is this question REALLY asking, and what are its hidden assumptions?\n\nQuestion: {question}"
    )

    await _progress("🔀 Step 2/6 — Generating competing hypotheses...")

    # ── STEP 2: Generate competing hypotheses ─────────────────────────────────
    hyp_prompt = build_system_prompt(
        "You are a lateral thinker. Generate 4-5 COMPLETELY DIFFERENT ways to"
        " answer a question — including contrarian, unconventional, and 'what if"
        " everyone is wrong' perspectives. Number each one. Keep each to 2-3 sentences."
    )
    hyp_raw = await llm_call(
        AGENT_MODELS["general"],
        hyp_prompt,
        f"Generate 4-5 competing hypotheses/answers for:\n\n{question}\n\nFraming context: {framing}",
    )
    hypotheses = hyp_raw

    await _progress("🛡️ Step 3/6 — Steel-manning each hypothesis...")

    # ── STEP 3: Steel-man each hypothesis ────────────────────────────────────
    steel_prompt = build_system_prompt(
        "You are a master debater. For each hypothesis provided, write the STRONGEST"
        " possible argument in its favor — even if you personally disagree. Each"
        " steel-man should be 2-3 sentences. Number them to match the original."
    )
    steelmans = await llm_call(
        AGENT_MODELS["architect"],
        steel_prompt,
        f"Steel-man each of these hypotheses:\n\n{hypotheses}"
    )

    await _progress("⚔️ Step 4/6 — Finding fatal flaws...")

    # ── STEP 4: Fatal flaw for each ───────────────────────────────────────────
    flaw_prompt = build_system_prompt(
        "You are a rigorous critic. For each hypothesis, find the single most"
        " devastating counterargument or logical flaw. Be surgical — one killer"
        " objection per hypothesis. Number them to match."
    )
    flaws = await llm_call(
        AGENT_MODELS["debug"],
        flaw_prompt,
        f"Find the fatal flaw in each hypothesis:\n\nHypotheses:\n{hypotheses}\n\nSteel-mans:\n{steelmans}"
    )

    await _progress("⚖️ Step 5/6 — Bayesian update — which hypothesis survives?...")

    # ── STEP 5: Bayesian update ───────────────────────────────────────────────
    bayes_prompt = build_system_prompt(
        "You are a Bayesian reasoner. Given the hypotheses, their best arguments,"
        " and their fatal flaws, assign rough probability weights (they don't need"
        " to sum to 100%) and explain which hypothesis survives best. Be explicit"
        " about what evidence tipped the balance."
    )
    surviving = await llm_call(
        AGENT_MODELS["analyst"],
        bayes_prompt,
        f"Hypotheses:\n{hypotheses}\n\nSteel-mans:\n{steelmans}\n\nFatal flaws:\n{flaws}\n\nWhich hypothesis survives Bayesian scrutiny?"
    )

    await _progress("📝 Step 6/6 — Writing final answer with uncertainty...")

    # ── STEP 6: Final answer with uncertainty ─────────────────────────────────
    final_prompt = build_system_prompt(
        "You are an expert who has just completed a rigorous thinking process."
        " Write a clear, direct final answer. Explicitly state:\n"
        " 1. What you're confident in\n"
        " 2. What's genuinely uncertain\n"
        " 3. What new information would change your answer\n\n"
        "Be honest, direct, and human. Don't summarize the process — just give the answer."
    )
    final_raw = await llm_call(
        AGENT_MODELS["general"],
        final_prompt,
        f"Original question: {question}\n\nAfter deep analysis, the surviving hypothesis is:\n{surviving}\n\nWrite the final answer."
    )

    # Extract uncertainty and what-would-change from final answer
    uncertainty = ""
    what_changes = ""
    if "uncertain" in final_raw.lower():
        # Try to extract uncertainty sentence
        for sent in final_raw.split('.'):
            if 'uncertain' in sent.lower() or 'not sure' in sent.lower():
                uncertainty = sent.strip() + '.'
                break
    if "would change" in final_raw.lower() or "new information" in final_raw.lower():
        for sent in final_raw.split('.'):
            if 'change' in sent.lower() or 'new information' in sent.lower():
                what_changes = sent.strip() + '.'
                break

    return {
        "framing": framing,
        "hypotheses": hypotheses,
        "steelmans": steelmans,
        "flaws": flaws,
        "surviving_hypothesis": surviving,
        "final_answer": final_raw,
        "uncertainty": uncertainty,
        "what_would_change": what_changes,
    }


def format_think_result(result: dict) -> str:
    """Format the deep think result for Telegram display.

    Uses spoiler tags for the thinking process, shows the final answer prominently.

    Args:
        result: Dict returned by run_deep_think().

    Returns:
        Telegram-formatted string.
    """
    thinking_summary = (
        f"Framing: {result['framing'][:200]}...\n\n"
        f"Hypotheses considered: {result['hypotheses'][:300]}...\n\n"
        f"Surviving: {result['surviving_hypothesis'][:200]}..."
    )

    parts = [
        f"💭 **THINKING PROCESS** ||{thinking_summary}||",
        "",
        "🎯 **FINAL ANSWER**",
        result["final_answer"],
    ]

    if result.get("uncertainty"):
        parts.append(f"\n⚠️ **UNCERTAINTY**: {result['uncertainty']}")

    if result.get("what_would_change"):
        parts.append(f"🔄 **WHAT WOULD CHANGE THIS**: {result['what_would_change']}")

    return "\n".join(parts)
