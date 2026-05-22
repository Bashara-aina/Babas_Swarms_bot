"""tests/test_swe_agent.py — Integration tests for native SWE-agent.

Tests the agent-computer interface (ACI) pattern with:
- str_replace_editor: view, create, str_replace, insert, undo
- bash: execute commands
- grep: search patterns
- glob: find files
- submit: submit the solution
- Trajectory logging

Run with: pytest tests/test_swe_agent.py -x --asyncio-mode=auto -q
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Set test env
os.environ.setdefault("MINIMAX_API_KEY", "test-key-for-integration-tests")
os.environ.setdefault("OPENAI_API_KEY", "test-key-for-integration-tests")
os.environ.setdefault("OPENAI_BASE_URL", "https://api.minimax.io/v1")


class TestSWETools:
    """Test SWE-agent tools."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repo for testing."""
        tmp = tempfile.mkdtemp(prefix="swe_test_")
        repo = Path(tmp) / "repo"
        repo.mkdir()

        # Initialize git repo
        os.system(f"cd {repo} && git init -q")
        os.system(f"cd {repo} && git config user.email 'test@test.com'")
        os.system(f"cd {repo} && git config user.name 'Test'")

        # Create a simple Python file
        (repo / "hello.py").write_text(
            '"""Hello module."""\n\n\ndef greet(name):\n    """Greet someone."""\n    return f"Hello, {name}!"\n'
        )

        # Create a test file
        (repo / "test_hello.py").write_text(
            '"""Test hello module."""\nfrom hello import greet\n\n\ndef test_greet():\n    assert greet("World") == "Hello, World!"\n'
        )

        # Initial commit
        os.system(f"cd {repo} && git add . && git commit -q -m 'initial'")

        yield str(repo)

        # Cleanup
        shutil.rmtree(tmp, ignore_errors=True)

    def test_tools_import(self):
        """Test that all tools can be imported."""
        from core.swe_agent import (
            bash,
            glob,
            grep,
            submit,
            str_replace_editor,
        )

        assert callable(str_replace_editor)
        assert callable(bash)
        assert callable(grep)
        assert callable(glob)
        assert callable(submit)

    def test_str_replace_editor_view(self, temp_repo):
        """Test viewing a file."""
        from core.swe_agent import str_replace_editor

        result = str_replace_editor(command="view", path="hello.py", working_dir=temp_repo)
        assert result.success
        assert "def greet" in result.output
        assert 'return f"Hello, {name}!"' in result.output

    def test_str_replace_editor_create(self, temp_repo):
        """Test creating a file."""
        from core.swe_agent import str_replace_editor

        result = str_replace_editor(
            command="create",
            path="new_file.py",
            file_text="# New file\n",
            working_dir=temp_repo,
        )
        assert result.success
        assert (Path(temp_repo) / "new_file.py").exists()

    def test_str_replace_editor_str_replace(self, temp_repo):
        """Test replacing text in a file."""
        from core.swe_agent import str_replace_editor

        result = str_replace_editor(
            command="str_replace",
            path="hello.py",
            old_str='return f"Hello, {name}!"',
            new_str='return f"Hi, {name}!"',
            working_dir=temp_repo,
        )
        assert result.success

        # Verify the change
        content = (Path(temp_repo) / "hello.py").read_text()
        assert 'return f"Hi, {name}!"' in content

    def test_str_replace_editor_undo(self, temp_repo):
        """Test undoing an edit."""
        from core.swe_agent import str_replace_editor

        # Make an edit
        str_replace_editor(
            command="str_replace",
            path="hello.py",
            old_str='return f"Hello, {name}!"',
            new_str='return f"Hi, {name}!"',
            working_dir=temp_repo,
        )

        # Undo it
        result = str_replace_editor(command="undo", path="hello.py", working_dir=temp_repo)
        assert result.success

        # Verify restored
        content = (Path(temp_repo) / "hello.py").read_text()
        assert 'return f"Hello, {name}!"' in content

    def test_bash(self, temp_repo):
        """Test bash tool."""
        from core.swe_agent import bash

        result = bash(command="echo hello", working_dir=temp_repo)
        assert result.success
        assert "hello" in result.output

    def test_bash_with_timeout(self, temp_repo):
        """Test bash with timeout."""
        from core.swe_agent import bash

        result = bash(command="echo done", working_dir=temp_repo, timeout=5)
        assert result.success
        assert "done" in result.output

    def test_bash_nonexistent_command(self, temp_repo):
        """Test bash with nonexistent command."""
        from core.swe_agent import bash

        result = bash(command="nonexistent_command_xyz", working_dir=temp_repo)
        assert not result.success
        assert "no such file" in result.error.lower() or "not found" in result.error.lower()

    def test_grep(self, temp_repo):
        """Test grep tool."""
        from core.swe_agent import grep

        result = grep(pattern="def greet", working_dir=temp_repo)
        assert result.success
        assert "hello.py" in result.output

    def test_glob(self, temp_repo):
        """Test glob tool."""
        from core.swe_agent import glob

        result = glob(pattern="*.py", working_dir=temp_repo)
        assert result.success
        assert "hello.py" in result.output or "test_hello.py" in result.output

    def test_submit(self, temp_repo):
        """Test submit tool."""
        from core.swe_agent import str_replace_editor, submit

        # Make a change
        str_replace_editor(
            command="str_replace",
            path="hello.py",
            old_str='return f"Hello, {name}!"',
            new_str='return f"Hi, {name}!"',
            working_dir=temp_repo,
        )

        result = submit(working_dir=temp_repo)
        assert result.success
        assert result.output  # Should have patch content


