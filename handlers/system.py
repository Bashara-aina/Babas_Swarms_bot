"""System info handlers: /status /gpu /keys /models /resources."""

from __future__ import annotations

import contextlib
import html as html_mod
import platform
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import handlers.shared as _shared

from .shared import (
    _key_status,
    _start_time,
    allowed_cb,
    is_allowed,
    main_keyboard,
    send_chunked,
)

router = Router()


def _ui_keyboard(panel: str = "home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),
                InlineKeyboardButton(text="📊 Visual", callback_data="ui:visual"),
                InlineKeyboardButton(text="🩺 Health", callback_data="ui:health"),
            ],
            [
                InlineKeyboardButton(text="🤖 Agents", callback_data="ui:agents"),
                InlineKeyboardButton(text="🧭 Routing", callback_data="ui:routing"),
                InlineKeyboardButton(text="🧾 Audit", callback_data="ui:audit"),
            ],
            [
                InlineKeyboardButton(text="❓ Help", callback_data="ui:help"),
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ui:refresh:{panel}"),
            ],
        ]
    )


async def _build_home_panel(msg: Message) -> str:
    uptime_s = int(time.time() - _start_time)
    h, rem = divmod(uptime_s, 3600)
    m, s = divmod(rem, 60)
    uptime = f"{h}h {m}m {s}s"

    lines = [
        "<b>🏠 Legion Control Center</b>",
        f"⏱ Uptime: <code>{uptime}</code>",
        "",
        "<b>Quick Actions</b>",
        "• <code>/swarm &lt;task&gt;</code> — multi-agent execution",
        "• <code>/research &lt;topic&gt;</code> — deep web research",
        "• <code>/jarvis &lt;goal&gt;</code> — context bundle + plan (no auto-send)",
        "• <code>/runbook</code> — maintenance playbooks (sites, Supabase)",
        "• <code>/do &lt;task&gt;</code> — autonomous computer control",
        "• <code>/visualize</code> — system visual dashboard",
        "• <code>/swarm_viz</code> — agent communication visualization",
        "• <code>/capability_stats</code> — quality leaderboard",
        "• <code>/benchmark</code> — capability benchmark",
        "• <code>/redteam</code> — safety stress suite",
        "",
        "<b>Tips</b>",
        "• Tap buttons below to switch panels instantly",
        "• Use /start anytime to return to this home",
    ]

    try:
        from tools.resource_monitor import get_resource_snapshot

        snap = await get_resource_snapshot(force=True)
        lines.insert(3, f"🧠 RAM free: <code>{snap.ram_free_gb:.1f}GB</code>")
    except Exception:
        pass

    return "\n".join(lines)


async def _build_agents_panel() -> str:
    import router as agents

    lines = ["<b>🤖 Agent Universe</b>"]
    models = getattr(agents, "AGENT_MODELS", {}) or {}
    lines.append(f"Total configured agents: <b>{len(models)}</b>")
    if models:
        lines.append("")
        lines.append("<b>Agent → Model</b>")
        for key, model in sorted(models.items(), key=lambda x: x[0]):
            lines.append(f"• <code>{html_mod.escape(str(key))}</code> → {html_mod.escape(str(model))}")
    return "\n".join(lines)


async def _build_routing_panel() -> str:
    lines: list[str] = ["<b>🧭 Routing & Performance</b>"]
    if _shared._chief_of_staff:
        lines.append(_shared._chief_of_staff.format_stats_html())
    if _shared._cost_router:
        lines.append(_shared._cost_router.format_stats_html())
    if _shared._evaluator:
        lines.append(_shared._evaluator.format_scores_html())
    if len(lines) == 1:
        lines.append("ℹ️ Routing components not initialized yet.")
    return "\n\n".join(lines)


async def _build_audit_panel() -> str:
    if not _shared._audit_logger:
        return "<b>🧾 Audit Panel</b>\n\nℹ️ Audit logger not initialized."
    summary = await _shared._audit_logger.get_summary(hours=24)
    total = int(summary.get("total_events", 0))
    success = int(summary.get("success_count", 0))
    failure = int(summary.get("failure_count", 0))
    cost = float(summary.get("total_cost_usd", 0.0))
    lines = [
        "<b>🧾 Audit Panel (24h)</b>",
        f"Events: <b>{total}</b>",
        f"Success: <b>{success}</b> | Failures: <b>{failure}</b>",
        f"Cost: <code>${cost:.4f}</code>",
    ]
    by_action = summary.get("by_action", {}) or {}
    if by_action:
        lines.append("")
        lines.append("<b>Top Actions</b>")
        for action, count in sorted(by_action.items(), key=lambda x: x[1], reverse=True)[:8]:
            lines.append(f"• {html_mod.escape(str(action))}: {int(count)}")
    return "\n".join(lines)


