"""
SWE-agent trajectory visualization, analysis, and ShareGPT export utilities.

This module provides tools for:
- Loading and analyzing trajectory files
- Generating HTML visualizations
- Computing statistics and metrics
- Converting trajectories to ShareGPT format for RL training
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool stats normalization (hermes ADR-095 G6 pattern)
# ---------------------------------------------------------------------------

# Default stats for tools that weren't used — ensures consistent schema
# in HuggingFace datasets (avoids JSON loading errors from missing fields)
DEFAULT_TOOL_STATS = {"count": 0, "success": 0, "failure": 0}


def _normalize_tool_stats(tool_stats: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    """Normalize tool_stats to include all possible tools with consistent schema.

    Ensures HuggingFace datasets can load the JSONL without schema mismatch errors.
    Tools that weren't used get zero counts.

    Args:
        tool_stats: Raw tool statistics from extraction

    Returns:
        Normalized tool statistics with all tools present
    """
    # Import here to avoid circular imports; tools is the canonical registry
    try:
        from core.swe_agent.tools import TOOL_DEFINITIONS

        def _get_all_tools() -> set[str]:
            tools: set[str] = set()
            for td in TOOL_DEFINITIONS:
                func = td.get("function", {})
                name = func.get("name")
                if name:
                    tools.add(name)
            return tools

        ALL_TOOLS: set[str] = _get_all_tools()
    except Exception:
        ALL_TOOLS: set[str] = {
            "str_replace_editor", "bash", "grep", "glob", "submit",
        }

    normalized: dict[str, dict[str, int]] = {}

    # Add all known tools with defaults
    for tool in ALL_TOOLS:
        normalized[tool] = tool_stats.get(tool, DEFAULT_TOOL_STATS).copy()
    # Include any unexpected tools not in the registry
    for tool, stats in tool_stats.items():
        if tool not in normalized:
            normalized[tool] = stats.copy()

    return normalized


def _normalize_tool_error_counts(tool_error_counts: dict[str, int]) -> dict[str, int]:
    """Normalize tool_error_counts to include all possible tools.

    Args:
        tool_error_counts: Raw error counts mapping

    Returns:
        Normalized error counts with all tools present
    """
    try:
        from core.swe_agent.tools import TOOL_DEFINITIONS

        def _get_all_tools() -> set[str]:
            tools: set[str] = set()
            for td in TOOL_DEFINITIONS:
                func = td.get("function", {})
                name = func.get("name")
                if name:
                    tools.add(name)
            return tools

        ALL_TOOLS: set[str] = _get_all_tools()
    except Exception:
        ALL_TOOLS: set[str] = {
            "str_replace_editor", "bash", "grep", "glob", "submit",
        }

    normalized: dict[str, int] = {}
    for tool in ALL_TOOLS:
        normalized[tool] = tool_error_counts.get(tool, 0)
    for tool, count in tool_error_counts.items():
        if tool not in normalized:
            normalized[tool] = count

    return normalized


# ---------------------------------------------------------------------------
# ShareGPT trajectory export
# ---------------------------------------------------------------------------

SHAREGPT_SYSTEM_PROMPT = """You are a coding assistant that solves GitHub issues.
You have access to tools: Read, Edit, Search, Bash, Grep, Glob, Submit.
Think step by step. Use tools when needed. When done, use the Submit tool."""


def extract_tool_stats_from_steps(steps: list[dict[str, Any]]) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """Extract tool usage statistics from a list of steps.

    Args:
        steps: List of step dicts (from Trajectory.to_dict()["steps"])

    Returns:
        Tuple of (tool_stats, tool_error_counts)
    """
    tool_stats: dict[str, dict[str, int]] = {}
    tool_error_counts: dict[str, int] = {}
    tool_calls_map: dict[str, str] = {}  # tool_call_id -> tool name

    for step in steps:
        for tc in step.get("tool_calls", []):
            if not tc or not isinstance(tc, dict):
                continue
            func = tc.get("function", {})
            tool_name = func.get("name", tc.get("name", "unknown"))
            tool_call_id = tc.get("id", "")

            if tool_name not in tool_stats:
                tool_stats[tool_name] = {"count": 0, "success": 0, "failure": 0}

            tool_stats[tool_name]["count"] += 1
            tool_calls_map[tool_call_id] = tool_name

        # Check observation for errors (tool response)
        obs = step.get("observation", "")
        if obs:
            try:
                obs_json = json.loads(obs) if isinstance(obs, str) else obs
                if isinstance(obs_json, dict) and obs_json.get("error") is not None:
                    # Find which tool this belongs to via tool_calls in step
                    for tc in step.get("tool_calls", []):
                        tid = tc.get("id", "")
                        if tid in tool_calls_map:
                            tn = tool_calls_map[tid]
                            tool_stats[tn]["failure"] += 1
                            tool_error_counts[tn] = tool_error_counts.get(tn, 0) + 1
                            break
                else:
                    for tc in step.get("tool_calls", []):
                        tid = tc.get("id", "")
                        if tid in tool_calls_map:
                            tool_calls_map.pop(tid, None)
            except (json.JSONDecodeError, TypeError):
                pass

    # Remaining unmapped tool calls are successes
    for tid, tool_name in tool_calls_map.items():
        tool_stats[tool_name]["success"] += 1

    return tool_stats, tool_error_counts


@dataclass
class TrajectoryStats:
    """Statistics from a trajectory."""

    instance_id: str
    total_steps: int
    total_cost: float
    duration_seconds: float
    tools_used: dict[str, int]
    success: bool
    submitted: bool
    error: str


def load_trajectory(path: str | Path) -> dict[str, Any]:
    """Load a trajectory from JSON file.

    Args:
        path: Path to the .traj file

    Returns:
        Trajectory dict
    """
    with open(path) as f:
        return json.load(f)


def load_trajectory_dir(dir_path: str | Path) -> list[dict[str, Any]]:
    """Load all trajectories from a directory.

    Args:
        dir_path: Directory containing .traj files

    Returns:
        List of trajectory dicts
    """
    dir_path = Path(dir_path)
    trajectories = []

    for traj_file in sorted(dir_path.glob("*.traj")):
        try:
            trajectories.append(load_trajectory(traj_file))
        except Exception as e:
            logger.warning(f"Failed to load {traj_file}: {e}")

    return trajectories


def compute_stats(trajectory: dict[str, Any]) -> TrajectoryStats:
    """Compute statistics from a trajectory.

    Args:
        trajectory: Trajectory dict from load_trajectory

    Returns:
        TrajectoryStats
    """
    tools_used: dict[str, int] = {}

    for step in trajectory.get("steps", []):
        for tc in step.get("tool_calls", []):
            tool_name = tc.get("name", "unknown")
            tools_used[tool_name] = tools_used.get(tool_name, 0) + 1

    return TrajectoryStats(
        instance_id=trajectory.get("instance_id", ""),
        total_steps=trajectory.get("total_steps", 0),
        total_cost=trajectory.get("total_cost", 0.0),
        duration_seconds=trajectory.get("duration_seconds", 0.0),
        tools_used=tools_used,
        success=trajectory.get("success", False),
        submitted=trajectory.get("submitted", False),
        error=trajectory.get("error", ""),
    )


def generate_html_report(trajectory: dict[str, Any], output_path: Path | None = None) -> str:
    """Generate an HTML report from a trajectory.

    Args:
        trajectory: Trajectory dict
        output_path: Optional path to save the HTML

    Returns:
        HTML string
    """
    stats = compute_stats(trajectory)
    steps = trajectory.get("steps", [])

    # Build tool usage table
    tool_rows = ""
    for tool, count in sorted(stats.tools_used.items(), key=lambda x: -x[1]):
        tool_rows += f"<tr><td>{tool}</td><td>{count}</td></tr>"

    # Build steps table
    step_rows = ""
    for step in steps:
        thought = step.get("thought", "")[:100]
        action = step.get("action", "")[:100]
        obs = step.get("observation", "")[:100]
        cost = step.get("cost", 0)

        step_rows += f"""
        <tr>
            <td>{step.get('step_num', 0)}</td>
            <td>{thought}...</td>
            <td>{action}...</td>
            <td>{obs}...</td>
            <td>${cost:.4f}</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SWE-agent Trajectory: {stats.instance_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        h1, h2 {{ color: #333; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #007AFF; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #fafafa; font-weight: 600; }}
        .success {{ color: #34C759; }}
        .failure {{ color: #FF3B30; }}
        .patch {{ background: #f0f0f0; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>SWE-agent Trajectory Report</h1>
    <p><strong>Instance:</strong> {stats.instance_id}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{stats.total_steps}</div>
            <div class="stat-label">Total Steps</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.total_cost:.4f}</div>
            <div class="stat-label">Total Cost</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.duration_seconds:.1f}s</div>
            <div class="stat-label">Duration</div>
        </div>
        <div class="stat-card">
            <div class="stat-value {'success' if stats.success else 'failure'}">
                {'✅' if stats.success else '❌'}
            </div>
            <div class="stat-label">Success</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">
                {'✅' if stats.submitted else '❌'}
            </div>
            <div class="stat-label">Submitted</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(stats.tools_used)}</div>
            <div class="stat-label">Tools Used</div>
        </div>
    </div>

    <h2>Tool Usage</h2>
    <table>
        <tr><th>Tool</th><th>Count</th></tr>
        {tool_rows}
    </table>

    <h2>Steps</h2>
    <table>
        <tr><th>#</th><th>Thought</th><th>Action</th><th>Observation</th><th>Cost</th></tr>
        {step_rows}
    </table>

    <h2>Final Patch</h2>
    <div class="patch">{trajectory.get('final_patch', 'No patch generated')[:500]}...</div>

    {f'<p><strong>Error:</strong> {stats.error}</p>' if stats.error else ''}
</body>
</html>
    """

    if output_path:
        output_path.write_text(html)
        logger.info(f"HTML report saved to: {output_path}")

    return html


def generate_summary_table(trajectories: list[dict[str, Any]]) -> str:
    """Generate a markdown summary table from multiple trajectories.

    Args:
        trajectories: List of trajectory dicts

    Returns:
        Markdown table string
    """
    lines = [
        "| Instance | Steps | Cost | Duration | Success | Submitted |",
        "|----------|-------|------|----------|---------|-----------|",
    ]

    for traj in trajectories:
        stats = compute_stats(traj)
        status = "✅" if stats.success else "❌"
        submitted = "✅" if stats.submitted else "❌"

        lines.append(
            f"| {stats.instance_id} | {stats.total_steps} | "
            f"${stats.total_cost:.4f} | {stats.duration_seconds:.1f}s | "
            f"{status} | {submitted} |"
        )

    return "\n".join(lines)


def tool_stats_from_trajectory(
    trajectory: dict[str, Any],
) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """Compute normalized tool stats and error counts from a trajectory dict.

    Args:
        trajectory: Trajectory dict (from load_trajectory or Trajectory.to_dict())

    Returns:
        Tuple of (normalized_tool_stats, normalized_error_counts)
    """
    steps = trajectory.get("steps", [])
    raw_stats: dict[str, dict[str, int]] = {}
    raw_error_counts: dict[str, int] = {}
    tool_calls_map: dict[str, str] = {}

    for step in steps:
        for tc in step.get("tool_calls", []):
            if not tc or not isinstance(tc, dict):
                continue
            func = tc.get("function", {})
            tool_name = func.get("name", tc.get("name", "unknown"))
            tool_call_id = tc.get("id", "")

            if tool_name not in raw_stats:
                raw_stats[tool_name] = {"count": 0, "success": 0, "failure": 0}
            raw_stats[tool_name]["count"] += 1
            tool_calls_map[tool_call_id] = tool_name

        obs = step.get("observation", "")
        if obs:
            try:
                obs_json = json.loads(obs) if isinstance(obs, str) else obs
                if isinstance(obs_json, dict) and obs_json.get("error") is not None:
                    for tc in step.get("tool_calls", []):
                        tid = tc.get("id", "")
                        if tid in tool_calls_map:
                            tn = tool_calls_map.pop(tid)
                            raw_stats[tn]["failure"] += 1
                            raw_error_counts[tn] = raw_error_counts.get(tn, 0) + 1
                            break
            except (json.JSONDecodeError, TypeError):
                pass

    for tid, tool_name in tool_calls_map.items():
        raw_stats[tool_name]["success"] += 1

    return _normalize_tool_stats(raw_stats), _normalize_tool_error_counts(raw_error_counts)


def export_sharegpt(trajectory: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a trajectory dict to ShareGPT conversation format.

    ShareGPT format::
        [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}, ...]

    The resulting list is suitable for RL training datasets (e.g. HuggingFace).

    Args:
        trajectory: Trajectory dict (from load_trajectory or Trajectory.to_dict())

    Returns:
        ShareGPT-format conversation list
    """
    steps = trajectory.get("steps", [])
    conversations: list[dict[str, Any]] = []

    # System prompt (first turn)
    conversations.append({
        "from": "system",
        "value": SHAREGPT_SYSTEM_PROMPT,
    })

    for step in steps:
        # Human turn: thought (the "thought" field from each step)
        thought = step.get("thought", "")
        if thought:
            conversations.append({"from": "human", "value": thought})

        # GPT turn: action (what the model decided to do)
        action = step.get("action", "")
        if action:
            conversations.append({"from": "gpt", "value": action})

        # Tool calls as assistant message
        tool_calls = step.get("tool_calls", [])
        if tool_calls:
            for tc in tool_calls:
                if not tc or not isinstance(tc, dict):
                    continue
                conversations.append({
                    "from": "gpt",
                    "value": "",
                    "tool_calls": [
                        {
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": tc.get("function", tc),
                        }
                    ],
                })

        # Tool response as tool message
        obs = step.get("observation", "")
        if obs:
            conversations.append({"from": "tool", "value": str(obs)[:4000]})

    return conversations


def save_sharegpt_trajectory(
    trajectory: dict[str, Any],
    filename: str | None = None,
    completed: bool = True,
) -> str:
    """Save a trajectory in ShareGPT JSONL format.

    Mirrors hermes trajectory_compressor.save_trajectory() pattern.

    Args:
        trajectory: Trajectory dict
        filename: Output filename override. Defaults to trajectory_samples.jsonl
                  or failed_trajectories.jsonl based on ``completed``.
        completed: Whether the conversation completed successfully.

    Returns:
        The filename the trajectory was saved to.
    """
    if filename is None:
        filename = "trajectory_samples.jsonl" if completed else "failed_trajectories.jsonl"

    conversations = export_sharegpt(trajectory)
    entry = {
        "conversations": conversations,
        "timestamp": datetime.now().isoformat(),
        "model": trajectory.get("model", "unknown"),
        "completed": completed,
        "instance_id": trajectory.get("instance_id", ""),
    }

    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return filename


# ---------------------------------------------------------------------------
# Trajectory compression (hermes TrajectoryCompressor pattern)
# ---------------------------------------------------------------------------

import asyncio  # noqa: E402
from dataclasses import dataclass  # noqa: E402

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except Exception:
    _TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CompressionConfig:
    """Configuration for trajectory compression."""
    # Tokenizer
    tokenizer_name: str = "moonshotai/Kimi-K2-Thinking"
    trust_remote_code: bool = True

    # Compression targets
    target_max_tokens: int = 15250
    summary_target_tokens: int = 750

    # Protected turns
    protect_first_system: bool = True
    protect_first_human: bool = True
    protect_first_gpt: bool = True
    protect_first_tool: bool = True
    protect_last_n_turns: int = 4

    # Summarization (uses swarm-bot's call_llm)
    summarization_model: str = "opencode-go/minimax-m3"
    temperature: float = 0.3
    max_retries: int = 3
    retry_delay: int = 2

    # Output
    add_summary_notice: bool = True
    summary_notice_text: str = "\n\nSome of your previous tool responses may be summarized to preserve context."
    output_suffix: str = "_compressed"

    # Processing
    max_concurrent_requests: int = 10
    skip_under_target: bool = True
    per_trajectory_timeout: int = 300

    # Metrics
    metrics_enabled: bool = True
    metrics_per_trajectory: bool = True


@dataclass
class TrajectoryCompressionMetrics:
    """Metrics for a single trajectory compression."""
    original_tokens: int = 0
    compressed_tokens: int = 0
    tokens_saved: int = 0
    compression_ratio: float = 1.0

    original_turns: int = 0
    compressed_turns: int = 0
    turns_removed: int = 0

    turns_compressed_start_idx: int = -1
    turns_compressed_end_idx: int = -1
    turns_in_compressed_region: int = 0

    was_compressed: bool = False
    still_over_limit: bool = False
    skipped_under_target: bool = False

    summarization_api_calls: int = 0
    summarization_errors: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "tokens_saved": self.tokens_saved,
            "compression_ratio": round(self.compression_ratio, 4),
            "original_turns": self.original_turns,
            "compressed_turns": self.compressed_turns,
            "turns_removed": self.turns_removed,
            "compression_region": {
                "start_idx": self.turns_compressed_start_idx,
                "end_idx": self.turns_compressed_end_idx,
                "turns_count": self.turns_in_compressed_region,
            },
            "was_compressed": self.was_compressed,
            "still_over_limit": self.still_over_limit,
            "skipped_under_target": self.skipped_under_target,
            "summarization_api_calls": self.summarization_api_calls,
            "summarization_errors": self.summarization_errors,
        }


class TrajectoryCompressor:
    """
    Compresses SWE-agent trajectories to fit within a target token budget.

    Compression strategy (hermes pattern):
    1. Keep protected head turns (system, human, first gpt+tool)
    2. Keep protected tail turns (last N turns)
    3. From the compressible middle region, compress only as much as needed
    4. Replace compressed turns with a single human summary message
    5. Keep remaining middle turns intact (model continues with tools)

    Uses swarm-bot's call_llm for summarization (MiniMax-M3 by default).
    """

    def __init__(self, config: CompressionConfig | None = None) -> None:
        self.config = config or CompressionConfig()
        self._tokenizer: tiktoken.Encoding | None = None
        self._init_tokenizer()

    def _init_tokenizer(self) -> None:
        """Initialize tiktoken tokenizer for token counting."""
        if not _TIKTOKEN_AVAILABLE:
            logger.warning("tiktoken not available, token counting will use char/4 estimate")
            return
        try:
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning("Failed to load tiktoken encoding: %s", e)
            self._tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using the configured tokenizer."""
        if not text:
            return 0
        if self._tokenizer is not None:
            try:
                return len(self._tokenizer.encode(text))
            except Exception:
                pass
        return len(text) // 4

    def count_trajectory_tokens(self, trajectory: list[dict[str, Any]]) -> int:
        """Count total tokens in a trajectory."""
        return sum(self.count_tokens(turn.get("value", "") or "") for turn in trajectory)

    def count_turn_tokens(self, trajectory: list[dict[str, Any]]) -> list[int]:
        """Count tokens for each turn in a trajectory."""
        return [self.count_tokens(turn.get("value", "") or "") for turn in trajectory]

    def _find_protected_indices(
        self, trajectory: list[dict[str, Any]]
    ) -> tuple[set[int], int, int]:
        """Find indices of protected turns."""
        n = len(trajectory)
        protected: set[int] = set()

        first_system = first_human = first_gpt = first_tool = None

        for i, turn in enumerate(trajectory):
            role = turn.get("from", "")
            if role == "system" and first_system is None:
                first_system = i
            elif role == "human" and first_human is None:
                first_human = i
            elif role == "gpt" and first_gpt is None:
                first_gpt = i
            elif role == "tool" and first_tool is None:
                first_tool = i

        if self.config.protect_first_system and first_system is not None:
            protected.add(first_system)
        if self.config.protect_first_human and first_human is not None:
            protected.add(first_human)
        if self.config.protect_first_gpt and first_gpt is not None:
            protected.add(first_gpt)
        if self.config.protect_first_tool and first_tool is not None:
            protected.add(first_tool)

        for i in range(max(0, n - self.config.protect_last_n_turns), n):
            protected.add(i)

        head_protected = [i for i in protected if i < n // 2]
        tail_protected = [i for i in protected if i >= n // 2]

        compressible_start = max(head_protected) + 1 if head_protected else 0
        compressible_end = min(tail_protected) if tail_protected else n

        return protected, compressible_start, compressible_end

    def _extract_turn_content_for_summary(
        self, trajectory: list[dict[str, Any]], start: int, end: int
    ) -> str:
        """Extract content from turns to be summarized."""
        parts = []
        for i in range(start, end):
            turn = trajectory[i]
            role = turn.get("from", "unknown")
            value = turn.get("value", "")
            if len(value) > 3000:
                value = value[:3000] + "..."
            parts.append(f"[{role.upper()}] {value}")
        return "\n---\n".join(parts)

    def _generate_summary(
        self, content: str, metrics: TrajectoryCompressionMetrics
    ) -> str:
        """Generate summary synchronously using call_llm."""
        prompt = (
            f"Summarize the following agent conversation turns concisely. "
            f"This summary will replace these turns in the conversation history.\n\n"
            f"Write the summary from a neutral perspective describing what the assistant did and learned. Include:\n"
            f"1. What actions the assistant took (tool calls, searches, file operations)\n"
            f"2. Key information or results obtained\n"
            f"3. Any important decisions or findings\n"
            f"4. Relevant data, file names, values, or outputs\n\n"
            f"Keep the summary factual and informative. Target approximately "
            f"{self.config.summary_target_tokens} tokens.\n\n"
            f"---\nTURNS TO SUMMARIZE:\n{content}\n---\n\n"
            f"Write only the summary, starting with '[CONTEXT SUMMARY]:' prefix."
        )

        for attempt in range(self.config.max_retries):
            try:
                metrics.summarization_api_calls += 1
                from llm_client import call_llm

                response = call_llm(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.config.summarization_model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.summary_target_tokens * 2,
                )
                if isinstance(response, dict) and response.get("type") == "tool_call":
                    content_result = response.get("args", {}).get("content", "")
                else:
                    content_result = str(response) if response else ""

                if not content_result:
                    raise ValueError("Empty response from LLM")

                summary = content_result.strip()
                if not summary.startswith("[CONTEXT SUMMARY]:"):
                    summary = "[CONTEXT SUMMARY]: " + summary
                return summary

            except Exception as e:
                metrics.summarization_errors += 1
                logger.warning("Summarization attempt %d failed: %s", attempt + 1, e)
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    return (
                        "[CONTEXT SUMMARY]: [Summary generation failed - "
                        "previous turns contained tool calls and responses "
                        "that have been compressed to save context space.]"
                    )
        return "[CONTEXT SUMMARY]: [Compression summary unavailable.]"

    async def _generate_summary_async(
        self, content: str, metrics: TrajectoryCompressionMetrics
    ) -> str:
        """Generate summary asynchronously using call_llm."""
        prompt = (
            f"Summarize the following agent conversation turns concisely. "
            f"This summary will replace these turns in the conversation history.\n\n"
            f"Write the summary from a neutral perspective describing what the assistant did and learned. Include:\n"
            f"1. What actions the assistant took (tool calls, searches, file operations)\n"
            f"2. Key information or results obtained\n"
            f"3. Any important decisions or findings\n"
            f"4. Relevant data, file names, values, or outputs\n\n"
            f"Keep the summary factual and informative. Target approximately "
            f"{self.config.summary_target_tokens} tokens.\n\n"
            f"---\nTURNS TO SUMMARIZE:\n{content}\n---\n\n"
            f"Write only the summary, starting with '[CONTEXT SUMMARY]:' prefix."
        )

        for attempt in range(self.config.max_retries):
            try:
                metrics.summarization_api_calls += 1
                import inspect

                from llm_client import call_llm

                if inspect.iscoroutinefunction(call_llm):
                    response = await call_llm(
                        messages=[{"role": "user", "content": prompt}],
                        model=self.config.summarization_model,
                        temperature=self.config.temperature,
                        max_tokens=self.config.summary_target_tokens * 2,
                    )
                else:
                    response = await asyncio.to_thread(
                        call_llm,
                        messages=[{"role": "user", "content": prompt}],
                        model=self.config.summarization_model,
                        temperature=self.config.temperature,
                        max_tokens=self.config.summary_target_tokens * 2,
                    )

                if isinstance(response, dict) and response.get("type") == "tool_call":
                    content_result = response.get("args", {}).get("content", "")
                else:
                    content_result = str(response) if response else ""

                if not content_result:
                    raise ValueError("Empty response from LLM")

                summary = content_result.strip()
                if not summary.startswith("[CONTEXT SUMMARY]:"):
                    summary = "[CONTEXT SUMMARY]: " + summary
                return summary

            except Exception as e:
                metrics.summarization_errors += 1
                logger.warning("Async summarization attempt %d failed: %s", attempt + 1, e)
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    return (
                        "[CONTEXT SUMMARY]: [Summary generation failed - "
                        "previous turns contained tool calls and responses "
                        "that have been compressed to save context space.]"
                    )
        return "[CONTEXT SUMMARY]: [Compression summary unavailable.]"

    def compress_trajectory(
        self, trajectory: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], TrajectoryCompressionMetrics]:
        """Compress a single trajectory to fit within target token budget."""
        metrics = TrajectoryCompressionMetrics()
        metrics.original_turns = len(trajectory)

        turn_tokens = self.count_turn_tokens(trajectory)
        total_tokens = sum(turn_tokens)
        metrics.original_tokens = total_tokens

        if total_tokens <= self.config.target_max_tokens:
            metrics.skipped_under_target = True
            metrics.compressed_tokens = total_tokens
            metrics.compressed_turns = len(trajectory)
            metrics.compression_ratio = 1.0
            return trajectory, metrics

        protected, compress_start, compress_end = self._find_protected_indices(trajectory)

        if compress_start >= compress_end:
            metrics.compressed_tokens = total_tokens
            metrics.compressed_turns = len(trajectory)
            metrics.still_over_limit = total_tokens > self.config.target_max_tokens
            return trajectory, metrics

        tokens_to_save = total_tokens - self.config.target_max_tokens
        target_tokens_to_compress = tokens_to_save + self.config.summary_target_tokens

        accumulated_tokens = 0
        compress_until = compress_start

        for i in range(compress_start, compress_end):
            accumulated_tokens += turn_tokens[i]
            compress_until = i + 1
            if accumulated_tokens >= target_tokens_to_compress:
                break

        if accumulated_tokens < target_tokens_to_compress and compress_until < compress_end:
            compress_until = compress_end
            accumulated_tokens = sum(turn_tokens[compress_start:compress_end])

        metrics.turns_compressed_start_idx = compress_start
        metrics.turns_compressed_end_idx = compress_until
        metrics.turns_in_compressed_region = compress_until - compress_start

        content_to_summarize = self._extract_turn_content_for_summary(
            trajectory, compress_start, compress_until
        )
        summary = self._generate_summary(content_to_summarize, metrics)

        compressed: list[dict[str, Any]] = []

        for i in range(compress_start):
            turn = dict(trajectory[i])
            if turn.get("from") == "system" and self.config.add_summary_notice:
                turn["value"] = turn["value"] + self.config.summary_notice_text
            compressed.append(turn)

        compressed.append({"from": "human", "value": summary})

        for i in range(compress_until, len(trajectory)):
            compressed.append(dict(trajectory[i]))

        metrics.compressed_turns = len(compressed)
        metrics.compressed_tokens = self.count_trajectory_tokens(compressed)
        metrics.turns_removed = metrics.original_turns - metrics.compressed_turns
        metrics.tokens_saved = metrics.original_tokens - metrics.compressed_tokens
        metrics.compression_ratio = (
            metrics.compressed_tokens / max(metrics.original_tokens, 1)
        )
        metrics.was_compressed = True
        metrics.still_over_limit = metrics.compressed_tokens > self.config.target_max_tokens

        return compressed, metrics

    async def compress_trajectory_async(
        self, trajectory: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], TrajectoryCompressionMetrics]:
        """Compress a single trajectory asynchronously."""
        metrics = TrajectoryCompressionMetrics()
        metrics.original_turns = len(trajectory)

        turn_tokens = self.count_turn_tokens(trajectory)
        total_tokens = sum(turn_tokens)
        metrics.original_tokens = total_tokens

        if total_tokens <= self.config.target_max_tokens:
            metrics.skipped_under_target = True
            metrics.compressed_tokens = total_tokens
            metrics.compressed_turns = len(trajectory)
            metrics.compression_ratio = 1.0
            return trajectory, metrics

        protected, compress_start, compress_end = self._find_protected_indices(trajectory)

        if compress_start >= compress_end:
            metrics.compressed_tokens = total_tokens
            metrics.compressed_turns = len(trajectory)
            metrics.still_over_limit = total_tokens > self.config.target_max_tokens
            return trajectory, metrics

        tokens_to_save = total_tokens - self.config.target_max_tokens
        target_tokens_to_compress = tokens_to_save + self.config.summary_target_tokens

        accumulated_tokens = 0
        compress_until = compress_start

        for i in range(compress_start, compress_end):
            accumulated_tokens += turn_tokens[i]
            compress_until = i + 1
            if accumulated_tokens >= target_tokens_to_compress:
                break

        if accumulated_tokens < target_tokens_to_compress and compress_until < compress_end:
            compress_until = compress_end
            accumulated_tokens = sum(turn_tokens[compress_start:compress_end])

        metrics.turns_compressed_start_idx = compress_start
        metrics.turns_compressed_end_idx = compress_until
        metrics.turns_in_compressed_region = compress_until - compress_start

        content_to_summarize = self._extract_turn_content_for_summary(
            trajectory, compress_start, compress_until
        )
        summary = await self._generate_summary_async(content_to_summarize, metrics)

        compressed: list[dict[str, Any]] = []

        for i in range(compress_start):
            turn = dict(trajectory[i])
            if turn.get("from") == "system" and self.config.add_summary_notice:
                turn["value"] = turn["value"] + self.config.summary_notice_text
            compressed.append(turn)

        compressed.append({"from": "human", "value": summary})

        for i in range(compress_until, len(trajectory)):
            compressed.append(dict(trajectory[i]))

        metrics.compressed_turns = len(compressed)
        metrics.compressed_tokens = self.count_trajectory_tokens(compressed)
        metrics.turns_removed = metrics.original_turns - metrics.compressed_turns
        metrics.tokens_saved = metrics.original_tokens - metrics.compressed_tokens
        metrics.compression_ratio = (
            metrics.compressed_tokens / max(metrics.original_tokens, 1)
        )
        metrics.was_compressed = True
        metrics.still_over_limit = metrics.compressed_tokens > self.config.target_max_tokens

        return compressed, metrics

    def compress_and_save(
        self,
        trajectory: dict[str, Any],
        output_path: str | None = None,
        completed: bool = True,
    ) -> tuple[str, TrajectoryCompressionMetrics]:
        """Compress a trajectory dict and save as ShareGPT JSONL.

        Args:
            trajectory: Trajectory dict (from load_trajectory or Trajectory.to_dict())
            output_path: Output file path. Defaults to {instance_id}_compressed.jsonl
            completed: Whether the trajectory represents a successful run

        Returns:
            Tuple of (output_path, metrics)
        """
        sharegpt = export_sharegpt(trajectory)
        compressed, metrics = self.compress_trajectory(sharegpt)

        instance_id = trajectory.get("instance_id", "unknown")
        if output_path is None:
            output_path = f"{instance_id}{self.config.output_suffix}.jsonl"

        entry = {
            "conversations": compressed,
            "timestamp": datetime.now().isoformat(),
            "model": trajectory.get("model", "unknown"),
            "completed": completed,
            "instance_id": instance_id,
            "compression": metrics.to_dict(),
        }

        with open(output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        logger.info(
            "Compressed trajectory %s: %d turns %d tokens -> %d turns %d tokens "
            "(saved %d tokens, ratio %.2f)",
            instance_id,
            metrics.original_turns,
            metrics.original_tokens,
            metrics.compressed_turns,
            metrics.compressed_tokens,
            metrics.tokens_saved,
            metrics.compression_ratio,
        )

        return output_path, metrics

    def process_entry(
        self, entry: dict[str, Any]
    ) -> tuple[dict[str, Any], TrajectoryCompressionMetrics]:
        """Process a single JSONL entry (synchronous).

        Args:
            entry: JSONL entry dict with 'conversations' key (ShareGPT format)

        Returns:
            Tuple of (processed_entry, metrics)
        """
        conversations = entry.get("conversations", [])
        if not conversations:
            return entry, TrajectoryCompressionMetrics()

        compressed, metrics = self.compress_trajectory(conversations)

        result = dict(entry)
        result["conversations"] = compressed
        result["compression"] = metrics.to_dict()
        result["compressed_at"] = datetime.now().isoformat()

        return result, metrics

    async def process_entry_async(
        self, entry: dict[str, Any]
    ) -> tuple[dict[str, Any], TrajectoryCompressionMetrics]:
        """Process a single JSONL entry (async).

        Args:
            entry: JSONL entry dict with 'conversations' key (ShareGPT format)

        Returns:
            Tuple of (processed_entry, metrics)
        """
        conversations = entry.get("conversations", [])
        if not conversations:
            return entry, TrajectoryCompressionMetrics()

        compressed, metrics = await self.compress_trajectory_async(conversations)

        result = dict(entry)
        result["conversations"] = compressed
        result["compression"] = metrics.to_dict()
        result["compressed_at"] = datetime.now().isoformat()

        return result, metrics

    def process_directory(self, input_dir: str | Path, output_dir: str | Path) -> None:
        """Process all JSONL files in a directory (sync wrapper).

        Args:
            input_dir: Input directory containing JSONL files
            output_dir: Output directory for compressed files
        """
        import asyncio
        asyncio.run(self._process_directory_async(Path(input_dir), Path(output_dir)))

    async def _process_directory_async(
        self, input_dir: Path, output_dir: Path
    ) -> None:
        """Async directory processing with parallel compression and progress tracking.

        Uses semaphore for rate limiting and Rich console for progress display.
        """
        try:
            from rich.console import Console
            from rich.progress import (
                BarColumn,
                Progress,
                SpinnerColumn,
                TaskProgressColumn,
                TextColumn,
                TimeElapsedColumn,
            )
        except ImportError:
            logger.warning("Rich not available, using basic progress output")
            Console = None
            Progress = None

        console = Console() if Console else None
        start_time = time.time()

        jsonl_files = sorted(input_dir.glob("*.jsonl"))
        if not jsonl_files:
            logger.warning("No JSONL files found in %s", input_dir)
            return

        if console:
            console.print(f"\n{'='*60}")
            console.print(f"Input: {input_dir}")
            console.print(f"Output: {output_dir}")
            console.print(f"Files: {len(jsonl_files)}")
            console.print(f"Target max tokens: {self.config.target_max_tokens:,}")
            console.print(f"Max concurrent: {self.config.max_concurrent_requests}")
            console.print(f"{'='*60}\n")

        all_entries: list[tuple[Path, int, dict[str, Any]]] = []
        for file_path in jsonl_files:
            with open(file_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            all_entries.append((file_path, line_num, entry))
                        except json.JSONDecodeError as e:
                            logger.warning("Skipping invalid JSON at %s:%d: %s", file_path, line_num, e)

        total_entries = len(all_entries)

        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        progress_lock = asyncio.Lock()

        compressed_count = 0
        skipped_count = 0
        api_calls = 0
        in_flight = 0

        results: dict[Path, dict[int, tuple[dict[str, Any] | None, TrajectoryCompressionMetrics | None]]] = {
            f: {} for f in jsonl_files
        }

        async def process_single(
            file_path: Path,
            entry_idx: int,
            entry: dict[str, Any],
            progress: Progress | None,
            main_task_id: int | None,
            status_task_id: int | None,
        ) -> None:
            nonlocal compressed_count, skipped_count, api_calls, in_flight

            async with semaphore:
                async with progress_lock:
                    in_flight += 1

                try:
                    processed_entry, metrics = await asyncio.wait_for(
                        self.process_entry_async(entry),
                        timeout=self.config.per_trajectory_timeout,
                    )
                    results[file_path][entry_idx] = (processed_entry, metrics)

                    async with progress_lock:
                        if metrics.was_compressed:
                            compressed_count += 1
                            api_calls += metrics.summarization_api_calls
                        if metrics.skipped_under_target:
                            skipped_count += 1
                        in_flight -= 1

                        if progress and main_task_id is not None and status_task_id is not None:
                            progress.advance(main_task_id)
                            desc = f"✅ {compressed_count} compressed | ⏭️ {skipped_count} skipped | 🔄 {api_calls} API calls | ⚡ {in_flight} in-flight"
                            progress.update(status_task_id, description=f"[dim]{desc}[/dim]")

                except TimeoutError:
                    logger.warning("Timeout processing entry from %s:%d", file_path, entry_idx)
                    async with progress_lock:
                        in_flight -= 1
                        if progress and main_task_id is not None:
                            progress.advance(main_task_id)
                    results[file_path][entry_idx] = (None, None)

                except Exception as e:
                    logger.error("Error processing entry from %s:%d: %s", file_path, entry_idx, e)
                    async with progress_lock:
                        in_flight -= 1
                        if progress and main_task_id is not None:
                            progress.advance(main_task_id)
                    results[file_path][entry_idx] = (entry, TrajectoryCompressionMetrics())

        tasks = []
        if Progress and console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                console=console,
                refresh_per_second=10,
            ) as progress:
                main_task_id = progress.add_task(f"[cyan]Compressing {total_entries:,} trajectories", total=total_entries)
                status_task_id = progress.add_task("[dim]Starting...[/dim]", total=None)

                tasks = [
                    process_single(file_path, entry_idx, entry, progress, main_task_id, status_task_id)
                    for file_path, entry_idx, entry in all_entries
                ]
                await asyncio.gather(*tasks)
        else:
            tasks = [
                process_single(file_path, entry_idx, entry, None, None, None)
                for file_path, entry_idx, entry in all_entries
            ]
            await asyncio.gather(*tasks)

        output_dir.mkdir(parents=True, exist_ok=True)
        for file_path in jsonl_files:
            output_path = output_dir / file_path.name
            file_results = results[file_path]
            sorted_entries = [
                file_results[idx][0]
                for idx in sorted(file_results.keys())
                if file_results[idx] is not None and file_results[idx][0] is not None
            ]
            with open(output_path, "w", encoding="utf-8") as f:
                for entry_out in sorted_entries:
                    f.write(json.dumps(entry_out, ensure_ascii=False) + "\n")

        elapsed = time.time() - start_time
        if console:
            console.print(f"\nCompleted in {elapsed:.1f}s")
            console.print(f"✅ {compressed_count} compressed | ⏭️ {skipped_count} skipped")
            if self.config.metrics_enabled:
                metrics_path = output_dir / "compression_metrics.json"
                metrics_summary = {
                    "total_entries": total_entries,
                    "compressed": compressed_count,
                    "skipped": skipped_count,
                    "elapsed_seconds": round(elapsed, 1),
                }
                with open(metrics_path, "w") as f:
                    json.dump(metrics_summary, f, indent=2)
                console.print(f"💾 Metrics saved to {metrics_path}")


# ---------------------------------------------------------------------------
# Aggregate metrics (hermes pattern for batch processing)
# ---------------------------------------------------------------------------

@dataclass
class TrajectoryMetrics:
    """Aggregate metrics for batch trajectory processing.

    Tracks cumulative statistics across all trajectories in a batch.
    """
    processing_start_time: str = ""
    processing_end_time: str = ""
    processing_duration_seconds: float = 0.0

    trajectories_total: int = 0
    trajectories_compressed: int = 0
    trajectories_skipped_under_target: int = 0
    trajectories_still_over_limit: int = 0
    trajectories_failed: int = 0

    total_original_tokens: int = 0
    total_compressed_tokens: int = 0
    total_tokens_saved: int = 0

    total_summarization_api_calls: int = 0
    total_summarization_errors: int = 0

    def add_trajectory_metrics(self, metrics: TrajectoryCompressionMetrics) -> None:
        """Add a single trajectory's metrics to the aggregate."""
        self.trajectories_total += 1
        self.total_original_tokens += metrics.original_tokens
        self.total_compressed_tokens += metrics.compressed_tokens
        self.total_tokens_saved += metrics.tokens_saved

        if metrics.was_compressed:
            self.trajectories_compressed += 1
        if metrics.skipped_under_target:
            self.trajectories_skipped_under_target += 1
        if metrics.still_over_limit:
            self.trajectories_still_over_limit += 1

        self.total_summarization_api_calls += metrics.summarization_api_calls
        self.total_summarization_errors += metrics.summarization_errors

    def to_dict(self) -> dict[str, Any]:
        avg_ratio = (
            round(self.total_compressed_tokens / max(self.total_original_tokens, 1), 4)
            if self.total_original_tokens > 0 else 1.0
        )
        return {
            "processing_start_time": self.processing_start_time,
            "processing_end_time": self.processing_end_time,
            "processing_duration_seconds": round(self.processing_duration_seconds, 2),
            "summary": {
                "total_trajectories": self.trajectories_total,
                "trajectories_compressed": self.trajectories_compressed,
                "trajectories_skipped_under_target": self.trajectories_skipped_under_target,
                "trajectories_still_over_limit": self.trajectories_still_over_limit,
                "trajectories_failed": self.trajectories_failed,
            },
            "tokens": {
                "total_original": self.total_original_tokens,
                "total_compressed": self.total_compressed_tokens,
                "total_saved": self.total_tokens_saved,
                "avg_compression_ratio": avg_ratio,
            },
            "summarization": {
                "total_api_calls": self.total_summarization_api_calls,
                "total_errors": self.total_summarization_errors,
            },
        }


# ---------------------------------------------------------------------------
# CLI for trajectory analysis
# ---------------------------------------------------------------------------

def main() -> int:
    """CLI for trajectory analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="SWE-agent Trajectory Analyzer")
    parser.add_argument("path", help="Trajectory file or directory")
    parser.add_argument("--html", help="Output HTML report to path")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    args = parser.parse_args()

    path = Path(args.path)

    if path.is_dir():
        trajectories = load_trajectory_dir(path)
        print(f"Loaded {len(trajectories)} trajectories from {path}")
        print()
        print(generate_summary_table(trajectories))

        if args.html:
            for traj in trajectories:
                traj_id = traj.get("instance_id", "unknown")
                out_path = Path(args.html) / f"{traj_id}.html"
                generate_html_report(traj, out_path)
            print(f"\nHTML reports saved to {args.html}/")

    elif path.is_file():
        traj = load_trajectory(path)
        stats = compute_stats(traj)

        if args.stats:
            print(f"Instance: {stats.instance_id}")
            print(f"Steps: {stats.total_steps}")
            print(f"Cost: ${stats.total_cost:.4f}")
            print(f"Duration: {stats.duration_seconds:.1f}s")
            print(f"Success: {stats.success}")
            print(f"Submitted: {stats.submitted}")
            print(f"Tools used: {stats.tools_used}")

        if args.html:
            generate_html_report(traj, Path(args.html))
            print(f"HTML report saved to {args.html}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
