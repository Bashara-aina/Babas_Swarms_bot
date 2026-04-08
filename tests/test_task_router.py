"""Unit tests for core/task_router (keyword classify + singleton)."""

from __future__ import annotations

from core.task_router import TaskType, get_task_router, keyword_task_type


def test_keyword_simulation() -> None:
    assert keyword_task_type("What if we cut prices 20%?") == TaskType.SIMULATION


def test_keyword_code_traceback() -> None:
    assert keyword_task_type("I get a traceback when I run pytest") == TaskType.CODE


def test_keyword_none_for_casual() -> None:
    assert keyword_task_type("hey thanks for yesterday") is None


def test_get_task_router_singleton() -> None:
    a = get_task_router()
    b = get_task_router()
    assert a is b
