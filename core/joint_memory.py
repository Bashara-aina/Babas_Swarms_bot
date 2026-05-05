"""Joint memory facade — single write path for all 3 systems."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Any

WIKI_ROOT = Path(__file__).parent.parent / ".wiki"
SESSION_DIRS = {
    "opencode": WIKI_ROOT / "opencode" / "sessions",
    "claude-code": WIKI_ROOT / "claude-code" / "sessions",
    "legionbot": WIKI_ROOT / "legionbot" / "sessions",
}
CROSS_REFS_DIR = WIKI_ROOT / "joint-brain" / "cross-refs"

_ensure_dirs_done = False
_lock = asyncio.Lock()


def _ensure_dirs() -> None:
    global _ensure_dirs_done
    if _ensure_dirs_done:
        return
    for d in [*list(SESSION_DIRS.values()), CROSS_REFS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    _ensure_dirs_done = True


def _slug(content: str) -> str:
    return hashlib.md5(content[:80].encode(), usedforsecurity=False).hexdigest()[:12]


async def joint_save(
    content: str,
    source: str,
    tags: list[str] | None = None,
    summary: str = "",
) -> int:
    """Write to joint brain. source: 'opencode' | 'claude-code' | 'legionbot'."""
    _ensure_dirs()
    slug = _slug(content)
    ts = str(asyncio.get_running_loop().time())
    entry_id = int(
        hashlib.md5(f"{source}{slug}{ts}".encode(), usedforsecurity=False).hexdigest()[:8], 16
    )

    session_dir = SESSION_DIRS.get(source, SESSION_DIRS["opencode"])
    filename = session_dir / f"{slug}.json"
    entry = {
        "id": entry_id,
        "content": content,
        "summary": summary or content[:200],
        "tags": tags or [],
        "source": source,
        "slug": slug,
    }

    async with _lock:
        with open(filename, "w") as f:
            json.dump(entry, f)

    # Write cross-ref
    cross_ref = {
        "id": entry_id,
        "sources": [source],
        "query_terms": list(set(re.findall(r"\w{4,}", content.lower()))),
        "original_slug": slug,
    }
    cross_ref_file = CROSS_REFS_DIR / f"{slug}.json"
    with open(cross_ref_file, "w") as f:
        json.dump(cross_ref, f)

    return entry_id


async def joint_search(
    query: str,
    sources: list[str] | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Search across all sources or filter to specific ones."""
    _ensure_dirs()
    query_terms = set(re.findall(r"\w{4,}", query.lower()))
    results: list[tuple[int, dict[str, Any]]] = []

    search_dirs = SESSION_DIRS
    if sources:
        search_dirs = {k: SESSION_DIRS[k] for k in sources if k in SESSION_DIRS}

    for _src, directory in search_dirs.items():
        for file in directory.glob("*.json"):
            try:
                with open(file) as f:
                    entry = json.load(f)
                entry["_src_file"] = str(file)
                content_terms = set(
                    re.findall(r"\w{4,}", entry.get("content", "").lower())
                )
                score = len(query_terms & content_terms)
                if score > 0:
                    results.append((score, entry))
            except Exception:
                continue

    results.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in results[:limit]]


async def joint_get_recent(
    days: int = 7,
    sources: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Get recent session summaries across all systems, sorted by file mtime."""
    _ensure_dirs()
    results: list[dict[str, Any]] = []

    search_dirs = SESSION_DIRS
    if sources:
        search_dirs = {k: SESSION_DIRS[k] for k in sources if k in SESSION_DIRS}

    for _src, directory in search_dirs.items():
        for file in directory.glob("*.json"):
            try:
                with open(file) as f:
                    entry = json.load(f)
                entry["_src_file"] = str(file)
                entry["_mtime"] = file.stat().st_mtime
                results.append(entry)
            except Exception:
                continue

    results.sort(key=lambda x: x["_mtime"], reverse=True)
    return results[:limit]
