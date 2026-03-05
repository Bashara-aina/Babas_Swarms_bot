# /home/newadmin/swarm-bot/tests/test_computer_control.py
"""Tests for computer_control.py — run with: pytest tests/test_computer_control.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch

import computer_control


def test_is_destructive_detects_rm():
    assert computer_control.is_destructive("rm -rf /tmp/foo") is True


def test_is_destructive_detects_force_push():
    assert computer_control.is_destructive("git push --force origin main") is True


def test_is_destructive_safe_command():
    assert computer_control.is_destructive("ls -la") is False
    assert computer_control.is_destructive("python train.py") is False


def test_rate_limit_enforced(monkeypatch):
    """Rate limiter should pause if called too fast."""
    import time
    calls = []
    original_sleep = time.sleep

    def mock_sleep(secs):
        calls.append(secs)

    monkeypatch.setattr(time, "sleep", mock_sleep)
    computer_control._last_screenshot_time = time.monotonic()  # simulate recent screenshot
    computer_control._rate_limit_screenshot()
    assert len(calls) == 1  # sleep was called


def test_action_limit_raises():
    ctrl = computer_control.ComputerController()
    ctrl._action_count = computer_control.MAX_ACTIONS_PER_CHAIN
    with pytest.raises(RuntimeError, match="Action limit"):
        ctrl._check_action_limit()


def test_action_limit_resets():
    ctrl = computer_control.ComputerController()
    ctrl._action_count = 5
    ctrl.reset_action_count()
    assert ctrl._action_count == 0
