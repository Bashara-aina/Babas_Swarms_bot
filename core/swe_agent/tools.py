"""
SWE-agent Tools — file editor, bash, grep, submit, and web search.

These are the computer-use tools that give the LLM agent-operating capabilities:
- str_replace_editor: view, create, str_replace, insert, undo
- bash: execute commands with working directory context
- grep: search for patterns in files
- submit: generate a git patch and finalize the solution
"""

from __future__ import annotations

import difflib
import logging
import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ToolExecutionError(Exception):
    """Raised when a tool fails to execute."""


class FileNotFoundError(Exception):
    """Raised when a file to edit/view does not exist."""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ToolResult:
    """Result from a tool execution."""

    success: bool
    output: str = ""
    error: str = ""
    # For file tools, track the modified file for undo
    modified_file: str = ""
    old_content: str = ""

    def to_obs(self) -> str:
        """Format as SWE-agent-style OBSERVATION block."""
        if self.success:
            return self.output
        return f"Error: {self.error}"


@dataclass
class EditHistory:
    """Tracks edits for undo capability."""

    path: str
    old_content: str
    new_content: str
    command: str  # 'str_replace', 'insert', 'create'
    timestamp: float = 0.0


# Global edit history for undo support
_undo_stack: list[EditHistory] = []
_MAX_UNDO = 50


# ---------------------------------------------------------------------------
# str_replace_editor tool
# ---------------------------------------------------------------------------


def str_replace_editor(
    command: str,
    path: str,
    file_text: str | None = None,
    old_str: str | None = None,
    new_str: str | None = None,
    insert_line: int | None = None,
    working_dir: str | None = None,
) -> ToolResult:
    """Execute a str_replace_editor command.

    Commands:
    - view <path>: Show file contents with line numbers
    - create <path> --file_text <content>: Create a new file
    - str_replace <path> --old_str <old> --new_str <new>: Replace text
    - insert <path> --insert_line <N>: Insert text after line N
    - undo <path>: Undo last edit to this file

    Args:
        command: One of 'view', 'create', 'str_replace', 'insert', 'undo'
        path: File path to operate on
        file_text: Content for create command
        old_str: Old text to replace (str_replace)
        new_str: New text to replace with (str_replace)
        insert_line: Line number to insert after (insert)
        working_dir: The working directory for this SWE-agent session

    Returns:
        ToolResult with output or error
    """
    global _undo_stack

    base_dir = working_dir or os.getcwd()
    full_path = Path(base_dir) / path if not Path(path).is_absolute() else Path(path)
    full_path = full_path.resolve()

    # Normalize path for display (use repo-relative)
    try:
        rel_path = full_path.relative_to(Path(base_dir).resolve())
        display_path = str(rel_path)
    except ValueError:
        display_path = str(full_path)

    try:
        if command == "view":
            return _view_file(full_path, display_path)

        elif command == "create":
            if file_text is None:
                return ToolResult(success=False, error="create requires --file_text")
            return _create_file(full_path, file_text, display_path)

        elif command == "str_replace":
            if old_str is None or new_str is None:
                return ToolResult(success=False, error="str_replace requires --old_str and --new_str")
            return _str_replace(full_path, old_str, new_str, display_path)

        elif command == "insert":
            if insert_line is None:
                return ToolResult(success=False, error="insert requires --insert_line")
            if file_text is None:
                return ToolResult(success=False, error="insert requires --file_text")
            return _insert_at_line(full_path, insert_line, file_text, display_path)

        elif command == "undo":
            return _undo_edit(full_path, display_path)

        else:
            return ToolResult(success=False, error=f"Unknown command: {command}")

    except FileNotFoundError as e:
        return ToolResult(success=False, error=str(e))
    except Exception as e:
        logger.exception("str_replace_editor failed: %s %s", command, path)
        return ToolResult(success=False, error=f"Unexpected error: {e}")


def _view_file(path: Path, display_path: str) -> ToolResult:
    """View a file with line numbers (cat -n style)."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {display_path}")

    content = path.read_text()
    lines = content.splitlines()

    # Produce "cat -n" style output
    output_lines = []
    for i, line in enumerate(lines, 1):
        output_lines.append(f"{i:>6}:  {line}")

    # Add trailing newline indicator if file ends without newline
    if content.endswith("\n"):
        output_lines.append("")
    else:
        output_lines.append("\n(No trailing newline)")

    header = f"File: {display_path}"
    output = header + "\n" + "=" * 60 + "\n" + "\n".join(output_lines)

    return ToolResult(success=True, output=output)


def _create_file(path: Path, content: str, display_path: str) -> ToolResult:
    """Create a new file."""
    if path.exists():
        return ToolResult(success=False, error=f"File already exists: {display_path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

    return ToolResult(
        success=True,
        output=f"File created successfully at {display_path}",
        modified_file=str(path),
        old_content="",
    )


def _str_replace(path: Path, old_str: str, new_str: str, display_path: str) -> ToolResult:
    """Replace old_str with new_str in file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {display_path}")

    content = path.read_text()

    # Find the old string - must match exactly
    if old_str not in content:
        # Try to find approximate match for better error message
        approximate = _find_approximate_match(content, old_str)
        error_msg = f"String '{old_str}' not found in {display_path}"
        if approximate:
            error_msg += f"\n\nDid you mean:\n{approximate}"
        return ToolResult(success=False, error=error_msg)

    # Save for undo
    history = EditHistory(
        path=str(path),
        old_content=content,
        new_content=content.replace(old_str, new_str, 1),
        command="str_replace",
    )
    _push_undo(history)

    # Apply the edit
    new_content = content.replace(old_str, new_str, 1)
    path.write_text(new_content)

    output = f"The file {display_path} has been edited. Here's the result of running `cat -n` on a snippet of {display_path}:\n"
    output += _view_file_snippet(path, display_path)

    return ToolResult(success=True, output=output, modified_file=str(path), old_content=old_str)


