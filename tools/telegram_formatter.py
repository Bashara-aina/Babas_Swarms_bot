"""telegram_formatter.py — Formatting rules for all Telegram bot responses.

All responses should pass through format_for_telegram() before sending.
Handles: TL;DR injection, markdown headers, code block labeling,
long-message chunking, and emoji budgeting.
"""

from __future__ import annotations
import re
from typing import Generator

MAX_MESSAGE_LEN = 4096
TLDR_THRESHOLD = 2000
MAX_PARA_CHARS = 280
MAX_EMOJI_PER_MSG = 3

# Telegram-safe markdown header → bold + newline
_MD_HEADER = re.compile(r'^#{1,3}\s+(.+)$', re.MULTILINE)
# Raw JSON detector
_RAW_JSON = re.compile(r'^\s*[{\[]', re.MULTILINE)
# Emoji counter
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U00002700-\U000027BF"
    "\U0001FA00-\U0001FA6F"
    "]+",
    re.UNICODE
)


def _convert_headers(text: str) -> str:
    """Convert ## headers to **bold** + newline for Telegram."""
    def _replace(m: re.Match) -> str:
        return f"\n**{m.group(1).strip()}**\n"
    return _MD_HEADER.sub(_replace, text)


def _budget_emojis(text: str) -> str:
    """Cap emoji count at MAX_EMOJI_PER_MSG by removing excess."""
    count = 0
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        if _EMOJI_RE.match(char):
            count += 1
            if count <= MAX_EMOJI_PER_MSG:
                result.append(char)
            # else: drop the emoji
        else:
            result.append(char)
        i += 1
    return ''.join(result)


def _generate_tldr(text: str) -> str:
    """Generate a simple TL;DR by extracting first meaningful sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Take first 2-3 sentences that aren't headers or empty
    summary_parts = []
    for s in sentences:
        s = s.strip()
        if s and not s.startswith('**') and not s.startswith('#') and len(s) > 20:
            summary_parts.append(s)
        if len(summary_parts) >= 2:
            break
    if not summary_parts:
        return ""
    return "**⚡ TL;DR:** " + ' '.join(summary_parts)


def format_for_telegram(text: str, inject_tldr: bool = True) -> str:
    """Main formatter. Converts markdown, injects TL;DR, budgets emojis.

    Args:
        text: Raw response string.
        inject_tldr: Whether to inject TL;DR for long responses.

    Returns:
        Telegram-ready formatted string.
    """
    if not text:
        return text

    text = _convert_headers(text)

    # Inject TL;DR at the TOP for long responses
    if inject_tldr and len(text) > TLDR_THRESHOLD:
        tldr = _generate_tldr(text)
        if tldr:
            text = tldr + "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n" + text

    text = _budget_emojis(text)
    return text.strip()


def chunk_message(text: str, max_len: int = MAX_MESSAGE_LEN) -> Generator[str, None, None]:
    """Split a long message into Telegram-safe chunks.

    Splits at paragraph boundaries when possible.

    Args:
        text: Full message text.
        max_len: Maximum characters per chunk.

    Yields:
        String chunks <= max_len characters.
    """
    if len(text) <= max_len:
        yield text
        return

    paragraphs = text.split('\n\n')
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph would exceed limit, flush current chunk
        candidate = (current_chunk + '\n\n' + para).strip() if current_chunk else para
        if len(candidate) > max_len:
            if current_chunk:
                yield current_chunk
                current_chunk = para
            else:
                # Single paragraph too long — hard split
                while len(para) > max_len:
                    yield para[:max_len]
                    para = para[max_len:]
                current_chunk = para
        else:
            current_chunk = candidate

    if current_chunk:
        yield current_chunk


def format_code_block(code: str, language: str = "python") -> str:
    """Wrap code in a Telegram code block with language label."""
    return f"```{language}\n{code.strip()}\n```"


def format_progress(step: str, total_steps: int, current: int) -> str:
    """Format a progress line for long-running operations."""
    bar_len = 10
    filled = int(bar_len * current / max(total_steps, 1))
    bar = '█' * filled + '░' * (bar_len - filled)
    return f"[{bar}] {current}/{total_steps} — {step}"
