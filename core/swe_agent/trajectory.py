"""
SWE-agent trajectory visualization and analysis utilities.

This module provides tools for:
- Loading and analyzing trajectory files
- Generating HTML visualizations
- Computing statistics and metrics
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryStats:
    """Statistics from a trajectory."""

    instance_id: str
    total_steps: int
    total_cost: float
    duration_seconds: float
    tools_used: dict[str, int]
    success: bool
    submitted: bool
    error: str


def load_trajectory(path: str | Path) -> dict[str, Any]:
    """Load a trajectory from JSON file.

    Args:
        path: Path to the .traj file

    Returns:
        Trajectory dict
    """
    with open(path) as f:
        return json.load(f)


def load_trajectory_dir(dir_path: str | Path) -> list[dict[str, Any]]:
    """Load all trajectories from a directory.

    Args:
        dir_path: Directory containing .traj files

    Returns:
        List of trajectory dicts
    """
    dir_path = Path(dir_path)
    trajectories = []

    for traj_file in sorted(dir_path.glob("*.traj")):
        try:
            trajectories.append(load_trajectory(traj_file))
        except Exception as e:
            logger.warning(f"Failed to load {traj_file}: {e}")

    return trajectories


def compute_stats(trajectory: dict[str, Any]) -> TrajectoryStats:
    """Compute statistics from a trajectory.

    Args:
        trajectory: Trajectory dict from load_trajectory

    Returns:
        TrajectoryStats
    """
    tools_used: dict[str, int] = {}

    for step in trajectory.get("steps", []):
        for tc in step.get("tool_calls", []):
            tool_name = tc.get("name", "unknown")
            tools_used[tool_name] = tools_used.get(tool_name, 0) + 1

    return TrajectoryStats(
        instance_id=trajectory.get("instance_id", ""),
        total_steps=trajectory.get("total_steps", 0),
        total_cost=trajectory.get("total_cost", 0.0),
        duration_seconds=trajectory.get("duration_seconds", 0.0),
        tools_used=tools_used,
        success=trajectory.get("success", False),
        submitted=trajectory.get("submitted", False),
        error=trajectory.get("error", ""),
    )


def generate_html_report(trajectory: dict[str, Any], output_path: Path | None = None) -> str:
    """Generate an HTML report from a trajectory.

    Args:
        trajectory: Trajectory dict
        output_path: Optional path to save the HTML

    Returns:
        HTML string
    """
    stats = compute_stats(trajectory)
    steps = trajectory.get("steps", [])

    # Build tool usage table
    tool_rows = ""
    for tool, count in sorted(stats.tools_used.items(), key=lambda x: -x[1]):
        tool_rows += f"<tr><td>{tool}</td><td>{count}</td></tr>"

    # Build steps table
    step_rows = ""
    for step in steps:
        thought = step.get("thought", "")[:100]
        action = step.get("action", "")[:100]
        obs = step.get("observation", "")[:100]
        cost = step.get("cost", 0)

        step_rows += f"""
        <tr>
            <td>{step.get('step_num', 0)}</td>
            <td>{thought}...</td>
            <td>{action}...</td>
            <td>{obs}...</td>
            <td>${cost:.4f}</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SWE-agent Trajectory: {stats.instance_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        h1, h2 {{ color: #333; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #007AFF; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #fafafa; font-weight: 600; }}
        .success {{ color: #34C759; }}
        .failure {{ color: #FF3B30; }}
        .patch {{ background: #f0f0f0; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>SWE-agent Trajectory Report</h1>
    <p><strong>Instance:</strong> {stats.instance_id}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{stats.total_steps}</div>
            <div class="stat-label">Total Steps</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.total_cost:.4f}</div>
            <div class="stat-label">Total Cost</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.duration_seconds:.1f}s</div>
            <div class="stat-label">Duration</div>
        </div>
        <div class="stat-card">
            <div class="stat-value {'success' if stats.success else 'failure'}">
                {'✅' if stats.success else '❌'}
            </div>
            <div class="stat-label">Success</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">
                {'✅' if stats.submitted else '❌'}
            </div>
            <div class="stat-label">Submitted</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(stats.tools_used)}</div>
            <div class="stat-label">Tools Used</div>
        </div>
    </div>

    <h2>Tool Usage</h2>
    <table>
        <tr><th>Tool</th><th>Count</th></tr>
        {tool_rows}
    </table>

    <h2>Steps</h2>
    <table>
        <tr><th>#</th><th>Thought</th><th>Action</th><th>Observation</th><th>Cost</th></tr>
        {step_rows}
    </table>

    <h2>Final Patch</h2>
    <div class="patch">{trajectory.get('final_patch', 'No patch generated')[:500]}...</div>

    {f'<p><strong>Error:</strong> {stats.error}</p>' if stats.error else ''}
</body>
</html>
    """

    if output_path:
        output_path.write_text(html)
        logger.info(f"HTML report saved to: {output_path}")

    return html


def generate_summary_table(trajectories: list[dict[str, Any]]) -> str:
    """Generate a markdown summary table from multiple trajectories.

    Args:
        trajectories: List of trajectory dicts

    Returns:
        Markdown table string
    """
    lines = [
        "| Instance | Steps | Cost | Duration | Success | Submitted |",
        "|----------|-------|------|----------|---------|-----------|",
    ]

    for traj in trajectories:
        stats = compute_stats(traj)
        status = "✅" if stats.success else "❌"
        submitted = "✅" if stats.submitted else "❌"

        lines.append(
            f"| {stats.instance_id} | {stats.total_steps} | "
            f"${stats.total_cost:.4f} | {stats.duration_seconds:.1f}s | "
            f"{status} | {submitted} |"
        )

    return "\n".join(lines)


# CLI for trajectory analysis
def main() -> int:
    """CLI for trajectory analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="SWE-agent Trajectory Analyzer")
    parser.add_argument("path", help="Trajectory file or directory")
    parser.add_argument("--html", help="Output HTML report to path")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    args = parser.parse_args()

    path = Path(args.path)

    if path.is_dir():
        trajectories = load_trajectory_dir(path)
        print(f"Loaded {len(trajectories)} trajectories from {path}")
        print()
        print(generate_summary_table(trajectories))

        if args.html:
            for traj in trajectories:
                traj_id = traj.get("instance_id", "unknown")
                out_path = Path(args.html) / f"{traj_id}.html"
                generate_html_report(traj, out_path)
            print(f"\nHTML reports saved to {args.html}/")

    elif path.is_file():
        traj = load_trajectory(path)
        stats = compute_stats(traj)

        if args.stats:
            print(f"Instance: {stats.instance_id}")
            print(f"Steps: {stats.total_steps}")
            print(f"Cost: ${stats.total_cost:.4f}")
            print(f"Duration: {stats.duration_seconds:.1f}s")
            print(f"Success: {stats.success}")
            print(f"Submitted: {stats.submitted}")
            print(f"Tools used: {stats.tools_used}")

        if args.html:
            generate_html_report(traj, Path(args.html))
            print(f"HTML report saved to {args.html}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())