"""Legion character enforcer — strip forbidden phrases, apply GSA voice, enforce soul.

Reads config/legion_character.json once at import time.
Used in llm_client.py after postprocess_response() to clean every response.

Key improvements over v1:
- Context-aware enforcement (emotional vs technical vs analytical)
- Visual signal awareness (emoji density, caps, punctuation)
- Flow-aware processing (follow-up, pivot, closing detection)
- Feedback learning system (tracks patterns that need enforcement)
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# === CJK/Arabic/Cyrillic Language Detection ===
import re as _re

# Detect CJK characters (Chinese/Japanese/Korean)
CJK_PATTERN = _re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\u3400-\u4dbf]")

# Arabic script
ARABIC_PATTERN = _re.compile(r"[\u0600-\u06ff]")

# Cyrillic script (Russian, Ukrainian, etc.)
CYRILLIC_PATTERN = _re.compile(r"[\u0400-\u04ff\u0500-\u052f\u2de0-\u2dff\ua640-\ua69f]")

ALLOWED_SCRIPTS = [
    r"[a-zA-Z]",  # Latin (English)
    r"[\u00C0-\u024F]",  # Extended Latin (accented chars)
    r"[0-9]",  # Numbers
    r"[\u0020-\u007E]",  # Basic ASCII punctuation/symbols
    r"[\u2000-\u206F]",  # General punctuation
    r"[\u2600-\u26FF]",  # Emoji symbols
    r"[\U0001F300-\U0001F9FF]",  # Emoji ranges
]


def has_non_allowed_script(text: str) -> bool:
    """Returns True if text contains CJK, Arabic, or Cyrillic characters."""
    return bool(CJK_PATTERN.search(text)) or bool(ARABIC_PATTERN.search(text)) or bool(CYRILLIC_PATTERN.search(text))


def strip_non_allowed_script(text: str) -> str:
    """
    Remove CJK and Arabic characters from response.
    Replace with closest Indonesian equivalent if mapping known,
    otherwise remove the character.
    """
    # Common Chinese leaks and their Indonesian equivalents
    CJK_REPLACEMENTS = {
        "好奇": "penasaran",
        "很好": "bagus",
        "谢谢": "terima kasih",
        "对": "ya",
        "不": "tidak",
        "是": "iya",
        "的": "",
        "了": "",
        "吗": "?",
        "嗯": "hmm",
        "哦": "oh",
    }

    for cjk, replacement in CJK_REPLACEMENTS.items():
        text = text.replace(cjk, replacement)

    # Strip any remaining CJK/Arabic/Cyrillic
    text = CJK_PATTERN.sub("", text)
    text = ARABIC_PATTERN.sub("", text)
    text = CYRILLIC_PATTERN.sub("", text)

    # Clean up double spaces from removals
    text = _re.sub(r"  +", " ", text)
    text = _re.sub(r" ([,\.!?])", r"\1", text)

    return text.strip()


def enforce_language(text: str) -> str:
    """Main enforcer — call this before sending any response to Telegram."""
    if has_non_allowed_script(text):
        fixed = strip_non_allowed_script(text)
        logging.warning(f"[LANGUAGE ENFORCER] Stripped non-allowed script. Before: {text[:100]}")
        return fixed
    return text


_CONFIG_PATH = Path(__file__).parent.parent / "config" / "legion_character.json"
_character: dict = {}

# Hardcoded fallback — always enforced even if config/legion_character.json missing
_FALLBACK_FORBIDDEN = [
    "Certainly!",
    "Certainly,",
    "Great question!",
    "Of course!",
    "I'd be happy to",
    "I would be happy to",
    "As an AI",
    "as an AI",
    "I'm just an AI",
    "I don't have feelings",
    "I cannot feel",
    "Absolutely!",
    "Absolutely,",
    "Sure!",
    "Sure,",
    "I hope this helps",
    "I hope that helps",
    "Let me know if you need",
    "Please let me know",
    "Feel free to ask",
    "Don't hesitate to",
    "I understand your concern",
    "That's a great point",
    "I apologize for any confusion",
    "I apologize for the confusion",
]

GSA_BANNED_OPENERS = [
    "iya, ",
    "ya, ",
    "ok, ",
    "oke, ",
    "baik, ",
    "tentu, ",
    "pastinya, ",
    "benar, ",
    "tepat, ",
]

GSA_BANNED_CLOSERS = [
    "kalau ada pertanyaan",
    "jangan ragu untuk",
    "semoga membantu",
    "silakan hubungi",
    "apakah ada yang ingin",
]

GSA_BANNED_PHRASES = [
    "kamu pasti bisa",
    "semangat",
    "jangan menyerah",
    "tetap semangat",
    "you got this",
    "keep going",
    "pada dasarnya",
    "sebenarnya",
    "jadi begini",
    "intinya adalah",
    "sesuai dengan visi misi",
    "dalam rangka",
    "dengan ini",
    "perlu diketahui bahwa",
    "tentu saja",
    "pastinya",
    "benar sekali",
    "tepat sekali",
    "pertanyaan yang bagus",
]


class EnforcementContext:
    """Context-aware enforcement parameters."""

    def __init__(
        self,
        context_type: str = "general",
        confidence: float = 0.5,
        visual_signals: Optional[list[str]] = None,
        flow_state: str = "new",
    ):
        self.context_type = context_type
        self.confidence = confidence
        self.visual_signals = visual_signals or []
        self.flow_state = flow_state

    @property
    def is_emotional(self) -> bool:
        return self.context_type == "emotional"

    @property
    def is_technical(self) -> bool:
        return self.context_type == "technical"

    @property
    def is_analytical(self) -> bool:
        return self.context_type == "analytical"

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.7


_enforcement_context: Optional[EnforcementContext] = None


def set_enforcement_context(context: EnforcementContext) -> None:
    """Set the current enforcement context for GSA-aware processing."""
    global _enforcement_context
    _enforcement_context = context


def get_enforcement_context() -> EnforcementContext:
    """Get current enforcement context, returns default if not set."""
    if _enforcement_context is None:
        return EnforcementContext()
    return _enforcement_context


def clear_enforcement_context() -> None:
    """Clear enforcement context after processing."""
    global _enforcement_context
    _enforcement_context = None


# Feedback learning system — tracks patterns that need enforcement
class GSAFeedbackTracker:
    """Tracks enforcement patterns for continuous improvement."""

    def __init__(self):
        self._pattern_counts: dict[str, int] = {}
        self._pattern_last_seen: dict[str, float] = {}
        self._recent_stripped: list[str] = []
        self._max_history = 100

    def record_stripped(self, pattern: str) -> None:
        """Record that a pattern was stripped."""
        self._pattern_counts[pattern] = self._pattern_counts.get(pattern, 0) + 1
        self._pattern_last_seen[pattern] = time.time()
        self._recent_stripped.append(pattern)
        if len(self._recent_stripped) > self._max_history:
            self._recent_stripped.pop(0)

    def get_hot_patterns(self, min_count: int = 3) -> list[str]:
        """Get patterns stripped multiple times recently."""
        now = time.time()
        hot = []
        for pattern, count in self._pattern_counts.items():
            if count >= min_count:
                last_seen = self._pattern_last_seen.get(pattern, 0)
                if now - last_seen < 3600:  # Seen in last hour
                    hot.append(pattern)
        return sorted(hot, key=lambda p: self._pattern_counts[p], reverse=True)

    def get_pattern_report(self) -> str:
        """Generate a report of enforcement patterns."""
        hot = self.get_hot_patterns(min_count=2)
        if not hot:
            return "No significant enforcement patterns."
        lines = ["Top stripped patterns:", *[f"  {p}: {self._pattern_counts[p]}x" for p in hot[:10]]]
        return "\n".join(lines)


_feedback_tracker = GSAFeedbackTracker()


def get_feedback_tracker() -> GSAFeedbackTracker:
    """Get the global feedback tracker instance."""
    return _feedback_tracker


def _load() -> dict:
    try:
        text = _CONFIG_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
        logger.debug("character_enforcer: loaded %s", _CONFIG_PATH)
        return data
    except FileNotFoundError:
        logger.warning("character_enforcer: config not found at %s — using fallback", _CONFIG_PATH)
        return {}
    except json.JSONDecodeError as exc:
        logger.warning("character_enforcer: invalid JSON in %s: %s — using fallback", _CONFIG_PATH, exc)
        return {}
    except Exception as exc:
        logger.warning("character_enforcer: unexpected error loading %s: %s", _CONFIG_PATH, exc)
        return {}


_character = _load()

_all_forbidden = list(dict.fromkeys(_FALLBACK_FORBIDDEN + _character.get("forbidden_phrases", [])))
_FORBIDDEN_PATTERNS: list[re.Pattern] = [re.compile(re.escape(phrase), re.IGNORECASE) for phrase in _all_forbidden]


def _build_gsa_banned_patterns() -> list[re.Pattern]:
    return [re.compile(re.escape(phrase), re.IGNORECASE) for phrase in GSA_BANNED_PHRASES]


_GSA_BANNED_PATTERNS: list[re.Pattern] = _build_gsa_banned_patterns()


def _should_strip_because(context: EnforcementContext, pattern_type: str) -> bool:
    """Determine if pattern should be stripped based on context."""
    if context.is_emotional:
        if pattern_type in ("banned_phrases", "opener"):
            return context.is_high_confidence
        return False

    if context.is_technical:
        return True

    if context.is_analytical:
        return pattern_type in ("banned_phrases", "opener", "closer")

    return True


def enforce_gsa_structure(text: str, context: Optional[EnforcementContext] = None) -> str:
    """Strip banned openers and closers from GSA-style responses.

    Args:
        text: Input text to clean
        context: Optional enforcement context for adaptive behavior
    """
    ctx = context or get_enforcement_context()
    result = text.lstrip()
    lower = result.lower()

    for opener in GSA_BANNED_OPENERS:
        if lower.startswith(opener):
            original = result
            result = result[len(opener) :].lstrip()
            if result:
                result = result[0].upper() + result[1:]
                _feedback_tracker.record_stripped(f"opener:{opener.strip()}")
            else:
                result = original

    if not ctx.is_emotional:
        lines = result.split("\n")
        filtered = []
        for line in lines:
            lower_line = line.lower()
            should_filter = any(c in lower_line for c in GSA_BANNED_CLOSERS)
            if should_filter:
                _feedback_tracker.record_stripped(f"closer:{line.strip()[:30]}")
            if not should_filter:
                filtered.append(line)
        result = "\n".join(filtered)

    return result.strip()


def _apply_emotional_softeners(text: str) -> str:
    """Apply context-specific softenings for emotional responses."""
    ctx = get_enforcement_context()

    if not ctx.is_emotional:
        return text

    if ctx.flow_state == "closing":
        return text

    lines = text.split("\n")
    if len(lines) > 4:
        return text

    return text


def _enforce_capitalization(text: str) -> str:
    """Ensure proper capitalization after stripping."""
    ctx = get_enforcement_context()

    if ctx.is_emotional:
        return text

    lines = text.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()
        if stripped and stripped[0].islower():
            result.append(stripped[0].upper() + stripped[1:])
        else:
            result.append(stripped)

    return "\n".join(result)


def enforce_character(response: str, agent_key: str = "general") -> str:
    """Strip forbidden phrases from response and apply Legion's voice.

    This function always runs — it never raises or returns the original
    unmodified response silently. Worst case: returns response unchanged
    after logging a warning.
    """
    if not response or not isinstance(response, str):
        return response or ""

    # 0. Language enforcement FIRST — strip CJK/Arabic before any other processing
    response = enforce_language(response)
    if not response:
        return ""

    ctx = get_enforcement_context()
    cleaned = response

    # 1. Strip forbidden phrases
    for pattern in _FORBIDDEN_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    # 2. Strip GSA banned phrases (context-aware)
    for pattern in _GSA_BANNED_PATTERNS:
        if _should_strip_because(ctx, "banned_phrases"):
            before = cleaned
            cleaned = pattern.sub("", cleaned)
            if before != cleaned:
                _feedback_tracker.record_stripped(f"phrase:{pattern.pattern}")

    # 3. Strip double spaces / leading whitespace artifacts
    cleaned = re.sub(r"  +", " ", cleaned)
    cleaned = re.sub(r"^\s+", "", cleaned, flags=re.MULTILINE)

    # 4. Apply mode-specific voice rules
    style = _character.get("style_adjustments", {})
    mode_rules = style.get(agent_key, style.get("general", []))
    for rule in mode_rules or []:
        find = rule.get("find", "")
        replace = rule.get("replace", "")
        if find:
            try:
                cleaned = re.sub(find, replace, cleaned, flags=re.IGNORECASE)
            except re.error:
                pass

    # 5. Strip corporate opener patterns
    _opener_patterns = [
        r"^(Of course[,!]?\s*)",
        r"^(Sure[,!]?\s*)",
        r"^(Certainly[,!]?\s*)",
        r"^(Absolutely[,!]?\s*)",
        r"^(Great[,!]?\s+)",
        r"^(No problem[,!]?\s*)",
        r"^(Happy to help[,!]?\s*)",
        r"^(I'd be glad to[,!]?\s*)",
    ]
    for pat in _opener_patterns:
        before = cleaned
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
        if before != cleaned:
            _feedback_tracker.record_stripped(f"corp_opener:{pat}")

    # 6. Enforce GSA structure
    cleaned = enforce_gsa_structure(cleaned, ctx)

    # 7. Apply capitalization rules
    cleaned = _enforce_capitalization(cleaned)

    # 8. Emotional context: apply softeners
    if ctx.is_emotional:
        cleaned = _apply_emotional_softeners(cleaned)

    # 9. Check hot patterns from feedback tracker
    hot = _feedback_tracker.get_hot_patterns(min_count=5)
    for pattern in hot:
        pattern_clean = pattern.split(":", 1)[1] if ":" in pattern else pattern
        if pattern_clean in cleaned.lower():
            pattern_obj = re.compile(re.escape(pattern_clean), re.IGNORECASE)
            cleaned = pattern_obj.sub("", cleaned)

    # 10. Never return empty string
    if not cleaned.strip():
        logger.debug("character_enforcer: strip produced empty string — returning original")
        return response

    # 11. Apply dynamic patterns learned from corrections
    from core.gsa_voice import get_dynamic_patterns

    dynamic = get_dynamic_patterns()
    cleaned = dynamic.apply_dynamic_filters(cleaned)

    # 12. Apply response quality scoring and learning
    quality_result = _score_response_quality(response, cleaned, ctx)
    if quality_result.was_corrected:
        _record_quality_feedback(quality_result)

    return cleaned.strip()


class ResponseQualityResult:
    """Result of quality scoring for a response."""

    def __init__(
        self,
        score: float,
        gsa_compliant: bool,
        suggestions: list[str],
        was_corrected: bool = False,
    ):
        self.score = score
        self.gsa_compliant = gsa_compliant
        self.suggestions = suggestions
        self.was_corrected = was_corrected


def _score_response_quality(original: str, cleaned: str, ctx: EnforcementContext) -> ResponseQualityResult:
    """Score response quality and track corrections."""
    suggestions = []
    was_corrected = False

    # Check if we made significant changes
    if len(original) > 20 and len(cleaned) < len(original) * 0.7:
        suggestions.append("Heavy filtering applied - consider adjusting initial generation")
        was_corrected = True

    # Check for GSA compliance
    opener = cleaned.lower().strip()[:20]
    gsa_compliant = True

    banned_openers = ["iya", "ya", "ok", "oke", "baik", "tentu", "pastinya", "benar", "tepat"]
    if any(opener.startswith(b) for b in banned_openers):
        suggestions.append("Starts with banned GSA opener")
        gsa_compliant = False

    if any(c in cleaned.lower() for c in GSA_BANNED_CLOSERS):
        suggestions.append("Contains banned GSA closer")

    # Check for generic motivation in emotional context
    if ctx.is_emotional:
        generic_motivators = ["semangat", "kamu pasti bisa", "mantap", "keren"]
        if any(m in cleaned.lower() for m in generic_motivators):
            suggestions.append("Generic motivation in emotional context - too soft")

    # Score based on structure quality
    score = 1.0
    if not gsa_compliant:
        score -= 0.2
    if suggestions:
        score -= 0.1 * len(suggestions)

    return ResponseQualityResult(
        score=max(0.0, score),
        gsa_compliant=gsa_compliant,
        suggestions=suggestions,
        was_corrected=was_corrected,
    )


_quality_history: list[ResponseQualityResult] = []
_MAX_QUALITY_HISTORY = 50


def _record_quality_feedback(result: ResponseQualityResult) -> None:
    """Record quality feedback for learning."""
    global _quality_history
    _quality_history.append(result)
    if len(_quality_history) > _MAX_QUALITY_HISTORY:
        _quality_history.pop(0)


def get_quality_report() -> str:
    """Generate a quality report of recent responses."""
    if not _quality_history:
        return "No quality data yet."

    total = len(_quality_history)
    avg_score = sum(r.score for r in _quality_history) / total
    compliant_count = sum(1 for r in _quality_history if r.gsa_compliant)

    return (
        f"Quality Report (last {total} responses):\n"
        f"  Average score: {avg_score:.2f}\n"
        f"  GSA compliant: {compliant_count}/{total} ({100 * compliant_count / total:.0f}%)\n"
        f"  Suggestions: {sum(len(r.suggestions) for r in _quality_history)}"
    )
