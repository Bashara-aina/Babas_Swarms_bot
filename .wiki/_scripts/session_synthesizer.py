#!/usr/bin/env python3
"""
Session Synthesizer — Option B wiki auto-ingestion
Reads draft stubs from .wiki/conversations/, synthesizes them into proper
wiki articles (concepts, decisions, architecture) using LLM analysis,
then moves stubs to .wiki/conversations/processed/.

Run via: python3 .wiki/_scripts/session_synthesizer.py
Schedule: after session_harvester.py, or as a separate hourly task
"""

from __future__ import annotations

import json
import re
import subprocess
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ── Config ────────────────────────────────────────────────────────────────────────
JST = timezone(timedelta(hours=9))
WIKI_ROOT = Path(__file__).parent.parent  # .wiki/ is wiki root
WIKI_CONVERSATIONS = WIKI_ROOT / "conversations"
WIKI_PROCESSED = WIKI_CONVERSATIONS / "processed"
WIKI_CONCEPTS = WIKI_ROOT / "concepts"
WIKI_DECISIONS = WIKI_ROOT / "decisions"
WIKI_ENTITIES = WIKI_ROOT / "entities"

WIKI_CONVERSATIONS.mkdir(parents=True, exist_ok=True)
WIKI_PROCESSED.mkdir(parents=True, exist_ok=True)
WIKI_CONCEPTS.mkdir(parents=True, exist_ok=True)
WIKI_DECISIONS.mkdir(parents=True, exist_ok=True)
WIKI_ENTITIES.mkdir(parents=True, exist_ok=True)

MAX_STUBS_PER_RUN = 5  # one synthesization per run to stay within budget


# ── LLM synthesis via litellm (same chain as Legion) ─────────────────────────

def _load_env() -> None:
    """Load .env from wiki root so API keys are available."""
    env_file = WIKI_ROOT.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                import os as _os
                _os.environ.setdefault(k.strip(), v.strip())


def synthesize_with_llm(stub_text: str, source: str) -> dict[str, Any] | None:
    """Analyze a stub and produce structured synthesis decisions."""
    _load_env()
    try:
        import litellm
        litellm.drop_params = True
    except ImportError:
        return None

    system_prompt = f"""You are a wiki synthesis assistant. Analyze this conversation stub from a {source} session and produce a structured JSON response.

Respond ONLY with valid JSON in this exact format:
{{
  "type": "concept" | "decision" | "architecture" | "entity",
  "title": "Short descriptive title (under 60 chars)",
  "slug": "kebab-case-slug",
  "summary": "2-3 sentence TL;DR for Dataview indexing",
  "tags": ["tag1", "tag2", "tag3"],
  "wikilinks": ["[[./concepts/other-concept]]", "[[./entities/tool-name]]", "[[INDEX]]"],
  "confidence": "high" | "medium" | "low",
  "body": "Full article text with TL;DR first, then detailed explanation. Must include at least one concrete example. Write for a future AI reader.",
  "key_decision": "If type is decision: what was decided? (else empty string)",
  "status": "active"
}}

Rules:
- summary must be 2-3 sentences, standalone (Dataview compatible)
- wikilinks must use relative paths from wiki root: ./concepts/, ./entities/, ./decisions/
- body must NOT be a conversation log — synthesize into knowledge
- If the session is trivial (small talk, one-off questions), set confidence: "low" and leave body shorter
- tags MUST be lowercase kebab-case
"""

    try:
        response = litellmcompletion(
            model="cerebras/llama3.1-8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": stub_text[:3000]},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        text = response["choices"][0]["message"]["content"]
        # strip markdown code fences
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text.strip())
    except Exception as e:
        print(f"  [LLM] synthesis failed: {e}")
        return None


def litellmcompletion(model: str, messages: list[dict], **kwargs):
    """Minimal litellm completion wrapper."""
    import litellm
    return litellm.completion(model=model, messages=messages, **kwargs)


# ── Keyword-based fallback synthesis ──────────────────────────────────────────

