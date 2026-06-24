"""
Legion Orchestrator — consolidated single entry point.

Merges unique value from 4 legacy orchestrators:
  - task_orchestrator.py      → Task chains, confirmation queue, monitors, SwarmDebateOrchestrator
  - core/legion_swarm.py      → 3-phase parallel swarm (dynamic team from AgentRegistry)  # type: ignore[reportAttributeAccessIssue]
  - core/nexus_orchestrator.py→ 3-layer routing (keyword → semantic → LLM fallback)
  - core/jarvis_orchestrator.py→ Context bundle (memory, Screenpipe, WhatsApp, calendar)

Single canonical entry point: LegionOrchestrator.run(task, user_id)
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models shared across orchestrators
# ---------------------------------------------------------------------------


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


@dataclass
class RoutingDecision:
    """Result of a routing determination."""

    agent: Any  # AgentDef
    confidence: float
    method: str  # "keyword" | "semantic" | "llm_fallback" | "department_override"
    reasoning: str


@dataclass
class AgentResult:
    key: str
    name: str
    output: str
    latency_ms: float
    success: bool
    error: str = ""


@dataclass
class SwarmReport:
    phase1_outputs: dict[str, str]
    phase2_outputs: dict[str, str]
    final_synthesis: str
    agent_results: list[AgentResult]
    total_latency_ms: float
    topology_used: str = "legion-swarm"


# ---------------------------------------------------------------------------
# Global state (from task_orchestrator.py)
# ---------------------------------------------------------------------------

_pending: dict[str, PendingConfirmation] = {}
_monitors: dict[str, MonitorTask] = {}
CONFIRMATION_TTL_SEC = 300
MAX_CHAIN_STEPS = 10


# ---------------------------------------------------------------------------
# Task chain execution (from task_orchestrator.py)
# ---------------------------------------------------------------------------


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
            try:
                from core.self_evolution import get_self_evolution_engine
                engine = get_self_evolution_engine()
                await engine.record_failure(
                    task=step.description,
                    approach="execute_chain step",
                    failure_mode=f"{type(exc).__name__}: {exc}",
                    root_cause="Exception in chain step execution",
                    fix_applied="Chain halted at failed step",
                    prevention_rule="Validate step inputs before execution; wrap async calls with timeouts",
                )
            except Exception:
                pass
            outputs.append(f"[Step {i} ERROR] {step.description}\nError: {exc}")
            break

    return "\n\n".join(outputs) if outputs else "Chain completed with no output."


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


# ---------------------------------------------------------------------------
# Monitoring tasks (from task_orchestrator.py)
# ---------------------------------------------------------------------------


async def start_monitor(
    description: str,
    interval_sec: int,
    fn: Callable[..., Coroutine[Any, Any, str]],
    notify_fn: Callable[[str], Coroutine[Any, Any, None]],
    alert_if: Callable[[str], bool] | None = None,
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
    alert_if: Callable[[str], bool] | None,
) -> None:
    while monitor.running:
        try:
            result = await monitor.fn()
            should_notify = alert_if(result) if alert_if else True
            if should_notify:
                await monitor.notify_fn(f"Monitor <b>{monitor.description}</b>\n\n<pre>{result[:2000]}</pre>")
        except Exception as exc:
            logger.exception("Monitor %s error: %s", monitor.task_id, exc)
            try:
                from core.self_evolution import get_self_evolution_engine
                engine = get_self_evolution_engine()
                await engine.record_failure(
                    task=monitor.description,
                    approach=f"monitor loop(task_id={monitor.task_id})",
                    failure_mode=f"{type(exc).__name__}: {exc}",
                    root_cause="Exception in monitor task loop",
                    fix_applied="Error logged; monitor continues running",
                    prevention_rule="Wrap monitor function with timeouts; ensure monitor fn handles its own exceptions",
                )
            except Exception:
                pass
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
            f"  <code>{tid}</code> — {m.description} (every {m.interval_sec}s)\n  → <code>/cancel {tid}</code>"
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


# ---------------------------------------------------------------------------
# SwarmDebateOrchestrator — 4-round debate (from task_orchestrator.py)
# ---------------------------------------------------------------------------


class SwarmDebateOrchestrator:
    """4-round debate system for /swarm.

    Round 1: Parallel divergence — all 6 agents give initial positions.
    Round 2: Cross-examination — each agent attacks one other and updates.
    Round 3: Judge synthesis — consensus, minority view, best argument, verdict.
    Round 4: Confidence ranking — each agent rates the verdict 1-10.
    """

    AGENTS = ["strategist", "devil_advocate", "researcher", "pragmatist", "visionary", "critic"]

    def __init__(
        self,
        llm_call: Callable[[str, str, str], Coroutine[Any, Any, str]],
        progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
    ):
        self.llm_call = llm_call
        self.progress_fn = progress_fn

    async def _progress(self, msg: str) -> None:
        if self.progress_fn:
            await self.progress_fn(msg)
        logger.info("[SwarmDebate] %s", msg)

    async def _call_agent(self, agent_name: str, task: str, context: str = "") -> str:
        from agents import DEBATE_PERSONA_MODELS, DEBATE_PERSONAS, build_system_prompt
        from core.agent_registry import MODEL_LOOKUP

        persona = DEBATE_PERSONAS.get(agent_name, "You are a brilliant expert.")
        system = build_system_prompt(
            f"Your debate role: {persona}\n\n"
            "Give your position in 3-4 sharp sentences. Be opinionated. "
            "No hedging. If you disagree with conventional thinking, say so directly."
        )
        user_msg = f"Topic: {task}"
        if context:
            user_msg += f"\n\nContext from other agents:\n{context}"
        model = DEBATE_PERSONA_MODELS.get(
            agent_name,
            MODEL_LOOKUP.get("minimax-m3", "opencode-go/minimax-m3"),
        )
        try:
            return await self.llm_call(model, system, user_msg)
        except Exception as e:
            logger.warning("Agent %s (model %s) failed: %s — falling back", agent_name, model, e)
            fallback = MODEL_LOOKUP.get("nemotron-free", MODEL_LOOKUP.get("minimax-m3", "opencode-go/minimax-m3"))
            try:
                return await self.llm_call(fallback, system, user_msg)
            except Exception as e2:
                return f"[{agent_name} failed: {e2}]"

    async def run(self, task: str) -> dict:
        """Run full 4-round debate. Returns dict with round1, round2, synthesis, confidence_scores."""
        # ── ROUND 1: Parallel Divergence ──────────────────────────────────────
        await self._progress("⚔️ Round 1/4 — Agents forming initial positions...")

        round1_tasks = [self._call_agent(agent, task) for agent in self.AGENTS]
        round1_results_raw = await asyncio.gather(*round1_tasks, return_exceptions=True)
        round1: dict[str, str] = {}
        for agent, result in zip(self.AGENTS, round1_results_raw, strict=False):
            round1[agent] = f"[Error: {result}]" if isinstance(result, Exception) else result  # type: ignore[reportArgumentType]

        # ── ROUND 2: Cross-Examination ───────────────────────────────────────
        await self._progress("🔥 Round 2/4 — Cross-examination and position updates...")

        round1_summary = "\n\n".join(f"{agent.upper()}: {pos}" for agent, pos in round1.items())
        round2_tasks = [
            self._call_agent(
                agent,
                task,
                context=(
                    f"Round 1 positions from all agents:\n{round1_summary}\n\n"
                    "Your job now: (a) identify the strongest flaw in ONE other agent's argument, "
                    "naming them explicitly. (b) Update your own position if any other agent "
                    "convinced you of something. Be specific and sharp."
                ),
            )
            for agent in self.AGENTS
        ]
        round2_results_raw = await asyncio.gather(*round2_tasks, return_exceptions=True)
        round2: dict[str, str] = {}
        for agent, result in zip(self.AGENTS, round2_results_raw, strict=False):
            round2[agent] = f"[Error: {result}]" if isinstance(result, Exception) else result  # type: ignore[reportArgumentType]

        # ── ROUND 3: Judge Synthesis ─────────────────────────────────────────
        await self._progress("🏆 Round 3/4 — Judge synthesizing all positions...")

        from core.agent_registry import MODEL_LOOKUP

        round2_summary = "\n\n".join(f"{agent.upper()} (Round 2): {pos}" for agent, pos in round2.items())
        judge_system = (
            "You are the debate Judge. You have read all agents' positions across 2 rounds.\n"
            "Produce a structured synthesis with EXACTLY these sections (use these exact labels):\n"
            "CONSENSUS: [what all or most agree on]\n"
            "BEST_ARGUMENT: [the single strongest point made, with agent name]\n"
            "MINORITY_VIEW: [the dissenting view worth preserving]\n"
            "FINAL_RECOMMENDATION: [your verdict — direct and actionable]"
        )
        judge_msg = (
            f"Topic: {task}\n\nRound 1 positions:\n{round1_summary}\n\nRound 2 cross-examination:\n{round2_summary}"
        )

        full_len = len(judge_msg)
        if full_len > 12000:
            logger.warning(
                "Judge context truncated: %d → 12000 chars (%d chars lost)",
                full_len,
                full_len - 12000,
            )
        synthesis_raw = await self.llm_call(
            MODEL_LOOKUP.get("minimax-m3", "opencode-go/minimax-m3"),
            judge_system,
            judge_msg[:12000],
        )

        synthesis = {
            "consensus": _extract_section(synthesis_raw, "CONSENSUS"),
            "best_argument": _extract_section(synthesis_raw, "BEST_ARGUMENT"),
            "minority_view": _extract_section(synthesis_raw, "MINORITY_VIEW"),
            "verdict": _extract_section(synthesis_raw, "FINAL_RECOMMENDATION"),
            "raw": synthesis_raw,
        }

        # ── ROUND 4: Confidence Ranking ───────────────────────────────────────
        await self._progress("📊 Round 4/4 — Agents rating the verdict...")

        verdict_text = synthesis.get("verdict") or synthesis_raw[:500]
        confidence_tasks = [
            self._call_agent(
                agent,
                task,
                context=(
                    f"The Judge's final verdict is:\n{verdict_text}\n\n"
                    "Rate this verdict from 1-10 and give ONE sentence justification. "
                    "Format: SCORE: X/10 — [justification]"
                ),
            )
            for agent in self.AGENTS
        ]
        confidence_raw = await asyncio.gather(*confidence_tasks, return_exceptions=True)
        confidence_scores: dict[str, str] = {}
        for agent, result in zip(self.AGENTS, confidence_raw, strict=False):
            confidence_scores[agent] = "?/10" if isinstance(result, Exception) else result[:150]  # type: ignore[reportIndexIssue]

        return {
            "round1": round1,
            "round2": round2,
            "synthesis": synthesis,
            "confidence_scores": confidence_scores,
        }


def _extract_section(text: str, section: str) -> str:
    """Extract a named section from structured LLM output."""
    section_pattern = section.replace("_", "[_ ]")
    pattern = (
        rf"\*{{0,2}}{section_pattern}\*{{0,2}}"
        rf"[\s:]+"
        rf"(.*?)"
        rf"(?=\n\*{{0,2}}[A-Z][A-Z_\s]{{2,}}\*{{0,2}}[:\s]|\Z)"
    )
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if m:
        content = m.group(1).strip()
        logger.debug("Extracted section '%s': %d chars", section, len(content))
        return content
    logger.warning(
        "_extract_section: could not find '%s' in synthesis output — "
        "falling back to first 300 chars. Raw output snippet: %s",
        section,
        text[:200].replace("\n", " "),
    )
    return text[:300]


def format_debate_for_telegram(result: dict, task: str) -> list[str]:
    """Format a SwarmDebateOrchestrator result into Telegram message chunks."""
    from agents import DEBATE_ICONS

    messages = []

    r1_lines = [f"🧠 **SWARM DEBATE — Round 1**\n**Topic:** {task[:200]}\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    for agent, pos in result["round1"].items():
        icon = DEBATE_ICONS.get(agent, "🤖")
        r1_lines.append(f"{icon} **{agent.upper().replace('_', ' ')}**:\n{pos[:400]}\n")
    messages.append("\n".join(r1_lines))

    r2_lines = ["🔥 **SWARM DEBATE — Round 2: Cross-Examination**\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    for agent, pos in result["round2"].items():
        icon = DEBATE_ICONS.get(agent, "🤖")
        r2_lines.append(f"{icon} **{agent.upper().replace('_', ' ')}** (updated):\n{pos[:400]}\n")
    messages.append("\n".join(r2_lines))

    s = result["synthesis"]
    conf = result["confidence_scores"]
    conf_line = " · ".join(f"{a.replace('_', ' ').title()} {_parse_score(v)}" for a, v in conf.items())
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
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)/10", text)
    return m.group(0) if m else "?/10"


# ---------------------------------------------------------------------------
# Jarvis-style context bundle (from core/jarvis_orchestrator.py)
# ---------------------------------------------------------------------------


async def _memory_layer(query: str, user_id: str) -> str:
    if os.getenv("LEGION_JARVIS_MEMORY", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from core.legion_memory_facade import get_memory_facade

        return await get_memory_facade().contextual_snapshot(query, user_id) or ""
    except Exception as exc:
        logger.debug("jarvis memory layer: %s", exc)
        return ""


async def _screenpipe_layer(query: str) -> str:
    if os.getenv("SCREENPIPE_ENABLED", "0").strip().lower() not in ("1", "true", "yes", "on"):
        return ""
    if os.getenv("LEGION_JARVIS_SCREENPIPE", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from tools.screenpipe_tool import get_screenpipe_tool

        sp = get_screenpipe_tool()
        if not sp.is_configured():
            return ""
        return await sp.search(
            query,
            limit=int(os.getenv("LEGION_JARVIS_SCREENPIPE_LIMIT", "5")),
            hours_back=int(os.getenv("LEGION_JARVIS_SCREENPIPE_HOURS", "4")),
        )
    except Exception as exc:
        logger.debug("jarvis screenpipe: %s", exc)
        return ""


async def _whatsapp_sidecar_layer(limit: int) -> str:
    if os.getenv("LEGION_JARVIS_WHATSAPP", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from bridges.whatsapp_bridge import WhatsAppBridge

        b = WhatsAppBridge()
        if not await b._is_healthy():
            return ""
        msgs = await b.get_unread(limit=limit)
        if not msgs:
            return ""
        lines: list[str] = ["## WHATSAPP (sidecar — unread / recent)"]
        for m in msgs[:limit]:
            if not isinstance(m, dict):
                continue
            who = m.get("from") or m.get("chatId") or m.get("author") or "?"
            body = (m.get("body") or m.get("text") or m.get("message") or "")[:500]
            lines.append(f"- **{who}**: {body}")
        return "\n".join(lines)
    except Exception as exc:
        logger.debug("jarvis wa sidecar: %s", exc)
        return ""


async def _whatsapp_mcp_layer(limit: int) -> str:
    if os.getenv("LEGION_JARVIS_MCP_WHATSAPP", "0").strip().lower() not in ("1", "true", "yes", "on"):
        return ""
    try:
        from core.mcp_client import MCPClient

        raw = await MCPClient().read_whatsapp_messages(limit=limit)
        if not (raw or "").strip():
            return ""
        return f"## WHATSAPP (MCP)\n{raw.strip()[:4000]}"
    except Exception as exc:
        logger.debug("jarvis wa mcp: %s", exc)
        return ""


async def _calendar_layer() -> str:
    if os.getenv("LEGION_JARVIS_CALENDAR", "0").strip().lower() not in ("1", "true", "yes", "on"):
        return ""
    try:
        from core.mcp_client import MCPClient

        return await asyncio.wait_for(
            MCPClient().get_calendar_events(days_ahead=int(os.getenv("LEGION_JARVIS_CALENDAR_DAYS", "3"))),
            timeout=float(os.getenv("LEGION_JARVIS_CALENDAR_TIMEOUT_SEC", "2.5")),
        )
    except Exception as exc:
        logger.debug("jarvis calendar: %s", exc)
        return ""


def _emotion_hint() -> str:
    if os.getenv("LEGION_JARVIS_EMOTION", "1").strip().lower() in ("0", "false", "no", "off"):
        return ""
    try:
        from core.emotion_tracker import emotion_prompt_block

        return (emotion_prompt_block() or "").strip()
    except Exception:
        return ""


async def gather_jarvis_bundle(user_goal: str, user_id: str) -> dict[str, Any]:
    """Collect parallel context slices for one user turn.

    Returns keys: goal, memory, screenpipe, whatsapp, calendar, emotion (strings).
    """
    goal = (user_goal or "").strip()
    uid = str(user_id or "").strip()
    wa_limit = int(os.getenv("LEGION_JARVIS_WA_LIMIT", "12"))

    memory_f, sp_f, wa_sc, wa_mcp, cal_f = await asyncio.gather(
        _memory_layer(goal, uid),
        _screenpipe_layer(goal or "error terminal code"),
        _whatsapp_sidecar_layer(wa_limit),
        _whatsapp_mcp_layer(wa_limit),
        _calendar_layer(),
        return_exceptions=True,
    )

    def _safe(x: Any) -> str:
        if isinstance(x, BaseException):
            logger.debug("jarvis gather subtask: %s", x)
            return ""
        return str(x or "")

    cal_text = _safe(cal_f)
    cal_block = f"## CALENDAR\n{cal_text}" if cal_text.strip() else ""

    wa_sc_text = _safe(wa_sc)
    wa_mcp_text = _safe(wa_mcp)
    whatsapp_combined = "\n\n".join(t for t in (wa_sc_text, wa_mcp_text) if t.strip())

    return {
        "goal": goal,
        "memory": _safe(memory_f),
        "screenpipe": _safe(sp_f),
        "whatsapp": whatsapp_combined,
        "calendar": cal_block,
        "emotion": _emotion_hint(),
    }


async def compose_jarvis_response(bundle: dict[str, Any]) -> str:
    """Turn bundle into a Telegram-safe Legion message (no sends)."""
    sections: list[str] = []
    if bundle.get("emotion"):
        sections.append(bundle["emotion"])
    if bundle.get("memory"):
        sections.append(bundle["memory"])
    if bundle.get("screenpipe"):
        sections.append(bundle["screenpipe"])
    if bundle.get("whatsapp"):
        sections.append(bundle["whatsapp"])
    if bundle.get("calendar"):
        sections.append(bundle["calendar"])

    context = "\n\n".join(sections)[:14000]
    goal = bundle.get("goal") or "(no goal text)"

    from llm_client import wiki_raw_completion

    os.getenv("LEGION_JARVIS_MODEL", "opencode-go/minimax-m3")
    prompt = f"""User goal (Bashara):
{goal}

