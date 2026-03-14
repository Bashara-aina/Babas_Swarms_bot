"""
tools/dashboard.py — Live visual dashboard for LegionSwarm agent departments.

Generates a Telegram-friendly visual showing:
  - Each agent department (row)
  - Current status: idle / running / done / failed
  - What task they're working on
  - Progress bar
  - Runtime so far
  - Overall job progress

Two output modes:
  1. ASCII dashboard  : for regular Telegram text message (always works)
  2. PNG chart        : rendered with matplotlib, sent as photo (richer)
"""

from __future__ import annotations

import io
import logging
import math
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Status → display metadata
STATUS_META = {
    "🟢 done":    {"color": "#2ecc71", "icon": "✅", "short": "DONE"},
    "🟡 running": {"color": "#f39c12", "icon": "⚡", "short": "RUN "},
    "🔴 failed":  {"color": "#e74c3c", "icon": "❌", "short": "FAIL"},
    "⚪ idle":    {"color": "#95a5a6", "icon": "○ ", "short": "IDLE"},
    "pending":    {"color": "#bdc3c7", "icon": "○ ", "short": "WAIT"},
}

AGENT_ICONS = {
    "vision":     "👁 ",
    "coding":     "💻",
    "debug":      "🐛",
    "math":       "📐",
    "architect":  "🏗 ",
    "analyst":    "📊",
    "computer":   "🖥 ",
    "general":    "🧠",
    "researcher": "🔬",
    "marketer":   "📢",
    "devops":     "🔧",
    "pm":         "📋",
    "humanizer":  "✨",
    "reviewer":   "🔍",
}


# ── ASCII Dashboard (Telegram text) ───────────────────────────────────────────

def build_ascii_dashboard(
    agent_status: dict,
    job_id: Optional[str] = None,
    job_tasks: Optional[list] = None,
    title: str = "Legion Dashboard",
) -> str:
    """
    Build a Telegram HTML dashboard string.
    agent_status: dict from tools/overnight.py AGENT_STATUS
    job_tasks: list of OvernightTask objects (for progress bars)
    """
    now = time.time()
    lines = []

    # Header
    lines.append(f"<b>📊 {title}</b>")
    if job_id:
        lines.append(f"Job <code>{job_id}</code> — {_now_str()}")
    lines.append("<code>" + "─" * 42 + "</code>")

    # Overall progress bar (if job_tasks provided)
    if job_tasks:
        total = len(job_tasks)
        done  = sum(1 for t in job_tasks if getattr(t, 'status', None) and t.status.value == 'done')
        fail  = sum(1 for t in job_tasks if getattr(t, 'status', None) and t.status.value == 'failed')
        run   = sum(1 for t in job_tasks if getattr(t, 'status', None) and t.status.value == 'running')
        pct   = int((done + fail) / total * 100) if total else 0
        bar   = _progress_bar(pct, width=20)
        lines.append(
            f"<b>Overall:</b> {bar} <b>{pct}%</b>  "
            f"✅{done} 🟡{run} ❌{fail} / {total}"
        )
        lines.append("<code>" + "─" * 42 + "</code>")

    # Agent rows
    if not agent_status:
        lines.append("<i>No agents active. Start a job with /overnight</i>")
    else:
        for agent, info in sorted(agent_status.items()):
            icon = AGENT_ICONS.get(agent, "🤖")
            status = info.get("status", "⚪ idle")
            task   = info.get("task", "")[:30]
            progress = info.get("progress", "")[:25]
            updated = info.get("updated_at", now)
            age_sec = int(now - updated)

            meta = STATUS_META.get(status, STATUS_META["⚪ idle"])
            status_icon = meta["icon"]

            # Format task snippet
            task_str = f" <i>{task}</i>" if task else ""
            prog_str = f" <code>{progress}</code>" if progress else ""
            age_str  = f" <i>({age_sec}s ago)</i>" if age_sec > 5 else ""

            lines.append(
                f"{status_icon} <b>{icon} {agent:<10}</b>{task_str}{prog_str}{age_str}"
            )

    lines.append("<code>" + "─" * 42 + "</code>")
    lines.append(f"<i>Updated {_now_str()} | /dashboard to refresh</i>")
    return "\n".join(lines)


def _progress_bar(pct: int, width: int = 20) -> str:
    filled = int(width * pct / 100)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _now_str() -> str:
    import datetime
    return datetime.datetime.now().strftime("%H:%M:%S")


