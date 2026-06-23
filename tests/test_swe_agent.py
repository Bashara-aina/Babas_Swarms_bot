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

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Set test env
os.environ.setdefault("MINIMAX_API_KEY", "test-key-for-integration-tests")
os.environ.setdefault("OPENAI_API_KEY", "test-key-for-integration-tests")
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:4001")


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
        from core.swe_agent import load_config

        config = load_config()
        assert config is not None
        assert config.agent.max_steps == 30

    def test_swe_agent_config(self):
        """Test SWE agent config structure."""
        from core.swe_agent import SWEAgentConfig

        config = SWEAgentConfig()
        assert config.agent.model.name == "deepseek-v4-flash"
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

    def test_normalize_tool_stats(self):
        """Test _normalize_tool_stats fills all tools with defaults."""
        from core.swe_agent.trajectory import _normalize_tool_stats

        raw = {"bash": {"count": 3, "success": 2, "failure": 1}}
        result = _normalize_tool_stats(raw)
        assert result["bash"] == {"count": 3, "success": 2, "failure": 1}
        assert result["str_replace_editor"] == {"count": 0, "success": 0, "failure": 0}

    def test_normalize_tool_error_counts(self):
        """Test _normalize_tool_error_counts fills all tools with zero."""
        from core.swe_agent.trajectory import _normalize_tool_error_counts

        raw = {"grep": 2}
        result = _normalize_tool_error_counts(raw)
        assert result["grep"] == 2
        assert result["bash"] == 0

    def test_tool_stats_from_trajectory(self):
        """Test tool_stats_from_trajectory extracts and normalizes stats."""
        from core.swe_agent.trajectory import tool_stats_from_trajectory

        trajectory = {
            "instance_id": "test-002",
            "steps": [
                {
                    "step_num": 1,
                    "tool_calls": [
                        {"id": "call_1", "function": {"name": "bash", "arguments": "{}"}},
                    ],
                    "observation": '{"error": null}',
                },
                {
                    "step_num": 2,
                    "tool_calls": [
                        {"id": "call_2", "function": {"name": "grep", "arguments": "{}"}},
                    ],
                    "observation": '{"error": "pattern not found"}',
                },
            ],
            "model": "test-model",
        }
        stats, errors = tool_stats_from_trajectory(trajectory)
        assert stats["bash"]["count"] == 1
        assert stats["grep"]["count"] == 1
        assert stats["bash"]["failure"] == 0
        assert stats["grep"]["failure"] == 1
        assert errors["grep"] == 1

    def test_export_sharegpt(self):
        """Test export_sharegpt converts trajectory to ShareGPT format."""
        from core.swe_agent.trajectory import export_sharegpt

        trajectory = {
            "steps": [
                {
                    "step_num": 1,
                    "thought": "I should look at the file",
                    "action": "str_replace_editor view file.py",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {"name": "str_replace_editor", "arguments": "{}"},
                        },
                    ],
                    "observation": "file contents here",
                },
            ],
            "model": "test-model",
        }
        convs = export_sharegpt(trajectory)
        assert convs[0]["from"] == "system"
        assert convs[1]["from"] == "human"
        assert "look at the file" in convs[1]["value"]
        # check tool call message present
        tool_msgs = [c for c in convs if c.get("from") == "gpt" and c.get("tool_calls")]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["tool_calls"][0]["function"]["name"] == "str_replace_editor"
        # check tool response
        tool_responses = [c for c in convs if c.get("from") == "tool"]
        assert len(tool_responses) == 1
        assert "file contents here" in tool_responses[0]["value"]

    def test_save_sharegpt_trajectory(self, tmp_path):
        """Test save_sharegpt_trajectory writes valid JSONL."""
        from core.swe_agent.trajectory import save_sharegpt_trajectory

        trajectory = {
            "instance_id": "test-003",
            "model": "test-model",
            "steps": [
                {
                    "step_num": 1,
                    "thought": "View file",
                    "action": "view",
                    "tool_calls": [],
                    "observation": "content",
                },
            ],
        }
        out_file = tmp_path / "trajectories.jsonl"
        result = save_sharegpt_trajectory(trajectory, filename=str(out_file), completed=True)
        assert Path(result) == out_file
        import json
        with open(out_file) as f:
            entry = json.loads(f.readline())
        assert "conversations" in entry
        assert entry["model"] == "test-model"
        assert entry["completed"] is True
        assert entry["instance_id"] == "test-003"


