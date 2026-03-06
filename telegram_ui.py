# /home/newadmin/swarm-bot/telegram_ui.py
"""Rich UI components for Telegram bot - buttons, keyboards, menus."""

from __future__ import annotations
from typing import List

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import agents


class TelegramUI:
    """Interactive UI components for production-grade bot experience."""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main menu with quick actions."""
        builder = InlineKeyboardBuilder()
        builder.button(text="🔧 Debug Code", callback_data="quick_debug")
        builder.button(text="💻 Write Code", callback_data="quick_code")
        builder.button(text="📊 Analyze Data", callback_data="quick_analyze")
        builder.button(text="💡 Explain", callback_data="quick_explain")
        builder.button(text="🖥️ Desktop", callback_data="quick_desktop")
        builder.button(text="📌 Threads", callback_data="show_threads")
        builder.button(text="📈 Stats", callback_data="show_stats")
        builder.button(text="⚙️ Settings", callback_data="settings")
        builder.adjust(2, 2, 2, 2)  # 2 buttons per row
        return builder.as_markup()

    @staticmethod
    def thread_selector(threads: List[str]) -> InlineKeyboardMarkup:
        """Dynamic thread selection menu."""
        builder = InlineKeyboardBuilder()
        for thread in threads[:10]:  # Limit to 10
            builder.button(
                text=f"📌 {thread}", callback_data=f"thread_switch:{thread}"
            )
        builder.button(text="➕ New Thread", callback_data="thread_new")
        builder.button(text="⬅️ Back", callback_data="main_menu")
        builder.adjust(1)  # 1 button per row
        return builder.as_markup()

    @staticmethod
    def agent_selector() -> InlineKeyboardMarkup:
        """Force agent selection menu."""
        builder = InlineKeyboardBuilder()
        agent_icons = {
            "vision": "👁️",
            "coding": "💻",
            "debug": "🐛",
            "math": "🔢",
            "architect": "🏗️",
            "mentor": "👨‍🏫",
            "analyst": "📈",
        }
        for agent_key in agents.AGENT_MODELS.keys():
            icon = agent_icons.get(agent_key, "🤖")
            builder.button(
                text=f"{icon} {agent_key.title()}",
                callback_data=f"agent_force:{agent_key}",
            )
        builder.button(text="⬅️ Back", callback_data="main_menu")
        builder.adjust(2, 2, 2, 2)  # 2 per row
        return builder.as_markup()

    @staticmethod
    def confirmation_buttons(action_id: str) -> InlineKeyboardMarkup:
        """Confirm destructive actions."""
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Confirm", callback_data=f"confirm_yes:{action_id}")
        builder.button(text="❌ Cancel", callback_data=f"confirm_no:{action_id}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def document_actions(file_id: str) -> InlineKeyboardMarkup:
        """Quick actions for uploaded documents."""
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Summarize", callback_data=f"doc_summarize:{file_id}")
        builder.button(
            text="❓ Ask Questions", callback_data=f"doc_qa:{file_id}"
        )
        builder.button(
            text="📊 Extract Data", callback_data=f"doc_extract:{file_id}"
        )
        builder.button(text="🔍 Full Analysis", callback_data=f"doc_analyze:{file_id}")
        builder.adjust(2, 2)
        return builder.as_markup()

    @staticmethod
    def photo_actions(file_id: str) -> InlineKeyboardMarkup:
        """Quick actions for uploaded images."""
        builder = InlineKeyboardBuilder()
        builder.button(text="👁️ Describe", callback_data=f"img_describe:{file_id}")
        builder.button(text="🐛 Debug Code", callback_data=f"img_debug:{file_id}")
        builder.button(text="📝 Extract Text", callback_data=f"img_ocr:{file_id}")
        builder.button(text="🔍 Full Analysis", callback_data=f"img_analyze:{file_id}")
        builder.adjust(2, 2)
        return builder.as_markup()

    @staticmethod
    def task_progress(
        task_id: str, step: int, total: int, can_pause: bool = True
    ) -> InlineKeyboardMarkup:
        """Progress indicator with controls."""
        builder = InlineKeyboardBuilder()
        progress_bar = "█" * step + "░" * (total - step)
        builder.button(
            text=f"{progress_bar} {step}/{total}", callback_data="progress_info"
        )
        if can_pause:
            builder.button(text="⏸️ Pause", callback_data=f"pause:{task_id}")
        builder.button(text="🛑 Cancel", callback_data=f"cancel:{task_id}")
        builder.adjust(1, 2)
        return builder.as_markup()

    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Settings and preferences."""
        builder = InlineKeyboardBuilder()
        builder.button(text="🔊 Voice: Off", callback_data="toggle_voice")
        builder.button(
            text="📊 Auto-analyze: On", callback_data="toggle_auto_analyze"
        )
        builder.button(text="🎨 Theme: Dark", callback_data="change_theme")
        builder.button(text="🔔 Alerts: All", callback_data="change_notifications")
        builder.button(text="⌨️ Keyboard: Off", callback_data="toggle_keyboard")
        builder.button(text="⬅️ Back", callback_data="main_menu")
        builder.adjust(2, 2, 1, 1)
        return builder.as_markup()

    @staticmethod
    def monitor_controls(monitor_id: str) -> InlineKeyboardMarkup:
        """Controls for active monitor."""
        builder = InlineKeyboardBuilder()
        builder.button(text="⏸️ Pause", callback_data=f"monitor_pause:{monitor_id}")
        builder.button(text="🛑 Stop", callback_data=f"monitor_stop:{monitor_id}")
        builder.button(text="📊 Report", callback_data=f"monitor_report:{monitor_id}")
        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def feedback_buttons(response_id: str) -> InlineKeyboardMarkup:
        """Quick feedback for responses."""
        builder = InlineKeyboardBuilder()
        builder.button(text="👍 Good", callback_data=f"feedback_good:{response_id}")
        builder.button(text="👎 Bad", callback_data=f"feedback_bad:{response_id}")
        builder.button(text="💯 Excellent", callback_data=f"feedback_excellent:{response_id}")
        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def power_user_keyboard() -> ReplyKeyboardMarkup:
        """Persistent keyboard for power users."""
        keyboard = [
            [KeyboardButton(text="🐛 Debug"), KeyboardButton(text="💻 Code")],
            [KeyboardButton(text="📊 Analyze"), KeyboardButton(text="💡 Explain")],
            [KeyboardButton(text="🖥️ Desktop"), KeyboardButton(text="📌 Threads")],
            [KeyboardButton(text="📈 Stats"), KeyboardButton(text="⚙️ Settings")],
        ]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            persistent=True,
            input_field_placeholder="Type your question or tap a button...",
        )

    @staticmethod
    def remove_keyboard() -> ReplyKeyboardMarkup:
        """Remove persistent keyboard."""
        return ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True, remove_keyboard=True)
