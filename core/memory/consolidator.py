"""Memory consolidator — guarantees long-term memory survives and stays useful.

Runs three jobs:
1. deduplicate()       — removes near-duplicate entries (TF-IDF cosine > 0.85)
2. run_nightly()       — groups old memories by topic (LLM), merges into summaries
3. promote_important() — after each conversation, promotes key facts to CoreMemory

Scheduled: nightly at 2:00 AM via main.py scheduler.
Called after each chat turn via _post_call_hooks() in llm_client.py.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Maximum characters of conversation to send to promote_important LLM call
_MAX_PROMOTE_CTX = 3000
# Maximum CoreMemory entries added per session (prevents bloat)
_MAX_PROMOTE_PER_SESSION = 3
_session_promote_count = 0


# ── TF-IDF helpers (no external deps) ────────────────────────────────────────


def _tokenise(text: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", text.lower())


def _tfidf_vector(text: str, corpus_df: Counter, n_docs: int) -> dict[str, float]:
    tokens = _tokenise(text)
    tf = Counter(tokens)
    total = sum(tf.values()) or 1
    vec: dict[str, float] = {}
    for token, count in tf.items():
        df = corpus_df.get(token, 1)
        vec[token] = (count / total) * math.log((n_docs + 1) / (df + 1))
    return vec


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    shared = set(a) & set(b)
    if not shared:
        return 0.0
    dot = sum(a[t] * b[t] for t in shared)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


# ── Core jobs ─────────────────────────────────────────────────────────────────


async def deduplicate() -> int:
    """Remove near-duplicate ArchivalMemory entries. Returns count deleted."""
    from core.memory.tiers import ArchivalMemory

    archival = ArchivalMemory()

    def _fetch_all() -> list[dict[str, Any]]:
        rows = archival.conn.execute("SELECT id, content, importance FROM memories ORDER BY importance DESC").fetchall()
        return [{"id": r[0], "content": r[1], "importance": r[2]} for r in rows]

    rows = await asyncio.to_thread(_fetch_all)
    if len(rows) < 2:
        return 0

    # Build corpus document-frequency for TF-IDF
    corpus_df: Counter = Counter()
    for r in rows:
        corpus_df.update(set(_tokenise(r["content"])))
    n_docs = len(rows)

    vecs = [(r["id"], r["importance"], _tfidf_vector(r["content"], corpus_df, n_docs)) for r in rows]
    deleted_ids: set[int] = set()

    for i in range(len(vecs)):
        if vecs[i][0] in deleted_ids:
            continue
        for j in range(i + 1, len(vecs)):
            if vecs[j][0] in deleted_ids:
                continue
            sim = _cosine(vecs[i][2], vecs[j][2])
            if sim >= 0.85:
                # Keep the higher-importance one
                keep_idx = i if vecs[i][1] >= vecs[j][1] else j
                drop_idx = j if keep_idx == i else i
                deleted_ids.add(vecs[drop_idx][0])

    if not deleted_ids:
        return 0

    def _delete(ids: list[int]) -> None:
        placeholders = ",".join("?" * len(ids))
        archival.conn.execute(f"DELETE FROM memories WHERE id IN ({placeholders})", ids)
        archival.conn.commit()

    await asyncio.to_thread(_delete, list(deleted_ids))
    logger.info("[Consolidator] Deduplicated %d memories", len(deleted_ids))
    return len(deleted_ids)


async def run_nightly() -> dict[str, int]:
    """Consolidate memories older than 30 days into topic-clustered summaries."""
    from core.memory.tiers import ArchivalMemory
    from llm_client import call_llm

    archival = ArchivalMemory()
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

    def _fetch_old() -> list[dict[str, Any]]:
        rows = archival.conn.execute(
            """
            SELECT id, content, tags, importance
            FROM memories
            WHERE created_at < ?
              AND (tags NOT LIKE '%consolidated%')
            ORDER BY created_at ASC
            LIMIT 200
            """,
            (cutoff,),
        ).fetchall()
        return [{"id": r[0], "content": r[1], "tags": r[2], "importance": r[3]} for r in rows]

    old_entries = await asyncio.to_thread(_fetch_old)
    if len(old_entries) < 5:
        logger.info("[Consolidator] Not enough old memories to consolidate (%d)", len(old_entries))
        return {"consolidated": 0, "deleted_duplicates": 0}

    # Ask LLM to cluster entries into topics and summarise each cluster
    combined = "\n".join(f"[{i + 1}] {e['content'][:300]}" for i, e in enumerate(old_entries[:80]))
    prompt = (
        "You are a memory consolidator for an AI assistant. "
        "These are old memory entries from conversations over the past months. "
        "Group them into topic clusters and write ONE concise summary per cluster. "
        "Format:\n"
        "CLUSTER: <topic name>\n"
        "SUMMARY: <2-3 sentence summary of what was discussed/decided/learned>\n"
        "IDS: <comma-separated numbers from the list>\n\n"
        f"Memory entries:\n{combined}\n\n"
        "Output all clusters. Keep summaries factual and useful."
    )

    try:
        llm_output = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model="groq/moonshotai/kimi-k2-instruct",
            temperature=0.2,
            max_tokens=2000,
        )
        if isinstance(llm_output, dict):
            llm_output = ""
    except Exception as exc:
        logger.warning("[Consolidator] LLM clustering failed: %s", exc)
        return {"consolidated": 0, "deleted_duplicates": 0}

    # Parse clusters
    cluster_pattern = re.compile(
        r"CLUSTER:\s*(.+?)\nSUMMARY:\s*(.+?)\nIDS:\s*([0-9,\s]+)",
        re.DOTALL | re.IGNORECASE,
    )
    consolidated = 0
    archived_ids: list[int] = []

    for match in cluster_pattern.finditer(llm_output):
        topic = match.group(1).strip()
        summary = match.group(2).strip()
        raw_ids = match.group(3).strip()
        try:
            id_indices = [int(x.strip()) - 1 for x in raw_ids.split(",") if x.strip().isdigit()]
            entry_ids = [old_entries[i]["id"] for i in id_indices if 0 <= i < len(old_entries)]
        except Exception:
            continue

        if not summary or len(entry_ids) < 2:
            continue

        # Write consolidated summary as a new high-importance memory
        def _store_summary() -> None:
            archival.store(
                content=summary,
                summary=f"Consolidated topic: {topic}",
                tags=["consolidated", "long_term", topic.lower().replace(" ", "_")],
                importance=0.90,
                source="consolidator",
            )

        await asyncio.to_thread(_store_summary)
        archived_ids.extend(entry_ids)
        consolidated += 1

    # Mark originals as archived (add tag — don't delete, keep for audit)
    if archived_ids:

        def _mark_archived(ids: list[int]) -> None:
            for entry_id in ids:
                archival.conn.execute(
                    "UPDATE memories SET tags = tags || ',consolidated', importance = importance * 0.3 WHERE id = ?",
                    (entry_id,),
                )
            archival.conn.commit()

        await asyncio.to_thread(_mark_archived, archived_ids)

    # Also run deduplication while we're at it
    deleted = await deduplicate()

    logger.info(
        "[Consolidator] Nightly complete: %d clusters consolidated, %d duplicates removed",
        consolidated,
        deleted,
    )
    return {"consolidated": consolidated, "deleted_duplicates": deleted}


async def promote_important(recent_turns: list[dict[str, str]]) -> None:
    """Extract permanently important facts from a conversation and save to CoreMemory."""
    global _session_promote_count
    if _session_promote_count >= _MAX_PROMOTE_PER_SESSION:
        return

    from core.memory.tiers import CoreMemory
    from llm_client import call_llm

    core = CoreMemory()
    existing = core.all()

    conversation = "\n".join(
        f"{t.get('role', 'unknown').upper()}: {t.get('content', '')[:400]}" for t in recent_turns[-8:]
    )
    if len(conversation) < 100:
        return

    existing_summary = "; ".join(f"{k}: {v[:80]}" for k, v in list(existing.items())[:10])

    prompt = (
        "You are reviewing a conversation between a user (Bashara) and his AI assistant (Legion). "
        "Identify facts that should be permanently remembered — things that would help Legion "
        "be more useful in future conversations. Only include genuinely important, lasting facts "
        "(not task-specific details that won't matter later).\n\n"
        f"Already in core memory: {existing_summary or 'nothing yet'}\n\n"
        f"Conversation:\n{conversation}\n\n"
        "Output a JSON object with key-value pairs to add to core memory. "
        "Max 2 entries. If nothing new is worth storing, output: {}\n"
        'Example: {"preferred_framework": "FastAPI over Flask", "home_location": "Koto City, Tokyo"}'
    )

    try:
        raw = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model="groq/llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=200,
        )
        if isinstance(raw, dict):
            raw = "{}"
        # Extract JSON
        json_match = re.search(r"\{[^}]*\}", raw, re.DOTALL)
        if not json_match:
            return
        facts: dict[str, str] = json.loads(json_match.group(0))
        for key, value in facts.items():
            if key and value and key not in existing:
                core.set(str(key)[:50], str(value)[:200])
                _session_promote_count += 1
                logger.info("[Consolidator] Promoted to CoreMemory: %s", key)
                if _session_promote_count >= _MAX_PROMOTE_PER_SESSION:
                    break
    except Exception as exc:
        logger.debug("[Consolidator] promote_important failed: %s", exc)
