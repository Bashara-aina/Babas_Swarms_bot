"""core/memory/session_summary_synthesizer.py — Synthesize session observations into wiki articles.

Triggered by the Stop hook or session end. Reads all observations for a session,
uses an LLM to synthesize them into structured <request>/<learned>/<next_steps>,
then writes the result to .wiki/joint-brain/sessions/.

This is the write path: session → observation_store → LLM synthesis → Obsidian wiki.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from core.memory.observation_store import get_observation_store

logger = logging.getLogger(__name__)

WIKI_SESSIONS_ROOT = Path(__file__).parent.parent.parent / ".wiki" / "joint-brain" / "sessions"
WIKI_SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)

# Observation type emoji for visual scanning
_TYPE_EMOJI = {
    "decision": "⚖️",
    "bugfix": "🐛",
    "feature": "✨",
    "refactor": "♻️",
    "discovery": "💡",
    "change": "📝",
}


async def synthesize_session(
    session_id: str,
    request: str = "",
    llm_client: Any | None = None,
) -> dict[str, Any] | None:
    """Synthesize a session from observation_store → structured summary + wiki article.

    Args:
        session_id: Unique session identifier.
        request: The original user request / task description.
        llm_client: Optional LLM client for synthesis. If None, uses raw observations.

    Returns:
        Dict with request, investigated, learned, completed, next_steps, notes.
        Writes wiki article to .wiki/joint-brain/sessions/{session_id}.md
    """
    store = get_observation_store()

    # Layer 3: fetch all observations for this session
    observations = await store.get_session_observations(session_id)
    if not observations:
        logger.debug("[SessionSynth] No observations for session %s", session_id)
        return None

    session_summary = await store.get_session_summary(session_id)
    if session_summary:
        # Already synthesized — return existing
        return session_summary

    # Build observation digest for LLM
    digest = _build_digest(observations)

    if llm_client:
        try:
            summary = await _llm_synthesize(session_id, request, digest, llm_client)
        except Exception:
            logger.warning("[SessionSynth] LLM synthesis failed, using raw digest")
            summary = _raw_digest_summary(session_id, request, digest)
    else:
        summary = _raw_digest_summary(session_id, request, digest)

    # Persist structured summary
    await store.add_session_summary(
        session_id=session_id,
        **summary,
    )

    # Write wiki article
    await _write_wiki_article(session_id, request, observations, summary)

    logger.info("[SessionSynth] Synthesized session %s (%d observations)", session_id, len(observations))
    return summary


def _build_digest(observations: list[dict[str, Any]]) -> str:
    """Build a compact observation digest for LLM synthesis."""
    lines = []
    for obs in observations:
        emoji = _TYPE_EMOJI.get(obs["type"], "📌")
        lines.append(f"{emoji} [{obs['type']}] {obs['title']}")
        if obs.get("narrative"):
            lines.append(f"   {obs['narrative'][:300]}")
        if obs.get("facts"):
            lines.append(f"   Facts: {obs['facts'][:200]}")
        if obs.get("files_modified"):
            files = [f for f in obs["files_modified"] if f]
            if files:
                lines.append(f"   Modified: {', '.join(files[:5])}")
        lines.append("")
    return "\n".join(lines)


async def _llm_synthesize(
    session_id: str,
    request: str,
    digest: str,
    llm_client: Any,
) -> dict[str, Any]:
    """Use LLM to synthesize observations into structured summary."""
    prompt = f"""You are synthesizing a Claude Code / OpenCode session summary.
The session had the following goal:
{request or '(no explicit request recorded)'}

Key observations from the session:
{digest}

Generate a structured session summary with these exact sections (respond in markdown):

## Request
[What the user asked to do]

## Investigated
[What approaches, files, or concepts were explored]

## Learned
[Key findings, decisions made, insights gained]

## Completed
[What was successfully finished]

## Next Steps
[Follow-up items, unresolved questions, future work]

## Notes
[Any additional context worth remembering]

