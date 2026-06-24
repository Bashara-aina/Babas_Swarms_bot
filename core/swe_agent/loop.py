"""
SWE-agent main loop — step-by-step agent loop with trajectory logging.

This module implements the core SWE-agent agent loop that:
1. Takes a problem statement (GitHub issue description)
2. Runs an LLM agent in a loop with tools
3. Tracks steps and trajectory for learning
4. Produces a patch at the end
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Iteration budget (hermes pattern — thread-safe, with refund support)
# ---------------------------------------------------------------------------

class IterationBudget:
    """Thread-safe iteration counter for an agent loop.

    Supports refund() for execute_code turns that shouldn't consume budget.
    The consume() method returns False when exhausted so the loop can stop.
    """

    def __init__(self, max_total: int) -> None:
        self.max_total = max_total
        self._used = 0
        self._lock = threading.Lock()

    def consume(self) -> bool:
        """Try to consume one iteration. Returns True if allowed, False if exhausted."""
        with self._lock:
            if self._used >= self.max_total:
                return False
            self._used += 1
            return True

    def refund(self) -> None:
        """Refund one iteration (e.g. for execute_code turns)."""
        with self._lock:
            if self._used > 0:
                self._used -= 1

    @property
    def used(self) -> int:
        return self._used

    @property
    def remaining(self) -> int:
        with self._lock:
            return max(0, self.max_total - self._used)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AgentLoopError(Exception):
    """Raised when the agent loop encounters an error."""


class MaxStepsExceeded(Exception):
    """Raised when max steps is reached."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Step:
    """A single step in the agent loop."""

    step_num: int
    thought: str = ""
    action: str = ""
    observation: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    timestamp: float = 0.0
    cost: float = 0.0
    tokens_sent: int = 0
    tokens_received: int = 0


@dataclass
class Trajectory:
    """Full trajectory of an agent run."""

    instance_id: str
    problem_statement: str
    repo_url: str = ""
    model: str = ""
    steps: list[Step] = field(default_factory=list)
    final_patch: str = ""
    submitted: bool = False
    success: bool = False
    total_cost: float = 0.0
    total_steps: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON export."""
        return {
            "instance_id": self.instance_id,
            "problem_statement": self.problem_statement,
            "repo_url": self.repo_url,
            "model": self.model,
            "steps": [
                {
                    "step_num": s.step_num,
                    "thought": s.thought,
                    "action": s.action,
                    "observation": s.observation,
                    "tool_calls": s.tool_calls,
                    "timestamp": s.timestamp,
                    "cost": s.cost,
                }
                for s in self.steps
            ],
            "final_patch": self.final_patch,
            "submitted": self.submitted,
            "success": self.success,
            "total_cost": self.total_cost,
            "total_steps": self.total_steps,
            "duration_seconds": self.end_time - self.start_time if self.end_time else 0,
            "error": self.error,
        }

    def save(self, output_dir: Path) -> Path:
        """Save trajectory to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.instance_id}.traj"
        filepath = output_dir / filename
        filepath.write_text(json.dumps(self.to_dict(), indent=2))
        return filepath


# ---------------------------------------------------------------------------
# SWEAgentLoop
# ---------------------------------------------------------------------------


