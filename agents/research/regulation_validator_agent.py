"""WAJAR_WATCH — Regulation Validator Agent.

Cross-validates extracted constants against secondary sources.
This agent is the SKEPTIC — its job is to find reasons NOT to trust an extraction.

Agent key: uses "debug" model (zai/glm-4 — analytical precision, GPQA Diamond 85.7%)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime

from tools.wajar_watch.constants import MAX_EXPECTED_CAP_DELTA, WatchedConstant
from tools.wajar_watch.pdf_extractor import ExtractedConstant

logger = logging.getLogger(__name__)

# ── Regex patterns for regulation number format validation ────────────────────
RE_PP = re.compile(r"PP\s*(?:No\.?\s*)?\d+(?:/| Tahun )\d{4}", re.IGNORECASE)
RE_PMK = re.compile(r"PMK\s*\d+/PMK\.\d+/\d{4}", re.IGNORECASE)
RE_PERPRES = re.compile(r"Perpres\s*(?:No\.?\s*)?\d+(?:/| Tahun )\d{4}", re.IGNORECASE)
RE_SE = re.compile(r"[A-Z]/\d+/\d{6}", re.IGNORECASE)
RE_UU = re.compile(r"UU\s*(?:No\.?\s*)?\d+(?:/| Tahun )\d{4}", re.IGNORECASE)

REGULATION_PATTERNS = [RE_PP, RE_PMK, RE_PERPRES, RE_SE, RE_UU]

FORMULA_TOLERANCE = 2000  # Rp2000


@dataclass
class ValidationResult:
    recommendation: str  # "approve" | "flag" | "reject"
    formula_check: bool | None = None  # None if formula not applicable
    date_check: bool = True
    format_check: bool = True
    delta_check: bool = True
    reasons: list[str] = field(default_factory=list)


def _check_date(effective_date_str: str) -> tuple[bool, str | None]:
    """Validate effective date is reasonable."""
    if effective_date_str in ("unknown", "", None):
        return False, "Effective date unknown"
    try:
        d = datetime.strptime(effective_date_str, "%Y-%m-%d").date()
    except ValueError:
        return False, f"Unparseable date: {effective_date_str}"

    earliest = date(2020, 1, 1)
    from datetime import timedelta
    latest = date.today() + timedelta(days=365)

    if d < earliest:
        return False, f"Date {d} is before 2020 — too old"
    if d > latest:
        return False, f"Date {d} is more than 1 year in the future"
    return True, None


def _check_format(legal_basis: str) -> tuple[bool, str | None]:
    """Validate regulation number matches expected pattern."""
    if not legal_basis:
        return False, "No legal basis provided"

    for pattern in REGULATION_PATTERNS:
        if pattern.search(legal_basis):
            return True, None

    return False, f"Legal basis '{legal_basis}' doesn't match any known format (PP/PMK/Perpres/SE/UU)"


def _check_formula(
    watched: WatchedConstant,
    proposed_value: float,
    pdb_growth_rate: float | None,
) -> tuple[bool | None, str | None]:
    """Verify formula if applicable."""
    if not watched.formula or pdb_growth_rate is None:
        return None, None

    expected = watched.current_value * (1 + pdb_growth_rate)
    matches = abs(expected - proposed_value) <= FORMULA_TOLERANCE
    detail = (
        f"{watched.current_value:,.0f} × (1 + {pdb_growth_rate:.4f}) = {expected:,.0f} "
        f"vs proposed {proposed_value:,.0f}"
    )
    if not matches:
        return False, f"Formula mismatch: {detail}"
    return True, None


def _check_delta(
    watched: WatchedConstant, proposed_value: float
) -> tuple[bool, str | None]:
    """Validate delta is within expected bounds."""
    if watched.current_value == 0:
        return True, None

    delta = proposed_value - watched.current_value
    delta_pct = abs(delta) / watched.current_value

    if watched.change_type == "cap":
        if delta_pct < 0.01:
            return False, f"Delta {delta_pct:.1%} is suspiciously small for a cap change"
        if delta_pct > MAX_EXPECTED_CAP_DELTA:
            return False, f"Delta {delta_pct:.1%} exceeds expected max {MAX_EXPECTED_CAP_DELTA:.0%}"
        if delta < 0:
            return False, f"Cap DECREASED by {abs(delta):,.0f} — highly unusual"
        return True, None
    elif watched.change_type == "rate":
        # ANY rate change is suspicious
        return False, f"Rate change detected ({watched.current_value} → {proposed_value}) — requires manual verification"
    elif watched.change_type in ("fixed", "bracket"):
        # Any change to fixed/bracket = reject
        return False, f"Fixed/bracket value changed — this requires a major regulation amendment"
    return True, None


async def validate_extraction(
    watched: WatchedConstant,
    candidate: ExtractedConstant,
    pdb_growth_rate: float | None = None,
) -> ValidationResult:
    """Run all 4 validation checks and determine recommendation."""
    result = ValidationResult(recommendation="approve")

    # 1. Date check
    result.date_check, date_reason = _check_date(candidate.effective_date)
    if date_reason:
        result.reasons.append(f"Date: {date_reason}")

    # 2. Format check
    result.format_check, format_reason = _check_format(candidate.legal_basis)
    if format_reason:
        result.reasons.append(f"Format: {format_reason}")

    # 3. Formula check
    result.formula_check, formula_reason = _check_formula(
        watched, candidate.value, pdb_growth_rate
    )
    if formula_reason:
        result.reasons.append(f"Formula: {formula_reason}")

    # 4. Delta check
    result.delta_check, delta_reason = _check_delta(watched, candidate.value)
    if delta_reason:
        result.reasons.append(f"Delta: {delta_reason}")

    # Determine recommendation
    checks = [result.date_check, result.format_check, result.delta_check]
    if result.formula_check is not None:
        checks.append(result.formula_check)

    failed = [c for c in checks if c is False]

    if not failed:
        result.recommendation = "approve"
    elif watched.change_type in ("fixed", "bracket"):
        result.recommendation = "reject"
    elif len(failed) >= 2:
        result.recommendation = "reject"
    else:
        result.recommendation = "flag"

    # Override: delta > MAX means reject regardless
    delta_pct = abs(candidate.value - watched.current_value) / watched.current_value if watched.current_value else 0
    if delta_pct > MAX_EXPECTED_CAP_DELTA:
        result.recommendation = "reject"
        if "exceeds expected max" not in str(result.reasons):
            result.reasons.append(f"Delta {delta_pct:.1%} exceeds max allowed")

    logger.info(
        "Validation for %s: %s (%d issues: %s)",
        watched.key, result.recommendation, len(result.reasons),
        "; ".join(result.reasons) if result.reasons else "none",
    )
    return result