Context gathered from Legion sensors (may be partial or empty):
{context or "(no extra context retrieved)"}

Write a single Telegram message for Bashara with these sections (use clear headings):

## Situation
2–4 sentences: what you infer from context + goal.

## Suggested actions
Numbered list: concrete next steps (e.g. fix error path, research library, check Supabase, draft guest reply). Mention tools: /research, /do, /screen, wiki, MCP when relevant.

## Draft reply (only if a guest/customer WhatsApp-style message appears in context)
Write a polite draft in Indonesian-English mix as appropriate. If no guest message, write: (none — no guest thread in context)

## Safety
State explicitly: **No messages were sent.** WhatsApp/email sends require Bashara's separate confirmation or existing /wa flows.

Keep total under ~3500 characters. No markdown code blocks."""

    body = await wiki_raw_completion(prompt, system_prompt="You are a concise summarizer. Keep under 3500 chars. No markdown code blocks.", temperature=0.35)
    if not (body or "").strip():
        return (
            "Jarvis bundle was gathered but the synthesis model returned empty. "
            f"Raw context length: {len(context)} chars. Check MINIMAX_API_KEY / LEGION_JARVIS_MODEL."
        )
    return body.strip()


# ---------------------------------------------------------------------------
# Nexus routing — 3-layer routing (merged from core/nexus_orchestrator.py)
# ---------------------------------------------------------------------------


class NexusOrchestrator:
    """3-layer intelligent routing.

    Layer 1: Keyword matching (routing_keywords.yaml, fast, O(1))
    Layer 2: Semantic embeddings (sentence-transformers, local)
    Layer 3: LLM fallback (local Gemma3:12b, last resort)
    """

    KEYWORD_THRESHOLD = 2
    SEMANTIC_THRESHOLD = 0.55

    def __init__(self) -> None:
        kw_path = Path("config/routing_keywords.yaml")
        if kw_path.exists():
            with kw_path.open() as f:
                self._keyword_map: dict[str, list[str]] = yaml.safe_load(f) or {}
        else:
            logger.warning("routing_keywords.yaml not found — Layer 1 disabled")
            self._keyword_map = {}

    async def route(self, task: str) -> RoutingDecision:
        """Cascade through 3 routing layers and return the best agent."""
        decision = await self._layer1_keyword(task)
        if decision:
            return decision

        decision = await self._layer2_semantic(task)
        if decision:
            return decision

        return await self._layer3_llm(task)

    async def route_to_dept(self, dept: str, task: str) -> RoutingDecision:
        """Skip all routing layers; use the department's default agent."""
        from core.agent_registry import agents_by_department, get_department_default

        agent = get_department_default(dept)
        if not agent:
            agents = agents_by_department(dept)
            agent = agents[0] if agents else self._fallback_agent()

        return RoutingDecision(
            agent=agent,
            confidence=1.0,
            method="department_override",
            reasoning=f"Manual department selection: {dept}",
        )

    async def execute_task(
        self,
        decision: RoutingDecision,
        task: str,
        stream: bool = True,
    ) -> str:
        """Execute task with the selected agent, using full fallback chain."""

        system_prompt = self._build_system_prompt(decision.agent, task)

        model_ids = [decision.agent.primary_model_id, *decision.agent.fallback_model_ids]

        last_error: Exception | None = None
        for model_id in model_ids:
            if not model_id:
                continue
            try:
                result = await self._call_model(model_id, system_prompt, task)
                return result
            except Exception as exc:
                logger.warning("Model %s failed: %s — trying next fallback", model_id, exc)
                last_error = exc

        error_msg = str(last_error) if last_error else "All models failed"
        return f"❌ Error executing task: {error_msg}"

    async def run_swarm(self, task: str, pattern: str = "auto") -> str:
        """Run multi-agent swarm via LegionOrchestrator."""
        try:
            from core.orchestration.supervisor import orchestrate  # type: ignore

            result = await orchestrate(task=task)  # type: ignore[reportCallIssue]
            return result
        except ImportError:
            return await self._simple_swarm(task)
        except Exception as exc:
            logger.error("Swarm execution failed: %s", exc)
            return f"❌ Swarm error: {exc}"

    async def _layer1_keyword(self, task: str) -> RoutingDecision | None:
        """Keyword matching using routing_keywords.yaml."""
        if not self._keyword_map:
            return None

        task_lower = task.lower()
        found_keywords = [kw for kw in self._keyword_map if kw in task_lower]

        if not found_keywords:
            return None

        from core.agent_registry import get_agent, search_by_capability

        results = search_by_capability(found_keywords)
        if not results:
            return None

        agent_name, score = results[0]
        if score < self.KEYWORD_THRESHOLD:
            return None

        agent = get_agent(agent_name)
        if not agent:
            return None

        confidence = min(score / 8.0, 1.0)
        return RoutingDecision(
            agent=agent,
            confidence=confidence,
            method="keyword",
            reasoning=f"Matched keywords: {', '.join(found_keywords[:5])}",
        )

    async def _layer2_semantic(self, task: str) -> RoutingDecision | None:
        """Sentence-transformer semantic similarity search."""
        from core.agent_registry import get_agent, semantic_search

        results = semantic_search(task, top_k=3)
        if not results:
            return None

        agent_name, similarity = results[0]
        if similarity < self.SEMANTIC_THRESHOLD:
            return None

        agent = get_agent(agent_name)
        if not agent:
            return None

        return RoutingDecision(
            agent=agent,
            confidence=similarity,
            method="semantic",
            reasoning=f"Semantic similarity: {similarity:.3f}",
        )

    async def _layer3_llm(self, task: str) -> RoutingDecision:
        """Ask local Gemma3:12b which department should handle the task."""
        from core.agent_registry import (
            AGENT_REGISTRY,
            get_department_default,
            list_all_departments,
        )

        dept_list = "\n".join(f"- {d}" for d in list_all_departments())
        prompt = (
            "You are a task router. Given a user task, choose ONE department.\n\n"
            f"Departments:\n{dept_list}\n\n"
            f'Task: "{task}"\n\n'
            "Respond with ONLY the department name (snake_case, no other text)."
        )

        dept_name = "engineering"
        try:
            raw = await self._call_model("ollama_chat/qwen3.5:35b", "", prompt, max_tokens=15)
            candidate = raw.strip().lower().replace(" ", "_").replace("-", "_")
            if candidate in AGENT_REGISTRY or candidate in list_all_departments():
                dept_name = candidate
        except Exception as exc:
            logger.warning("Layer 3 LLM routing failed: %s", exc)

        agent = get_department_default(dept_name) or self._fallback_agent()
        return RoutingDecision(
            agent=agent,
            confidence=0.65,
            method="llm_fallback",
            reasoning=f"LLM routed to department: {dept_name}",
        )

    def _build_system_prompt(self, agent: Any, task: str) -> str:
        """Load Jinja2 template or return a default system prompt."""

        tmpl_path = Path(agent.prompt_template)
        try:
            if tmpl_path.exists():
                from jinja2 import Environment, FileSystemLoader  # type: ignore

                env = Environment(
                    loader=FileSystemLoader(str(tmpl_path.parent)),
                    autoescape=True,
                )
                tmpl = env.get_template(tmpl_path.name)
                return tmpl.render(
                    role=agent.name.replace("_", " ").title(),
                    department=agent.department.replace("_", " ").title(),
                    role_description=agent.description,
                    capabilities=agent.capabilities,
                    tools=agent.tools,
                    task=task,
                    context="",
                )
        except Exception as exc:
            logger.debug("Template load failed (%s): %s", tmpl_path, exc)

        return (
            f"You are {agent.name.replace('_', ' ')} in the "
            f"{agent.department.replace('_', ' ')} department. "
            f"{agent.description} "
            "Think step-by-step. Be precise and practical."
        )

    async def _call_model(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4000,
    ) -> str:
        """Call any LiteLLM-compatible model asynchronously."""
        from llm_client import call_llm

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            content = await call_llm(
                messages=messages,
                model=model_id,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return content.strip()  # type: ignore[reportAttributeAccessIssue]

        except Exception as exc:
            raise RuntimeError(f"LiteLLM call failed for {model_id}: {exc}") from exc

    async def _simple_swarm(self, task: str) -> str:
        """Minimal parallel swarm: 3 best keyword-matched agents collaborate."""
        from core.agent_registry import get_agent, search_by_capability

        results_raw = search_by_capability(task.lower().split()[:5])
        top_agents = [get_agent(name) for name, _ in results_raw[:3] if get_agent(name) is not None]
        if not top_agents:
            top_agents = [self._fallback_agent()]

        async def _run(agent: Any) -> str:
            system_prompt = self._build_system_prompt(agent, task)
            try:
                return await self._call_model(agent.primary_model_id, system_prompt, task)
            except Exception as exc:
                return f"[{agent.name} error: {exc}]"

        responses = await asyncio.gather(*[_run(a) for a in top_agents])
        parts = [f"**{a.name}** ({a.department}):\n{r}" for a, r in zip(top_agents, responses, strict=False)]  # type: ignore[reportOptionalMemberAccess]
        return "\n\n---\n\n".join(parts)

    def _fallback_agent(self) -> Any:
        """Absolute last-resort agent (first engineering agent)."""
        from core.agent_registry import AGENT_REGISTRY, agents_by_department

        eng = agents_by_department("engineering")
        if eng:
            return eng[0]
        return next(iter(AGENT_REGISTRY.values()))


# ---------------------------------------------------------------------------
# LegionSwarmOrchestrator — 3-phase swarm with dynamic team selection
# (replaces hardcoded LEGION_TEAM with AgentRegistry.select_team())  # type: ignore[reportAttributeAccessIssue]
# ---------------------------------------------------------------------------


class LegionSwarmOrchestrator:
    """3-phase parallel swarm with dynamic team selection.

    Phase 1: Team proposes in parallel (via AgentRegistry.select_team())  # type: ignore[reportAttributeAccessIssue]
    Phase 2: Cross-examination debate rounds
    Phase 3: Synthesis by architect agent
    """

    def __init__(
        self,
        llm_call: Callable[[str, str, str], Coroutine[Any, Any, str]],
        progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
        debate_rounds: int = 2,
        max_parallel: int = 5,
    ):
        self.llm_call = llm_call
        self.progress_fn = progress_fn
        self.debate_rounds = debate_rounds
        self.max_parallel = max_parallel

    async def _progress(self, msg: str) -> None:
        if self.progress_fn:
            await self.progress_fn(msg)
        logger.info("[LegionSwarm] %s", msg)

    def _get_model_for_agent(self, agent_def: Any) -> str:
        if hasattr(agent_def, "primary_model_id") and agent_def.primary_model_id:
            return agent_def.primary_model_id
        if hasattr(agent_def, "primary_model") and agent_def.primary_model:
            from core.agent_registry import MODEL_LOOKUP
            return MODEL_LOOKUP.get(agent_def.primary_model, agent_def.primary_model)
        from core.agent_registry import MODEL_LOOKUP
        return MODEL_LOOKUP.get("minimax-m3", "opencode-go/minimax-m3")

    def _build_system_prompt(self, agent_def: Any) -> str:
        from core.agent_registry import PERSONA_WRAPPER

        persona = (
            f"You are {agent_def.name.replace('_', ' ')} in the "
            f"{agent_def.department.replace('_', ' ')} department. "
            f"{agent_def.description}. "
            f"Your capabilities: {', '.join(agent_def.capabilities)}. "
            "Think step-by-step. Be precise and practical."
        )
        return f"{PERSONA_WRAPPER.strip()}\n\n{persona}"

    async def _call_agent(
        self,
        agent_def: Any,
        task: str,
        context: str = "",
    ) -> AgentResult:
        started = time.perf_counter()
        system = self._build_system_prompt(agent_def)
        user_msg = f"Task: {task}"
        if context:
            user_msg += f"\n\nAdditional context:\n{context}"
        model = self._get_model_for_agent(agent_def)
        try:
            output = await self.llm_call(model, system, user_msg)
            return AgentResult(
                key=agent_def.name,
                name=agent_def.name,
                output=output,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                success=True,
            )
        except Exception as exc:
            logger.warning("Agent %s failed: %s", agent_def.name, exc)
            return AgentResult(
                key=agent_def.name,
                name=agent_def.name,
                output="",
                latency_ms=(time.perf_counter() - started) * 1000.0,
                success=False,
                error=str(exc),
            )

    async def run(self, task: str) -> SwarmReport:
        """Run 3-phase swarm using dynamically selected team."""
        started = time.perf_counter()
        semaphore = asyncio.Semaphore(self.max_parallel)

        # Get dynamic team from agent_registry
        from core.agent_registry import select_team as _select_team

        team_defs = await _select_team(task_description=task, max_agents=self.max_parallel)

        if not team_defs:
            # Fallback to general agent
            from core.agent_registry import get_agent

            fallback = get_agent("general")
            team_defs = [fallback] if fallback else []

        async def _run_with_sem(agent_def: Any, ctx: str = "") -> AgentResult:
            async with semaphore:
                return await self._call_agent(agent_def, task, ctx)

        phase1_outputs: dict[str, str] = {}

        # ── PHASE 1: Parallel Proposal ──────────────────────────────────────────
        await self._progress(f"🧠 Phase 1/3 — {len(team_defs)} agents proposing in parallel...")

        phase1_tasks = [_run_with_sem(agent_def) for agent_def in team_defs]
        phase1_results = await asyncio.gather(*phase1_tasks, return_exceptions=True)

        for agent_def, result in zip(team_defs, phase1_results, strict=False):
            if isinstance(result, Exception):
                phase1_outputs[agent_def.name] = f"[Error: {result}]"  # type: ignore[reportAttributeAccessIssue]
            else:
                phase1_outputs[agent_def.name] = result.output if isinstance(result, AgentResult) else str(result)  # type: ignore[reportAttributeAccessIssue]

        # ── PHASE 2: Debate Rounds ─────────────────────────────────────────────
        await self._progress(f"🔥 Phase 2/3 — {self.debate_rounds} debate round(s)...")

        phase2_outputs: dict[str, str] = {}
        current_proposals = dict(phase1_outputs)

        for round_num in range(self.debate_rounds):
            await self._progress(f"  Debate round {round_num + 1}/{self.debate_rounds}...")

            debate_contexts = []
            for agent_def in team_defs:
                others_text = "\n\n".join(
                    f"[{key}]: {prop}" for key, prop in current_proposals.items() if key != agent_def.name  # type: ignore[reportAttributeAccessIssue]
                )
                debate_contexts.append(
                    f"You are {agent_def.name}.\n"
                    f"Task: {task}\n\n"
                    f"Your initial proposal:\n{current_proposals[agent_def.name]}\n\n"  # type: ignore[reportAttributeAccessIssue]
                    f"Other agents' proposals:\n{others_text}\n\n"
                    "Critique the strongest weaknesses in other proposals and refine your own. "
                    "Keep what's strong, fix what's weak. Respond with your refined position."
                )

            round_tasks = [_run_with_sem(agent_def, ctx) for agent_def, ctx in zip(team_defs, debate_contexts, strict=False)]
            round_results = await asyncio.gather(*round_tasks, return_exceptions=True)

            for agent_def, result in zip(team_defs, round_results, strict=False):
                if isinstance(result, Exception):
                    current_proposals[agent_def.name] = current_proposals.get(agent_def.name, "")  # type: ignore[reportAttributeAccessIssue]
                else:
                    current_proposals[agent_def.name] = result.output if isinstance(result, AgentResult) else str(result)  # type: ignore[reportAttributeAccessIssue]

        phase2_outputs = dict(current_proposals)

        # ── PHASE 3: Synthesis ─────────────────────────────────────────────────
        await self._progress("🏆 Phase 3/3 — Synthesizing final recommendation...")

        all_proposals_text = "\n\n".join(
            f"=== {team_defs[i].name} ({team_defs[i].name}) ===\n{output}"
            for i, output in enumerate(phase1_outputs.values())
        )
        refined_text = "\n\n".join(
            f"=== {team_defs[i].name} ({team_defs[i].name}) ===\n{output}"
            for i, output in enumerate(phase2_outputs.values())
        )

        synth_system = (
            "You are the Chief Architect. You have witnessed a multi-agent debate where "
            "specialized agents proposed and refined their solutions.\n\n"
            "Your job: Synthesize all proposals into ONE coherent, actionable recommendation.\n"
            "Format your response as:\n"
            "## Summary\n[2-3 sentence overview]\n\n"
            "## Key Decisions\n[bullet points of major decisions with reasoning]\n\n"
            "## Implementation Plan\n[numbered steps]\n\n"
            "## Risks & Mitigations\n[potential issues and how to address them]"
        )

        synth_msg = (
            f"Original task: {task}\n\n"
            f"=== INITIAL PROPOSALS ===\n{all_proposals_text}\n\n"
            f"=== POST-DEBATE REFINEMENTS ===\n{refined_text}\n\n"
            "Synthesize the strongest elements from all proposals into one optimal solution."
        )

        try:
            final_synthesis = await self.llm_call(
                "opencode-go/minimax-m3",
                synth_system,
                synth_msg,
            )
        except Exception as exc:
            logger.warning("Synthesis failed: %s", exc)
            final_synthesis = (
                f"[Synthesis failed: {exc}]\n\nBest initial proposal:\n{max(phase2_outputs.values(), key=len)}"
            )

        agent_results: list[AgentResult] = []
        for agent_def in team_defs:
            result = AgentResult(
                key=agent_def.name,  # type: ignore[reportAttributeAccessIssue]
                name=agent_def.name,
                output=phase2_outputs.get(agent_def.name, ""),  # type: ignore[reportAttributeAccessIssue]
                latency_ms=0.0,
                success=True,
            )
            agent_results.append(result)

        # Wire self-evolution: record this swarm session
        try:
            from core.swarm_utils import record_swarm_session
            agent_names = [a.name for a in team_defs]
            await record_swarm_session(
                task=task,
                agents=agent_names,
                outcome=f"Synthesized: {final_synthesis[:100]}...",
                success=bool(final_synthesis),
            )
        except Exception as exc:
            logger.debug("Swarm session recording failed (non-fatal): %s", exc)

        return SwarmReport(
            phase1_outputs=phase1_outputs,
            phase2_outputs=phase2_outputs,
            final_synthesis=final_synthesis,
            agent_results=agent_results,
            total_latency_ms=(time.perf_counter() - started) * 1000.0,
            topology_used="legion-swarm",
        )


# ---------------------------------------------------------------------------
# Compatibility shim for LegionAgentDef (original hardcoded team definition)
# ---------------------------------------------------------------------------


@dataclass
class LegionAgentDef:
    """Compatibility shim for legacy LegionSwarmOrchestrator agent definitions."""

    key: str
    name: str
    persona: str
    role_description: str


# ---------------------------------------------------------------------------
# Main entry point — LegionOrchestrator
# ---------------------------------------------------------------------------


class LegionOrchestrator:
    """Single canonical entry point for Legion orchestration.

    Uses AgentRegistry.select_team() for dynamic team selection.  # type: ignore[reportAttributeAccessIssue]
    Falls back to NexusRouting for single-agent tasks.
    """

    def __init__(self) -> None:
        self.nexus = NexusOrchestrator()

    async def run(self, task: str, user_id: int) -> str:
        """Route and execute task.

        Phase 1: Route and select team from REAL registry
        Phase 2: If single agent → run directly; if team → run debate swarm
        """
        # Gather Jarvis context bundle first (for enrichment)
        bundle = await gather_jarvis_bundle(task, user_id)  # type: ignore[reportArgumentType]

        # Check if task is complex enough for multi-agent
        from core.agent_registry import select_team as _select_team

        team = await _select_team(
            task_description=task,
            max_agents=5,
        )

        if len(team) <= 1:
            return await self._run_single(team[0] if team else None, task, user_id, bundle)
        else:
            return await self._run_debate(team, task, user_id, bundle)

    async def _run_single(
        self,
        agent: Any,
        task: str,
        user_id: int,
        bundle: dict[str, Any],
    ) -> str:
        """Run single agent with context bundle."""
        from llm_client import chat

        if agent is None:
            return "No agent selected for this task."

        # Enrich task with Jarvis context
        context_parts = []
        if bundle.get("memory"):
            context_parts.append(f"## MEMORY\n{bundle['memory']}")
        if bundle.get("screenpipe"):
            context_parts.append(f"## SCREENPIPE\n{bundle['screenpipe']}")
        if bundle.get("whatsapp"):
            context_parts.append(f"## WHATSAPP\n{bundle['whatsapp']}")
        if bundle.get("calendar"):
            context_parts.append(bundle["calendar"])

        context_block = "\n\n".join(context_parts)
        enriched_task = f"{task}\n\n[Context]\n{context_block}" if context_block else task

        try:
            result, _ = await chat(
                enriched_task,
                agent_key=agent.name,
                task_context=self._build_agent_system_prompt(agent),
            )
            return result
        except Exception as exc:
            logger.error("Single agent run failed: %s", exc)
            try:
                from core.self_evolution import get_self_evolution_engine
                engine = get_self_evolution_engine()
                await engine.record_failure(
                    task=task[:100],
                    approach=f"LegionOrchestrator._run_single(agent={agent.name})",
                    failure_mode=f"{type(exc).__name__}: {exc}",
                    root_cause="Exception in single-agent orchestration",
                    fix_applied="Error returned to caller",
                    prevention_rule="Validate agent and task before calling _run_single; wrap chat() call",
                )
            except Exception:
                pass
            return f"Error: {exc}"

    async def _run_debate(
        self,
        team: list[Any],
        task: str,
        user_id: int,
        bundle: dict[str, Any],
    ) -> str:
        """Run multi-agent debate swarm."""
        from llm_client import chat

        async def llm_call(model: str, system: str, user: str) -> str:
            result, _ = await chat(user, agent_key="general", task_context=system)
            return result

        swarm = LegionSwarmOrchestrator(llm_call=llm_call)
        report = await swarm.run(task)

        # Format with bundle context
        context_note = ""
        if bundle.get("memory") or bundle.get("screenpipe"):
            context_note = f"\n\n*Context enrichment: {len(str(bundle))} chars gathered*"

        return f"{report.final_synthesis}{context_note}"

    def _build_agent_system_prompt(self, agent: Any) -> str:
        """Build system prompt for an agent."""
        return (
            f"You are {agent.name.replace('_', ' ')} in the "
            f"{agent.department.replace('_', ' ')} department. "
            f"{agent.description} "
            "Think step-by-step. Be precise and practical."
        )


# ---------------------------------------------------------------------------
# Convenience function (replaces run_legion_swarm from legion_swarm.py)
# ---------------------------------------------------------------------------


async def run_legion_swarm(
    task: str,
    progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
) -> SwarmReport:
    """Convenience function to run the Legion swarm."""

    async def llm_call(model: str, system: str, user: str) -> str:
        from llm_client import chat

        result, _ = await chat(user, agent_key="general", system_prompt=system)  # type: ignore[reportCallIssue]
        return result

    orchestrator = LegionSwarmOrchestrator(llm_call=llm_call, progress_fn=progress_fn)
    return await orchestrator.run(task)


# ---------------------------------------------------------------------------
# Global singleton (mirrors nexus from nexus_orchestrator.py)
# ---------------------------------------------------------------------------

nexus = NexusOrchestrator()


# ---------------------------------------------------------------------------
# HarnessFS CLI tool
# ---------------------------------------------------------------------------


def harness_fs_cli(base_dir: str = "/tmp/meta_harness") -> None:
    """
    CLI tool for querying HarnessFS.

    Usage:
        from core.orchestrator import harness_fs_cli
        harness_fs_cli("/path/to/harness/fs")

    Provides:
        - List Pareto frontier candidates
        - Show top-k candidates by reward
        - Diff two candidates
        - Show candidate details (code, traces, scores)
    """
    from core.meta_harness import HarnessFS

    fs = HarnessFS(base_dir=base_dir)

    print(f"\n=== HarnessFS at {base_dir} ===")
    stats = fs.get_stats()
    print(f"Total candidates: {stats['total_candidates']}")
    print(f"Pareto frontier size: {stats['pareto_frontier_size']}")
    print(f"Domains: {', '.join(stats.get('domains', []))}")

    # Show Pareto frontier
    frontier = fs.get_pareto_frontier()
    if frontier.candidates:
        print(f"\n=== Pareto Frontier ({len(frontier.candidates)} candidates) ===")
        for i, c in enumerate(frontier.candidates):
            print(f"{i+1}. {c.candidate_id}")
            print(f"   Domain: {c.domain.value}")
            print(f"   Reward: {c.mean_reward:.4f}, Cost: {c.mean_cost:.4f}")
            print(f"   Description: {c.description[:80]}...")

    # Show recent candidates
    recent = fs.query_recent(n=10)
    if recent:
        print(f"\n=== Recent Candidates ({len(recent)} shown) ===")
        for c in recent:
            print(f"- {c.candidate_id}: reward={c.mean_reward:.4f}, {c.description[:60]}")

    print("\n=== Available Commands ===")
    print("  fs.get(candidate_id)     - Get full candidate details")
    print("  fs.query_by_keyword(k)   - Search by keyword")
    print("  fs.query_by_reward_range(min, max) - Filter by reward")
    print("  fs.get_pareto_frontier() - Get non-dominated candidates")


def diff_candidates(
    candidate_id_1: str,
    candidate_id_2: str,
    base_dir: str = "/tmp/meta_harness",
) -> str:
    """
    Diff two harness candidates and return a summary.

    Usage:
        diff = diff_candidates("harness_abc123", "harness_def456")
        print(diff)
    """
    from core.meta_harness import HarnessFS

    fs = HarnessFS(base_dir=base_dir)

    c1 = fs.get(candidate_id_1)
    c2 = fs.get(candidate_id_2)

    if not c1 or not c2:
        return "Error: One or both candidates not found"

    lines = [
        f"=== Diff: {candidate_id_1} vs {candidate_id_2} ===",
        "",
        f"Metric          | {candidate_id_1:20} | {candidate_id_2:20}",
        "-" * 60,
        f"Reward          | {c1.mean_reward:20.4f} | {c2.mean_reward:20.4f}",
        f"Cost            | {c1.mean_cost:20.4f} | {c2.mean_cost:20.4f}",
        f"Domain          | {c1.domain.value:20} | {c2.domain.value:20}",
        f"Evaluations     | {len(c1.evaluations):20} | {len(c2.evaluations):20}",
    ]

    # Show code length comparison
    lines.append(f"Code length    | {len(c1.source_code):20} | {len(c2.source_code):20}")

    # Find line-by-line differences
    import difflib

    l1 = c1.source_code.splitlines()
    l2 = c2.source_code.splitlines()
    diff = list(difflib.unified_diff(l1, l2, fromfile=candidate_id_1, tofile=candidate_id_2, lineterm=""))

    if diff:
        lines.append(f"\n=== Code Differences ({len(diff)} lines) ===")
        lines.extend(diff[:50])  # Show first 50 diff lines
        if len(diff) > 50:
            lines.append(f"  ... ({len(diff) - 50} more lines)")
    else:
        lines.append("\n(No code differences)")

    return "\n".join(lines)


async def run_meta_harness(
    task: str,
    pattern: str = "sequential",
    recursion_depth: int = 3,
    use_harness: bool = True,
    harness_domain: str = "agentic_coding",
    progress_fn: Callable[[str], Coroutine[Any, Any, None]] | None = None,
) -> dict:
    """
    Run integrated Meta-Harness + RecursiveMAS pipeline.

    This combines Meta-Harness (harness optimization) with RecursiveMAS
    (multi-agent collaboration) in a unified workflow.

    Usage:
        result = await run_meta_recursive(
            task="Solve this coding task...",
            pattern="sequential",
            recursion_depth=3,
            use_harness=True,
            harness_domain="agentic_coding",
        )
        print(result["output"])
        print(f"Harness used: {result.get('harness_id', 'none')}")

    Args:
        task: The task/question to solve
        pattern: RecursiveMAS collaboration pattern
        recursion_depth: Number of recursion rounds
        use_harness: Whether to use harness optimization
        harness_domain: Domain for harness optimization
        progress_fn: Optional callback for progress updates

    Returns:
        Dict with output, metrics, and harness info
    """
    from core.meta_harness import HarnessFS
    from core.recursive_mas import CollaborationPattern, RecursiveMASOrchestrator

    async def llm_call(model: str, system: str, user: str) -> str:
        from llm_client import chat

        result, _ = await chat(user, agent_key="general", task_context=system)
        return result

    async def progress(msg: str) -> None:
        if progress_fn:
            await progress_fn(msg)
        logger.info("[Meta-Recursive] %s", msg)

    # Map pattern string to enum
    pattern_map = {
        "sequential": CollaborationPattern.SEQUENTIAL,
        "mixture": CollaborationPattern.MIXTURE,
        "distillation": CollaborationPattern.DISTILLATION,
        "deliberation": CollaborationPattern.DELIBERATION,
    }
    collab_pattern = pattern_map.get(pattern.lower(), CollaborationPattern.SEQUENTIAL)

    # If harness requested, get best harness from FS
    harness_used = None
    if use_harness:
        await progress("Loading optimized harness from Meta-Harness...")
        fs = HarnessFS()
        frontier = fs.get_pareto_frontier()
        if frontier.candidates:
            best = frontier.candidates[0]
            harness_used = best.candidate_id
            await progress(f"Using harness: {best.candidate_id} (reward={best.mean_reward:.4f})")

    # Run RecursiveMAS
    await progress(f"Running RecursiveMAS ({pattern}, depth={recursion_depth})...")
    orchestrator = RecursiveMASOrchestrator(
        llm_call=llm_call,
        collaboration_pattern=collab_pattern,
        recursion_depth=recursion_depth,
        progress_fn=progress_fn,
    )
    result = await orchestrator.run(task)

    return {
        "output": result.output,
        "success": result.success,
        "pattern": pattern,
        "recursion_depth": recursion_depth,
        "harness_id": harness_used,
        "num_agents": len(orchestrator.agents),
        "latency_ms": result.total_latency_ms,
        "agent_results": result.agent_results,
    }
