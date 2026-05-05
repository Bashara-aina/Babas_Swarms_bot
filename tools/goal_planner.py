"""
tools/goal_planner.py
Goal decomposition engine for the /goal autonomous delivery system.
Converts a natural language goal into a structured PLAN.md that
mini-SWE-agent executes task by task.
"""

import os
import re
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic


GOAL_DIR = Path(".goal")
PLANS_DIR = GOAL_DIR / "plans"


DECOMPOSE_SYSTEM = """You are a senior software architect decomposing a
development goal into executable tasks for an autonomous AI coding agent.

The agent has access to bash only. It can: read/write files, run tests,
install packages, commit to git, open PRs with gh CLI.

Output a JSON object with this exact structure:
{
  "goal": "original goal",
  "project": "cekwajar|rumahlabuh|legion|mirofish|research|general",
  "estimated_hours": number,
  "phases": [
    {
      "phase": 1,
      "name": "Phase name",
      "tasks": [
        {
          "id": "T1.1",
          "description": "Precise, self-contained task for the agent",
          "acceptance_criteria": ["criterion 1", "criterion 2"],
          "rollback": "what to undo if this fails",
          "files_likely_touched": ["path/to/file.py"],
          "estimated_minutes": number
        }
      ]
    }
  ],
  "final_audit": {
    "run_tests": "command to run all tests",
    "run_lint": "command to lint",
    "run_typecheck": "command to typecheck if applicable",
    "manual_checks": ["check 1", "check 2"]
  },
  "pr_title": "feat: ...",
  "pr_body": "## Summary\n...\n## Changes\n..."
}

Rules:
- Each task must be independently executable by an agent with no memory of previous tasks
- Each task description must include full context (file paths, function names, exact behavior)
- Maximum 8 tasks per phase, maximum 4 phases
- Be concrete — never say "implement feature X", say exactly what to write
- acceptance_criteria must be verifiable by running a bash command"""


async def decompose_goal(goal: str, repo_context: str = "") -> dict:
    """Call Claude to decompose goal into structured plan."""
    client = anthropic.AsyncAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL", None)
    )

    user_msg = f"""Goal: {goal}

Repository context:
{repo_context}

Decompose this into a structured execution plan."""

    try:
        message = await client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            system=DECOMPOSE_SYSTEM,
            messages=[{"role": "user", "content": user_msg}]
        )

        content = message.content[0].text

        # Parse JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError(f"Could not parse JSON from planner response: {content[:500]}")
    except Exception as e:
        # Fallback: return a simple single-phase plan
        return {
            "goal": goal,
            "project": "general",
            "estimated_hours": 1,
            "phases": [{
                "phase": 1,
                "name": "Implementation",
                "tasks": [{
                    "id": "T1.1",
                    "description": goal,
                    "acceptance_criteria": ["Task completed successfully"],
                    "rollback": "git checkout .",
                    "files_likely_touched": [],
                    "estimated_minutes": 60
                }]
            }],
            "final_audit": {
                "run_tests": "echo 'No tests specified'",
                "run_lint": "echo 'No lint specified'",
                "run_typecheck": "echo 'No typecheck'",
                "manual_checks": []
            },
            "pr_title": f"feat: {goal[:60]}",
            "pr_body": f"## Summary\n{goal}\n\n## Changes\n- Initial implementation"
        }


def get_repo_context() -> str:
    """Read key files to give the planner context about the codebase."""
    context_parts = []

    for fname in ["CLAUDE.md", "AGENTS.md", "README.md"]:
        p = Path(fname)
        if p.exists():
            content = p.read_text()[:2000]
            context_parts.append(f"=== {fname} ===\n{content}")

    # List tools/ directory
    tools_dir = Path("tools")
    if tools_dir.exists():
        tool_files = [f.name for f in tools_dir.glob("*.py")]
        context_parts.append(f"=== tools/ directory ===\n" + "\n".join(tool_files))

    # Recent git log
    import subprocess
    result = subprocess.run(
        ["git", "log", "--oneline", "-10"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        context_parts.append(f"=== Recent commits ===\n{result.stdout}")

    return "\n\n".join(context_parts)


def write_plan_md(plan: dict, goal_id: str) -> Path:
    """Write structured PLAN.md for human review and agent reference."""
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    plan_path = PLANS_DIR / f"{goal_id}_PLAN.md"

    lines = [
        f"# Goal Plan: {plan['goal']}",
        f"\n**Goal ID:** {goal_id}",
        f"**Project:** {plan.get('project', 'unknown')}",
        f"**Estimated time:** {plan.get('estimated_hours', '?')} hours",
        f"**Created:** {datetime.now().isoformat()}",
        f"**Status:** pending\n",
        "---\n"
    ]

    for phase in plan.get("phases", []):
        lines.append(f"## Phase {phase['phase']}: {phase['name']}\n")
        for task in phase.get("tasks", []):
            lines.append(f"### {task['id']} — {task['description']}\n")
            lines.append("**Acceptance criteria:**")
            for c in task.get("acceptance_criteria", []):
                lines.append(f"- {c}")
            lines.append(f"\n**Rollback:** {task.get('rollback', 'git checkout .')}")
            lines.append(f"**Est. time:** {task.get('estimated_minutes', '?')} min\n")

    audit = plan.get("final_audit", {})
    lines.append("---\n## Final Audit\n")
    lines.append(f"- Tests: `{audit.get('run_tests', 'N/A')}`")
    lines.append(f"- Lint: `{audit.get('run_lint', 'N/A')}`")
    lines.append(f"- Typecheck: `{audit.get('run_typecheck', 'N/A')}`")
    for check in audit.get("manual_checks", []):
        lines.append(f"- {check}")

    lines.append(f"\n---\n## PR\n**Title:** {plan.get('pr_title', '')}")
    lines.append(f"\n{plan.get('pr_body', '')}")

    plan_path.write_text("\n".join(lines))
    return plan_path


async def plan_goal(goal: str) -> tuple[dict, Path, str]:
    """Main entry point: decompose goal and write plan. Returns (plan_dict, plan_path, goal_id)."""
    goal_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    repo_context = get_repo_context()
    plan = await decompose_goal(goal, repo_context)
    plan_path = write_plan_md(plan, goal_id)
    return plan, plan_path, goal_id


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python tools/goal_planner.py \"your goal\"")
        sys.exit(1)
    goal = " ".join(sys.argv[1:])
    plan, plan_path, goal_id = asyncio.run(plan_goal(goal))
    print(f"✅ Plan written: {plan_path}")
    print(f"   Goal ID: {goal_id}")
    print(f"   Phases: {len(plan.get('phases', []))}")
    total_tasks = sum(len(p['tasks']) for p in plan.get('phases', []))
    print(f"   Tasks: {total_tasks}")
    print(f"   Estimated: {plan.get('estimated_hours', '?')} hours")