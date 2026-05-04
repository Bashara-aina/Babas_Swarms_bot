"""Codebase understanding tool — like Copilot/Cursor for any repo on the machine.

Given a natural language query about a codebase, this tool:
1. Locates the relevant project directory
2. Searches for files/functions/classes matching the query
3. Reads the relevant sections
4. Returns a structured summary with file paths and line numbers

Usage via autonomous router (codebase_understanding skill) or directly:
    result = await explain_codebase("how does the memory system work?", project_dir="~/Babas_Swarms_bot")
    result = await find_in_code("where is detect_agent defined?", project_dir="~/Babas_Swarms_bot")
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default project roots to search if no dir specified
_DEFAULT_SEARCH_ROOTS = [
    "~/Babas_Swarms_bot",
    "~/swarm-bot",
    "~/WorkerNet",
]

# File extensions to search
_CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml",
    ".json", ".md", ".toml", ".sh", ".env.example",
}

# Always skip these
_SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".mypy_cache", "dist", "build", ".next", ".cache",
    "htmlcov", ".pytest_cache",
}


def _resolve_project_dir(project_dir: str | None = None) -> Path | None:
    """Find the project directory to search."""
    if project_dir:
        p = Path(os.path.expanduser(project_dir)).resolve()
        if p.is_dir():
            return p
        return None

    # Auto-detect from default roots
    for root in _DEFAULT_SEARCH_ROOTS:
        p = Path(os.path.expanduser(root)).resolve()
        if p.is_dir():
            return p
    return None


def _find_files(root: Path, extensions: set[str] = _CODE_EXTENSIONS) -> list[Path]:
    """Walk directory tree and collect code files (skipping ignored dirs)."""
    files: list[Path] = []
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune skip dirs in-place
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for fname in filenames:
                fp = Path(dirpath) / fname
                if fp.suffix in extensions:
                    files.append(fp)
    except Exception as _e:
        logger.warning("codebase_reader: file walk failed: %s", _e)
    return files


def _grep_in_file(
    filepath: Path,
    pattern: str,
    context_lines: int = 5,
    max_matches: int = 3,
) -> list[dict]:
    """Search for pattern in file, return matches with context."""
    results = []
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet = "\n".join(lines[start:end])
                results.append({
                    "file": str(filepath),
                    "line": i + 1,
                    "match": line.strip(),
                    "context": snippet,
                })
                if len(results) >= max_matches:
                    break
    except Exception:
        pass
    return results


def _extract_definitions(filepath: Path, symbol: str) -> list[dict]:
    """Extract function/class/method definitions matching symbol name."""
    results = []
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        patterns = [
            rf"^\s*(def|async def)\s+{re.escape(symbol)}\s*[:(]",
            rf"^\s*class\s+{re.escape(symbol)}\s*[:(]",
            rf"^\s*{re.escape(symbol)}\s*=",  # assignment/constant
        ]
        for i, line in enumerate(lines):
            for pat in patterns:
                if re.match(pat, line, re.IGNORECASE):
                    # Grab the definition + body start
                    end = min(len(lines), i + 20)
                    snippet = "\n".join(lines[i:end])
                    results.append({
                        "file": str(filepath),
                        "line": i + 1,
                        "definition": line.strip(),
                        "snippet": snippet,
                    })
    except Exception:
        pass
    return results


def _build_structure_map(root: Path, max_depth: int = 3) -> str:
    """Build a compact directory/file structure map."""
    lines: list[str] = [f"{root.name}/"]
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
            depth = len(Path(dirpath).relative_to(root).parts)
            if depth > max_depth:
                dirnames.clear()
                continue
            indent = "  " * depth
            # Only show code files
            code_files = sorted(f for f in filenames if Path(f).suffix in _CODE_EXTENSIONS)
            for fname in code_files[:10]:  # cap per dir
                lines.append(f"{indent}├── {fname}")
            if len(code_files) > 10:
                lines.append(f"{indent}└── ... ({len(code_files) - 10} more)")
    except Exception as _e:
        logger.warning("codebase_reader: structure map failed: %s", _e)
    return "\n".join(lines)


async def explain_codebase(
    query: str,
    project_dir: str | None = None,
    max_files_to_read: int = 5,
    max_chars_per_file: int = 2000,
) -> str:
    """Explain how something works in the codebase.

    Args:
        query: Natural language question, e.g. "how does the memory system work?"
        project_dir: Path to project root. Auto-detects if None.
        max_files_to_read: Max files to include in response.
        max_chars_per_file: Max chars to extract per file.

    Returns:
        Structured explanation with file paths and line numbers.
    """
    root = _resolve_project_dir(project_dir)
    if root is None:
        return "Couldn't find project directory. Specify a path with project_dir."

    # Extract key terms from the query for searching
    stopwords = {
        "how", "does", "the", "what", "is", "where", "find", "which",
        "explain", "tell", "me", "about", "work", "works", "do", "a",
        "an", "in", "this", "project", "codebase", "code", "file",
        "bagaimana", "cara", "kerja", "jelaskan", "dimana", "ada", "di",
    }
    terms = [
        w for w in re.findall(r'\b\w{3,}\b', query.lower())
        if w not in stopwords
    ]

    if not terms:
        # Fall back to structure map if no searchable terms
        structure = await asyncio.to_thread(_build_structure_map, root)
        return f"Project structure of {root.name}/:\n```\n{structure}\n```"

    # Search files for relevant content
    all_files = await asyncio.to_thread(_find_files, root)
    results: list[dict] = []
    file_scores: dict[str, int] = {}

    for term in terms[:5]:  # Search top 5 terms
        pattern = re.escape(term)
        for filepath in all_files:
            matches = await asyncio.to_thread(_grep_in_file, filepath, pattern, context_lines=3)
            if matches:
                fp_str = str(filepath)
                file_scores[fp_str] = file_scores.get(fp_str, 0) + len(matches)
                results.extend(matches)

    if not results:
        return (
            f"Searched {len(all_files)} files in {root.name}/ for terms: {', '.join(terms)}\n"
            f"No direct matches found. Try a more specific term or file name."
        )

    # Rank files by hit count, pick top N
    top_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)[:max_files_to_read]

    sections: list[str] = [
        f"**Searching {root.name}/ for: '{query}'**\n"
        f"Found matches in {len(file_scores)} file(s). Showing top {len(top_files)}:\n"
    ]

    for filepath_str, hit_count in top_files:
        filepath = Path(filepath_str)
        rel_path = filepath.relative_to(root)
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
            # Show the most relevant portion
            file_results = [r for r in results if r["file"] == filepath_str]
            if file_results:
                # Find the first match line and grab surrounding context
                first_line = file_results[0]["line"]
                lines = content.splitlines()
                start = max(0, first_line - 5)
                end = min(len(lines), first_line + 40)
                excerpt = "\n".join(lines[start:end])
                if len(excerpt) > max_chars_per_file:
                    excerpt = excerpt[:max_chars_per_file] + "\n... (truncated)"
                sections.append(
                    f"**{rel_path}** (line {first_line}, {hit_count} match{'es' if hit_count > 1 else ''}):\n"
                    f"```python\n{excerpt}\n```"
                )
        except Exception:
            sections.append(f"**{rel_path}** — {hit_count} matches (could not read file)")

    return "\n\n".join(sections)


async def find_in_code(
    query: str,
    project_dir: str | None = None,
) -> str:
    """Find where a symbol (function, class, variable) is defined in the codebase.

    Args:
        query: e.g. "where is detect_agent defined?" or "find detect_agent"
        project_dir: Project root path.

    Returns:
        List of locations with file path and line number.
    """
    root = _resolve_project_dir(project_dir)
    if root is None:
        return "Couldn't find project directory."

    # Extract the symbol name from the query
    symbol_patterns = [
        r"where is (\w+)",
        r"find (\w+)",
        r"locate (\w+)",
        r"(\w+) is defined",
        r"definition of (\w+)",
    ]
    symbol = None
    for pat in symbol_patterns:
        m = re.search(pat, query, re.IGNORECASE)
        if m:
            symbol = m.group(1)
            break

    if not symbol:
        # Fall back to explain_codebase
        return await explain_codebase(query, project_dir=project_dir)

    all_files = await asyncio.to_thread(_find_files, root, {".py", ".ts", ".js"})
    all_defs: list[dict] = []

    for filepath in all_files:
        defs = await asyncio.to_thread(_extract_definitions, filepath, symbol)
        all_defs.extend(defs)

    if not all_defs:
        # Fall back to grep
        return await explain_codebase(query, project_dir=project_dir)

    sections: list[str] = [f"**Found `{symbol}` defined in {len(all_defs)} location(s):**\n"]
    for defn in all_defs[:6]:
        rel = Path(defn["file"]).relative_to(root)
        snippet = defn["snippet"]
        if len(snippet) > 600:
            snippet = snippet[:600] + "\n..."
        sections.append(
            f"**{rel}:{defn['line']}**\n"
            f"```python\n{snippet}\n```"
        )

    return "\n\n".join(sections)


async def get_project_overview(project_dir: str | None = None) -> str:
    """Return a high-level overview of the project structure and key files."""
    root = _resolve_project_dir(project_dir)
    if root is None:
        return "Couldn't find project directory."

    structure = await asyncio.to_thread(_build_structure_map, root, max_depth=2)
    all_files = await asyncio.to_thread(_find_files, root)

    py_count = sum(1 for f in all_files if f.suffix == ".py")
    ts_count = sum(1 for f in all_files if f.suffix in {".ts", ".tsx"})

    summary_lines = [
        f"**{root.name}/** — project overview",
        f"Python files: {py_count} | TypeScript files: {ts_count} | Total: {len(all_files)}",
        "",
        "**Structure:**",
        f"```\n{structure}\n```",
    ]

    # Try to read README if present
    readme = root / "README.md"
    if readme.exists():
        try:
            readme_text = readme.read_text(encoding="utf-8", errors="replace")
            if len(readme_text) > 1000:
                readme_text = readme_text[:1000] + "\n..."
            summary_lines.append(f"**README:**\n{readme_text}")
        except Exception:
            pass

    return "\n".join(summary_lines)
