"""System info handlers: /status /gpu /keys /models /resources."""  # type: ignore[reportUnusedCoroutine]

from __future__ import annotations

import contextlib
import html as html_mod
import platform
import time

from aiogram import F, Router  # type: ignore[reportUnusedCoroutine]
from aiogram.filters import Command  # type: ignore[reportUnusedCoroutine]
from aiogram.types import (  # type: ignore[reportUnusedCoroutine]
    BufferedInputFile,  # type: ignore[reportUnusedCoroutine]
    CallbackQuery,  # type: ignore[reportUnusedCoroutine]
    InlineKeyboardButton,  # type: ignore[reportUnusedCoroutine]
    InlineKeyboardMarkup,  # type: ignore[reportUnusedCoroutine]
    Message,  # type: ignore[reportUnusedCoroutine]
)

import handlers.shared as _shared  # type: ignore[reportUnusedCoroutine]

from .shared import (  # type: ignore[reportUnusedCoroutine]
    _key_status,  # type: ignore[reportUnusedCoroutine]
    _start_time,  # type: ignore[reportUnusedCoroutine]
    allowed_cb,  # type: ignore[reportUnusedCoroutine]
    is_allowed,  # type: ignore[reportUnusedCoroutine]
    main_keyboard,  # type: ignore[reportUnusedCoroutine]
    send_chunked,  # type: ignore[reportUnusedCoroutine]
)

router = Router()  # type: ignore[reportUnusedCoroutine]


def _ui_keyboard(panel: str = "home") -> InlineKeyboardMarkup:  # type: ignore[reportUnusedCoroutine]
    return InlineKeyboardMarkup(  # type: ignore[reportUnusedCoroutine]
        inline_keyboard=[  # type: ignore[reportUnusedCoroutine]
            [
                InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),  # type: ignore[reportUnusedCoroutine]
                InlineKeyboardButton(text="📊 Visual", callback_data="ui:visual"),  # type: ignore[reportUnusedCoroutine]
                InlineKeyboardButton(text="🩺 Health", callback_data="ui:health"),  # type: ignore[reportUnusedCoroutine]
            ],  # type: ignore[reportUnusedCoroutine]
            [
                InlineKeyboardButton(text="🤖 Agents", callback_data="ui:agents"),  # type: ignore[reportUnusedCoroutine]
                InlineKeyboardButton(text="🧭 Routing", callback_data="ui:routing"),  # type: ignore[reportUnusedCoroutine]
                InlineKeyboardButton(text="🧾 Audit", callback_data="ui:audit"),  # type: ignore[reportUnusedCoroutine]
            ],  # type: ignore[reportUnusedCoroutine]
            [
                InlineKeyboardButton(text="❓ Help", callback_data="ui:help"),  # type: ignore[reportUnusedCoroutine]
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"ui:refresh:{panel}"),  # type: ignore[reportUnusedCoroutine]
            ],  # type: ignore[reportUnusedCoroutine]
        ]
    )


async def _build_home_panel(msg: Message) -> str:  # type: ignore[reportUnusedCoroutine]
    uptime_s = int(time.time() - _start_time)  # type: ignore[reportUnusedCoroutine]
    h, rem = divmod(uptime_s, 3600)  # type: ignore[reportUnusedCoroutine]
    m, s = divmod(rem, 60)  # type: ignore[reportUnusedCoroutine]
    uptime = f"{h}h {m}m {s}s"  # type: ignore[reportUnusedCoroutine]

    lines = [  # type: ignore[reportUnusedCoroutine]
        "<b>🏠 Legion Control Center</b>",  # type: ignore[reportUnusedCoroutine]
        f"⏱ Uptime: <code>{uptime}</code>",  # type: ignore[reportUnusedCoroutine]
        "",  # type: ignore[reportUnusedCoroutine]
        "<b>Quick Actions</b>",  # type: ignore[reportUnusedCoroutine]
        "• <code>/swarm &lt;task&gt;</code> — multi-agent execution",  # type: ignore[reportUnusedCoroutine]
        "• <code>/research &lt;topic&gt;</code> — deep web research",  # type: ignore[reportUnusedCoroutine]
        "• <code>/jarvis &lt;goal&gt;</code> — context bundle + plan (no auto-send)",  # type: ignore[reportUnusedCoroutine]
        "• <code>/runbook</code> — maintenance playbooks (sites, Supabase)",  # type: ignore[reportUnusedCoroutine]
        "• <code>/do &lt;task&gt;</code> — autonomous computer control",  # type: ignore[reportUnusedCoroutine]
        "• <code>/visualize</code> — system visual dashboard",  # type: ignore[reportUnusedCoroutine]
        "• <code>/swarm_viz</code> — agent communication visualization",  # type: ignore[reportUnusedCoroutine]
        "• <code>/capability_stats</code> — quality leaderboard",  # type: ignore[reportUnusedCoroutine]
        "• <code>/benchmark</code> — capability benchmark",  # type: ignore[reportUnusedCoroutine]
        "• <code>/redteam</code> — safety stress suite",  # type: ignore[reportUnusedCoroutine]
        "",  # type: ignore[reportUnusedCoroutine]
        "<b>Tips</b>",  # type: ignore[reportUnusedCoroutine]
        "• Tap buttons below to switch panels instantly",  # type: ignore[reportUnusedCoroutine]
        "• Use /start anytime to return to this home",  # type: ignore[reportUnusedCoroutine]
    ]

    try:
        from tools.resource_monitor import (
            get_resource_snapshot,  # type: ignore[reportUnusedCoroutine]
        )

        snap = await get_resource_snapshot(force=True)  # type: ignore[reportUnusedCoroutine]
        lines.insert(3, f"🧠 RAM free: <code>{snap.ram_free_gb:.1f}GB</code>")  # type: ignore[reportUnusedCoroutine]
    except Exception:
        pass

    return "\n".join(lines)  # type: ignore[reportUnusedCoroutine]


async def _build_agents_panel() -> str:  # type: ignore[reportUnusedCoroutine]
    import router as agents

    lines = ["<b>🤖 Agent Universe</b>"]  # type: ignore[reportUnusedCoroutine]
    models = getattr(agents, "AGENT_MODELS", {}) or {}  # type: ignore[reportUnusedCoroutine]
    lines.append(f"Total configured agents: <b>{len(models)}</b>")  # type: ignore[reportUnusedCoroutine]
    if models:
        lines.append("")  # type: ignore[reportUnusedCoroutine]
        lines.append("<b>Agent → Model</b>")  # type: ignore[reportUnusedCoroutine]
        for key, model in sorted(models.items(), key=lambda x: x[0]):  # type: ignore[reportUnusedCoroutine]
            lines.append(f"• <code>{html_mod.escape(str(key))}</code> → {html_mod.escape(str(model))}")  # type: ignore[reportUnusedCoroutine]
    return "\n".join(lines)  # type: ignore[reportUnusedCoroutine]


async def _build_routing_panel() -> str:  # type: ignore[reportUnusedCoroutine]
    lines: list[str] = ["<b>🧭 Routing & Performance</b>"]  # type: ignore[reportUnusedCoroutine]
    if _shared._chief_of_staff:  # type: ignore[reportUnusedCoroutine]
        lines.append(_shared._chief_of_staff.format_stats_html())  # type: ignore[reportUnusedCoroutine]
    if _shared._cost_router:  # type: ignore[reportUnusedCoroutine]
        lines.append(_shared._cost_router.format_stats_html())  # type: ignore[reportUnusedCoroutine]
    if _shared._evaluator:  # type: ignore[reportUnusedCoroutine]
        lines.append(_shared._evaluator.format_scores_html())  # type: ignore[reportUnusedCoroutine]
    if len(lines) == 1:  # type: ignore[reportUnusedCoroutine]
        lines.append("ℹ️ Routing components not initialized yet.")  # type: ignore[reportUnusedCoroutine]
    return "\n\n".join(lines)  # type: ignore[reportUnusedCoroutine]