def _insert_at_line(path: Path, line_num: int, content: str, display_path: str) -> ToolResult:
    """Insert content after line_num."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {display_path}")

    old_content = path.read_text()
    lines = old_content.splitlines(True)  # keepends

    if line_num < 1 or line_num > len(lines):
        return ToolResult(
            success=False,
            error=f"Line {line_num} out of range (file has {len(lines)} lines)",
        )

    # Save for undo
    new_lines = [*lines[:line_num], content + "\n", *lines[line_num:]]
    new_content = "".join(new_lines)

    history = EditHistory(
        path=str(path),
        old_content=old_content,
        new_content=new_content,
        command="insert",
    )
    _push_undo(history)

    path.write_text(new_content)

    output = f"Content inserted after line {line_num} in {display_path}.\n"
    output += _view_file_snippet(path, display_path)

    return ToolResult(success=True, output=output, modified_file=str(path))


def _undo_edit(path: Path, display_path: str) -> ToolResult:
    """Undo the last edit to this file."""
    global _undo_stack

    if not _undo_stack:
        return ToolResult(success=False, error="No edits to undo")

    # Find most recent edit to this file
    for i in range(len(_undo_stack) - 1, -1, -1):
        if _undo_stack[i].path == str(path):
            edit = _undo_stack.pop(i)
            path.write_text(edit.old_content)
            return ToolResult(
                success=True,
                output=f"Undid last edit to {display_path}",
            )

    return ToolResult(success=False, error="No edits to undo for this file")


def _push_undo(history: EditHistory) -> None:
    """Push an edit onto the undo stack."""
    global _undo_stack, _MAX_UNDO
    _undo_stack.append(history)
    if len(_undo_stack) > _MAX_UNDO:
        _undo_stack = _undo_stack[-_MAX_UNDO:]


def _find_approximate_match(content: str, pattern: str) -> str | None:
    """Find approximately matching substring for better error messages."""
    words = pattern.split()
    if len(words) < 2:
        return None

    for i in range(len(content) - len(pattern)):
        substr = content[i : i + len(pattern)]
        similarity = difflib.SequenceMatcher(None, pattern, substr).ratio()
        if similarity > 0.8:
            return substr[:100]
    return None


def _view_file_snippet(path: Path, display_path: str, context_lines: int = 5) -> str:
    """Show first 20 lines of file for confirmation output."""
    if not path.exists():
        return f"File not found: {display_path}"

    content = path.read_text()
    lines = content.splitlines()[:20]

    output_lines = []
    for i, line in enumerate(lines, 1):
        output_lines.append(f"{i:>6}:  {line}")

    if len(lines) >= 20:
        output_lines.append(f"... ({len(lines)} lines shown)")

    return "\n".join(output_lines)


def _make_diff(filename: str, old: str, new: str) -> str:
    """Create a unified diff string."""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=filename,
        tofile=filename,
        lineterm="",
    )
    return "\n".join(diff)


# ---------------------------------------------------------------------------
# bash tool
# ---------------------------------------------------------------------------


def bash(command: str, working_dir: str | None = None, timeout: int = 60) -> ToolResult:
    """Execute a bash command.

    Args:
        command: Shell command to execute
        working_dir: Working directory for the command
        timeout: Timeout in seconds (default 60)

    Returns:
        ToolResult with stdout/stderr
    """
    cwd = working_dir or os.getcwd()

    env = {**os.environ}
    # Ensure we have a usable PATH
    if "PATH" not in env:
        env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

    try:
        # Parse command safely
        parts = shlex.split(command) if isinstance(command, str) else command

        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            timeout=timeout,
        )

        output = result.stdout if result.stdout else ""
        error = result.stderr if result.stderr else ""

        if result.returncode != 0:
            error = f"Command '{command}' exited with code {result.returncode}:\n{error}"
            return ToolResult(success=False, output=output, error=error)

        return ToolResult(success=True, output=output, error=error if error else "")

    except subprocess.TimeoutExpired:
        return ToolResult(success=False, error=f"Command timed out after {timeout}s")
    except Exception as e:
        logger.exception("bash failed: %s", command)
        return ToolResult(success=False, error=str(e))


# ---------------------------------------------------------------------------
# grep tool
# ---------------------------------------------------------------------------


def grep(
    pattern: str,
    working_dir: str | None = None,
    file_pattern: str = "*",
    recursive: bool = True,
    include: str | None = None,
    exclude: str | None = None,
) -> ToolResult:
    """Search for a pattern in files.

    Args:
        pattern: Regex pattern to search for
        working_dir: Base directory to search in
        file_pattern: Glob pattern for files to search (e.g. "*.py")
        recursive: Whether to search recursively
        include: Only search in files matching this pattern
        exclude: Exclude files matching this pattern

    Returns:
        ToolResult with matching lines
    """
    cwd = working_dir or os.getcwd()
    path = Path(cwd)

    if not path.exists():
        return ToolResult(success=False, error=f"Directory not found: {cwd}")

    # Build grep command
    cmd = ["grep", "-n", "-H", "-E"]  # line numbers, filename, extended regex

    if recursive:
        cmd.append("-r")
    else:
        cmd.append("--no-recursive")

    if exclude:
        cmd.extend(["--exclude-dir", exclude])
    if exclude:
        cmd.extend(["--exclude", exclude])

    cmd.append(pattern)

    # Add path
    cmd.append(str(path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )

        if result.returncode == 1:
            # No matches is not an error
            return ToolResult(success=True, output="No matches found")

        if result.returncode != 0:
            return ToolResult(success=False, error=result.stderr)

        return ToolResult(success=True, output=result.stdout)

    except subprocess.TimeoutExpired:
        return ToolResult(success=False, error="grep timed out")
    except Exception as e:
        return ToolResult(success=False, error=str(e))


# ---------------------------------------------------------------------------
# glob tool
# ---------------------------------------------------------------------------


def glob(
    pattern: str,
    working_dir: str | None = None,
    file_pattern: str = "*",
) -> ToolResult:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g. "**/*.py")
        working_dir: Directory to search in
        file_pattern: Filter by file pattern

    Returns:
        ToolResult with matching file paths
    """
    cwd = working_dir or os.getcwd()
    path = Path(cwd)

    if not path.exists():
        return ToolResult(success=False, error=f"Directory not found: {cwd}")

    try:
        matches = list(path.glob(pattern))
        matches = [m for m in matches if m.is_file()]

        if not matches:
            return ToolResult(success=True, output=f"No files matching {pattern}")

        output = "\n".join(str(m.relative_to(path)) for m in matches)
        return ToolResult(success=True, output=output)

    except Exception as e:
        return ToolResult(success=False, error=str(e))


