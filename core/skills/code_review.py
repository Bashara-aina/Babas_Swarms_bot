"""core/skills/code_review.py — Real code review skill using LLM.

FIX: Code review wasn't registered as a skill. This module provides a working
implementation that actually reviews code using the coding LLM and returns
structured feedback.
"""

from __future__ import annotations

import logging

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def execute(code: str, language: str = "auto") -> str:
    """Review the provided code using the coding LLM.

    Args:
        code: The source code to review.
        language: Programming language (auto-detected if not specified).

    Returns:
        Structured code review with BUGS, PERFORMANCE, SECURITY,
        IMPROVEMENTS, and VERDICT sections.
    """
    if not code or len(code.strip()) < 10:
        return "Please paste the code you want me to review."

    # Detect language if auto
    if language == "auto":
        language = _detect_language(code)

    review_prompt = f"""Review this {language} code. Be specific and actionable.
Format your review as:
1. BUGS: Any actual bugs or errors (not style preferences)
2. PERFORMANCE: Any O(n²) or unnecessary operations, memory issues
3. SECURITY: Any injection, auth, or exposure risks
4. IMPROVEMENTS: Top 2-3 concrete improvements with code suggestions
5. VERDICT: Ship it / Needs work / Rewrite (pick one)

Code:
```{language}
{code}
```"""

    try:
        from llm_client import call_llm

        result = await call_llm(
            messages=[{"role": "user", "content": review_prompt}],
            model="coding_model",
        )
        return result
    except Exception as e:
        logger.error("Code review failed: %e", e)
        return f"❌ Code review failed: {e}"


def _detect_language(code: str) -> str:
    """Simple language detection based on code patterns."""
    code_lower = code.lower().strip()

    # Check for common patterns
    if "import asyncio" in code_lower or "async def" in code_lower:
        return "python"
    if "def " in code and ":" in code:
        return "python"
    if "class " in code_lower and ":" in code:
        return "python"
    if "function" in code_lower or "const " in code_lower or "let " in code_lower:
        return "javascript"
    if "fn " in code_lower and "->" in code:
        return "rust"
    if "func " in code_lower and "(" in code:
        return "go"
    if "public class" in code or "private void" in code:
        return "java"
    if "#include" in code_lower:
        return "c"
    if "package " in code and "func" in code:
        return "go"
    if "SELECT" in code.upper() and "FROM" in code.upper():
        return "sql"

    return "text"


# Skill registration
def _register_code_review_skill() -> None:
    """Register the code review skill."""
    SKILL_REGISTRY.register(
        Skill(
            name="code_review",
            description="Review code for bugs, performance issues, security risks, and improvements",
            trigger_keywords=[
                "review code",
                "review this",
                "cek bug",
                "review kode",
                "code review",
                "audit code",
                "scan code",
                "inspect code",
            ],
            handler=execute,
            required_env_keys=[],
            category="general",
        )
    )


_register_code_review_skill()