class TestSWEConfig:
    """Test SWE-agent configuration."""

    def test_load_default_config(self):
        """Test loading default config."""
        from core.swe_agent import DEFAULT_CONFIG, load_config

        config = load_config()
        assert config is not None
        assert config.agent.max_steps == 30

    def test_swe_agent_config(self):
        """Test SWE agent config structure."""
        from core.swe_agent import SWEAgentConfig

        config = SWEAgentConfig()
        assert config.agent.model.name == "minimax-coding-plan/MiniMax-M2.7"
        assert config.agent.max_steps == 30
        assert config.env.repo_path == ""


class TestSWELoop:
    """Test SWE-agent loop."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repo for testing."""
        tmp = tempfile.mkdtemp(prefix="swe_test_")
        repo = Path(tmp) / "repo"
        repo.mkdir()

        # Initialize git repo
        os.system(f"cd {repo} && git init -q")
        os.system(f"cd {repo} && git config user.email 'test@test.com'")
        os.system(f"cd {repo} && git config user.name 'Test'")

        # Create a simple Python file
        (repo / "hello.py").write_text(
            '"""Hello module."""\n\n\ndef greet(name):\n    """Greet someone."""\n    return f"Hello, {name}!"\n'
        )

        # Initial commit
        os.system(f"cd {repo} && git add . && git commit -q -m 'initial'")

        yield str(repo)

        # Cleanup
        shutil.rmtree(tmp, ignore_errors=True)

    def test_swe_agent_loop_init(self, temp_repo):
        """Test SWEAgentLoop initialization."""
        from core.swe_agent import SWEAgentLoop

        loop = SWEAgentLoop(
            instance_id="test-001",
            problem_statement="Fix the greeting function",
            working_dir=temp_repo,
        )

        assert loop.instance_id == "test-001"
        assert loop.problem_statement == "Fix the greeting function"
        assert loop.max_steps == 30
        assert loop.working_dir == temp_repo

    def test_swe_agent_loop_add_step(self, temp_repo):
        """Test adding a step to the trajectory."""
        from core.swe_agent import SWEAgentLoop

        loop = SWEAgentLoop(
            instance_id="test-001",
            problem_statement="Fix the greeting function",
            working_dir=temp_repo,
        )

        loop.add_step(
            thought="I need to view the file first",
            action="str_replace_editor view hello.py",
            observation="def greet(name): ...",
            cost=0.01,
        )

        assert len(loop.trajectory.steps) == 1
        assert loop.trajectory.steps[0].thought == "I need to view the file first"
        assert loop.trajectory.total_cost == 0.01

    def test_swe_agent_loop_max_steps(self, temp_repo):
        """Test max steps exceeded."""
        from core.swe_agent import SWEAgentLoop
        from core.swe_agent.loop import MaxStepsExceeded

        loop = SWEAgentLoop(
            instance_id="test-001",
            problem_statement="Fix the greeting function",
            working_dir=temp_repo,
            max_steps=2,
        )

        loop.add_step(thought="Step 1")
        loop.add_step(thought="Step 2")

        with pytest.raises(MaxStepsExceeded):
            loop.check_step_limit()

    def test_trajectory_save(self, temp_repo):
        """Test trajectory saving."""
        from core.swe_agent import SWEAgentLoop

        loop = SWEAgentLoop(
            instance_id="test-save-001",
            problem_statement="Fix the greeting function",
            working_dir=temp_repo,
        )

        loop.add_step(thought="View the file", action="view hello.py")
        loop.trajectory.final_patch = "dummy patch content"

        traj_path = loop.save_trajectory()

        assert traj_path.exists()

        # Load and verify
        data = json.loads(traj_path.read_text())
        assert data["instance_id"] == "test-save-001"
        assert data["total_steps"] == 1
        assert data["final_patch"] == "dummy patch content"


