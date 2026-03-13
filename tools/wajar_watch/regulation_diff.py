"""WAJAR_WATCH — regulation_diff: generate minimal TypeScript diffs for regulation updates."""
from __future__ import annotations

import base64
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from tools.wajar_watch.confidence_scorer import ConfidenceResult
from tools.wajar_watch.constants import (
    CEKWAJAR_BASE_BRANCH,
    CEKWAJAR_GITHUB_OWNER,
    CEKWAJAR_GITHUB_REPO,
    CEKWAJAR_REGULATIONS_FILE,
    WatchedConstant,
)

logger = logging.getLogger(__name__)


@dataclass
class RegulationDiff:
    watched_key: str
    file_path: str  # always "lib/regulations.ts"
    old_content: str
    new_content: str
    old_value_str: str  # specific line that changed
    new_value_str: str  # replacement line
    commit_message: str
    pr_title: str
    pr_body: str
    branch_name: str
    current_file_sha: str  # GitHub blob SHA for update API


def _format_ts_number(value: float) -> str:
    """Format a number for TypeScript with underscores for readability.

    11086300 → 11_086_300
    0.01 → 0.01
    54000000 → 54_000_000
    """
    if isinstance(value, float) and value < 1:
        return str(value)
    int_val = int(value)
    s = str(int_val)
    # Add underscores every 3 digits from the right
    parts = []
    while s:
        parts.append(s[-3:])
        s = s[:-3]
    return "_".join(reversed(parts))


