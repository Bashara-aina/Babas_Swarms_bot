"""humanizer.py — Post-processing filter to strip AI-speak from all bot responses.

Apply humanize_response() to every message before sending to Telegram.
This is the single highest-impact UX change in the v3.0 upgrade.
"""

from __future__ import annotations
import re

# ── Phrases that mark a response as robotic ─────────────────────────────────
ROBOTIC_PHRASES = [
    r"Based on the (above|information|context|data|analysis)",
    r"In conclusion[,.]?",
    r"To summarize[,.]?",
    r"In summary[,.]?",
    r"It is important to note (that)?",
    r"It should be noted (that)?",
    r"It is worth noting (that)?",
    r"As an AI (language model|assistant)?,?",
    r"As a large language model,?",
    r"I (am|'m) (just |only )?an AI,?",
    r"Certainly[!.]?",
    r"Of course[!.]?",
    r"I'd be happy to",
    r"I would be happy to",
    r"I'm happy to",
    r"Absolutely[!.]?",
    r"Great question[!.]?",
    r"That's a great question[.!]?",
    r"Without further ado[,.]?",
    r"Let me (provide|give|explain|outline|walk you through|break down)",
    r"Allow me to",
    r"Here is a (comprehensive|detailed|step-by-step|thorough)",
    r"Here are some (key|important|main)",
    r"I hope this (helps|clarifies|answers)",
    r"Please (note|be aware|keep in mind) that",
    r"Feel free to",
    r"Do not hesitate to",
    r"I'm (here to help|unable to|not able to)",
]

# Compiled regex patterns (case-insensitive)
_ROBOTIC_RE = [re.compile(p, re.IGNORECASE) for p in ROBOTIC_PHRASES]

# ── Passive-voice -tion heavy patterns → flag for restructuring ──────────────
_PASSIVE_TION = re.compile(
    r'\b(is|are|was|were|be|been|being)\s+\w+ed\b.*?tion\b',
    re.IGNORECASE
)

# ── Bullet-wall detector: 5+ consecutive bullet lines ────────────────────────
_BULLET_LINE = re.compile(r'^\s*[-•*]\s+.+', re.MULTILINE)
_BULLET_BLOCK = re.compile(r'(^\s*[-•*]\s+.+\n?){5,}', re.MULTILINE)


def _strip_robotic_phrases(text: str) -> str:
    """Remove sentence openers and filler phrases that sound corporate."""
    for pattern in _ROBOTIC_RE:
        # Remove the phrase and clean up leftover leading punctuation
        text = pattern.sub('', text)
    # Clean double spaces and leading/trailing whitespace per line
    lines = [re.sub(r' {2,}', ' ', line).strip() for line in text.splitlines()]
    # Remove lines that are now empty due to full phrase removal
    lines = [l for l in lines if l]
    return '\n'.join(lines)


def _reformat_bullet_walls(text: str) -> str:
    """Convert 5+ consecutive bullet points into flowing paragraphs."""
    def _bullets_to_prose(match: re.Match) -> str:
        block = match.group(0)
        items = _BULLET_LINE.findall(block)
        # Clean the bullet marker
        cleaned = [re.sub(r'^\s*[-•*]\s+', '', item).strip() for item in items]
        if not cleaned:
            return block
        # Join into paragraph with semicolons, last item ends with period
        if len(cleaned) == 1:
            return cleaned[0] + '.'
        prose = ', '.join(cleaned[:-1]) + ', and ' + cleaned[-1]
        if not prose.endswith('.'):
            prose += '.'
        return prose

    return _BULLET_BLOCK.sub(_bullets_to_prose, text)


def humanize_response(text: str) -> str:
    """Full pipeline: strip robotic phrases, reformat bullet walls.

    Apply this to ALL bot responses before sending to Telegram.

    Args:
        text: Raw LLM response string.

    Returns:
        Cleaned, more human-sounding response string.
    """
    if not text or not text.strip():
        return text

    text = _strip_robotic_phrases(text)
    text = _reformat_bullet_walls(text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Ensure we didn't reduce to empty string
    return text if text else "...hm, something went sideways generating that response."
