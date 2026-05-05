"""
tools/goal_planner.py
Goal decomposition -- converts natural language goal to structured PLAN.md.
Logs its own reasoning trace to .goal/traces/ (Meta-Harness pattern).
"""

import os, json, asyncio, re, subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
import anthropic

GOAL_DIR = Path(".goal")
PLANS_DIR = GOAL_DIR / "plans"
TRACES_DIR = GOAL_DIR / "traces"

DECOMPOSE_SYSTEM = """You are a senior software architect. Convert a development
goal into executable tasks for an autonomous bash-only AI coding agent.

Output ONLY a JSON object with this exact structure:
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
          "description": "Complete, self-contained task. Include file paths, function signatures, exact behavior. The agent has ZERO memory of other tasks.",
          "acceptance_criteria": ["Verifiable bash command or observable output"],
          "rollback": "git checkout -- path/to/file.py",
          "files_likely_touched": ["path/to/file.py"],
          "estimated_minutes": number
        }
      ]
    }
  ],
  "final_audit": {
    "run_tests": "pytest -q 2>/dev/null || echo no-tests",
    "run_lint": "ruff check . --select=E,W,F --ignore=E501 2>/dev/null || true",
    "run_typecheck": "mypy . --ignore-missing-imports 2>/dev/null || echo no-mypy"
  },
  "pr_title": "feat(project): short description",
  "pr_body": "## Summary\n...\n## Changes\n- ..."
}

Rules:
- Max 8 tasks per phase, max 4 phases
- Every task description must be 100% self-contained with no assumed context
- acceptance_criteria must be checkable by running a bash command
- NEVER touch tools/mirofish/ -- read-only submodule
- Always use os.getenv() for secrets, never hardcode"""


async def decompose_goal(goal: str, repo_context: str) -> dict:
    """Decompose goal using Claude. Log the full trace."""
    client = anthropic.AsyncAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL") or None
    )
    user_msg = f"Goal: {goal}\n\nRepository context:\n{repo_context}\n\nDecompose this goal."

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        system=DECOMPOSE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}]
    )
    content = message.content[0].text
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if not json_match:
        raise ValueError(f"No JSON in planner response: {content[:300]}")
    return json.loads(json_match.group())


def get_repo_context() -> str:
    """Read key project files for planner context."""
    parts = []
    for fname in ["CLAUDE.md", "AGENTS.md", "README.md"]:
        p = Path(fname)
        if p.exists():
            parts.append(f"=== {fname} ===\n{p.read_text()[:2000]}")
    tools_dir = Path("tools")
    if tools_dir.exists():
        parts.append(f"=== tools/ ===\n{chr(10).join(f.name for f in tools_dir.glob('*.py'))}")
    r = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True)
    if r.returncode == 0:
        parts.append(f"=== Recent commits ===\n{r.stdout}")
    return "\n\n".join(parts)


def write_plan_md(plan: dict, goal_id: str) -> Path:
    """Write PLAN.md to .goal/plans/ for human review."""
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    plan_path = PLANS_DIR / f"{goal_id}_PLAN.md"
    lines = [
        f"# Goal Plan: {plan['goal']}",
        f"\n**Goal ID:** {goal_id}",
        f"**Project:** {plan.get('project', '?')}",
        f"**Estimated:** {plan.get('estimated_hours', '?')}h",
        f"**Created:** {datetime.now().isoformat()}\n---\n"
    ]
    for phase in plan.get("phases", []):
        lines.append(f"## Phase {phase['phase']}: {phase['name']}\n")
        for task in phase.get("tasks", []):
            lines.append(f"### {task['id']}: {task['description']}\n")
            lines.append("**Criteria:**")
            for c in task.get("acceptance_criteria", []):
                lines.append(f"- {c}")
            lines.append(f"\n**Rollback:** `{task.get('rollback', 'git checkout -- .')}`\n")
    audit = plan.get("final_audit", {})
    lines += [
        "---\n## Final Audit",
        f"- Tests: `{audit.get('run_tests', 'N/A')}`",
        f"- Lint: `{audit.get('run_lint', 'N/A')}`",
        f"\n## PR\n**{plan.get('pr_title', '')}**\n{plan.get('pr_body', '')}"
    ]
    plan_path.write_text("\n".join(lines))
    return plan_path


async def plan_goal(goal: str) -> tuple:
    """Main entry: decompose goal, write PLAN.md, return (plan, path, goal_id)."""
    goal_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    repo_context = get_repo_context()

    # Log planner trace (Meta-Harness: everything gets logged)
    trace_dir = TRACES_DIR / goal_id
    trace_dir.mkdir(parents=True, exist_ok=True)
    (trace_dir / "planner_input.txt").write_text(f"Goal: {goal}\n\nContext:\n{repo_context}")

    plan = await decompose_goal(goal, repo_context)
    plan_path = write_plan_md(plan, goal_id)

    (trace_dir / "planner_output.json").write_text(json.dumps(plan, indent=2))

    return plan, plan_path, goal_id


if __name__ == "__main__":
    import sys
    goal = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not goal:
        print("Usage: python tools/goal_planner.py \"your goal\"")
        sys.exit(1)
    plan, path, gid = asyncio.run(plan_goal(goal))
    total = sum(len(p['tasks']) for p in plan.get('phases', []))
    print(f"Plan: {path}\nGoal ID: {gid}\nPhases: {len(plan.get('phases',[]))}\nTasks: {total}")