def _build_help_panel() -> str:
    return (
        "<b>❓ Legion Help</b>\n"
        "\n"
        "<b>Core Commands</b>\n"
        "• <code>/run &lt;task&gt;</code> chat-only\n"
        "• <code>/do &lt;task&gt;</code> computer agent\n"
        "• <code>/swarm &lt;task&gt;</code> multi-agent team\n"
        "• <code>/research &lt;topic&gt;</code> deep search\n"
        "• <code>/jarvis &lt;goal&gt;</code> memory + screen + WA context → plan\n"
        "• <code>/runbook [id]</code> business/site maintenance checks\n"
        "\n"
        "<b>Visualization</b>\n"
        "• <code>/visualize</code> system dashboard\n"
        "• <code>/swarm_viz</code> swarm communication map\n"
        "• <code>/capability_stats</code> capability leaderboard\n"
        "• <code>/benchmark</code> capability benchmark\n"
        "• <code>/redteam</code> red-team regression\n"
        "\n"
        "<b>Diagnostics</b>\n"
        "• <code>/status</code> <code>/resources</code> <code>/gpu</code> <code>/keys</code>"
    )


async def _render_panel(msg: Message, panel: str) -> tuple[str, str]:
    panel = (panel or "home").lower().strip()
    if panel == "home":
        return panel, await _build_home_panel(msg)
    if panel == "visual":
        return panel, await _build_visual_summary(msg)
    if panel == "health":
        return panel, await _build_visual_summary(msg)
    if panel == "agents":
        return panel, await _build_agents_panel()
    if panel == "routing":
        return panel, await _build_routing_panel()
    if panel == "audit":
        return panel, await _build_audit_panel()
    if panel == "help":
        return panel, _build_help_panel()
    return "home", await _build_home_panel(msg)


@router.message(Command("start"))
@router.message(F.text == "🏠 Home")
async def cmd_start(msg: Message) -> None:
    if not is_allowed(msg):
        return

    # Onboarding keyboard — first-time / deep-dive options
    onboarding_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📖 Learn More", callback_data="onb:learn"),
                InlineKeyboardButton(text="🚀 Get Started", callback_data="onb:start"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Settings", callback_data="onb:settings"),
                InlineKeyboardButton(text="💡 Shortcuts", callback_data="onb:shortcuts"),
            ],
            [
                InlineKeyboardButton(text="📊 Dashboard", callback_data="ui:visual"),
                InlineKeyboardButton(text="🤖 Agents", callback_data="ui:agents"),
            ],
        ]
    )

    _panel, text = await _render_panel(msg, "home")
    await msg.answer(text, parse_mode="HTML", reply_markup=main_keyboard())
    await msg.answer(
        "<b>👋 Welcome to Legion!</b>\n\n"
        "<i>What would you like to do?</i>",
        parse_mode="HTML",
        reply_markup=onboarding_kb,
    )


