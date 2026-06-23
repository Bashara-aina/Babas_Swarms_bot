"""
.goal/harnesses/current/harness.py
H_0 -- Initial harness (version 0) for the /goal system.

HARNESS DESIGN PHILOSOPHY (from Meta-Harness paper):
- The harness determines what the model sees at each step
- Small harness changes can produce 6x performance gaps on the same model
- This file is the TARGET of automated optimization -- it WILL be rewritten
  by the Meta-Harness proposer after accumulating execution trace evidence

HARNESS ID: H_0
SCORE: N/A (not yet evaluated)
CREATED: initial
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime


TRACE_DIR = Path(".goal/traces")
HARNESS_VERSION = "H_0"


def build_context_block(plan: dict, repo_root: str) -> str:
    """
    HARNESS FUNCTION: Builds the shared context given to every task prompt.
    This is the primary optimization target for Meta-Harness.
    H_0 strategy: Include CLAUDE.md + AGENTS.md + recent git log + file tree.
    """
    context_parts = []

    # Read key project files (bounded to avoid token explosion)
    for fname in ["CLAUDE.md", "AGENTS.md", "README.md"]:
        p = Path(repo_root) / fname
        if p.exists():
            content = p.read_text()[:3000]
            context_parts.append(f"=== {fname} ===\n{content}")

    # Recent commits (causal context for what changed)
    result = subprocess.run(
        ["git", "log", "--oneline", "--stat", "-5"],
        capture_output=True, text=True, cwd=repo_root
    )
    if result.returncode == 0:
        context_parts.append(f"=== Recent commits ===\n{result.stdout[:1000]}")

    # List of tools available
    tools_dir = Path(repo_root) / "tools"
    if tools_dir.exists():
        tool_names = [f.stem for f in tools_dir.glob("*.py")]
        context_parts.append(f"=== Available Legion tools ===\n{chr(10).join(tool_names)}")

    # Goal plan summary
    context_parts.append(f"""=== Goal Plan ===
Goal: {plan.get('goal', '?')}
Project: {plan.get('project', '?')}
Total phases: {len(plan.get('phases', []))}
Estimated: {plan.get('estimated_hours', '?')}h""")

    return "\n\n".join(context_parts)


def build_task_prompt(task: dict, plan: dict, repo_root: str,
                      phase_num: int, task_num: int,
                      prior_task_traces: list[str] = None) -> str:
    """
    HARNESS FUNCTION: Builds the complete prompt for a single task.

    H_0 strategy: Full self-contained prompt with context + task + criteria.
    Key: mini-SWE-agent has ZERO memory between tasks. Every prompt must be
    completely self-contained. Include prior task summaries for continuity.

    RecursiveMAS insight: Pass lightweight latent state (prior task outcomes)
    as part of the context to enable cross-task information flow.
    """
    context = build_context_block(plan, repo_root)
    criteria_str = "\n".join(
        f"  [ ] {c}" for c in task.get("acceptance_criteria", [])
    )
    files_str = "\n".join(
        f"  - {f}" for f in task.get("files_likely_touched", [])
    )

    # Include abbreviated prior task outcomes (RecursiveMAS latent state)
    prior_context = ""
    if prior_task_traces:
        prior_context = "\n\n=== COMPLETED TASKS (context for this task) ===\n"
        for trace_summary in prior_task_traces[-3:]:  # Last 3 tasks max
            prior_context += f"{trace_summary}\n---\n"

    return f"""You are a software engineering agent working on a specific task.
Repository: {repo_root}
Harness version: {HARNESS_VERSION}

{context}
{prior_context}

==============================================================================
CURRENT TASK: Phase {phase_num}, Task {task_num} of {task.get('id', '?')}
==============================================================================
{task['description']}

ACCEPTANCE CRITERIA (mark each as done when verified):
{criteria_str}

FILES LIKELY INVOLVED:
{files_str}

ROLLBACK IF BLOCKED: {task.get('rollback', 'git checkout -- .')}
ESTIMATED TIME: {task.get('estimated_minutes', '?')} minutes