async def _build_audit_panel() -> str:  # type: ignore[reportUnusedCoroutine]
    if not _shared._audit_logger:  # type: ignore[reportUnusedCoroutine]
        return "<b>🧾 Audit Panel</b>\n\nℹ️ Audit logger not initialized."  # type: ignore[reportUnusedCoroutine]
    summary = await _shared._audit_logger.get_summary(hours=24)  # type: ignore[reportUnusedCoroutine]
    total = int(summary.get("total_events", 0))  # type: ignore[reportUnusedCoroutine]
    success = int(summary.get("success_count", 0))  # type: ignore[reportUnusedCoroutine]
    failure = int(summary.get("failure_count", 0))  # type: ignore[reportUnusedCoroutine]
    cost = float(summary.get("total_cost_usd", 0.0))  # type: ignore[reportUnusedCoroutine]
    lines = [  # type: ignore[reportUnusedCoroutine]
        "<b>🧾 Audit Panel (24h)</b>",  # type: ignore[reportUnusedCoroutine]
        f"Events: <b>{total}</b>",  # type: ignore[reportUnusedCoroutine]
        f"Success: <b>{success}</b> | Failures: <b>{failure}</b>",  # type: ignore[reportUnusedCoroutine]
        f"Cost: <code>${cost:.4f}</code>",  # type: ignore[reportUnusedCoroutine]
    ]
    by_action = summary.get("by_action", {}) or {}  # type: ignore[reportUnusedCoroutine]
    if by_action:
        lines.append("")  # type: ignore[reportUnusedCoroutine]
        lines.append("<b>Top Actions</b>")  # type: ignore[reportUnusedCoroutine]
        for action, count in sorted(by_action.items(), key=lambda x: x[1], reverse=True)[:8]:  # type: ignore[reportUnusedCoroutine]
            lines.append(f"• {html_mod.escape(str(action))}: {int(count)}")  # type: ignore[reportUnusedCoroutine]
    return "\n".join(lines)  # type: ignore[reportUnusedCoroutine]


def _build_help_panel() -> str:  # type: ignore[reportUnusedCoroutine]
    return (  # type: ignore[reportUnusedCoroutine]
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


async def _render_panel(msg: Message, panel: str) -> tuple[str, str]:  # type: ignore[reportUnusedCoroutine]
    panel = (panel or "home").lower().strip()  # type: ignore[reportUnusedCoroutine]
    if panel == "home":  # type: ignore[reportUnusedCoroutine]
        return panel, await _build_home_panel(msg)  # type: ignore[reportUnusedCoroutine]
    if panel == "visual":  # type: ignore[reportUnusedCoroutine]
        return panel, await _build_visual_summary(msg)  # type: ignore[reportUnusedCoroutine]
    if panel == "health":  # type: ignore[reportUnusedCoroutine]
        return panel, await _build_visual_summary(msg)  # type: ignore[reportUnusedCoroutine]
    if panel == "agents":  # type: ignore[reportUnusedCoroutine]
        return panel, await _build_agents_panel()  # type: ignore[reportUnusedCoroutine]
    if panel == "routing":  # type: ignore[reportUnusedCoroutine]
        return panel, await _build_routing_panel()  # type: ignore[reportUnusedCoroutine]
    if panel == "audit":  # type: ignore[reportUnusedCoroutine]
        return panel, await _build_audit_panel()  # type: ignore[reportUnusedCoroutine]
    if panel == "help":  # type: ignore[reportUnusedCoroutine]
        return panel, _build_help_panel()  # type: ignore[reportUnusedCoroutine]
    return "home", await _build_home_panel(msg)  # type: ignore[reportUnusedCoroutine]


@router.message(Command("start"))  # type: ignore[reportUnusedCoroutine]
@router.message(F.text == "🏠 Home")  # type: ignore[reportUnusedCoroutine]
async def cmd_start(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return

    # Onboarding keyboard — first-time / deep-dive options
    onboarding_kb = InlineKeyboardMarkup(  # type: ignore[reportUnusedCoroutine]
        inline_keyboard=[  # type: ignore[reportUnusedCoroutine]
            [
                InlineKeyboardButton(text="📖 Learn More", callback_data="onb:learn"),  # type: ignore[reportUnusedCoroutine]
                InlineKeyboardButton(text="🚀 Get Started", callback_data="onb:start"),  # type: ignore[reportUnusedCoroutine]
            ],  # type: ignore[reportUnusedCoroutine]
            [
                InlineKeyboardButton(text="⚙️ Settings", callback_data="onb:settings"),  # type: ignore[reportUnusedCoroutine]
                InlineKeyboardButton(text="💡 Shortcuts", callback_data="onb:shortcuts"),  # type: ignore[reportUnusedCoroutine]
            ],  # type: ignore[reportUnusedCoroutine]
            [
                InlineKeyboardButton(text="📊 Dashboard", callback_data="ui:visual"),  # type: ignore[reportUnusedCoroutine]
                InlineKeyboardButton(text="🤖 Agents", callback_data="ui:agents"),  # type: ignore[reportUnusedCoroutine]
            ],  # type: ignore[reportUnusedCoroutine]
        ]
    )

    _panel, text = await _render_panel(msg, "home")  # type: ignore[reportUnusedCoroutine]
    await msg.answer(text, parse_mode="HTML", reply_markup=main_keyboard())  # type: ignore[reportUnusedCoroutine]
    await msg.answer(  # type: ignore[reportUnusedCoroutine]
        "<b>👋 Welcome to Legion!</b>\n\n"
        "<i>What would you like to do?</i>",  # type: ignore[reportUnusedCoroutine]
        parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        reply_markup=onboarding_kb,  # type: ignore[reportUnusedCoroutine]
    )


@router.callback_query(lambda c: c.data and c.data.startswith("onb:"))  # type: ignore[reportUnusedCoroutine]
async def cb_onboarding(cb: CallbackQuery) -> None:  # type: ignore[reportUnusedCoroutine]
    if not allowed_cb(cb) or not cb.data:  # type: ignore[reportUnusedCoroutine]
        return

    action = cb.data.split(":", 1)[1] if ":" in cb.data else ""  # type: ignore[reportUnusedCoroutine]

    if action == "learn":  # type: ignore[reportUnusedCoroutine]
        text = (  # type: ignore[reportUnusedCoroutine]
            "<b>📖 Legion — What is this?</b>\n\n"
            "Legion is an <b>AI-powered agent system</b> that lives inside Telegram. "  # type: ignore[reportUnusedCoroutine]
            "It wraps a multi-agent orchestrator with computer control, "  # type: ignore[reportUnusedCoroutine]
            "web research, memory, and more.\n\n"  # type: ignore[reportUnusedCoroutine]
            "<b>Core concepts:</b>\n"
            "• <code>/run &lt;task&gt;</code> — chat-only response\n"
            "• <code>/do &lt;task&gt;</code> — computer agent (clicks, types, screenshots)\n"  # type: ignore[reportUnusedCoroutine]
            "• <code>/swarm &lt;task&gt;</code> — multi-agent team tackling complex goals\n"
            "• <code>/research &lt;topic&gt;</code> — deep web search with citations\n"
            "• <code>/jarvis &lt;goal&gt;</code> — bundle memory + screen → execution plan\n"
            "• <code>/budget</code> — live API cost tracking\n"
            "• <code>/soul</code> — view Legion's identity file (SOUL.md)\n\n"  # type: ignore[reportUnusedCoroutine]
            "Tap <b>🚀 Get Started</b> below to run your first task."  # type: ignore[reportUnusedCoroutine]
        )
        kb = InlineKeyboardMarkup(  # type: ignore[reportUnusedCoroutine]
            inline_keyboard=[  # type: ignore[reportUnusedCoroutine]
                [
                    InlineKeyboardButton(text="🚀 Get Started", callback_data="onb:start"),  # type: ignore[reportUnusedCoroutine]
                    InlineKeyboardButton(text="💡 Shortcuts", callback_data="onb:shortcuts"),  # type: ignore[reportUnusedCoroutine]
                ],  # type: ignore[reportUnusedCoroutine]
                [
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),  # type: ignore[reportUnusedCoroutine]
                ],  # type: ignore[reportUnusedCoroutine]
            ]
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)  # type: ignore[reportOptionalMemberAccess]
        await cb.answer("📖 Learn More")  # type: ignore[reportUnusedCoroutine]

    elif action == "start":  # type: ignore[reportUnusedCoroutine]
        text = (  # type: ignore[reportUnusedCoroutine]
            "<b>🚀 Get Started</b>\n\n"
            "Try one of these to see Legion in action:\n\n"
            "<b>1.</b> <code>/do Count files in home directory</code>\n"  # type: ignore[reportUnusedCoroutine]
            "<i>Legion will open a terminal and count files.</i>\n\n"  # type: ignore[reportUnusedCoroutine]
            "<b>2.</b> <code>/research Latest AI developments 2025</code>\n"  # type: ignore[reportUnusedCoroutine]
            "<i>Legion will search the web and summarize findings.</i>\n\n"  # type: ignore[reportUnusedCoroutine]
            "<b>3.</b> <code>/debate AI will replace programmers by 2030</code>\n"  # type: ignore[reportUnusedCoroutine]
            "<i>Legion will argue both sides with evidence.</i>\n\n"  # type: ignore[reportUnusedCoroutine]
            "<b>4.</b> <code>/run Write a Python quicksort</code>\n"  # type: ignore[reportUnusedCoroutine]
            "<i>Legion writes and explains code in chat.</i>"  # type: ignore[reportUnusedCoroutine]
        )
        kb = InlineKeyboardMarkup(  # type: ignore[reportUnusedCoroutine]
            inline_keyboard=[  # type: ignore[reportUnusedCoroutine]
                [
                    InlineKeyboardButton(text="📖 Learn More", callback_data="onb:learn"),  # type: ignore[reportUnusedCoroutine]
                    InlineKeyboardButton(text="💡 Shortcuts", callback_data="onb:shortcuts"),  # type: ignore[reportUnusedCoroutine]
                ],  # type: ignore[reportUnusedCoroutine]
                [
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),  # type: ignore[reportUnusedCoroutine]
                ],  # type: ignore[reportUnusedCoroutine]
            ]
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)  # type: ignore[reportOptionalMemberAccess]
        await cb.answer("🚀 Get Started")  # type: ignore[reportUnusedCoroutine]

    elif action == "settings":  # type: ignore[reportUnusedCoroutine]
        text = (  # type: ignore[reportUnusedCoroutine]
            "<b>⚙️ Settings</b>\n\n"
            "<b>Model routing:</b> Legion automatically picks the best model for each task. "  # type: ignore[reportUnusedCoroutine]
            "Use <code>/models</code> to see what's configured.\n\n"  # type: ignore[reportUnusedCoroutine]
            "<b>API keys:</b> Use <code>/keys</code> to check which providers are active.\n\n"  # type: ignore[reportUnusedCoroutine]
            "<b>Cost tracking:</b> <code>/budget</code> shows your daily/monthly spend.\n\n"  # type: ignore[reportUnusedCoroutine]
            "<b>Memory:</b> <code>/memory</code> shows your conversation context. "  # type: ignore[reportUnusedCoroutine]
            "Legion forgets after 7 days of inactivity.\n\n"  # type: ignore[reportUnusedCoroutine]
            "All settings are per-user and persist across sessions."  # type: ignore[reportUnusedCoroutine]
        )
        kb = InlineKeyboardMarkup(  # type: ignore[reportUnusedCoroutine]
            inline_keyboard=[  # type: ignore[reportUnusedCoroutine]
                [
                    InlineKeyboardButton(text="🔑 API Keys", callback_data="cmd:keys"),  # type: ignore[reportUnusedCoroutine]
                    InlineKeyboardButton(text="💰 Budget", callback_data="cmd:budget"),  # type: ignore[reportUnusedCoroutine]
                ],  # type: ignore[reportUnusedCoroutine]
                [
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),  # type: ignore[reportUnusedCoroutine]
                ],  # type: ignore[reportUnusedCoroutine]
            ]
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)  # type: ignore[reportOptionalMemberAccess]
        await cb.answer("⚙️ Settings")  # type: ignore[reportUnusedCoroutine]

    elif action == "shortcuts":  # type: ignore[reportUnusedCoroutine]
        from handlers.shortcuts import get_shortcuts_text  # type: ignore[reportUnusedCoroutine]

        text = get_shortcuts_text()  # type: ignore[reportUnusedCoroutine]
        kb = InlineKeyboardMarkup(  # type: ignore[reportUnusedCoroutine]
            inline_keyboard=[  # type: ignore[reportUnusedCoroutine]
                [
                    InlineKeyboardButton(text="📖 Learn More", callback_data="onb:learn"),  # type: ignore[reportUnusedCoroutine]
                    InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),  # type: ignore[reportUnusedCoroutine]
                ],  # type: ignore[reportUnusedCoroutine]
            ]
        )
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)  # type: ignore[reportOptionalMemberAccess]
        await cb.answer("💡 Shortcuts")  # type: ignore[reportUnusedCoroutine]

    else:
        await cb.answer("unknown onboarding action")  # type: ignore[reportUnusedCoroutine]


