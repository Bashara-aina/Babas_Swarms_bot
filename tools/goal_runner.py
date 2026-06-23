"""
tools/goal_runner.py
Main orchestrator -- RecursiveMAS inner loop pattern.
Agents share latent state (execution traces) rather than raw text.
"""

import asyncio
import json
import os
import subprocess
import sys
import io
import contextlib
import importlib.util
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any

_minisweagent_available = True
try:
    from minisweagent.agents.default import DefaultAgent, AgentConfig
    from minisweagent.models.litellm_model import LitellmModel
    from minisweagent.environments.local import LocalEnvironment
except ImportError:
    _minisweagent_available = False
    DefaultAgent = None
    AgentConfig = None
    LitellmModel = None
    LocalEnvironment = None
    logging.warning("minisweagent not installed -- some goal-runner features disabled")

from tools.goal_planner import plan_goal  # noqa: E402
from tools.goal_auditor import run_full_audit  # noqa: E402

GOAL_DIR = Path(".goal")
STATUS_FILE = GOAL_DIR / "STATUS.md"
LOGS_DIR = GOAL_DIR / "logs"
TRACES_DIR = GOAL_DIR / "traces"


def update_status(goal: str, status: str, goal_id: str = ""):
    STATUS_FILE.write_text(
        f"# Goal Runner Status\n\n"
        f"## Current Goal\n{goal}\n\n"
        f"## Status\n{status}\n\n"
        f"## Goal ID\n{goal_id}\n\n"
        f"## Last Updated\n{datetime.now().isoformat()}\n"
    )


def _load_harness():
    """Load current harness from .goal/harnesses/current/harness.py"""
    harness_path = Path(".goal/harnesses/current/harness.py")
    if not harness_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("harness", harness_path)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    return h


def get_mini_agent() -> DefaultAgent:
    """Build mini-SWE-agent v2.2.8+ with proper AgentConfig."""
    if not _minisweagent_available:
        raise ImportError(
            "minisweagent is not installed. Install with: pip install minisweagent"
        )
    import yaml
    from pathlib import Path

    model_name = os.getenv("MSWEA_MODEL_NAME", "openai/minimax-primary")

    # Load templates from mini.yaml (mini-swe-agent v2.2.8)
    config_path = Path(__file__).parent.parent / ".goal" / "mini_agent_config.yaml"
    if not config_path.exists():
        # Fallback to installed package config
        import importlib.resources
        for p in importlib.resources.files("minisweagent").rglob("config/mini.yaml"):
            config_path = str(p)
            break

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    agent_cfg = cfg["agent"]
    return DefaultAgent(
        LitellmModel(model_name=model_name),
        LocalEnvironment(),
        config_class=AgentConfig,
        system_template=agent_cfg["system_template"],
        instance_template=agent_cfg["instance_template"],
        step_limit=agent_cfg.get("step_limit", 0),
        cost_limit=agent_cfg.get("cost_limit", 3.0),
    )


def _litellm_running() -> bool:
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "2", "http://localhost:4000/health"],
            capture_output=True, timeout=3
        )
        return r.returncode == 0
    except Exception:
        return False


