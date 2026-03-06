# /home/newadmin/swarm-bot/formatters.py
"""Telegram HTML response formatters.

Each method returns a Telegram-safe HTML string.
Telegram supports: <b>, <i>, <u>, <s>, <code>, <pre>, <a>, <blockquote>
"""

from __future__ import annotations

import html
import re
from typing import Optional


def _esc(text: str) -> str:
    """Escape text for Telegram HTML (but not our own HTML tags)."""
    return html.escape(text, quote=False)


class ResponseFormatter:
    """Format agent responses for maximum Telegram readability."""

    # ── Agent-specific formatters ──────────────────────────────────────────────

    @staticmethod
    def coding(result: str, language: str = "python") -> str:
        """Wrap code generation output."""
        code_blocks, prose = _split_code_and_prose(result)
        if code_blocks:
            body = prose.strip()
            code_section = "\n\n".join(
                f"<pre><code class=\"language-{language}\">{_esc(cb)}</code></pre>"
                for cb in code_blocks
            )
            return (
                f"<b>💻 Generated Code</b>\n\n"
                + (f"{body}\n\n" if body else "")
                + code_section
            )
        return f"<b>💻 Coding Agent</b>\n\n{result}"

    @staticmethod
    def debug(result: str, error_text: str = "") -> str:
        """Format debug/error analysis output."""
        parts = ["<b>🐛 Debug Analysis</b>"]
        if error_text:
            short_error = error_text.strip()[:300]
            parts.append(f"<b>Error:</b>\n<code>{_esc(short_error)}</code>")
        parts.append(result)
        return "\n\n".join(parts)

    @staticmethod
    def mentor(result: str, concept: str = "") -> str:
        """Format educational explanation."""
        header = f"<b>📚 {_esc(concept)}</b>\n\n" if concept else "<b>📚 Explanation</b>\n\n"
        # Wrap the last paragraph as a key-takeaway blockquote if it's short
        paragraphs = [p.strip() for p in result.strip().split("\n\n") if p.strip()]
        if len(paragraphs) > 1 and len(paragraphs[-1]) < 200:
            body = "\n\n".join(paragraphs[:-1])
            takeaway = paragraphs[-1]
            return (
                header
                + body
                + f"\n\n<blockquote>💡 <b>Key Takeaway:</b>\n{takeaway}</blockquote>"
            )
        return header + result

    @staticmethod
    def analyst(result: str) -> str:
        """Format data analysis output."""
        return f"<b>📊 Analysis Results</b>\n\n{result}"

    @staticmethod
    def math(result: str) -> str:
        """Format mathematical derivations."""
        return f"<b>🔢 Math Solution</b>\n\n{result}"

    @staticmethod
    def architect(result: str) -> str:
        """Format system design output."""
        return f"<b>🏗️ System Design</b>\n\n{result}"

    @staticmethod
    def vision(result: str) -> str:
        """Format visual analysis output."""
        return f"<b>👁️ Screen Analysis</b>\n\n{result}"

    @staticmethod
    def generic(result: str, agent_key: str) -> str:
        """Fallback formatter for any agent."""
        icons = {
            "vision":    "👁️",
            "coding":    "💻",
            "debug":     "🐛",
            "math":      "🔢",
            "architect": "🏗️",
            "mentor":    "📚",
            "analyst":   "📊",
        }
        icon = icons.get(agent_key, "🤖")
        label = agent_key.upper()
        return f"<b>{icon} {label}</b>\n\n{result}"

    # ── UI-specific formatters ─────────────────────────────────────────────────

    @staticmethod
    def thread_status(thread_id: str, turn: int, last_agent: str) -> str:
        """Thread context bar appended to every response."""
        return (
            f"\n\n<i>📍 <b>{thread_id}</b> · Turn {turn} · {last_agent}</i>"
        )

    @staticmethod
    def file_preview(name: str, size_kb: float, mime: str) -> str:
        """Preview card for uploaded documents."""
        ext = name.rsplit(".", 1)[-1].upper() if "." in name else "FILE"
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
        return (
            f"<b>📄 {_esc(name)}</b>\n\n"
            f"<b>Type:</b> {ext} · <b>Size:</b> {size_str}\n\n"
            f"What would you like me to do with it?"
        )

    @staticmethod
    def supervisor_summary(steps: list[str], results: list[str]) -> str:
        """Collapsible summary of multi-step orchestration."""
        lines = ["<b>✅ Multi-Step Task Complete</b>\n"]
        for i, (step, res) in enumerate(zip(steps, results), 1):
            snippet = res.strip()[:120].replace("\n", " ")
            lines.append(f"<b>{i}.</b> {_esc(step)}\n   <i>{_esc(snippet)}…</i>")
        return "\n\n".join(lines)

    @staticmethod
    def error_box(title: str, detail: str) -> str:
        """Formatted error notification."""
        return (
            f"<b>🔴 {_esc(title)}</b>\n\n"
            f"<code>{_esc(detail[:800])}</code>"
        )


# ── Dispatch helper ────────────────────────────────────────────────────────────

def format_response(result: str, agent_key: str, context: str = "") -> str:
    """Route to agent-specific formatter.

    Args:
        result: Raw text from interpreter_bridge.run_task().
        agent_key: Agent identifier.
        context: Optional context (error text, concept name, etc.).

    Returns:
        Telegram HTML string.
    """
    fmt = ResponseFormatter
    if agent_key == "coding":
        return fmt.coding(result)
    if agent_key == "debug":
        return fmt.debug(result, error_text=context)
    if agent_key == "mentor":
        return fmt.mentor(result, concept=context)
    if agent_key == "analyst":
        return fmt.analyst(result)
    if agent_key == "math":
        return fmt.math(result)
    if agent_key == "architect":
        return fmt.architect(result)
    if agent_key == "vision":
        return fmt.vision(result)
    return fmt.generic(result, agent_key)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _split_code_and_prose(text: str) -> tuple[list[str], str]:
    """Extract fenced code blocks from markdown-ish text.

    Returns:
        (list of code strings, remaining prose text)
    """
    code_blocks: list[str] = []
    prose = re.sub(
        r"```[a-zA-Z]*\n(.*?)```",
        lambda m: (code_blocks.append(m.group(1)) or ""),
        text,
        flags=re.DOTALL,
    )
    return code_blocks, prose.strip()