==============================================================================
EXECUTION RULES (read every time, no exceptions):
==============================================================================
1. Work ONLY in {repo_root}
2. NEVER touch tools/mirofish/ -- it is a READ-ONLY git submodule
3. NEVER hardcode API keys -- always os.getenv('KEY_NAME')
4. After implementation, verify EACH acceptance criterion explicitly
5. Run: {plan.get('final_audit', {}).get('run_tests', 'pytest -q 2>/dev/null || echo no-tests')}
6. Commit: git add -A && git commit -m "feat({plan.get('project','app')}): {task.get('id','T')} - {task.get('description', '')[:50]}"
7. If blocked: write EXACTLY what blocked you to .goal/BLOCKERS.md and continue
8. After each criterion, write a one-line status to .goal/traces/<goal_id>/<task_id>.status

BEGIN. Read relevant files first. Implement. Verify. Commit.
"""


def extract_task_summary(stdout: str, task_id: str) -> str:
    """
    HARNESS FUNCTION: Extract a concise summary from task execution output.
    This becomes the 'latent state' passed to subsequent tasks (RecursiveMAS).

    H_0 strategy: Last 500 chars of stdout + any DONE/ERROR lines.
    The Meta-Harness proposer may improve this to extract more signal.
    """
    lines = stdout.split('\n')
    # Find key outcome lines
    key_lines = [
        line for line in lines
        if any(kw in line.lower() for kw in
               ['done', 'complete', 'error', 'failed', 'passed', 'commit', 'created', 'wrote'])
    ]
    summary = f"Task {task_id}:\n"
    if key_lines:
        summary += "\n".join(key_lines[-5:])
    else:
        summary += stdout[-300:] if stdout else "(no output)"
    return summary


def log_trace(goal_id: str, task_id: str, prompt: str,
              stdout: str, stderr: str, returncode: int,
              git_diff: str = "") -> Path:
    """
    HARNESS FUNCTION: Log FULL execution trace to filesystem.

    Meta-Harness key insight: Store everything -- not just scores.
    The proposer needs raw traces to diagnose failures and propose
    targeted harness improvements. Compressed summaries lose the signal.
    """
    trace_dir = TRACE_DIR / goal_id
    trace_dir.mkdir(parents=True, exist_ok=True)

    trace = {
        "task_id": task_id,
        "goal_id": goal_id,
        "harness_version": HARNESS_VERSION,
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,                # Full prompt sent to agent
        "stdout": stdout,                # Full agent output
        "stderr": stderr,                # Full stderr
        "returncode": returncode,
        "git_diff": git_diff,            # What code actually changed
        "outcome": "success" if returncode == 0 else "failure"
    }

    trace_path = trace_dir / f"{task_id}.trace.json"
    trace_path.write_text(json.dumps(trace, indent=2))

    # Also write human-readable version for grep
    readable_path = trace_dir / f"{task_id}.trace"
    readable_path.write_text(
        f"=== TASK: {task_id} ===\n"
        f"HARNESS: {HARNESS_VERSION}\n"
        f"OUTCOME: {trace['outcome']}\n"
        f"TIMESTAMP: {trace['timestamp']}\n\n"
        f"--- PROMPT ---\n{prompt[:2000]}\n\n"
        f"--- STDOUT ---\n{stdout[-3000:]}\n\n"
        f"--- GIT DIFF ---\n{git_diff[:2000]}\n"
    )

    return trace_path


def score_harness(audit_results: dict) -> dict:
    """
    HARNESS FUNCTION: Compute Pareto-optimal scores for this harness run.

    Meta-Harness uses Pareto dominance when multiple objectives matter.
    For /goal: accuracy (did tasks complete?) vs cost ($ spent on LLM).
    """
    checks = []
    for category in audit_results.values():
        if isinstance(category, dict):
            if "passed" in category:
                checks.append(category["passed"])
            else:
                for check in category.values():
                    if isinstance(check, dict) and "passed" in check:
                        checks.append(check["passed"])

    accuracy = int(sum(checks) / len(checks) * 100) if checks else 0
    cost = float(os.environ.get("_GOAL_ACTUAL_COST", "0.0"))

    return {
        "harness_version": HARNESS_VERSION,
        "accuracy": accuracy,
        "cost_usd": cost,
        "pareto_candidate": True,  # Will be filtered by actual Pareto frontier
        "timestamp": datetime.now().isoformat()
    }
