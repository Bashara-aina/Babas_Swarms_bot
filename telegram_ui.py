# /home/newadmin/swarm-bot/telegram_ui.py
"""Rich UI components for Telegram bot interface."""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional


class TelegramUI:
    """Rich interactive UI components for LegionSwarm bot."""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Show main menu with quick actions."""
        builder = InlineKeyboardBuilder()
        builder.button(text="💻 Code", callback_data="quick_coding")
        builder.button(text="🐛 Debug", callback_data="quick_debug")
        builder.button(text="📊 Analyze", callback_data="quick_analyze")
        builder.button(text="💡 Explain", callback_data="quick_explain")
        builder.button(text="🔢 Math", callback_data="quick_math")
        builder.button(text="🏗️ Design", callback_data="quick_architect")
        builder.button(text="📌 Threads", callback_data="show_threads")
        builder.button(text="⚙️ Settings", callback_data="settings")
        builder.adjust(2, 2, 2, 2)  # 2 buttons per row
        return builder.as_markup()
    
    @staticmethod
    def thread_selector(threads: List[str], current_thread: Optional[str] = None) -> InlineKeyboardMarkup:
        """Dynamic thread selection menu."""
        builder = InlineKeyboardBuilder()
        
        if not threads:
            builder.button(text="No threads yet", callback_data="noop")
        else:
            for thread in threads[:10]:  # Limit to 10 recent threads
                # Mark current thread
                prefix = "📍 " if thread == current_thread else "📌 "
                builder.button(
                    text=f"{prefix}{thread}",
                    callback_data=f"thread_switch:{thread}"
                )
        
        builder.button(text="➕ New Thread", callback_data="thread_new")
        builder.button(text="⬅️ Back", callback_data="main_menu")
        builder.adjust(1)  # 1 button per row
        return builder.as_markup()
    
    @staticmethod
    def agent_selector() -> InlineKeyboardMarkup:
        """Force agent selection."""
        builder = InlineKeyboardBuilder()
        agents = [
            ("👁️ Vision", "agent_vision"),
            ("💻 Coding", "agent_coding"),
            ("🐛 Debug", "agent_debug"),
            ("🔢 Math", "agent_math"),
            ("🏗️ Architect", "agent_architect"),
            ("👨‍🏫 Mentor", "agent_mentor"),
            ("📈 Analyst", "agent_analyst")
        ]
        for label, callback in agents:
            builder.button(text=label, callback_data=callback)
        builder.button(text="⬅️ Back", callback_data="main_menu")
        builder.adjust(2, 2, 2, 2, 1)
        return builder.as_markup()
    
    @staticmethod
    def confirmation_buttons(action: str, action_id: str = "") -> InlineKeyboardMarkup:
        """Confirm destructive actions."""
        builder = InlineKeyboardBuilder()
        callback_suffix = f":{action_id}" if action_id else ""
        builder.button(text="✅ Confirm", callback_data=f"confirm_yes:{action}{callback_suffix}")
        builder.button(text="❌ Cancel", callback_data=f"confirm_no:{action}{callback_suffix}")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def task_controls(task_id: str) -> InlineKeyboardMarkup:
        """Show task control buttons (pause/cancel)."""
        builder = InlineKeyboardBuilder()
        builder.button(text="⏸️ Pause", callback_data=f"pause:{task_id}")
        builder.button(text="🛑 Cancel", callback_data=f"cancel:{task_id}")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def file_actions(file_id: str) -> InlineKeyboardMarkup:
        """Actions for uploaded files."""
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Summarize", callback_data=f"doc_summarize:{file_id}")
        builder.button(text="❓ Q&A", callback_data=f"doc_qa:{file_id}")
        builder.button(text="📊 Extract Data", callback_data=f"doc_extract:{file_id}")
        builder.button(text="💻 Analyze Code", callback_data=f"doc_code:{file_id}")
        builder.adjust(2, 2)
        return builder.as_markup()
    
    @staticmethod
    def settings_menu(user_settings: dict) -> InlineKeyboardMarkup:
        """Settings configuration menu."""
        builder = InlineKeyboardBuilder()
        
        # Voice responses toggle
        voice_status = "On" if user_settings.get("voice_enabled", False) else "Off"
        builder.button(
            text=f"🔊 Voice: {voice_status}",
            callback_data="toggle_voice"
        )
        
        # Auto-analyze toggle
        auto_status = "On" if user_settings.get("auto_analyze", True) else "Off"
        builder.button(
            text=f"📊 Auto-analyze: {auto_status}",
            callback_data="toggle_auto_analyze"
        )
        
        # Streaming toggle
        stream_status = "On" if user_settings.get("streaming", True) else "Off"
        builder.button(
            text=f"📡 Streaming: {stream_status}",
            callback_data="toggle_streaming"
        )
        
        # Notifications
        notif_level = user_settings.get("notifications", "all")
        builder.button(
            text=f"🔔 Notifications: {notif_level.title()}",
            callback_data="cycle_notifications"
        )
        
        # Usage stats
        builder.button(text="📈 Usage Stats", callback_data="show_stats")
        
        # Reset
        builder.button(text="🔄 Reset Settings", callback_data="reset_settings")
        
        builder.button(text="⬅️ Back", callback_data="main_menu")
        builder.adjust(2, 2, 1, 1, 1)
        return builder.as_markup()
    
    @staticmethod
    def agent_list_display() -> InlineKeyboardMarkup:
        """Show all agents with info."""
        builder = InlineKeyboardBuilder()
        builder.button(text="ℹ️ View Models", callback_data="show_models")
        builder.button(text="📊 Performance", callback_data="show_performance")
        builder.button(text="⬅️ Back", callback_data="main_menu")
        builder.adjust(2, 1)
        return builder.as_markup()
    
    @staticmethod
    def quick_reply_keyboard() -> ReplyKeyboardMarkup:
        """Persistent keyboard for power users."""
        keyboard = [
            [KeyboardButton(text="🐛 Debug"), KeyboardButton(text="💻 Code")],
            [KeyboardButton(text="📊 Analyze"), KeyboardButton(text="💡 Explain")],
            [KeyboardButton(text="📌 Threads"), KeyboardButton(text="⚙️ Menu")]
        ]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            persistent=True,
            input_field_placeholder="Type your request or use buttons..."
        )
    
    @staticmethod
    def hide_keyboard() -> ReplyKeyboardMarkup:
        """Remove keyboard."""
        return ReplyKeyboardMarkup(
            keyboard=[],
            resize_keyboard=True,
            remove_keyboard=True
        )
    
    @staticmethod
    def progress_indicator(step: int, total: int, description: str) -> str:
        """Render progress bar text."""
        filled = int((step / total) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        percentage = int((step / total) * 100)
        return f"[{bar}] {percentage}%\n\n<b>Step {step}/{total}:</b> {description}"
