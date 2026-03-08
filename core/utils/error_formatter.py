"""Beautiful, actionable error messages with recovery options.

Transforms technical errors into user-friendly messages with
contextual recovery actions and helpful guidance.
"""

from __future__ import annotations

import logging
from typing import Tuple, Optional

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)


class ErrorFormatter:
    """Format errors with context and recovery options."""

    # Error category templates
    _ERROR_TEMPLATES = {
        "timeout": (
            "⏱️ <b>Timeout</b>\n\n"
            "The operation took too long and was cancelled."
        ),
        "network": (
            "🌐 <b>Network Error</b>\n\n"
            "Couldn't connect to the service. Check your internet connection."
        ),
        "not_found": (
            "🔍 <b>Not Found</b>\n\n"
            "The requested resource doesn't exist."
        ),
        "permission": (
            "🔒 <b>Permission Denied</b>\n\n"
            "I don't have access to that resource."
        ),
        "rate_limit": (
            "⏱️ <b>Rate Limited</b>\n\n"
            "Too many requests. Please wait a moment and try again."
        ),
        "file_error": (
            "📁 <b>File Error</b>\n\n"
            "There was a problem accessing the file."
        ),
        "syntax_error": (
            "⚠️ <b>Syntax Error</b>\n\n"
            "The code or input has a syntax problem."
        ),
    }

    @staticmethod
    def format_error(
        error_type: str,
        error: Exception,
        context: str,
        recovery_actions: list[tuple[str, str]] | None = None,
    ) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
        """Format error with context and recovery options.
        
        Args:
            error_type: User-friendly category ("Screenshot", "File Read", etc.)
            error: The exception that occurred
            context: What was being attempted ("Taking screenshot of example.com")
            recovery_actions: List of (button_label, callback_data) tuples
                Example: [("🔄 Retry", "retry:shot:url"), ("📷 Try Desktop", "quick:desktop")]
            
        Returns:
            Tuple of (formatted_message, inline_keyboard or None)
            
        Example:
            >>> error_msg, keyboard = ErrorFormatter.format_error(
            ...     error_type="Screenshot",
            ...     error=TimeoutError("Page load timeout"),
            ...     context="Taking screenshot of https://example.com",
            ...     recovery_actions=[
            ...         ("🔄 Retry", "retry:shot:https://example.com"),
            ...         ("📷 Desktop Screenshot", "quick:desktop"),
            ...     ]
            ... )
            >>> await message.answer(error_msg, reply_markup=keyboard, parse_mode="HTML")
        """
        # Detect error category from exception
        category = ErrorFormatter._categorize_error(error)
        
        # Get template
        template = ErrorFormatter._ERROR_TEMPLATES.get(category, "❌ <b>Error</b>\n\n")
        
        # Build message
        lines = [template]
        
        # Add context
        lines.append(f"<b>While:</b> {context}")
        
        # Add technical details (collapsed)
        error_str = str(error)
        if error_str:
            # Truncate long errors
            if len(error_str) > 200:
                error_str = error_str[:197] + "..."
            lines.append(f"\n<b>Details:</b>\n<code>{error_str}</code>")
        
        message = "\n\n".join(lines)
        
        # Build recovery keyboard
        keyboard = None
        if recovery_actions:
            builder = InlineKeyboardBuilder()
            
            # Add custom recovery actions
            for label, callback in recovery_actions:
                builder.button(text=label, callback_data=callback)
            
            # Always add help option
            builder.button(text="ℹ️ Get Help", callback_data="error:help")
            builder.button(text="⬅️ Main Menu", callback_data="nav:main_menu")
            
            builder.adjust(1)  # One button per row for clarity
            keyboard = builder.as_markup()
        
        return message, keyboard

    @staticmethod
    def _categorize_error(error: Exception) -> str:
        """Detect error category from exception.
        
        Returns:
            Error category key for templates
        """
        exc_str = str(error).lower()
        exc_type = type(error).__name__.lower()
        
        # Check exception type
        if "timeout" in exc_type or "timeout" in exc_str:
            return "timeout"
        
        if "network" in exc_str or "connection" in exc_str:
            return "network"
        
        if "not found" in exc_str or "404" in exc_str or "filenotfound" in exc_type:
            return "not_found"
        
        if "permission" in exc_str or "403" in exc_str or "access denied" in exc_str:
            return "permission"
        
        if "rate limit" in exc_str or "429" in exc_str:
            return "rate_limit"
        
        if "file" in exc_type or "io" in exc_type:
            return "file_error"
        
        if "syntax" in exc_type or "syntax" in exc_str:
            return "syntax_error"
        
        # Default to generic error
        return "unknown"

    @staticmethod
    def format_validation_error(
        field: str,
        issue: str,
        suggestion: str | None = None,
    ) -> str:
        """Format validation error with suggestion.
        
        Args:
            field: Field name that failed validation
            issue: What's wrong
            suggestion: Optional suggestion for fixing
            
        Returns:
            Formatted validation error message
            
        Example:
            >>> msg = ErrorFormatter.format_validation_error(
            ...     field="URL",
            ...     issue="Invalid format",
            ...     suggestion="Use format: https://example.com"
            ... )
        """
        lines = [
            "⚠️ <b>Validation Error</b>\n",
            f"<b>Field:</b> {field}",
            f"<b>Issue:</b> {issue}",
        ]
        
        if suggestion:
            lines.append(f"\n💡 <b>Suggestion:</b>\n{suggestion}")
        
        return "\n".join(lines)
