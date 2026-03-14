"""
tools/citation.py — Citation quality layer for LegionSwarm.

Handles:
  - Inline citation injection into LLM responses
  - Source verification hints (arXiv, docs, GitHub)
  - Citation formatting for Telegram HTML
  - A post-processor that enriches bare claims with [Source: ...] tags

Design:
  - Works as a response post-processor: takes raw LLM output,
    detects uncited factual claims, adds [Source: ?] markers.
  - Also provides a citation prompt addon that can be appended to
    any system prompt to instruct the LLM to cite inline.
"""

from __future__ import annotations
import re
from typing import Optional

# ── Citation prompt addon ─────────────────────────────────────────────────────
# Append this to system prompts for research/debug/coding agents
CITATION_ADDON = """
CITATION INSTRUCTIONS:
For every factual claim, recommendation, or non-obvious statement:
  1. Add an inline marker: [Source: <name>]
     Examples: [Source: PyTorch 2.3 docs], [Source: arXiv:1705.07115],
               [Source: MDN Web Docs], [Source: litellm README],
               [Source: Stack Overflow #12345678], [Source: PEP 484]
  2. At the END of your response, add a numbered sources list:
     📚 <b>Sources:</b>
     [1] PyTorch 2.3 docs — https://pytorch.org/docs/stable/
     [2] arXiv:1705.07115 — Multi-Task Learning Using Uncertainty (Kendall 2018)
  3. If you cannot verify a source, write: [Source: unverified — please check]
  4. Mark opinions explicitly: (my take)
  5. Mark code patterns: [Pattern: <library> official example] or [Pattern: common practice]
"""

# ── Known source map (expand as needed) ──────────────────────────────────────
# Maps common phrases/libs to their canonical docs URL
KNOWN_SOURCES: dict[str, str] = {
    "pytorch":         "https://pytorch.org/docs/stable/",
    "litellm":         "https://docs.litellm.ai/",
    "aiogram":         "https://docs.aiogram.dev/en/latest/",
    "supabase":        "https://supabase.com/docs",
    "nextjs":          "https://nextjs.org/docs",
    "fastapi":         "https://fastapi.tiangolo.com/",
    "playwright":      "https://playwright.dev/python/docs/intro",
    "aiosqlite":       "https://aiosqlite.omnilib.dev/en/stable/",
    "groq":            "https://console.groq.com/docs/openai",
    "cerebras":        "https://inference-docs.cerebras.ai/introduction",
    "ollama":          "https://ollama.com/library",
    "xdotool":         "https://www.semicomplete.com/projects/xdotool/",
    "scrot":           "https://github.com/resurrecting-open-source-projects/scrot",
    "pep 484":         "https://peps.python.org/pep-0484/",
    "pep 8":           "https://peps.python.org/pep-0008/",
    "ikea asm":        "https://arxiv.org/abs/2007.09812",
    "kendall 2018":    "https://arxiv.org/abs/1705.07115",
    "focal loss":      "https://arxiv.org/abs/1708.02002",
    "wing loss":       "https://arxiv.org/abs/1711.06753",
    "film":            "https://arxiv.org/abs/1709.07871",
    "class-balanced":  "https://arxiv.org/abs/1901.05555",
}


def enrich_source_urls(text: str) -> str:
    """
    Post-process LLM output: find [Source: X] markers and append URL
    if X matches a known source in KNOWN_SOURCES.
    e.g. [Source: pytorch] → [Source: pytorch — https://pytorch.org/docs/stable/]
    """
    def replace_source(match: re.Match) -> str:
        source_name = match.group(1).strip()
        lower = source_name.lower()
        for key, url in KNOWN_SOURCES.items():
            if key in lower:
                return f"[Source: {source_name} — {url}]"
        return match.group(0)  # no change if unknown

    return re.sub(r"\[Source:\s*([^\]]+)\]", replace_source, text)


def format_sources_section(sources_raw: list[str]) -> str:
    """
    Format a list of raw source strings into a clean Telegram HTML block.
    Input: ["PyTorch docs https://...", "arXiv:1705.07115"]
    Output: HTML formatted 📚 Sources section
    """
    if not sources_raw:
        return ""
    lines = ["\n📚 <b>Sources:</b>"]
    for i, src in enumerate(sources_raw, 1):
        # If it contains a URL, make it a clickable link
        url_match = re.search(r"(https?://\S+)", src)
        if url_match:
            url = url_match.group(1)
            name = src[:url_match.start()].strip().rstrip("—-").strip()
            if name:
                lines.append(f"  [{i}] <a href='{url}'>{name}</a>")
            else:
                lines.append(f"  [{i}] <a href='{url}'>{url}</a>")
        else:
            lines.append(f"  [{i}] {src}")
    return "\n".join(lines)


def extract_and_format_sources(text: str) -> tuple[str, str]:
    """
    If the LLM output contains a '📚 Sources:' or 'Sources:' section,
    extract it and reformat it cleanly.
    Returns (main_text_without_sources, formatted_sources_html)
    """
    # Match Sources section at end of response
    pattern = r"(📚\s*(?:<b>)?Sources:(?:</b>)?)(.*?)$"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return text, ""

    main_text = text[:match.start()].rstrip()
    sources_block = match.group(2).strip()

    # Parse numbered list
    sources = re.findall(r"\[?\d+\]?[.)\s]+(.+?)(?=\n\[?\d|$)", sources_block, re.DOTALL)
    if not sources:
        # fallback: split by newlines
        sources = [s.strip() for s in sources_block.split("\n") if s.strip()]

    formatted = format_sources_section(sources)
    return main_text, formatted


def add_citation_notice(text: str) -> str:
    """
    If the response has no citations at all (no [Source: ...] markers),
    append a gentle disclaimer.
    """
    if "[Source:" in text or "📚" in text:
        return text
    if len(text) > 500:  # only for long factual-ish responses
        return text + "\n\n<i>⚠️ No sources cited — verify important claims independently.</i>"
    return text


def post_process_response(text: str) -> str:
    """
    Full pipeline:
    1. Enrich [Source: X] with known URLs
    2. Extract and reformat sources section
    3. Recombine cleanly
    """
    text = enrich_source_urls(text)
    main_text, sources_html = extract_and_format_sources(text)
    if sources_html:
        return main_text + "\n" + sources_html
    return add_citation_notice(text)
