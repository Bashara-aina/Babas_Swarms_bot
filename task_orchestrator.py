# /home/newadmin/swarm-bot/task_orchestrator.py
"""Task chaining, scheduled monitoring, confirmation queue, and SwarmDebateOrchestrator.

Enables multi-step autonomous workflows:
    "Check terminal errors → fix code → restart service"
    "Monitor training every 5 minutes → alert on loss spike"

Also implements the 4-round SwarmDebateOrchestrator for /swarm.

Safety:
- Destructive commands always paused for /confirm yes|no
- Max 10 steps per chain
- Monitoring tasks can be cancelled with /cancel <task_id>
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

MAX_CHAIN_STEPS = 10


# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class TaskStep:
    description: str
    fn: Callable[..., Coroutine[Any, Any, str]]
    requires_confirmation: bool = False


@dataclass
class PendingConfirmation:
    action_id: str
    description: str
    fn: Callable[..., Coroutine[Any, Any, str]]
    created_at: float = field(default_factory=time.time)


@dataclass
class MonitorTask:
    task_id: str
    description: str
    interval_sec: int
    fn: Callable[..., Coroutine[Any, Any, str]]
    notify_fn: Callable[[str], Coroutine[Any, Any, None]]
    running: bool = True


# ── Global State ───────────────────────────────────────────────────────────────

_pending: dict[str, PendingConfirmation] = {}
_monitors: dict[str, MonitorTask] = {}
CONFIRMATION_TTL_SEC = 300


# ── Task Chain Execution ───────────────────────────────────────────────────────

async def execute_chain(
    steps: list[TaskStep],
    progress_fn: Callable[[str], Coroutine[Any, Any, None]],
    confirm_fn: Callable[[str, str], Coroutine[Any, Any, None]],
) -> str:
    if len(steps) > MAX_CHAIN_STEPS:
        raise ValueError(f"Chain exceeds max steps ({MAX_CHAIN_STEPS})")

    outputs: list[str] = []

    for i, step in enumerate(steps, 1):
        await progress_fn(f"Step {i}/{len(steps)}: {step.description}")

        if step.requires_confirmation:
            action_id = _queue_confirmation(step.description, step.fn)
            await confirm_fn(action_id, step.description)
            outputs.append(f"[Step {i} paused — waiting for /confirm yes {action_id}]")
            return "\n\n".join(outputs)

        try:
            result = await step.fn()
            outputs.append(f"[Step {i}] {step.description}\n{result}")
            logger.info("Chain step %d complete", i)
        except Exception as exc:
            logger.exception("Chain step %d failed: %s", i, exc)
            outputs.append(f"[Step {i} ERROR] {step.description}\nError: {exc}")
            break

    return "\n\n".join(outputs) if outputs else "Chain completed with no output."


# ── Confirmation Queue ─────────────────────────────────────────────────────────

def _queue_confirmation(description: str, fn: Callable) -> str:
    action_id = str(uuid.uuid4())[:8]
    _pending[action_id] = PendingConfirmation(
        action_id=action_id,
        description=description,
        fn=fn,
    )
    logger.info("Queued confirmation %s: %s", action_id, description)
    return action_id


def queue_confirmation(description: str, fn: Callable) -> str:
    return _queue_confirmation(description, fn)


async def confirm_action(action_id: str) -> str:
    _expire_old_confirmations()
    pending = _pending.pop(action_id, None)
    if pending is None:
        return f"No pending action '{action_id}' (may have expired after 5 min)"
    logger.info("Executing confirmed action %s: %s", action_id, pending.description)
    try:
        result = await pending.fn()
        return f"Confirmed: {pending.description}\n\n{result}"
    except Exception as exc:
        logger.exception("Confirmed action failed: %s", exc)
        return f"Action failed: {exc}"


def deny_action(action_id: str) -> str:
    pending = _pending.pop(action_id, None)
    if pending is None:
        return f"No pending action '{action_id}'"
    logger.info("Denied action %s: %s", action_id, pending.description)
    return f"Cancelled: {pending.description}"


def list_pending() -> str:
    _expire_old_confirmations()
    if not _pending:
        return "No pending confirmations."
    lines = ["<b>Pending Confirmations</b>\n"]
    for aid, p in _pending.items():
        age = int(time.time() - p.created_at)
        lines.append(
            f"  <code>{aid}</code> — {p.description} ({age}s ago)\n"
            f"  → <code>/confirm yes {aid}</code> or <code>/confirm no {aid}</code>"
        )
    return "\n\n".join(lines)


def _expire_old_confirmations() -> None:
    now = time.time()
    expired = [aid for aid, p in _pending.items() if now - p.created_at > CONFIRMATION_TTL_SEC]
    for aid in expired:
        logger.info("Expired confirmation %s", aid)
        del _pending[aid]


# ── Monitoring Tasks ───────────────────────────────────────────────────────────

async def start_monitor(
    description: str,
    interval_sec: int,
    fn: Callable[..., Coroutine[Any, Any, str]],
    notify_fn: Callable[[str], Coroutine[Any, Any, None]],
    alert_if: Optional[Callable[[str], bool]] = None,
) -> str:
    task_id = str(uuid.uuid4())[:8]
    monitor = MonitorTask(
        task_id=task_id,
        description=description,
        interval_sec=interval_sec,
        fn=fn,
        notify_fn=notify_fn,
        running=True,
    )
    _monitors[task_id] = monitor
    asyncio.create_task(_monitor_loop(monitor, alert_if), name=f"monitor-{task_id}")
    logger.info("Started monitor %s: %s (every %ds)", task_id, description, interval_sec)
    return task_id


async def _monitor_loop(
    monitor: MonitorTask,
    alert_if: Optional[Callable[[str], bool]],
) -> None:
    while monitor.running:
        try:
            result = await monitor.fn()
            should_notify = alert_if(result) if alert_if else True
            if should_notify:
                await monitor.notify_fn(
                    f"Monitor <b>{monitor.description}</b>\n\n<pre>{result[:2000]}</pre>"
                )
        except Exception as exc:
            logger.exception("Monitor %s error: %s", monitor.task_id, exc)
            await monitor.notify_fn(f"Monitor <b>{monitor.description}</b> error: {exc}")
        await asyncio.sleep(monitor.interval_sec)


def cancel_monitor(task_id: str) -> str:
    monitor = _monitors.pop(task_id, None)
    if monitor is None:
        return f"No monitor '{task_id}' found."
    monitor.running = False
    logger.info("Cancelled monitor %s: %s", task_id, monitor.description)
    return f"Stopped monitor: {monitor.description}"


def list_monitors() -> str:
    active = {tid: m for tid, m in _monitors.items() if m.running}
    if not active:
        return "No active monitors."
    lines = ["<b>Active Monitors</b>\n"]
    for tid, m in active.items():
        lines.append(
            f"  <code>{tid}</code> — {m.description} (every {m.interval_sec}s)\n"
            f"  → <code>/cancel {tid}</code>"
        )
    return "\n\n".join(lines)


def make_loss_spike_detector(threshold: float = 0.5) -> Callable[[str], bool]:
    def _detect(text: str) -> bool:
        matches = re.findall(r"loss[:\s=]+([0-9]+\.?[0-9]*)", text, re.IGNORECASE)
        for m in matches:
            try:
                if float(m) > threshold:
                    return True
            except ValueError:
                pass
        return "nan" in text.lower() or "inf" in text.lower()
    return _detect


# ── SwarmDebateOrchestrator ────────────────────────────────────────────────────

class SwarmDebateOrchestrator:
    """4-round debate system for /swarm.

    Round 1: Parallel divergence — all 6 agents give initial positions.
    Round 2: Cross-examination — each agent attacks one other and updates.
    Round 3: Judge synthesis — consensus, minority view, best argument, verdict.
    Round 4: Confidence ranking — each agent rates the verdict 1-10.

    Each persona uses its preferred model (see DEBATE_PERSONA_MODELS in agents.py)
    so reasoning styles are genuinely differentiated.
    """

    AGENTS = ["strategist", "devil_advocate", "researcher", "pragmatist", "visionary", "critic"]

    def __init__(
        self,
        llm_call: Callable[[str, str, str], Coroutine[Any, Any, str]],
        progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    ):
        self.llm_call = llm_call
        self.progress_fn = progress_fn

    async def _progress(self, msg: str):
        if self.progress_fn:
            await self.progress_fn(msg)
        logger.info("[SwarmDebate] %s", msg)

    async def _call_agent(self, agent_name: str, task: str, context: str = "") -> str:
        from agents import DEBATE_PERSONAS, DEBATE_PERSONA_MODELS, AGENT_MODELS, build_system_prompt
        persona = DEBATE_PERSONAS.get(agent_name, "You are a brilliant expert.")
        system = build_system_prompt(
            f"Your debate role: {persona}\n\n"
            "Give your position in 3-4 sharp sentences. Be opinionated. "
            "No hedging. If you disagree with conventional thinking, say so directly."
        )
        user_msg = f"Topic: {task}"
        if context:
            user_msg += f"\n\nContext from other agents:\n{context}"
        # Each persona uses its preferred model for differentiated reasoning
        model = DEBATE_PERSONA_MODELS.get(
            agent_name,
            AGENT_MODELS.get("general", "groq/llama-3.3-70b-versatile")
        )
        try:
            return await self.llm_call(model, system, user_msg)
        except Exception as e:
            logger.warning("Agent %s (model %s) failed: %s — falling back", agent_name, model, e)
            fallback = AGENT_MODELS.get("general", "groq/llama-3.3-70b-versatile")
            try:
                return await self.llm_call(fallback, system, user_msg)
            except Exception as e2:
                return f"[{agent_name} failed: {e2}]"

    async def run(self, task: str) -> dict:
        """Run full 4-round debate.

        Returns:
            dict with round1, round2, synthesis, confidence_scores
        """
        # ── ROUND 1: Parallel Divergence ────────────────────────────────────
        await self._progress("⚔️ Round 1/4 — Agents forming initial positions...")

        round1_tasks = [self._call_agent(agent, task) for agent in self.AGENTS]
        round1_results_raw = await asyncio.gather(*round1_tasks, return_exceptions=True)
        round1: dict[str, str] = {}
        for agent, result in zip(self.AGENTS, round1_results_raw):
            round1[agent] = f"[Error: {result}]" if isinstance(result, Exception) else result

        # ── ROUND 2: Cross-Examination ──────────────────────────────────────
        await self._progress("🔥 Round 2/4 — Cross-examination and position updates...")

        round1_summary = "\n\n".join(
            f"{agent.upper()}: {pos}" for agent, pos in round1.items()
        )
        round2_tasks = [
            self._call_agent(
                agent,
                task,
                context=(
                    f"Round 1 positions from all agents:\n{round1_summary}\n\n"
                    "Your job now: (a) identify the strongest flaw in ONE other agent's argument,"
                    " naming them explicitly. (b) Update your own position if any other agent "
                    "convinced you of something. Be specific and sharp."
                )
            )
            for agent in self.AGENTS
        ]
        round2_results_raw = await asyncio.gather(*round2_tasks, return_exceptions=True)
        round2: dict[str, str] = {}
        for agent, result in zip(self.AGENTS, round2_results_raw):
            round2[agent] = f"[Error: {result}]" if isinstance(result, Exception) else result

        # ── ROUND 3: Judge Synthesis ────────────────────────────────────────
        await self._progress("🏆 Round 3/4 — Judge synthesizing all positions...")

        from agents import AGENT_MODELS, build_system_prompt

        round2_summary = "\n\n".join(
            f"{agent.upper()} (Round 2): {pos}" for agent, pos in round2.items()
        )
        judge_system = build_system_prompt(
            "You are the debate Judge. You have read all agents' positions across 2 rounds."
            " Produce a structured synthesis with EXACTLY these sections (use these exact labels):\n"
            "CONSENSUS: [what all or most agree on]\n"
            "BEST_ARGUMENT: [the single strongest point made, with agent name]\n"
            "MINORITY_VIEW: [the dissenting view worth preserving]\n"
            "FINAL_RECOMMENDATION: [your verdict — direct and actionable]"
        )
        judge_msg = (
            f"Topic: {task}\n\n"
            f"Round 1 positions:\n{round1_summary}\n\n"
            f"Round 2 cross-examination:\n{round2_summary}"
        )
        # Warn if content is being truncated
        full_len = len(judge_msg)
        if full_len > 12000:
            logger.warning(
                "Judge context truncated: %d → 12000 chars (%d chars lost)",
                full_len, full_len - 12000
            )
        synthesis_raw = await self.llm_call(
            AGENT_MODELS["architect"],  # cerebras for large context synthesis
            judge_system,
            judge_msg[:12000],
        )

        synthesis = {
            "consensus":     _extract_section(synthesis_raw, "CONSENSUS"),
            "best_argument": _extract_section(synthesis_raw, "BEST_ARGUMENT"),
            "minority_view": _extract_section(synthesis_raw, "MINORITY_VIEW"),
            "verdict":       _extract_section(synthesis_raw, "FINAL_RECOMMENDATION"),
            "raw": synthesis_raw,
        }

        # ── ROUND 4: Confidence Ranking ─────────────────────────────────────
        await self._progress("📊 Round 4/4 — Agents rating the verdict...")

        verdict_text = synthesis.get("verdict") or synthesis_raw[:500]
        confidence_tasks = [
            self._call_agent(
                agent,
                task,
                context=(
                    f"The Judge's final verdict is:\n{verdict_text}\n\n"
                    "Rate this verdict from 1-10 and give ONE sentence justification."
                    " Format: SCORE: X/10 — [justification]"
                )
            )
            for agent in self.AGENTS
        ]
        confidence_raw = await asyncio.gather(*confidence_tasks, return_exceptions=True)
        confidence_scores: dict[str, str] = {}
        for agent, result in zip(self.AGENTS, confidence_raw):
            confidence_scores[agent] = "?/10" if isinstance(result, Exception) else result[:150]

        return {
            "round1": round1,
            "round2": round2,
            "synthesis": synthesis,
            "confidence_scores": confidence_scores,
        }


def _extract_section(text: str, section: str) -> str:
    """Extract a named section from structured LLM output.

    Handles all real-world Gemini/Cerebras output variants:
      FINAL_RECOMMENDATION: ...
      FINAL RECOMMENDATION: ...
      **FINAL_RECOMMENDATION**: ...
      Final Recommendation: ...
    Falls back to first 300 chars with a warning log.
    """
    # Build pattern that matches underscored or spaced version, optional bold markers
    section_pattern = section.replace("_", "[_ ]")  # FINAL_RECOMMENDATION → FINAL[_ ]RECOMMENDATION
    pattern = (
        rf'\*{{0,2}}{section_pattern}\*{{0,2}}'
        rf'[\s:]+'
        rf'(.*?)'
        rf'(?=\n\*{{0,2}}[A-Z][A-Z_\s]{{2,}}\*{{0,2}}[:\s]|\Z)'
    )
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if m:
        content = m.group(1).strip()
        logger.debug("Extracted section '%s': %d chars", section, len(content))
        return content
    logger.warning(
        "_extract_section: could not find '%s' in synthesis output — "
        "falling back to first 300 chars. Raw output snippet: %s",
        section, text[:200].replace("\n", " ")
    )
    return text[:300]


def format_debate_for_telegram(result: dict, task: str) -> list[str]:
    """Format a SwarmDebateOrchestrator result into Telegram message chunks.

    Returns a list of message strings (each <= 4096 chars) to send sequentially.
    """
    from agents import DEBATE_ICONS

    messages = []

    # Message 1: Round 1
    r1_lines = [f"🧠 **SWARM DEBATE — Round 1**\n**Topic:** {task[:200]}\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    for agent, pos in result["round1"].items():
        icon = DEBATE_ICONS.get(agent, "🤖")
        r1_lines.append(f"{icon} **{agent.upper().replace('_', ' ')}**:\n{pos[:400]}\n")
    messages.append("\n".join(r1_lines))

    # Message 2: Round 2
    r2_lines = ["🔥 **SWARM DEBATE — Round 2: Cross-Examination**\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    for agent, pos in result["round2"].items():
        icon = DEBATE_ICONS.get(agent, "🤖")
        r2_lines.append(f"{icon} **{agent.upper().replace('_', ' ')}** (updated):\n{pos[:400]}\n")
    messages.append("\n".join(r2_lines))

    # Message 3: Synthesis + Confidence
    s = result["synthesis"]
    conf = result["confidence_scores"]
    conf_line = " · ".join(
        f"{a.replace('_', ' ').title()} {_parse_score(v)}"
        for a, v in conf.items()
    )
    synth_msg = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 **JUDGE'S SYNTHESIS**\n\n"
        f"**Consensus**: {s.get('consensus', 'N/A')}\n\n"
        f"**Best argument**: {s.get('best_argument', 'N/A')}\n\n"
        f"**Minority view**: {s.get('minority_view', 'N/A')}\n\n"
        f"**VERDICT**: {s.get('verdict', 'N/A')}\n\n"
        f"**Confidence scores**: {conf_line}"
    )
    messages.append(synth_msg)

    return messages


def _parse_score(text: str) -> str:
    """Extract X/10 or X.Y/10 from confidence text."""
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)/10', text)
    return m.group(0) if m else "?/10"
