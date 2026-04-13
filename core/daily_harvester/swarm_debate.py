"""SwarmDebate — 4-agent debate for candidate intelligence pieces."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.daily_harvester.types import (
    CandidateInfo,
    SwarmVerdict,
    VerdictDecision,
)

logger = logging.getLogger(__name__)


def _budget_guard_check(task_type: str) -> bool:
    """Return True if budget allows the LLM call, False to skip."""
    try:
        from swarms_bot.routing.budget_guard import get_budget_guard

        return get_budget_guard().can_spend(task_type)
    except Exception:
        return True  # If budget guard fails, allow the call


async def run_prosecutor(candidate: CandidateInfo) -> list[str]:
    """
    PROSECUTOR agent: identify concerns and weaknesses in a candidate piece.

    Returns a list of concern strings.
    """
    from llm_client import chat

    prompt = f"""You are the PROSECUTOR in a 4-agent intelligence debate.

Candidate info:
- Title: {candidate.get("title", "")}
- Content: {candidate.get("content", "")}
- Topic: {candidate.get("topic", "unknown")}
- Source: {candidate.get("url", "unknown")}
- Source type: {candidate.get("source_type", "unknown")}
- Citations: {candidate.get("citations", 0)}

Your role: Find FLAWS. What is wrong, incomplete, contradicted, or questionable?
List 1-5 specific concerns. Be concrete and skeptical.
Reply with a JSON object: {{"concerns": ["concern 1", "concern 2", ...]}}"""

    try:
        if not _budget_guard_check("debate"):
            logger.warning("Budget exceeded — skipping Prosecutor for %s", candidate.get("candidate_id"))
            return ["Budget exceeded — candidate skipped"]
        response, _ = await chat(
            task=prompt,
            agent_key="debate",
            model_override="minimax/M2.7",
        )
        import json as _json

        data = _json.loads(response)
        return data.get("concerns", [])
    except Exception as e:
        logger.warning("Prosecutor failed: %s", e)
        return [f"Prosecutor error: {e}"]


async def run_defender(candidate: CandidateInfo, concerns: list[str]) -> list[str]:
    """
    DEFENDER agent: rebut the prosecutor's concerns.

    Returns a list of rebuttal strings.
    """
    from llm_client import chat

    prompt = f"""You are the DEFENDER in a 4-agent intelligence debate.

Candidate info:
- Title: {candidate.get("title", "")}
- Content: {candidate.get("content", "")}
- Topic: {candidate.get("topic", "unknown")}

Prosecutor's concerns:
{chr(10).join(f"- {c}" for c in concerns)}

Your role: DEFEND the candidate. For each concern, provide a counter-argument.
If a concern is valid, acknowledge it honestly but explain why the piece is still valuable.
Reply with a JSON object: {{"rebuttals": ["rebuttal 1", "rebuttal 2", ...]}}"""

    try:
        if not _budget_guard_check("debate"):
            logger.warning("Budget exceeded — skipping Defender for %s", candidate.get("candidate_id"))
            return ["Budget exceeded — candidate skipped"]
        response, _ = await chat(
            task=prompt,
            agent_key="debate",
            model_override="minimax/M2.7",
        )
        import json as _json

        data = _json.loads(response)
        return data.get("rebuttals", [])
    except Exception as e:
        logger.warning("Defender failed: %s", e)
        return [f"Defender error: {e}"]


async def run_fact_checker(candidate: CandidateInfo, concerns: list[str]) -> dict[str, Any]:
    """
    FACT_CHECKER agent: verify claims, find contradictions and supporting sources.

    Returns a dict with keys: result, contradiction_file, supporting_sources.
    """
    from llm_client import chat

    prompt = f"""You are the FACT_CHECKER in a 4-agent intelligence debate.

Candidate info:
- Title: {candidate.get("title", "")}
- Content: {candidate.get("content", "")}
- Topic: {candidate.get("topic", "unknown")}
- URL: {candidate.get("url", "")}

Concerns raised by the prosecutor:
{chr(10).join(f"- {c}" for c in concerns)}

Your role: VERIFY. Cross-reference against known facts, regulations, research.
Flag contradictions. Note any supporting sources found.
Reply with a JSON object:
{{
  "result": "VERIFIED | PARTIAL | CONTRADICTED | UNABLE_TO_VERIFY",
  "contradiction_file": "file_id if contradicted, else null",
  "supporting_sources": ["source1", "source2"]
}}"""

    try:
        if not _budget_guard_check("research"):
            logger.warning("Budget exceeded — skipping FactChecker for %s", candidate.get("candidate_id"))
            return {"result": "UNABLE_TO_VERIFY", "contradiction_file": None, "supporting_sources": []}
        response, _ = await chat(
            task=prompt,
            agent_key="researcher",
            model_override="anthropic/claude-sonnet-4",
        )
        import json as _json

        data = _json.loads(response)
        return {
            "result": data.get("result", "UNABLE_TO_VERIFY"),
            "contradiction_file": data.get("contradiction_file"),
            "supporting_sources": data.get("supporting_sources", []),
        }
    except Exception as e:
        logger.warning("Fact checker failed: %s", e)
        return {
            "result": "UNABLE_TO_VERIFY",
            "contradiction_file": None,
            "supporting_sources": [],
        }


async def run_judge(
    candidate: CandidateInfo,
    concerns: list[str],
    rebuttals: list[str],
    fact_check: dict[str, Any],
) -> SwarmVerdict:
    """
    JUDGE agent: render the final verdict after hearing all sides.

    Returns a SwarmVerdict dict.
    """
    from llm_client import chat

    prompt = f"""You are the JUDGE in a 4-agent intelligence debate.