# ── PNG Chart Dashboard ────────────────────────────────────────────────────────

async def build_png_dashboard(
    agent_status: dict,
    job_id: Optional[str] = None,
    job_tasks: Optional[list] = None,
) -> Optional[bytes]:
    """
    Render a PNG dashboard image using matplotlib.
    Returns PNG bytes or None if matplotlib unavailable.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.gridspec import GridSpec
    except ImportError:
        logger.warning("matplotlib not available, using ASCII dashboard only")
        return None

    agents = sorted(agent_status.keys()) if agent_status else ["No agents"]
    n = len(agents)

    fig_height = max(4, 1.2 + n * 0.65)
    fig = plt.figure(figsize=(12, fig_height), facecolor="#1a1a2e")

    if job_tasks and len(job_tasks) > 0:
        gs = GridSpec(2, 1, height_ratios=[1, n], hspace=0.4, figure=fig)
        ax_progress = fig.add_subplot(gs[0])
        ax_agents   = fig.add_subplot(gs[1])
        _draw_job_progress(ax_progress, job_tasks, job_id)
    else:
        gs = GridSpec(1, 1, figure=fig)
        ax_agents = fig.add_subplot(gs[0])

    _draw_agent_grid(ax_agents, agent_status, agents)

    # Title
    fig.suptitle(
        f"⚡ LegionSwarm Dashboard  —  {_now_str()}",
        color="white", fontsize=13, fontweight="bold", y=0.98,
    )

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _draw_job_progress(ax, tasks: list, job_id: Optional[str]) -> None:
    total = len(tasks)
    if total == 0:
        return

    counts = {"done": 0, "running": 0, "failed": 0, "pending": 0, "skipped": 0}
    for t in tasks:
        status_val = t.status.value if hasattr(t.status, 'value') else str(t.status)
        counts[status_val] = counts.get(status_val, 0) + 1

    left = 0
    colors = {
        "done":    "#2ecc71",
        "running": "#f39c12",
        "failed":  "#e74c3c",
        "pending": "#34495e",
        "skipped": "#7f8c8d",
    }
    for status, count in counts.items():
        if count > 0:
            w = count / total
            ax.barh(0, w, left=left, height=0.5, color=colors[status], alpha=0.9)
            if w > 0.06:
                ax.text(
                    left + w / 2, 0, f"{status}\n{count}",
                    ha="center", va="center", color="white",
                    fontsize=8, fontweight="bold"
                )
            left += w

    done_pct = int((counts["done"] + counts["failed"]) / total * 100)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 0.5)
    ax.set_facecolor("#16213e")
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    title = f"Job {job_id} — {done_pct}% complete ({counts['done']}/{total} tasks done)"
    ax.set_title(title, color="white", fontsize=10, pad=4)


def _draw_agent_grid(ax, agent_status: dict, agents: list) -> None:
    ax.set_facecolor("#16213e")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, len(agents) - 0.5)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    for i, agent in enumerate(reversed(agents)):
        info   = agent_status.get(agent, {})
        status = info.get("status", "⚪ idle")
        task   = info.get("task", "")[:35]
        prog   = info.get("progress", "")[:20]
        meta   = STATUS_META.get(status, STATUS_META["⚪ idle"])
        color  = meta["color"]
        icon   = AGENT_ICONS.get(agent, "🤖")
        short  = meta["short"]

        # Status block
        ax.barh(i, 1.2, left=0, height=0.7, color=color, alpha=0.85)
        ax.text(0.6, i, short, ha="center", va="center",
                color="white", fontsize=7.5, fontweight="bold")

        # Agent name
        ax.text(1.4, i, f"{agent}", ha="left", va="center",
                color="white", fontsize=9, fontweight="bold")

        # Task description
        if task:
            ax.text(3.5, i + 0.18, task, ha="left", va="center",
                    color="#ecf0f1", fontsize=7.5)
        if prog:
            ax.text(3.5, i - 0.18, prog, ha="left", va="center",
                    color="#bdc3c7", fontsize=6.5, style="italic")

        # Horizontal divider
        if i > 0:
            ax.axhline(y=i - 0.5, color="#2c3e50", linewidth=0.5)

    ax.set_title("Agent Status by Department", color="white", fontsize=10, pad=6)
