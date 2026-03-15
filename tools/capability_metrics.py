"""Capability telemetry and leaderboard utilities.

Tracks quality/reliability metrics for advanced runs (swarm, multi_execute,
multi_plan, research) and renders a compact HTML leaderboard.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


METRICS_PATH = Path(__file__).resolve().parent.parent / "data" / "capability_metrics.jsonl"


def _ensure_path() -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not METRICS_PATH.exists():
        METRICS_PATH.touch()


def record_capability_run(
    mode: str,
    task: str,
    *,
    agent: str = "",
    category: str = "",
    verifier_pass: bool,
    confidence: float,
    source_count: int,
    unique_domains: int,
    diversity_score: float,
    blocked: bool,
    contradiction_count: int,
    latency_ms: int,
) -> None:
    """Append one capability telemetry event to local JSONL storage."""
    _ensure_path()
    payload = {
        "ts": time.time(),
        "mode": str(mode or "unknown"),
        "agent": str(agent or ""),
        "category": str(category or ""),
        "task_preview": (task or "")[:180],
        "verifier_pass": bool(verifier_pass),
        "confidence": float(max(0.0, min(1.0, confidence))),
        "source_count": int(max(0, source_count)),
        "unique_domains": int(max(0, unique_domains)),
        "diversity_score": float(max(0.0, min(1.0, diversity_score))),
        "blocked": bool(blocked),
        "contradiction_count": int(max(0, contradiction_count)),
        "latency_ms": int(max(0, latency_ms)),
    }
    with METRICS_PATH.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _load_recent(hours: int = 72, max_rows: int = 3000) -> list[dict[str, Any]]:
    _ensure_path()
    cutoff = time.time() - max(1, int(hours)) * 3600
    rows: list[dict[str, Any]] = []
    with METRICS_PATH.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if float(row.get("ts", 0.0)) >= cutoff:
                rows.append(row)
    if len(rows) > max_rows:
        rows = rows[-max_rows:]
    return rows


def summarize_capabilities(hours: int = 72) -> dict[str, Any]:
    """Aggregate capability metrics for dashboarding."""
    rows = _load_recent(hours=hours)
    if not rows:
        return {"hours": hours, "total": 0, "by_mode": {}}

    total = len(rows)
    verifier_passes = sum(1 for row in rows if row.get("verifier_pass"))
    blocked = sum(1 for row in rows if row.get("blocked"))
    avg_conf = sum(float(row.get("confidence", 0.0)) for row in rows) / total
    avg_sources = sum(int(row.get("source_count", 0)) for row in rows) / total
    avg_diversity = sum(float(row.get("diversity_score", 0.0)) for row in rows) / total
    avg_latency = sum(int(row.get("latency_ms", 0)) for row in rows) / total
    contradictions = sum(int(row.get("contradiction_count", 0)) for row in rows)

    by_mode: dict[str, dict[str, Any]] = {}
    by_agent: dict[str, dict[str, Any]] = {}
    for row in rows:
        mode = str(row.get("mode", "unknown"))
        bucket = by_mode.setdefault(
            mode,
            {
                "total": 0,
                "pass_count": 0,
                "blocked": 0,
                "confidence_sum": 0.0,
                "sources_sum": 0,
                "diversity_sum": 0.0,
                "latency_sum": 0,
                "contradictions": 0,
            },
        )
        bucket["total"] += 1
        bucket["pass_count"] += 1 if row.get("verifier_pass") else 0
        bucket["blocked"] += 1 if row.get("blocked") else 0
        bucket["confidence_sum"] += float(row.get("confidence", 0.0))
        bucket["sources_sum"] += int(row.get("source_count", 0))
        bucket["diversity_sum"] += float(row.get("diversity_score", 0.0))
        bucket["latency_sum"] += int(row.get("latency_ms", 0))
        bucket["contradictions"] += int(row.get("contradiction_count", 0))

        agent = str(row.get("agent", "") or "").strip()
        if agent:
            ab = by_agent.setdefault(
                agent,
                {
                    "total": 0,
                    "pass_count": 0,
                    "confidence_sum": 0.0,
                    "category_hits": {},
                },
            )
            ab["total"] += 1
            ab["pass_count"] += 1 if row.get("verifier_pass") else 0
            ab["confidence_sum"] += float(row.get("confidence", 0.0))
            category = str(row.get("category", "") or "").strip() or "general"
            ab["category_hits"][category] = int(ab["category_hits"].get(category, 0)) + 1

    leaderboard: list[dict[str, Any]] = []
    for mode, bucket in by_mode.items():
        count = max(1, int(bucket["total"]))
        pass_rate = bucket["pass_count"] / count
        avg_mode_conf = bucket["confidence_sum"] / count
        avg_mode_sources = bucket["sources_sum"] / count
        avg_mode_diversity = bucket["diversity_sum"] / count
        avg_mode_latency = bucket["latency_sum"] / count
        penalty = (bucket["blocked"] / count) * 0.2 + (bucket["contradictions"] / count) * 0.05
        score = max(0.0, min(1.0, (0.45 * pass_rate) + (0.25 * avg_mode_conf) + (0.15 * min(1.0, avg_mode_sources / 6.0)) + (0.15 * avg_mode_diversity) - penalty))
        leaderboard.append(
            {
                "mode": mode,
                "total": bucket["total"],
                "pass_rate": pass_rate,
                "avg_confidence": avg_mode_conf,
                "avg_sources": avg_mode_sources,
                "avg_diversity": avg_mode_diversity,
                "avg_latency_ms": avg_mode_latency,
                "blocked": bucket["blocked"],
                "contradictions": bucket["contradictions"],
                "score": score,
            }
        )

    leaderboard.sort(key=lambda item: item["score"], reverse=True)

    agent_leaderboard: list[dict[str, Any]] = []
    for agent, bucket in by_agent.items():
        count = max(1, int(bucket["total"]))
        pass_rate = bucket["pass_count"] / count
        avg_conf = bucket["confidence_sum"] / count
        top_category = "general"
        if bucket["category_hits"]:
            top_category = max(bucket["category_hits"], key=lambda key: bucket["category_hits"][key])
        agent_score = max(0.0, min(1.0, 0.6 * pass_rate + 0.4 * avg_conf))
        agent_leaderboard.append(
            {
                "agent": agent,
                "score": agent_score,
                "pass_rate": pass_rate,
                "avg_confidence": avg_conf,
                "runs": count,
                "top_category": top_category,
            }
        )
    agent_leaderboard.sort(key=lambda item: item["score"], reverse=True)

    return {
        "hours": hours,
        "total": total,
        "overall": {
            "pass_rate": verifier_passes / total,
            "blocked_rate": blocked / total,
            "avg_confidence": avg_conf,
            "avg_sources": avg_sources,
            "avg_diversity": avg_diversity,
            "avg_latency_ms": avg_latency,
            "contradictions": contradictions,
        },
        "leaderboard": leaderboard,
        "agent_leaderboard": agent_leaderboard,
    }


def render_capability_summary_html(hours: int = 72) -> str:
    """Render capability summary as Telegram HTML."""
    report = summarize_capabilities(hours=hours)
    total = int(report.get("total", 0))
    if total == 0:
        return (
            "<b>🏁 Capability Leaderboard</b>\n"
            "\n"
            "No telemetry yet. Run /swarm, /multi_execute, or /multi_plan first."
        )

    overall = report.get("overall", {}) or {}
    lines = [
        "<b>🏁 Capability Leaderboard</b>",
        f"Window: <code>{int(report.get('hours', hours))}h</code> | Runs: <b>{total}</b>",
        "",
        "<b>Overall</b>",
        f"• Verifier pass: <b>{int(float(overall.get('pass_rate', 0.0)) * 100)}%</b>",
        f"• Blocked rate: <b>{int(float(overall.get('blocked_rate', 0.0)) * 100)}%</b>",
        f"• Avg confidence: <b>{int(float(overall.get('avg_confidence', 0.0)) * 100)}%</b>",
        f"• Avg sources: <b>{float(overall.get('avg_sources', 0.0)):.1f}</b>",
        f"• Source diversity: <b>{int(float(overall.get('avg_diversity', 0.0)) * 100)}%</b>",
        f"• Avg latency: <b>{int(float(overall.get('avg_latency_ms', 0.0)))}ms</b>",
        f"• Contradictions: <b>{int(overall.get('contradictions', 0))}</b>",
        "",
        "<b>Top Modes</b>",
    ]

    for row in (report.get("leaderboard", []) or [])[:8]:
        lines.append(
            "• <code>{mode}</code> score=<b>{score}</b> pass=<b>{pass_pct}</b> "
            "src=<b>{src:.1f}</b> div=<b>{div}%</b> runs=<b>{runs}</b>".format(
                mode=row.get("mode", "unknown"),
                score=int(float(row.get("score", 0.0)) * 100),
                pass_pct=int(float(row.get("pass_rate", 0.0)) * 100),
                src=float(row.get("avg_sources", 0.0)),
                div=int(float(row.get("avg_diversity", 0.0)) * 100),
                runs=int(row.get("total", 0)),
            )
        )

    agents = report.get("agent_leaderboard", []) or []
    if agents:
        lines.extend(["", "<b>Top Agents</b>"])
        for row in agents[:8]:
            lines.append(
                "• <code>{agent}</code> score=<b>{score}</b> pass=<b>{pass_pct}</b> "
                "conf=<b>{conf}%</b> runs=<b>{runs}</b> cat=<b>{cat}</b>".format(
                    agent=row.get("agent", "unknown"),
                    score=int(float(row.get("score", 0.0)) * 100),
                    pass_pct=int(float(row.get("pass_rate", 0.0)) * 100),
                    conf=int(float(row.get("avg_confidence", 0.0)) * 100),
                    runs=int(row.get("runs", 0)),
                    cat=row.get("top_category", "general"),
                )
            )

    return "\n".join(lines)