Candidate:
- Title: {candidate.get("title", "")}
- Content: {candidate.get("content", "")}
- Topic: {candidate.get("topic", "unknown")}

PROSECUTOR concerns:
{chr(10).join(f"- {c}" for c in concerns)}

DEFENDER rebuttals:
{chr(10).join(f"- {r}" for r in rebuttals)}

FACT_CHECKER result: {fact_check.get("result", "unknown")}
Sources: {fact_check.get("supporting_sources", [])}

Render the FINAL VERDICT. Choose ONE:
- ACCEPT: solid, well-sourced, no major issues
- ACCEPT_WITH_CAVEAT: useful but with minor concerns noted
- SUPERSEDE: newer/more accurate info exists, supersedes prior entries
- REJECT: fundamentally flawed, unsupported, or contradicted
- NEEDS_MORE_RESEARCH: promising but insufficient verification

Also provide: confidence (0.0-1.0), reasoning (2-3 sentences), final_citations.

Reply JSON:
{{
  "verdict": "ACCEPT|ACCEPT_WITH_CAVEAT|SUPERSEDE|REJECT|NEEDS_MORE_RESEARCH",
  "confidence": 0.85,
  "reasoning": "...",
  "final_citations": ["source1", "source2"]
}}"""

    try:
        if not _budget_guard_check("analyst"):
            logger.warning("Budget exceeded — skipping Judge for %s", candidate.get("candidate_id"))
            return SwarmVerdict(
                candidate_id=candidate.get("candidate_id", ""),
                verdict=VerdictDecision.NEEDS_MORE_RESEARCH,
                confidence=0.0,
                concerns=concerns,
                rebuttals=rebuttals,
                fact_check_result=fact_check,
                reasoning="Budget exceeded",
                final_citations=[],
            )
        response, _ = await chat(
            task=prompt,
            agent_key="analyst",
            model_override="anthropic/claude-sonnet-4",
        )
        import json as _json

        data = _json.loads(response)

        verdict_str = data.get("verdict", "NEEDS_MORE_RESEARCH")
        try:
            verdict = VerdictDecision(verdict_str)
        except ValueError:
            verdict = VerdictDecision.NEEDS_MORE_RESEARCH

        return SwarmVerdict(
            candidate_id=candidate.get("candidate_id", ""),
            verdict=verdict,
            confidence=data.get("confidence", 0.5),
            concerns=concerns,
            rebuttals=rebuttals,
            fact_check_result=fact_check,
            reasoning=data.get("reasoning", ""),
            final_citations=data.get("final_citations", []),
        )
    except Exception as e:
        logger.warning("Judge failed: %s", e)
        return SwarmVerdict(
            candidate_id=candidate.get("candidate_id", ""),
            verdict=VerdictDecision.NEEDS_MORE_RESEARCH,
            confidence=0.0,
            concerns=concerns,
            rebuttals=rebuttals,
            fact_check_result=fact_check,
            reasoning=f"Judge error: {e}",
            final_citations=[],
        )


async def run_debate(candidate: CandidateInfo) -> SwarmVerdict:
    """
    Run the full 4-agent debate pipeline for a single candidate.
    Order: Prosecutor → Defender → FactChecker → Judge.
    """
    concerns = await run_prosecutor(candidate)
    await asyncio.sleep(0.5)

    rebuttals = await run_defender(candidate, concerns)
    await asyncio.sleep(0.5)

    fact_check = await run_fact_checker(candidate, concerns)
    await asyncio.sleep(0.5)

    verdict = await run_judge(candidate, concerns, rebuttals, fact_check)

    logger.info("Debate complete for %s: %s", candidate.get("candidate_id"), verdict["verdict"])
    return verdict


async def run_debate_batch(candidates: list[CandidateInfo], batch_size: int = 10) -> list[SwarmVerdict]:
    """
    Run debates for a list of candidates in parallel batches.
    """
    results: list[SwarmVerdict] = []

    for i in range(0, len(candidates), batch_size):
        batch = candidates[i : i + batch_size]
        verdicts = await asyncio.gather(*[run_debate(c) for c in batch])
        results.extend(verdicts)
        await asyncio.sleep(1)  # small pause between batches

    return results
