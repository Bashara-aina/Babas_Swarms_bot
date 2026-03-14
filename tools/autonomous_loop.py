"""Autonomous loop — multi-iteration goal pursuit with safety bounds.

Usage from Telegram:
  /loop <goal>           — start autonomous execution
  /loop_stop             — kill the running loop

Safety bounds:
  max_iterations   = 25   (each iteration = plan + execute cycle)
  cost_ceiling_usd = 0.50 (estimated via litellm token pricing)
  timeout_minutes  = 30
  progress update every 5 iterations
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

import litellm

logger = logging.getLogger(__name__)

# Type alias for Telegram message callback
NotifyCb = Callable[[str], Coroutine[Any, Any, None]]


@dataclass
class LoopConfig:
    max_iterations: int = 25
    cost_ceiling_usd: float = 0.50
    timeout_minutes: float = 30
    progress_every: int = 5


@dataclass
class LoopState:
    """Mutable state for a running loop."""
    goal: str = ""
    iteration: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    estimated_cost_usd: float = 0.0
    start_time: float = 0.0
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)
    history: list[str] = field(default_factory=list)
    last_result: str = ""
    model_used: str = ""
    status: str = "idle"  # idle | running | stopped | completed | error


# Global registry: user_id → LoopState (single loop per user)
_active_loops: dict[int, LoopState] = {}


def get_active_loop(user_id: int) -> Optional[LoopState]:
    state = _active_loops.get(user_id)
    if state and state.status == "running":
        return state
    return None


def get_loop_state(user_id: int) -> Optional[LoopState]:
    """Get loop state regardless of status (for status queries)."""
    return _active_loops.get(user_id)


def stop_loop(user_id: int) -> bool:
    """Signal a running loop to stop. Returns True if there was one."""
    state = _active_loops.get(user_id)
    if state and state.status == "running":
        state.stop_event.set()
        return True
    return False


def pause_loop(user_id: int) -> bool:
    """Pause a running loop. Returns True if there was one."""
    state = _active_loops.get(user_id)
    if state and state.status == "running":
        state.status = "paused"
        return True
    return False


def resume_loop(user_id: int) -> bool:
    """Resume a paused loop. Returns True if there was one."""
    state = _active_loops.get(user_id)
    if state and state.status == "paused":
        state.status = "running"
        return True
    return False


def format_loop_status_html(state: LoopState) -> str:
    """Format loop status as HTML for Telegram."""
    elapsed_min = (time.time() - state.start_time) / 60 if state.start_time else 0

    status_icon = {
        "idle": "⚪", "running": "🔄", "paused": "⏸️",
        "stopped": "🛑", "completed": "✅", "error": "❌",
    }.get(state.status, "⚪")

    lines = [
        f"{status_icon} <b>Loop Status</b>\n",
        f"Goal: <code>{state.goal[:150]}</code>",
        f"Status: {state.status}",
        f"Iteration: {state.iteration}",
        f"Elapsed: {elapsed_min:.1f} min",
        f"Est. cost: ${state.estimated_cost_usd:.4f}",
        f"Model: {state.model_used or 'n/a'}",
    ]

    if state.history:
        lines.append("\n<b>Recent steps:</b>")
        for i, h in enumerate(state.history[-5:], 1):
            lines.append(f"  {i}. <code>{h[:100]}</code>")

    if state.status == "running":
        lines.append("\nCommands: /loop_stop | /loop_pause")
    elif state.status == "paused":
        lines.append("\nCommands: /loop_resume | /loop_stop")

    return "\n".join(lines)


def _estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate cost using litellm's cost tracking. Returns 0 for free/unknown."""
    try:
        return litellm.completion_cost(
            model=model,
            prompt_tokens=tokens_in,
            completion_tokens=tokens_out,
        )
    except Exception:
        # Free tier or unknown model — use conservative estimate
        # ~$0.0001 per 1K tokens as a rough floor
        return (tokens_in + tokens_out) * 0.0000001


