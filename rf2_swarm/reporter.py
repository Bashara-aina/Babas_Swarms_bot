"""Report generator — text format + JSON, backward-compatible schema."""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .base_agent import Verdict, AgentResult


def generate_report(
    results: list[AgentResult],
    state: dict[str, Any],
    cycle: int = 0,
) -> str:
    """Generate human-readable text report (same format as monolithic checklist)."""
    lines: list[str] = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"{'=' * 72}")
    lines.append(f"  RF2 SWARM REPORT  —  Cycle #{cycle}  —  {ts}")
    lines.append(f"{'=' * 72}")

    all_checks: list[dict] = []
    for ar in results:
        for c in ar.checks:
            all_checks.append(c.to_dict())
        if ar.error:
            lines.append(f"\n  ⚠ Agent [{ar.agent_name}] error: {ar.error}")

    # Group by category (agent name)
    categories: dict[str, list[dict]] = {}
    for c in all_checks:
        categories.setdefault(c["category"], []).append(c)

    total = len(all_checks)
    passed = sum(1 for c in all_checks if c["verdict"] == Verdict.PASS)
    failed = sum(1 for c in all_checks if c["verdict"] == Verdict.FAIL)
    warned = sum(1 for c in all_checks if c["verdict"] == Verdict.WARN)
    info = sum(1 for c in all_checks if c["verdict"] == Verdict.INFO)
    blocking = sum(1 for c in all_checks if c["verdict"] == Verdict.FAIL and c["blocking"])

    for cat_name in sorted(categories):
        items = categories[cat_name]
        cat_p = sum(1 for r in items if r["verdict"] == Verdict.PASS)
        cat_f = sum(1 for r in items if r["verdict"] == Verdict.FAIL)
        cat_w = sum(1 for r in items if r["verdict"] == Verdict.WARN)
        lines.append(f"\n{'─' * 72}")
        lines.append(f"  {cat_name}  [{cat_p}P {cat_w}W {cat_f}F]")
        lines.append(f"{'─' * 72}")

        for r in items:
            icon = {"PASS": "✓", "FAIL": "✗", "WARN": "▲", "INFO": "•", "SKIP": "−"}.get(r["verdict"], "?")
            block_tag = " [BLOCKING]" if r.get("blocking") else ""
            lines.append(f"  {r['uid']:6s} {icon} {r['verdict']:5s}{block_tag} | {r['desc']}")
            if r.get("detail"):
                lines.append(f"         {r['detail']}")

    # Summary
    lines.append(f"\n{'=' * 72}")
    if blocking > 0:
        blocking_fails = [c for c in all_checks if c["verdict"] == Verdict.FAIL and c["blocking"]]
        lines.append(f"  VERDICT: BLOCKED — {blocking} blocking failure(s)")
        for r in blocking_fails:
            lines.append(f"    - {r['uid']}: {r['desc']} → {r['detail']}")
    elif failed > 0:
        lines.append(f"  VERDICT: DEGRADED — {failed} non-blocking failure(s), {warned} warning(s)")
    elif warned > 5:
        lines.append(f"  VERDICT: ATTENTION — {warned} warning(s) to review")
    else:
        lines.append("  VERDICT: HEALTHY — All checks passing")
    lines.append(f"{'=' * 72}")

    lines.append(f"\nTotals: {total} checks — {passed}P {warned}W {failed}F {info}I | {blocking} blocking")
    return "\n".join(lines)


def write_results(
    results: list[AgentResult],
    state: dict[str, Any],
    json_path: Path,
    report_path: Path,
    cycle: int = 0,
):
    """Write backward-compatible JSON and text report."""
    all_checks: list[dict] = []
    for ar in results:
        for c in ar.checks:
            all_checks.append(c.to_dict())

    total = len(all_checks)
    passed = sum(1 for c in all_checks if c["verdict"] == Verdict.PASS)
    failed = sum(1 for c in all_checks if c["verdict"] == Verdict.FAIL)
    warned = sum(1 for c in all_checks if c["verdict"] == Verdict.WARN)
    info = sum(1 for c in all_checks if c["verdict"] == Verdict.INFO)
    block_count = sum(1 for c in all_checks if c["verdict"] == Verdict.FAIL and c["blocking"])
    summary = (
        "HEALTHY" if block_count == 0 and failed == 0 else
        "BLOCKED" if block_count > 0 else
        "DEGRADED"
    )

    payload = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "pass": passed,
        "warn": warned,
        "fail": failed,
        "info": info,
        "blocking": block_count,
        "gate_passed": state.get("gate_passed", False),
        "epoch": state.get("epoch", 0),
        "max_epochs": state.get("max_epochs", 21),
        "results": all_checks,
        "summary": summary,
    }

    json_path.write_text(json.dumps(payload, indent=2, default=str))
    report = generate_report(results, state, cycle)
    report_path.write_text(report)
