"""
tools/goal_runner.py
Main orchestrator for the /goal autonomous delivery system.
Called from the Telegram bot via: await run_goal(goal_text, chat_id, bot)
Can also be run standalone: python tools/goal_runner.py "build the feature"
"""

import asyncio
import json
import os
import subprocess
import sys
import io
import contextlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any

from minisweagent.agents.default import DefaultAgent, AgentConfig
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.environments.local import LocalEnvironment

from tools.goal_planner import plan_goal
from tools.goal_auditor import run_full_audit, format_telegram_report


GOAL_DIR = Path(".goal")
STATUS_FILE = GOAL_DIR / "STATUS.md"
LOGS_DIR = GOAL_DIR / "logs"
CHECKPOINTS_DIR = GOAL_DIR / "checkpoints"


def update_status(goal: str, status: str, goal_id: str = ""):
    """Update .goal/STATUS.md — visible to all agents."""
    STATUS_FILE.write_text(f"""# Goal Runner Status

## Current Goal
{goal}

## Status
{status}

## Goal ID
{goal_id}

## Last Updated
{datetime.now().isoformat()}
""")


def get_mini_agent() -> DefaultAgent:
    """Create a configured mini-SWE-agent instance."""
    # Get API credentials
    openai_key = os.getenv("OPENAI_API_KEY", "legion-proxy-key")
    openai_base = os.getenv("OPENAI_BASE_URL", "http://localhost:4000")

    # Get model name
    model_name = os.getenv("MSWEA_MODEL_NAME", "openai/minimax-primary")

    # Set environment for litellm
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["OPENAI_BASE_URL"] = openai_base

    model = LitellmModel(model_name=model_name)

    config = AgentConfig(
        system_template="You are an expert coding agent. Execute the task with bash commands only.",
        instance_template="Task: {task}",
        step_limit=100,
        cost_limit=float(os.getenv("MSWEA_GLOBAL_COST_LIMIT", "5.0")),
        output_path=None
    )

    return DefaultAgent(model, LocalEnvironment(), config=config)


def _check_litellm_running() -> bool:
    """Check if LiteLLM proxy is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "2", "-H", "Authorization: Bearer legion-proxy-key",
             "http://localhost:4000/health"],
            capture_output=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False


def build_task_prompt(task: dict, plan: dict, repo_root: str,
                       phase_num: int, task_num: int) -> str:
    """Build a complete, self-contained prompt for a single task."""
    criteria_str = "\n".join(f"  - {c}" for c in task.get("acceptance_criteria", []))
    files_str = "\n".join(f"  - {f}" for f in task.get("files_likely_touched", []))

    return f"""You are working on the "{plan['goal']}" project.
Repository root: {repo_root}
Project type: {plan.get('project', 'unknown')}

CURRENT TASK (Phase {phase_num}, Task {task_num}):
{task['description']}

ACCEPTANCE CRITERIA (all must be true when you finish):
{criteria_str}

FILES LIKELY INVOLVED:
{files_str}

ROLLBACK IF BLOCKED: {task.get('rollback', 'git checkout .')}

CRITICAL RULES:
1. Work only in {repo_root} — do not touch files outside this repo
2. NEVER modify tools/mirofish/ — it is a read-only git submodule
3. NEVER hardcode API keys — always use os.getenv()
4. When done, run: git add -A && git commit -m "feat({plan.get('project','app')}): {task['id']} - {task['description'][:60]}"
5. If a criterion cannot be met, write a clear note in .goal/BLOCKERS.md and continue