async def _fetch_file_from_github(
    file_path: str,
) -> tuple[str, str]:
    """Fetch a file from the slip_cekwajar_id repo.

    Returns (content, sha).
    """
    token = os.environ["CEKWAJAR_GITHUB_TOKEN"]
    url = (
        f"https://api.github.com/repos/{CEKWAJAR_GITHUB_OWNER}/{CEKWAJAR_GITHUB_REPO}"
        f"/contents/{file_path}?ref={CEKWAJAR_BASE_BRANCH}"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    content = base64.b64decode(data["content"]).decode("utf-8")
    sha = data["sha"]
    return content, sha


def _find_and_replace_value(
    content: str,
    watched: WatchedConstant,
    new_value: float,
) -> tuple[str, str, str]:
    """Find the line with the constant value and replace it.

    Returns (new_content, old_line, new_line).
    Raises ValueError if not exactly 1 line changes.
    """
    lines = content.split("\n")
    old_value_formatted = _format_ts_number(watched.current_value)
    new_value_formatted = _format_ts_number(new_value)

    # Also try without underscores
    old_value_plain = str(int(watched.current_value)) if watched.current_value >= 1 else str(watched.current_value)

    matched_indices = []
    for i, line in enumerate(lines):
        if old_value_formatted in line or old_value_plain in line:
            # Additional context check: the line should relate to the watched constant
            matched_indices.append(i)

    if not matched_indices:
        raise ValueError(
            f"Could not find value {old_value_formatted} (or {old_value_plain}) "
            f"in {CEKWAJAR_REGULATIONS_FILE} for key {watched.key}"
        )

    # Pick the best match — prefer lines that mention the code_path context
    best_idx = matched_indices[0]
    code_hints = watched.code_path.split(".")
    for idx in matched_indices:
        line_lower = lines[idx].lower()
        if any(hint.lower() in line_lower for hint in code_hints):
            best_idx = idx
            break

    old_line = lines[best_idx]
    new_line = old_line.replace(old_value_formatted, new_value_formatted)
    if new_line == old_line:
        new_line = old_line.replace(old_value_plain, new_value_formatted)

    new_lines = lines.copy()
    new_lines[best_idx] = new_line
    new_content = "\n".join(new_lines)

    # Safety Rule 6: verify exactly 1 line changed
    changed_lines = [
        i for i, (a, b) in enumerate(zip(lines, new_lines)) if a != b
    ]
    if len(changed_lines) != 1:
        raise ValueError(
            f"Expected 1 changed line, got {len(changed_lines)}. "
            f"Refusing to create PR for {watched.key}."
        )

    return new_content, old_line.strip(), new_line.strip()


def _build_commit_message(
    watched: WatchedConstant, result: ConfidenceResult
) -> str:
    formula_line = f"\n{result.formula_detail}" if result.formula_detail else ""
    verbatim = result.verbatim_quotes[0] if result.verbatim_quotes else "see PR body"

    return (
        f"auto(regulation): update {watched.key} "
        f"{watched.current_value:,.0f} → {result.proposed_value:,.0f}\n\n"
        f"Source: {result.legal_basis}\n"
        f"URL: {result.legal_basis_url}\n"
        f"Effective: {watched.effective_date}\n"
        f"Previous value: {watched.current_value:,}\n"
        f"New value: {result.proposed_value:,.0f}"
        f"{formula_line}\n\n"
        f"Extracted by: WAJAR_WATCH pipeline (Babas Swarms legal_compliance agent)\n"
        f"Confidence: {result.confidence} ({result.sources_agreeing}/{result.sources_total} sources agree)\n"
        f'Verbatim: "{verbatim}"\n\n'
        f"🤖 Auto-generated. Auto-merge if CI passes."
    )


def _build_pr_body(watched: WatchedConstant, result: ConfidenceResult) -> str:
    verbatim = result.verbatim_quotes[0] if result.verbatim_quotes else "See source URL"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    return (
        f"## 🤖 Auto-Regulation Update\n\n"
        f"| Field | Value |\n"
        f"|---|---|\n"
        f"| **Constant** | `{watched.code_path}` |\n"
        f"| **Old Value** | `Rp{watched.current_value:,}` |\n"
        f"| **New Value** | `Rp{result.proposed_value:,.0f}` |\n"
        f"| **Change** | +{result.delta_pct:.2f}% |\n"
        f"| **Effective** | {watched.effective_date} |\n"
        f"| **Source** | [{result.legal_basis}]({result.legal_basis_url}) |\n"
        f"| **Confidence** | {result.confidence} ({result.sources_agreeing}/{result.sources_total} sources) |\n"
        f"| **Formula** | {result.formula_detail or 'N/A'} |\n\n"
        f"### Legal Basis\n"
        f"> {verbatim}\n\n"
        f"### What This Affects\n"
        f"Every payslip in `slip_cekwajar_id` where gross salary exceeds the old cap "
        f"will now calculate BPJS JP using the updated cap from {watched.effective_date}.\n\n"
        f"### Auto-Merge Policy\n"
        f"- ✅ Will auto-merge if ALL CI tests pass\n"
        f"- ❌ Will NOT auto-merge if any test fails (human review required)\n"
        f"- Override: `WAJAR_WATCH_AUTO_MERGE_ENABLED=false` blocks auto-merge regardless\n\n"
        f"---\n"
        f"*Generated by WAJAR_WATCH | Babas Swarms × cekwajar.id | {now} UTC*"
    )


async def generate_diff(
    watched: WatchedConstant,
    result: ConfidenceResult,
) -> RegulationDiff | None:
    """Generate a minimal TypeScript diff for the regulation update.

    Returns None if the diff cannot be generated (value not found, etc).
    """
    try:
        # Fetch current file
        old_content, file_sha = await _fetch_file_from_github(CEKWAJAR_REGULATIONS_FILE)

        # Generate the replacement
        new_content, old_line, new_line = _find_and_replace_value(
            old_content, watched, result.proposed_value
        )

        now = datetime.now(timezone.utc)
        branch_name = f"auto/wajar-{watched.key}-{now:%Y-%m-%d}"

        return RegulationDiff(
            watched_key=watched.key,
            file_path=CEKWAJAR_REGULATIONS_FILE,
            old_content=old_content,
            new_content=new_content,
            old_value_str=old_line,
            new_value_str=new_line,
            commit_message=_build_commit_message(watched, result),
            pr_title=f"auto(regulation): {watched.key} → {result.proposed_value:,.0f} [{result.confidence}]",
            pr_body=_build_pr_body(watched, result),
            branch_name=branch_name,
            current_file_sha=file_sha,
        )
    except ValueError as e:
        logger.error("Diff generation failed: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error generating diff for %s: %s", watched.key, e)
        return None
