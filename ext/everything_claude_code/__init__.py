"""
Everything Claude Code (ECC) Integration — v1.0

Selective integration of ECC's specialized agents, skills, hooks, and rules
into the Legion swarm-bot ecosystem.

ECC provides:
- 13 premium agents: architect, planner, code-reviewer, security-reviewer,
  tdd-guide, build-error-resolver, refactor-cleaner, e2e-runner,
  loop-operator, performance-optimizer, harness-optimizer,
  silent-failure-hunter, type-design-analyzer
- 9 high-value skills: agentic-engineering, autonomous-loops, tdd-workflow,
  security-review, security-scan, continuous-learning, etc.
- Hook system for pre/post-tool quality enforcement
- Language-specific linting rules (Python, TypeScript, Go, Rust, etc.)

Source: https://github.com/affaan-m/everything-claude-code
License: MIT
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ECC root directory — sibling to this package (ext/everything-claude-code/)
_ECC_ROOT = Path(__file__).parent.parent / "everything-claude-code"
_AGENTS_DIR = _ECC_ROOT / "agents"
_SKILLS_DIR = _ECC_ROOT / "skills"
_HOOKS_FILE = _ECC_ROOT / "hooks" / "hooks.json"
_HOOKS_README = _ECC_ROOT / "hooks" / "README.md"
_RULES_DIR = _ECC_ROOT / "rules"

# ── Agent Registry ──────────────────────────────────────────────────────────────

ECC_AGENTS: dict[str, dict[str, Any]] = {
    "planner": {
        "description": "Expert planning specialist for complex features and refactoring",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.1,
        "prompt_file": "planner.md",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "domain": "planning",
    },
    "code-reviewer": {
        "description": "Senior code reviewer ensuring quality, security, and maintainability",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.0,
        "prompt_file": "code-reviewer.md",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "domain": "engineering",
    },
    "security-reviewer": {
        "description": "Vulnerability detection — OWASP Top 10, secrets, injection, SSRF",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.0,
        "prompt_file": "security-reviewer.md",
        "tools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        "domain": "engineering",
    },
    "tdd-guide": {
        "description": "TDD specialist enforcing write-tests-first with 80%+ coverage",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.1,
        "prompt_file": "tdd-guide.md",
        "tools": ["Read", "Write", "Edit", "Bash", "Grep"],
        "domain": "engineering",
    },
    "build-error-resolver": {
        "description": "General build and type error resolution across all languages",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.0,
        "prompt_file": "build-error-resolver.md",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "domain": "engineering",
    },
    "refactor-cleaner": {
        "description": "Dead code detection, cleanup, and refactoring guidance",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.1,
        "prompt_file": "refactor-cleaner.md",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "domain": "engineering",
    },
    "e2e-runner": {
        "description": "Playwright end-to-end testing — critical user flow automation",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.1,
        "prompt_file": "e2e-runner.md",
        "tools": ["Read", "Write", "Bash", "Grep"],
        "domain": "engineering",
    },
    "loop-operator": {
        "description": "Autonomous loop execution — monitor for stalls, intervene on failures",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.0,
        "prompt_file": "loop-operator.md",
        "tools": ["Read", "Bash", "Grep", "Glob"],
        "domain": "operations",
    },
    "performance-optimizer": {
        "description": "Performance profiling, bottleneck detection, optimization",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.1,
        "prompt_file": "performance-optimizer.md",
        "tools": ["Read", "Bash", "Grep", "Glob"],
        "domain": "engineering",
    },
    "harness-optimizer": {
        "description": "Agent harness config tuning — reliability, cost, throughput",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.0,
        "prompt_file": "harness-optimizer.md",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "domain": "engineering",
    },
    "architect": {
        "description": "System design and scalability — architectural decision support",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.1,
        "prompt_file": "architect.md",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "domain": "engineering",
    },
    "silent-failure-hunter": {
        "description": "Detects silent failures, swallowed exceptions, failed async tasks",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.0,
        "prompt_file": "silent-failure-hunter.md",
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "domain": "engineering",
    },
    "type-design-analyzer": {
        "description": "Type system design — API contracts, generic constraints, variance",
        "model": "opencode-go/minimax-m3",
        "temperature": 0.1,
        "prompt_file": "type-design-analyzer.md",
        "tools": ["Read", "Grep", "Glob"],
        "domain": "engineering",
    },
}

# ── Skills Index ───────────────────────────────────────────────────────────────

ECC_SKILLS: dict[str, dict[str, Any]] = {
    "agentic-engineering": {
        "description": "Building reliable autonomous agents with loops, guards, and recovery",
        "path": "agentic-engineering/SKILL.md",
    },
    "autonomous-loops": {
        "description": "Running autonomous loops safely — stall detection, intervention",
        "path": "autonomous-loops/SKILL.md",
    },
    "continuous-learning": {
        "description": "Auto-extracting patterns from sessions into reusable skills",
        "path": "continuous-learning/SKILL.md",
    },
    "tdd-workflow": {
        "description": "Test-driven development workflow — red-green-refactor cycle",
        "path": "tdd-workflow/SKILL.md",
    },
    "security-review": {
        "description": "Security review methodology — OWASP Top 10, secrets scanning",
        "path": "security-review/SKILL.md",
    },
    "security-scan": {
        "description": "Automated security scanning — npm audit, dependency checks",
        "path": "security-scan/SKILL.md",
    },
}


# ── Prompt Loader ──────────────────────────────────────────────────────────────

def load_agent_prompt(agent_key: str) -> str | None:
    """Load ECC agent markdown prompt by key."""
    agent = ECC_AGENTS.get(agent_key)
    if not agent:
        return None
    prompt_file = _AGENTS_DIR / agent["prompt_file"]
    if prompt_file.exists():
        return prompt_file.read_text()
    logger.warning(f"ECC prompt file not found: {prompt_file}")
    return None


def load_skill_content(skill_key: str) -> str | None:
    """Load ECC skill content by key."""
    skill = ECC_SKILLS.get(skill_key)
    if not skill:
        return None
    skill_file = _SKILLS_DIR / skill["path"]
    if skill_file.exists():
        return skill_file.read_text()
    logger.warning(f"ECC skill file not found: {skill_file}")
    return None


# ── Hooks Loader ───────────────────────────────────────────────────────────────

def load_hooks_config() -> dict[str, Any] | None:
    """Load ECC hooks configuration."""
    if _HOOKS_FILE.exists():
        return json.loads(_HOOKS_FILE.read_text())
    return None


def get_hooks_summary() -> str:
    """Get a human-readable summary of ECC hooks for debugging."""
    hooks = load_hooks_config()
    if not hooks:
        return "ECC hooks: not available"
    hook_count = len(hooks.get("hooks", []))
    return f"ECC hooks: {hook_count} hooks configured"


# ── Agent Lookup ───────────────────────────────────────────────────────────────

def get_ecc_agent(agent_key: str) -> dict[str, Any] | None:
    """Get ECC agent definition by key."""
    return ECC_AGENTS.get(agent_key)


def list_ecc_agents() -> list[str]:
    """List all available ECC agent keys."""
    return list(ECC_AGENTS.keys())


def list_ecc_skills() -> list[str]:
    """List all available ECC skill keys."""
    return list(ECC_SKILLS.keys())


def get_ecc_agent_prompt(agent_key: str) -> str | None:
    """Get the full system prompt for an ECC agent."""
    return load_agent_prompt(agent_key)


# ── Verification ───────────────────────────────────────────────────────────────

def verify_installation() -> dict[str, Any]:
    """Verify ECC integration is correctly installed."""
    results = {
        "agents_dir": str(_AGENTS_DIR),
        "agents_dir_exists": _AGENTS_DIR.exists(),
        "skills_dir": str(_SKILLS_DIR),
        "skills_dir_exists": _SKILLS_DIR.exists(),
        "hooks_file": str(_HOOKS_FILE),
        "hooks_file_exists": _HOOKS_FILE.exists(),
        "rules_dir": str(_RULES_DIR),
        "rules_dir_exists": _RULES_DIR.exists(),
        "agents_loaded": len(ECC_AGENTS),
        "skills_loaded": len(ECC_SKILLS),
    }
    results["status"] = "ok" if all([
        results["agents_dir_exists"],
        results["skills_dir_exists"],
        results["hooks_file_exists"],
    ]) else "broken"
    return results


if __name__ == "__main__":
    print("Everything Claude Code Integration v1.0")
    print("=" * 50)
    v = verify_installation()
    for k, val in v.items():
        status = "✅" if isinstance(val, bool) and val else "   "
        print(f"  {status} {k}: {val}")
