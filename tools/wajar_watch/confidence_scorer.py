"""WAJAR_WATCH — confidence_scorer: multi-rule scoring with safety enforcement."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from tools.wajar_watch.constants import (
    CONFIDENCE_BLOCK,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    MAX_EXPECTED_CAP_DELTA,
    NEVER_AUTO_APPLY_KEYS,
    NOISE_THRESHOLD,
    ROUTE_ALERT_HUMAN,
    ROUTE_ALERT_ONLY,
    ROUTE_AUTO_APPLY,
    ROUTE_BLOCK,
    ROUTE_SKIP,
    WatchedConstant,
)
from tools.wajar_watch.pdf_extractor import ExtractedConstant

logger = logging.getLogger(__name__)

SOURCE_TOLERANCE = 500  # Rp500 tolerance for source "agreement"
FORMULA_TOLERANCE = 2000  # Rp2000 tolerance for formula verification


@dataclass
class ConfidenceResult:
    watched_key: str
    proposed_value: float
    current_value: float
    delta: float
    delta_pct: float
    confidence: str
    routing: str
    sources_agreeing: int
    sources_total: int
    legal_basis: str
    legal_basis_url: str
    verbatim_quotes: list[str] = field(default_factory=list)
    formula_verified: bool = False
    formula_detail: str | None = None
    block_reason: str | None = None


def score_confidence(
    watched: WatchedConstant,
    candidates: list[ExtractedConstant],
    pdb_growth_rate: float | None = None,
) -> ConfidenceResult:
    """Score confidence for a proposed regulation change.

    Implements 7 rules in strict order. See SPEC-E for full documentation.
    """
    # Pick the best proposed value from candidates
    proposed_value = _pick_best_value(candidates)
    delta = proposed_value - watched.current_value
    delta_pct = abs(delta) / watched.current_value if watched.current_value else 0
    sources_total = len(candidates)

    # Collect verbatim quotes (up to 3)
    verbatim_quotes = [c.verbatim_quote for c in candidates if c.verbatim_quote][:3]

    # Best legal basis from highest-confidence candidate
    best = max(candidates, key=lambda c: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(c.confidence, 0))
    legal_basis = best.legal_basis or watched.legal_basis
    legal_basis_url = watched.legal_basis_url

    # Build base result
    result = ConfidenceResult(
        watched_key=watched.key,
        proposed_value=proposed_value,
        current_value=watched.current_value,
        delta=delta,
        delta_pct=delta_pct * 100,  # store as percentage
        confidence="",
        routing="",
        sources_agreeing=0,
        sources_total=sources_total,
        legal_basis=legal_basis,
        legal_basis_url=legal_basis_url,
        verbatim_quotes=verbatim_quotes,
    )

    # ── RULE 0: Defense in depth — hardcoded blocklist ────────────────────────
    if watched.key in NEVER_AUTO_APPLY_KEYS:
        result.confidence = CONFIDENCE_BLOCK
        result.routing = ROUTE_BLOCK
        result.block_reason = f"Hardcoded safety block: {watched.key} is a rate/bracket"
        logger.info("RULE 0: BLOCK %s (in NEVER_AUTO_APPLY_KEYS)", watched.key)
        return result

    # ── RULE 1: change_type safety ────────────────────────────────────────────
    if watched.change_type in ("rate", "bracket", "fixed"):
        result.confidence = CONFIDENCE_BLOCK
        result.routing = ROUTE_BLOCK
        result.block_reason = "Rate/bracket/fixed constants require manual legal review"
        logger.info("RULE 1: BLOCK %s (change_type=%s)", watched.key, watched.change_type)
        return result

    # ── RULE 2: Noise filter ─────────────────────────────────────────────────
    if delta_pct < NOISE_THRESHOLD:
        result.confidence = "skip"
        result.routing = ROUTE_SKIP
        logger.info("RULE 2: SKIP %s (delta %.4f%% below noise threshold)", watched.key, delta_pct * 100)
        return result

    # ── RULE 3: Cap decrease check ───────────────────────────────────────────
    if watched.change_type == "cap" and delta < 0:
        result.confidence = CONFIDENCE_MEDIUM
        result.routing = ROUTE_ALERT_HUMAN
        result.block_reason = "Cap DECREASE detected — unusual, requires human review"
        logger.info("RULE 3: ALERT %s (cap decrease: %s → %s)", watched.key, watched.current_value, proposed_value)
        return result

    # ── RULE 4: Suspiciously large jump ──────────────────────────────────────
    if watched.change_type == "cap" and delta_pct > MAX_EXPECTED_CAP_DELTA:
        result.confidence = CONFIDENCE_MEDIUM
        result.routing = ROUTE_ALERT_HUMAN
        result.block_reason = f"Delta {delta_pct:.1%} exceeds expected max {MAX_EXPECTED_CAP_DELTA:.0%}"
        logger.info("RULE 4: ALERT %s (delta %.1f%% too large)", watched.key, delta_pct * 100)
        return result

    # ── RULE 5: Formula verification ─────────────────────────────────────────
    formula_verified = False
    formula_detail = None
    if watched.formula and pdb_growth_rate is not None:
        expected = watched.current_value * (1 + pdb_growth_rate)
        formula_verified = abs(expected - proposed_value) <= FORMULA_TOLERANCE
        formula_detail = (
            f"{watched.current_value:,.0f} × (1 + {pdb_growth_rate:.4f}) = {expected:,.0f} "
            f"{'≈' if formula_verified else '≠'} {proposed_value:,.0f} "
            f"{'✅' if formula_verified else '⚠️'}"
        )
        logger.info("RULE 5: Formula check for %s: %s", watched.key, formula_detail)
    result.formula_verified = formula_verified
    result.formula_detail = formula_detail

    # ── RULE 6: Source counting ──────────────────────────────────────────────
    sources_agreeing = 0
    for c in candidates:
        if c.confidence in ("HIGH", "MEDIUM"):
            if abs(c.value - proposed_value) <= SOURCE_TOLERANCE:
                sources_agreeing += 1
    result.sources_agreeing = sources_agreeing

    # ── RULE 7: Final confidence assignment ──────────────────────────────────
    if sources_agreeing >= watched.sources_required:
        result.confidence = CONFIDENCE_HIGH
        result.routing = ROUTE_AUTO_APPLY
    elif sources_agreeing == watched.sources_required - 1:
        result.confidence = CONFIDENCE_MEDIUM
        result.routing = ROUTE_ALERT_HUMAN
    else:
        result.confidence = CONFIDENCE_LOW
        result.routing = ROUTE_ALERT_ONLY

    logger.info(
        "RULE 7: %s → %s (sources=%d/%d, required=%d)",
        watched.key, result.confidence, sources_agreeing, sources_total, watched.sources_required,
    )
    return result


def _pick_best_value(candidates: list[ExtractedConstant]) -> float:
    """Pick the best proposed value from candidates.

    Strategy: highest confidence wins, break ties by most recent effective_date.
    """
    if not candidates:
        return 0.0

    conf_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    sorted_candidates = sorted(
        candidates,
        key=lambda c: (conf_order.get(c.confidence, 0), c.effective_date or ""),
        reverse=True,
    )
    return sorted_candidates[0].value