async def run_autonomous_loop(
    user_id: int,
    goal: str,
    notify_cb: NotifyCb,
    config: LoopConfig | None = None,
    thread_id: Optional[str] = None,
) -> LoopState:
    """Run an autonomous plan-execute loop until the goal is done or bounds hit.

    Each iteration:
      1. Ask the planner LLM: "Given the goal and history, what's the next step?
         Reply DONE if finished."
      2. If DONE → stop
      3. Otherwise execute the step via agent_loop() (with computer tools)
      4. Record result, check bounds, repeat

    Returns the final LoopState.
    """
    from llm_client import chat, agent_loop

    cfg = config or LoopConfig()
    state = LoopState(
        goal=goal,
        start_time=time.time(),
        status="running",
    )
    _active_loops[user_id] = state

    # Build the planner prompt (no tools — just planning)
    planner_system = (
        "You are an autonomous task planner. You receive a GOAL and a HISTORY "
        "of steps already completed. Your job:\n"
        "1. Decide the NEXT concrete step to accomplish the goal.\n"
        "2. Output ONLY the step as a direct instruction (e.g. 'Run pytest and check for failures').\n"
        "3. If the goal is fully accomplished, output exactly: DONE\n"
        "4. If you're stuck or the goal is impossible, output exactly: STUCK: <reason>\n\n"
        "Keep steps small and actionable. Each step should be one clear action."
    )

    try:
        for iteration in range(1, cfg.max_iterations + 1):
            # ── Check stop signal ────────────────────────────────
            if state.stop_event.is_set():
                state.status = "stopped"
                await notify_cb(
                    f"<b>Loop stopped</b> by user after {state.iteration} iterations.\n"
                    f"Cost: ~${state.estimated_cost_usd:.4f}"
                )
                return state

            # ── Check pause ──────────────────────────────────────
            while state.status == "paused":
                await asyncio.sleep(2)
                if state.stop_event.is_set():
                    state.status = "stopped"
                    await notify_cb(
                        f"<b>Loop stopped</b> while paused after {state.iteration} iterations.\n"
                        f"Cost: ~${state.estimated_cost_usd:.4f}"
                    )
                    return state

            # ── Check timeout ────────────────────────────────────
            elapsed_min = (time.time() - state.start_time) / 60
            if elapsed_min > cfg.timeout_minutes:
                state.status = "stopped"
                await notify_cb(
                    f"<b>Loop timeout</b> ({cfg.timeout_minutes}min) after "
                    f"{state.iteration} iterations.\nCost: ~${state.estimated_cost_usd:.4f}"
                )
                return state

            # ── Check cost ceiling ───────────────────────────────
            if state.estimated_cost_usd >= cfg.cost_ceiling_usd:
                state.status = "stopped"
                await notify_cb(
                    f"<b>Cost ceiling hit</b> (${cfg.cost_ceiling_usd:.2f}) after "
                    f"{state.iteration} iterations."
                )
                return state

            state.iteration = iteration

            # ── Phase 1: Plan next step ──────────────────────────
            history_text = "\n".join(
                f"  Step {i+1}: {h}" for i, h in enumerate(state.history[-10:])
            )
            planner_prompt = (
                f"{planner_system}\n\n"
                f"GOAL: {goal}\n\n"
                f"HISTORY ({len(state.history)} steps done):\n"
                f"{history_text or '  (none yet)'}\n\n"
                f"What is the next step?"
            )

            try:
                plan_text, plan_model = await chat(
                    planner_prompt,
                    agent_key="architect",
                    thread_id=thread_id,
                )
            except Exception as e:
                logger.error("Loop planner error: %s", e)
                state.history.append(f"[planner error: {e}]")
                continue

            plan_text = plan_text.strip()
            state.model_used = plan_model

            # ── Check if done ────────────────────────────────────
            if plan_text.upper().startswith("DONE"):
                state.status = "completed"
                elapsed = (time.time() - state.start_time) / 60
                await notify_cb(
                    f"<b>Loop completed</b> in {iteration} iterations "
                    f"({elapsed:.1f}min)\n"
                    f"Cost: ~${state.estimated_cost_usd:.4f}\n\n"
                    f"Last result:\n{state.last_result[:2000]}"
                )
                return state

            # ── Check if stuck ───────────────────────────────────
            if plan_text.upper().startswith("STUCK"):
                state.status = "error"
                await notify_cb(
                    f"<b>Loop stuck</b> at iteration {iteration}:\n"
                    f"<code>{plan_text[:500]}</code>"
                )
                return state

            # ── Phase 2: Execute the step ────────────────────────
            try:
                exec_result, exec_model = await agent_loop(
                    plan_text,
                    max_iterations=10,  # sub-loop cap per step
                    thread_id=thread_id,
                )
            except Exception as e:
                exec_result = f"execution error: {e}"
                exec_model = "error"
                logger.error("Loop execution error at step %d: %s", iteration, e)

            # ── Track tokens/cost ────────────────────────────────
            # litellm tracks usage globally; we estimate per-call
            step_cost = _estimate_cost(exec_model, 500, 500)  # rough per-step
            state.estimated_cost_usd += step_cost

            # ── Record result ────────────────────────────────────
            summary = f"{plan_text[:80]} → {exec_result[:120]}"
            state.history.append(summary)
            state.last_result = exec_result

            logger.info(
                "Loop[%d/%d] cost=$%.4f step: %s",
                iteration, cfg.max_iterations, state.estimated_cost_usd, summary[:100],
            )

            # ── Progress update every N iterations ───────────────
            if iteration % cfg.progress_every == 0:
                elapsed = (time.time() - state.start_time) / 60
                recent = "\n".join(
                    f"  {i+1}. {h[:100]}"
                    for i, h in enumerate(state.history[-cfg.progress_every:])
                )
                await notify_cb(
                    f"<b>Loop progress</b> — iteration {iteration}/{cfg.max_iterations}\n"
                    f"Elapsed: {elapsed:.1f}min | Cost: ~${state.estimated_cost_usd:.4f}\n\n"
                    f"Recent steps:\n<code>{recent}</code>"
                )

        # ── Exhausted iterations ─────────────────────────────────
        state.status = "completed"
        elapsed = (time.time() - state.start_time) / 60
        await notify_cb(
            f"<b>Loop finished</b> — hit max {cfg.max_iterations} iterations "
            f"({elapsed:.1f}min)\n"
            f"Cost: ~${state.estimated_cost_usd:.4f}\n\n"
            f"Last result:\n{state.last_result[:2000]}"
        )
        return state

    except Exception as e:
        state.status = "error"
        logger.exception("Autonomous loop crashed: %s", e)
        await notify_cb(
            f"<b>Loop error</b> at iteration {state.iteration}:\n"
            f"<code>{str(e)[:500]}</code>"
        )
        return state
    finally:
        # Clean up — leave state in registry for status queries
        if state.status == "running":
            state.status = "error"
