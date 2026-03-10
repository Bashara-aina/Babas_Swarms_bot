"""
tools/humanizer.py

Post-processing filter that strips AI-speak and robotic phrasing from all bot responses.
Apply humanize_response() to EVERY outgoing message before sending to Telegram.
"""
from __future__ import annotations
import re

# ── Phrases to strip unconditionally ────────────────────────────────────────
_STRIP_PHRASES: list[str] = [
    r"based on the above[,.]?",
    r"in conclusion[,.]?",
    r"it is important to note that",
    r"it's important to note that",
    r"as an ai language model[,.]?",
    r"as an ai[,.]?",
    r"certainly!",
    r"certainly,",
    r"of course!",
    r"of course,",
    r"i'd be happy to",
    r"i'd be glad to",
    r"i'm happy to",
    r"i'm glad to",
    r"great question!",
    r"great question,",
    r"absolutely!",
    r"absolutely,",
    r"sure!",
    r"sure,",
    r"to summarize[,:]?",
    r"in summary[,:]?",
    r"let me summarize[,.]?",
    r"allow me to",
    r"i hope this helps[!.]?",
    r"feel free to ask[^.]*[.!]?",
    r"please let me know[^.]*[.!]?",
    r"is there anything else[^?]*\??",
]

_STRIP_RE = re.compile(
    "|".join(f"(?i){p}" for p in _STRIP_PHRASES),
    re.IGNORECASE,
)

# ── Opener patterns to strip ─────────────────────────────────────────────────
_OPENER_RE = re.compile(
    r'^(I\'ll |I will |Let me |I can |I\'d like to |Here\'s |Here is )[a-z]',
    re.IGNORECASE,
)


def strip_ai_opener(text: str) -> str:
    """Remove the first sentence if it's a robotic opener like 'Let me explain...'."""
    lines = text.strip().splitlines()
    if not lines:
        return text
    first = lines[0].strip()
    # Match opener pattern on first sentence
    first_sentence_end = first.find('.')
    if first_sentence_end == -1:
        first_sentence_end = len(first)
    first_sentence = first[:first_sentence_end + 1]
    if _OPENER_RE.match(first_sentence) and len(first_sentence) < 120:
        # Remove the first sentence
        remainder = text[text.find(first_sentence) + len(first_sentence):].lstrip()
        return remainder if remainder else text
    return text


def _collapse_bullet_walls(text: str) -> str:
    """
    If there are >5 consecutive bullet lines with no intervening prose,
    reformat groups of 3-4 bullets into a flowing paragraph.
    """
    lines = text.splitlines()
    result: list[str] = []
    bullet_buffer: list[str] = []

    def flush_bullets(buf: list[str]) -> list[str]:
        """Convert bullet list to paragraphs (groups of 3)."""
        if len(buf) <= 5:
            return buf
        paragraphs: list[str] = []
        chunk: list[str] = []
        for b in buf:
            stripped = re.sub(r'^[-*•]\s+', '', b).strip()
            chunk.append(stripped)
            if len(chunk) == 3:
                paragraphs.append('. '.join(chunk) + '.')
                chunk = []
        if chunk:
            paragraphs.append('. '.join(chunk) + '.')
        return paragraphs

    bullet_re = re.compile(r'^\s*[-*•]\s+')
    for line in lines:
        if bullet_re.match(line):
            bullet_buffer.append(line)
        else:
            if bullet_buffer:
                result.extend(flush_bullets(bullet_buffer))
                bullet_buffer = []
            result.append(line)
    if bullet_buffer:
        result.extend(flush_bullets(bullet_buffer))

    return '\n'.join(result)


def humanize_response(text: str) -> str:
    """
    Main filter: strip AI-speak, collapse bullet walls, clean whitespace.
    Apply to ALL bot responses before sending to Telegram.
    """
    if not text:
        return text

    # 1. Strip robotic phrases
    cleaned = _STRIP_RE.sub('', text)

    # 2. Strip AI opener from first sentence
    cleaned = strip_ai_opener(cleaned)

    # 3. Collapse bullet walls
    cleaned = _collapse_bullet_walls(cleaned)

    # 4. Clean up double blank lines and leading/trailing whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()

    return cleaned