Be concise. Each section should be 1-3 sentences max."""
    try:
        response = await llm_client.chat(
            model="groq/llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            timeout=60,
        )
        return _parse_synthesis_response(response)
    except Exception as e:
        logger.warning("[SessionSynth] LLM synthesis error: %s", e)
        raise


def _parse_synthesis_response(response: str) -> dict[str, Any]:
    """Parse LLM response into structured summary dict."""
    sections = {
        "request": "",
        "investigated": "",
        "learned": "",
        "completed": "",
        "next_steps": "",
        "notes": "",
    }
    current = ""
    for line in response.split("\n"):
        line_stripped = line.strip()
        if line_stripped.startswith("## "):
            current = line_stripped[3:].lower().strip()
            if current not in sections:
                current = ""
        elif current and current in sections:
            sections[current] += line_stripped + "\n"
    # Clean up
    for key in sections:
        sections[key] = sections[key].strip()
    return sections


def _raw_digest_summary(session_id: str, request: str, digest: str) -> dict[str, Any]:
    """Fallback: build summary from raw digest without LLM."""
    return {
        "request": request or "Session " + session_id,
        "investigated": digest[:1000],
        "learned": "",
        "completed": "",
        "next_steps": "",
        "notes": "Auto-generated from observations (LLM synthesis unavailable)",
    }


async def _write_wiki_article(
    session_id: str,
    request: str,
    observations: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """Write synthesized session as an Obsidian markdown article."""
    emoji_by_type = _TYPE_EMOJI

    # Build frontmatter
    created = observations[0]["created_at"] if observations else ""
    obs_types = list(set(o["type"] for o in observations))
    all_tags = []
    for o in observations:
        all_tags.extend(o.get("tags", []))
    all_tags = list(set(all_tags))

    frontmatter = f"""---
name: {session_id}
description: {request[:200] if request else 'Session ' + session_id}
type: session
created: {created}
tags: [{", ".join(all_tags[:10])}]
observation_types: [{", ".join(obs_types)}]
wikilinks:
  - [[joint-brain/index]]
---

# Session: {session_id}

**Request**: {request or '(no explicit request)'}
**Observations**: {len(observations)}
"""

    # Observation index (Layer 1)
    obs_index = "\n## Observation Index\n\n"
    for o in observations:
        emoji = emoji_by_type.get(o["type"], "📌")
        files = o.get("files_modified", [])
        file_str = f" • {', '.join(files[:3])}" if files else ""
        obs_index += f"- {emoji} `{o['type']}` [{o['title']}](#{o['id']}){file_str}\n"
    obs_index += "\n"

    # Structured summary sections
    summary_sections = ""
    for section in ["request", "investigated", "learned", "completed", "next_steps", "notes"]:
        content = summary.get(section, "")
        if content:
            summary_sections += f"## {section.capitalize()}\n\n{content}\n\n"

    # Full observation details (Layer 3 — on demand)
    details = "\n## Observation Details\n\n"
    for o in observations:
        emoji = emoji_by_type.get(o["type"], "📌")
        details += f"### {emoji} [{o['id']}] {o['title']}\n\n"
        details += f"**Type**: `{o['type']}` | **Created**: {o['created_at']}\n\n"
        if o.get("subtitle"):
            details += f"**Subtitle**: {o['subtitle']}\n\n"
        if o.get("narrative"):
            details += f"{o['narrative']}\n\n"
        if o.get("facts"):
            details += f"**Facts**: {o['facts']}\n\n"
        if o.get("files_read"):
            details += f"**Files read**: {', '.join(o['files_read'][:10])}\n\n"
        if o.get("files_modified"):
            details += f"**Files modified**: {', '.join(o['files_modified'][:10])}\n\n"
        details += "---\n\n"

    # Compile
    article = f"{frontmatter}\n{obs_index}\n{summary_sections}\n{details}"
    article = article.strip()

    # Write to wiki
    safe_id = session_id.replace("/", "_").replace(" ", "-")
    out_path = WIKI_SESSIONS_ROOT / f"{safe_id}.md"
    try:
        out_path.write_text(article, encoding="utf-8")
        logger.debug("[SessionSynth] Wrote wiki article: %s", out_path)
    except Exception:
        logger.warning("[SessionSynth] Failed to write wiki article: %s", out_path)
