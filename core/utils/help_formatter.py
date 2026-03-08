"""Beautiful, scannable help and documentation formatting.

Provides well-structured help messages with visual hierarchy
and easy navigation.
"""

from __future__ import annotations


class HelpFormatter:
    """Format help messages with visual hierarchy."""

    @staticmethod
    def format_help_menu() -> str:
        """Main help screen with clear sections and examples.
        
        Returns:
            Formatted help text with HTML markup
        """
        return (
            "🤖 <b>LegionSwarm — Your AI Desktop Assistant</b>\n"
            "\n"
            "🎯 <b>Quick Start</b>\n"
            "• Just <i>talk naturally</i> — no commands needed!\n"
            "• Or tap buttons below for common tasks\n"
            "\n"
            "✨ <b>What I Can Do</b>\n"
            "\n"
            "<b>💻 Code & Debug</b>\n"
            "• Write, fix, and explain code\n"
            "• Debug errors with stack traces\n"
            "• Read/write files in your workspace\n"
            "\n"
            "<b>🔍 Analysis & Data</b>\n"
            "• Analyze CSV, JSON, logs\n"
            "• Extract data from documents\n"
            "• Create visualizations\n"
            "\n"
            "<b>🖥️ Desktop Control</b>\n"
            "• Take screenshots\n"
            "• Read screen text (OCR)\n"
            "• Click UI elements by name\n"
            "\n"
            "<b>📝 Documents</b>\n"
            "• Upload PDFs, Word docs\n"
            "• Ask questions about content\n"
            "• Summarize & extract data\n"
            "\n"
            "🔗 <i>Tip: Send /commands for full command list</i>"
        )

    @staticmethod
    def format_command_list() -> str:
        """Organized command reference by category.
        
        Returns:
            Formatted command list with HTML markup
        """
        return (
            "📚 <b>Command Reference</b>\n"
            "\n"
            "<b>💻 Development</b>\n"
            "<code>/run &lt;task&gt;</code> — Auto-route to best agent\n"
            "<code>/agent &lt;name&gt; &lt;task&gt;</code> — Force specific agent\n"
            "<code>/read &lt;path&gt;</code> — Read file\n"
            "<code>/cmd &lt;shell&gt;</code> — Run shell command\n"
            "<code>/git</code> — Git status\n"
            "\n"
            "<b>🖥️ Desktop</b>\n"
            "<code>/desktop</code> — Screenshot\n"
            "<code>/screen</code> — OCR read\n"
            "<code>/click &lt;text&gt;</code> — Click element\n"
            "\n"
            "<b>🌐 Web</b>\n"
            "<code>/scrape &lt;url&gt;</code> — Extract text\n"
            "<code>/shot &lt;url&gt;</code> — Screenshot page\n"
            "\n"
            "<b>📌 Organization</b>\n"
            "<code>/threads</code> — List conversations\n"
            "<code>/thread &lt;name&gt;</code> — Switch thread\n"
            "<code>/context</code> — Show history\n"
            "\n"
            "<b>⚙️ System</b>\n"
            "<code>/stats</code> — Performance report\n"
            "<code>/usage</code> — API costs\n"
            "<code>/circuits</code> — Circuit breaker status\n"
            "\n"
            "💡 <i>Most commands work with natural language too!</i>\n"
            "Example: \"show me my threads\" = /threads"
        )

    @staticmethod
    def format_agent_roster() -> str:
        """Beautiful agent roster with descriptions.
        
        Returns:
            Formatted agent list
        """
        return (
            "🤖 <b>Agent Roster</b>\n"
            "\n"
            "<b>👁️ Vision</b> — Image analysis & OCR\n"
            "<b>💻 Coding</b> — Write & review code\n"
            "<b>🐛 Debug</b> — Fix errors & bugs\n"
            "<b>🔢 Math</b> — Calculations & formulas\n"
            "<b>🏗️ Architect</b> — System design\n"
            "<b>📚 Mentor</b> — Teach & explain concepts\n"
            "<b>📊 Analyst</b> — Data analysis\n"
            "\n"
            "💡 <i>I'll auto-select the best agent for your task</i>"
        )

    @staticmethod
    def format_examples() -> str:
        """Show usage examples.
        
        Returns:
            Formatted examples
        """
        return (
            "💡 <b>Example Queries</b>\n"
            "\n"
            "<b>💻 Coding</b>\n"
            "• \"Write a Python function to parse JSON\"\n"
            "• \"Debug this error: [paste traceback]\"\n"
            "• \"Read /path/to/file.py\"\n"
            "\n"
            "<b>📊 Data Analysis</b>\n"
            "• [Upload CSV] + \"Analyze this data\"\n"
            "• \"Show me trends in this dataset\"\n"
            "• \"Extract tables from this PDF\"\n"
            "\n"
            "<b>🖥️ Desktop</b>\n"
            "• \"What's on my screen?\"\n"
            "• \"Click on the Submit button\"\n"
            "• \"Take a screenshot\"\n"
            "\n"
            "<b>📝 Documents</b>\n"
            "• [Upload PDF] + \"Summarize this\"\n"
            "• \"What's the main point of this document?\"\n"
            "• \"Extract all numbers from this file\"\n"
        )
