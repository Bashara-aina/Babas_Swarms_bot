"""Quality guard utilities for grounded, verifiable bot outputs.

Provides:
- research intent detection
- URL/source extraction
- evidence envelope formatting
- verifier + one-pass repair loop
"""

from __future__ import annotations

import json
import re
import time
from urllib.parse import urlparse
from typing import Any

RESEARCH_HINTS = (
    "research",
    "scrape",
    "find",
    "top",
    "market",
    "competitor",
    "holding",
    "benchmark",
    "compare",
    "sources",
    "evidence",
)


def is_research_like(text: str) -> bool:
    """Return True when text likely requires grounded web retrieval."""
    lowered = (text or "").lower()
    return any(hint in lowered for hint in RESEARCH_HINTS)


def extract_urls(text: str) -> list[str]:
    """Extract unique URLs from text in first-seen order."""
    found = re.findall(r"https?://[^\s)\]>\"']+", text or "")
    seen: set[str] = set()
    unique: list[str] = []
    for url in found:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def source_diversity(urls: list[str]) -> dict[str, Any]:
    """Compute source diversity from URL domains."""
    domains: list[str] = []
    for url in urls:
        try:
            domain = urlparse(url).netloc.lower().strip()
            if domain.startswith("www."):
                domain = domain[4:]
            if domain:
                domains.append(domain)
        except Exception:
            continue
    unique_domains = sorted(set(domains))
    total = len(urls)
    unique_count = len(unique_domains)
    score = (unique_count / total) if total else 0.0
    return {
        "domains": unique_domains,
        "unique_domains": unique_count,
        "score": round(max(0.0, min(score, 1.0)), 3),
    }


def analyze_answer_consistency(text: str) -> dict[str, Any]:
    """Heuristic contradiction detector for final answers."""
    lowered = (text or "").lower()
    contradiction_pairs = [
        (r"\bincrease(d)?\b", r"\bdecrease(d)?\b", "increase vs decrease"),
        (r"\bhigher\b", r"\blower\b", "higher vs lower"),
        (r"\bblocked\b", r"\bcomplete(d)?\b", "blocked vs complete"),
        (r"\byes\b", r"\bno\b", "yes vs no"),
        (r"\bpass\b", r"\bfail(ed)?\b", "pass vs fail"),
    ]
    hits: list[str] = []
    for left_pattern, right_pattern, label in contradiction_pairs:
        if re.search(left_pattern, lowered) and re.search(right_pattern, lowered):
            hits.append(label)
    return {
        "count": len(hits),
        "items": hits,
        "score": max(0.0, 1.0 - (0.2 * len(hits))),
    }


def estimate_confidence(text: str, source_count: int) -> float:
    """Heuristic confidence score based on evidence density and failure cues."""
    lowered = (text or "").lower()
    if "no results" in lowered or "couldn't extract" in lowered:
        return 0.30
    if source_count >= 8:
        return 0.92
    if source_count >= 5:
        return 0.85
    if source_count >= 2:
        return 0.72
    return 0.55


def build_evidence_envelope(raw_evidence: str, generated_answer: str = "") -> str:
    """Build a standardized evidence metadata appendix."""
    urls = extract_urls(raw_evidence)
    diversity = source_diversity(urls)
    confidence = estimate_confidence(raw_evidence + "\n" + generated_answer, len(urls))
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "",
        "### Evidence Envelope",
        f"- Retrieved at: {timestamp}",
        f"- Source count: {len(urls)}",
        f"- Unique domains: {int(diversity.get('unique_domains', 0))}",
        f"- Diversity score: {int(float(diversity.get('score', 0.0)) * 100)}%",
        f"- Confidence: {int(confidence * 100)}%",
        "- Sources:",
    ]
    if urls:
        lines.extend(f"  - {url}" for url in urls[:12])
    else:
        lines.append("  - (no explicit URLs found)")
    return "\n".join(lines)


def format_verifier_block(meta: dict[str, Any]) -> str:
    """Format verifier metadata consistently across handlers."""
    return (
        "\n\n### Verifier\n"
        f"- Pass: {'YES' if meta.get('pass') else 'NO'}\n"
        f"- Confidence: {int(float(meta.get('confidence', 0.0)) * 100)}%\n"
        f"- Repairs: {int(meta.get('repairs', 0))}\n"
        f"- Notes: {meta.get('notes', 'n/a')}"
    )


