"""swarm_wire.py — drop-in wiring layer for /swarm command.

This module bridges main.py's /swarm handler to the fully-implemented
SwarmDebateOrchestrator in task_orchestrator.py.

Usage in main.py cmd_swarm():
    from tools.swarm_wire import run_swarm_debate
    messages = await run_swarm_debate(task, progress_fn)
    for m in messages:
        await msg.answer(m, parse_mode="HTML")
"""

from __future__ import annotations

import asyncio
import html
import logging
import re
from typing import Callable, Coroutine, Any, Optional

from task_orchestrator import SwarmDebateOrchestrator, format_debate_for_telegram

logger = logging.getLogger(__name__)


# ── LLM bridge (single-turn chat, no tools) ──────────────────────────────────

async def _llm_call(model: str, system: str, user: str) -> str:
    """Minimal single-turn LLM call used by the debate orchestrator.

    Uses litellm directly so it works with all providers already configured
    in llm_client.py without importing the full agentic loop.
    """
    import os
    import litellm

    provider = model.split("/")[0].lower()
    key_map = {
        "cerebras":   "CEREBRAS_API_KEY",
        "groq":       "GROQ_API_KEY",
        "gemini":     "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "zai":        "ZAI_API_KEY",
    }
    env_var = key_map.get(provider)
    api_key = os.getenv(env_var) if env_var else None

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens": 800,
        "temperature": 0.85,
    }
    if api_key:
        kwargs["api_key"] = api_key
    if provider == "openrouter":
        kwargs["extra_headers"] = {
            "HTTP-Referer": "https://github.com/Bashara-aina/Babas_Swarms_bot",
            "X-Title": "LegionSwarm",
        }

    # Try primary model, fall back to groq general
    try:
        resp = await litellm.acompletion(**kwargs)
        return resp.choices[0].message.content or ""
    except Exception as e:
        logger.warning("Primary model %s failed (%s), falling back to groq", model, e)
        kwargs["model"] = "groq/llama-3.3-70b-versatile"
        kwargs["api_key"] = os.getenv("GROQ_API_KEY", "")
        kwargs.pop("extra_headers", None)
        try:
            resp = await litellm.acompletion(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e2:
            return f"[model error: {e2}]"


# ── Department parallel layer ─────────────────────────────────────────────────
# Each department runs its specialist agents in parallel BEFORE the debate.
# Department leads synthesize their team's findings into one position,
# which then enters the 4-round debate as a unified voice.

DEPARTMENTS: dict[str, dict] = {
    "engineering": {
        "icon": "⚙️",
        "lead": "Lead Engineer",
        "agents": [
            ("Senior Backend Dev",   "You specialise in APIs, databases, and system reliability. You think in terms of latency, failure modes, and schema design."),
            ("Senior Frontend Dev",  "You specialise in UI architecture, component design, and user-facing performance. You care deeply about UX consistency."),
            ("DevOps / SRE",         "You think in pipelines, uptime, and blast radius. You ask: what breaks first and who gets paged at 3am?"),
            ("Security Engineer",    "You find vulnerabilities. Every design decision is a potential attack surface to you."),
            ("ML Engineer",          "You specialise in model training pipelines, GPU utilisation, and bridging research code to production."),
            ("Data Engineer",        "You design data pipelines, lake architectures, and the systems that feed ML models."),
            ("Mobile Dev",           "You think in cross-platform constraints, offline-first design, and app store dynamics."),
            ("Platform / Infra",     "You think in Kubernetes, cloud costs, and developer experience at scale."),
        ],
        "synthesis_instruction": "Synthesize your team's technical findings into ONE clear engineering recommendation. Flag the top risk and the fastest path to working code.",
    },
    "research": {
        "icon": "🔬",
        "lead": "Research Director",
        "agents": [
            ("Literature Analyst",   "You surface what is known in academic and industry literature. You cite precedent and distinguish proven from speculative."),
            ("Domain Expert",        "You provide deep subject-matter knowledge. You correct misconceptions and add nuance."),
            ("Data Scientist",       "You look for quantitative evidence. If there is no data, you say so clearly."),
            ("Fact Checker",         "You verify claims. You flag speculation presented as fact. You demand primary sources."),
            ("Trend Analyst",        "You identify where the field is moving over the next 2-3 years based on current signals."),
            ("Contrarian Scholar",   "You find the papers that disagree. You surface the evidence against the mainstream view."),
            ("Synthesizer",          "You integrate findings across sources into a coherent picture, noting where evidence conflicts."),
            ("Methodology Critic",   "You evaluate research quality: sample size, bias, reproducibility, confounds."),
        ],
        "synthesis_instruction": "Synthesize your team's research into a crisp evidence summary. Separate what is well-established from what is contested. Note the highest-confidence finding and the biggest open question.",
    },
    "product": {
        "icon": "📦",
        "lead": "Head of Product",
        "agents": [
            ("Product Manager",      "You think in user problems, prioritisation, and roadmap trade-offs. You ask: is this the right thing to build?"),
            ("UX Researcher",        "You represent the user. You ask who actually has this problem and whether they would pay for the solution."),
            ("Growth PM",            "You think in acquisition, activation, retention, and referral loops."),
            ("B2B PM",               "You think in enterprise sales cycles, procurement, and multi-stakeholder decisions."),
            ("B2C PM",               "You think in consumer psychology, virality, and daily habit formation."),
            ("Platform PM",          "You think in APIs, ecosystems, and developer adoption."),
            ("Monetisation PM",      "You think in pricing models, conversion funnels, and unit economics."),
            ("Roadmap Strategist",   "You balance now/next/later and push back on scope creep with evidence."),
        ],
        "synthesis_instruction": "Synthesize your team's product thinking into ONE recommendation: what to build first, for whom, and why. Include the key metric that would prove success.",
    },
    "marketing": {
        "icon": "📣",
        "lead": "CMO",
        "agents": [
            ("Brand Strategist",     "You think in positioning, perception, and differentiation. You ask: what do we want people to feel?"),
            ("Growth Hacker",        "You think in channels, CAC, and virality coefficients."),
            ("Content Strategist",   "You think in narratives, distribution, and audience building."),
            ("SEO/SEM Specialist",   "You think in search intent, keyword clusters, and conversion paths."),
            ("Social Media Lead",    "You think in platform algorithms, content formats, and community engagement."),
            ("PR Strategist",        "You think in earned media, narrative control, and crisis communication."),
            ("Email Marketer",       "You think in segmentation, lifecycle automation, and deliverability."),
            ("Performance Marketer", "You think in ROAS, attribution, and bid strategy."),
        ],
        "synthesis_instruction": "Synthesize your team's marketing perspective into ONE go-to-market recommendation: channel, message, and expected outcome.",
    },
    "design": {
        "icon": "🎨",
        "lead": "Design Lead",
        "agents": [
            ("UX Designer",          "You think in user flows, friction reduction, and cognitive load."),
            ("UI Designer",          "You think in visual hierarchy, typography, and accessibility."),
            ("Interaction Designer", "You think in micro-interactions, feedback loops, and delight."),
            ("Design Systems Lead",  "You think in consistency, scalability, and component reuse."),
            ("Motion Designer",      "You think in transitions, animation timing, and perceived performance."),
            ("User Researcher",      "You validate designs with real users. You are deeply skeptical of untested assumptions."),
            ("Accessibility Expert", "You ensure designs work for all users, including those with disabilities."),
            ("Brand Designer",       "You ensure every touchpoint reinforces the brand identity."),
        ],
        "synthesis_instruction": "Synthesize your team's design perspective into ONE concrete recommendation: the single most impactful design change with clear rationale.",
    },
    "operations": {
        "icon": "🏭",
        "lead": "COO",
        "agents": [
            ("Process Analyst",      "You map workflows and find bottlenecks. You ask: where does work get stuck?"),
            ("Supply Chain Expert",  "You think in lead times, inventory, and supplier risk."),
            ("Finance Analyst",      "You think in unit economics, cash flow, and ROI timelines."),
            ("HR Strategist",        "You think in org design, hiring timelines, and cultural fit."),
            ("Legal Counsel",        "You flag regulatory risk, IP issues, and contractual exposure."),
            ("Risk Manager",         "You enumerate what could go wrong, likelihood, and mitigation cost."),
            ("Customer Success",     "You think in onboarding, retention, and turning customers into advocates."),
            ("Support Lead",         "You think in ticket volume, escalation paths, and knowledge base quality."),
        ],
        "synthesis_instruction": "Synthesize your team's operational view into ONE recommendation: the single operational change with the highest leverage on efficiency or risk reduction.",
    },
    "creative": {
        "icon": "✨",
        "lead": "Creative Director",
        "agents": [
            ("Copywriter",           "You write with clarity, punch, and voice. You find the one sentence that lands."),
            ("Storyteller",          "You find the narrative arc. You ask: what is the hero's journey here?"),
            ("Creative Strategist",  "You bridge creative instinct with business objectives."),
            ("Art Director",         "You think in visual metaphors, colour theory, and compositional balance."),
            ("Video Producer",       "You think in narrative pacing, B-roll, and emotional arc."),
            ("Meme / Viral Expert",  "You understand cultural context, timing, and why things spread."),
            ("Editor",               "You cut ruthlessly. Every word must earn its place."),
            ("Tone of Voice Expert", "You ensure the brand sounds like itself consistently across contexts."),
        ],
        "synthesis_instruction": "Synthesize your team's creative perspective into ONE creative direction: the central idea, the tone, and the format that would resonate most.",
    },
    "legal_compliance": {
        "icon": "⚖️",
        "lead": "General Counsel",
        "agents": [
            ("Contract Lawyer",      "You review terms, liabilities, and contractual risk."),
            ("Privacy / GDPR Expert","You flag data handling risks and compliance requirements."),
            ("IP Lawyer",            "You protect and assess intellectual property exposure."),
            ("Regulatory Expert",    "You map applicable regulations by jurisdiction."),
            ("Compliance Officer",   "You ensure internal policies match external obligations."),
            ("Ethics Advisor",       "You raise uncomfortable questions about unintended consequences."),
            ("Employment Lawyer",    "You flag workforce-related legal risks."),
            ("Litigation Risk",      "You estimate litigation probability and cost of various paths."),
        ],
        "synthesis_instruction": "Synthesize your team's legal view into ONE risk assessment: the top legal risk, its likelihood, and the minimum viable mitigation.",
    },
    "strategy_nexus": {
        "icon": "🧭",
        "lead": "Chief Strategy Officer",
        "agents": [
            ("Corporate Strategist", "You think in competitive moats, market positioning, and 5-year trajectories."),
            ("Venture Capitalist",   "You evaluate ideas by market size, defensibility, and team capability."),
            ("Management Consultant","You apply frameworks (Porter, BCG, Jobs-to-be-done) to structure the problem."),
            ("Futurist",             "You extrapolate current signals into 10-year scenarios."),
            ("Economist",            "You think in incentive structures, market dynamics, and second-order effects."),
            ("Geopolitical Analyst", "You consider how macro forces — regulation, trade, politics — affect the decision."),
            ("First Principles Thinker", "You strip away assumptions and rebuild reasoning from scratch."),
            ("Devil's Advocate",     "You attack the strategy's core assumption. Your job is to find the fatal flaw."),
        ],
        "synthesis_instruction": "Synthesize your team's strategic view into ONE strategic recommendation: the core bet, why now, and the biggest risk to the thesis.",
    },
}


async def _run_department(
    dept_name: str,
    dept_config: dict,
    task: str,
    progress_fn: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
) -> tuple[str, str]:
    """Run all agents in a department in parallel, then synthesize via the lead.

    Returns: (dept_name, lead_synthesis_text)
    """
    icon = dept_config["icon"]
    lead = dept_config["lead"]
    agents = dept_config["agents"]
    synthesis_instruction = dept_config["synthesis_instruction"]

    if progress_fn:
        await progress_fn(f"{icon} {dept_name.upper()} dept launching {len(agents)} agents...")

    from agents import build_system_prompt, AGENT_MODELS

    # Run all specialist agents in parallel
    async def _agent_call(agent_name: str, agent_persona: str) -> str:
        system = build_system_prompt(
            f"You are the {agent_name} in the {dept_name} department.\n"
            f"Your specialist perspective: {agent_persona}\n\n"
            "Give your expert take in 3-4 focused sentences. Be direct, specific, opinionated."
        )
        model = AGENT_MODELS.get("general", "cerebras/qwen-3-235b")
        return await _llm_call(model, system, f"Analyse this from your specialist angle: {task}")

    agent_tasks = [_agent_call(name, persona) for name, persona in agents]
    agent_results_raw = await asyncio.gather(*agent_tasks, return_exceptions=True)

    agent_outputs = []
    for (name, _), result in zip(agents, agent_results_raw):
        if isinstance(result, Exception):
            agent_outputs.append(f"{name}: [error: {result}]")
        else:
            agent_outputs.append(f"{name}: {result}")

    # Department lead synthesizes all agent outputs
    team_briefing = "\n\n".join(agent_outputs)
    lead_system = build_system_prompt(
        f"You are the {lead} of the {dept_name} department.\n"
        f"Your team of {len(agents)} specialists has just briefed you. "
        f"{synthesis_instruction}"
    )
    lead_user = (
        f"Topic: {task}\n\n"
        f"Your team's briefing:\n{team_briefing[:6000]}"
    )
    # Use architect model (Gemini) for lead synthesis — large context
    lead_model = AGENT_MODELS.get("architect", "gemini/gemini-2.0-flash")
    lead_synthesis = await _llm_call(lead_model, lead_system, lead_user)

    return dept_name, lead_synthesis


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_swarm_debate(
    task: str,
    progress_fn: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
    departments: Optional[list[str]] = None,
    skip_departments: bool = False,
) -> list[str]:
    """Full swarm pipeline:

    Phase 1 (parallel): All 9 departments run their 8 agents simultaneously.
                        Each dept lead synthesizes their team into one position.
    Phase 2 (parallel): 6 debate personas run Round 1 simultaneously,
                        enriched with department lead positions as context.
    Phase 3 (sequential): Rounds 2, 3, 4 of the debate orchestrator.
    Phase 4: Format all output into Telegram-ready message chunks.

    Args:
        task: The question or topic to debate.
        progress_fn: Async callback that sends progress messages to Telegram.
        departments: Optional list of dept names to run (default: all 9).
        skip_departments: If True, skip Phase 1 and go straight to debate.

    Returns:
        List of Telegram message strings (each <= 4000 chars).
    """
    selected_depts = departments or list(DEPARTMENTS.keys())

    # ── PHASE 1: Department parallel sprint ──────────────────────────────────
    dept_positions: dict[str, str] = {}

    if not skip_departments:
        if progress_fn:
            total_agents = sum(len(DEPARTMENTS[d]["agents"]) for d in selected_depts)
            await progress_fn(
                f"🚀 <b>Swarm activated</b>\n"
                f"📊 {len(selected_depts)} departments · {total_agents} specialist agents\n"
                f"⚡ All running in parallel..."
            )

        dept_tasks = [
            _run_department(name, DEPARTMENTS[name], task, progress_fn)
            for name in selected_depts
            if name in DEPARTMENTS
        ]
        dept_results = await asyncio.gather(*dept_tasks, return_exceptions=True)

        for result in dept_results:
            if isinstance(result, Exception):
                logger.warning("Department failed: %s", result)
            else:
                dname, dpos = result
                dept_positions[dname] = dpos
                logger.info("Department %s completed", dname)

        if progress_fn:
            await progress_fn(
                f"✅ All {len(dept_positions)}/{len(selected_depts)} departments complete.\n"
                f"🔥 Entering 4-round debate..."
            )

    # Build department context string for the debate personas
    dept_context = ""
    if dept_positions:
        lines = ["Department lead positions:\n"]
        for dname, pos in dept_positions.items():
            cfg = DEPARTMENTS.get(dname, {})
            icon = cfg.get("icon", "🏢")
            lead = cfg.get("lead", dname)
            lines.append(f"{icon} <b>{lead}</b> ({dname}): {pos[:400]}")
        dept_context = "\n\n".join(lines)

    # ── PHASE 2+3: 4-round debate with department context injected ────────────

    # Monkey-patch the debate orchestrator's task to include dept context
    enriched_task = task
    if dept_context:
        enriched_task = (
            f"{task}\n\n"
            f"--- Department briefings (use as evidence) ---\n"
            f"{dept_context[:8000]}"
        )

    orchestrator = SwarmDebateOrchestrator(
        llm_call=_llm_call,
        progress_fn=progress_fn,
    )
    debate_result = await orchestrator.run(enriched_task)

    # ── PHASE 4: Format for Telegram ─────────────────────────────────────────
    messages = []

    # Message 0: Department summary (if depts were run)
    if dept_positions:
        dept_lines = [
            f"🏢 <b>SWARM — {len(dept_positions)} Department Briefings</b>\n"
            f"<b>Topic:</b> {html.escape(task[:200])}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
        ]
        for dname, pos in dept_positions.items():
            cfg = DEPARTMENTS.get(dname, {})
            icon = cfg.get("icon", "🏢")
            lead = cfg.get("lead", dname)
            dept_lines.append(
                f"{icon} <b>{lead}</b>\n"
                f"<i>{html.escape(pos[:350])}</i>\n"
            )
        dept_msg = "\n".join(dept_lines)
        # Split if too long
        if len(dept_msg) > 4000:
            dept_msg = dept_msg[:3990] + "..."
        messages.append(dept_msg)

    # Messages 1-3: Debate rounds from format_debate_for_telegram
    debate_messages = format_debate_for_telegram(debate_result, task)
    # Convert ** markdown to HTML bold for aiogram HTML parse mode
    debate_messages = [_md_to_html(m) for m in debate_messages]
    messages.extend(debate_messages)

    return messages


def _md_to_html(text: str) -> str:
    """Convert **bold** markdown to <b>bold</b> HTML for Telegram HTML parse mode."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def get_swarm_stats() -> str:
    """Return a formatted string with swarm capability stats."""
    total_dept_agents = sum(len(d["agents"]) for d in DEPARTMENTS.values())
    debate_agents = 6  # strategist, devil_advocate, researcher, pragmatist, visionary, critic
    total = total_dept_agents + debate_agents  # 72 + 6 = 78 + 9 dept leads = 87 total
    lines = [
        "<b>🐝 Swarm Capability</b>\n",
        f"📊 <b>{len(DEPARTMENTS)} departments</b> · <b>{total_dept_agents} specialist agents</b> · <b>{debate_agents} debate personas</b>",
        f"🔢 <b>Total agent calls per /swarm: ~{total_dept_agents + debate_agents * 4}</b> (dept agents × 1 + debate personas × 4 rounds)\n",
        "<b>Departments:</b>",
    ]
    for dname, cfg in DEPARTMENTS.items():
        lines.append(
            f"  {cfg['icon']} <b>{cfg['lead']}</b> — {len(cfg['agents'])} agents"
        )
    lines.append("\n<b>Debate Personas:</b>")
    from agents import DEBATE_ICONS
    for persona, icon in DEBATE_ICONS.items():
        lines.append(f"  {icon} {persona.replace('_', ' ').title()}")
    return "\n".join(lines)
