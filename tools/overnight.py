"""
tools/overnight.py — Overnight autonomous agent task runner.

Allows Bashara to assign tasks before sleeping and wake up to completed results.

Features:
  - Queue multiple tasks with dependencies
  - Each task assigned to the best specialist agent
  - Live progress sent via Telegram at each step
  - Final summary report sent on completion
  - Crash-safe: resumes from checkpoint if bot restarts
  - Dashboard integration: updates AGENT_STATUS for /dashboard command
  - Heartbeat: sends "still working..." every 15 min if tasks running
  - Max runtime guard: auto-stops after MAX_RUNTIME_HOURS
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

MAX_RUNTIME_HOURS = 10
HEARTBEAT_INTERVAL = 900   # 15 min
CHECKPOINT_PATH = Path.home() / ".legion_overnight_checkpoint.json"


# ── Status & Models ────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    DONE      = "done"
    FAILED    = "failed"
    SKIPPED   = "skipped"


@dataclass
class OvernightTask:
    task_id:    str
    title:      str
    prompt:     str
    agent:      str          # agent key from AGENT_MODELS
    status:     TaskStatus   = TaskStatus.PENDING
    result:     str          = ""
    error:      str          = ""
    started_at: float        = 0.0
    ended_at:   float        = 0.0
    tokens_used: int         = 0
    depends_on: list[str]    = field(default_factory=list)  # task_ids this depends on

    @property
    def duration_sec(self) -> float:
        if self.ended_at and self.started_at:
            return self.ended_at - self.started_at
        if self.started_at:
            return time.time() - self.started_at
        return 0.0

    @property
    def duration_str(self) -> str:
        secs = self.duration_sec
        if secs < 60:
            return f"{secs:.0f}s"
        return f"{secs/60:.1f}m"


# ── Global state ───────────────────────────────────────────────────────────────

# Map: job_id → list of OvernightTask
_jobs: dict[str, list[OvernightTask]] = {}
_active_job: Optional[str] = None       # currently running job id
_job_cancelled: dict[str, bool] = {}
_job_paused: dict[str, bool] = {}


# ── Agent Status (used by dashboard) ──────────────────────────────────────────
# Keyed by agent name → current status string
AGENT_STATUS: dict[str, dict] = {}


def _update_agent_status(
    agent: str,
    status: str,
    task_title: str = "",
    progress: str = "",
    job_id: str = "",
) -> None:
    AGENT_STATUS[agent] = {
        "status":     status,
        "task":       task_title,
        "progress":   progress,
        "job_id":     job_id,
        "updated_at": time.time(),
    }


# ── Checkpoint helpers ─────────────────────────────────────────────────────────

def _save_checkpoint(job_id: str, tasks: list[OvernightTask]) -> None:
    try:
        data = {
            "job_id": job_id,
            "saved_at": time.time(),
            "tasks": [
                {
                    **asdict(t),
                    "status": t.status.value,
                    "depends_on": t.depends_on,
                }
                for t in tasks
            ],
        }
        CHECKPOINT_PATH.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.warning("Checkpoint save failed: %s", e)


def load_checkpoint() -> Optional[tuple[str, list[OvernightTask]]]:
    if not CHECKPOINT_PATH.exists():
        return None
    try:
        data = json.loads(CHECKPOINT_PATH.read_text())
        job_id = data["job_id"]
        tasks = []
        for t in data["tasks"]:
            status_val = t.pop("status", "pending")
            ot = OvernightTask(**t)
            ot.status = TaskStatus(status_val)
            tasks.append(ot)
        logger.info("Loaded checkpoint: job=%s tasks=%d", job_id, len(tasks))
        return job_id, tasks
    except Exception as e:
        logger.warning("Checkpoint load failed: %s", e)
        return None


def clear_checkpoint() -> None:
    try:
        CHECKPOINT_PATH.unlink(missing_ok=True)
    except Exception:
        pass


# ── Job creation helpers ───────────────────────────────────────────────────────

def create_job(tasks: list[dict]) -> tuple[str, list[OvernightTask]]:
    """
    Create a new overnight job.
    tasks = [{"title": str, "prompt": str, "agent": str, "depends_on": [ids]}, ...]
    Returns (job_id, [OvernightTask])
    """
    job_id = str(uuid.uuid4())[:8]
    task_objs = []
    for t in tasks:
        ot = OvernightTask(
            task_id    = str(uuid.uuid4())[:6],
            title      = t["title"],
            prompt     = t["prompt"],
            agent      = t.get("agent", "general"),
            depends_on = t.get("depends_on", []),
        )
        task_objs.append(ot)
    _jobs[job_id] = task_objs
    logger.info("Created job %s with %d tasks", job_id, len(task_objs))
    return job_id, task_objs


async def plan_job_with_llm(
    goal: str,
    llm_call: Callable,
) -> list[dict]:
    """
    Use the architect agent to decompose a high-level goal into a
    structured list of overnight tasks with agent assignments.
    Returns list of task dicts ready for create_job().
    """
    from agents import AGENT_MODELS, build_system_prompt

    system = build_system_prompt(
        "You are a project planner. The user will describe a goal they want "
        "completed overnight. Decompose it into 3-8 concrete subtasks. "
        "For each subtask, assign the best specialist agent from this list: "
        "coding, debug, math, architect, analyst, researcher, marketer, devops, pm, general. "
        "Return ONLY a JSON array. No explanation, no markdown fences. "
        "Each item must have EXACTLY these fields: "
        '{"title": str, "prompt": str, "agent": str, "depends_on": []}. '
        "depends_on should contain title strings of prerequisite tasks (empty if none)."
    )
    raw = await llm_call(AGENT_MODELS["architect"], system, f"Goal: {goal}")

    import re
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?\n?", "", raw).strip().rstrip("`")

    try:
        tasks = json.loads(raw)
        # Validate structure
        validated = []
        for i, t in enumerate(tasks):
            if "title" not in t or "prompt" not in t:
                continue
            validated.append({
                "title":      str(t.get("title", f"Task {i+1}")),
                "prompt":     str(t.get("prompt", "")),
                "agent":      str(t.get("agent", "general")),
                "depends_on": list(t.get("depends_on", [])),
            })
        return validated
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON for task planning, using single-task fallback")
        return [{"title": goal[:80], "prompt": goal, "agent": "general", "depends_on": []}]


# ── Main runner ────────────────────────────────────────────────────────────────

async def run_overnight_job(
    job_id: str,
    tasks: list[OvernightTask],
    llm_call: Callable,
    notify_fn: Callable[[str], Coroutine],
    update_dashboard_fn: Optional[Callable] = None,
) -> dict:
    """
    Execute all tasks in the job.
    - Runs independent tasks in parallel
    - Runs dependent tasks after their prerequisites complete
    - Sends Telegram updates at each step
    - Returns summary dict
    """
    global _active_job
    _active_job = job_id
    _job_cancelled[job_id] = False
    _job_paused[job_id] = False

    total = len(tasks)
    start_time = time.time()
    deadline = start_time + MAX_RUNTIME_HOURS * 3600

    # Build title→task_id map for depends_on resolution
    title_to_id = {t.title: t.task_id for t in tasks}
    for t in tasks:
        t.depends_on = [title_to_id.get(dep, dep) for dep in t.depends_on]

    _save_checkpoint(job_id, tasks)

    await notify_fn(
        f"🌙 <b>Overnight job started</b> — Job <code>{job_id}</code>\n"
        f"📋 <b>{total} tasks</b> queued across agents\n"
        f"⏰ Max runtime: {MAX_RUNTIME_HOURS}h\n\n"
        + "\n".join(f"  {i+1}. [{t.agent}] {t.title}" for i, t in enumerate(tasks))
    )

    # Start heartbeat
    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(job_id, tasks, notify_fn),
        name=f"heartbeat-{job_id}"
    )

    completed_ids: set[str] = set()
    failed_ids: set[str] = set()

    while True:
        if _job_cancelled.get(job_id):
            await notify_fn(f"⛔ Job <code>{job_id}</code> cancelled.")
            break

        if time.time() > deadline:
            await notify_fn(f"⏰ Job <code>{job_id}</code> hit max runtime ({MAX_RUNTIME_HOURS}h). Stopping.")
            for t in tasks:
                if t.status == TaskStatus.PENDING:
                    t.status = TaskStatus.SKIPPED
            break

        # Find tasks ready to run (deps met, not yet started)
        ready = [
            t for t in tasks
            if t.status == TaskStatus.PENDING
            and all(dep in completed_ids or dep in failed_ids for dep in t.depends_on)
        ]

        if not ready:
            # Check if anything still running
            still_running = any(t.status == TaskStatus.RUNNING for t in tasks)
            if still_running:
                await asyncio.sleep(2)
                continue
            # Nothing ready and nothing running → done
            break

        # Handle pause
        while _job_paused.get(job_id):
            await asyncio.sleep(5)
            if _job_cancelled.get(job_id):
                break

        # Launch ready tasks in parallel
        run_tasks = []
        for t in ready:
            t.status = TaskStatus.RUNNING
            t.started_at = time.time()
            _update_agent_status(t.agent, "🟡 running", t.title, "starting...", job_id)
            if update_dashboard_fn:
                await update_dashboard_fn()
            run_tasks.append(
                asyncio.create_task(
                    _execute_single_task(t, job_id, llm_call, notify_fn, update_dashboard_fn),
                    name=f"task-{t.task_id}"
                )
            )

        if run_tasks:
            await asyncio.gather(*run_tasks, return_exceptions=True)

        # Update completion sets
        for t in tasks:
            if t.status == TaskStatus.DONE:
                completed_ids.add(t.task_id)
            elif t.status == TaskStatus.FAILED:
                failed_ids.add(t.task_id)

        _save_checkpoint(job_id, tasks)

    heartbeat_task.cancel()
    _active_job = None
    clear_checkpoint()

    # Mark idle agents
    for t in tasks:
        _update_agent_status(t.agent, "⚪ idle", "", "", "")

    summary = _build_summary(job_id, tasks, time.time() - start_time)
    await notify_fn(summary)
    return {"job_id": job_id, "tasks": tasks, "total_duration": time.time() - start_time}


async def _execute_single_task(
    task: OvernightTask,
    job_id: str,
    llm_call: Callable,
    notify_fn: Callable,
    update_dashboard_fn: Optional[Callable],
) -> None:
    from agents import AGENT_MODELS, FALLBACK_CHAIN, build_system_prompt
    from tools.memory import add_memory

    agent_key = task.agent
    model = AGENT_MODELS.get(agent_key, AGENT_MODELS["general"])
    system = build_system_prompt(
        f"You are the {agent_key} specialist in an overnight autonomous job. "
        "Work carefully and thoroughly — there's no user to ask follow-up questions. "
        "If something is unclear, make the best reasonable assumption and state it. "
        "Produce complete, actionable output. Cite sources where relevant."
    )

    try:
        await notify_fn(
            f"▶️ <b>[{agent_key.upper()}]</b> Starting: <i>{task.title}</i>"
        )
        _update_agent_status(agent_key, "🟡 running", task.title, "calling LLM...", job_id)
        if update_dashboard_fn:
            asyncio.create_task(update_dashboard_fn())

        result = await llm_call(model, system, task.prompt)

        task.result = result
        task.status = TaskStatus.DONE
        task.ended_at = time.time()
        _update_agent_status(agent_key, "🟢 done", task.title, f"✅ {task.duration_str}", job_id)

        # Save to memory
        try:
            await add_memory(
                f"Overnight task [{agent_key}]: {task.title}\n\nResult:\n{result[:800]}",
                tags=["overnight", agent_key, job_id],
                source="overnight",
            )
        except Exception:
            pass

        # Send result to Telegram (chunked)
        header = f"✅ <b>[{agent_key.upper()}]</b> <i>{task.title}</i> — done in {task.duration_str}\n\n"
        result_preview = result[:3500]
        if len(result) > 3500:
            result_preview += f"\n\n<i>...({len(result)-3500} chars truncated — saved to memory)</i>"
        await notify_fn(header + result_preview)

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        task.ended_at = time.time()
        _update_agent_status(agent_key, "🔴 failed", task.title, str(e)[:80], job_id)
        logger.exception("Task %s failed: %s", task.task_id, e)
        await notify_fn(
            f"❌ <b>[{agent_key.upper()}]</b> <i>{task.title}</i> failed\n"
            f"<code>{str(e)[:300]}</code>"
        )

    if update_dashboard_fn:
        asyncio.create_task(update_dashboard_fn())


async def _heartbeat_loop(
    job_id: str,
    tasks: list[OvernightTask],
    notify_fn: Callable,
) -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        if _job_cancelled.get(job_id):
            break
        done   = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        running = [t.title for t in tasks if t.status == TaskStatus.RUNNING]
        total  = len(tasks)
        running_str = ", ".join(running) if running else "none"
        await notify_fn(
            f"💓 <b>Overnight heartbeat</b> — Job <code>{job_id}</code>\n"
            f"✅ Done: {done}/{total}  ❌ Failed: {failed}  🟡 Running: {running_str}"
        )


def _build_summary(job_id: str, tasks: list[OvernightTask], total_sec: float) -> str:
    done    = [t for t in tasks if t.status == TaskStatus.DONE]
    failed  = [t for t in tasks if t.status == TaskStatus.FAILED]
    skipped = [t for t in tasks if t.status == TaskStatus.SKIPPED]
    total_min = total_sec / 60

    lines = [
        f"🌅 <b>Overnight job complete!</b> — <code>{job_id}</code>",
        f"⏱ Total time: <b>{total_min:.1f} min</b>",
        f"✅ Completed: <b>{len(done)}</b>  ❌ Failed: <b>{len(failed)}</b>  ⏭ Skipped: <b>{len(skipped)}</b>",
        "",
    ]
    if done:
        lines.append("<b>✅ Completed tasks:</b>")
        for t in done:
            lines.append(f"  • [{t.agent}] <i>{t.title}</i> — {t.duration_str}")
        lines.append("")
    if failed:
        lines.append("<b>❌ Failed tasks:</b>")
        for t in failed:
            lines.append(f"  • [{t.agent}] <i>{t.title}</i> — {t.error[:80]}")
        lines.append("")
    lines.append("Results saved to memory. Use /recall &lt;topic&gt; to retrieve them.")
    return "\n".join(lines)


# ── Control functions ──────────────────────────────────────────────────────────

def cancel_job(job_id: str) -> str:
    if job_id not in _jobs:
        return f"No job '{job_id}' found."
    _job_cancelled[job_id] = True
    return f"⛔ Job {job_id} cancellation requested."


def pause_job(job_id: str) -> str:
    if job_id not in _jobs:
        return f"No job '{job_id}' found."
    _job_paused[job_id] = True
    return f"⏸ Job {job_id} paused. Use /overnight_resume {job_id} to continue."


def resume_job(job_id: str) -> str:
    if job_id not in _jobs:
        return f"No job '{job_id}' found."
    _job_paused[job_id] = False
    return f"▶️ Job {job_id} resumed."


def get_active_job_id() -> Optional[str]:
    return _active_job


def get_job_tasks(job_id: str) -> list[OvernightTask]:
    return _jobs.get(job_id, [])


def list_all_jobs() -> str:
    if not _jobs:
        return "No overnight jobs registered."
    lines = ["<b>🌙 Overnight Jobs</b>\n"]
    for jid, tasks in _jobs.items():
        done  = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        total = len(tasks)
        active_marker = " ← active" if jid == _active_job else ""
        lines.append(f"  <code>{jid}</code> — {done}/{total} done{active_marker}")
    return "\n".join(lines)