def enforce_grounded_answer(
    task: str,
    candidate: str,
    evidence_text: str,
    *,
    min_sources: int = 3,
) -> tuple[str, dict[str, Any]]:
    """Gate final answers when research tasks lack sufficient evidence.

    Returns (text, meta). If blocked=True in meta, the returned text is a safe
    grounded response that asks for retrieval retry instead of hallucinating.
    """
    urls = extract_urls(evidence_text or "")
    diversity = source_diversity(urls)
    source_count = len(urls)
    blocked = is_research_like(task) and source_count < min_sources
    if not blocked:
        return candidate, {
            "blocked": False,
            "source_count": source_count,
            "unique_domains": int(diversity.get("unique_domains", 0)),
            "diversity_score": float(diversity.get("score", 0.0)),
            "min_sources": min_sources,
            "sources": urls,
        }

    blocked_text = (
        "1) Status\n"
        "Blocked — insufficient grounded evidence was retrieved.\n\n"
        "2) Key Findings\n"
        f"• Retrieved explicit sources: {source_count} (required: {min_sources})\n"
        "• Proceeding would risk unsupported claims.\n\n"
        "3) Evidence\n"
        + ("\n".join(f"• {u}" for u in urls[:12]) if urls else "• No explicit URLs were captured in the evidence payload.")
        + "\n\n4) Confidence\n"
        "Low (grounding threshold not met).\n\n"
        "5) Next Actions\n"
        "• Retry retrieval with more pages/sources.\n"
        "• Provide a trusted source list or document for extraction.\n"
        "• Re-run analysis once evidence threshold is satisfied."
    )
    return blocked_text, {
        "blocked": True,
        "source_count": source_count,
        "unique_domains": int(diversity.get("unique_domains", 0)),
        "diversity_score": float(diversity.get("score", 0.0)),
        "min_sources": min_sources,
        "sources": urls,
    }