class SWEAgentLoop:
    """Main agent loop for SWE-agent style problem solving."""

    def __init__(
        self,
        instance_id: str,
        problem_statement: str,
        model: str = "opencode-go/minimax-m3",
        max_steps: int = 30,
        working_dir: str | None = None,
        repo_url: str = "",
        trajectory_dir: str | None = None,
    ) -> None:
        """Initialize the SWE agent loop.

        Args:
            instance_id: Unique identifier for this run
            problem_statement: The GitHub issue or problem description
            model: Model to use for the agent
            max_steps: Maximum steps before giving up
            working_dir: Working directory for file operations
            repo_url: Repository URL for context
            trajectory_dir: Where to save trajectory files
        """
        self.instance_id = instance_id
        self.problem_statement = problem_statement
        self.model = model
        self.max_steps = max_steps
        self.working_dir = working_dir or str(Path.cwd())
        self.repo_url = repo_url
        self.trajectory_dir = Path(trajectory_dir) if trajectory_dir else Path.home() / ".swe_agent" / "trajectories"

        self.trajectory = Trajectory(
            instance_id=instance_id,
            problem_statement=problem_statement,
            repo_url=repo_url,
            model=model,
            start_time=time.time(),
        )

        self._steps: list[Step] = []
        self._step_count = 0
        self._total_cost = 0.0

        # Tools instance for this loop
        self._tools_enabled = True

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool and return the observation.

        Args:
            tool_name: Name of the tool (str_replace_editor, bash, grep, etc.)
            arguments: Tool arguments

        Returns:
            Observation string from tool execution
        """
        from .tools import (
            ToolResult,
            bash,
            glob,
            grep,
            str_replace_editor,
            submit,
        )

        # Add working_dir to arguments that need it
        if tool_name in ("str_replace_editor", "bash", "grep", "glob"):
            arguments.setdefault("working_dir", self.working_dir)

        try:
            if tool_name == "str_replace_editor":
                result: ToolResult = str_replace_editor(**arguments)
                return result.to_obs()

            elif tool_name == "bash":
                result = bash(**arguments)
                return result.to_obs()

            elif tool_name == "grep":
                result = grep(**arguments)
                return result.to_obs()

            elif tool_name == "glob":
                result = glob(**arguments)
                return result.to_obs()

            elif tool_name == "submit":
                result = submit(working_dir=self.working_dir)
                if result.success:
                    self.trajectory.final_patch = result.patch
                    self.trajectory.submitted = True
                    self.trajectory.success = True
                return result.message

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            logger.exception("Tool execution failed: %s", tool_name)
            return f"Tool execution error: {e}"

    # ------------------------------------------------------------------
    # Step tracking
    # ------------------------------------------------------------------

    def add_step(
        self,
        thought: str = "",
        action: str = "",
        observation: str = "",
        tool_calls: list[dict[str, Any]] | None = None,
        cost: float = 0.0,
    ) -> None:
        """Record a step in the trajectory."""
        self._step_count += 1
        step = Step(
            step_num=self._step_count,
            thought=thought,
            action=action,
            observation=observation,
            tool_calls=tool_calls or [],
            timestamp=time.time(),
            cost=cost,
        )
        self._steps.append(step)
        self._total_cost += cost

        self.trajectory.steps = self._steps
        self.trajectory.total_cost = self._total_cost
        self.trajectory.total_steps = self._step_count

    def check_step_limit(self) -> None:
        """Check if step limit exceeded."""
        if self._step_count >= self.max_steps:
            raise MaxStepsExceeded(
                f"Maximum steps ({self.max_steps}) reached. "
                "Consider using more specific commands or submitting partial work."
            )

    # ------------------------------------------------------------------
    # Trajectory management
    # ------------------------------------------------------------------

    def save_trajectory(self) -> Path:
        """Save the trajectory to disk."""
        self.trajectory.end_time = time.time()
        return self.trajectory.save(self.trajectory_dir)

    def finalize(self, success: bool = True, error: str = "") -> None:
        """Finalize the trajectory."""
        self.trajectory.end_time = time.time()
        self.trajectory.success = success
        self.trajectory.error = error
        self.save_trajectory()

    # ------------------------------------------------------------------
    # System prompt construction
    # ------------------------------------------------------------------

    @staticmethod
    def build_system_prompt(
        repo_path: str,
        repo_url: str = "",
        additional_context: str = "",
    ) -> str:
        """Build the system prompt for SWE-agent.

        Args:
            repo_path: Path to the repository on disk
            repo_url: GitHub URL for the repo
            additional_context: Any extra context to add

        Returns:
            System prompt string
        """
        repo_name = Path(repo_path).name

        prompt = f"""You are a helpful assistant that can interact with a computer to solve tasks.

You are working in the repository {repo_name} located at {repo_path}.
{"The repository URL is: " + repo_url if repo_url else ""}

## Your Tools

You have access to the following tools:
1. str_replace_editor: View, create, or edit files
   - view <path>: Show file contents
   - create <path> --file_text <content>: Create new file
   - str_replace <path> --old_str <old> --new_str <new>: Replace text
   - insert <path> --insert_line <N> --file_text <content>: Insert after line N
   - undo <path>: Undo last edit

2. bash: Execute bash commands
   - Usage: bash --command "python script.py"

3. grep: Search for patterns in files
   - Usage: grep --pattern "function_name" --file_pattern "*.py"

4. glob: Find files by pattern
   - Usage: glob --pattern "**/*.py"

5. submit: Submit your changes as a patch
   - Usage: submit

## Workflow

1. First, explore the repository to understand the structure
2. Find and read code relevant to the problem
3. Create a reproduction script to confirm the issue
4. Make the minimal fix to resolve the issue
5. Run your reproduction script to verify the fix
6. Submit your changes when done

## Important

- Make minimal changes - only fix what's necessary
- Don't modify test files unless explicitly asked
- Clean up any temporary files (reproduction scripts) before submitting
- Always verify your fix works before submitting
"""

        if additional_context:
            prompt += f"\n\n## Additional Context\n\n{additional_context}"

        return prompt

    @staticmethod
    def build_instance_prompt(problem_statement: str, format: str = "github") -> str:
        """Build the instance prompt from a problem statement.

        Args:
            problem_statement: The problem description
            format: Format of the statement ('github', 'plain', 'swe_bench')

        Returns:
            Formatted instance prompt
        """
        if format == "github":
            # Parse GitHub issue format
            lines = problem_statement.split("\n")
            title = ""
            body = []

            for i, line in enumerate(lines):
                if i == 0 and not title:
                    title = line.strip()
                else:
                    body.append(line)

            body_text = "\n".join(body).strip()

            prompt = f"""<issue>
<description>
{body_text}
</description>
</issue>

I've already taken care of all changes to any of the test files described in the issue. This means you DON'T have to modify the testing logic or any of the tests in any way!

Your task is to make the minimal changes to non-test files in the repository to ensure the issue is resolved.

Follow these steps to resolve the issue:
1. As a first step, explore the repository to understand the structure
2. Find and read code relevant to the issue
3. Create a script to reproduce the issue and execute it to confirm the error
4. Edit the source code to resolve the issue
5. Rerun your reproduction script and confirm that the issue is fixed
6. Think about edge cases and make sure your fix handles them as well
7. Submit your changes

Your thinking should be thorough and so it's fine if it's very long."""
        else:
            prompt = f"""Consider the following problem:

{problem_statement}

Solve this problem step by step. Follow the workflow:
1. Explore and understand the codebase
2. Create a reproduction to confirm the issue
3. Fix the issue
4. Verify the fix works
5. Submit
"""
        return prompt