class TestTrajectoryCompressor:
    """Test TrajectoryCompressor compression."""

    def test_compression_config_defaults(self):
        """Test CompressionConfig has correct defaults."""
        from core.swe_agent.trajectory import CompressionConfig

        config = CompressionConfig()
        assert config.target_max_tokens == 15250
        assert config.summary_target_tokens == 750
        assert config.protect_first_system is True
        assert config.protect_first_human is True
        assert config.protect_first_gpt is True
        assert config.protect_first_tool is True
        assert config.protect_last_n_turns == 4
        assert config.summarization_model == "deepseek-v4-flash"

    def test_compression_metrics_to_dict(self):
        """Test TrajectoryCompressionMetrics serialization."""
        from core.swe_agent.trajectory import TrajectoryCompressionMetrics

        metrics = TrajectoryCompressionMetrics(
            original_tokens=1000,
            compressed_tokens=500,
            tokens_saved=500,
            compression_ratio=0.5,
            original_turns=20,
            compressed_turns=10,
            turns_removed=10,
            was_compressed=True,
            still_over_limit=False,
        )
        d = metrics.to_dict()
        assert d["original_tokens"] == 1000
        assert d["compressed_tokens"] == 500
        assert d["was_compressed"] is True
        assert "compression_region" in d

    def test_compressor_init(self):
        """Test TrajectoryCompressor initializes correctly."""
        from core.swe_agent.trajectory import TrajectoryCompressor, CompressionConfig

        compressor = TrajectoryCompressor()
        assert compressor.config.target_max_tokens == 15250
        assert compressor._tokenizer is not None  # tiktoken loaded

        config = CompressionConfig(target_max_tokens=5000, protect_last_n_turns=2)
        compressor2 = TrajectoryCompressor(config=config)
        assert compressor2.config.target_max_tokens == 5000
        assert compressor2.config.protect_last_n_turns == 2

    def test_count_tokens(self):
        """Test token counting with tiktoken."""
        from core.swe_agent.trajectory import TrajectoryCompressor

        compressor = TrajectoryCompressor()
        # "hello world" is 2 tokens in cl100k_base
        count = compressor.count_tokens("hello world")
        assert count == 2

        # Empty string
        assert compressor.count_tokens("") == 0

    def test_compress_trajectory_short(self):
        """Test compression doesn't touch short trajectories."""
        from core.swe_agent.trajectory import TrajectoryCompressor

        compressor = TrajectoryCompressor()
        # Short trajectory under target
        trajectory = [
            {"from": "system", "value": "You are a helpful assistant."},
            {"from": "human", "value": "Hello"},
            {"from": "gpt", "value": "Hi there!"},
        ]

        compressed, metrics = compressor.compress_trajectory(trajectory)
        assert compressed == trajectory
        assert metrics.was_compressed is False
        assert metrics.skipped_under_target is True

    def test_compress_trajectory_identifies_protected(self):
        """Test _find_protected_indices identifies head and tail."""
        from core.swe_agent.trajectory import TrajectoryCompressor

        compressor = TrajectoryCompressor()
        # 10-turn trajectory
        trajectory = [
            {"from": "system", "value": "System prompt"},
            {"from": "human", "value": "Human input"},
            {"from": "gpt", "value": "First response"},
            {"from": "tool", "value": "Tool result"},
            {"from": "gpt", "value": "Second response"},
            {"from": "tool", "value": "Tool result 2"},
            {"from": "gpt", "value": "Third response"},
            {"from": "tool", "value": "Tool result 3"},
            {"from": "gpt", "value": "Fourth response"},
            {"from": "tool", "value": "Tool result 4"},
        ]

        protected, compress_start, compress_end = compressor._find_protected_indices(trajectory)

        # First system, human, gpt, tool should be protected
        assert 0 in protected  # system
        assert 1 in protected  # human
        assert 2 in protected  # first gpt
        assert 3 in protected  # first tool

        # Last 4 turns should be protected (tail)
        assert 6 in protected  # gpt (3rd from end)
        assert 7 in protected  # tool
        assert 8 in protected  # gpt
        assert 9 in protected  # tool (last)

    def test_compress_and_save(self, tmp_path):
        """Test compress_and_save produces valid JSONL."""
        from core.swe_agent.trajectory import TrajectoryCompressor

        compressor = TrajectoryCompressor()
        # compress_and_save expects a trajectory DICT (with steps key), not a raw list
        trajectory = {
            "instance_id": "test-compress-001",
            "model": "test-model",
            "steps": [
                {"from": "system", "value": "You are a helpful assistant."},
                {"from": "human", "value": "Hello"},
                {"from": "gpt", "value": "Hi there!"},
            ],
        }

        out_path = tmp_path / "output_compressed.jsonl"
        result_path, metrics = compressor.compress_and_save(
            trajectory, output_path=str(out_path), completed=True
        )

        assert Path(result_path) == out_path
        assert out_path.exists()

        import json
        with open(out_path) as f:
            entry = json.loads(f.readline())
        assert "conversations" in entry
        assert entry["completed"] is True
        assert entry["instance_id"] == "test-compress-001"


class TestSWEPromptBuilder:
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
