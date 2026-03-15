"""deep_think.py — Multi-layer extended thinking pipeline.

Designed for long-form reasoning tasks where we want:
    1) framing
    2) multiple competing hypotheses
    3) adversarial critique
    4) iterative refinement across several layers
    5) final synthesis with confidence and uncertainty

This is intentionally slower and deeper than a regular single-turn chat call.
"""

from __future__ import annotations
import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)


async def run_deep_think(
    question: str,
    llm_call: Callable[[str, str, str], Coroutine[Any, Any, str]],
    progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    depth: int = 3,
    branches: int = 5,
) -> dict:
    """Run a multi-layer deep thinking pipeline.

    Args:
        question: The user's original question.
        llm_call: async fn(model, system_prompt, user_message) -> str
        progress_fn: Optional async callback for Telegram status updates.
        depth: Number of iterative refinement layers (2-6 recommended).
        branches: Number of competing hypotheses per layer.

    Returns:
        dict with keys:
          framing
          layers
          final_answer
          confidence
          uncertainty
          what_would_change
    """
    from agents import AGENT_MODELS, build_system_prompt

    depth = max(2, min(int(depth), 6))
    branches = max(3, min(int(branches), 8))

    async def _progress(msg: str):
        if progress_fn:
            await progress_fn(msg)
        logger.info("[DeepThink] %s", msg)

    await _progress("🧠 Layered Think 1/5 — Framing the question...")

    # ── Stage 1: Frame the problem ───────────────────────────────────────────
    framing_prompt = build_system_prompt(
        "You are a rigorous first-principles analyst."
        " Clarify what the question is truly asking, surface hidden assumptions,"
        " identify constraints, and define success criteria."
        " Keep it concise but sharp."
    )
    framing = await llm_call(
        AGENT_MODELS["debug"],
        framing_prompt,
        f"Question:\n{question}\n\n"
        "Return sections:\n"
        "- Core problem\n"
        "- Hidden assumptions\n"
        "- Constraints\n"
        "- Success criteria"
    )

    await _progress(f"🔀 Layered Think 2/5 — Running {depth} reasoning layers...")

    layers: list[dict[str, str]] = []
    rolling_context = f"Question:\n{question}\n\nFraming:\n{framing}"

    for idx in range(1, depth + 1):
        await _progress(f"🧩 Layer {idx}/{depth} — hypotheses")

        hyp_prompt = build_system_prompt(
            "You are a strategic hypothesis generator."
            " Produce mutually distinct candidate explanations/solutions,"
            " including at least one contrarian option."
        )
        hypotheses = await llm_call(
            AGENT_MODELS["architect"],
            hyp_prompt,
            f"{rolling_context}\n\n"
            f"Generate {branches} competing hypotheses."
            " For each hypothesis include:\n"
            "- claim\n- why it may be true\n- key risk"
        )

        await _progress(f"⚔️ Layer {idx}/{depth} — adversarial critique")
        critique_prompt = build_system_prompt(
            "You are an adversarial reviewer."
            " Attack each hypothesis with strongest counter-evidence,"
            " edge-case failures, and hidden risks."
        )
        critique = await llm_call(
            AGENT_MODELS["debug"],
            critique_prompt,
            f"Context:\n{rolling_context}\n\nHypotheses:\n{hypotheses}\n\n"
            "For each hypothesis provide:\n"
            "- strongest objection\n- failure mode\n- evidence needed to validate"
        )

        await _progress(f"🧠 Layer {idx}/{depth} — synthesis update")
        synthesis_prompt = build_system_prompt(
            "You are a Bayesian synthesizer."
            " Merge hypotheses and critiques into the best current thesis,"
            " assign confidence bands, and list unresolved uncertainty."
        )
        synthesis = await llm_call(
            AGENT_MODELS["analyst"],
            synthesis_prompt,
            f"Question:\n{question}\n\n"
            f"Hypotheses:\n{hypotheses}\n\n"
            f"Critique:\n{critique}\n\n"
            "Return:\n"
            "- Current best thesis\n"
            "- Confidence (0-100%)\n"
            "- What remains uncertain\n"
            "- What evidence would change the conclusion"
        )

        layers.append(
            {
                "hypotheses": hypotheses,
                "critique": critique,
                "synthesis": synthesis,
            }
        )
        rolling_context = (
            f"Question:\n{question}\n\n"
            f"Framing:\n{framing}\n\n"
            f"Layer-{idx} synthesis:\n{synthesis}"
        )

    await _progress("📝 Layered Think 3/5 — final synthesis")

    final_prompt = build_system_prompt(
        "You are an expert making a final call after multi-layer analysis."
        " Be clear, decisive, and honest about uncertainty."
    )
    final_raw = await llm_call(
        AGENT_MODELS["reviewer"],
        final_prompt,
        f"Original question:\n{question}\n\n"
        f"Framing:\n{framing}\n\n"
        f"Final layer synthesis:\n{layers[-1]['synthesis']}\n\n"
        "Write final output with sections:\n"
        "- Answer\n"
        "- Confidence\n"
        "- Uncertainty\n"
        "- What would change my mind\n"
        "- Next best action"
    )

    await _progress("🔍 Layered Think 4/5 — extracting uncertainty")

    uncertainty = ""
    what_changes = ""
    for sent in final_raw.replace("\n", ". ").split("."):
        low = sent.lower()
        if not uncertainty and (
            "uncertain" in low
            or "unknown" in low
            or "not sure" in low
            or "confidence" in low
        ):
            uncertainty = sent.strip() + "."
        if not what_changes and (
            "change" in low
            or "would change" in low
            or "new evidence" in low
            or "what would change" in low
        ):
            what_changes = sent.strip() + "."
        if uncertainty and what_changes:
            break

    await _progress("✅ Layered Think 5/5 — done")

    confidence = ""
    for sent in final_raw.replace("\n", ". ").split("."):
        if "%" in sent or "confidence" in sent.lower():
            confidence = sent.strip()
            if confidence:
                break

    return {
        "framing": framing,
        "layers": layers,
        "final_answer": final_raw,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "what_would_change": what_changes,
        "depth": depth,
        "branches": branches,
    }


def format_think_result(result: dict) -> str:
    """Format deep-think result for Telegram display."""
    layers = result.get("layers", [])
    last_syn = ""
    if layers:
        last_syn = str(layers[-1].get("synthesis", ""))

    thinking_summary = (
        f"Framing: {str(result.get('framing', ''))[:260]}...\n\n"
        f"Layers: {int(result.get('depth', len(layers) or 0))}\n"
        f"Branches/layer: {int(result.get('branches', 0) or 0)}\n\n"
        f"Last synthesis: {last_syn[:360]}..."
    )

    parts = [
        f"💭 <b>THINKING PROCESS</b>\n<pre>{thinking_summary}</pre>",
        "",
        "🎯 <b>FINAL ANSWER</b>",
        str(result.get("final_answer", "")),
    ]

    if result.get("confidence"):
        parts.append(f"\n📈 <b>CONFIDENCE</b>: {result['confidence']}")

    if result.get("uncertainty"):
        parts.append(f"\n⚠️ <b>UNCERTAINTY</b>: {result['uncertainty']}")

    if result.get("what_would_change"):
        parts.append(f"🔄 <b>WHAT WOULD CHANGE THIS</b>: {result['what_would_change']}")

    return "\n".join(parts)
