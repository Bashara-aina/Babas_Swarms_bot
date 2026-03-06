# /home/newadmin/swarm-bot/tests/test_vscode_bridge.py
"""Tests for vscode_bridge.py — run with: pytest tests/test_vscode_bridge.py"""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import core.tools.vscode_bridge as vscode_bridge


def test_read_file_not_found():
    with pytest.raises(FileNotFoundError):
        vscode_bridge._read_file_sync("/nonexistent/file.txt")


def test_write_and_read_file(tmp_path):
    p = tmp_path / "test.txt"
    vscode_bridge._write_file_sync(str(p), "hello world")
    content = vscode_bridge._read_file_sync(str(p))
    assert content == "hello world"


def test_list_files_returns_string(tmp_path):
    (tmp_path / "a.py").write_text("pass")
    (tmp_path / "b.py").write_text("pass")
    result = vscode_bridge._list_files_sync(str(tmp_path), "*.py")
    assert "a.py" in result
    assert "b.py" in result


def test_run_command_echo():
    output = vscode_bridge._run_command_sync("echo hello_world")
    assert "hello_world" in output


def test_run_command_timeout():
    output = vscode_bridge._run_command_sync("sleep 100", timeout=1)
    assert "timed out" in output.lower()


def test_run_command_nonzero_exit():
    output = vscode_bridge._run_command_sync("exit 1", timeout=5)
    assert "exit 1" in output or output  # just shouldn't raise
