# /home/newadmin/swarm-bot/tests/test_task_orchestrator.py
"""Tests for task_orchestrator.py — run with: pytest tests/test_task_orchestrator.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import pytest
import core.nexus_orchestrator as task_orchestrator


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_queue_and_confirm():
    async def _action():
        return "action executed"

    action_id = task_orchestrator.queue_confirmation("test action", _action)
    assert action_id in task_orchestrator._pending

    result = run(task_orchestrator.confirm_action(action_id))
    assert "action executed" in result
    assert action_id not in task_orchestrator._pending


def test_queue_and_deny():
    async def _action():
        return "should not run"

    action_id = task_orchestrator.queue_confirmation("deny this", _action)
    result = task_orchestrator.deny_action(action_id)
    assert "Cancelled" in result
    assert action_id not in task_orchestrator._pending


def test_confirm_unknown_id():
    result = run(task_orchestrator.confirm_action("nonexistent"))
    assert "No pending" in result


def test_list_pending_empty():
    task_orchestrator._pending.clear()
    result = task_orchestrator.list_pending()
    assert "No pending" in result


def test_make_loss_spike_detector():
    detect = task_orchestrator.make_loss_spike_detector(threshold=0.5)
    assert detect("loss: 2.3 step 100") is True
    assert detect("loss: 0.1 step 100") is False
    assert detect("training loss=nan") is True
    assert detect("all good, loss: 0.01") is False


def test_chain_executes_steps():
    results = []

    async def step1():
        results.append(1)
        return "step1 done"

    async def step2():
        results.append(2)
        return "step2 done"

    steps = [
        task_orchestrator.TaskStep("Step 1", step1),
        task_orchestrator.TaskStep("Step 2", step2),
    ]

    progress = []

    async def progress_fn(msg):
        progress.append(msg)

    async def confirm_fn(aid, desc):
        pass

    output = run(task_orchestrator.execute_chain(steps, progress_fn, confirm_fn))
    assert results == [1, 2]
    assert "step1 done" in output
    assert "step2 done" in output


def test_chain_pauses_on_destructive():
    async def dangerous():
        return "danger"

    async def safe():
        return "safe"

    steps = [
        task_orchestrator.TaskStep("Safe", safe),
        task_orchestrator.TaskStep("Dangerous", dangerous, requires_confirmation=True),
        task_orchestrator.TaskStep("After danger", safe),
    ]

    confirmed = []

    async def confirm_fn(aid, desc):
        confirmed.append(aid)

    async def progress_fn(msg):
        pass

    output = run(task_orchestrator.execute_chain(steps, progress_fn, confirm_fn))
    assert len(confirmed) == 1  # paused at step 2
    assert "paused" in output.lower()
