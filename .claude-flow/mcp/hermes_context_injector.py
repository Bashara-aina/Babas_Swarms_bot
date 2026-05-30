#!/usr/bin/env python3
"""
Hermes Context Injector — Auto-injects CLAUDE.md and project context for Hermes sessions.

Bridges the gap where Claude Code's native session auto-indexes CLAUDE.md but
Hermes must be explicitly passed context per call.

Features:
- CLAUDE.md auto-reader with fallback to memory bootstrap
- Context aggregation from project files (package.json, requirements.txt, etc.)
- Project profile system for saved context configurations
- Token budgeting with intelligent prioritization
- Integration with hermes-mcp-server.py for session auto-injection
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Paths ─────────────────────────────────────────────────────────────────────
HERMES_CONFIG_DIR = Path.home() / ".hermes"
CONTEXT_PROFILES_DIR = HERMES_CONFIG_DIR / "context_profiles"
MEMORY_BOOTSTRAP_PATH = Path.home() / ".claude" / "memory_bootstrap.md"

# ── Token Budget Defaults ──────────────────────────────────────────────────────
DEFAULT_MAX_CHARS = 4000
PRIORITY_ORDER = ["claude_md", "git_commits", "package_deps", "project_config"]

# ── File Search Paths ─────────────────────────────────────────────────────────
CLAUDE_MD_LOCATIONS = [
    "CLAUDE.md",
    ".claude/CLAUDE.md",
    ".claude/rules/swarm-orchestration/SKILL.md",
    ".claude/rules/ui-ux-excellence.md",
    ".claude/rules/*.md",
]

DEP_FILES = {
    "package.json": "package_deps",
    "requirements.txt": "pip_deps",
    "pyproject.toml": "python_deps",
    "Cargo.toml": "rust_deps",
    "go.mod": "go_deps",
    "pom.xml": "java_deps",
    "build.gradle": "java_deps",
}


# =============================================================================
# CLAUDE.md Auto-Reader
# =============================================================================

def read_claude_md(project_path: str) -> str:
    """
    Read CLAUDE.md from project root with fallback support.

    Searches in order:
    1. CLAUDE.md in project root
    2. .claude/CLAUDE.md
    3. .claude/rules/*.md files
    4. Memory bootstrap if nothing found

    Args:
        project_path: Absolute path to project directory

    Returns:
        CLAUDE.md contents as string, or memory bootstrap fallback
    """
    project = Path(project_path)

    # Try main CLAUDE.md locations
    for rel_path in ["CLAUDE.md", ".claude/CLAUDE.md"]:
        full_path = project / rel_path
        if full_path.exists() and full_path.is_file():
            try:
                content = full_path.read_text(encoding="utf-8").strip()
                if content:
                    return f"# CLAUDE.md ({rel_path})\n\n{content}"
            except Exception:
                pass

    # Try .claude/rules/*.md files
    rules_dir = project / ".claude" / "rules"
    if rules_dir.exists():
        rule_files = sorted(rules_dir.glob("*.md"))
        if rule_files:
            collected = ["# CLAUDE.md (.claude/rules/)"]
            for rf in rule_files:
                try:
                    content = rf.read_text(encoding="utf-8").strip()
                    if content and len(content) > 100:  # Skip tiny snippets
                        collected.append(f"\n## {rf.name}\n\n{content}")
                except Exception:
                    pass
            if len(collected) > 1:
                return "\n".join(collected)

    # Fallback to memory bootstrap
    if MEMORY_BOOTSTRAP_PATH.exists():
        try:
            return f"# Memory Bootstrap (fallback)\n\n{MEMORY_BOOTSTRAP_PATH.read_text(encoding='utf-8')}"
        except Exception:
            pass

    return ""


def get_recent_commits(project_path: str, count: int = 3) -> str:
    """
    Get recent git commit messages.

    Args:
        project_path: Absolute path to project directory
        count: Number of recent commits to retrieve

    Returns:
        Formatted string of recent commit messages
    """
    try:
        result = subprocess.run(
            ["git", "log", f"-{count}", "--oneline", "--format=%s"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            commits = result.stdout.strip().split("\n")
            lines = [f"- {msg}" for msg in commits if msg.strip()]
            return "# Recent Commits\n" + "\n".join(lines)
    except Exception:
        pass
    return ""


def get_git_commit_message(project_path: str) -> str:
    """
    Get current COMMIT_EDITMSG content if exists.

    Args:
        project_path: Absolute path to project directory

    Returns:
        COMMIT_EDITMSG contents or empty string
    """
    commit_file = Path(project_path) / ".git" / "COMMIT_EDITMSG"
    if commit_file.exists():
        try:
            return f"# Commit Message Template\n\n{commit_file.read_text(encoding='utf-8').strip()}"
        except Exception:
            pass
    return ""


# =============================================================================
# Dependency Parsers
# =============================================================================

def parse_package_json(content: str) -> str:
    """Extract key dependencies from package.json."""
    try:
        data = json.loads(content)
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})

        lines = ["## Dependencies"]
        if deps:
            lines.append("**Production:**")
            for name, ver in list(deps.items())[:15]:
                lines.append(f"- {name}: {ver}")
        if dev_deps:
            lines.append("**Dev:**")
            for name, ver in list(dev_deps.items())[:10]:
                lines.append(f"- {name}: {ver}")
        return "\n".join(lines)
    except Exception:
        return ""


def parse_requirements_txt(content: str) -> str:
    """Extract packages from requirements.txt."""
    lines = ["## Python Dependencies"]
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-"):
            # Handle pkg[extra]==version format
            pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0]
            if pkg:
                lines.append(f"- {pkg}")
    return "\n".join(lines[:20])


def parse_pyproject_toml(content: str) -> str:
    """Extract dependencies from pyproject.toml."""
    try:
        lines = ["## Python Dependencies (pyproject.toml)"]
        in_deps = False
        for line in content.split("\n"):
            if line.strip().startswith("dependencies"):
                in_deps = True
            elif in_deps and line.strip().startswith("["):
                in_deps = False
            elif in_deps and line.strip():
                pkg = line.strip().strip('"').strip("'")
                if pkg:
                    lines.append(f"- {pkg}")
        return "\n".join(lines[:20])
    except Exception:
        return ""


def parse_dep_file(file_path: Path, file_type: str) -> str:
    """Parse a dependency file based on its type."""
    if not file_path.exists():
        return ""

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return ""

    if file_type == "package_deps":
        return parse_package_json(content)
    elif file_type == "pip_deps":
        return parse_requirements_txt(content)
    elif file_type == "python_deps":
        return parse_pyproject_toml(content)
    return ""


# =============================================================================
# Context Aggregation
# =============================================================================

def build_context(
    project_path: str,
    includes: list[str] | None = None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """
    Build a complete context injection string.

    Args:
        project_path: Absolute path to project directory
        includes: List of context types to include. Defaults to all.
        max_chars: Maximum characters for the context (for budgeting)

    Returns:
        Formatted context string ready for injection
    """
    project = Path(project_path)
    if not project.exists():
        return "# Error\n\nProject path does not exist."

    # Determine what to include
    if includes is None:
        includes = ["claude_md", "git_commits", "package_deps", "project_config"]

    parts = []

    # 1. CLAUDE.md (highest priority)
    if "claude_md" in includes:
        claude_md = read_claude_md(project_path)
        if claude_md:
            parts.append(claude_md)

    # 2. Git commit message template
    if "git_commits" in includes:
        commit_msg = get_git_commit_message(project_path)
        if commit_msg:
            parts.append(commit_msg)

    # 3. Recent commits
    if "git_commits" in includes:
        recent = get_recent_commits(project_path, count=3)
        if recent:
            parts.append(recent)

    # 4. Dependency files
    if "package_deps" in includes:
        for filename, dep_type in DEP_FILES.items():
            file_path = project / filename
            if file_path.exists():
                deps = parse_dep_file(file_path, dep_type)
                if deps:
                    parts.append(deps)

    # Combine and budget
    context = "\n\n---\n\n".join(parts)
    return budget_context(context, max_chars)


def budget_context(context: str, max_chars: int) -> str:
    """
    Truncate context to max_chars while preserving priority order.

    Priority: CLAUDE.md instructions > git commit messages > package deps

    Args:
        context: The full context string
        max_chars: Maximum allowed characters

    Returns:
        Truncated context string
    """
    if len(context) <= max_chars:
        return context

    # Split into sections by markdown headers
    sections = re.split(r"(?=^# )", context, flags=re.MULTILINE)
    prioritized = []
    remaining = []

    for section in sections:
        if not section.strip():
            continue
        # Prioritize CLAUDE.md content
        if "CLAUDE.md" in section[:100]:
            prioritized.append(section)
        else:
            remaining.append(section)

    # Rebuild with priority
    result_parts = prioritized.copy()
    for section in remaining:
        test = "\n\n---\n\n".join(result_parts + [section])
        if len(test) <= max_chars:
            result_parts.append(section)

    return "\n\n---\n\n".join(result_parts)


# =============================================================================
# Project Profile System
# =============================================================================

def context_profile_save(
    name: str,
    project_path: str,
    includes: list[str] | None = None,
) -> str:
    """
    Save a context profile for later use.

    Profiles are stored in ~/.hermes/context_profiles/{name}.json

    Args:
        name: Profile name
        project_path: Path to associate with this profile
        includes: List of context types to include

    Returns:
        Path to the saved profile
    """
    CONTEXT_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    profile = {
        "name": name,
        "project_path": project_path,
        "includes": includes or ["claude_md", "git_commits", "package_deps"],
        "max_chars": DEFAULT_MAX_CHARS,
    }

    profile_path = CONTEXT_PROFILES_DIR / f"{name}.json"
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    return str(profile_path)


def context_profile_load(name: str) -> dict[str, Any] | None:
    """
    Load a saved context profile.

    Args:
        name: Profile name to load

    Returns:
        Profile dictionary or None if not found
    """
    profile_path = CONTEXT_PROFILES_DIR / f"{name}.json"
    if not profile_path.exists():
        return None

    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def context_profile_list() -> list[dict[str, Any]]:
    """
    List all available context profiles.

    Returns:
        List of profile metadata dictionaries
    """
    CONTEXT_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    profiles = []
    for profile_path in CONTEXT_PROFILES_DIR.glob("*.json"):
        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            data["_file"] = str(profile_path)
            profiles.append(data)
        except Exception:
            pass

    return sorted(profiles, key=lambda x: x.get("name", ""))


# =============================================================================
# MCP Handler
# =============================================================================

HERMES_CONTEXT_INJECTOR_SCHEMA = {
    "name": "hermes_context_injector",
    "description": "Auto-injects CLAUDE.md and project context for Hermes sessions",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "enum": [
                    "inject",
                    "read_claude_md",
                    "build_context",
                    "profile_save",
                    "profile_load",
                    "profile_list",
                ],
                "description": "Action to perform",
            },
            "project_path": {
                "type": "string",
                "description": "Absolute path to the project directory",
            },
            "profile_name": {
                "type": "string",
                "description": "Name for profile save/load operations",
            },
            "max_chars": {
                "type": "integer",
                "default": DEFAULT_MAX_CHARS,
                "description": "Maximum characters for context budget",
            },
            "includes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of context types to include",
            },
        },
    },
}


def handle_hermes_context_injector(
    action: str,
    project_path: str | None = None,
    profile_name: str | None = None,
    max_chars: int = DEFAULT_MAX_CHARS,
    includes: list[str] | None = None,
) -> dict[str, Any]:
    """
    MCP handler for hermes_context_injector tools.

    Args:
        action: One of inject, read_claude_md, build_context,
                profile_save, profile_load, profile_list
        project_path: Project path for context operations
        profile_name: Name for profile operations
        max_chars: Max characters for context budgeting
        includes: List of context types to include

    Returns:
        Dictionary with operation results
    """
    # Default project path
    if project_path is None:
        project_path = os.getcwd()

    if action == "read_claude_md":
        content = read_claude_md(project_path)
        return {
            "success": True,
            "content": content,
            "found": bool(content),
        }

    elif action == "build_context":
        context = build_context(project_path, includes=includes, max_chars=max_chars)
        return {
            "success": True,
            "context": context,
            "length": len(context),
        }

    elif action == "inject":
        context = build_context(project_path, includes=includes, max_chars=max_chars)
        return {
            "success": True,
            "injected_context": context,
            "length": len(context),
        }

    elif action == "profile_save":
        if not profile_name:
            return {"success": False, "error": "profile_name required"}
        path = context_profile_save(profile_name, project_path, includes=includes)
        return {"success": True, "profile_path": path}

    elif action == "profile_load":
        if not profile_name:
            return {"success": False, "error": "profile_name required"}
        profile = context_profile_load(profile_name)
        if profile:
            return {"success": True, "profile": profile}
        return {"success": False, "error": f"Profile '{profile_name}' not found"}

    elif action == "profile_list":
        profiles = context_profile_list()
        return {"success": True, "profiles": profiles}

    else:
        return {"success": False, "error": f"Unknown action: {action}"}


# =============================================================================
# Integration Functions for hermes-mcp-server.py
# =============================================================================

def context_inject(project_path: str) -> str:
    """
    Main integration function for hermes-mcp-server.py.

    Called on session init to get auto-injected context.

    Args:
        project_path: Absolute path to project directory

    Returns:
        Formatted context string ready for injection
    """
    return build_context(project_path, max_chars=DEFAULT_MAX_CHARS)


def context_inject_now(project_path: str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """
    Tool-exposed context injection function.

    Use this as the MCP tool handler for context_inject_now.

    Args:
        project_path: Absolute path to project directory
        max_chars: Maximum characters for context budgeting

    Returns:
        Formatted context string ready for injection
    """
    return build_context(project_path, max_chars=max_chars)


# =============================================================================
# Auto-Injection Integration
# =============================================================================

SESSION_START_CONTEXT = """
# Session Context Injection

This context was automatically generated by Hermes Context Injector.
It provides project configuration and CLAUDE.md instructions to ensure
Hermes operates with the same context as a direct Claude Code session.

"""


def get_session_start_context(project_path: str) -> str:
    """
    Get context for session start injection.

    Use this when Hermes starts a new session to automatically
    prepend CLAUDE.md and project context.

    Args:
        project_path: Absolute path to project directory

    Returns:
        Full context string for session start injection
    """
    context = context_inject(project_path)
    return SESSION_START_CONTEXT + context


# =============================================================================
# CLI Entry Point (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python hermes_context_injector.py <project_path>")
        sys.exit(1)

    path = sys.argv[1]
    print("=== CLAUDE.md ===")
    print(read_claude_md(path))
    print("\n=== FULL CONTEXT ===")
    print(build_context(path))