def get_git_diff() -> str:
    """Get current git diff for trace logging."""
    r = subprocess.run(["git", "diff", "--stat", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


async def execute_task(
    task: dict, plan: dict, repo_root: str,
    goal_id: str, phase_num: int, task_num: int,
    prior_task_summaries: list[str],  # RecursiveMAS latent state
    notify_fn: Optional[Callable] = None
) -> dict:
    """
    Execute one task via mini-SWE-agent.
    Implements RecursiveMAS: passes prior task summaries as latent state.
    Logs full trace to .goal/traces/ (Meta-Harness principle).
    """
    task_id = task.get("id", f"T{phase_num}.{task_num}")
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    (TRACES_DIR / goal_id).mkdir(parents=True, exist_ok=True)

    if notify_fn:
        await notify_fn(f"⚙️ Task {task_id}: {task['description'][:60]}...")

    # Check for stop signal
    stop_signal = GOAL_DIR / "STOP_SIGNAL"
    if stop_signal.exists():
        stop_signal.unlink()
        raise InterruptedError("Stop signal received")

    # Load harness (Meta-Harness: harness determines what context each task sees)
    harness = _load_harness()

    if harness:
        prompt = harness.build_task_prompt(
            task, plan, repo_root, phase_num, task_num,
            prior_task_traces=prior_task_summaries
        )
    else:
        # Fallback: inline prompt builder
        criteria_str = "\n".join(f"  - {c}" for c in task.get("acceptance_criteria", []))
        files_str = "\n".join(f"  - {f}" for f in task.get("files_likely_touched", []))
        prior_context = ""
        if prior_task_summaries:
            prior_context = "\n\n=== COMPLETED TASKS ===\n" + "\n".join(prior_task_summaries[-3:])
        prompt = f"""You are working on: {plan['goal']}
Repository: {repo_root}

{prior_context}

==============================================================================
TASK: {task_id} -- {task['description']}
==============================================================================
ACCEPTANCE CRITERIA:
{criteria_str}

FILES: {files_str}

CRITICAL:
1. Work ONLY in {repo_root}
2. NEVER touch tools/mirofish/ (read-only git submodule)
3. Use os.getenv() for secrets, never hardcode
4. When done: git add -A && git commit -m "feat({plan.get('project','app')}): {task_id}"

BEGIN. Implement and verify each criterion.
"""

    log_path = LOGS_DIR / f"{task_id}.log"
    log_path.write_text(f"=== Task {task_id} ===\n\n{prompt}\n\n=== Output ===\n")

    try:
        agent = get_mini_agent()
        buf = io.StringIO()
        err_buf = io.StringIO()

        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err_buf):
            agent.run(prompt)

        stdout = buf.getvalue()
        stderr = err_buf.getvalue()
        returncode = 0

    except Exception as e:
        stdout = ""
        stderr = str(e)
        returncode = 1

    git_diff = get_git_diff()
    log_path.open("a").write(stdout)
    if stderr:
        log_path.open("a").write(f"\n\nSTDERR:\n{stderr}")

    # Log FULL trace via harness (Meta-Harness: raw traces, not summaries)
    if harness and hasattr(harness, 'log_trace'):
        harness.log_trace(goal_id, task_id, prompt, stdout, stderr, returncode, git_diff)

    # Extract concise summary for next task's latent state (RecursiveMAS)
    if harness and hasattr(harness, 'extract_task_summary'):
        summary = harness.extract_task_summary(stdout, task_id)
    else:
        lines = stdout.split('\n')
        key_lines = [line for line in lines if any(kw in line.lower() for kw in
                   ['done', 'complete', 'error', 'failed', 'passed', 'commit', 'created'])]
        summary = f"Task {task_id}: " + (" | ".join(key_lines[-5:]) if key_lines else stdout[-200:])

    result = {
        "task_id": task_id,
        "status": "completed" if returncode == 0 else "failed",
        "summary": summary,
        "returncode": returncode,
        "timestamp": datetime.now().isoformat()
    }

    # Save checkpoint
    (GOAL_DIR / "checkpoints" / f"{task_id}.json").write_text(json.dumps(result))

    if notify_fn:
        icon = "✅" if result["status"] == "completed" else "⚠️"
        await notify_fn(f"{icon} Task {task_id} {result['status']}")

    return result


def open_pull_request(plan: dict, goal_id: str) -> Optional[str]:
    """Open GitHub PR via gh CLI. Returns URL or None."""
    if not subprocess.run(["which", "gh"], capture_output=True).returncode == 0:
        return None
    try:
        branch = f"goal/{goal_id}"
        subprocess.run(["git", "checkout", "-b", branch], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch], check=True, cwd=".")
        result = subprocess.run(
            ["gh", "pr", "create",
             "--title", plan.get("pr_title", f"feat: {plan['goal'][:60]}"),
             "--body", plan.get("pr_body", f"Automated by /goal\n\nGoal: {plan['goal']}"),
             "--base", "main"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[-1]
    except Exception as e:
        print(f"PR error: {e}")
    return None


async def run_goal(
    goal: str,
    chat_id: Optional[str] = None,
    bot: Any = None,
    cost_limit: float = 5.0,
    call_limit: int = 200
) -> dict:
    """
    Main orchestrator. RecursiveMAS pattern:
    - Planner -> Executor (with latent state from prior tasks)
    - Executor -> Auditor (with full execution trace)
    - Auditor -> Meta-Harness proposer (for future harness improvement)
    """
    goal_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    repo_root = str(Path(".").resolve())

    os.environ["MSWEA_GLOBAL_COST_LIMIT"] = str(cost_limit)
    os.environ["MSWEA_GLOBAL_CALL_LIMIT"] = str(call_limit)
    os.environ["MSWEA_COST_TRACKING"] = "ignore_errors"

    async def notify(msg: str):
        print(f"[NOTIFY] {msg}")
        if bot and chat_id:
            try:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            except Exception:
                pass

    try:
        update_status(goal, "planning", goal_id)
        await notify(f"🎯 *Goal:* {goal}\n\n⏳ Decomposing into tasks...")

        plan, plan_path, goal_id = await plan_goal(goal)
        total_tasks = sum(len(p["tasks"]) for p in plan.get("phases", []))
        total_phases = len(plan.get("phases", []))

        await notify(
            f"📋 *Plan ready*\n"
            f"Phases: {total_phases} | Tasks: {total_tasks} | "
            f"Est: {plan.get('estimated_hours','?')}h\n"
            f"Starting..."
        )

        update_status(goal, "executing", goal_id)
        completed, failed = [], []

        # RecursiveMAS: maintain running latent state across ALL tasks
        # Each task's summary is passed to the next task as context
        global_latent_state: list[str] = []

        for phase in plan.get("phases", []):
            phase_num = phase["phase"]
            phase_name = phase["name"]
            tasks = phase.get("tasks", [])
            await notify(f"🔄 *Phase {phase_num}/{total_phases}:* {phase_name}")

            for i, task in enumerate(tasks, 1):
                result = await execute_task(
                    task, plan, repo_root, goal_id,
                    phase_num, i,
                    prior_task_summaries=global_latent_state,
                    notify_fn=notify
                )

                # Update global latent state (RecursiveMAS cross-agent transfer)
                global_latent_state.append(result["summary"])
                global_latent_state = global_latent_state[-5:]  # Keep last 5 to avoid token explosion

                if result["status"] == "completed":
                    completed.append(result["task_id"])
                else:
                    failed.append(result["task_id"])

            # Phase audit
            phase_audit = run_full_audit(goal, goal_id, plan, phase=f"phase_{phase_num}")
            score_ico = "✅" if phase_audit["score"] >= 60 else "⚠️"
            await notify(f"{score_ico} Phase {phase_num} audit: {phase_audit['score']}/100")

        # Final audit
        update_status(goal, "auditing", goal_id)
        await notify("🔍 Running final audit...")
        final_audit = run_full_audit(goal, goal_id, plan, phase="final")

        # Open PR
        pr_url = None
        if final_audit["score"] >= 50:
            pr_url = open_pull_request(plan, goal_id)
            if pr_url:
                final_audit["pr_url"] = pr_url

        # Write Meta-Harness proposer trigger
        proposer_trigger = Path(".goal/harnesses/PROPOSE_NEXT.md")
        proposer_trigger.write_text(
            f"# Meta-Harness: Propose Next Harness\n\n"
            f"Goal ID: {goal_id}\n"
            f"Final score: {final_audit['score']}/100\n"
            f"Completed: {len(completed)}/{len(completed)+len(failed)}\n\n"
            f"## To evolve harness:\n"
            f"  python tools/goal_harness_proposer.py\n"
            f"  # or: ./scripts/evolve_harness.sh\n\n"
            f"## Read traces:\n"
            f"  ls .goal/traces/{goal_id}/\n\n"
            f"## Key improvement targets:\n"
            f"  .goal/harnesses/current/harness.py\n"
        )

        update_status(goal, "completed", goal_id)
        summary_msg = (
            f"🎉 *Goal Delivered!*\n\n"
            f"Tasks: {len(completed)}/{total_tasks} | "
            f"Audit: {final_audit['score']}/100 {final_audit['grade']}\n"
        )
        if pr_url:
            summary_msg += f"PR: {pr_url}\n"
        if failed:
            summary_msg += f"Issues: {', '.join(failed)}\n"
        await notify(summary_msg)

        return {
            "status": "completed", "goal_id": goal_id,
            "score": final_audit["score"],
            "completed_tasks": completed, "failed_tasks": failed,
            "pr_url": pr_url, "plan_path": str(plan_path)
        }

    except InterruptedError:
        update_status(goal, "stopped", goal_id)
        await notify("⏹ Goal stopped by user.")
        return {"status": "stopped", "goal_id": goal_id}
    except Exception as e:
        update_status(goal, f"ERROR: {e}", goal_id)
        await notify(f"❌ *Goal failed:* {str(e)[:300]}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/goal_runner.py \"your goal\"")
        sys.exit(1)
    result = asyncio.run(run_goal(" ".join(sys.argv[1:])))
    print(json.dumps(result, indent=2))