async def gather_web_evidence(
    topic: str,
    *,
    min_sources: int = 5,
    start_pages: int = 8,
    max_pages: int = 18,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Collect grounded web evidence with a hard minimum-source target.

    Tries multiple retrieval passes with increasing page budgets until
    minimum source count is reached or attempts are exhausted.
    """
    from computer_agent import execute_tool

    pages = max(3, start_pages)
    attempts = 0
    best_evidence = ""
    best_urls: list[str] = []

    while attempts < max_attempts:
        attempts += 1
        raw = await execute_tool(
            "web_research",
            {
                "topic": topic,
                "max_pages": min(pages, max_pages),
            },
        )
        evidence = str(raw or "")
        urls = extract_urls(evidence)
        if len(urls) > len(best_urls):
            best_urls = urls
            best_evidence = evidence
        if len(urls) >= min_sources:
            return {
                "ok": True,
                "attempts": attempts,
                "source_count": len(urls),
                "sources": urls,
                "evidence": evidence,
                "min_sources": min_sources,
            }
        pages = min(max_pages, pages + 4)

    return {
        "ok": len(best_urls) >= min_sources,
        "attempts": attempts,
        "source_count": len(best_urls),
        "sources": best_urls,
        "evidence": best_evidence,
        "min_sources": min_sources,
    }


async def gather_fused_evidence(
    topic: str,
    *,
    user_id: str = "0",
    min_sources: int = 5,
    start_pages: int = 8,
    max_pages: int = 20,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Fuse retrieval from web research + arXiv + memory.

    Returns the same shape as gather_web_evidence(), plus retriever breakdown.
    """
    web_meta = await gather_web_evidence(
        topic,
        min_sources=min_sources,
        start_pages=start_pages,
        max_pages=max_pages,
        max_attempts=max_attempts,
    )

    evidence_parts: list[str] = [str(web_meta.get("evidence", "") or "")]
    urls = list(web_meta.get("sources", []) or [])
    retrievers: dict[str, Any] = {
        "web": {
            "source_count": int(web_meta.get("source_count", 0)),
            "ok": bool(web_meta.get("ok", False)),
        }
    }

    try:
        from tools.arxiv import search_arxiv

        papers = await search_arxiv(topic, max_results=3)
        if papers:
            arxiv_lines = ["\n\n[arXiv Results]"]
            for paper in papers:
                arxiv_lines.append(
                    f"- {paper.get('title', '')} | {paper.get('pdf_url', '')} | {paper.get('published', '')}"
                )
                pdf_url = str(paper.get("pdf_url", "") or "")
                if pdf_url:
                    urls.append(pdf_url)
            evidence_parts.append("\n".join(arxiv_lines))
        retrievers["arxiv"] = {"count": len(papers)}
    except Exception:
        retrievers["arxiv"] = {"count": 0}

    try:
        from tools.memory import search_memory

        mem_hits = await search_memory(topic, top_k=4, user_id=user_id)
        if mem_hits:
            mem_lines = ["\n\n[Memory Hits]"]
            for hit in mem_hits[:4]:
                snippet = str(hit.get("text", "")).replace("\n", " ")[:260]
                source = str(hit.get("source", "memory"))
                mem_lines.append(f"- ({source}) {snippet}")
            evidence_parts.append("\n".join(mem_lines))
        retrievers["memory"] = {"count": len(mem_hits)}
    except Exception:
        retrievers["memory"] = {"count": 0}

    merged_evidence = "\n\n".join(part for part in evidence_parts if part)
    merged_urls = extract_urls("\n".join(urls) + "\n" + merged_evidence)
    return {
        "ok": len(merged_urls) >= min_sources,
        "attempts": int(web_meta.get("attempts", 0)),
        "source_count": len(merged_urls),
        "sources": merged_urls,
        "evidence": merged_evidence,
        "min_sources": min_sources,
        "retrievers": retrievers,
    }


async def verify_and_repair(
    task: str,
    candidate: str,
    *,
    verifier_agent: str = "debug",
    repair_agent: str = "architect",
    user_id: str = "0",
    max_repairs: int = 1,
) -> tuple[str, dict[str, Any]]:
    """Verify answer quality and optionally repair once.

    Returns:
        (final_text, meta)
        meta keys: pass(bool), confidence(float), notes(str), repairs(int)
    """
    from llm_client import chat

    current = candidate
    repairs = 0

    async def _verify(text: str) -> tuple[bool, float, str]:
        prompt = (
            "You are a strict verifier. Validate if the answer below is grounded, complete, "
            "and directly answers the task.\n\n"
            f"Task:\n{task}\n\n"
            f"Answer:\n{text}\n\n"
            "Return ONLY JSON:\n"
            '{"pass": true|false, "confidence": 0.0-1.0, "notes": "short reason", '
            '"fix": "if fail, concise repair instruction"}'
        )
        raw, _ = await chat(prompt, agent_key=verifier_agent, user_id=user_id)
        payload = raw.strip()
        if "{" in payload and "}" in payload:
            payload = payload[payload.index("{"): payload.rindex("}") + 1]
        parsed = json.loads(payload)
        passed = bool(parsed.get("pass", False))
        confidence = float(parsed.get("confidence", 0.5))
        notes = str(parsed.get("notes") or parsed.get("fix") or "no notes")
        return passed, max(0.0, min(confidence, 1.0)), notes[:700]

    try:
        passed, confidence, notes = await _verify(current)
    except Exception:
        passed = "source" in current.lower() or "http" in current.lower()
        confidence = 0.70 if passed else 0.50
        notes = "fallback verifier used (malformed verifier output)"

    while not passed and repairs < max_repairs:
        repairs += 1
        repair_prompt = (
            "Repair this answer using verifier feedback while keeping claims grounded.\n\n"
            f"Task:\n{task}\n\n"
            f"Verifier feedback:\n{notes}\n\n"
            f"Current answer:\n{current}\n\n"
            "Return improved final answer."
        )
        repaired, _ = await chat(repair_prompt, agent_key=repair_agent, user_id=user_id)
        current = repaired
        try:
            passed, confidence, notes = await _verify(current)
        except Exception:
            passed = "source" in current.lower() or "http" in current.lower()
            confidence = 0.70 if passed else 0.50
            notes = "fallback verifier used (malformed verifier output)"
            break

    meta = {
        "pass": passed,
        "confidence": confidence,
        "notes": notes,
        "repairs": repairs,
    }
    return current, meta
