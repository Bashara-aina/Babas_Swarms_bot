"""
tools/telegram_formatter.py

Formatting utilities for Telegram messages:
- TL;DR injection for long responses
- Markdown header conversion
- Message splitting at paragraph boundaries
- Inline keyboard builders
"""
from __future__ import annotations
import re

try:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    AIOGRAM_AVAILABLE = True
except ImportError:
    AIOGRAM_AVAILABLE = False


def _extract_tldr(text: str) -> str:
    """Extract a TL;DR from the last paragraph or last 2 sentences."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        return ""
    # Use the last meaningful paragraph
    last = paragraphs[-1]
    # Take first 2 sentences
    sentences = re.split(r'(?<=[.!?])\s+', last)
    tldr = ' '.join(sentences[:2])
    # Clean markdown
    tldr = re.sub(r'[*_`]', '', tldr)
    return tldr[:280] if len(tldr) > 280 else tldr


def format_response(text: str) -> str:
    """
    Apply Telegram-friendly formatting:
    - Inject TL;DR at top if >2000 chars
    - Convert ## headers to bold
    - Convert ### headers to bold inline
    """
    if not text:
        return text

    # Convert markdown headers to Telegram bold
    text = re.sub(r'^### (.+)$', r'**\1:**', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'\n**\1**\n', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'\n**\1**\n', text, flags=re.MULTILINE)

    # Add language specifier to bare code blocks
    text = re.sub(r'```\n', '```text\n', text)

    # Inject TL;DR at top if long
    if len(text) > 2000:
        tldr = _extract_tldr(text)
        if tldr:
            text = f"**TL;DR:** {tldr}\n\n---\n\n{text}"

    return text


def split_message(text: str, max_len: int = 4096) -> list[str]:
    """
    Split text into chunks of max_len, preferring paragraph boundaries.
    Returns a list of message strings.
    """
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    paragraphs = text.split('\n\n')
    current = ""

    for para in paragraphs:
        candidate = (current + '\n\n' + para).strip() if current else para
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If a single paragraph is too long, split by line
            if len(para) > max_len:
                lines = para.splitlines()
                line_chunk = ""
                for line in lines:
                    test = (line_chunk + '\n' + line).strip() if line_chunk else line
                    if len(test) <= max_len:
                        line_chunk = test
                    else:
                        if line_chunk:
                            chunks.append(line_chunk)
                        line_chunk = line[:max_len]
                if line_chunk:
                    chunks.append(line_chunk)
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks if chunks else [text[:max_len]]


def build_inline_keyboard(keyboard_type: str):
    """Build inline keyboard for swarm/research/think responses."""
    if not AIOGRAM_AVAILABLE:
        return None

    if keyboard_type == "swarm":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="\ud83d\udd01 Re-debate", callback_data="re_debate"),
                InlineKeyboardButton(text="\ud83d\udcca Export JSON", callback_data="export_json"),
            ],
            [
                InlineKeyboardButton(text="\ud83d\udd0d Deep Research This", callback_data="deep_research_this"),
            ],
        ])
    elif keyboard_type == "research":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="\ud83d\udcc4 Full Sources", callback_data="full_sources"),
                InlineKeyboardButton(text="\ud83e\udde0 Synthesize", callback_data="synthesize"),
            ],
            [
                InlineKeyboardButton(text="\ud83d\udcbe Save Note", callback_data="save_note"),
            ],
        ])
    elif keyboard_type == "think":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="\u2694\ufe0f Challenge This", callback_data="challenge_this"),
                InlineKeyboardButton(text="\ud83d\udd01 Think Again", callback_data="think_again"),
            ],
            [
                InlineKeyboardButton(text="\u2705 Accept", callback_data="accept_answer"),
            ],
        ])
    else:
        return None

    return keyboard
