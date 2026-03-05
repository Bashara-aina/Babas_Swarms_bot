# /home/newadmin/swarm-bot/task_orchestrator.py
"""Task chaining, scheduled monitoring, and confirmation queue.

Enables multi-step autonomous workflows:
    "Check terminal errors → fix code → restart service"
    "Monitor training every 5 minutes → alert on loss spike"

Safety:
- Destructive commands always paused for /confirm yes|no
- Max 10 steps per chain
- Monitoring tasks can be cancelled with /cancel <task_id>
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

MAX_CHAIN_STEPS = 10


# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class TaskStep:
    """A single step in a task chain.

    Attributes:
        description: Human-readable description of what this step does.
        fn: Async callable that executes the step.
        requires_confirmation: Whether to pause and ask user before executing.
    """

    description: str
    fn: Callable[..., Coroutine[Any, Any, str]]
    requires_confirmation: bool = False


@dataclass
class PendingConfirmation:
    """Holds a paused action waiting for user approval.

    Attributes:
        action_id: Unique ID for /confirm yes <id>.
        description: What will happen if confirmed.
        fn: Async callable to execute on confirmation.
        created_at: Unix timestamp of when this was queued.
    """

    action_id: str
    description: str
    fn: Callable[..., Coroutine[Any, Any, str]]
    created_at: float = field(default_factory=time.time)


@dataclass
class MonitorTask:
    """A recurring scheduled task.

    Attributes:
        task_id: Unique ID for /cancel <task_id>.
        description: What is being monitored.
        interval_sec: How often to run (seconds).
        fn: Async callable that returns the status string.
        notify_fn: Callback to send alerts to the user.
        running: Whether this task is active.
    """

    task_id: str
    description: str
    interval_sec: int
    fn: Callable[..., Coroutine[Any, Any, str]]
    notify_fn: Callable[[str], Coroutine[Any, Any, None]]
    running: bool = True


# ── Global State ───────────────────────────────────────────────────────────────

# action_id → PendingConfirmation
_pending: dict[str, PendingConfirmation] = {}

# task_id → MonitorTask
_monitors: dict[str, MonitorTask] = {}

# Confirmation expiry: 5 minutes
CONFIRMATION_TTL_SEC = 300


# ── Task Chain Execution ───────────────────────────────────────────────────────

async def execute_chain(
    steps: list[TaskStep],
    progress_fn: Callable[[str], Coroutine[Any, Any, None]],
    confirm_fn: Callable[[str, str], Coroutine[Any, Any, None]],
) -> str:
    """Execute a sequence of steps, pausing on destructive ones.

    Args:
        steps: Ordered list of TaskStep objects.
        progress_fn: Async callback to send progress messages to the user.
        confirm_fn: Async callback(action_id, description) to request confirmation.

    Returns:
        Final summary of all step outputs.
    """
    if len(steps) > MAX_CHAIN_STEPS:
        raise ValueError(f"Chain exceeds max steps ({MAX_CHAIN_STEPS})")

    outputs: list[str] = []

    for i, step in enumerate(steps, 1):
        await progress_fn(f"Step {i}/{len(steps)}: {step.description}")

        if step.requires_confirmation:
            action_id = _queue_confirmation(step.description, step.fn)
            await confirm_fn(action_id, step.description)
            outputs.append(f"[Step {i} paused — waiting for /confirm yes {action_id}]")
            # Remaining steps are abandoned until confirmed; chain ends here
            return "\n\n".join(outputs)

        try:
            result = await step.fn()
            outputs.append(f"[Step {i}] {step.description}\n{result}")
            logger.info("Chain step %d complete", i)
        except Exception as exc:
            logger.exception("Chain step %d failed: %s", i, exc)
            outputs.append(f"[Step {i} ERROR] {step.description}\nError: {exc}")
            break

    return "\n\n".join(outputs) if outputs else "Chain completed with no output."


# ── Confirmation Queue ─────────────────────────────────────────────────────────

def _queue_confirmation(description: str, fn: Callable) -> str:
    """Add a pending confirmation and return its ID.

    Args:
        description: Human-readable description of the action.
        fn: Async callable to execute if confirmed.

    Returns:
        Short action ID (first 8 chars of UUID).
    """
    action_id = str(uuid.uuid4())[:8]
    _pending[action_id] = PendingConfirmation(
        action_id=action_id,
        description=description,
        fn=fn,
    )
    logger.info("Queued confirmation %s: %s", action_id, description)
    return action_id


def queue_confirmation(description: str, fn: Callable) -> str:
    """Public: queue a destructive action for user confirmation.

    Args:
        description: What will happen.
        fn: Async callable to execute on confirmation.

    Returns:
        action_id string.
    """
    return _queue_confirmation(description, fn)


async def confirm_action(action_id: str) -> str:
    """Execute a pending confirmation by ID.

    Args:
        action_id: ID from /confirm yes <id>.

    Returns:
        Result string from the confirmed action, or error message.
    """
    _expire_old_confirmations()

    pending = _pending.pop(action_id, None)
    if pending is None:
        return f"No pending action '{action_id}' (may have expired after 5 min)"

    logger.info("Executing confirmed action %s: %s", action_id, pending.description)
    try:
        result = await pending.fn()
        return f"Confirmed: {pending.description}\n\n{result}"
    except Exception as exc:
        logger.exception("Confirmed action failed: %s", exc)
        return f"Action failed: {exc}"


def deny_action(action_id: str) -> str:
    """Cancel a pending confirmation.

    Args:
        action_id: ID from /confirm no <id>.

    Returns:
        Cancellation message.
    """
    pending = _pending.pop(action_id, None)
    if pending is None:
        return f"No pending action '{action_id}'"
    logger.info("Denied action %s: %s", action_id, pending.description)
    return f"Cancelled: {pending.description}"


def list_pending() -> str:
    """Return a formatted list of all pending confirmations.

    Returns:
        HTML-formatted list, or message if none pending.
    """
    _expire_old_confirmations()
    if not _pending:
        return "No pending confirmations."

    lines = ["<b>Pending Confirmations</b>\n"]
    for aid, p in _pending.items():
        age = int(time.time() - p.created_at)
        lines.append(
            f"  <code>{aid}</code> — {p.description} ({age}s ago)\n"
            f"  → <code>/confirm yes {aid}</code> or <code>/confirm no {aid}</code>"
        )
    return "\n\n".join(lines)


def _expire_old_confirmations() -> None:
    """Remove confirmations older than CONFIRMATION_TTL_SEC."""
    now = time.time()
    expired = [
        aid for aid, p in _pending.items()
        if now - p.created_at > CONFIRMATION_TTL_SEC
    ]
    for aid in expired:
        logger.info("Expired confirmation %s", aid)
        del _pending[aid]


# ── Monitoring Tasks ───────────────────────────────────────────────────────────

async def start_monitor(
    description: str,
    interval_sec: int,
    fn: Callable[..., Coroutine[Any, Any, str]],
    notify_fn: Callable[[str], Coroutine[Any, Any, None]],
    alert_if: Optional[Callable[[str], bool]] = None,
) -> str:
    """Start a recurring monitoring task.

    Args:
        description: What is being monitored (shown in /monitors list).
        interval_sec: How often to run (e.g. 300 = every 5 minutes).
        fn: Async callable returning status string.
        notify_fn: Async callback to send alerts to user.
        alert_if: Optional predicate — only notify if True (e.g. loss spike detector).

    Returns:
        task_id string for use with /cancel.
    """
    task_id = str(uuid.uuid4())[:8]

    monitor = MonitorTask(
        task_id=task_id,
        description=description,
        interval_sec=interval_sec,
        fn=fn,
        notify_fn=notify_fn,
        running=True,
    )
    _monitors[task_id] = monitor

    asyncio.create_task(_monitor_loop(monitor, alert_if), name=f"monitor-{task_id}")
    logger.info("Started monitor %s: %s (every %ds)", task_id, description, interval_sec)
    return task_id


async def _monitor_loop(
    monitor: MonitorTask,
    alert_if: Optional[Callable[[str], bool]],
) -> None:
    """Internal loop for a monitoring task.

    Args:
        monitor: The MonitorTask to run.
        alert_if: Optional predicate to filter notifications.
    """
    while monitor.running:
        try:
            result = await monitor.fn()
            should_notify = alert_if(result) if alert_if else True
            if should_notify:
                await monitor.notify_fn(
                    f"Monitor <b>{monitor.description}</b>\n\n<pre>{result[:2000]}</pre>"
                )
        except Exception as exc:
            logger.exception("Monitor %s error: %s", monitor.task_id, exc)
            await monitor.notify_fn(
                f"Monitor <b>{monitor.description}</b> error: {exc}"
            )

        await asyncio.sleep(monitor.interval_sec)


def cancel_monitor(task_id: str) -> str:
    """Stop a running monitor task.

    Args:
        task_id: ID returned by start_monitor.

    Returns:
        Cancellation message.
    """
    monitor = _monitors.pop(task_id, None)
    if monitor is None:
        return f"No monitor '{task_id}' found."
    monitor.running = False
    logger.info("Cancelled monitor %s: %s", task_id, monitor.description)
    return f"Stopped monitor: {monitor.description}"


def list_monitors() -> str:
    """Return formatted list of active monitors.

    Returns:
        HTML string for Telegram, or message if none active.
    """
    active = {tid: m for tid, m in _monitors.items() if m.running}
    if not active:
        return "No active monitors."

    lines = ["<b>Active Monitors</b>\n"]
    for tid, m in active.items():
        lines.append(
            f"  <code>{tid}</code> — {m.description} (every {m.interval_sec}s)\n"
            f"  → <code>/cancel {tid}</code>"
        )
    return "\n\n".join(lines)


# ── Convenience: Common Monitors ───────────────────────────────────────────────

def make_loss_spike_detector(threshold: float = 0.5) -> Callable[[str], bool]:
    """Return a predicate that detects loss spikes in training output.

    Args:
        threshold: Alert if 'loss' value in text exceeds this (simple heuristic).

    Returns:
        Callable predicate for use with start_monitor's alert_if parameter.
    """
    import re

    def _detect(text: str) -> bool:
        matches = re.findall(r"loss[:\s=]+([0-9]+\.?[0-9]*)", text, re.IGNORECASE)
        for m in matches:
            try:
                if float(m) > threshold:
                    return True
            except ValueError:
                pass
        return "nan" in text.lower() or "inf" in text.lower()

    return _detect