class TestSWEEnvironment:
    """Test SWE-agent environment."""

    def test_environment_init(self):
        """Test Environment initialization."""
        from core.swe_agent.environment import EnvConfig, Environment

        config = EnvConfig(repo_path="/tmp")
        env = Environment(config=config)
        assert str(env.config.repo_path) == "/tmp"

    @pytest.mark.skip(reason="Requires network access and proper git setup")
    def test_environment_git_clone(self):
        """Test git clone in environment."""
        from core.swe_agent.environment import EnvConfig, Environment

        with tempfile.TemporaryDirectory() as tmp:
            config = EnvConfig(repo_path=tmp)
            env = Environment(config=config)

            # Clone a small public repo
            env.setup()  # This will clone based on config if needed


class TestTrajectoryAnalysis:
    """Test trajectory analysis utilities."""

    def test_load_and_compute_stats(self):
        """Test loading trajectory and computing stats."""
        from core.swe_agent.trajectory import TrajectoryStats, compute_stats

        trajectory = {
            "instance_id": "test-001",
            "problem_statement": "Fix bug",
            "steps": [
                {
                    "step_num": 1,
                    "thought": "View file",
                    "action": "view hello.py",
                    "observation": "content",
                    "tool_calls": [{"name": "str_replace_editor"}],
                    "cost": 0.01,
                },
                {
                    "step_num": 2,
                    "thought": "Edit file",
                    "action": "str_replace hello.py",
                    "observation": "edited",
                    "tool_calls": [{"name": "str_replace_editor"}],
                    "cost": 0.02,
                },
            ],
            "total_steps": 2,
            "total_cost": 0.03,
            "duration_seconds": 10.0,
            "success": True,
            "submitted": True,
            "error": "",
        }

        stats = compute_stats(trajectory)

        assert isinstance(stats, TrajectoryStats)
        assert stats.instance_id == "test-001"
        assert stats.total_steps == 2
        assert stats.total_cost == 0.03
        assert stats.duration_seconds == 10.0
        assert stats.success is True
        assert stats.submitted is True
        assert stats.tools_used.get("str_replace_editor", 0) == 2


class TestPromptBuilder:
    """Test SWE-agent prompt builder."""

    def test_system_prompt(self):
        """Test system prompt generation."""
        from core.swe_agent import PromptBuilder

        pb = PromptBuilder(working_dir="/tmp", repo_name="test-repo")

        system_prompt = pb.system_prompt()

        assert "test-repo" in system_prompt
        assert "str_replace_editor" in system_prompt
        assert "bash" in system_prompt
        assert "submit" in system_prompt

    def test_instance_prompt(self):
        """Test instance prompt generation."""
        from core.swe_agent import PromptBuilder

        pb = PromptBuilder(working_dir="/tmp", repo_name="test-repo")

        instance_prompt = pb.instance_prompt(
            issue_text="Fix the bug where X crashes on empty input"
        )

        assert "Fix the bug where X crashes on empty input" in instance_prompt


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])