@router.callback_query(lambda c: c.data and c.data.startswith("onb:"))
async def cb_onboarding(cb: CallbackQuery) -> None:
    if not allowed_cb(cb) or not cb.data:
        return

    action = cb.data.split(":", 1)[1] if ":" in cb.data else ""

    if action == "learn":
        text = (
            "<b>📖 Legion — What is this?</b>\n\n"
            "Legion is an <b>AI-powered agent system</b> that lives inside Telegram. "
            "It wraps a multi-agent orchestrator with computer control, "
            "web research, memory, and more.\n\n"
            "<b>Core concepts:</b>\n"
            "• <code>/run &lt;task&gt;</code> — chat-only response\n"
            "• <code>/do &lt;task&gt;</code> — computer agent (clicks, types, screenshots)\n"
            "• <code>/swarm &lt;task&gt;</code> — multi-agent team tackling complex goals\n"
            "• <code>/research &lt;topic&gt;</code> — deep web search with citations\n"
            "• <code>/jarvis &lt;goal&gt;</code> — bundle memory + screen → execution plan\n"
            "• <code>/budget</code> — live API cost tracking\n"
            "• <code>/soul</code> — view Legion's identity file (SOUL.md)\n\n"
            "Tap <b>🚀 Get Started</b> below to run your first task."
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚀 Get Started", callback_data="onb:start"),
                    InlineKeyboardButton(text="💡 Shortcuts", callback_data="onb:shortcuts"),
                ],
                [
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),
                ],
            ]
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await cb.answer("📖 Learn More")

    elif action == "start":
        text = (
            "<b>🚀 Get Started</b>\n\n"
            "Try one of these to see Legion in action:\n\n"
            "<b>1.</b> <code>/do Count files in home directory</code>\n"
            "<i>Legion will open a terminal and count files.</i>\n\n"
            "<b>2.</b> <code>/research Latest AI developments 2025</code>\n"
            "<i>Legion will search the web and summarize findings.</i>\n\n"
            "<b>3.</b> <code>/debate AI will replace programmers by 2030</code>\n"
            "<i>Legion will argue both sides with evidence.</i>\n\n"
            "<b>4.</b> <code>/run Write a Python quicksort</code>\n"
            "<i>Legion writes and explains code in chat.</i>"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📖 Learn More", callback_data="onb:learn"),
                    InlineKeyboardButton(text="💡 Shortcuts", callback_data="onb:shortcuts"),
                ],
                [
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),
                ],
            ]
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await cb.answer("🚀 Get Started")

    elif action == "settings":
        text = (
            "<b>⚙️ Settings</b>\n\n"
            "<b>Model routing:</b> Legion automatically picks the best model for each task. "
            "Use <code>/models</code> to see what's configured.\n\n"
            "<b>API keys:</b> Use <code>/keys</code> to check which providers are active.\n\n"
            "<b>Cost tracking:</b> <code>/budget</code> shows your daily/monthly spend.\n\n"
            "<b>Memory:</b> <code>/memory</code> shows your conversation context. "
            "Legion forgets after 7 days of inactivity.\n\n"
            "All settings are per-user and persist across sessions."
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔑 API Keys", callback_data="cmd:keys"),
                    InlineKeyboardButton(text="💰 Budget", callback_data="cmd:budget"),
                ],
                [
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),
                ],
            ]
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await cb.answer("⚙️ Settings")

    elif action == "shortcuts":
        from handlers.shortcuts import get_shortcuts_text

        text = get_shortcuts_text()
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📖 Learn More", callback_data="onb:learn"),
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),
                ],
            ]
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await cb.answer("💡 Shortcuts")

    else:
        await cb.answer("unknown onboarding action")


@router.callback_query(lambda c: c.data and c.data.startswith("cmd:"))
async def cb_cmd_redirect(cb: CallbackQuery) -> None:
    """Handle cmd:xxx callback data by forwarding to the message handler."""
    if not allowed_cb(cb) or not cb.data or not cb.message:
        return

    action = cb.data.split(":", 1)[1] if ":" in cb.data else ""

    if action == "keys":
        await cb.message.edit_text(_key_status(), parse_mode="HTML")
        await cb.answer("🔑 API Keys")
    elif action == "budget":
        # Forward to budget handler by simulating a message
        if not is_allowed(cb.message):
            return
        try:
            if _shared._budget_manager:
                budget_status = _shared._budget_manager.check_budget()
                day_breakdown = _shared._budget_manager.get_cost_breakdown("day")
                import os

                proactive_cap = int(os.getenv("MAX_PROACTIVE_PER_DAY", "3"))
                daily_spent = float(budget_status.get("daily_spent", 0.0))
                daily_limit = float(budget_status.get("daily_limit", 0.0))
                daily_pct = (daily_spent / daily_limit * 100.0) if daily_limit > 0 else 0.0

                lines = [
                    "<b>💰 Budget Dashboard</b>",
                    f"<b>Daily:</b> ${daily_spent:.4f} / ${daily_limit:.2f} ({daily_pct:.1f}%)",
                    f"<b>Daily remaining:</b> ${float(budget_status.get('daily_remaining', 0.0)):.4f}",
                    f"<b>Monthly:</b> ${float(budget_status.get('monthly_spent', 0.0)):.4f} / "
                    f"${float(budget_status.get('monthly_limit', 0.0)):.2f}",
                    f"<b>Proactive cap:</b> {proactive_cap}",
                    f"<b>Requests today:</b> {int(day_breakdown.get('total_requests', 0))}",
                    f"<b>Tokens today:</b> {int(day_breakdown.get('total_tokens', 0)):,}",
                ]
                await cb.message.edit_text("\n".join(lines), parse_mode="HTML")
            else:
                await cb.message.edit_text("<b>Budget manager not initialized.</b>", parse_mode="HTML")
        except Exception as e:
            import html as html_mod

            await cb.message.edit_text(
                f"<b>Budget error:</b> <code>{html_mod.escape(str(e)[:200])}</code>",
                parse_mode="HTML",
            )
        await cb.answer("💰 Budget")
    else:
        await cb.answer("unknown command")


