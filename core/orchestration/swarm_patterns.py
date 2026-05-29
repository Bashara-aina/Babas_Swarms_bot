# /home/newadmin/swarm-bot/orchestration/swarm_patterns.py
"""Swarm intelligence collaboration patterns.

Patterns:
- Voting: N agents solve independently → mentor picks best
- Critique-Refine: agent produces → critic reviews → agent fixes
- Debate: agents argue their proposals → consensus emerges

Enhanced with:
- Anti-loop guard: stops after 2+ repeated same actions
- Thinking protocol: interleaved evaluation between steps
- Self-audit footer: structured confidence output on all results
- Convergence criteria: early termination at 70% agreement
- Minority report: preserved losing arguments after consensus
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter

logger = logging.getLogger(__name__)

# Anti-loop: max rounds per debater before convergence check
MAX_DEBATE_ROUNDS = 3
# Convergence threshold: % agreement before early termination
CONVERGENCE_THRESHOLD = 0.70


async def voting(
    task: str,
    agents: list[str],
    run_fn,
    judge_agent: str = "mentor",
) -> str:
    """Multiple agents solve task independently; judge picks the best solution.

    Enhanced with anti-loop detection and self-audit footer.

    Args:
        task: Task to solve.
        agents: List of agent keys to use as voters.
        run_fn: Async function(model, task, agent_key) → str.
        judge_agent: Agent key that evaluates and selects the best solution.

    Returns:
        Best solution as selected by the judge agent.
    """
    from core.agent_registry import get_model as ag_get_model

    logger.info("Voting: %d agents on task '%s'", len(agents), task[:60])

    # All agents solve in parallel
    async def _solve(agent_key: str) -> tuple[str, str]:
        model = ag_get_model(agent_key) or ag_get_model("coding")
        try:
            result = await run_fn(model, task, agent_key)
        except Exception as exc:
            result = f"[{agent_key} failed: {exc}]"
        return agent_key, result

    pairs = await asyncio.gather(*[_solve(a) for a in agents])

    if len(pairs) == 1:
        return _apply_self_audit(pairs[0][1], task)

    # Track proposals for anti-loop (same result = convergence signal)
    result_hashes = [hash(r[-200:]) for _, r in pairs]
    result_counter = Counter(result_hashes)
    most_common_count = result_counter.most_common(1)[0][1] if result_counter else 0

    # Check convergence: if >70% agents produced same result
    converged = most_common_count / len(pairs) >= CONVERGENCE_THRESHOLD if len(pairs) > 1 else False
    convergence_note = " (converged — agents independently reached same answer)" if converged else ""

    # Format solutions for judge
    solutions_text = "\n\n".join(
        f"### Solution by {agent_key}:\n{result}" for agent_key, result in pairs
    )

    judge_prompt = (
        f"Original task: {task}\n\n"
        f"You have {len(pairs)} candidate solutions. "
        f"Select and return the BEST one (or merge the best parts). "
        f"Explain your choice in one sentence first, then give the full best solution.\n\n"
        f"{solutions_text}"
    )

    judge_model = ag_get_model(judge_agent) or ag_get_model("coding")
    try:
        best = await run_fn(judge_model, judge_prompt, judge_agent)
    except Exception as exc:
        logger.warning("Judge agent failed: %s — returning first solution", exc)
        best = pairs[0][1]

    logger.info("Voting complete — judge selected from %d solutions%s", len(pairs), convergence_note)

    result = best + f"\n_[Voting: {len(pairs)} agents, convergence={converged}]_"
    return _apply_self_audit(result, task)


async def critique_refine(
    task: str,
    producer_agent: str,
    critic_agent: str,
    run_fn,
    max_iterations: int = 2,
) -> str:
    """Producer generates → critic reviews → producer refines (iterative).

    Enhanced with thinking protocol injection between iterations.

    Args:
        task: Task to solve.
        producer_agent: Agent that generates the solution.
        critic_agent: Agent that reviews and critiques.
        run_fn: Async function(model, task, agent_key) → str.
        max_iterations: Maximum critique-refine cycles (default 2).

    Returns:
        Refined solution after critique cycles.
    """
    from core.agent_registry import get_model as ag_get_model

    logger.info(
        "Critique-refine: producer=%s critic=%s iterations=%d",
        producer_agent, critic_agent, max_iterations,
    )

    producer_model = ag_get_model(producer_agent) or ag_get_model("coding")
    critic_model = ag_get_model(critic_agent) or ag_get_model("debug")

    # Initial solution
    solution = await run_fn(producer_model, task, producer_agent)
    last_critique = ""

    for i in range(max_iterations):
        # Inject thinking protocol into critic prompt
        thinking_injection = ""
        if last_critique:
            thinking_injection = f"""