KEYWORD_PATTERNS: list[tuple[str, str, str, list[str]]] = [
    # (keyword, type, title_prefix, tags)
    ("bug", "decision", "Bug Fix", ["bug", "fix"]),
    ("fix", "decision", "Bug Fix", ["bug", "fix"]),
    ("refactor", "architecture", "Refactor", ["refactor", "architecture"]),
    ("architect", "architecture", "Architecture Decision", ["architecture", "design"]),
    ("memory", "concept", "Memory System", ["memory", "legion"]),
    ("intent", "concept", "Intent Routing", ["intent", "routing"]),
    ("soul", "concept", "Soul Engine", ["soul", "personality"]),
    ("emotion", "concept", "Emotion Engine", ["emotion", "personality"]),
    ("wiki", "concept", "Wiki Knowledge Base", ["wiki", "karpathy-kb"]),
    ("model", "entity", "Model Configuration", ["model", "llm"]),
    ("agent", "architecture", "Agent Architecture", ["agent", "architecture"]),
    ("routing", "concept", "LLM Routing", ["routing", "llm"]),
    ("test", "decision", "Testing Decision", ["testing", "quality"]),
    ("deploy", "architecture", "Deployment", ["deploy", "infrastructure"]),
    ("security", "concept", "Security", ["security"]),
    ("performance", "concept", "Performance", ["performance"]),
    ("api", "entity", "API Integration", ["api", "integration"]),
    ("error", "decision", "Error Resolution", ["error", "debugging"]),
    ("change", "decision", "Change Decision", ["change"]),
    ("add ", "decision", "New Feature", ["feature", "change"]),
    ("remove", "decision", "Removal Decision", ["change"]),
]

EXISTING_ARTICLES: list[str] = []  # populated once


def get_existing_articles() -> list[str]:
    """Get list of existing article slugs for wikilink suggestions."""
    global EXISTING_ARTICLES
    if EXISTING_ARTICLES:
        return EXISTING_ARTICLES
    slugs = []
    for ext in ["md"]:
        for f in WIKI_CONCEPTS.glob(f"*.{ext}"):
            slugs.append(f"./concepts/{f.stem}")
        for f in WIKI_DECISIONS.glob(f"*.{ext}"):
            slugs.append(f"./decisions/{f.stem}")
        for f in WIKI_ENTITIES.glob(f"*.{ext}"):
            slugs.append(f"./entities/{f.stem}")
    EXISTING_ARTICLES = sorted(slugs)
    return EXISTING_ARTICLES


def synthesize_with_keywords(stub_text: str, source: str, slug_hint: str = "") -> dict[str, Any]:
    """Fallback synthesis when LLM is unavailable."""
    text_lower = stub_text.lower()
    best_match = ("general", "concept", "General Session", ["session", source])

    for keyword, art_type, title_pref, tags in KEYWORD_PATTERNS:
        if keyword in text_lower:
            best_match = (keyword, art_type, title_pref, tags)
            break

    keyword, art_type, title_pref, tags = best_match

    # Extract a title from the first meaningful user message
    lines = [l.strip() for l in stub_text.split("\n") if l.strip() and l.strip().startswith("- **USER")]
    first_msg = lines[0] if lines else ""
    title_content = re.sub(r"^- \*\*USER\*\*:\s*", "", first_msg)[:50] if first_msg else "session note"
    title = f"{title_pref}: {title_content}"

    slug_base = re.sub(r"[^a-z0-9]+", "-", title.lower())[:50]
    slug = f"{source}-{slug_base}" if slug_hint in ["", "claude-code", "opencode", "legion-bot"] else slug_hint

    body = f"""## Summary

Captured from {source} session — synthesized into a concept note.

## Details

{stub_text[:1500]}

## Key Takeaway

Keywords detected: {keyword}
Type classified as: {art_type}

---

_Synthesized via session_synthesizer.py keyword fallback (LLM unavailable)_
"""
    return {
        "type": art_type,
        "title": title,
        "slug": slug,
        "summary": f"{source} session note: {title_content}",
        "tags": tags + [source],
        "wikilinks": ["[[INDEX]]"],
        "confidence": "low",
        "body": body,
        "key_decision": "",
        "status": "active",
    }


# ── Wiki article writer ────────────────────────────────────────────────────────

