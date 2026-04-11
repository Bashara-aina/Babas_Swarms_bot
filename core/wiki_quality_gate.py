"""Wiki quality gate — heuristic + LLM evaluation before wiki writes.

Architecture:
  fast_gate  → heuristic pass (<5ms, no I/O)
  deep_gate  → LLM pass (async, for NEEDS_IMPROVEMENT)
  evaluate_before_write → orchestrates fast → deep flow
  quarantine/restore/flush → content isolation for rejected writes
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from llm_client import chat

logger = logging.getLogger(__name__)

# ── Directory constants ────────────────────────────────────────────────────────

WIKI_DIR = Path("/home/newadmin/swarm-bot/.wiki")
QUARANTINE_DIR = WIKI_DIR / "_quarantine"
_REJECTIONS_LOG = Path.home() / ".legion" / "wiki_rejections.json"

# ── EvaluationResult ───────────────────────────────────────────────────────────

Verdict = Literal["PASS", "REJECT", "NEEDS_IMPROVEMENT"]
Gate = Literal["fast", "deep"]


@dataclass
class EvaluationResult:
    """Result of a wiki quality gate evaluation."""

    verdict: Verdict
    score: float
    reason: str
    gate: Gate
    latency_ms: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be 0.0-1.0, got {self.score}")


# ── Filler phrases for deduction ──────────────────────────────────────────────

_FILLER_PHRASES = frozenset(
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
    ]
)

# ── fast_gate ─────────────────────────────────────────────────────────────────


def fast_gate(content: str, path: str) -> EvaluationResult:
    """Heuristic wiki quality check — runs in <5ms, no I/O."""
    t0 = time.perf_counter()

    # Hard REJECT rules
    if len(content) < 50:
        return _result("REJECT", 0.0, "content too short (<50 chars)", "fast", t0)

    if "../" in path:
        return _result("REJECT", 0.0, "path traversal attempt detected", "fast", t0)

    # Spam detection
    caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
    if caps_ratio > 0.70:
        return _result("REJECT", 0.0, f"spam: {caps_ratio:.0%} caps (>70%)", "fast", t0)

    if re.search(r"(.)\1{10,}", content):
        return _result("REJECT", 0.0, "spam: >10 consecutive same chars", "fast", t0)

    # Score contributions
    score = 0.0
    reasons: list[str] = []

    if re.search(r"LEGION RULE", content, re.IGNORECASE):
        score += 0.15
        reasons.append("has_legion_rule")

    if re.search(r"https?://|Source:", content):
        score += 0.05
        reasons.append("has_source_url")

    words = content.split()
    if len(words) > 200:
        score += 0.10
        reasons.append("word_count>200")

    if re.search(r"```|`", content):
        score += 0.05
        reasons.append("has_code")

    if re.search(r"Applied to:", content):
        score += 0.10
        reasons.append("has_applied_to")

    # Deductions
    content_lower = content.lower()
    for phrase in _FILLER_PHRASES:
        if phrase in content_lower:
            score -= 0.05
            reasons.append(f"filler:{phrase[:20]}")

    if re.search(r"best practices", content_lower):
        score -= 0.05
        reasons.append("generic_best_practices")

    if re.search(r"\bit depends\b", content_lower):
        score -= 0.05
        reasons.append("vague_it_depends")

    # Clamp score
    score = max(0.0, min(1.0, score))

    # Verdict
    if score >= 0.7:
        verdict: Verdict = "PASS"
        reason = f"PASS (score={score:.2f}): {', '.join(reasons)}"
    elif score < 0.3:
        verdict = "REJECT"
        reason = f"REJECT (score={score:.2f}): {', '.join(reasons)}"
    else:
        verdict = "NEEDS_IMPROVEMENT"
        reason = f"NEEDS_IMPROVEMENT (score={score:.2f}): {', '.join(reasons)}"

    return _result(verdict, score, reason, "fast", t0)


def _result(verdict: Verdict, score: float, reason: str, gate: Gate, t0: float) -> EvaluationResult:
    latency_ms = (time.perf_counter() - t0) * 1000
    return EvaluationResult(verdict=verdict, score=score, reason=reason, gate=gate, latency_ms=latency_ms)


# ── deep_gate ──────────────────────────────────────────────────────────────────


async def deep_gate(content: str, path: str) -> EvaluationResult:
    """LLM-powered wiki quality check — for NEEDS_IMPROVEMENT cases."""
    t0 = time.perf_counter()

    user_prompt = (
        f"Evaluate this wiki content for page: {path}\n\n"
        f"--- CONTENT ---\n{content[:3000]}\n"
        f"--- END CONTENT ---\n\n"
        "Score criteria:\n"
        "  1.0 = perfect Legion-specific actionable knowledge\n"
        "  0.7-0.99 = useful, specific, applicable\n"
        "  0.3-0.69 = vague, generic, needs more specificity\n"
        "  0.0-0.29 = generic blog noise /spam /useless\n\n"
        "Respond with JSON only."
    )

    try:
        response, _ = await chat(
            task=user_prompt,
            agent_key="general",
            model_override="minimax/MiniMax-M2.7",
            run_post_hooks=False,
        )
        # Parse JSON response
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

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning("deep_gate LLM call failed: %s", e)
        score = 0.5
        verdict_str = "NEEDS_IMPROVEMENT"
        reason = f"deep_gate error: {e}"

    # Normalize verdict
    if verdict_str not in ("PASS", "REJECT", "NEEDS_IMPROVEMENT"):
        verdict_str = "NEEDS_IMPROVEMENT"

    verdict: Verdict = verdict_str  # type: ignore

    # Apply thresholds
    if verdict == "PASS" and score < 0.7:
        verdict = "NEEDS_IMPROVEMENT"
    elif verdict == "REJECT" and score >= 0.3:
        verdict = "NEEDS_IMPROVEMENT"
    elif verdict not in ("PASS", "REJECT") and score >= 0.7:
        verdict = "PASS"
    elif verdict not in ("PASS", "REJECT") and score < 0.3:
        verdict = "REJECT"

    latency_ms = (time.perf_counter() - t0) * 1000
    return EvaluationResult(verdict=verdict, score=score, reason=reason, gate="deep", latency_ms=latency_ms)


# ── evaluate_before_write ──────────────────────────────────────────────────────


async def evaluate_before_write(page_path: str, content: str) -> EvaluationResult:
    """Orchestrate fast → deep evaluation flow."""
    fast_result = fast_gate(content, page_path)

    if fast_result.verdict == "REJECT":
        return fast_result

    if fast_result.verdict == "NEEDS_IMPROVEMENT":
        return await deep_gate(content, page_path)

    # PASS — return fast result
    return fast_result


# ── Quarantine operations ──────────────────────────────────────────────────────


async def quarantine_content(page_path: str, content: str, reason: str, score: float) -> Path:
    """Write rejected content to quarantine with metadata frontmatter."""
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    # Sanitize page_path for filename
    safe_name = re.sub(r"[^\w\-_.]", "_", page_path.replace("/", "_"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{safe_name}_{timestamp}.md"
    dest_path = QUARANTINE_DIR / filename

    metadata = {
        "page_path": page_path,
        "reason": reason,
        "score": score,
        "quarantined_at": datetime.now().isoformat(),
    }

    frontmatter = json.dumps(metadata, indent=2)
    file_content = f"---\n{frontmatter}\n---\n\n{content}"

    await asyncio.to_thread(lambda: Path(dest_path).write_text(file_content))

    # Log to rejections file
    await _append_rejection_log(metadata)

    logger.info("Quarantined wiki content: %s → %s", page_path, dest_path)
    return dest_path


async def _append_rejection_log(metadata: dict) -> None:
    """Append a rejection entry to the global rejections log."""
    _REJECTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)

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


async def restore_from_quarantine(page_path: str) -> bool:
    """Move content back from quarantine and re-evaluate."""
    if not QUARANTINE_DIR.exists():
        return False

    # Find matching quarantine file
    safe_name = re.sub(r"[^\w\-_.]", "_", page_path.replace("/", "_"))
    candidates = list(QUARANTINE_DIR.glob(f"{safe_name}_*.md"))

    if not candidates:
        return False

    # Get most recent
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    content = await asyncio.to_thread(lambda: latest.read_text())

    # Strip frontmatter
    match = re.match(r"---[\s\S]*?---\n\n", content)
    if match:
        content = content[match.end() :]

    # Re-evaluate
    result = await evaluate_before_write(page_path, content)
    return result.verdict == "PASS"


async def flush_quarantine() -> int:
    """Delete all quarantine files. Returns count of deleted files."""
    if not QUARANTINE_DIR.exists():
        return 0

    files = list(QUARANTINE_DIR.glob("*.md"))
    for f in files:
        await asyncio.to_thread(f.unlink)

    logger.info("Flushed %d quarantine files", len(files))
    return len(files)