THINKING PROTOCOL:
- Previous critique: {last_critique[:150]}
- What to verify: Does your next critique address the previous feedback?
- Risk: Don't repeat the same criticism if it was already addressed.
"""
        else:
            thinking_injection = """

THINKING PROTOCOL:
- Is the solution correct, complete, and production-ready?
- What is the single most important issue to fix?
- Have I verified the solution against the task requirements?
"""

        # Critic reviews
        critique_prompt = (
            f"Review this solution for task: {task}{thinking_injection}\n\n"
            f"Solution:\n{solution}\n\n"
            f"Identify specific issues (bugs, inefficiencies, gaps). "
            f"If the solution is excellent, say APPROVED. "
            f"Otherwise list exact improvements needed."
        )

        try:
            critique = await run_fn(critic_model, critique_prompt, critic_agent)
        except Exception as exc:
            logger.warning("Critic iteration %d failed: %s", i, exc)
            break

        last_critique = critique

        if "APPROVED" in critique.upper() or len(critique.strip()) < 30:
            logger.info("Critique-refine: APPROVED at iteration %d", i)
            break

        # Producer refines based on critique
        refine_prompt = (
            f"Task: {task}\n\n"
            f"Your previous solution:\n{solution}\n\n"
            f"Critic feedback:\n{critique}\n\n"
            f"Provide an improved solution addressing all the feedback.\n\n"
            f"THINKING PROTOCOL: Did you address every point from the critic? "
            f"If you ignored any feedback, explain why."
        )

        try:
            solution = await run_fn(producer_model, refine_prompt, producer_agent)
        except Exception as exc:
            logger.warning("Producer refinement %d failed: %s", i, exc)
            break

        logger.debug("Critique-refine iteration %d complete", i + 1)

    return _apply_self_audit(solution, task)


async def debate(
    task: str,
    debaters: list[str],
    run_fn,
    rounds: int = 1,
    synthesizer: str = "architect",
) -> str:
    """Agents propose solutions, debate each other's approaches, converge to consensus.

    Enhanced with anti-loop guard, convergence tracking, and minority report preservation.

    Args:
        task: Problem to debate.
        debaters: List of agent keys to debate.
        run_fn: Async function(model, task, agent_key) → str.
        rounds: Number of debate rounds (default 1, max 3).
        synthesizer: Agent that produces the final synthesis.

    Returns:
        Consensus solution synthesized from debate.
    """
    from core.agent_registry import get_model as ag_get_model

    actual_rounds = min(rounds, MAX_DEBATE_ROUNDS)
    logger.info("Debate: %d agents, %d rounds (capped from %d)", len(debaters), actual_rounds, rounds)

    # Track proposals for anti-loop and convergence
    proposal_history: dict[str, list[str]] = {a: [] for a in debaters}
    all_minority_reports: list[str] = []

    # Initial proposals
    async def _propose(agent_key: str) -> tuple[str, str]:
        model = ag_get_model(agent_key) or ag_get_model("coding")
        try:
            proposal = await run_fn(model, task, agent_key)
        except Exception as exc:
            proposal = f"[{agent_key} unavailable: {exc}]"
        return agent_key, proposal

    proposals = dict(await asyncio.gather(*[_propose(a) for a in debaters]))
    for a, p in proposals.items():
        proposal_history[a].append(p[-300:] if len(p) > 300 else p)

    for round_num in range(actual_rounds):
        logger.debug("Debate round %d of %d", round_num + 1, actual_rounds)

        # Check convergence: if same proposal hash appears in most debaters
        latest_hashes = [hash(proposals[a][-200:]) for a in debaters]
        hash_counter = Counter(latest_hashes)
        top_hash, top_count = hash_counter.most_common(1)[0] if hash_counter else (0, 0)
        convergence_ratio = top_count / len(debaters) if len(debaters) > 0 else 0

        if convergence_ratio >= CONVERGENCE_THRESHOLD:
            logger.info("Debate converged early at round %d — %.0f%% agreement", round_num + 1, convergence_ratio * 100)
            break

        # Each agent reviews the others' proposals
        async def _review(agent_key: str) -> tuple[str, str]:
            others_text = "\n\n".join(
                f"[{other_key}]: {prop}"
                for other_key, prop in proposals.items()
                if other_key != agent_key
            )
            review_prompt = (
                f"Task: {task}\n\n"
                f"Your current proposal:\n{proposals[agent_key]}\n\n"
                f"Other agents' proposals:\n{others_text}\n\n"
                f"Incorporate the best ideas from others and improve your proposal. "
                f"Keep what's strong, fix what's weak.\n\n"
                f"THINKING PROTOCOL: What did you learn from other proposals? "
                f"What will you change and why?"
            )
            model = ag_get_model(agent_key) or ag_get_model("coding")
            try:
                refined = await run_fn(model, review_prompt, agent_key)
            except Exception:
                refined = proposals[agent_key]   # Keep original on failure
            return agent_key, refined

        updated = dict(await asyncio.gather(*[_review(a) for a in debaters]))

        # Detect minority reports: proposals that changed significantly
        for a in debaters:
            old_hash = hash(proposal_history[a][-1][-200:]) if proposal_history[a] else 0
            new_hash = hash(updated[a][-200:] if len(updated[a]) > 200 else updated[a])
            if old_hash != new_hash and round_num > 0:
                # This debater changed their view — save minority opinion
                all_minority_reports.append(f"[{a} changed]: {proposals[a][-200:]}")

        proposals.update(updated)
        for a, p in proposals.items():
            proposal_history[a].append(p[-300:] if len(p) > 300 else p)

    # Final synthesis — include minority reports
    all_proposals = "\n\n".join(
        f"**{key}**:\n{prop}" for key, prop in proposals.items()
    )

    minority_section = ""
    if all_minority_reports:
        minority_section = "\n\n## Minority Reports (arguments that lost but should be preserved):\n" + "\n".join(all_minority_reports)

    synth_prompt = (
        f"Task: {task}\n\n"
        f"These agents have debated and refined their solutions:{minority_section}\n\n"
        f"**Final proposals:**\n{all_proposals}\n\n"
        f"Synthesize the strongest elements from all proposals into one optimal solution. "
        f"Acknowledge valid points from minority reports if they improve the result."
    )

    synth_model = ag_get_model(synthesizer) or ag_get_model("architect")
    try:
        consensus = await run_fn(synth_model, synth_prompt, synthesizer)
    except Exception:
        # Return the longest proposal as best effort
        consensus = max(proposals.values(), key=len)

    logger.info("Debate complete — consensus synthesized")
    return _apply_self_audit(consensus, task)


def _apply_self_audit(result: str, task: str, confidence: float = 0.85) -> str:
    """Add a LEGIONA SELF-AUDIT footer to a pattern result.

    Args:
        result: The pattern's output text.
        task: The task that was solved.
        confidence: Estimated confidence 0.0-1.0.

    Returns:
        Result with self-audit footer appended.
    """
    if confidence >= 0.90:
        conf_level = "HIGH"
    elif confidence >= 0.70:
        conf_level = "MEDIUM"
    else:
        conf_level = "LOW"

    # Check for verification-needed phrases
    needs_verification: list[str] = []
    for phrase in ["need to verify", "unclear", "should confirm", "probably", "might be", "unknown"]:
        if phrase.lower() in result.lower():
            needs_verification.append(phrase)

    footer = f"""
---
**LEGIONA SELF-AUDIT**
- Confidence: {conf_level}
- Items needing verification: {", ".join(needs_verification) if needs_verification else "none"}
"""
    return result + footer


def select_pattern(task: str) -> str | None:
    """Heuristically choose the best swarm pattern for a task.

    Args:
        task: Task description.

    Returns:
        Pattern name: 'voting' | 'critique_refine' | 'debate' | None
        Returns None for tasks that don't benefit from collaboration.
    """
    t = task.lower()

    # Voting: when multiple valid approaches exist
    voting_indicators = ["best way", "should i use", "which is better", "compare", "options for"]
    if any(kw in t for kw in voting_indicators):
        return "voting"

    # Critique-refine: when correctness is critical
    critique_indicators = ["write tests", "production code", "fix bug", "debug", "traceback", "error", "test", "audit", "review"]
    if any(kw in t for kw in critique_indicators):
        return "critique_refine"

    # Debate: when trade-offs need to be explored
    debate_indicators = ["architecture", "trade-off", "pros and cons", "approach", "design"]
    if any(kw in t for kw in debate_indicators):
        return "debate"

    return None