@router.callback_query(lambda c: c.data and c.data.startswith("cmd:"))  # type: ignore[reportUnusedCoroutine]
async def cb_cmd_redirect(cb: CallbackQuery) -> None:  # type: ignore[reportUnusedCoroutine]
    """Handle cmd:xxx callback data by forwarding to the message handler."""  # type: ignore[reportUnusedCoroutine]
    if not allowed_cb(cb) or not cb.data or not cb.message:  # type: ignore[reportUnusedCoroutine]
        return

    action = cb.data.split(":", 1)[1] if ":" in cb.data else ""  # type: ignore[reportUnusedCoroutine]

    if action == "keys":  # type: ignore[reportUnusedCoroutine]
        await cb.message.edit_text(_key_status(), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        await cb.answer("🔑 API Keys")  # type: ignore[reportUnusedCoroutine]
    elif action == "budget":  # type: ignore[reportUnusedCoroutine]
        # Forward to budget handler by simulating a message
        if not is_allowed(cb.message):  # type: ignore[reportUnusedCoroutine]
            return
        try:
            if _shared._budget_manager:  # type: ignore[reportUnusedCoroutine]
                budget_status = _shared._budget_manager.check_budget()  # type: ignore[reportUnusedCoroutine]
                day_breakdown = _shared._budget_manager.get_cost_breakdown("day")  # type: ignore[reportUnusedCoroutine]
                import os

                proactive_cap = int(os.getenv("MAX_PROACTIVE_PER_DAY", "3"))  # type: ignore[reportUnusedCoroutine]
                daily_spent = float(budget_status.get("daily_spent", 0.0))  # type: ignore[reportUnusedCoroutine]
                daily_limit = float(budget_status.get("daily_limit", 0.0))  # type: ignore[reportUnusedCoroutine]
                daily_pct = (daily_spent / daily_limit * 100.0) if daily_limit > 0 else 0.0  # type: ignore[reportUnusedCoroutine]

                lines = [  # type: ignore[reportUnusedCoroutine]
                    "<b>💰 Budget Dashboard</b>",  # type: ignore[reportUnusedCoroutine]
                    f"<b>Daily:</b> ${daily_spent:.4f} / ${daily_limit:.2f} ({daily_pct:.1f}%)",  # type: ignore[reportUnusedCoroutine]
                    f"<b>Daily remaining:</b> ${float(budget_status.get('daily_remaining', 0.0)):.4f}",  # type: ignore[reportUnusedCoroutine]
                    f"<b>Monthly:</b> ${float(budget_status.get('monthly_spent', 0.0)):.4f} / "  # type: ignore[reportUnusedCoroutine]
                    f"${float(budget_status.get('monthly_limit', 0.0)):.2f}",  # type: ignore[reportUnusedCoroutine]
                    f"<b>Proactive cap:</b> {proactive_cap}",  # type: ignore[reportUnusedCoroutine]
                    f"<b>Requests today:</b> {int(day_breakdown.get('total_requests', 0))}",  # type: ignore[reportUnusedCoroutine]
                    f"<b>Tokens today:</b> {int(day_breakdown.get('total_tokens', 0)):,}",  # type: ignore[reportUnusedCoroutine]
                ]
                await cb.message.edit_text("\n".join(lines), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
            else:
                await cb.message.edit_text("<b>Budget manager not initialized.</b>", parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
        except Exception as e:
            import html as html_mod

            await cb.message.edit_text(  # type: ignore[reportOptionalMemberAccess]
                f"<b>Budget error:</b> <code>{html_mod.escape(str(e)[:200])}</code>",  # type: ignore[reportUnusedCoroutine]
                parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
            )
        await cb.answer("💰 Budget")  # type: ignore[reportUnusedCoroutine]
    else:
        await cb.answer("unknown command")  # type: ignore[reportUnusedCoroutine]


@router.callback_query(lambda c: c.data and c.data.startswith("ui:"))  # type: ignore[reportUnusedCoroutine]
async def cb_ui_panel(cb: CallbackQuery) -> None:  # type: ignore[reportUnusedCoroutine]
    if not allowed_cb(cb) or not cb.message or not cb.data:  # type: ignore[reportUnusedCoroutine]
        return

    panel = cb.data.split(":", 2)[1] if ":" in cb.data else "home"  # type: ignore[reportUnusedCoroutine]
    if panel == "refresh":  # type: ignore[reportUnusedCoroutine]
        parts = cb.data.split(":", 2)  # type: ignore[reportUnusedCoroutine]
        panel = parts[2] if len(parts) > 2 else "home"  # type: ignore[reportUnusedCoroutine]

    try:
        if not isinstance(cb.message, Message):  # type: ignore[reportUnusedCoroutine]
            await cb.answer("unsupported message type")  # type: ignore[reportUnusedCoroutine]
            return
        panel_name, text = await _render_panel(cb.message, panel)  # type: ignore[reportUnusedCoroutine]
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=_ui_keyboard(panel_name))  # type: ignore[reportOptionalMemberAccess]
        await cb.answer(f"Opened {panel_name}")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        await cb.answer("panel error")  # type: ignore[reportUnusedCoroutine]
        with contextlib.suppress(Exception):  # type: ignore[reportUnusedCoroutine]
            await cb.message.answer(  # type: ignore[reportUnusedCoroutine]
                f"ui panel error: <code>{html_mod.escape(str(e)[:300])}</code>",  # type: ignore[reportUnusedCoroutine]
                parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
            )


def _bar(pct: float, width: int = 16) -> str:  # type: ignore[reportUnusedCoroutine]
    pct_clamped = max(0.0, min(100.0, pct))  # type: ignore[reportUnusedCoroutine]
    filled = round(width * pct_clamped / 100.0)  # type: ignore[reportUnusedCoroutine]
    return "[" + ("█" * filled) + ("░" * (width - filled)) + f"] {int(pct_clamped)}%"  # type: ignore[reportUnusedCoroutine]


def _mini_architecture() -> str:  # type: ignore[reportUnusedCoroutine]
    return (  # type: ignore[reportUnusedCoroutine]
        "<b>🧭 Legion Architecture</b>\n"
        "<pre>"
        "Telegram\n"
        "   │\n"
        "   ▼\n"
        "Aiogram Handlers\n"
        "   │\n"
        "   ├── chat()  → multi-provider LLM routing\n"  # type: ignore[reportUnusedCoroutine]
        "   ├── agent_loop() → computer tools + screenshots\n"  # type: ignore[reportUnusedCoroutine]
        "   ├── orchestrator → multi-agent DAG execution\n"
        "   └── memory/audit → persistence + telemetry\n"
        "</pre>"
    )


async def _build_visual_summary(msg: Message) -> str:  # type: ignore[reportUnusedCoroutine]
    uptime_s = int(time.time() - _start_time)  # type: ignore[reportUnusedCoroutine]
    h, rem = divmod(uptime_s, 3600)  # type: ignore[reportUnusedCoroutine]
    m, s = divmod(rem, 60)  # type: ignore[reportUnusedCoroutine]
    uptime = f"{h}h {m}m {s}s"  # type: ignore[reportUnusedCoroutine]

    lines = [  # type: ignore[reportUnusedCoroutine]
        "<b>📊 Legion Visual Dashboard</b>",  # type: ignore[reportUnusedCoroutine]
        f"⏱ Uptime: <code>{uptime}</code>",  # type: ignore[reportUnusedCoroutine]
        "",  # type: ignore[reportUnusedCoroutine]
        "<b>System Health</b>",  # type: ignore[reportUnusedCoroutine]
    ]

    try:
        from tools.resource_monitor import (
            get_resource_snapshot,  # type: ignore[reportUnusedCoroutine]
        )

        snap = await get_resource_snapshot(force=True)  # type: ignore[reportUnusedCoroutine]
        ram_pct = max(0.0, min(100.0, (1.0 - (snap.ram_free_gb / max(snap.ram_total_gb, 0.1))) * 100.0))  # type: ignore[reportUnusedCoroutine]
        lines.append(f"🧠 RAM usage  {_bar(ram_pct)}")  # type: ignore[reportUnusedCoroutine]
        if snap.vram_total_gb and snap.vram_free_gb is not None:  # type: ignore[reportUnusedCoroutine]
            vram_pct = max(0.0, min(100.0, (1.0 - (snap.vram_free_gb / max(snap.vram_total_gb, 0.1))) * 100.0))  # type: ignore[reportUnusedCoroutine]
            lines.append(f"🎮 VRAM usage {_bar(vram_pct)}")  # type: ignore[reportUnusedCoroutine]
        else:
            lines.append("🎮 VRAM usage [not detected]")  # type: ignore[reportUnusedCoroutine]
        ollama_state = "ready" if snap.local_allowed else f"bypassed ({snap.block_reason[:50]})"  # type: ignore[reportUnusedCoroutine]
        lines.append(f"🤖 Local vision: <code>{html_mod.escape(ollama_state)}</code>")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        lines.append(f"⚠️ resource monitor unavailable: <code>{html_mod.escape(str(e)[:120])}</code>")  # type: ignore[reportUnusedCoroutine]

    lines.extend(["", "<b>Reliability & Throughput (24h)</b>"])  # type: ignore[reportUnusedCoroutine]

    if _shared._audit_logger and msg.from_user:  # type: ignore[reportUnusedCoroutine]
        try:
            summary = await _shared._audit_logger.get_summary(hours=24)  # type: ignore[reportUnusedCoroutine]
            total = int(summary.get("total_events", 0))  # type: ignore[reportUnusedCoroutine]
            success = int(summary.get("success_count", 0))  # type: ignore[reportUnusedCoroutine]
            failure = int(summary.get("failure_count", 0))  # type: ignore[reportUnusedCoroutine]
            pass_rate = (success / total * 100.0) if total else 0.0  # type: ignore[reportUnusedCoroutine]
            fail_rate = (failure / total * 100.0) if total else 0.0  # type: ignore[reportUnusedCoroutine]
            lines.append(f"✅ Pass rate  {_bar(pass_rate)}")  # type: ignore[reportUnusedCoroutine]
            lines.append(f"❌ Fail rate  {_bar(fail_rate)}")  # type: ignore[reportUnusedCoroutine]
            lines.append(f"💸 Cost 24h: <code>${float(summary.get('total_cost_usd', 0.0)):.4f}</code>")  # type: ignore[reportUnusedCoroutine]

            by_agent = summary.get("by_agent", {}) or {}  # type: ignore[reportUnusedCoroutine]
            if by_agent:
                top = sorted(by_agent.items(), key=lambda x: x[1], reverse=True)[:5]  # type: ignore[reportUnusedCoroutine]
                lines.append("")  # type: ignore[reportUnusedCoroutine]
                lines.append("<b>Top Active Agents</b>")  # type: ignore[reportUnusedCoroutine]
                for name, count in top:  # type: ignore[reportUnusedCoroutine]
                    ratio = (count / max(total, 1)) * 100.0  # type: ignore[reportUnusedCoroutine]
                    lines.append(f"• <code>{html_mod.escape(str(name))}</code> {_bar(ratio, width=10)}")  # type: ignore[reportUnusedCoroutine]
        except Exception as e:
            lines.append(f"⚠️ audit summary unavailable: <code>{html_mod.escape(str(e)[:120])}</code>")  # type: ignore[reportUnusedCoroutine]
    else:
        lines.append("ℹ️ Audit logger not initialized yet")  # type: ignore[reportUnusedCoroutine]

    lines.extend(["", "<b>Model Keys</b>", _key_status()])  # type: ignore[reportUnusedCoroutine]
    return "\n".join(lines)  # type: ignore[reportUnusedCoroutine]


@router.message(Command("visualize"))  # type: ignore[reportUnusedCoroutine]
@router.message(Command("viz"))  # type: ignore[reportUnusedCoroutine]
@router.message(F.text == "📊 Visualize")  # type: ignore[reportUnusedCoroutine]
async def cmd_visualize(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return

    status_msg = await msg.answer("📊 building visual dashboard…")  # type: ignore[reportUnusedCoroutine]
    try:
        summary = await _build_visual_summary(msg)  # type: ignore[reportUnusedCoroutine]
        await status_msg.edit_text(summary, parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]

        # Try sending a rich PNG grid if overnight dashboard module has data.  # type: ignore[reportUnusedCoroutine]
        try:
            from tools.dashboard import build_png_dashboard  # type: ignore[reportUnusedCoroutine]
            from tools.overnight import (  # type: ignore[reportUnusedCoroutine]
                AGENT_STATUS,
                get_active_job_id,
                get_job_tasks,
            )

            job_id = get_active_job_id()  # type: ignore[reportUnusedCoroutine]
            job_tasks = get_job_tasks(job_id) if job_id else None  # type: ignore[reportUnusedCoroutine]
            png = await build_png_dashboard(AGENT_STATUS, job_id=job_id, job_tasks=job_tasks)  # type: ignore[reportUnusedCoroutine]
            if png:
                await msg.answer_photo(  # type: ignore[reportUnusedCoroutine]
                    photo=BufferedInputFile(png, filename="legion_dashboard.png"),  # type: ignore[reportUnusedCoroutine]
                    caption="📈 Live agent visualization",  # type: ignore[reportUnusedCoroutine]
                )
        except Exception:
            pass

        await msg.answer(_mini_architecture(), parse_mode="HTML")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
            f"visualization error: <code>{html_mod.escape(str(e)[:400])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


# ── /status ───────────────────────────────────────────────────────────────────
def _feature_flags_block() -> str:  # type: ignore[reportUnusedCoroutine]
    """Build a feature flags display block for /status."""  # type: ignore[reportUnusedCoroutine]
    lines = ["", "<b>🔧 Feature Flags</b>"]  # type: ignore[reportUnusedCoroutine]

    # Planned features (explicit FF flags in codebase)  # type: ignore[reportUnusedCoroutine]
    planned_flags = [  # type: ignore[reportUnusedCoroutine]
        ("FEATURE_GIT_LOG_ANALYSIS_ENABLED", "Git log analysis"),  # type: ignore[reportUnusedCoroutine]
        ("FEATURE_BRIEFING_CONSOLIDATION_ENABLED", "Briefing consolidation"),  # type: ignore[reportUnusedCoroutine]
        ("FEATURE_WEB_SEARCH_ENABLED", "Web search integration"),  # type: ignore[reportUnusedCoroutine]
        ("FEATURE_TOPIC_WEIGHTS_ENABLED", "Topic weights engine"),  # type: ignore[reportUnusedCoroutine]
    ]
    for flag_name, label in planned_flags:  # type: ignore[reportUnusedCoroutine]
        # Check if the flag exists and is True
        import os as _os

        enabled = _os.getenv(flag_name, "").strip().lower() in ("1", "true", "yes", "on")  # type: ignore[reportUnusedCoroutine]
        icon = "✅" if enabled else "🔇"  # type: ignore[reportUnusedCoroutine]
        status = "ON" if enabled else "OFF (v2.0)"  # type: ignore[reportUnusedCoroutine]
        lines.append(f"{icon} <code>{flag_name}</code> — {label} [{status}]")  # type: ignore[reportUnusedCoroutine]

    # Health check flags (conditional dependencies)  # type: ignore[reportUnusedCoroutine]
    lines.append("")  # type: ignore[reportUnusedCoroutine]
    lines.append("<b>📦 Conditional Features</b>")  # type: ignore[reportUnusedCoroutine]
    try:
        from core.health_check import (  # type: ignore[reportUnusedCoroutine]
            FEATURE_FLAGS,
            run_health_check,
        )

        results = run_health_check()  # type: ignore[reportUnusedCoroutine]
        for feat, data in FEATURE_FLAGS.items():  # type: ignore[reportUnusedCoroutine]
            available = data.get("enabled", False)  # type: ignore[reportUnusedCoroutine]
            reason = results.get(feat, {}).get("reason", "OK")  # type: ignore[reportUnusedCoroutine]
            icon = "✅" if available else "⚠️"  # type: ignore[reportUnusedCoroutine]
            lines.append(f"{icon} <code>{feat}</code> — {reason[:40]}")  # type: ignore[reportUnusedCoroutine]
        # Show archived features as 🔇
        from core.health_check import _ARCHIVED_FEATURES  # type: ignore[reportUnusedCoroutine]

        for feat, data in _ARCHIVED_FEATURES.items():  # type: ignore[reportUnusedCoroutine]
            lines.append(f"🔇 <code>{feat}</code> — archived")  # type: ignore[reportUnusedCoroutine]
    except Exception:
        lines.append("⚠️ Could not load feature flags")  # type: ignore[reportUnusedCoroutine]

    # Optional external services
    lines.append("")  # type: ignore[reportUnusedCoroutine]
    lines.append("<b>🔗 External Services</b>")  # type: ignore[reportUnusedCoroutine]
    _has_voicevox = False  # type: ignore[reportUnusedCoroutine]
    try:
        import importlib.util  # type: ignore[reportUnusedCoroutine]

        _has_voicevox = importlib.util.find_spec("voicevox_core") is not None  # type: ignore[reportUnusedCoroutine]
    except Exception:
        pass
    icon_vv = "✅" if _has_voicevox else "⚠️"  # type: ignore[reportUnusedCoroutine]
    vv_status = "loaded" if _has_voicevox else "not installed"  # type: ignore[reportUnusedCoroutine]
    lines.append(f"{icon_vv} <code>VOICEVOX</code> — {vv_status}")  # type: ignore[reportUnusedCoroutine]

    _has_chromadb = False  # type: ignore[reportUnusedCoroutine]
    with contextlib.suppress(Exception):  # type: ignore[reportUnusedCoroutine]

        _has_chromadb = True  # type: ignore[reportUnusedCoroutine]
    icon_cdb = "✅" if _has_chromadb else "⚠️"  # type: ignore[reportUnusedCoroutine]
    cdb_status = "connected" if _has_chromadb else "not connected"  # type: ignore[reportUnusedCoroutine]
    lines.append(f"{icon_cdb} <code>CHROMADB</code> — {cdb_status}")  # type: ignore[reportUnusedCoroutine]

    return "\n".join(lines)  # type: ignore[reportUnusedCoroutine]


@router.message(Command("status"))  # type: ignore[reportUnusedCoroutine]
@router.message(F.text == "\u2699\ufe0f Status")  # type: ignore[reportUnusedCoroutine]
async def cmd_status(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    uptime_s = int(time.time() - _start_time)  # type: ignore[reportUnusedCoroutine]
    h, rem = divmod(uptime_s, 3600)  # type: ignore[reportUnusedCoroutine]
    m, s = divmod(rem, 60)  # type: ignore[reportUnusedCoroutine]
    uptime = f"{h}h {m}m {s}s"  # type: ignore[reportUnusedCoroutine]
    py_ver = platform.python_version()  # type: ignore[reportUnusedCoroutine]
    os_info = f"{platform.system()} {platform.release()}"  # type: ignore[reportUnusedCoroutine]

    key_block = _key_status()  # type: ignore[reportUnusedCoroutine]
    feature_block = _feature_flags_block()  # type: ignore[reportUnusedCoroutine]

    try:
        from tools.resource_monitor import (
            get_resource_snapshot,  # type: ignore[reportUnusedCoroutine]
        )

        snap = await get_resource_snapshot()  # type: ignore[reportUnusedCoroutine]
        local_line = (  # type: ignore[reportUnusedCoroutine]
            "\U0001f916 Ollama: \u2705 ready"
            if snap.local_allowed  # type: ignore[reportUnusedCoroutine]
            else f"\U0001f916 Ollama: \u26a0\ufe0f bypassed ({snap.block_reason[:60]})"  # type: ignore[reportUnusedCoroutine]
        )
        ram_line = f"\U0001f9e0 RAM free: {snap.ram_free_gb:.1f}GB"  # type: ignore[reportUnusedCoroutine]
        gpu_line = (  # type: ignore[reportUnusedCoroutine]
            f"\U0001f3ae VRAM free: {snap.vram_free_gb:.1f}GB"  # type: ignore[reportUnusedCoroutine]
            if snap.vram_free_gb is not None  # type: ignore[reportUnusedCoroutine]
            else "\U0001f3ae GPU: not detected"
        )
        resource_block = f"\n{ram_line}\n{gpu_line}\n{local_line}"  # type: ignore[reportUnusedCoroutine]
    except Exception:
        resource_block = ""  # type: ignore[reportUnusedCoroutine]

    text = (  # type: ignore[reportUnusedCoroutine]
        f"<b>\U0001f916 Legion Status</b>\n\n"
        f"\u23f1 uptime: <code>{uptime}</code>\n"
        f"\U0001f40d Python: <code>{py_ver}</code>\n"
        f"\U0001f4bb OS: <code>{os_info}</code>\n"
        f"{resource_block}\n\n"
        f"{key_block}\n\n"
        f"{feature_block}"
    )
    await msg.answer(text, parse_mode="HTML")  # type: ignore[reportUnusedCoroutine]


@router.message(Command("stats"))  # type: ignore[reportUnusedCoroutine]
async def cmd_stats(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    status_msg = await msg.answer("\U0001f4ca building stats\u2026")  # type: ignore[reportUnusedCoroutine]
    try:
        lines = ["<b>📊 Performance Metrics</b>", ""]  # type: ignore[reportUnusedCoroutine]

        # ── LLM latency percentiles ──────────────────────────────────────────
        try:
            from core.observability import (
                get_metrics_snapshot,  # type: ignore[reportUnusedCoroutine]
            )

            data = get_metrics_snapshot()  # type: ignore[reportUnusedCoroutine]
            if data:
                all_latencies: list[float] = []  # type: ignore[reportUnusedCoroutine]
                for provider, stats in data.items():  # type: ignore[reportUnusedCoroutine]
                    calls = int(stats.get("calls", 0))  # type: ignore[reportUnusedCoroutine]
                    total_lat = float(stats.get("latency_ms", 0.0))  # type: ignore[reportUnusedCoroutine]
                    tokens = int(stats.get("tokens", 0))  # type: ignore[reportUnusedCoroutine]
                    errors = int(stats.get("errors", 0))  # type: ignore[reportUnusedCoroutine]
                    avg = total_lat / calls if calls else 0.0  # type: ignore[reportUnusedCoroutine]
                    all_latencies.append(avg)  # type: ignore[reportUnusedCoroutine]
                    lines.append(  # type: ignore[reportUnusedCoroutine]
                        f"• <b>{provider}</b>: calls={calls}, tokens={tokens}, avg={avg:.0f}ms, errors={errors}"  # type: ignore[reportUnusedCoroutine]
                    )
                if all_latencies:
                    sorted_lat = sorted(all_latencies)  # type: ignore[reportUnusedCoroutine]
                    p50 = sorted_lat[len(sorted_lat) // 2]  # type: ignore[reportUnusedCoroutine]
                    p95_idx = min(len(sorted_lat) - 1, int(len(sorted_lat) * 0.95))  # type: ignore[reportUnusedCoroutine]
                    p99_idx = min(len(sorted_lat) - 1, int(len(sorted_lat) * 0.99))  # type: ignore[reportUnusedCoroutine]
                    lines.append("")  # type: ignore[reportUnusedCoroutine]
                    lines.append(  # type: ignore[reportUnusedCoroutine]
                        f"LLM latency percentiles: p50=<b>{p50:.0f}ms</b>, "  # type: ignore[reportUnusedCoroutine]
                        f"p95=<b>{sorted_lat[p95_idx]:.0f}ms</b>, "  # type: ignore[reportUnusedCoroutine]
                        f"p99=<b>{sorted_lat[p99_idx]:.0f}ms</b>"  # type: ignore[reportUnusedCoroutine]
                    )
            else:
                lines.append("No LLM metrics yet.")  # type: ignore[reportUnusedCoroutine]
        except Exception as e:
            lines.append(f"⚠️ LLM metrics error: <code>{html_mod.escape(str(e)[:100])}</code>")  # type: ignore[reportUnusedCoroutine]

        # ── Token usage per session ────────────────────────────────────────────
        try:
            from core.observability import (
                get_session_token_stats,  # type: ignore[reportUnusedCoroutine]
            )

            token_stats = get_session_token_stats(str(msg.from_user.id if msg.from_user else 0))  # type: ignore[reportUnusedCoroutine]
            if token_stats:
                lines.append("")  # type: ignore[reportUnusedCoroutine]
                lines.append(  # type: ignore[reportUnusedCoroutine]
                    f"Token usage (session): in=<b>{token_stats.get('prompt_tokens', 0)}</b> "  # type: ignore[reportUnusedCoroutine]
                    f"out=<b>{token_stats.get('completion_tokens', 0)}</b> "  # type: ignore[reportUnusedCoroutine]
                    f"total=<b>{token_stats.get('total_tokens', 0)}</b>"  # type: ignore[reportUnusedCoroutine]
                )
            else:
                lines.append("No token stats yet for this session.")  # type: ignore[reportUnusedCoroutine]
        except Exception:
            pass

        # ── Circuit breaker state ─────────────────────────────────────────────
        try:
            from core.circuit_breaker import (
                get_circuit_breakers,  # type: ignore[reportUnusedCoroutine]
            )

            cbs = get_circuit_breakers()  # type: ignore[reportUnusedCoroutine]
            if cbs:
                lines.append("")  # type: ignore[reportUnusedCoroutine]
                lines.append("<b>Circuit Breakers</b>")  # type: ignore[reportUnusedCoroutine]
                for name, cb in cbs.items():  # type: ignore[reportUnusedCoroutine]
                    lines.append(f"• <b>{name}</b>: <code>{cb.state.value}</code> (failures={cb._failure_count})")  # type: ignore[reportUnusedCoroutine]
        except Exception as e:
            lines.append(f"⚠️ circuit breaker error: <code>{html_mod.escape(str(e)[:100])}</code>")  # type: ignore[reportUnusedCoroutine]

        # ── Memory tier counts ────────────────────────────────────────────────
        try:
            from core.memory_engine import MemoryEngine  # type: ignore[reportUnusedCoroutine]

            me = MemoryEngine()  # type: ignore[reportUnusedCoroutine]
            stats = me.get_stats()  # type: ignore[reportUnusedCoroutine]
            wm = stats.get("working", {})  # type: ignore[reportUnusedCoroutine]
            lines.append("")  # type: ignore[reportUnusedCoroutine]
            lines.append("<b>Memory Tiers</b>")  # type: ignore[reportUnusedCoroutine]
            lines.append(  # type: ignore[reportUnusedCoroutine]
                f"• Working: buffer=<b>{wm.get('buffer_size', 0)}</b>, "  # type: ignore[reportUnusedCoroutine]
                f"tokens=<b>{wm.get('total_tokens', 0)}</b>, "  # type: ignore[reportUnusedCoroutine]
                f"summary=<b>{'yes' if wm.get('has_summary') else 'no'}</b>"  # type: ignore[reportUnusedCoroutine]
            )
            em = stats.get("episodic", {})  # type: ignore[reportUnusedCoroutine]
            lines.append(f"• Episodic: db=<b>{'yes' if em.get('db_exists') else 'no'}</b>")  # type: ignore[reportUnusedCoroutine]
            pm = stats.get("permanent", {})  # type: ignore[reportUnusedCoroutine]
            lines.append(  # type: ignore[reportUnusedCoroutine]
                f"• Permanent: collection=<b>{pm.get('collection', '?')}</b>, docs~<b>{pm.get('approx_count', 0)}</b>"  # type: ignore[reportUnusedCoroutine]
            )
        except Exception as e:
            lines.append(f"⚠️ memory stats error: <code>{html_mod.escape(str(e)[:100])}</code>")  # type: ignore[reportUnusedCoroutine]

        await status_msg.edit_text("\n".join(lines), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
    except Exception as e:
        await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
            f"stats error: <code>{html_mod.escape(str(e)[:350])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


# ── /gpu ──────────────────────────────────────────────────────────────────────
@router.message(Command("gpu"))  # type: ignore[reportUnusedCoroutine]
async def cmd_gpu(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    status_msg = await msg.answer("\U0001f3ae checking GPU\u2026")  # type: ignore[reportUnusedCoroutine]
    try:
        from tools.resource_monitor import (  # type: ignore[reportUnusedCoroutine]
            format_resource_html,
            get_resource_snapshot,
        )

        snap = await get_resource_snapshot(force=True)  # type: ignore[reportUnusedCoroutine]
        await status_msg.edit_text(format_resource_html(snap), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
    except Exception:
        # Fallback to raw nvidia-smi
        try:
            from llm_client import run_shell_command

            out = await run_shell_command("nvidia-smi", timeout=10)  # type: ignore[reportUnusedCoroutine]
            await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
                f"<pre>{html_mod.escape(out[:3000])}</pre>",  # type: ignore[reportUnusedCoroutine]
                parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
            )
        except Exception as e2:
            await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
                f"GPU info unavailable: <code>{html_mod.escape(str(e2))}</code>",  # type: ignore[reportUnusedCoroutine]
                parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
            )


# ── /keys ──────────────────────────────────────────────────────────────────────
@router.message(Command("keys"))  # type: ignore[reportUnusedCoroutine]
async def cmd_keys(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    await msg.answer(_key_status(), parse_mode="HTML")  # type: ignore[reportUnusedCoroutine]


# ── /models ────────────────────────────────────────────────────────────────────
@router.message(Command("models"))  # type: ignore[reportUnusedCoroutine]
async def cmd_models(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    import os

    import router as agents

    registry = getattr(agents, "AGENT_REGISTRY", {}) or {}  # type: ignore[reportUnusedCoroutine]
    if not registry:
        await msg.answer(agents.list_agents(), parse_mode="HTML")  # type: ignore[reportUnusedCoroutine]
        return

    lines = ["<b>🤖 Agent Registry (v5)</b>"]  # type: ignore[reportUnusedCoroutine]
    for key, meta in registry.items():  # type: ignore[reportUnusedCoroutine]
        required = getattr(meta, "requires_env", None)  # type: ignore[reportUnusedCoroutine]
        status = "active"  # type: ignore[reportUnusedCoroutine]
        if required and not os.getenv(required):  # type: ignore[reportUnusedCoroutine]
            status = "unavailable"  # type: ignore[reportUnusedCoroutine]
        lines.append(  # type: ignore[reportUnusedCoroutine]
            f"• <code>{html_mod.escape(key)}</code> — {html_mod.escape(meta.model)} "  # type: ignore[reportUnusedCoroutine]
            f"(<i>{html_mod.escape(meta.sdk)}</i>) [{status}]"  # type: ignore[reportUnusedCoroutine]
        )
    await msg.answer("\n".join(lines), parse_mode="HTML")  # type: ignore[reportUnusedCoroutine]


@router.message(Command("metrics"))  # type: ignore[reportUnusedCoroutine]
async def cmd_metrics(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    try:
        from core.observability import render_metrics_html  # type: ignore[reportUnusedCoroutine]

        await msg.answer(render_metrics_html(), parse_mode="HTML")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        await msg.answer(f"metrics unavailable: <code>{html_mod.escape(str(e)[:250])}</code>", parse_mode="HTML")  # type: ignore[reportUnusedCoroutine]


@router.message(Command("ping"))  # type: ignore[reportUnusedCoroutine]
async def cmd_ping(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    await msg.answer("🏓 Pong! Legion is alive.")  # type: ignore[reportUnusedCoroutine]


# ── /resources — live RAM + GPU + local model policy ──────────────────────────
@router.message(Command("resources"))  # type: ignore[reportUnusedCoroutine]
async def cmd_resources(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    """Show live RAM, GPU VRAM, and whether local Ollama is currently allowed."""  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    status_msg = await msg.answer("\U0001f4ca reading system resources\u2026")  # type: ignore[reportUnusedCoroutine]
    try:
        from tools.resource_monitor import (  # type: ignore[reportUnusedCoroutine]
            format_resource_html,
            get_resource_snapshot,
        )

        # force=True to bypass cache and get a fresh reading  # type: ignore[reportUnusedCoroutine]
        snap = await get_resource_snapshot(force=True)  # type: ignore[reportUnusedCoroutine]
        await status_msg.edit_text(format_resource_html(snap), parse_mode="HTML")  # type: ignore[reportOptionalMemberAccess]
    except Exception as e:
        await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
            f"\u274c resource monitor error:\n<code>{html_mod.escape(str(e)[:400])}</code>\n\n"  # type: ignore[reportUnusedCoroutine]
            "Make sure <code>psutil</code> is installed: "
            "<code>pip install psutil pynvml</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


@router.message(Command("capability_stats"))  # type: ignore[reportUnusedCoroutine]
@router.message(Command("cap_stats"))  # type: ignore[reportUnusedCoroutine]
async def cmd_capability_stats(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    """Show rolling capability leaderboard from recent runs."""  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return

    status_msg = await msg.answer("🏁 building capability leaderboard…")  # type: ignore[reportUnusedCoroutine]
    try:
        from tools.capability_metrics import (
            render_capability_summary_html,  # type: ignore[reportUnusedCoroutine]
        )

        text = render_capability_summary_html(hours=72)  # type: ignore[reportUnusedCoroutine]
        await status_msg.delete()  # type: ignore[reportUnusedCoroutine]
        await send_chunked(msg, text, model_used="capability-metrics")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
            f"capability stats unavailable: <code>{html_mod.escape(str(e)[:350])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


@router.message(Command("benchmark"))  # type: ignore[reportUnusedCoroutine]
async def cmd_benchmark(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    """Run capability benchmark suite now."""  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    status_msg = await msg.answer("🏁 running capability benchmark suite…")  # type: ignore[reportUnusedCoroutine]
    try:
        from tools.capability_benchmark import (  # type: ignore[reportUnusedCoroutine]
            render_suite_report_html,
            run_capability_suite,
        )

        report = await run_capability_suite(  # type: ignore[reportUnusedCoroutine]
            user_id=str(msg.from_user.id) if msg.from_user else "0",  # type: ignore[reportUnusedCoroutine]
            include_redteam=False,  # type: ignore[reportUnusedCoroutine]
        )
        text = render_suite_report_html(report, title="Capability Benchmark")  # type: ignore[reportUnusedCoroutine]
        await status_msg.delete()  # type: ignore[reportUnusedCoroutine]
        await send_chunked(msg, text, model_used="capability-benchmark")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
            f"benchmark failed: <code>{html_mod.escape(str(e)[:350])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


@router.message(Command("compact"))  # type: ignore[reportUnusedCoroutine]
async def cmd_compact(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    """Manually compact conversation history to free context space."""  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    try:
        from core.conversation_interface import (  # type: ignore[reportUnusedCoroutine]
            add_to_conversation,  # type: ignore[reportUnusedCoroutine]
            clear_conversation,  # type: ignore[reportUnusedCoroutine]
            get_conversation_history,  # type: ignore[reportUnusedCoroutine]
        )
        from llm_client import _compact_messages

        user_id = str(msg.from_user.id) if msg.from_user else "0"  # type: ignore[reportUnusedCoroutine]
        history = get_conversation_history(user_id, last_n=100)  # type: ignore[reportUnusedCoroutine]
        original = len(history)  # type: ignore[reportUnusedCoroutine]
        if original < 10:
            await msg.answer("Conversation is already short — no compaction needed.")  # type: ignore[reportUnusedCoroutine]
            return

        try:
            from core.hooks import get_hooks  # type: ignore[reportUnusedCoroutine]

            get_hooks().emit("pre_compact", {  # type: ignore[reportUnusedCoroutine]
                "user_id": user_id,  # type: ignore[reportUnusedCoroutine]
                "messages": list(history),  # type: ignore[reportUnusedCoroutine]
            })
        except Exception:
            pass

        compacted = _compact_messages(history, keep_recent=6)  # type: ignore[reportUnusedCoroutine]
        clear_conversation(user_id)  # type: ignore[reportUnusedCoroutine]
        for m in compacted[1:]:
            role = m.get("role", "user")  # type: ignore[reportUnusedCoroutine]
            content = m.get("content", "")  # type: ignore[reportUnusedCoroutine]
            if role in ("user", "assistant") and content:  # type: ignore[reportUnusedCoroutine]
                add_to_conversation(user_id, role, content)  # type: ignore[reportUnusedCoroutine]

        try:
            from core.hooks import get_hooks  # type: ignore[reportUnusedCoroutine]
            get_hooks().emit("post_compact", {  # type: ignore[reportUnusedCoroutine]
                "user_id": user_id,  # type: ignore[reportUnusedCoroutine]
                "original_count": original,  # type: ignore[reportUnusedCoroutine]
                "compacted_count": len(compacted),  # type: ignore[reportUnusedCoroutine]
                "reduction": original - len(compacted),  # type: ignore[reportUnusedCoroutine]
            })
        except Exception:
            pass
        await msg.answer(  # type: ignore[reportUnusedCoroutine]
            f"✅ Compacted {original} → {len(compacted)} messages. "  # type: ignore[reportUnusedCoroutine]
            f"Reduced by {original - len(compacted)} turns.",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )
    except Exception as e:
        await msg.answer(  # type: ignore[reportUnusedCoroutine]
            f"❌ Compaction failed: <code>{html_mod.escape(str(e)[:200])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


@router.message(Command("snapshot"))  # type: ignore[reportUnusedCoroutine]
async def cmd_snapshot(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    """Save a named snapshot of current conversation to wiki. GAP-17."""  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    label = (msg.text or "").removeprefix("/snapshot").strip() or "manual snapshot"  # type: ignore[reportUnusedCoroutine]
    user_id = str(msg.from_user.id) if msg.from_user else "0"  # type: ignore[reportUnusedCoroutine]

    try:
        import html_mod  # type: ignore[reportMissingImports]

        from core.session_snapshots import create_snapshot  # type: ignore[reportUnusedCoroutine]

        snapshot_id = await create_snapshot(user_id, label=label)  # type: ignore[reportUnusedCoroutine]
        await msg.answer(  # type: ignore[reportUnusedCoroutine]
            f"📸 Snapshot saved: <code>{html_mod.escape(snapshot_id)}</code>\n"  # type: ignore[reportUnusedCoroutine]
            f"Label: {html_mod.escape(label)}\n"  # type: ignore[reportUnusedCoroutine]
            f"Restored with: /restore {snapshot_id}",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )
    except Exception as e:
        await msg.answer(  # type: ignore[reportUnusedCoroutine]
            f"❌ Snapshot failed: <code>{html_mod.escape(str(e)[:200])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


@router.message(Command("restore"))  # type: ignore[reportUnusedCoroutine]
async def cmd_restore(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    """Restore a conversation from a wiki snapshot. GAP-17."""  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    parts = (msg.text or "").removeprefix("/restore").strip().split()  # type: ignore[reportUnusedCoroutine]
    snapshot_id = parts[0] if parts else ""  # type: ignore[reportUnusedCoroutine]
    if not snapshot_id:
        await msg.answer("Usage: /restore <snapshot_id>")  # type: ignore[reportUnusedCoroutine]
        return

    user_id = str(msg.from_user.id) if msg.from_user else "0"  # type: ignore[reportUnusedCoroutine]
    try:
        from core.session_snapshots import restore_snapshot  # type: ignore[reportUnusedCoroutine]

        success = await restore_snapshot(snapshot_id, user_id)  # type: ignore[reportUnusedCoroutine]
        if success:
            await msg.answer(f"✅ Restored snapshot <code>{html_mod.escape(snapshot_id)}</code>")  # type: ignore[reportUnusedCoroutine]
        else:
            await msg.answer("❌ Could not restore snapshot — not found or error")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        await msg.answer(  # type: ignore[reportUnusedCoroutine]
            f"❌ Restore failed: <code>{html_mod.escape(str(e)[:200])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


@router.message(Command("snapshots"))  # type: ignore[reportUnusedCoroutine]
async def cmd_snapshots(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    """List all available session snapshots. GAP-17."""  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    try:
        import html_mod  # type: ignore[reportMissingImports]

        from core.session_snapshots import list_snapshots  # type: ignore[reportUnusedCoroutine]

        snaps = list_snapshots()  # type: ignore[reportUnusedCoroutine]
        if not snaps:
            await msg.answer("No snapshots available.")  # type: ignore[reportUnusedCoroutine]
            return

        lines = ["📸 Available snapshots:"]  # type: ignore[reportUnusedCoroutine]
        for s in snaps[:10]:
            fid = html_mod.escape(s["snapshot_id"])  # type: ignore[reportUnusedCoroutine]
            mod = html_mod.escape(s.get("modified", ""))  # type: ignore[reportUnusedCoroutine]
            lines.append(f"- <code>{fid}</code> ({mod})")  # type: ignore[reportUnusedCoroutine]

        await msg.answer("\n".join(lines), parse_mode="HTML")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        await msg.answer(  # type: ignore[reportUnusedCoroutine]
            f"❌ List failed: <code>{html_mod.escape(str(e)[:200])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )


@router.message(Command("redteam"))  # type: ignore[reportUnusedCoroutine]
@router.message(Command("capability_redteam"))  # type: ignore[reportUnusedCoroutine]
async def cmd_redteam(msg: Message) -> None:  # type: ignore[reportUnusedCoroutine]
    """Run red-team stress suite now."""  # type: ignore[reportUnusedCoroutine]
    if not is_allowed(msg):  # type: ignore[reportUnusedCoroutine]
        return
    status_msg = await msg.answer("🛡 running red-team capability regression…")  # type: ignore[reportUnusedCoroutine]
    try:
        from tools.capability_benchmark import (  # type: ignore[reportUnusedCoroutine]
            render_suite_report_html,
            run_capability_suite,
        )

        report = await run_capability_suite(  # type: ignore[reportUnusedCoroutine]
            user_id=str(msg.from_user.id) if msg.from_user else "0",  # type: ignore[reportUnusedCoroutine]
            include_redteam=True,  # type: ignore[reportUnusedCoroutine]
        )
        text = render_suite_report_html(report, title="Capability Red-Team")  # type: ignore[reportUnusedCoroutine]
        await status_msg.delete()  # type: ignore[reportUnusedCoroutine]
        await send_chunked(msg, text, model_used="capability-redteam")  # type: ignore[reportUnusedCoroutine]
    except Exception as e:
        await status_msg.edit_text(  # type: ignore[reportOptionalMemberAccess]
            f"red-team failed: <code>{html_mod.escape(str(e)[:350])}</code>",  # type: ignore[reportUnusedCoroutine]
            parse_mode="HTML",  # type: ignore[reportUnusedCoroutine]
        )
