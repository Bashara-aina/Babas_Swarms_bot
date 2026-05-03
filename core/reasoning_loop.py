"""Pre-Response Reasoning Loop — Legion thinks before answering.

This module implements the reasoning loop described in DEEP_AUDIT_2026-04-12.md
Priority 1: For messages >20 words OR confidence <0.7, Legion decomposes the question,
checks if external sources or memory are needed, gathers them, and produces a
structured reasoning context before the LLM call.

For simple questions (short, high confidence): returns None (skip reasoning).
All functions are async. All calls are wrapped in try/except. Logger used throughout.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SubQuestion:
    """A decomposed sub-question from the main user message."""

    text: str
    requires_external: bool = False  # needs web search, API call, etc.
    requires_memory: bool = False  # needs memory retrieval
    complexity: str = "simple"  # simple | moderate | complex


@dataclass
class ReasoningContext:
    """The output of the reasoning loop — structured input for the LLM."""

    sub_questions: list[SubQuestion] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: float = 1.0
    skip_reasoning: bool = False  # True means simple question, reasoning not needed

    def has_sources(self) -> bool:
        return len(self.sources) > 0

    def has_sub_questions(self) -> bool:
        return len(self.sub_questions) > 0


def _is_simple_question(message: str, confidence: float) -> bool:
    """Decide if a message is simple enough to skip the reasoning loop.

    Simple = less than 20 words AND confidence > 0.8
    """
    word_count = len(message.split()) if message else 0
    return word_count < 20 and confidence > 0.8


async def decompose_question(message: str) -> list[SubQuestion]:
    """Decompose a complex message into sub-questions.

    Uses keyword patterns + lightweight heuristics to identify:
    - Questions requiring external knowledge (search, API)
    - Questions that need memory retrieval (personal, past conversations)
    - Multi-part questions that should be broken down

    Args:
        message: The raw user message

    Returns:
        List of SubQuestion objects
    """
    import re

    sub_questions: list[SubQuestion] = []
    word_count = len(message.split())

    # Pattern: explicit multi-part (first... then..., 1)... 2)..., etc.)
    multi_patterns = [
        r"\d+\)\s*",
        r"\d+\.\s*",
        r"first(?:ly)?\s*,?\s*",
        r"then\s+,?\s*",
        r"also\s+,?\s*",
        r"plus\s+,?\s*",
        r"and\s+(?:also\s+)?",
    ]
    has_explicit_parts = any(re.search(p, message, re.IGNORECASE) for p in multi_patterns)

    if has_explicit_parts:
        # Split by known delimiters
        parts = re.split(r"(?:\d+[\.\)]\s*|first(?:ly)?\s*,?\s*|then\s+,?\s*)", message, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip().strip('"')
            if len(part) > 10:
                sq = SubQuestion(text=part)
                sq.requires_external = _needs_external_knowledge(part)
                sq.requires_memory = _needs_memory(part)
                sq.complexity = "moderate" if len(part.split()) > 10 else "simple"
                sub_questions.append(sq)
        if sub_questions:
            logger.debug("Decomposed into %d explicit sub-questions", len(sub_questions))
            return sub_questions

    # Pattern: question marks indicate direct questions
    question_count = message.count("?")
    if question_count >= 2:
        # Multiple questions
        sentences = re.split(r"[.!?]+", message)
        for sent in sentences:
            sent = sent.strip()
            if "?" in sent and len(sent) > 10:
                sq = SubQuestion(text=sent)
                sq.requires_external = _needs_external_knowledge(sent)
                sq.requires_memory = _needs_memory(sent)
                sq.complexity = "moderate"
                sub_questions.append(sq)
        if sub_questions:
            logger.debug("Decomposed %d-question message into %d sub-questions", question_count, len(sub_questions))
            return sub_questions

    # Single complex question
    if word_count > 15 or any(
        kw in message.lower() for kw in ["why", "how", "explain", "compare", "analyze", "design", "implement"]
    ):
        sq = SubQuestion(text=message)
        sq.requires_external = _needs_external_knowledge(message)
        sq.requires_memory = _needs_memory(message)
        sq.complexity = "complex" if word_count > 25 else "moderate"
        sub_questions.append(sq)
        logger.debug("Single complex question, complexity=%s", sq.complexity)
        return sub_questions

    # Default: simple single question
    sub_questions.append(SubQuestion(text=message))
    return sub_questions


def _needs_external_knowledge(text: str) -> bool:
    """Heuristic: does this question need external knowledge (search, API)?"""
    external_keywords = [
        "latest",
        "recent",
        "new",
        "current",
        "2024",
        "2025",
        "2026",
        "search",
        "find",
        "look up",
        "who is",
        "what is",
        "when did",
        "price",
        "stock",
        "weather",
        "news",
        "arxiv",
        "github",
        "download",
        "install",
        "update",
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in external_keywords)


def _needs_memory(text: str) -> bool:
    """Heuristic: does this question need personal memory retrieval?"""
    memory_keywords = [
        "my ",
        "i told you",
        "remember",
        "previously",
        "earlier",
        "last week",
        "yesterday",
        "before",
        "when i ",
        "my project",
        "rumahlabuh",
        "bashara",
        "thèse",
        "thesis",
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in memory_keywords)


async def gather_sources(
    sub_questions: list[SubQuestion],
    *,
    search: bool = False,
    memory: bool = False,
) -> list[str]:
    """Gather external sources for the reasoning context.

    Args:
        sub_questions: The decomposed questions needing sources
        search: Whether any sub-question requires external search
        memory: Whether any sub-question requires memory retrieval

    Returns:
        List of source strings (web results, memory snippets, etc.)
    """
    sources: list[str] = []

    # Memory retrieval if needed
    if memory:
        try:
            memory_sources = await _gather_memory_sources(sub_questions)
            sources.extend(memory_sources)
        except Exception as e:
            logger.warning("Memory gathering failed (non-fatal): %s", e)

    # Web search if needed
    if search:
        try:
            search_sources = await _gather_search_sources(sub_questions)
            sources.extend(search_sources)
        except Exception as e:
            logger.warning("Search gathering failed (non-fatal): %s", e)

    return sources


async def _gather_memory_sources(sub_questions: list[SubQuestion]) -> list[str]:
    """Gather relevant memories for the sub-questions."""
    results: list[str] = []
    try:
        from core.memory.unified_context import build_unified_memory_context

        for sq in sub_questions:
            if sq.requires_memory:
                try:
                    mem_ctx = await build_unified_memory_context("bashara", sq.text)
                    if mem_ctx:
                        results.append(f"[Memory for: {sq.text[:50]}]\n{mem_ctx}")
                except Exception as e:
                    logger.debug("Memory retrieval for sub-question failed: %s", e)
    except Exception as e:
        logger.warning("Failed to import memory systems: %s", e)
    return results


async def _gather_search_sources(sub_questions: list[SubQuestion]) -> list[str]:
    """Gather web search results for the sub-questions."""
    results: list[str] = []
    try:
        from tools.web_search import search_web

        for sq in sub_questions:
            if sq.requires_external:
                try:
                    search_results = await search_web(sq.text, max_results=3)
                    if search_results:
                        results.append(f"[Search for: {sq.text[:50]}]\n{search_results}")
                except Exception as e:
                    logger.debug("Search for sub-question failed: %s", e)
    except ImportError:
        logger.debug("Web search tool not available")
    except Exception as e:
        logger.warning("Search gathering errored: %s", e)
    return results


async def reason_before_responding(
    message: str,
    intent: str,
    confidence: float,
) -> ReasoningContext | None:
    """Main entry point — the pre-response reasoning loop.

    For messages >20 words OR confidence <0.7:
      1. Decompose question into sub-questions
      2. Check if search/memory needed
      3. Gather sources
      4. Return ReasoningContext with structured input for LLM

    For simple questions (short, high confidence): return None (skip reasoning)

    Args:
        message: The raw user message
        intent: The classified intent string
        confidence: Classification confidence (0.0-1.0)

    Returns:
        ReasoningContext if reasoning should run, None if message is simple
    """
    logger.debug("reason_before_responding: msg_len=%d, intent=%s, confidence=%.2f", len(message), intent, confidence)

    # Quick exit for simple questions
    if _is_simple_question(message, confidence):
        logger.debug("Simple question detected — skipping reasoning loop")
        return None

    try:
        # Step 1: Decompose
        sub_questions = await decompose_question(message)
        if not sub_questions:
            logger.warning("decompose_question returned empty — returning None")
            return None

        # Step 2: Check sources needed
        needs_search = any(sq.requires_external for sq in sub_questions)
        needs_memory = any(sq.requires_memory for sq in sub_questions)

        logger.debug(
            "Sub-questions: %d, needs_search=%s, needs_memory=%s", len(sub_questions), needs_search, needs_memory
        )

        # Step 3: Gather sources (only if needed)
        sources: list[str] = []
        if needs_search or needs_memory:
            sources = await gather_sources(sub_questions, search=needs_search, memory=needs_memory)
            logger.debug("Gathered %d sources", len(sources))

        # Step 4: Build reasoning context
        ctx = ReasoningContext(
            sub_questions=sub_questions,
            sources=sources,
            confidence=confidence,
            skip_reasoning=False,
        )

        logger.info(
            "Reasoning loop complete: %d sub-questions, %d sources, confidence=%.2f",
            len(sub_questions),
            len(sources),
            confidence,
        )
        return ctx

    except Exception as e:
        logger.error("reason_before_responding failed (fallback to None): %s", e)
        return None


def build_reasoning_prompt(context: ReasoningContext) -> str:
    """Build a structured reasoning prompt from the ReasoningContext.

    This formats the reasoning context into a prompt block that can be
    injected into the LLM's system message stream before the user message.

    Args:
        context: The ReasoningContext from reason_before_responding

    Returns:
        A formatted string to add as a system message, or empty string if skipped
    """
    if context.skip_reasoning:
        return ""

    parts = ["[PRE-RESPONSE REASONING]\n"]

    if context.has_sub_questions():
        parts.append("Before answering, I decomposed this into sub-questions:")
        for i, sq in enumerate(context.sub_questions, 1):
            flags = []
            if sq.requires_external:
                flags.append("needs external search")
            if sq.requires_memory:
                flags.append("needs memory")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            parts.append(f"  {i}. {sq.text}{flag_str}")
        parts.append("")

    if context.has_sources():
        parts.append("I gathered the following sources:")
        for src in context.sources:
            # Truncate very long sources
            src_trimmed = src[:500] + "..." if len(src) > 500 else src
            parts.append(f"  - {src_trimmed}")
        parts.append("")

    parts.append("Use the above reasoning and sources to inform your response.")

    return "\n".join(parts)


# ── Convenience function for llm_client wiring ─────────────────────────────────


async def run_reasoning_loop_if_needed(
    message: str,
    intent: str,
    confidence: float,
) -> str | None:
    """Run the reasoning loop and return a formatted prompt block.

    Returns None if reasoning is skipped (simple question).
    Returns the reasoning prompt string if reasoning ran.

    This is the preferred wiring point for llm_client/__init__.py.
    """
    ctx = await reason_before_responding(message, intent, confidence)
    if ctx is None:
        return None
    return build_reasoning_prompt(ctx)
