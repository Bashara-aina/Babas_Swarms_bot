"""Clarifying Questions — Legion asks one focused question when intent is ambiguous.

Implements Priority 5 from DEEP_AUDIT_2026-04-12.md:
When intent confidence < 0.4 AND message is short (< 8 words),
ask ONE specific clarifying question before giving a generic answer.

All functions are async. All calls wrapped in try/except. Logger used throughout.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ── Thresholds ───────────────────────────────────────────────────────────────

AMBIGUITY_THRESHOLD = 0.4  # confidence below this triggers clarification
SHORT_MESSAGE_THRESHOLD = 8  # words


# ── Core functions ────────────────────────────────────────────────────────────


async def should_clarify(message: str, intent: str, confidence: float) -> bool:
    """Return True if we should ask a clarifying question.

    Triggers when BOTH:
      - confidence < 0.4 (low intent confidence)
      - message is short (< 8 words)

    Does NOT trigger for greetings and common courtesies.
    """
    try:
        normalized = message.lower().strip()
        normalized_tokens = set(re.findall(r"\b\w+\b", normalized))
        word_count = len(message.split())
        is_short = word_count < SHORT_MESSAGE_THRESHOLD
        is_low_confidence = confidence < AMBIGUITY_THRESHOLD

        # Clear direct questions should be answered, not bounced with clarification.
        # This avoids over-triggering for short conversational prompts like
        # "Hei Legion, lo siapa?" in integration flows.
        direct_question_tokens = {
            "siapa",
            "apa",
            "kenapa",
            "mengapa",
            "bagaimana",
            "kapan",
            "dimana",
            "gimana",
            "who",
            "what",
            "why",
            "how",
            "when",
            "where",
        }
        if "?" in normalized and direct_question_tokens.intersection(normalized_tokens):
            return False

        NEVER_CLARIFY = {
            "hei",
            "hai",
            "hi",
            "hello",
            "hola",
            "oke",
            "ok",
            "okay",
            "thanks",
            "makasih",
            "terima kasih",
            "yes",
            "no",
            "ya",
            "nope",
            "👍",
            "👋",
            "sip",
            "sipp",
            "betul",
            "benar",
            "good",
            "great",
            "nice",
        }
        if normalized in NEVER_CLARIFY:
            return False

        return is_short and is_low_confidence

    except Exception as e:
        logger.warning("[clarification] should_clarify error (non-fatal): %s", e)
        return False


async def generate_clarification(message: str, intent: str) -> str:
    """Generate a SINGLE specific clarifying question.

    Not a list. Not vague. One sentence maximum.
    Legion's voice: direct, no fluff.

    Examples:
      User: 'fix this'        → 'Fix what exactly? Paste the code or error.'
      User: 'translate'       → 'Translate what, and to which language?'
      User: 'search'          → 'Search for what topic?'
      User: 'analisis sistem' → 'Analisis sistem yang mana? Beri nama sistem atau detail spesifik.'

    Keep the question to 1 sentence maximum. Legion's voice: direct, no fluff.
    """
    try:
        msg = message.strip()
        msg_lower = msg.lower()

        # Pattern: vague pronouns / objects
        vague_words = {"this", "it", "that", "them", "something", "stuff", "thing", "things", "situ"}
        if any(w in msg_lower.split() for w in vague_words):
            if intent in ("code_generation", "code_review"):
                return "Fix what exactly? Paste the code or error message."
            if intent in ("web_research", "web_scrape"):
                return "Search for what? Give me the topic or keywords."
            if intent == "translation":
                return "Translate what, and to which language?"
            if intent == "memory_search":
                return "Search memory for what topic?"
            return "Yang kamu maksud apa specifically? Bisa kasih detail lebih?"

        # Pattern: single-word command (no object)
        if len(msg.split()) <= 2:
            if msg_lower.startswith(("fix", "patch", "debug", "error")):
                return "Fix what exactly? Paste the code or error message."
            if msg_lower.startswith(("translate", "terjemahkan")):
                return "Translate what text, and to which language?"
            if msg_lower.startswith(("search", "cari", "searching")):
                return "Search for what topic?"
            if msg_lower.startswith(("analisis", "analyze", "analysis")):
                return "Analisis sistem yang mana? Beri nama sistem atau detail spesifik."
            if msg_lower.startswith(("build", "create", "buatkan", "tulis")):
                return "Build or create what? Describe the target."
            if msg_lower.startswith(("show", "tampilkan", "cek", "check")):
                return "Show or check what exactly? Be specific."
            return f"'{msg}' — bisa diperjelas maksudnya?"

        # Pattern: message contains implicit context gaps
        if intent == "code_generation" or intent == "code_review":
            if any(w in msg_lower for w in ["function", "code", "script", "class", "api", "bug"]):
                return "Which function/code specifically? Paste it or give the filename."
            return "What code do you want me to write or fix?"

        if intent == "translation":
            return "Translate what text, and to which language?"

        if intent in ("web_research", "web_scrape"):
            return "Search for what? Give me the topic or URL."

        if intent == "memory_search":
            return "Search memory for what topic or keyword?"

        if intent == "data_analysis":
            return "Analyze what data? Give me the file or dataset name."

        # Fallback — make it specific to what was said
        return f"'{msg}' — maksudnya apa genau? Bisa diperjelas sedikit?"

    except Exception as e:
        logger.warning("[clarification] generate_clarification error (non-fatal): %s", e)
        return "Bisa diperjelas maksudnya?"


# ── Convenience wrapper ────────────────────────────────────────────────────────


async def ask_if_needed(
    message: str,
    intent: str,
    confidence: float,
) -> Optional[str]:
    """Main wiring entry point for message_handler.py.

    Returns the clarifying question string if clarification is needed,
    otherwise returns None.

    Call this AFTER intent classification and BEFORE routing to handler.
    """
    if not await should_clarify(message, intent, confidence):
        return None
    return await generate_clarification(message, intent)