Start by reading the relevant files, then implement, then verify each criterion.
"""


async def execute_task_with_mini(
    task: dict,
    plan: dict,
    repo_root: str,
    phase_num: int,
    task_num: int,
    notify_fn: Optional[Callable] = None
) -> dict:
    """Run a single task through mini-SWE-agent. Returns result dict."""
    task_id = task.get("id", f"T{phase_num}.{task_num}")
    log_path = LOGS_DIR / f"{task_id}.log"
    checkpoint_path = CHECKPOINTS_DIR / f"{task_id}.json"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

    if notify_fn:
        await notify_fn(f"⚙️ Starting task {task_id}: {task['description'][:80]}...")

    prompt = build_task_prompt(task, plan, repo_root, phase_num, task_num)

    # Write prompt to log for debugging
    log_path.write_text(f"=== Task {task_id} ===\n\n{prompt}\n\n=== Agent Output ===\n")

    try:
        agent = get_mini_agent()

        # Capture stdout/stderr during agent run
        output_buffer = io.StringIO()

        with contextlib.redirect_stdout(output_buffer):
            with contextlib.redirect_stderr(output_buffer):
                agent.run(prompt)

        output = output_buffer.getvalue()
        log_path.open("a").write(output)

        result = {
            "task_id": task_id,
            "status": "completed",
            "output_preview": output[-1000:],
            "timestamp": datetime.now().isoformat()
        }

        # Save checkpoint
        checkpoint_path.write_text(json.dumps(result, indent=2))

        if notify_fn:
            await notify_fn(f"✅ Task {task_id} complete")

        return result

    except Exception as e:
        error_msg = f"Task {task_id} failed: {str(e)}"
        log_path.open("a").write(f"\n\nERROR: {error_msg}")

        result = {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        checkpoint_path.write_text(json.dumps(result, indent=2))

        if notify_fn:
            await notify_fn(f"⚠️ Task {task_id} hit an issue — continuing...")

        return result


def open_pull_request(plan: dict, goal_id: str) -> Optional[str]:
    """Open a GitHub PR using gh CLI. Returns PR URL or None."""
    try:
        # Create branch name from goal
        branch_name = f"goal/{goal_id}"
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

        pr_title = plan.get("pr_title", f"feat: {plan['goal'][:60]}")
        pr_body = plan.get("pr_body", f"Automated delivery by /goal system\n\nGoal: {plan['goal']}")

        result = subprocess.run(
            ["gh", "pr", "create",
             "--title", pr_title,
             "--body", pr_body,
             "--base", "main"],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            pr_url = result.stdout.strip().split("\n")[-1]
            return pr_url
        else:
            print(f"PR creation failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"PR creation error: {e}")
        return None


async def run_goal(
    goal: str,
    chat_id: Optional[str] = None,
    bot: Any = None,
    cost_limit: float = 5.0,
    call_limit: int = 200
) -> dict:
    """
    Main entry point. Orchestrates full goal delivery pipeline.

    Args:
        goal: Natural language goal description
        chat_id: Telegram chat ID for notifications (optional)
        bot: Telegram bot instance for notifications (optional)
        cost_limit: Max $ to spend on LLM calls
        call_limit: Max LLM API calls

    Returns:
        Result dict with status, score, pr_url, report
    """
    goal_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    repo_root = str(Path(".").resolve())

    # Set cost/call limits as env vars for mini-SWE-agent
    os.environ["MSWEA_GLOBAL_COST_LIMIT"] = str(cost_limit)
    os.environ["MSWEA_GLOBAL_CALL_LIMIT"] = str(call_limit)
    os.environ["MSWEA_COST_TRACKING"] = "ignore_errors"

    # Notification helper
    async def notify(msg: str):
        print(f"[NOTIFY] {msg}")
        if bot and chat_id:
            try:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Telegram notify failed: {e}")

    try:
        # Step 1: Update status
        update_status(goal, "planning", goal_id)
        await notify(f"🎯 *Goal received:* {goal}\n\n⏳ Decomposing into tasks...")

        # Step 2: Plan
        plan, plan_path, goal_id = await plan_goal(goal)
        total_tasks = sum(len(p["tasks"]) for p in plan.get("phases", []))
        total_phases = len(plan.get("phases", []))
        est_hours = plan.get("estimated_hours", "?")

        await notify(
            f"📋 *Plan ready*\n"
            f"Phases: {total_phases}\n"
            f"Tasks: {total_tasks}\n"
            f"Estimated: {est_hours}h\n"
            f"Starting execution..."
        )

        # Step 3: Execute phase by phase
        update_status(goal, "executing", goal_id)
        completed_tasks = []
        failed_tasks = []

        for phase in plan.get("phases", []):
            phase_num = phase["phase"]
            phase_name = phase["name"]
            tasks = phase.get("tasks", [])

            await notify(f"🔄 *Phase {phase_num}/{total_phases}:* {phase_name} ({len(tasks)} tasks)")

            for i, task in enumerate(tasks, 1):
                result = await execute_task_with_mini(
                    task, plan, repo_root, phase_num, i, notify_fn=notify
                )
                if result["status"] == "completed":
                    completed_tasks.append(result["task_id"])
                else:
                    failed_tasks.append(result["task_id"])

            # Phase-level audit
            phase_audit = run_full_audit(goal, goal_id, plan, phase=f"phase_{phase_num}")
            if phase_audit["score"] < 60:
                await notify(
                    f"⚠️ Phase {phase_num} audit score: {phase_audit['score']}/100\n"
                    f"Continuing to next phase..."
                )
            else:
                await notify(f"✅ Phase {phase_num} audit: {phase_audit['score']}/100")

        # Step 4: Final audit
        update_status(goal, "auditing", goal_id)
        await notify("🔍 Running final end-to-end audit...")

        final_audit = run_full_audit(goal, goal_id, plan, phase="final")

        # Step 5: Open PR
        pr_url = None
        if final_audit["score"] >= 60:
            await notify("📤 Opening Pull Request...")
            pr_url = open_pull_request(plan, goal_id)
            if pr_url:
                final_audit["pr_url"] = pr_url

        # Step 6: Final report
        update_status(goal, "completed", goal_id)
        report = format_telegram_report(goal, final_audit, goal_id, "final")

        summary = (
            f"🎉 *Goal Delivered!*\n\n"
            f"**Tasks:** {len(completed_tasks)}/{total_tasks} completed\n"
            f"**Audit:** {final_audit['score']}/100 {final_audit['grade']}\n"
        )
        if pr_url:
            summary += f"**PR:** {pr_url}\n"
        if failed_tasks:
            summary += f"**Issues:** {', '.join(failed_tasks)}\n"
        summary += f"\n{report}"

        await notify(summary)

        return {
            "status": "completed",
            "goal_id": goal_id,
            "score": final_audit["score"],
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "pr_url": pr_url,
            "plan_path": str(plan_path)
        }

    except Exception as e:
        error_msg = f"Goal runner crashed: {str(e)}"
        update_status(goal, f"ERROR: {error_msg}", goal_id)
        if notify:
            await notify(f"❌ *Goal failed:* {error_msg}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/goal_runner.py \"your goal here\"")
        sys.exit(1)
    goal = " ".join(sys.argv[1:])

    # Run synchronously for CLI usage
    async def run_sync():
        return await run_goal(goal)

    result = asyncio.run(run_sync())
    print(json.dumps(result, indent=2))