@router.callback_query(lambda c: c.data and c.data.startswith("ui:"))
async def cb_ui_panel(cb: CallbackQuery) -> None:
    if not allowed_cb(cb) or not cb.message or not cb.data:
        return

    panel = cb.data.split(":", 2)[1] if ":" in cb.data else "home"
    if panel == "refresh":
        parts = cb.data.split(":", 2)
        panel = parts[2] if len(parts) > 2 else "home"

    try:
        if not isinstance(cb.message, Message):
            await cb.answer("unsupported message type")
            return
        panel_name, text = await _render_panel(cb.message, panel)
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=_ui_keyboard(panel_name))
        await cb.answer(f"Opened {panel_name}")
    except Exception as e:
        await cb.answer("panel error")
        with contextlib.suppress(Exception):
            await cb.message.answer(
                f"ui panel error: <code>{html_mod.escape(str(e)[:300])}</code>",
                parse_mode="HTML",
            )


def _bar(pct: float, width: int = 16) -> str:
    pct_clamped = max(0.0, min(100.0, pct))
    filled = round(width * pct_clamped / 100.0)
    return "[" + ("█" * filled) + ("░" * (width - filled)) + f"] {int(pct_clamped)}%"


def _mini_architecture() -> str:
    return (
        "<b>🧭 Legion Architecture</b>\n"
        "<pre>"
        "Telegram\n"
        "   │\n"
        "   ▼\n"
        "Aiogram Handlers\n"
        "   │\n"
        "   ├── chat()  → multi-provider LLM routing\n"
        "   ├── agent_loop() → computer tools + screenshots\n"
        "   ├── orchestrator → multi-agent DAG execution\n"
        "   └── memory/audit → persistence + telemetry\n"
        "</pre>"
    )


async def _build_visual_summary(msg: Message) -> str:
    uptime_s = int(time.time() - _start_time)
    h, rem = divmod(uptime_s, 3600)
    m, s = divmod(rem, 60)
    uptime = f"{h}h {m}m {s}s"

    lines = [
        "<b>📊 Legion Visual Dashboard</b>",
        f"⏱ Uptime: <code>{uptime}</code>",
        "",
        "<b>System Health</b>",
    ]

    try:
        from tools.resource_monitor import get_resource_snapshot

        snap = await get_resource_snapshot(force=True)
        ram_pct = max(0.0, min(100.0, (1.0 - (snap.ram_free_gb / max(snap.ram_total_gb, 0.1))) * 100.0))
        lines.append(f"🧠 RAM usage  {_bar(ram_pct)}")
        if snap.vram_total_gb and snap.vram_free_gb is not None:
            vram_pct = max(0.0, min(100.0, (1.0 - (snap.vram_free_gb / max(snap.vram_total_gb, 0.1))) * 100.0))
            lines.append(f"🎮 VRAM usage {_bar(vram_pct)}")
        else:
            lines.append("🎮 VRAM usage [not detected]")
        ollama_state = "ready" if snap.local_allowed else f"bypassed ({snap.block_reason[:50]})"
        lines.append(f"🤖 Local vision: <code>{html_mod.escape(ollama_state)}</code>")
    except Exception as e:
        lines.append(f"⚠️ resource monitor unavailable: <code>{html_mod.escape(str(e)[:120])}</code>")

    lines.extend(["", "<b>Reliability & Throughput (24h)</b>"])

    if _shared._audit_logger and msg.from_user:
        try:
            summary = await _shared._audit_logger.get_summary(hours=24)
            total = int(summary.get("total_events", 0))
            success = int(summary.get("success_count", 0))
            failure = int(summary.get("failure_count", 0))
            pass_rate = (success / total * 100.0) if total else 0.0
            fail_rate = (failure / total * 100.0) if total else 0.0
            lines.append(f"✅ Pass rate  {_bar(pass_rate)}")
            lines.append(f"❌ Fail rate  {_bar(fail_rate)}")
            lines.append(f"💸 Cost 24h: <code>${float(summary.get('total_cost_usd', 0.0)):.4f}</code>")

            by_agent = summary.get("by_agent", {}) or {}
            if by_agent:
                top = sorted(by_agent.items(), key=lambda x: x[1], reverse=True)[:5]
                lines.append("")
                lines.append("<b>Top Active Agents</b>")
                for name, count in top:
                    ratio = (count / max(total, 1)) * 100.0
                    lines.append(f"• <code>{html_mod.escape(str(name))}</code> {_bar(ratio, width=10)}")
        except Exception as e:
            lines.append(f"⚠️ audit summary unavailable: <code>{html_mod.escape(str(e)[:120])}</code>")
    else:
        lines.append("ℹ️ Audit logger not initialized yet")

    lines.extend(["", "<b>Model Keys</b>", _key_status()])
    return "\n".join(lines)


