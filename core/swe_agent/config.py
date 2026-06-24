"""
SWE-agent configuration — YAML-based config for agent, environment, and tools.

Configuration is hierarchical:
- agent: Model, prompts, tool settings
- env: Repository, docker/runtime settings
- tools: Per-tool configuration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config model
# ---------------------------------------------------------------------------


@dataclass
class ModelConfig:
    """LLM model configuration."""

    name: str = "opencode-go/minimax-m3"
    temperature: float = 0.0
    max_tokens: int = 8192
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


@dataclass
class AgentConfig:
    """Agent loop configuration."""

    model: ModelConfig = field(default_factory=ModelConfig)
    max_steps: int = 30
    tool_call_format: str = "openai"  # 'openai' or 'anthropic'
    extra_headers: dict[str, str] | None = None


@dataclass
class EnvConfig:
    """Environment configuration."""

    repo_url: str = ""
    repo_path: str = ""
    commit: str = ""
    branch: str = ""
    work_dir: str = ""
    docker_image: str = ""  # Optional docker image for sandbox
    env_vars: dict[str, str] = field(default_factory=dict)


@dataclass
class ToolsConfig:
    """Tools configuration."""

    # Bash tool
    bash_timeout: int = 60
    dangerous_commands_allowed: bool = False

    # Grep tool
    grep_max_results: int = 100

    # Str_replace_editor
    max_file_size: int = 1024 * 1024  # 1MB


@dataclass
class SWEAgentConfig:
    """Complete SWE-agent configuration."""

    agent: AgentConfig = field(default_factory=AgentConfig)
    env: EnvConfig = field(default_factory=EnvConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SWEAgentConfig:
        """Create config from dict."""
        model_cfg = ModelConfig(**data.get("agent", {}).get("model", {}))
        agent_cfg = AgentConfig(model=model_cfg, **{
            k: v for k, v in data.get("agent", {}).items()
            if k != "model"
        })
        env_cfg = EnvConfig(**data.get("env", {}))
        tools_cfg = ToolsConfig(**data.get("tools", {}))

        return cls(agent=agent_cfg, env=env_cfg, tools=tools_cfg)

    @classmethod
    def from_yaml(cls, path: str | Path) -> SWEAgentConfig:
        """Load config from YAML file."""
        p = Path(path)
        if not p.exists():
            logger.warning("Config file not found: %s, using defaults", path)
            return cls()

        with p.open() as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data or {})

    def to_yaml(self, path: str | Path) -> None:
        """Save config to YAML file."""
        data = {
            "agent": {
                "model": self.agent.model.__dict__,
                "max_steps": self.agent.max_steps,
                "tool_call_format": self.agent.tool_call_format,
            },
            "env": self.env.__dict__,
            "tools": self.tools.__dict__,
        }

        with Path(path).open("w") as f:
            yaml.dump(data, f, default_flow_style=False)


# ---------------------------------------------------------------------------
# Default configs
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = SWEAgentConfig()

DEFAULT_CONFIG_MINIMAX = SWEAgentConfig(
    agent=AgentConfig(
        model=ModelConfig(
            name="opencode-go/minimax-m3",
            temperature=0.0,
            max_tokens=8192,
        ),
        max_steps=30,
    ),
)

DEFAULT_CONFIG_ANTHROPIC = SWEAgentConfig(
    agent=AgentConfig(
        model=ModelConfig(
            name="anthropic/claude-sonnet-4-20250514",
            temperature=0.0,
            max_tokens=4096,
        ),
        max_steps=30,
    ),
)


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


def load_config(config_path: str | Path | None = None) -> SWEAgentConfig:
    """Load configuration.

    Args:
        config_path: Path to YAML config file. If None, returns defaults.

    Returns:
        SWEAgentConfig instance
    """
    if config_path:
        return SWEAgentConfig.from_yaml(config_path)

    # Check for config in common locations
    search_paths = [
        Path.cwd() / "swe_agent.yaml",
        Path.cwd() / "swe_agent.yml",
        Path.home() / ".swe_agent" / "config.yaml",
        Path(__file__).parent.parent.parent / "config" / "swe_agent.yaml",
    ]

    for p in search_paths:
        if p.exists():
            logger.info("Loading SWE-agent config from %s", p)
            return SWEAgentConfig.from_yaml(p)

    logger.info("No config file found, using defaults")
    return DEFAULT_CONFIG
