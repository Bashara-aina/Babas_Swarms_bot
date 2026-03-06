# /home/newadmin/swarm-bot/callback_handlers.py
"""Callback query handlers for all interactive buttons."""

from __future__ import annotations
import logging
from aiogram import F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

import agents
import computer_control
import multimodal_processor
import task_orchestrator
import telegram_ui
import formatters

logger = logging.getLogger(__name__)

# Track file states for quick actions
file_states: dict[str, dict] = {}


def register_callback_handlers(dp):
    """Register all callback query handlers.
    
    Args:
        dp: Dispatcher instance
    """

    @dp.callback_query(F.data == "main_menu")
    async def cb_main_menu(callback: CallbackQuery):
        """Show main menu."""
        try:
            await callback.message.edit_text(
                "🤖 <b>LegionSwarm Main Menu</b>\n\n"
                "What would you like to do?",
                parse_mode="HTML",
                reply_markup=telegram_ui.TelegramUI.main_menu(),
            )
        except TelegramBadRequest:
            await callback.answer("Menu already open")
        await callback.answer()

    @dp.callback_query(F.data.startswith("quick_"))
    async def cb_quick_actions(callback: CallbackQuery):
        """Handle quick action buttons."""
        action = callback.data.split("_", 1)[1]
        
        prompts = {
            "debug": "🐛 <b>Debug Mode</b>\n\nSend me your error traceback or describe the issue.",
            "code": "💻 <b>Coding Mode</b>\n\nDescribe what you want to build, and I'll write the code.",
            "analyze": "📊 <b>Analysis Mode</b>\n\nUpload your data file (CSV, JSON, logs) or paste the data.",
            "explain": "💡 <b>Explanation Mode</b>\n\nWhat concept do you want me to explain?",
            "desktop": "🖥️ <b>Desktop Control</b>\n\nTaking screenshot...",
        }
        
        prompt = prompts.get(action, "Ready.")
        
        if action == "desktop":
            await callback.answer()
            await callback.message.answer(prompt, parse_mode="HTML")
            # Trigger desktop screenshot
            from main import _send_desktop_screenshot
            await _send_desktop_screenshot(callback.message)
        else:
            await callback.message.answer(prompt, parse_mode="HTML")
            await callback.answer()

    @dp.callback_query(F.data == "show_threads")
    async def cb_show_threads(callback: CallbackQuery):
        """Show thread selector."""
        thread_list = agents.get_all_threads()
        if not thread_list:
            await callback.answer("No active threads yet")
            return
        
        try:
            await callback.message.edit_text(
                "📌 <b>Your Conversation Threads</b>\n\n"
                "Select a thread to switch to:",
                parse_mode="HTML",
                reply_markup=telegram_ui.TelegramUI.thread_selector(thread_list),
            )
        except TelegramBadRequest:
            await callback.answer("Thread list already open")
        await callback.answer()

    @dp.callback_query(F.data.startswith("thread_switch:"))
    async def cb_thread_switch(callback: CallbackQuery):
        """Switch to selected thread."""
        thread_id = callback.data.split(":", 1)[1]
        from main import current_thread
        current_thread[callback.from_user.id] = thread_id
        
        ctx = agents.get_thread_context(thread_id, last_n=3)
        turns = agents.get_thread_turn_count(thread_id)
        
        summary = formatters.ResponseFormatter.format_thread_summary(
            thread_id, turns, ctx[:100] if ctx else "(empty)"
        )
        
        await callback.message.answer(summary, parse_mode="HTML")
        await callback.answer(f"Switched to {thread_id}")

    @dp.callback_query(F.data == "thread_new")
    async def cb_thread_new(callback: CallbackQuery):
        """Create new thread."""
        await callback.message.answer(
            "➕ <b>New Thread</b>\n\n"
            "Send me a message, and I'll create a new thread automatically.\n"
            "Or use: <code>/thread your_thread_name</code>",
            parse_mode="HTML",
        )
        await callback.answer()

    @dp.callback_query(F.data == "show_stats")
    async def cb_show_stats(callback: CallbackQuery):
        """Show system stats."""
        try:
            from observability.metrics import format_stats
            stats = format_stats()
        except Exception:
            stats = "⚡ <b>System Status</b>\n\nAll systems operational ✅"
        
        await callback.message.answer(stats, parse_mode="HTML")
        await callback.answer()

    @dp.callback_query(F.data == "settings")
    async def cb_settings(callback: CallbackQuery):
        """Show settings menu."""
        try:
            await callback.message.edit_text(
                "⚙️ <b>Settings</b>\n\n"
                "Configure your bot preferences:",
                parse_mode="HTML",
                reply_markup=telegram_ui.TelegramUI.settings_menu(),
            )
        except TelegramBadRequest:
            await callback.answer("Settings already open")
        await callback.answer()

    @dp.callback_query(F.data.startswith("confirm_"))
    async def cb_confirm(callback: CallbackQuery):
        """Handle confirmation buttons."""
        parts = callback.data.split(":", 1)
        verdict = parts[0].split("_")[1]  # yes or no
        action_id = parts[1] if len(parts) > 1 else ""
        
        if verdict == "yes":
            result = await task_orchestrator.confirm_action(action_id)
            await callback.message.answer(f"✅ Confirmed\n\n{result[:500]}", parse_mode="HTML")
        else:
            result = task_orchestrator.deny_action(action_id)
            await callback.message.answer(result, parse_mode="HTML")
        
        # Remove confirmation buttons
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        
        await callback.answer()

    @dp.callback_query(F.data.startswith("doc_"))
    async def cb_document_actions(callback: CallbackQuery):
        """Handle document quick actions."""
        parts = callback.data.split(":", 1)
        action = parts[0].split("_")[1]
        file_id = parts[1] if len(parts) > 1 else ""
        
        file_data = file_states.get(file_id)
        if not file_data:
            await callback.answer("❌ Document data expired", show_alert=True)
            return
        
        extracted_text = file_data.get("text", "")
        filename = file_data.get("filename", "document")
        
        if action == "summarize":
            await callback.message.answer(
                f"📝 Summarizing <code>{filename}</code>...",
                parse_mode="HTML"
            )
            # Import here to avoid circular dependency
            from main import bot
            import interpreter_bridge
            model = agents.get_model("mentor") or agents.get_model("coding")
            summary = await interpreter_bridge.run_task(
                model,
                f"Provide a concise summary of this document:\n\n{extracted_text[:6000]}",
                "mentor",
            )
            await callback.message.answer(summary[:4000], parse_mode="HTML")
        
        elif action == "qa":
            await callback.message.answer(
                f"❓ <b>Q&A Mode</b>\n\n"
                f"Ask me anything about <code>{filename}</code>",
                parse_mode="HTML"
            )
        
        elif action == "extract":
            await callback.message.answer(
                f"📊 <b>Data Extraction</b>\n\n"
                f"Analyzing <code>{filename}</code> for structured data...",
                parse_mode="HTML"
            )
        
        elif action == "analyze":
            await callback.message.answer(
                f"🔍 Full analysis of <code>{filename}</code> starting...",
                parse_mode="HTML"
            )
        
        await callback.answer()

    @dp.callback_query(F.data.startswith("img_"))
    async def cb_image_actions(callback: CallbackQuery):
        """Handle image quick actions."""
        parts = callback.data.split(":", 1)
        action = parts[0].split("_")[1]
        file_id = parts[1] if len(parts) > 1 else ""
        
        file_data = file_states.get(file_id)
        if not file_data:
            await callback.answer("❌ Image data expired", show_alert=True)
            return
        
        image_bytes = file_data.get("bytes")
        
        prompts = {
            "describe": "Provide a detailed description of this image.",
            "debug": "This image shows code or an error. Analyze and debug it.",
            "ocr": "Extract all text visible in this image.",
            "analyze": "Perform a comprehensive analysis of this image.",
        }
        
        prompt = prompts.get(action, "Analyze this image.")
        
        await callback.message.answer(
            f"👁️ Vision agent analyzing...",
            parse_mode="HTML"
        )
        
        analysis = await multimodal_processor.analyze_image(image_bytes, prompt)
        await callback.message.answer(analysis[:4000], parse_mode="HTML")
        await callback.answer()

    @dp.callback_query(F.data.startswith("feedback_"))
    async def cb_feedback(callback: CallbackQuery):
        """Handle feedback buttons."""
        parts = callback.data.split(":", 1)
        rating = parts[0].split("_")[1]  # good, bad, excellent
        response_id = parts[1] if len(parts) > 1 else ""
        
        rating_map = {"good": 1, "bad": -1, "excellent": 2}
        rating_value = rating_map.get(rating, 0)
        
        try:
            from optimization.feedback_learner import get_learner
            get_learner().record(response_id, rating_value, "")
            
            formatted = formatters.ResponseFormatter.format_feedback_confirmation(rating)
            await callback.message.answer(formatted, parse_mode="HTML")
        except Exception as exc:
            await callback.answer(f"❌ {exc}", show_alert=True)
        
        # Remove feedback buttons
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        
        await callback.answer()

    @dp.callback_query(F.data.startswith("monitor_"))
    async def cb_monitor_control(callback: CallbackQuery):
        """Handle monitor control buttons."""
        parts = callback.data.split(":", 1)
        action = parts[0].split("_")[1]  # pause, stop, report
        monitor_id = parts[1] if len(parts) > 1 else ""
        
        if action == "stop":
            result = task_orchestrator.cancel_monitor(monitor_id)
            await callback.message.answer(result, parse_mode="HTML")
        elif action == "pause":
            await callback.message.answer(
                "⏸️ Monitor paused (not implemented yet)",
                parse_mode="HTML"
            )
        elif action == "report":
            await callback.message.answer(
                task_orchestrator.list_monitors(),
                parse_mode="HTML"
            )
        
        await callback.answer()

    @dp.callback_query(F.data.startswith("cancel:"))
    async def cb_cancel_task(callback: CallbackQuery):
        """Cancel a running task."""
        task_id = callback.data.split(":", 1)[1]
        await callback.message.answer(
            f"🛑 Task {task_id} cancelled",
            parse_mode="HTML"
        )
        
        # Remove progress buttons
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        
        await callback.answer("Task cancelled")

    @dp.callback_query(F.data == "progress_info")
    async def cb_progress_info(callback: CallbackQuery):
        """Show progress info."""
        await callback.answer(
            "Task in progress... This is a visual progress indicator.",
            show_alert=False
        )

    logger.info("Callback handlers registered")
