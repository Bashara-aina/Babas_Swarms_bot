"""SWE-agent __init__ — public API."""

from core.swe_agent.config import (
    DEFAULT_CONFIG,
    DEFAULT_CONFIG_ANTHROPIC,
    DEFAULT_CONFIG_MINIMAX,
    SWEAgentConfig,
    load_config,
)
from core.swe_agent.environment import Environment
from core.swe_agent.loop import MaxStepsExceeded, SWEAgentLoop, Trajectory
from core.swe_agent.prompts import PromptBuilder
from core.swe_agent.tools import (
    TOOL_DEFINITIONS,
    ToolResult,
    bash,
    grep,
    glob,
    str_replace_editor,
    submit,
)
from core.swe_agent.trajectory import (
    TrajectoryStats,
    compute_stats,
    generate_html_report,
    generate_summary_table,
    load_trajectory,
    load_trajectory_dir,
)

__all__ = [
    # Config
    "SWEAgentConfig",
    "DEFAULT_CONFIG",
    "DEFAULT_CONFIG_MINIMAX",
    "DEFAULT_CONFIG_ANTHROPIC",
    "load_config",
    # Loop
    "SWEAgentLoop",
    "Trajectory",
    "MaxStepsExceeded",
    # Environment
    "Environment",
    # Tools
    "str_replace_editor",
    "bash",
    "grep",
    "glob",
    "submit",
    "ToolResult",
    "TOOL_DEFINITIONS",
    # Prompts
    "PromptBuilder",
    # Trajectory
    "TrajectoryStats",
    "compute_stats",
    "generate_html_report",
    "generate_summary_table",
    "load_trajectory",
    "load_trajectory_dir",
]