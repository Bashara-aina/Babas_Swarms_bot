"""handlers/shortcuts.py — /shortcuts command showing all keyboard shortcuts."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from handlers.shared import is_allowed

router = Router()


def get_shortcuts_text() -> str:
    """Standalone text for shortcuts (used by onboarding + /shortcuts command)."""
    return (
        "<b>💡 Legion Shortcuts</b>\n\n"
        "<b>Quick Tasks</b>\n"
        "• <code>/run &lt;task&gt;</code> — chat-only response\n"
        "• <code>/do &lt;task&gt;</code> — computer agent (clicks + terminal)\n"
        "• <code>/swarm &lt;task&gt;</code> — multi-agent team\n"
        "• <code>/think &lt;prompt&gt;</code> — reasoning chain\n\n"
        "<b>Research & Code</b>\n"
        "• <code>/research &lt;topic&gt;</code> — deep web search\n"
        "• <code>/paper &lt;arXiv ID&gt;</code> — read a paper\n"
        "• <code>/ask_paper &lt;question&gt;</code> — ask about a paper\n"
        "• <code>/code &lt;description&gt;</code> — generate code\n"
        "• <code>/fix &lt;error&gt;</code> — auto-fix an error\n"
        "• <code>/scaffold &lt;framework&gt; &lt;desc&gt;</code> — scaffold a project\n\n"
        "<b>Memory & Identity</b>\n"
        "• <code>/memory</code> — show conversation context\n"
        "• <code>/remember &lt;fact&gt;</code> — teach Legion something\n"
        "• <code>/recall &lt;query&gt;</code> — search memory\n"
        "• <code>/soul</code> — view Legion's identity file (SOUL.md)\n\n"
        "<b>Analysis & Debate</b>\n"
        "• <code>/debate &lt;topic&gt;</code> — debate with evidence\n"
        "• <code>/opinion &lt;thing&gt;</code> — Legion's honest opinion\n"
        "• <code>/analyze &lt;file&gt;</code> — static analysis\n"
        "• <code>/benchmark</code> — capability benchmark\n\n"
        "<b>System & Admin</b>\n"
        "• <code>/start</code> — welcome + control center\n"
        "• <code>/status</code> — bot health + feature flags\n"
        "• <code>/budget</code> — cost tracking dashboard\n"
        "• <code>/keys</code> — API key status\n"
        "• <code>/models</code> — agent → model mapping\n"
        "• <code>/resources</code> — live RAM + GPU usage\n"
        "• <code>/capability_stats</code> — capability leaderboard\n"
        "• <code>/self_report</code> — 24h activity report\n"
        "• <code>/capabilities</code> — honest capability status\n\n"
        "<b>Specialist Commands</b>\n"
        "• <code>/jarvis &lt;goal&gt;</code> — memory + screen → plan\n"
        "• <code>/hermes &lt;task&gt;</code> — delegate to sub-agents\n"
        "• <code>/runbook [id]</code> — maintenance playbooks\n"
        "• <code>/wiki &lt;query&gt;</code> — search project wiki\n"
        "• <code>/emails</code> — email management\n"
        "• <code>/calendar</code> — calendar integration\n"
        "• <code>/db &lt;query&gt;</code> — database explorer\n"
        "• <code>/site_health &lt;url&gt;</code> — check a site\n"
        "• <code>/overnight</code> — run tasks while you sleep\n\n"
        "<b>Reply Buttons (after any response)</b>\n"
        "• 👍 — Feedback: good\n"
        "• 🔄 — Retry with same prompt\n"
        "• ℹ️ — Show model info\n\n"
        "<i>Tip: Use <code>/shortcuts</code> anytime to see this list.</i>"
    )


def shortcuts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔑 API Keys", callback_data="cmd:keys"),
                InlineKeyboardButton(text="💰 Budget", callback_data="cmd:budget"),
            ],
            [
                InlineKeyboardButton(text="🏠 Home", callback_data="ui:home"),
                InlineKeyboardButton(text="📖 Learn More", callback_data="onb:learn"),
            ],
        ]
    )


@router.message(Command("shortcuts"))
async def cmd_shortcuts(msg: Message) -> None:
    if not is_allowed(msg):
        return
    await msg.answer(get_shortcuts_text(), parse_mode="HTML", reply_markup=shortcuts_keyboard())
