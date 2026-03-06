# /home/newadmin/swarm-bot/orchestration/swarm_patterns.py
"""Swarm intelligence collaboration patterns.

Patterns:
- Voting: N agents solve independently → mentor picks best
- Critique-Refine: agent produces → critic reviews → agent fixes
- Debate: agents argue their proposals → consensus emerges
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def voting(
    task: str,
    agents: list[str],
    run_fn,
    judge_agent: str = "mentor",
) -> str:
    """Multiple agents solve task independently; judge picks the best solution.

    Args:
        task: Task to solve.
        agents: List of agent keys to use as voters.
        run_fn: Async function(model, task, agent_key) → str.
        judge_agent: Agent key that evaluates and selects the best solution.

    Returns:
        Best solution as selected by the judge agent.
    """
    import agents as ag

    logger.info("Voting: %d agents on task '%s'", len(agents), task[:60])

    # All agents solve in parallel
    async def _solve(agent_key: str) -> tuple[str, str]:
        model = ag.get_model(agent_key) or ag.get_model("coding")
        try:
            result = await run_fn(model, task, agent_key)
        except Exception as exc:
            result = f"[{agent_key} failed: {exc}]"
        return agent_key, result

    pairs = await asyncio.gather(*[_solve(a) for a in agents])

    if len(pairs) == 1:
        return pairs[0][1]

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

    judge_model = ag.get_model(judge_agent) or ag.get_model("coding")
    try:
        best = await run_fn(judge_model, judge_prompt, judge_agent)
    except Exception as exc:
        logger.warning("Judge agent failed: %s — returning first solution", exc)
        best = pairs[0][1]

    logger.info("Voting complete — judge selected from %d solutions", len(pairs))
    return best


async def critique_refine(
    task: str,
    producer_agent: str,
    critic_agent: str,
    run_fn,
    max_iterations: int = 2,
) -> str:
    """Producer generates → critic reviews → producer refines (iterative).

    Args:
        task: Task to solve.
        producer_agent: Agent that generates the solution.
        critic_agent: Agent that reviews and critiques.
        run_fn: Async function(model, task, agent_key) → str.
        max_iterations: Maximum critique-refine cycles (default 2).

    Returns:
        Refined solution after critique cycles.
    """
    import agents as ag

    logger.info(
        "Critique-refine: producer=%s critic=%s iterations=%d",
        producer_agent, critic_agent, max_iterations,
    )

    producer_model = ag.get_model(producer_agent) or ag.get_model("coding")
    critic_model = ag.get_model(critic_agent) or ag.get_model("debug")

    # Initial solution
    solution = await run_fn(producer_model, task, producer_agent)

    for i in range(max_iterations):
        # Critic reviews
        critique_prompt = (
            f"Review this solution for task: {task}\n\n"
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

        if "APPROVED" in critique.upper() or len(critique.strip()) < 30:
            logger.info("Critique-refine: APPROVED at iteration %d", i)
            break

        # Producer refines based on critique
        refine_prompt = (
            f"Task: {task}\n\n"
            f"Your previous solution:\n{solution}\n\n"
            f"Critic feedback:\n{critique}\n\n"
            f"Provide an improved solution addressing all the feedback."
        )

        try:
            solution = await run_fn(producer_model, refine_prompt, producer_agent)
        except Exception as exc:
            logger.warning("Producer refinement %d failed: %s", i, exc)
            break

        logger.debug("Critique-refine iteration %d complete", i + 1)

    return solution


async def debate(
    task: str,
    debaters: list[str],
    run_fn,
    rounds: int = 1,
    synthesizer: str = "architect",
) -> str:
    """Agents propose solutions, debate each other's approaches, converge to consensus.

    Args:
        task: Problem to debate.
        debaters: List of agent keys to debate.
        run_fn: Async function(model, task, agent_key) → str.
        rounds: Number of debate rounds (default 1).
        synthesizer: Agent that produces the final synthesis.

    Returns:
        Consensus solution synthesized from debate.
    """
    import agents as ag

    logger.info("Debate: %d agents, %d rounds", len(debaters), rounds)

    # Initial proposals
    async def _propose(agent_key: str) -> tuple[str, str]:
        model = ag.get_model(agent_key) or ag.get_model("coding")
        try:
            proposal = await run_fn(model, task, agent_key)
        except Exception as exc:
            proposal = f"[{agent_key} unavailable: {exc}]"
        return agent_key, proposal

    proposals = dict(await asyncio.gather(*[_propose(a) for a in debaters]))

    for round_num in range(rounds):
        logger.debug("Debate round %d", round_num + 1)

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
                f"Keep what's strong, fix what's weak."
            )
            model = ag.get_model(agent_key) or ag.get_model("coding")
            try:
                refined = await run_fn(model, review_prompt, agent_key)
            except Exception as exc:
                refined = proposals[agent_key]   # Keep original on failure
            return agent_key, refined

        updated = dict(await asyncio.gather(*[_review(a) for a in debaters]))
        proposals.update(updated)

    # Final synthesis
    all_proposals = "\n\n".join(
        f"**{key}**:\n{prop}" for key, prop in proposals.items()
    )
    synth_prompt = (
        f"Task: {task}\n\n"
        f"These agents have debated and refined their solutions:\n\n{all_proposals}\n\n"
        f"Synthesize the strongest elements from all proposals into one optimal solution."
    )

    synth_model = ag.get_model(synthesizer) or ag.get_model("architect")
    try:
        consensus = await run_fn(synth_model, synth_prompt, synthesizer)
    except Exception:
        # Return the longest proposal as best effort
        consensus = max(proposals.values(), key=len)

    logger.info("Debate complete — consensus synthesized")
    return consensus


def select_pattern(task: str) -> Optional[str]:
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
    critique_indicators = ["write tests", "production code", "fix bug", "debug", "traceback", "error"]
    if any(kw in t for kw in critique_indicators) and len(task) > 100:
        return "critique_refine"

    # Debate: when trade-offs need to be explored
    debate_indicators = ["architecture", "design", "trade-off", "pros and cons", "approach"]
    if any(kw in t for kw in debate_indicators) and len(task) > 80:
        return "debate"

    return None
