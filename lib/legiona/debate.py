"""
lib/legiona/debate.py
Three-agent debate for high-stakes decisions.
Improves factual accuracy ~18% on contested questions (M3 research).

Usage:
    from lib.legiona.debate import debate_simple  # 3-agent basic debate
    from lib.legiona.debate import full_debate      # 5-stage enhanced debate

    verdict = await debate_simple("Should we use ivfflat or hnsw for pgvector?")
    verdict = await full_debate("Should we use ivfflat or hnsw for pgvector?")
"""

from __future__ import annotations

import asyncio

from lib.legiona.minimax_client import LegionaOutput, complete

ADVOCATE_SYSTEM = """You are the ADVOCATE. Given a question, build the
strongest possible case FOR the most promising approach.
Be specific, cite tradeoffs, give concrete evidence.
Do not hedge — argue confidently."""

CHALLENGER_SYSTEM = """You are the CHALLENGER. Given a question and an
advocate's argument, find every flaw, edge case, and alternative.
Be rigorous. If the advocate is right, acknowledge it — but push hard."""

JUDGE_SYSTEM = """You are the JUDGE. You have heard an advocate and
a challenger debate a question. Synthesize both perspectives into
a final verdict. Be decisive. State your confidence level clearly.
Your answer will be acted upon — make it actionable."""


EXTRACT_CLAIMS_SYSTEM = """You are a CLAIMS EXTRACTOR. Given a question,
break it down into distinct factual claims that need verification.
List each claim on its own line with a brief explanation."""

VERIFY_SYSTEM = """You are a CLAIMS VERIFIER. Given a list of claims,
check each one against the provided context. For each claim, state:
VERIFIED: [explanation] if confirmed
CONTRADICTED: [explanation] if false
UNVERIFIED: [explanation] if insufficient data
Be precise and cite specific evidence."""


async def debate_simple(question: str, context: str = "") -> LegionaOutput:
    """
    Run 3-agent debate (basic). Returns judge's verdict as LegionaOutput.
    All 3 agents run in parallel (advocate + challenger), then judge.
    """
    user_msg = f"{context}\n\nQUESTION: {question}" if context else question

    # Round 1: Advocate + Challenger in parallel
    advocate_task = asyncio.to_thread(complete, [
        {"role": "system", "content": ADVOCATE_SYSTEM},
        {"role": "user",   "content": user_msg},
    ], preset="research")

    challenger_task = asyncio.to_thread(complete, [
        {"role": "system", "content": CHALLENGER_SYSTEM},
        {"role": "user",   "content": user_msg},
    ], preset="research")

    advocate, challenger = await asyncio.gather(advocate_task, challenger_task)

    # Round 2: Judge synthesizes
    verdict = await asyncio.to_thread(complete, [
        {"role": "system",    "content": JUDGE_SYSTEM},
        {"role": "user",      "content": question},
        {"role": "assistant", "content": f"ADVOCATE:\n{advocate.answer}"},
        {"role": "user",      "content": f"CHALLENGER:\n{challenger.answer}\n\nNow give your verdict."},
    ], preset="research")

    return verdict


async def full_debate(question: str, context: str = "") -> LegionaOutput:
    """
    Run 5-stage enhanced debate for maximum factual accuracy.

    Stage 1: Extract claims — break question into factual claims
    Stage 2: Advocate — build strongest case FOR the approach
    Stage 3: Challenger — attack every flaw and edge case
    Stage 4: Verify — cross-reference claims against provided context
    Stage 5: Judge — synthesize all perspectives into final verdict

    Returns judge's verdict as LegionaOutput with verification metadata.
    """
    user_msg = f"{context}\n\nQUESTION: {question}" if context else question

    # Stage 1: Extract claims
    claims_response = await asyncio.to_thread(complete, [
        {"role": "system", "content": EXTRACT_CLAIMS_SYSTEM},
        {"role": "user",   "content": user_msg},
    ], preset="research")

    claims_text = claims_response.answer

    # Stage 2: Advocate + Challenger in parallel
    advocate_task = asyncio.to_thread(complete, [
        {"role": "system", "content": ADVOCATE_SYSTEM},
        {"role": "user",   "content": f"{user_msg}\n\nKEY CLAIMS TO ADDRESS:\n{claims_text}"},
    ], preset="debate")

    challenger_task = asyncio.to_thread(complete, [
        {"role": "system", "content": CHALLENGER_SYSTEM},
        {"role": "user",   "content": f"{user_msg}\n\nADVOCATE'S KEY CLAIMS:\n{claims_text}"},
    ], preset="debate")

    advocate, challenger = await asyncio.gather(advocate_task, challenger_task)

    # Stage 3: Verify claims against context
    verify_response = await asyncio.to_thread(complete, [
        {"role": "system",    "content": VERIFY_SYSTEM},
        {"role": "user",      "content": f"CLAIMS TO VERIFY:\n{claims_text}\n\nADVOCATE ARGUMENT:\n{advocate.answer}\n\nCHALLENGER ARGUMENT:\n{challenger.answer}\n\nCONTEXT:\n{context if context else '(no external context provided)'}"},
    ], preset="research")

    # Stage 4: Judge synthesizes with verification in mind
    judge_messages = [
        {"role": "system",    "content": JUDGE_SYSTEM},
        {"role": "user",      "content": f"QUESTION: {question}"},
        {"role": "assistant", "content": f"KEY CLAIMS:\n{claims_text}"},
        {"role": "user",      "content": f"ADVOCATE:\n{advocate.answer}"},
        {"role": "assistant", "content": f"CHALLENGER:\n{challenger.answer}"},
        {"role": "user",      "content": f"VERIFICATION RESULTS:\n{verify_response.answer}\n\nNow give your final verdict with confidence level."},
    ]
    verdict = await asyncio.to_thread(complete, judge_messages, preset="debate")

    # Enhance the verdict with claims and verification info
    enhanced_answer = f"""VERDICT (confidence: {verdict.confidence})

CLAIMS ADDRESSED:
{claims_text}

VERIFICATION SUMMARY:
{verify_response.answer}

FINAL VERDICT:
{verdict.answer}"""

    return LegionaOutput(
        answer=enhanced_answer,
        confidence=verdict.confidence,
        verified_from_context=verify_response.verified_from_context,
        items_needing_verification=verdict.items_needing_verification,
        reasoning_summary="5-stage debate: claims extracted, advocate/challenger debated, verified against context, judged.",
    )


# Backward compatibility alias
async def debate(question: str, context: str = "") -> LegionaOutput:
    """Legacy alias for debate_simple(). Use debate_simple() or full_debate() instead."""
    return await debate_simple(question, context)


def debate_sync(question: str, context: str = "") -> LegionaOutput:
    """Synchronous wrapper for debate_simple()."""
    return asyncio.run(debate_simple(question, context))


def full_debate_sync(question: str, context: str = "") -> LegionaOutput:
    """Synchronous wrapper for full_debate()."""
    return asyncio.run(full_debate(question, context))