@router.message(Command("visualize"))
@router.message(Command("viz"))
@router.message(F.text == "📊 Visualize")
async def cmd_visualize(msg: Message) -> None:
    if not is_allowed(msg):
        return

    status_msg = await msg.answer("📊 building visual dashboard…")
    try:
        summary = await _build_visual_summary(msg)
        await status_msg.edit_text(summary, parse_mode="HTML")

        # Try sending a rich PNG grid if overnight dashboard module has data.
        try:
            from tools.dashboard import build_png_dashboard
            from tools.overnight import AGENT_STATUS, get_active_job_id, get_job_tasks

            job_id = get_active_job_id()
            job_tasks = get_job_tasks(job_id) if job_id else None
            png = await build_png_dashboard(AGENT_STATUS, job_id=job_id, job_tasks=job_tasks)
            if png:
                await msg.answer_photo(
                    photo=BufferedInputFile(png, filename="legion_dashboard.png"),
                    caption="📈 Live agent visualization",
                )
        except Exception:
            pass

        await msg.answer(_mini_architecture(), parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"visualization error: <code>{html_mod.escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ── /status ───────────────────────────────────────────────────────────────────
def _feature_flags_block() -> str:
    """Build a feature flags display block for /status."""
    lines = ["", "<b>🔧 Feature Flags</b>"]

    # Planned features (explicit FF flags in codebase)
    planned_flags = [
        ("FEATURE_GIT_LOG_ANALYSIS_ENABLED", "Git log analysis"),
        ("FEATURE_BRIEFING_CONSOLIDATION_ENABLED", "Briefing consolidation"),
        ("FEATURE_WEB_SEARCH_ENABLED", "Web search integration"),
        ("FEATURE_TOPIC_WEIGHTS_ENABLED", "Topic weights engine"),
    ]
    for flag_name, label in planned_flags:
        # Check if the flag exists and is True
        import os as _os

        enabled = _os.getenv(flag_name, "").strip().lower() in ("1", "true", "yes", "on")
        icon = "✅" if enabled else "🔇"
        status = "ON" if enabled else "OFF (v2.0)"
        lines.append(f"{icon} <code>{flag_name}</code> — {label} [{status}]")

    # Health check flags (conditional dependencies)
    lines.append("")
    lines.append("<b>📦 Conditional Features</b>")
    try:
        from core.health_check import FEATURE_FLAGS, run_health_check

        results = run_health_check()
        for feat, data in FEATURE_FLAGS.items():
            available = data.get("enabled", False)
            reason = results.get(feat, {}).get("reason", "OK")
            icon = "✅" if available else "⚠️"
            lines.append(f"{icon} <code>{feat}</code> — {reason[:40]}")
        # Show archived features as 🔇
        from core.health_check import _ARCHIVED_FEATURES

        for feat, data in _ARCHIVED_FEATURES.items():
            lines.append(f"🔇 <code>{feat}</code> — archived")
    except Exception:
        lines.append("⚠️ Could not load feature flags")

    # Optional external services
    lines.append("")
    lines.append("<b>🔗 External Services</b>")
    _has_voicevox = False
    try:
        import importlib.util

        _has_voicevox = importlib.util.find_spec("voicevox_core") is not None
    except Exception:
        pass
    icon_vv = "✅" if _has_voicevox else "⚠️"
    vv_status = "loaded" if _has_voicevox else "not installed"
    lines.append(f"{icon_vv} <code>VOICEVOX</code> — {vv_status}")

    _has_chromadb = False
    with contextlib.suppress(Exception):

        _has_chromadb = True
    icon_cdb = "✅" if _has_chromadb else "⚠️"
    cdb_status = "connected" if _has_chromadb else "not connected"
    lines.append(f"{icon_cdb} <code>CHROMADB</code> — {cdb_status}")

    return "\n".join(lines)


@router.message(Command("status"))
@router.message(F.text == "\u2699\ufe0f Status")
async def cmd_status(msg: Message) -> None:
    if not is_allowed(msg):
        return
    uptime_s = int(time.time() - _start_time)
    h, rem = divmod(uptime_s, 3600)
    m, s = divmod(rem, 60)
    uptime = f"{h}h {m}m {s}s"
    py_ver = platform.python_version()
    os_info = f"{platform.system()} {platform.release()}"

    key_block = _key_status()
    feature_block = _feature_flags_block()

    try:
        from tools.resource_monitor import get_resource_snapshot

        snap = await get_resource_snapshot()
        local_line = (
            "\U0001f916 Ollama: \u2705 ready"
            if snap.local_allowed
            else f"\U0001f916 Ollama: \u26a0\ufe0f bypassed ({snap.block_reason[:60]})"
        )
        ram_line = f"\U0001f9e0 RAM free: {snap.ram_free_gb:.1f}GB"
        gpu_line = (
            f"\U0001f3ae VRAM free: {snap.vram_free_gb:.1f}GB"
            if snap.vram_free_gb is not None
            else "\U0001f3ae GPU: not detected"
        )
        resource_block = f"\n{ram_line}\n{gpu_line}\n{local_line}"
    except Exception:
        resource_block = ""

    text = (
        f"<b>\U0001f916 Legion Status</b>\n\n"
        f"\u23f1 uptime: <code>{uptime}</code>\n"
        f"\U0001f40d Python: <code>{py_ver}</code>\n"
        f"\U0001f4bb OS: <code>{os_info}</code>\n"
        f"{resource_block}\n\n"
        f"{key_block}\n\n"
        f"{feature_block}"
    )
    await msg.answer(text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\U0001f4ca building stats\u2026")
    try:
        lines = ["<b>📊 Performance Metrics</b>", ""]

        # ── LLM latency percentiles ──────────────────────────────────────────
        try:
            from core.observability import get_metrics_snapshot

            data = get_metrics_snapshot()
            if data:
                all_latencies: list[float] = []
                for provider, stats in data.items():
                    calls = int(stats.get("calls", 0))
                    total_lat = float(stats.get("latency_ms", 0.0))
                    tokens = int(stats.get("tokens", 0))
                    errors = int(stats.get("errors", 0))
                    avg = total_lat / calls if calls else 0.0
                    all_latencies.append(avg)
                    lines.append(
                        f"• <b>{provider}</b>: calls={calls}, tokens={tokens}, avg={avg:.0f}ms, errors={errors}"
                    )
                if all_latencies:
                    sorted_lat = sorted(all_latencies)
                    p50 = sorted_lat[len(sorted_lat) // 2]
                    p95_idx = min(len(sorted_lat) - 1, int(len(sorted_lat) * 0.95))
                    p99_idx = min(len(sorted_lat) - 1, int(len(sorted_lat) * 0.99))
                    lines.append("")
                    lines.append(
                        f"LLM latency percentiles: p50=<b>{p50:.0f}ms</b>, "
                        f"p95=<b>{sorted_lat[p95_idx]:.0f}ms</b>, "
                        f"p99=<b>{sorted_lat[p99_idx]:.0f}ms</b>"
                    )
            else:
                lines.append("No LLM metrics yet.")
        except Exception as e:
            lines.append(f"⚠️ LLM metrics error: <code>{html_mod.escape(str(e)[:100])}</code>")

        # ── Token usage per session ────────────────────────────────────────────
        try:
            from core.observability import get_session_token_stats

            token_stats = get_session_token_stats(str(msg.from_user.id if msg.from_user else 0))
            if token_stats:
                lines.append("")
                lines.append(
                    f"Token usage (session): in=<b>{token_stats.get('prompt_tokens', 0)}</b> "
                    f"out=<b>{token_stats.get('completion_tokens', 0)}</b> "
                    f"total=<b>{token_stats.get('total_tokens', 0)}</b>"
                )
            else:
                lines.append("No token stats yet for this session.")
        except Exception:
            pass

        # ── Circuit breaker state ─────────────────────────────────────────────
        try:
            from core.circuit_breaker import get_circuit_breakers

            cbs = get_circuit_breakers()
            if cbs:
                lines.append("")
                lines.append("<b>Circuit Breakers</b>")
                for name, cb in cbs.items():
                    lines.append(f"• <b>{name}</b>: <code>{cb.state.value}</code> (failures={cb._failure_count})")
        except Exception as e:
            lines.append(f"⚠️ circuit breaker error: <code>{html_mod.escape(str(e)[:100])}</code>")

        # ── Memory tier counts ────────────────────────────────────────────────
        try:
            from core.memory_engine import MemoryEngine

            me = MemoryEngine()
            stats = me.get_stats()
            wm = stats.get("working", {})
            lines.append("")
            lines.append("<b>Memory Tiers</b>")
            lines.append(
                f"• Working: buffer=<b>{wm.get('buffer_size', 0)}</b>, "
                f"tokens=<b>{wm.get('total_tokens', 0)}</b>, "
                f"summary=<b>{'yes' if wm.get('has_summary') else 'no'}</b>"
            )
            em = stats.get("episodic", {})
            lines.append(f"• Episodic: db=<b>{'yes' if em.get('db_exists') else 'no'}</b>")
            pm = stats.get("permanent", {})
            lines.append(
                f"• Permanent: collection=<b>{pm.get('collection', '?')}</b>, docs~<b>{pm.get('approx_count', 0)}</b>"
            )
        except Exception as e:
            lines.append(f"⚠️ memory stats error: <code>{html_mod.escape(str(e)[:100])}</code>")

        await status_msg.edit_text("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"stats error: <code>{html_mod.escape(str(e)[:350])}</code>",
            parse_mode="HTML",
        )


# ── /gpu ──────────────────────────────────────────────────────────────────────
@router.message(Command("gpu"))
async def cmd_gpu(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\U0001f3ae checking GPU\u2026")
    try:
        from tools.resource_monitor import format_resource_html, get_resource_snapshot

        snap = await get_resource_snapshot(force=True)
        await status_msg.edit_text(format_resource_html(snap), parse_mode="HTML")
    except Exception:
        # Fallback to raw nvidia-smi
        try:
            from llm_client import run_shell_command

            out = await run_shell_command("nvidia-smi", timeout=10)
            await status_msg.edit_text(
                f"<pre>{html_mod.escape(out[:3000])}</pre>",
                parse_mode="HTML",
            )
        except Exception as e2:
            await status_msg.edit_text(
                f"GPU info unavailable: <code>{html_mod.escape(str(e2))}</code>",
                parse_mode="HTML",
            )


# ── /keys ──────────────────────────────────────────────────────────────────────
@router.message(Command("keys"))
async def cmd_keys(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(_key_status(), parse_mode="HTML")


# ── /models ────────────────────────────────────────────────────────────────────
@router.message(Command("models"))
async def cmd_models(msg: Message) -> None:
    if not is_allowed(msg):
        return
    import os

    import router as agents

    registry = getattr(agents, "AGENT_REGISTRY", {}) or {}
    if not registry:
        await msg.answer(agents.list_agents(), parse_mode="HTML")
        return

    lines = ["<b>🤖 Agent Registry (v5)</b>"]
    for key, meta in registry.items():
        required = getattr(meta, "requires_env", None)
        status = "active"
        if required and not os.getenv(required):
            status = "unavailable"
        lines.append(
            f"• <code>{html_mod.escape(key)}</code> — {html_mod.escape(meta.model)} "
            f"(<i>{html_mod.escape(meta.sdk)}</i>) [{status}]"
        )
    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("metrics"))
async def cmd_metrics(msg: Message) -> None:
    if not is_allowed(msg):
        return
    try:
        from core.observability import render_metrics_html

        await msg.answer(render_metrics_html(), parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"metrics unavailable: <code>{html_mod.escape(str(e)[:250])}</code>", parse_mode="HTML")


@router.message(Command("ping"))
async def cmd_ping(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer("🏓 Pong! Legion is alive.")


# ── /resources — live RAM + GPU + local model policy ──────────────────────────
@router.message(Command("resources"))
async def cmd_resources(msg: Message) -> None:
    """Show live RAM, GPU VRAM, and whether local Ollama is currently allowed."""
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\U0001f4ca reading system resources\u2026")
    try:
        from tools.resource_monitor import format_resource_html, get_resource_snapshot

        # force=True to bypass cache and get a fresh reading
        snap = await get_resource_snapshot(force=True)
        await status_msg.edit_text(format_resource_html(snap), parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(
            f"\u274c resource monitor error:\n<code>{html_mod.escape(str(e)[:400])}</code>\n\n"
            "Make sure <code>psutil</code> is installed: "
            "<code>pip install psutil pynvml</code>",
            parse_mode="HTML",
        )


@router.message(Command("capability_stats"))
@router.message(Command("cap_stats"))
async def cmd_capability_stats(msg: Message) -> None:
    """Show rolling capability leaderboard from recent runs."""
    if not is_allowed(msg):
        return

    status_msg = await msg.answer("🏁 building capability leaderboard…")
    try:
        from tools.capability_metrics import render_capability_summary_html

        text = render_capability_summary_html(hours=72)
        await status_msg.delete()
        await send_chunked(msg, text, model_used="capability-metrics")
    except Exception as e:
        await status_msg.edit_text(
            f"capability stats unavailable: <code>{html_mod.escape(str(e)[:350])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("benchmark"))
async def cmd_benchmark(msg: Message) -> None:
    """Run capability benchmark suite now."""
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("🏁 running capability benchmark suite…")
    try:
        from tools.capability_benchmark import render_suite_report_html, run_capability_suite

        report = await run_capability_suite(
            user_id=str(msg.from_user.id) if msg.from_user else "0",
            include_redteam=False,
        )
        text = render_suite_report_html(report, title="Capability Benchmark")
        await status_msg.delete()
        await send_chunked(msg, text, model_used="capability-benchmark")
    except Exception as e:
        await status_msg.edit_text(
            f"benchmark failed: <code>{html_mod.escape(str(e)[:350])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("compact"))
async def cmd_compact(msg: Message) -> None:
    """Manually compact conversation history to free context space."""
    if not is_allowed(msg):
        return
    try:
        from core.conversation_interface import (
            add_to_conversation,
            clear_conversation,
            get_conversation_history,
        )
        from llm_client import _compact_messages

        user_id = str(msg.from_user.id) if msg.from_user else "0"
        history = get_conversation_history(user_id, last_n=100)
        original = len(history)
        if original < 10:
            await msg.answer("Conversation is already short — no compaction needed.")
            return

        try:
            from core.hooks import get_hooks

            get_hooks().emit("pre_compact", {
                "user_id": user_id,
                "messages": list(history),
            })
        except Exception:
            pass

        compacted = _compact_messages(history, keep_recent=6)
        clear_conversation(user_id)
        for m in compacted[1:]:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role in ("user", "assistant") and content:
                add_to_conversation(user_id, role, content)

        try:
            from core.hooks import get_hooks
            get_hooks().emit("post_compact", {
                "user_id": user_id,
                "original_count": original,
                "compacted_count": len(compacted),
                "reduction": original - len(compacted),
            })
        except Exception:
            pass
        await msg.answer(
            f"✅ Compacted {original} → {len(compacted)} messages. "
            f"Reduced by {original - len(compacted)} turns.",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.answer(
            f"❌ Compaction failed: <code>{html_mod.escape(str(e)[:200])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("snapshot"))
async def cmd_snapshot(msg: Message) -> None:
    """Save a named snapshot of current conversation to wiki. GAP-17."""
    if not is_allowed(msg):
        return
    label = (msg.text or "").removeprefix("/snapshot").strip() or "manual snapshot"
    user_id = str(msg.from_user.id) if msg.from_user else "0"

    try:
        import html_mod

        from core.session_snapshots import create_snapshot

        snapshot_id = await create_snapshot(user_id, label=label)
        await msg.answer(
            f"📸 Snapshot saved: <code>{html_mod.escape(snapshot_id)}</code>\n"
            f"Label: {html_mod.escape(label)}\n"
            f"Restored with: /restore {snapshot_id}",
            parse_mode="HTML",
        )
    except Exception as e:
        await msg.answer(
            f"❌ Snapshot failed: <code>{html_mod.escape(str(e)[:200])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("restore"))
async def cmd_restore(msg: Message) -> None:
    """Restore a conversation from a wiki snapshot. GAP-17."""
    if not is_allowed(msg):
        return
    parts = (msg.text or "").removeprefix("/restore").strip().split()
    snapshot_id = parts[0] if parts else ""
    if not snapshot_id:
        await msg.answer("Usage: /restore <snapshot_id>")
        return

    user_id = str(msg.from_user.id) if msg.from_user else "0"
    try:
        from core.session_snapshots import restore_snapshot

        success = await restore_snapshot(snapshot_id, user_id)
        if success:
            await msg.answer(f"✅ Restored snapshot <code>{html_mod.escape(snapshot_id)}</code>")
        else:
            await msg.answer("❌ Could not restore snapshot — not found or error")
    except Exception as e:
        await msg.answer(
            f"❌ Restore failed: <code>{html_mod.escape(str(e)[:200])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("snapshots"))
async def cmd_snapshots(msg: Message) -> None:
    """List all available session snapshots. GAP-17."""
    if not is_allowed(msg):
        return
    try:
        import html_mod

        from core.session_snapshots import list_snapshots

        snaps = list_snapshots()
        if not snaps:
            await msg.answer("No snapshots available.")
            return

        lines = ["📸 Available snapshots:"]
        for s in snaps[:10]:
            fid = html_mod.escape(s["snapshot_id"])
            mod = html_mod.escape(s.get("modified", ""))
            lines.append(f"- <code>{fid}</code> ({mod})")

        await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        await msg.answer(
            f"❌ List failed: <code>{html_mod.escape(str(e)[:200])}</code>",
            parse_mode="HTML",
        )


@router.message(Command("redteam"))
@router.message(Command("capability_redteam"))
async def cmd_redteam(msg: Message) -> None:
    """Run red-team stress suite now."""
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("🛡 running red-team capability regression…")
    try:
        from tools.capability_benchmark import render_suite_report_html, run_capability_suite

        report = await run_capability_suite(
            user_id=str(msg.from_user.id) if msg.from_user else "0",
            include_redteam=True,
        )
        text = render_suite_report_html(report, title="Capability Red-Team")
        await status_msg.delete()
        await send_chunked(msg, text, model_used="capability-redteam")
    except Exception as e:
        await status_msg.edit_text(
            f"red-team failed: <code>{html_mod.escape(str(e)[:350])}</code>",
            parse_mode="HTML",
        )
