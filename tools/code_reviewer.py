"""tools/code_reviewer.py — AI-powered code review via LLM.

Provides multi-aspect code review: correctness, security, performance, style.
Uses the coding/reviewer agent with specialized system prompts.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Review prompts (adapted from everything-claude-code patterns) ────────────

_REVIEW_PROMPTS = {
    "general": (
        "You are a senior code reviewer. Analyze the code below for:\n"
        "1. **Correctness**: Logic errors, edge cases, error handling gaps\n"
        "2. **Security**: Injection risks, hardcoded secrets, unsafe patterns\n"
        "3. **Performance**: Inefficient algorithms, N+1 queries, memory issues\n"
        "4. **Style**: Naming, readability, Pythonic idioms, missing type hints\n"
        "5. **Architecture**: SOLID violations, tight coupling, missing abstractions\n\n"
        "For each issue found, provide:\n"
        "- Severity: 🔴 critical / 🟠 high / 🟡 medium / 🔵 low\n"
        "- Line number (if applicable)\n"
        "- What's wrong\n"
        "- How to fix it (with code snippet if helpful)\n\n"
        "End with a brief overall assessment and a score out of 10.\n"
        "Format your response in HTML (use <b>, <code>, <i> tags only — no markdown)."
    ),
    "security": (
        "You are a security auditor. Review the code below for vulnerabilities:\n"
        "1. OWASP Top 10 issues (injection, XSS, auth bypass, etc.)\n"
        "2. Hardcoded secrets (API keys, passwords, tokens)\n"
        "3. Unsafe deserialization or eval/exec usage\n"
        "4. Missing input validation or sanitization\n"
        "5. Insecure cryptography or hashing\n"
        "6. Path traversal or file access issues\n"
        "7. Command injection via subprocess/os.system\n"
        "8. Information disclosure in error messages\n\n"
        "For each finding:\n"
        "- Severity: 🔴 critical / 🟠 high / 🟡 medium / 🔵 info\n"
        "- CWE ID if applicable\n"
        "- Exploitation scenario\n"
        "- Recommended fix\n\n"
        "Format your response in HTML (use <b>, <code>, <i> tags only — no markdown)."
    ),
    "python": (
        "You are a Python expert reviewer. Check for:\n"
        "1. PEP 8 compliance and naming conventions\n"
        "2. Type annotation completeness\n"
        "3. Async/await correctness (missing await, blocking calls in async)\n"
        "4. Anti-patterns: mutable defaults, bare except, global state\n"
        "5. Pythonic improvements (comprehensions, context managers, f-strings)\n"
        "6. Error handling quality (specific exceptions, proper cleanup)\n"
        "7. Test coverage gaps (what tests are missing?)\n\n"
        "For each issue, provide severity and a concrete fix.\n"
        "Format your response in HTML (use <b>, <code>, <i> tags only — no markdown)."
    ),
}


async def review_code(
    code: str,
    language: str = "python",
    review_type: str = "general",
) -> str:
    """Review inline code using an LLM agent.

    Args:
        code: The source code to review.
        language: Programming language (for context).
        review_type: One of 'general', 'security', 'python'.

    Returns:
        HTML-formatted review results.
    """
    from llm_client import chat

    prompt_key = review_type if review_type in _REVIEW_PROMPTS else "general"
    system_hint = _REVIEW_PROMPTS[prompt_key]

    task = (
        f"{system_hint}\n\n"
        f"## Code to Review ({language})\n"
        f"```{language}\n{code}\n```"
    )

    try:
        result, model = await chat(task, agent_key="coding", user_id="0")
        return (
            f"<b>Code Review</b> ({review_type}) via <code>{html.escape(model)}</code>\n\n"
            f"{result}"
        )
    except Exception as e:
        return f"<b>Review failed:</b> <code>{html.escape(str(e)[:300])}</code>"


async def review_file(
    file_path: str,
    review_type: str = "general",
) -> str:
    """Review a file on disk.

    Args:
        file_path: Path to the file to review.
        review_type: One of 'general', 'security', 'python'.

    Returns:
        HTML-formatted review results.
    """
    p = Path(file_path)
    if not p.exists():
        return f"<b>File not found:</b> <code>{html.escape(file_path)}</code>"
    if not p.is_file():
        return f"<b>Not a file:</b> <code>{html.escape(file_path)}</code>"

    # Safety: limit file size to ~50KB
    size = p.stat().st_size
    if size > 50_000:
        return (
            f"<b>File too large for review:</b> {size:,} bytes. "
            "Max 50KB. Consider reviewing specific sections."
        )

    code = p.read_text(errors="replace")

    # Detect language from extension
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".sh": "bash", ".yaml": "yaml", ".yml": "yaml",
        ".json": "json", ".sql": "sql", ".html": "html",
        ".css": "css", ".rs": "rust", ".go": "go",
    }
    language = ext_map.get(p.suffix.lower(), "text")

    # Auto-select python review for .py files if general
    if language == "python" and review_type == "general":
        review_type = "python"

    header = (
        f"<b>Reviewing:</b> <code>{html.escape(p.name)}</code> "
        f"({len(code.splitlines())} lines, {language})\n\n"
    )

    result = await review_code(code, language=language, review_type=review_type)
    return header + result
