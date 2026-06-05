"""Anti-Slop core — 4-guard quality pipeline.

Architecture:
  Guard 1 (FormatGuard)  → filler phrase detection (<1ms, no I/O)
  Guard 2 (PackageGuard) → toxicity/severity check (<2ms, pattern match)
  Guard 3 (CritiqueGuard)→ repetition patterns (<2ms, regex)
  Guard 4 (ConfidenceGuard)→ LLM grounding (async, for NEEDS_IMPROVEMENT only)

run_quality_gate() orchestrates the pipeline and returns a QualityResult.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# ── Directory constants ────────────────────────────────────────────────────────

_LEGION_DIR = Path.home() / ".legion"
_ANTI_SLOP_DIR = _LEGION_DIR / "anti_slop"
_QUARANTINE_DIR = _ANTI_SLOP_DIR / "_quarantine"
_REJECTIONS_LOG = _ANTI_SLOP_DIR / "rejections.json"

# ── Result types ───────────────────────────────────────────────────────────────

Verdict = Literal["PASS", "REJECT", "NEEDS_IMPROVEMENT"]
GuardName = Literal["format", "package", "critique", "confidence"]


@dataclass
class QualityResult:
    """Result of a quality gate evaluation."""

    verdict: Verdict
    score: float
    reason: str
    guard_triggered: GuardName | None
    latency_ms: float
    quarantined: bool = False
    quarantine_path: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be 0.0-1.0, got {self.score}")


# ── Guard 1: FormatGuard (filler phrases) ──────────────────────────────────────

_FILLER_PHRASES: frozenset[str] = frozenset(
    [
        "it goes without saying",
        "as you know",
        "as we all know",
        "it is important to note",
        "needless to say",
        "in order to",
        "at the end of the day",
        "the fact of the matter is",
        "it should be noted",
        "with that being said",
        "that being said",
        "all things considered",
        "in conclusion",
        "to sum up",
        "overall",
        "generally speaking",
        "in general",
        "for the most part",
        "as previously mentioned",
        "as mentioned earlier",
        "to be honest",
        "honestly speaking",
        "frankly speaking",
        "quite frankly",
        "if i'm being honest",
    ]
)

# ── Guard 2: PackageGuard (toxicity patterns) ───────────────────────────────────

_TOXIC_PATTERNS: list[tuple[str, str, float]] = [
    # (regex pattern, description, severity 0-1)
    (r"\b(stupid|idiot|dumb|moron|loser|pathetic)\b", "insult", 0.4),
    (r"\b(hate|despise|detest)\s+\w+", "hostile", 0.3),
    (r"\b(kill|die|death)\s+\w+", "violent threat", 0.5),
    (r"(you are a|you're a|you seem like a)\s+(fool|moron|idiot)", "personal insult", 0.5),
]

# ── Guard 3: CritiqueGuard (repetition) ──────────────────────────────────────

# ── QualityResult builder ──────────────────────────────────────────────────────


def _make_result(
    verdict: Verdict,
    score: float,
    reason: str,
    guard: GuardName | None,
    t0: float,
) -> QualityResult:
    return QualityResult(
        verdict=verdict,
        score=score,
        reason=reason,
        guard_triggered=guard,
        latency_ms=(time.perf_counter() - t0) * 1000,
    )


# ── Guard implementations ──────────────────────────────────────────────────────


def guard_format(content: str) -> tuple[bool, str]:
    """Detect filler phrases. Returns (is_rejected, reason)."""
    content_lower = content.lower()
    for phrase in _FILLER_PHRASES:
        if phrase in content_lower:
            return True, f"filler_phrase:{phrase[:30]}"
    return False, ""


def guard_package(content: str) -> tuple[bool, str]:
    """Check for toxicity/severity. Returns (is_rejected, reason)."""
    for pattern, description, severity in _TOXIC_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True, f"toxicity:{description} (severity={severity})"
    return False, ""


def guard_critique(content: str) -> tuple[bool, str]:
    """Detect repetition patterns. Returns (is_rejected, reason)."""
    # >10 consecutive same characters
    if re.search(r"(.)\1{10,}", content):
        return True, "repetition:>10_same_char"

    # >50% caps
    if content:
        caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
        if caps_ratio > 0.50:
            return True, f"repetition:caps_{caps_ratio:.0%}"

    # Same word >5 times in short span
    words = content.split()
    if len(words) > 20:
        word_counts: dict[str, int] = {}
        for w in words:
            word_counts[w] = word_counts.get(w, 0) + 1
        for w, count in word_counts.items():
            if count > 5 and len(w) >= 2:
                return True, f"repetition:word '{w}' x{count}"

    return False, ""


async def guard_confidence(content: str, query: str) -> tuple[Verdict, float, str]:
    """LLM-powered grounding check. Returns (verdict, score, reason).

    Guard 4 — only called when content passes guards 1-3 but score is borderline.
    Uses existing llm_client.chat() for LLM grounding verification.
    """
    t0 = time.perf_counter()

    prompt = (
        "You are a content quality reviewer for an AI assistant.\n\n"
        f"USER QUERY: {query[:500]}\n\n"
        f"RESPONSE TO EVALUATE: {content[:2000]}\n\n"
        "Evaluate whether the response is relevant and grounded to the user's query.\n"
        "Score criteria:\n"
        "  1.0 = directly answers the query with specific, actionable content\n"
        "  0.7-0.99 = mostly relevant, minor gaps\n"
        "  0.3-0.69 = generic, vague, partially off-topic\n"
        "  0.0-0.29 = completely off-topic, generic blog noise, or spam\n\n"
        'Respond with JSON only: {"score": <float>, "verdict": "PASS"|"REJECT"|"NEEDS_IMPROVEMENT", "reason": "<brief reason>"}'
    )

    try:
        # Import here to avoid circular imports
        from llm_client import chat

        response, _ = await chat(
            task=prompt,
            agent_key="general",
            model_override="minimax-coding-plan/MiniMax-M3",
            run_post_hooks=False,
        )

        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            parsed = json.loads(json_match.group())
            score = float(parsed.get("score", 0.5))
            verdict_str = str(parsed.get("verdict", "NEEDS_IMPROVEMENT")).upper()
            reason = str(parsed.get("reason", "no reason provided"))
        else:
            score = 0.5
            verdict_str = "NEEDS_IMPROVEMENT"
            reason = f"could not parse LLM response: {response[:100]}"

    except (json.JSONDecodeError, ValueError, TypeError, ImportError) as e:
        logger.warning("guard_confidence LLM call failed: %s", e)
        score = 0.5
        verdict_str = "NEEDS_IMPROVEMENT"
        reason = f"guard_confidence error: {e}"

    # Normalize verdict
    if verdict_str not in ("PASS", "REJECT", "NEEDS_IMPROVEMENT"):
        verdict_str = "NEEDS_IMPROVEMENT"

    # Apply thresholds
    if (verdict_str == "PASS" and score < 0.7) or (verdict_str == "REJECT" and score >= 0.3):
        verdict_str = "NEEDS_IMPROVEMENT"
    elif verdict_str not in ("PASS", "REJECT") and score >= 0.7:
        verdict_str = "PASS"
    elif verdict_str not in ("PASS", "REJECT") and score < 0.3:
        verdict_str = "REJECT"

    latency_ms = (time.perf_counter() - t0) * 1000
    logger.debug("guard_confidence completed in %.1fms: %s %.2f", latency_ms, verdict_str, score)

    return Verdict(verdict_str), score, reason  # type: ignore[arg-type]


# ── Main pipeline ──────────────────────────────────────────────────────────────


async def run_quality_gate(content: str, query: str = "") -> QualityResult:
    """Run full 4-guard quality pipeline.

    Args:
        content: The LLM response to evaluate.
        query: The original user query (for grounding check).

    Returns:
        QualityResult with verdict, score, reason, and guard_triggered.
    """
    t0 = time.perf_counter()

    # Guard 1: FormatGuard — filler phrases
    rejected, reason = guard_format(content)
    if rejected:
        result = _make_result("REJECT", 0.0, reason, "format", t0)
        _update_stats(result)
        return result

    # Guard 2: PackageGuard — toxicity
    rejected, reason = guard_package(content)
    if rejected:
        result = _make_result("REJECT", 0.0, reason, "package", t0)
        _update_stats(result)
        return result

    # Guard 3: CritiqueGuard — repetition
    rejected, reason = guard_critique(content)
    if rejected:
        result = _make_result("REJECT", 0.0, reason, "critique", t0)
        _update_stats(result)
        return result

    # Score based on heuristics (guards 1-3 passed)
    score = 0.8  # base score after passing heuristic guards

    # Small content penalty
    if len(content) < 30:
        score -= 0.2
        result = _make_result("NEEDS_IMPROVEMENT", score, "content_too_short", "critique", t0)
        _update_stats(result)
        return result

    # Content length bonus
    if len(content) > 200:
        score += 0.1
    if len(content) > 500:
        score += 0.1

    score = max(0.0, min(1.0, score))

    # Guard 4: ConfidenceGuard — LLM grounding for borderline cases
    if 0.4 <= score <= 0.7:
        verdict, llm_score, llm_reason = await guard_confidence(content, query)
        if verdict == "REJECT":
            result = _make_result("REJECT", llm_score, f"grounding_fail:{llm_reason}", "confidence", t0)
            _update_stats(result)
            return result
        if verdict == "PASS":
            result = _make_result("PASS", llm_score, f"grounding_pass:{llm_reason}", "confidence", t0)
            _update_stats(result)
            return result
        # NEEDS_IMPROVEMENT — continue with LLM score
        score = llm_score

    # Final verdict
    if score >= 0.7:
        verdict: Verdict = "PASS"
        reason_str = "quality_pass"
    elif score < 0.3:
        verdict = "REJECT"
        reason_str = "quality_fail"
    else:
        verdict = "NEEDS_IMPROVEMENT"
        reason_str = "quality_borderline"

    result = _make_result(verdict, score, reason_str, None, t0)
    _update_stats(result)
    return result


# ── Quarantine operations ──────────────────────────────────────────────────────


async def quarantine_response(
    content: str,
    query: str,
    result: QualityResult,
) -> Path:
    """Write rejected content to quarantine with metadata."""
    _QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_query = re.sub(r"[^\w\-_.]", "_", query.replace("/", "_")[:50])
    filename = f"slop_{safe_query}_{timestamp}.txt"
    dest_path = _QUARANTINE_DIR / filename

    metadata = {
        "query": query[:200],
        "reason": result.reason,
        "verdict": result.verdict,
        "score": result.score,
        "guard": result.guard_triggered,
        "quarantined_at": datetime.now().isoformat(),
    }

    frontmatter = json.dumps(metadata, indent=2)
    file_content = f"---\n{frontmatter}\n---\n\n{content}"

    await asyncio.to_thread(lambda: Path(dest_path).write_text(file_content))
    await _append_rejection_log(metadata)

    logger.info("Quarantined slop response: %s → %s", query[:30], dest_path)
    return dest_path


async def _append_rejection_log(metadata: dict) -> None:
    """Append a rejection entry to the global rejections log."""
    _ANTI_SLOP_DIR.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if _REJECTIONS_LOG.exists():
        try:
            text = await asyncio.to_thread(lambda: _REJECTIONS_LOG.read_text())
            existing = json.loads(text) if text.strip() else []
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read rejections log: %s", e)
            existing = []

    existing.append(metadata)

    text = json.dumps(existing, indent=2)
    await asyncio.to_thread(lambda: _REJECTIONS_LOG.write_text(text))


# ── SlopStats ──────────────────────────────────────────────────────────────────


@dataclass
class SlopStats:
    """Statistics for anti-slop monitoring."""

    total_calls: int = 0
    total_rejects: int = 0
    total_passes: int = 0
    total_needs_improvement: int = 0
    guard_format_rejects: int = 0
    guard_package_rejects: int = 0
    guard_critique_rejects: int = 0
    guard_confidence_rejects: int = 0
    avg_latency_ms: float = 0.0
    last_reset: str = field(default_factory=lambda: datetime.now().isoformat())

    def rejection_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_rejects / self.total_calls

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_rejects": self.total_rejects,
            "total_passes": self.total_passes,
            "total_needs_improvement": self.total_needs_improvement,
            "rejection_rate": f"{self.rejection_rate():.1%}",
            "guard_format_rejects": self.guard_format_rejects,
            "guard_package_rejects": self.guard_package_rejects,
            "guard_critique_rejects": self.guard_critique_rejects,
            "guard_confidence_rejects": self.guard_confidence_rejects,
            "avg_latency_ms": f"{self.avg_latency_ms:.1f}",
            "last_reset": self.last_reset,
        }


# Global stats instance
_slop_stats = SlopStats()


def get_slop_stats() -> SlopStats:
    """Get the global slop statistics instance."""
    return _slop_stats


def reset_slop_stats() -> None:
    """Reset all slop statistics to zero."""
    global _slop_stats
    _slop_stats = SlopStats()


def _update_stats(result: QualityResult) -> None:
    """Update global stats with a new result."""
    global _slop_stats
    _slop_stats.total_calls += 1
    _slop_stats.total_passes += 1 if result.verdict == "PASS" else 0
    _slop_stats.total_rejects += 1 if result.verdict == "REJECT" else 0
    _slop_stats.total_needs_improvement += 1 if result.verdict == "NEEDS_IMPROVEMENT" else 0

    if result.guard_triggered == "format":
        _slop_stats.guard_format_rejects += 1
    elif result.guard_triggered == "package":
        _slop_stats.guard_package_rejects += 1
    elif result.guard_triggered == "critique":
        _slop_stats.guard_critique_rejects += 1
    elif result.guard_triggered == "confidence":
        _slop_stats.guard_confidence_rejects += 1

    # Running average for latency
    n = _slop_stats.total_calls
    _slop_stats.avg_latency_ms = ((n - 1) * _slop_stats.avg_latency_ms + result.latency_ms) / n