def write_article(synthesis: dict[str, Any], source: str) -> Path | None:
    """Write a synthesized article to the appropriate wiki directory."""
    art_type = synthesis.get("type", "concept")
    slug = synthesis.get("slug", "untitled")
    body = synthesis.get("body", "")
    confidence = synthesis.get("confidence", "medium")

    if not body:
        # Nothing to write
        return None

    # Choose directory by type
    type_map = {
        "concept": WIKI_CONCEPTS,
        "decision": WIKI_DECISIONS,
        "architecture": WIKI_CONCEPTS,
        "entity": WIKI_ENTITIES,
    }
    directory = type_map.get(art_type, WIKI_CONCEPTS)
    path = directory / f"{slug}.md"

    if path.exists():
        print(f"  [SKIP] already exists: {path.name}")
        return None

    dt = datetime.now(JST)
    created = synthesis.get("created", dt.strftime("%Y-%m-%d"))
    wikilinks = synthesis.get("wikilinks", [])
    wikilinks_md = "\n".join(f"  - {link}" for link in wikilinks)

    frontmatter = f"""---
title: {synthesis.get('title', slug)}
type: {art_type}
status: {synthesis.get('status', 'active')}
tags: {json.dumps(synthesis.get('tags', [source]), ensure_ascii=False)}
created: {created}
updated: {dt.strftime('%Y-%m-%d')}
summary: {synthesis.get('summary', '')}
wikilinks:
{wikilinks_md}
confidence: {confidence}
source: {source}
---

"""
    path.write_text(frontmatter + body, encoding="utf-8")
    print(f"  Wrote: {path.relative_to(WIKI_ROOT)}")
    return path


# ── Decision extractor ────────────────────────────────────────────────────────

def extract_decisions(stub_text: str) -> list[dict[str, str]]:
    """Detect decision-like statements in conversation stub."""
    decisions = []
    # Look for action/commitment language
    patterns = [
        r"(?:i'll|i will|we'll|we will|legion will)\s+(.{10,80})",
        r"(?:decided|decision|agreed|commit|commitment)[:\s]+(. {10,100})",
        r"(?:change[d]?\s+to|moved\s+to|switched\s+to|refactored\s+to)[:\s]+(. {10,80})",
        r"(?:fixed|bug|destroyed|removed|added)[:\s]+(. {10,80})",
        r"(?:the problem was|root cause)[:\s]+(. {10,120})",
    ]
    for pat in patterns:
        for match in re.finditer(pat, stub_text, re.IGNORECASE):
            decision_text = match.group(1).strip()
            if len(decision_text) > 15:
                decisions.append({
                    "decision": decision_text[:200],
                    "pattern": pat[:40],
                })
    return decisions[:3]  # cap at 3 decisions per stub


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[SYNTHESIZER] Starting synthesis at {datetime.now(JST).isoformat()}")

    stubs = sorted(WIKI_CONVERSATIONS.glob("*.md"))
    if not stubs:
        print("[SYNTHESIZER] No stubs to process")
        return

    print(f"[SYNTHESIZER] Found {len(stubs)} stubs, processing up to {MAX_STUBS_PER_RUN}")
    processed = 0
    articles_written = 0

    for stub_path in stubs[:MAX_STUBS_PER_RUN]:
        try:
            content = stub_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  [ERR] reading {stub_path.name}: {e}")
            continue

        # Determine source from filename
        source = "unknown"
        for s in ["claude-code", "opencode", "legion-bot"]:
            if s in stub_path.name:
                source = s
                break

        # Extract frontmatter + body
        parts = content.split("---", 3)
        frontmatter_raw = parts[1] if len(parts) > 2 else ""
        body = parts[2] if len(parts) > 2 else content

        # Try LLM synthesis first
        synthesis = synthesize_with_llm(body, source)

        # Fall back to keyword synthesis
        if not synthesis:
            synthesis = synthesize_with_keywords(body, source, slug_hint=stub_path.stem)

        # Write article
        path = write_article(synthesis, source)
        if path:
            articles_written += 1

        # Archive stub
        archive_path = WIKI_PROCESSED / stub_path.name
        stub_path.rename(archive_path)
        processed += 1
        print(f"  Archived: {stub_path.name} → processed/")

    # Update compile state
    try:
        f = WIKI_ROOT / "_meta" / "compile_state.json"
        d = json.load(open(f)) if f.exists() else {}
        convs = len(list(WIKI_CONVERSATIONS.glob("*.md")))
        convs_processed = len(list(WIKI_PROCESSED.glob("*.md")))
        from glob import glob as _glob
        articles = len([x for x in _glob(str(WIKI_ROOT / "**/*.md"), recursive=True)
                        if not any(s in x for s in ["_meta", "INDEX", "SCHEMA", "output", "conversations"])])
        d.update({
            "last_compiled": datetime.now(JST).isoformat(),
            "articles": articles,
            "conversation_stubs": convs,
            "conversation_stubs_processed": convs_processed,
        })
        json.dump(d, open(f, "w"), indent=2)
    except Exception as e:
        print(f"[WARN] compile_state update failed: {e}")

    print(f"[SYNTHESIZER] Done — {processed} stubs processed, {articles_written} articles written")


if __name__ == "__main__":
    main()
