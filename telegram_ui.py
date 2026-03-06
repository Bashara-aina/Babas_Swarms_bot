# /home/newadmin/swarm-bot/telegram_ui.py
"""Telegram UI components — inline keyboards, quick reply keyboards.

All builders return ready-to-use markup objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

if TYPE_CHECKING:
    pass


class TelegramUI:
    """Factory for all bot UI components."""

    # ── Main Navigation ────────────────────────────────────────────────────────

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Start screen quick-action grid."""
        b = InlineKeyboardBuilder()
        b.button(text="🐛 Debug Code",     callback_data="quick:debug")
        b.button(text="💻 Write Code",     callback_data="quick:code")
        b.button(text="📊 Analyze Data",   callback_data="quick:analyze")
        b.button(text="💡 Explain Concept",callback_data="quick:explain")
        b.button(text="🏗️ Design System",  callback_data="quick:design")
        b.button(text="🖥️ Desktop Status", callback_data="quick:desktop")
        b.button(text="📌 Threads",        callback_data="nav:threads")
        b.button(text="⚙️ Settings",       callback_data="nav:settings")
        b.adjust(2, 2, 2, 2)
        return b.as_markup()

    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        """Single back-to-menu button."""
        b = InlineKeyboardBuilder()
        b.button(text="⬅️ Main Menu", callback_data="nav:main_menu")
        return b.as_markup()

    # ── Agent Selection ────────────────────────────────────────────────────────

    @staticmethod
    def agent_selector(task: str = "") -> InlineKeyboardMarkup:
        """Pick a specific agent for a task.

        Args:
            task: URL-safe task snippet used as callback suffix.
        """
        b = InlineKeyboardBuilder()
        agents = [
            ("👁️ Vision",     "vision"),
            ("💻 Coding",     "coding"),
            ("🐛 Debug",      "debug"),
            ("🔢 Math",       "math"),
            ("🏗️ Architect",  "architect"),
            ("👨‍🏫 Mentor",    "mentor"),
            ("📈 Analyst",    "analyst"),
        ]
        for label, key in agents:
            b.button(text=label, callback_data=f"agent_force:{key}")
        b.button(text="⬅️ Auto-route", callback_data="nav:main_menu")
        b.adjust(2, 2, 2, 1, 1)
        return b.as_markup()

    # ── Thread Management ──────────────────────────────────────────────────────

    @staticmethod
    def thread_selector(threads: list[str]) -> InlineKeyboardMarkup:
        """Show switchable thread list."""
        b = InlineKeyboardBuilder()
        for tid in threads[-8:]:          # Cap at 8 to avoid huge keyboards
            b.button(text=f"📌 {tid[:20]}", callback_data=f"thread_switch:{tid}")
        b.button(text="➕ New Thread",   callback_data="thread_new")
        b.button(text="⬅️ Back",        callback_data="nav:main_menu")
        b.adjust(1)
        return b.as_markup()

    # ── Confirmation ───────────────────────────────────────────────────────────

    @staticmethod
    def confirmation(action_id: str) -> InlineKeyboardMarkup:
        """Yes/No for destructive action confirmation."""
        b = InlineKeyboardBuilder()
        b.button(text="✅ Confirm", callback_data=f"confirm_yes:{action_id}")
        b.button(text="❌ Cancel",  callback_data=f"confirm_no:{action_id}")
        b.adjust(2)
        return b.as_markup()

    # ── Task Progress ──────────────────────────────────────────────────────────

    @staticmethod
    def task_controls(task_id: str) -> InlineKeyboardMarkup:
        """Cancel button shown during long-running tasks."""
        b = InlineKeyboardBuilder()
        b.button(text="🛑 Cancel Task", callback_data=f"task_cancel:{task_id}")
        return b.as_markup()

    # ── Document / File Actions ────────────────────────────────────────────────

    @staticmethod
    def document_actions(file_id: str) -> InlineKeyboardMarkup:
        """Actions to take on an uploaded document."""
        b = InlineKeyboardBuilder()
        b.button(text="📝 Summarize",          callback_data=f"doc:summarize:{file_id}")
        b.button(text="❓ Ask Questions",       callback_data=f"doc:qa:{file_id}")
        b.button(text="📊 Extract Data/Tables", callback_data=f"doc:extract:{file_id}")
        b.button(text="🔍 Full Analysis",       callback_data=f"doc:analyze:{file_id}")
        b.adjust(2, 2)
        return b.as_markup()

    @staticmethod
    def image_actions(file_id: str) -> InlineKeyboardMarkup:
        """Actions on uploaded screenshot/image."""
        b = InlineKeyboardBuilder()
        b.button(text="🔍 Describe",     callback_data=f"img:describe:{file_id}")
        b.button(text="🐛 Find Errors",  callback_data=f"img:errors:{file_id}")
        b.button(text="📋 Extract Text", callback_data=f"img:ocr:{file_id}")
        b.button(text="💡 Suggest Fix",  callback_data=f"img:fix:{file_id}")
        b.adjust(2, 2)
        return b.as_markup()

    # ── Feedback ───────────────────────────────────────────────────────────────

    @staticmethod
    def feedback_buttons(fid: str) -> InlineKeyboardMarkup:
        """Thumbs up/down after every agent response."""
        b = InlineKeyboardBuilder()
        b.button(text="👍 Good",  callback_data=f"fb:good:{fid}")
        b.button(text="👎 Bad",   callback_data=f"fb:bad:{fid}")
        b.adjust(2)
        return b.as_markup()

    # ── Settings ───────────────────────────────────────────────────────────────

    @staticmethod
    def settings_menu(prefs: dict) -> InlineKeyboardMarkup:
        """Toggleable preferences panel."""
        stream_icon  = "🟢" if prefs.get("streaming", True)    else "⚫"
        context_icon = "🟢" if prefs.get("show_context", True) else "⚫"
        notify_icon  = "🟢" if prefs.get("notifications", True) else "⚫"
        b = InlineKeyboardBuilder()
        b.button(text=f"{stream_icon} Streaming: {'On' if prefs.get('streaming', True) else 'Off'}",
                 callback_data="setting:toggle:streaming")
        b.button(text=f"{context_icon} Thread context: {'Shown' if prefs.get('show_context', True) else 'Hidden'}",
                 callback_data="setting:toggle:show_context")
        b.button(text=f"{notify_icon} Notifications: {'On' if prefs.get('notifications', True) else 'Off'}",
                 callback_data="setting:toggle:notifications")
        b.button(text="⬅️ Back", callback_data="nav:main_menu")
        b.adjust(1)
        return b.as_markup()

    # ── Quick Reply Keyboard (persistent) ─────────────────────────────────────

    @staticmethod
    def quick_reply_keyboard() -> ReplyKeyboardMarkup:
        """Persistent bottom keyboard for power users."""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🐛 Debug"), KeyboardButton(text="💻 Code")],
                [KeyboardButton(text="📊 Analyze"), KeyboardButton(text="💡 Explain")],
                [KeyboardButton(text="📌 Threads"), KeyboardButton(text="⚙️ Settings")],
            ],
            resize_keyboard=True,
            is_persistent=True,
            input_field_placeholder="Ask me anything…",
        )