# ---------------------------------------------------------------------------
# submit tool
# ---------------------------------------------------------------------------


def submit(working_dir: str | None = None) -> ToolResult:
    """Generate a git patch for the changes made.

    This tool analyzes the git diff in the working directory and generates
    a patch that can be applied to submit the solution.

    Args:
        working_dir: The SWE-agent working directory

    Returns:
        ToolResult with patch and message
    """
    cwd = working_dir or os.getcwd()

    try:
        # Get git diff
        result = subprocess.run(
            ["git", "diff", "--patch"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        if result.returncode not in (0, 1):
            return ToolResult(success=False, error=f"git diff failed: {result.stderr}")

        diff = result.stdout if result.stdout else ""

        # Check for any changes
        if not diff.strip():
            return ToolResult(success=False, error="No changes found to submit")

        # Generate patch file — already in patch format from diff output
        # (patch variable kept for future extension: write to file, validate, etc.)
        patch = diff  # noqa: F841 — reserved for future patch file write/validation

        return ToolResult(
            success=True,
            output="Submission successful! Changes have been recorded.",
            modified_file="patch.diff",
            old_content=diff,
        )

    except Exception as e:
        logger.exception("submit failed")
        return ToolResult(success=False, error=str(e))


# ---------------------------------------------------------------------------
# Tool definitions for OpenAI function calling format
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "str_replace_editor",
            "description": "View, create, or edit files in the repository. "
                           "Use this for reading files, creating reproduction scripts, "
                           "or fixing bugs by editing source code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["view", "create", "str_replace", "insert", "undo"],
                        "description": "The command to execute",
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to the file (relative to repo root or absolute)",
                    },
                    "file_text": {
                        "type": "string",
                        "description": "File content for create or insert commands",
                    },
                    "old_str": {
                        "type": "string",
                        "description": "Old string to replace (for str_replace)",
                    },
                    "new_str": {
                        "type": "string",
                        "description": "New string to replace with (for str_replace)",
                    },
                    "insert_line": {
                        "type": "integer",
                        "description": "Line number to insert after (for insert)",
                    },
                },
                "required": ["command", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a bash command. Use for running tests, "
                           "checking git status, or running scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to execute"},
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 60)",
                        "default": 60,
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for a regex pattern in files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search for"},
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to search in (e.g. *.py)",
                        "default": "*",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Search recursively",
                        "default": True,
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern filter",
                        "default": "*",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit",
            "description": "Submit the changes as a patch. Call this when the fix is complete.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]