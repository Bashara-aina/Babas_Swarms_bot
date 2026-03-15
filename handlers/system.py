"""System info handlers: /status /gpu /keys /models /resources."""
from __future__ import annotations

import asyncio
import html as html_mod
import platform
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .shared import (
    _start_time,
    allowed_cb,
    _key_status,
    main_keyboard,
    is_allowed,
    send_chunked,
)
import handlers.shared as _shared

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
    panel, text = await _render_panel(msg, "home")
    await msg.answer(text, parse_mode="HTML", reply_markup=main_keyboard())
    await msg.answer("Use the control center buttons:", reply_markup=_ui_keyboard(panel))


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
        try:
            await cb.message.answer(
                f"ui panel error: <code>{html_mod.escape(str(e)[:300])}</code>",
                parse_mode="HTML",
            )
        except Exception:
            pass


def _bar(pct: float, width: int = 16) -> str:
    pct_clamped = max(0.0, min(100.0, pct))
    filled = int(round(width * pct_clamped / 100.0))
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
            from tools.overnight import AGENT_STATUS, get_active_job_id, get_job_tasks
            from tools.dashboard import build_png_dashboard

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
@router.message(Command("status"))
@router.message(F.text == "\u2699\ufe0f Status")
async def cmd_status(msg: Message) -> None:
    if not is_allowed(msg):
        return
    uptime_s  = int(time.time() - _start_time)
    h, rem    = divmod(uptime_s, 3600)
    m, s      = divmod(rem, 60)
    uptime    = f"{h}h {m}m {s}s"
    py_ver    = platform.python_version()
    os_info   = f"{platform.system()} {platform.release()}"

    key_block = _key_status()

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
        f"{key_block}"
    )
    await msg.answer(text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(msg: Message) -> None:
    await cmd_status(msg)


# ── /gpu ──────────────────────────────────────────────────────────────────────
@router.message(Command("gpu"))
async def cmd_gpu(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\U0001f3ae checking GPU\u2026")
    try:
        from tools.resource_monitor import get_resource_snapshot, format_resource_html
        snap = await get_resource_snapshot(force=True)
        await status_msg.edit_text(format_resource_html(snap), parse_mode="HTML")
    except Exception as e:
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
    import router as agents
    await msg.answer(agents.list_agents(), parse_mode="HTML")


# ── /resources — live RAM + GPU + local model policy ──────────────────────────
@router.message(Command("resources"))
async def cmd_resources(msg: Message) -> None:
    """Show live RAM, GPU VRAM, and whether local Ollama is currently allowed."""
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\U0001f4ca reading system resources\u2026")
    try:
        from tools.resource_monitor import get_resource_snapshot, format_resource_html
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
        from tools.capability_benchmark import run_capability_suite, render_suite_report_html

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


@router.message(Command("redteam"))
@router.message(Command("capability_redteam"))
async def cmd_redteam(msg: Message) -> None:
    """Run red-team stress suite now."""
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("🛡 running red-team capability regression…")
    try:
        from tools.capability_benchmark import run_capability_suite, render_suite_report_html

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
