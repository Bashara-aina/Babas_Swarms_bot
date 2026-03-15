"""Swarm observability utilities.

Tracks latest swarm run per user and renders rich visualization output:
- full department/agent universe from config/departments.yaml
- swarm thought stream
- inter-agent communication edges (dependency/result passing)
- subtask conclusions and final synthesis path
"""

from __future__ import annotations

import html
import re
import time
from pathlib import Path
from typing import Any

import yaml


_TRACE_STORE: dict[int, dict[str, Any]] = {}


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=False)


def _clean_excerpt(text: str, limit: int = 260) -> str:
    """Normalize noisy model text for Telegram HTML display."""
    raw = html.unescape(text or "")
    raw = raw.replace("```", " ").replace("`", "")
    raw = re.sub(r"</?(code|pre|b|i)>", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"(?m)^\s*#{1,6}\s*", "", raw)
    raw = re.sub(r"(?m)^\s*[-*]\s+", "• ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    raw = raw.strip()
    if len(raw) > limit:
        raw = raw[:limit].rstrip() + "…"
    return _esc(raw or "(no content)")


def _now() -> str:
    return time.strftime("%H:%M:%S")


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_departments() -> dict[str, list[str]]:
    """Load all departments and agent names from YAML config."""
    cfg_path = _root() / "config" / "departments.yaml"
    if not cfg_path.exists():
        return {}
    with cfg_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    departments: dict[str, list[str]] = {}
    for dept_name, dept_data in raw.items():
        if not isinstance(dept_data, dict):
            continue
        agents = dept_data.get("agents", {}) or {}
        if isinstance(agents, dict):
            departments[str(dept_name)] = sorted(str(a) for a in agents.keys())
    return departments


def start_swarm_trace(user_id: int, task: str, subtasks: list[dict[str, Any]]) -> None:
    """Initialize trace state for a swarm run."""
    records: list[dict[str, Any]] = []
    for s in subtasks:
        records.append(
            {
                "id": str(s.get("id", "?")),
                "agent": str(s.get("agent", "general")),
                "task": str(s.get("task", "")),
                "depends_on": [str(d) for d in (s.get("depends_on", []) or [])],
                "result": "",
                "status": "pending",
            }
        )

    _TRACE_STORE[user_id] = {
        "task": task,
        "started_at": time.time(),
        "finished_at": None,
        "events": [],
        "subtasks": records,
        "final_answer": "",
    }


def record_event(user_id: int, event: str) -> None:
    """Record one swarm progress/thought event."""
    trace = _TRACE_STORE.get(user_id)
    if not trace:
        return
    trace["events"].append({"t": _now(), "text": str(event)})


def record_subtask_result(user_id: int, subtask_id: str, result: str) -> None:
    """Persist subtask result + inferred status for a given subtask id."""
    trace = _TRACE_STORE.get(user_id)
    if not trace:
        return

    for row in trace.get("subtasks", []):
        if row.get("id") == str(subtask_id):
            row["result"] = result or ""
            lowered = (result or "").lower()
            row["status"] = "failed" if lowered.startswith("failed:") or "error" in lowered[:120] else "done"
            return


def finalize_trace(user_id: int, final_answer: str) -> None:
    """Finalize swarm trace with final synthesis output."""
    trace = _TRACE_STORE.get(user_id)
    if not trace:
        return
    trace["final_answer"] = final_answer or ""
    trace["finished_at"] = time.time()


def _duration(trace: dict[str, Any]) -> str:
    start = float(trace.get("started_at") or time.time())
    end = float(trace.get("finished_at") or time.time())
    sec = max(0, int(end - start))
    m, s = divmod(sec, 60)
    return f"{m}m {s}s"


def build_swarm_live_panel_html(user_id: int) -> str:
    """Render compact live panel suitable for frequent message edits."""
    trace = _TRACE_STORE.get(user_id)
    if not trace:
        return "<b>📡 Swarm Live</b>\n<i>No active trace yet. Run /swarm first.</i>"

    task = str(trace.get("task", ""))
    subtasks = trace.get("subtasks", []) or []
    events = trace.get("events", []) or []

    total = len(subtasks)
    done = sum(1 for s in subtasks if s.get("status") == "done")
    failed = sum(1 for s in subtasks if s.get("status") == "failed")
    running = max(0, total - done - failed)
    completed = done + failed
    pct = int((completed / total) * 100) if total else 0

    def _bar(p: int, width: int = 18) -> str:
        p = max(0, min(100, p))
        fill = int(width * p / 100)
        return "[" + ("█" * fill) + ("░" * (width - fill)) + "]"

    lines = [
        "<b>📡 Swarm Live Monitor</b>",
        f"Task: <code>{_esc(task[:180])}</code>",
        f"Progress: <code>{_bar(pct)} {pct}%</code>",
        f"Status: ✅{done} | ⏳{running} | ❌{failed} / {total}",
        f"Elapsed: <code>{_duration(trace)}</code>",
        "",
        "<b>🔗 Communication</b>",
    ]

    # show up to last 8 dependency edges
    edges: list[str] = []
    for row in subtasks:
        sid = str(row.get("id", "?"))
        agent = str(row.get("agent", "general"))
        deps = row.get("depends_on", []) or []
        if not deps:
            edges.append(f"• START → T{sid} ({_esc(agent)})")
        for dep in deps:
            dep_agent = next((str(r.get("agent", "?")) for r in subtasks if str(r.get("id")) == str(dep)), "?")
            edges.append(f"• T{dep} ({_esc(dep_agent)}) → T{sid} ({_esc(agent)})")
    lines.extend(edges[-8:] if edges else ["<i>No edges yet</i>"])

    lines.extend(["", "<b>💭 Latest Thoughts</b>"])
    if events:
        for e in events[-8:]:
            t = _esc(str(e.get("t", "")))
            text = _esc(str(e.get("text", ""))[:140])
            lines.append(f"• <code>{t}</code> {text}")
    else:
        lines.append("<i>No events yet</i>")

    out = "\n".join(lines)
    # Telegram edit limit safety margin
    if len(out) > 3800:
        out = out[:3790] + "\n…"
    return out


def build_swarm_viz_html(user_id: int) -> str:
    """Render full swarm visualization (departments + run trace)."""
    departments = load_departments()
    total_agents = sum(len(v) for v in departments.values())

    lines: list[str] = [
        "<b>🕸 Swarm Observability View</b>",
        f"Departments: <b>{len(departments)}</b> | Agents: <b>{total_agents}</b>",
        "",
        "<b>🏢 Department Universe</b>",
    ]

    if departments:
        for dept, agents in sorted(departments.items(), key=lambda x: x[0]):
            lines.append(f"• <b>{_esc(dept)}</b> ({len(agents)})")
            lines.append(f"  <code>{_esc(', '.join(agents))}</code>")
    else:
        lines.append("<i>No departments config loaded.</i>")

    trace = _TRACE_STORE.get(user_id)
    lines.extend(["", "<b>🧠 Latest Swarm Run</b>"])
    if not trace:
        lines.append("<i>No swarm trace yet. Run /swarm first.</i>")
        return "\n".join(lines)

    task = str(trace.get("task", ""))
    lines.append(f"Task: <code>{_esc(task[:300])}</code>")
    lines.append(f"Duration: <code>{_duration(trace)}</code>")

    # Communication graph (dependency/result passing)
    lines.extend(["", "<b>🔗 Inter-Agent Communication (Dependency Graph)</b>"])
    edges: list[str] = []
    subtasks = trace.get("subtasks", []) or []
    for row in subtasks:
        sid = row.get("id", "?")
        agent = row.get("agent", "general")
        deps = row.get("depends_on", []) or []
        if not deps:
            edges.append(f"• START → T{sid} ({_esc(str(agent))})")
        for dep in deps:
            dep_agent = next((r.get("agent", "?") for r in subtasks if r.get("id") == dep), "?")
            edges.append(
                f"• T{dep} ({_esc(str(dep_agent))}) → T{sid} ({_esc(str(agent))})"
            )
    if edges:
        lines.extend(edges)
    else:
        lines.append("<i>No dependency edges recorded.</i>")

    # Mermaid-style diagram block (text only; useful for copy/paste)
    lines.extend(["", "<b>📈 Flow Diagram (Mermaid)</b>", "<pre>graph TD"])
    for row in subtasks:
        sid = row.get("id", "?")
        label = f"T{sid}:{str(row.get('agent', 'general'))}".replace('"', "")
        lines.append(f"T{sid}[\"{html.escape(label)}\"]")
    for row in subtasks:
        sid = row.get("id", "?")
        deps = row.get("depends_on", []) or []
        if not deps:
            lines.append(f"START --> T{sid}")
        else:
            for dep in deps:
                lines.append(f"T{dep} --> T{sid}")
    lines.append("SYNTH[\"Final Synthesis\"]")
    for row in subtasks:
        lines.append(f"T{row.get('id', '?')} --> SYNTH")
    lines.append("SYNTH --> ANSWER[\"Final Answer\"]")
    lines.append("</pre>")

    # Thought stream
    lines.extend(["", "<b>💭 Thought Stream</b>"])
    events = trace.get("events", []) or []
    if events:
        for e in events[-40:]:
            text = str(e.get("text", ""))
            lines.append(f"• <code>{_esc(str(e.get('t', '')))}</code> {_esc(text[:260])}")
    else:
        lines.append("<i>No thought events captured.</i>")

    # Subtask conclusions
    lines.extend(["", "<b>✅ Per-Agent Conclusions</b>"])
    for row in subtasks:
        sid = row.get("id", "?")
        agent = row.get("agent", "general")
        status = row.get("status", "pending")
        result = str(row.get("result", "")).strip()
        excerpt = _clean_excerpt(result, limit=420)
        icon = "✅" if status == "done" else ("❌" if status == "failed" else "⏳")
        lines.append(f"{icon} <b>T{sid} [{_esc(str(agent))}]</b>")
        lines.append(f"  <i>{_esc(str(row.get('task', ''))[:220])}</i>")
        lines.append(f"  {excerpt}")

    # Final synthesis explanation
    final_answer = str(trace.get("final_answer", "")).strip()
    lines.extend(["", "<b>🎯 How Answer Was Concluded</b>"])
    if final_answer:
        excerpt = _clean_excerpt(final_answer, limit=1200)
        lines.append(
            "The synthesizer merged all subtask outputs, validated consistency, "
            "then produced this final conclusion:"
        )
        lines.append(excerpt)
    else:
        lines.append("<i>Final synthesis not captured yet.</i>")

    return "\n".join(lines)
