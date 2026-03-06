# /home/newadmin/swarm-bot/formatters.py
"""Response formatters for beautiful, readable Telegram messages."""

from __future__ import annotations
from typing import List
import html


class ResponseFormatter:
    """Format agent responses with rich HTML for maximum readability."""

    @staticmethod
    def format_code_response(
        code: str, language: str = "python", explanation: str = ""
    ) -> str:
        """Format code with syntax highlighting hints."""
        escaped_code = html.escape(code)
        result = f"<b>💻 Generated Code</b>\n\n"
        if explanation:
            result += f"{explanation}\n\n"
        result += f'<pre><code class="language-{language}">{escaped_code}</code></pre>\n\n'
        result += "<i>Copy and test this code, then let me know if you need adjustments.</i>"
        return result

    @staticmethod
    def format_error_analysis(error: str, solution: str, agent: str = "DEBUG") -> str:
        """Format debug output."""
        escaped_error = html.escape(error[:500])
        return f"""<b>🐛 Error Analysis</b> <i>by {agent}</i>

<b>Issue Detected:</b>
<code>{escaped_error}</code>

<b>Root Cause:</b>
{solution}

<blockquote>💡 <b>Quick Fix:</b>
See code or explanation above ☝️</blockquote>
"""

    @staticmethod
    def format_explanation(concept: str, content: str) -> str:
        """Format teaching explanations."""
        return f"""<b>📚 {html.escape(concept)}</b>

{content}

<blockquote>💡 <b>Key Takeaway:</b>
Remember this for next time!</blockquote>
"""

    @staticmethod
    def format_data_analysis(
        insights: List[str], summary: str = "", chart_attached: bool = False
    ) -> str:
        """Format analysis results."""
        formatted_insights = "\n".join([f"  • {i}" for i in insights])
        result = "<b>📊 Analysis Results</b>\n\n"
        if summary:
            result += f"{summary}\n\n"
        result += f"<b>Key Insights:</b>\n{formatted_insights}\n\n"
        if chart_attached:
            result += "<i>See visualization below</i> 👇"
        return result

    @staticmethod
    def format_thread_summary(thread_id: str, turns: int, last_topic: str) -> str:
        """Format thread context display."""
        return f"""<b>📌 Thread: {html.escape(thread_id)}</b>

<b>Conversation Stats:</b>
  • Total turns: {turns}
  • Last topic: {html.escape(last_topic)}
  • Status: Active ✅

<i>All responses in this thread have full context.</i>
"""

    @staticmethod
    def format_system_status(cache_hit_rate: float, avg_latency: float) -> str:
        """Format system performance status."""
        return f"""<b>⚡ System Status</b>

<b>Performance:</b>
  • Cache hit rate: {cache_hit_rate:.1f}%
  • Avg latency: {avg_latency:.2f}s
  • Status: Operational ✅

<i>All systems running smoothly.</i>
"""

    @staticmethod
    def format_with_context(
        agent: str, response: str, thread_id: str = None, turn_count: int = None
    ) -> str:
        """Add context bar to response."""
        context_bar = ""
        if thread_id and turn_count:
            context_bar = f"\n\n<i>📍 Thread: {html.escape(thread_id)} • Turn {turn_count}</i>"
        return f"<b>{agent.upper()}</b>\n\n{response}{context_bar}"

    @staticmethod
    def format_progress_update(step: str, step_num: int, total: int) -> str:
        """Format progress update message."""
        percentage = int((step_num / total) * 100)
        bar_length = 10
        filled = int((step_num / total) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"""⚙️ <b>Progress Update</b>

[{bar}] {percentage}%

<b>Step {step_num}/{total}:</b> {step}
"""

    @staticmethod
    def format_document_preview(filename: str, size_kb: float, pages: int = None) -> str:
        """Format document upload preview."""
        info = f"""📄 <b>Document Received</b>

<b>Filename:</b> <code>{html.escape(filename)}</code>
<b>Size:</b> {size_kb:.1f} KB
"""
        if pages:
            info += f"<b>Pages:</b> {pages}\n"
        info += "\n<b>What would you like me to do?</b>"
        return info

    @staticmethod
    def format_monitor_alert(
        monitor_name: str, status: str, details: str = ""
    ) -> str:
        """Format monitoring alert."""
        icon = "🔴" if "error" in status.lower() or "fail" in status.lower() else "🟢"
        result = f"{icon} <b>Monitor Alert: {html.escape(monitor_name)}</b>\n\n"
        result += f"<b>Status:</b> {status}\n"
        if details:
            result += f"\n{details}"
        return result

    @staticmethod
    def format_feedback_confirmation(rating: str) -> str:
        """Format feedback confirmation."""
        emoji = "👍" if rating == "good" else "👎" if rating == "bad" else "💯"
        return f"{emoji} <b>Feedback Recorded</b>\n\n<i>Thank you! I'll learn from this.</i>"

    @staticmethod
    def escape(text: str) -> str:
        """HTML escape helper."""
        return html.escape(text)
