"""dev_tools.py — Development tools for Legion.

Testing, linting, code search, and database operations.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def _shell(cmd: str, timeout: int = 60) -> str:
    from computer_agent import run_shell
    return await run_shell(cmd, timeout=timeout)


async def run_tests(
    path: str = ".",
    framework: str = "pytest",
    args: str = "",
) -> str:
    """Run tests using pytest or unittest."""
    expanded = str(Path(path).expanduser())
    if framework == "pytest":
        result = await _shell(f"cd '{expanded}' && python -m pytest {args} -v 2>&1", timeout=120)
    elif framework == "unittest":
        result = await _shell(f"cd '{expanded}' && python -m unittest discover {args} -v 2>&1", timeout=120)
    else:
        result = await _shell(f"cd '{expanded}' && {framework} {args} 2>&1", timeout=120)

    if len(result) > 6000:
        result = result[:6000] + "\n\n[...truncated]"
    return result


async def lint_code(path: str, tool: str = "ruff") -> str:
    """Lint code with ruff, flake8, or pylint."""
    expanded = str(Path(path).expanduser())
    if tool == "ruff":
        return await _shell(f"ruff check '{expanded}' 2>&1")
    elif tool == "flake8":
        return await _shell(f"flake8 '{expanded}' 2>&1")
    elif tool == "pylint":
        return await _shell(f"pylint '{expanded}' 2>&1")
    return f"unknown linter: {tool}"


async def format_code(path: str, tool: str = "ruff") -> str:
    """Format code with ruff format, black, or autopep8."""
    expanded = str(Path(path).expanduser())
    if tool == "ruff":
        return await _shell(f"ruff format '{expanded}' 2>&1")
    elif tool == "black":
        return await _shell(f"black '{expanded}' 2>&1")
    return f"unknown formatter: {tool}"


async def find_in_codebase(
    pattern: str,
    path: str = ".",
    file_type: str = "*.py",
    max_results: int = 30,
) -> str:
    """Search for a pattern in code files (grep-like)."""
    expanded = str(Path(path).expanduser())
    result = await _shell(
        f"grep -rn --include='{file_type}' '{pattern}' '{expanded}' 2>/dev/null | head -n {max_results}",
        timeout=15,
    )
    if not result.strip() or "no output" in result.lower():
        return f"No matches for '{pattern}' in {file_type} files"
    return result


async def analyze_codebase(path: str = ".") -> str:
    """Quick codebase analysis: structure, file counts, line counts."""
    expanded = str(Path(path).expanduser())
    structure = await _shell(f"find '{expanded}' -name '*.py' -type f | head -30", timeout=10)
    line_count = await _shell(
        f"find '{expanded}' -name '*.py' -type f -exec wc -l {{}} + 2>/dev/null | tail -1",
        timeout=10,
    )
    file_count = await _shell(f"find '{expanded}' -name '*.py' -type f | wc -l", timeout=5)

    return (
        f"Codebase: {expanded}\n"
        f"Python files: {file_count.strip()}\n"
        f"Total lines: {line_count.strip()}\n\n"
        f"Files:\n{structure}"
    )


async def db_query(
    query: str,
    db_path: str = "",
    db_type: str = "sqlite",
) -> str:
    """Execute a SQL query.

    For SQLite: provide db_path.
    For PostgreSQL: uses psql via shell.
    """
    if db_type == "sqlite":
        if not db_path:
            return "db_path required for SQLite"
        expanded = str(Path(db_path).expanduser())
        return await _shell(f"sqlite3 '{expanded}' '{query}' 2>&1", timeout=15)
    elif db_type == "postgres":
        return await _shell(f"psql -c '{query}' 2>&1", timeout=15)
    elif db_type == "mysql":
        return await _shell(f"mysql -e '{query}' 2>&1", timeout=15)
    return f"unknown db_type: {db_type}"
