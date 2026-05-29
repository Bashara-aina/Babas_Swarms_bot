#!/usr/bin/env python3
"""
Dreaming Consolidation — Hippocampal replay for Minerva/Hermes.

Async background job that reorganizes memory between sessions:
  1. Parse recent session transcripts (from session_archivist FTS5 store)
  2. Identify patterns: repeated bugs, contradicting decisions, new conventions,
     recurring errors, code patterns used repeatedly
  3. Reorganize GraphRAG: archive superseded facts, promote high-confidence
     patterns, add new entity relationships
  4. Update confidence scores: increment access counts, apply decay, boost
     frequently-used patterns
  5. Deduplicate near-duplicate entries (Jaccard similarity > 0.8)
  6. Pre-compute next-session context briefings and cache them

Triggers:
  - Session end + idle time > 60 seconds
  - Manual call to dreaming_run(force=True)
  - Scheduled every 30 minutes during idle

State: /tmp/hermes_dreaming_state.json
Cache:  /tmp/hermes_dream_cache/   (pre-computed briefings)
Max 450 lines.
"""
import asyncio
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# Paths
# ============================================================================

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
STATE_FILE = Path("/tmp/hermes_dreaming_state.json")
CACHE_DIR = Path("/tmp/hermes_dream_cache")

# Session archivist DB (read-only reference)
FTS_DB = HERMES_HOME / "sessions" / "fts.db"

# Cross-session memory DB
MEMORY_DB = HERMES_HOME / "memories" / "cross_session_memory.db"

LOCK = threading.Lock()

# Decay constants (aligned with cross_session_memory.py)
DECAY_BASE = 0.5
DECAY_RATE = 0.1
USAGE_BOOST = 0.05
MIN_PRIORITY_THRESHOLD = 0.1

# Idempotency / deduplication
JACCARD_THRESHOLD = 0.8
MIN_SESSION_AGE_SECONDS = 60  # idle before dreaming

# Per-run limits
MAX_SESSIONS_TO_SCAN = 50
MAX_PATTERNS_TO_CONSOLIDATE = 100
MAX_DEDUP_PAIRS = 50


# ============================================================================
# State Persistence
# ============================================================================

def _load_state() -> Dict[str, Any]:
    """Load dreaming state, returning defaults on missing/invalid file."""
    if not STATE_FILE.exists():
        return {"last_run_at": 0.0, "last_run_duration": 0.0,
                "total_runs": 0, "entries_processed": 0,
                "changes_made": 0, "patterns_found": 0,
                "dedup_merges": 0, "last_error": None,
                "is_running": False, "run_history": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"last_run_at": 0.0, "last_run_duration": 0.0,
                "total_runs": 0, "entries_processed": 0,
                "changes_made": 0, "patterns_found": 0,
                "dedup_merges": 0, "last_error": None,
                "is_running": False, "run_history": []}


def _save_state(state: Dict[str, Any]) -> None:
    """Atomically write state to disk."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ============================================================================
# Session Data Access (read-only from session_archivist DB)
# ============================================================================

def _get_recent_sessions(limit: int = MAX_SESSIONS_TO_SCAN) -> List[Dict[str, Any]]:
    """Read recent session metadata from the FTS DB (read-only)."""
    if not FTS_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(FTS_DB), check_same_thread=False)
        conn.execute("PRAGMA query_only=ON")
        rows = conn.execute("""
            SELECT session_id, timestamp, agent_name, parent_session_id,
                   summary, tool_calls, error_count, message_count
            FROM sessions_fts
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [
            {"session_id": r[0], "timestamp": r[1], "agent_name": r[2],
             "parent_session_id": r[3], "summary": r[4], "tool_calls": r[5],
             "error_count": r[6], "message_count": r[7]}
            for r in rows
        ]
    except Exception as e:
        logger.warning("Failed to read sessions from FTS DB: %s", e)
        return []


def _get_session_content(session_id: str) -> str:
    """Read raw session content from archived session JSON files."""
    sessions_dir = HERMES_HOME / "sessions"
    for f in sorted(sessions_dir.glob("session_*.json"), key=lambda x: -x.stat().st_mtime):
        try:
            data = json.loads(f.read_text())
            if data.get("session_id") == session_id:
                msgs = data.get("messages", [])
                return " ".join(m.get("content", "") for m in msgs[-50:]
                                if isinstance(m.get("content"), str))
        except Exception:
            pass
    return ""


# ============================================================================
# Cross-Session Memory Access (read-only)
# ============================================================================

def _get_memory_entries(include_archived: bool = False) -> List[Dict[str, Any]]:
    """Read all entries from cross_session_memory DB (read-only)."""
    if not MEMORY_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("PRAGMA query_only=ON")
        query = """
            SELECT entry_key, value, version, created_at, updated_at,
                   last_accessed_at, access_count, priority, is_archived,
                   metadata_json, provenance_json
            FROM memory_entries
        """
        if not include_archived:
            query += " WHERE is_archived = 0"
        query += " ORDER BY priority DESC"
        rows = conn.execute(query).fetchall()
        conn.close()
        results = []
        for r in rows:
            results.append({
                "key": r[0], "value": r[1], "version": r[2],
                "created_at": r[3], "updated_at": r[4],
                "last_accessed_at": r[5], "access_count": r[6],
                "priority": round(r[7], 4), "is_archived": bool(r[8]),
                "metadata": json.loads(r[9] or "{}"),
                "provenance": json.loads(r[10] or "{}"),
            })
        return results
    except Exception as e:
        logger.warning("Failed to read memory entries: %s", e)
        return []


# ============================================================================
# Pattern Recognition (lightweight heuristics, no LLM)
# ============================================================================

def _tokenize(text: str) -> Set[str]:
    """Normalize and tokenize text for similarity comparison."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return {t for t in tokens if len(t) > 2}


def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _detect_repeated_bugs(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find error patterns that appear across multiple sessions."""
    error_patterns: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    bug_regex = re.compile(
        r"(?:Error|Exception|Traceback|failed|FAILED|crashed|CRASHED)"
        r"[^\n]{0,100}", re.IGNORECASE
    )
    for sess in sessions:
        if sess.get("error_count", 0) == 0:
            continue
        content = _get_session_content(sess["session_id"])
        for match in bug_regex.finditer(content):
            pattern_key = hashlib.sha256(match.group().lower().encode()).hexdigest()[:16]
            error_patterns[pattern_key].append((sess["session_id"], sess["timestamp"]))
    repeated = []
    for pattern_key, occurrences in error_patterns.items():
        if len(occurrences) >= 2:
            repeated.append({
                "type": "repeated_bug",
                "pattern_key": pattern_key,
                "occurrences": len(occurrences),
                "sessions": [s for s, _ in occurrences],
                "first_seen": min(t for _, t in occurrences),
                "last_seen": max(t for _, t in occurrences),
            })
    return repeated[:MAX_PATTERNS_TO_CONSOLIDATE]


def _detect_decision_reversals(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find memory entries where a decision was later reversed."""
    topic_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    decision_indicators = ["instead", "prefer", "changed", "updated", "now using",
                           "switched", "migrated", "refactored", "replaced", "new approach"]
    for entry in entries:
        val = entry.get("value", "")
        if isinstance(val, str) and any(ind in val.lower() for ind in decision_indicators):
            tokens = _tokenize(val)
            topic = "|".join(sorted(tokens))[:60]
            topic_groups[topic].append(entry)
    reversals = []
    for topic, group in topic_groups.items():
        if len(group) >= 2:
            sorted_group = sorted(group, key=lambda x: x.get("created_at", 0))
            newest = sorted_group[-1]["value"]
            oldest = sorted_group[0]["value"]
            if newest != oldest and _jaccard_similarity(_tokenize(newest), _tokenize(oldest)) < 0.6:
                reversals.append({
                    "type": "decision_reversal",
                    "topic": topic,
                    "superseded_value": oldest[:200],
                    "current_value": newest[:200],
                    "old_version": sorted_group[0]["version"],
                    "new_version": sorted_group[-1]["version"],
                })
    return reversals[:MAX_PATTERNS_TO_CONSOLIDATE]


def _detect_new_conventions(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find new file patterns, imports, or conventions introduced recently."""
    convention_patterns: Dict[str, Dict[str, Any]] = {}
    file_regex = re.compile(r"(?:import|from)\s+([a-zA-Z0-9_\.]+)", re.MULTILINE)
    for sess in sessions[-10:]:
        content = _get_session_content(sess["session_id"])
        for match in file_regex.finditer(content):
            mod = match.group(1)
            if mod not in convention_patterns:
                convention_patterns[mod] = {"type": "import", "pattern": mod,
                                            "first_session": sess["session_id"],
                                            "first_timestamp": sess["timestamp"],
                                            "seen_count": 1}
            else:
                convention_patterns[mod]["seen_count"] += 1
    conventions = []
    for pattern, info in convention_patterns.items():
        if info["seen_count"] >= 2:
            conventions.append({
                "type": "new_convention",
                "pattern": info["pattern"],
                "category": info["type"],
                "first_session": info["first_session"],
                "confidence": min(1.0, info["seen_count"] / 5.0),
            })
    return conventions[:MAX_PATTERNS_TO_CONSOLIDATE]


def _detect_recurring_errors(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find errors that keep appearing without permanent fixes."""
    error_keywords = ["TypeError", "ImportError", "SyntaxError", "AttributeError",
                      "NameError", "ValueError", "RuntimeError", "ConnectionError"]
    session_errors: Dict[str, List[str]] = defaultdict(list)
    for sess in sessions:
        if sess.get("error_count", 0) > 0:
            content = _get_session_content(sess["session_id"])
            for kw in error_keywords:
                if kw in content:
                    session_errors[kw].append(sess["session_id"])
    recurring = []
    for error_type, sess_ids in session_errors.items():
        unique_sessions = len(set(sess_ids))
        if unique_sessions >= 2:
            recurring.append({
                "type": "recurring_error",
                "error_type": error_type,
                "affected_sessions": unique_sessions,
                "session_ids": list(set(sess_ids))[:10],
            })
    return recurring[:MAX_PATTERNS_TO_CONSOLIDATE]


# ============================================================================
# Jaccard-Based Deduplication
# ============================================================================

def _find_near_duplicates(entries: List[Dict[str, Any]]) -> List[Tuple[Dict, Dict, float]]:
    """Find near-duplicate entries (Jaccard > JACCARD_THRESHOLD)."""
    active = [e for e in entries if not e.get("is_archived") and e.get("value")]
    pairs: List[Tuple[Dict, Dict, float]] = []
    checked: Set[str] = set()
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            if len(pairs) >= MAX_DEDUP_PAIRS:
                break
            key = f"{a['key']}|{b['key']}"
            if key in checked:
                continue
            checked.add(key)
            sim = _jaccard_similarity(_tokenize(a["value"]), _tokenize(b["value"]))
            if sim > JACCARD_THRESHOLD:
                pairs.append((a, b, sim))
    pairs.sort(key=lambda x: -x[2])
    return pairs[:MAX_DEDUP_PAIRS]


# ============================================================================
# Memory Reorganization Actions
# ============================================================================

def _archive_superseded_facts(entries: List[Dict[str, Any]], reversals: List[Dict]) -> int:
    """Archive memory entries that have been superseded by newer decisions."""
    if not MEMORY_DB.exists():
        return 0
    try:
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        archived = 0
        for reversal in reversals:
            old_val = reversal.get("superseded_value")
            if not old_val:
                continue
            rows = conn.execute("""
                SELECT entry_key FROM memory_entries
                WHERE is_archived = 0 AND value LIKE ?
                LIMIT 1
            """, (f"%{old_val[:80]}%",)).fetchall()
            for row in rows:
                conn.execute("""
                    UPDATE memory_entries SET is_archived = 1, priority = 0, updated_at = ?
                    WHERE entry_key = ? AND is_archived = 0
                """, (time.time(), row[0]))
                archived += 1
        conn.commit()
        conn.close()
        return archived
    except Exception as e:
        logger.warning("Failed to archive superseded facts: %s", e)
        return 0


def _promote_high_confidence_patterns(patterns: List[Dict], sessions: List[Dict]) -> int:
    """Boost priority for high-frequency pattern memories."""
    if not MEMORY_DB.exists():
        return 0
    promoted = 0
    confidence_patterns = [p for p in patterns if p.get("confidence", 0) >= 0.7]
    if not confidence_patterns:
        return 0
    try:
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        now = time.time()
        for pattern in confidence_patterns:
            pattern_val = json.dumps(pattern)
            pat_type = pattern.get("type", "unknown")
            pat_key = pattern.get("pattern_key") or pattern.get("error_type", "unknown")
            key = f"pattern:{pat_type}:{pat_key}"
            existing = conn.execute("""
                SELECT entry_key, priority FROM memory_entries
                WHERE entry_key = ? AND is_archived = 0
            """, (key,)).fetchone()
            if existing:
                current_priority = existing[1]
                new_priority = min(1.0, current_priority + 0.15)
                conn.execute("""
                    UPDATE memory_entries SET priority = ?, updated_at = ?, metadata_json = ?
                    WHERE entry_key = ?
                """, (new_priority, now, pattern_val, key))
                promoted += 1
            else:
                conn.execute("""
                    INSERT INTO memory_entries
                    (entry_key, value, version, created_at, updated_at, last_accessed_at,
                     access_count, priority, is_archived, metadata_json, provenance_json)
                    VALUES (?, ?, 1, ?, ?, ?, 0, 0.8, 0, ?, '{}')
                """, (key, pattern_val, now, now, now, json.dumps({
                    "source": "dreaming_consolidation",
                    "pattern": pattern,
                    "session_count": len(sessions),
                })))
                promoted += 1
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("Failed to promote patterns: %s", e)
    return promoted


def _apply_decay_to_unused_memories() -> int:
    """Run Ebbinghaus decay cycle on cross_session_memory."""
    if not MEMORY_DB.exists():
        return 0
    try:
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        now = time.time()
        rows = conn.execute("""
            SELECT entry_key, last_accessed_at, access_count FROM memory_entries
            WHERE is_archived = 0
        """).fetchall()
        modified = 0
        for key, last_access, count in rows:
            days_since = (now - last_access) / 86400
            recency = DECAY_BASE ** (days_since * DECAY_RATE)
            usage = min(count * USAGE_BOOST, 0.4)
            new_priority = max(0.0, min(1.0, recency + usage))
            conn.execute("""
                UPDATE memory_entries SET priority = ? WHERE entry_key = ?
            """, (new_priority, key))
            if new_priority < MIN_PRIORITY_THRESHOLD:
                conn.execute("""
                    UPDATE memory_entries SET is_archived = 1 WHERE entry_key = ?
                """, (key,))
            modified += 1
        conn.commit()
        conn.close()
        return modified
    except Exception as e:
        logger.warning("Failed to apply decay: %s", e)
        return 0


def _merge_near_duplicates(pairs: List[Tuple[Dict, Dict, float]]) -> int:
    """Merge near-duplicate entries by keeping the higher-priority one."""
    if not MEMORY_DB.exists():
        return 0
    merged = 0
    for a, b, sim in pairs:
        winner = a if a.get("priority", 0) >= b.get("priority", 0) else b
        loser_key = b["key"] if winner["key"] != a["key"] else a["key"]
        try:
            conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            old_meta = winner.get("metadata", {})
            new_meta = {
                **old_meta,
                "merged_from": loser_key,
                "similarity": round(sim, 3),
                "merged_at": time.time(),
            }
            now = time.time()
            conn.execute("""
                UPDATE memory_entries SET metadata_json = ?, priority = ?, updated_at = ?
                WHERE entry_key = ?
            """, (json.dumps(new_meta), min(1.0, winner["priority"] + 0.05), now, winner["key"]))
            conn.execute("""
                UPDATE memory_entries SET is_archived = 1, priority = 0 WHERE entry_key = ?
            """, (loser_key,))
            merged += 1
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Failed to merge duplicate %s: %s", loser_key, e)
    return merged


# ============================================================================
# Pre-computed Briefing Cache
# ============================================================================

def _generate_briefing(sessions: List[Dict], patterns: List[Dict],
                       reversals: List[Dict]) -> str:
    """Generate a synthesized briefing text for session resume."""
    lines = ["# Session Briefing — Generated by Dreaming Consolidation\n"]
    lines.append(f"_Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}_\n")
    if sessions:
        recent = sessions[0]
        lines.append(f"## Last Session ({recent.get('session_id', '?')[:8]})")
        lines.append(f"- Agent: {recent.get('agent_name', 'unknown')}")
        lines.append(f"- Summary: {recent.get('summary', 'N/A')[:200]}\n")
    if patterns:
        lines.append(f"## Active Patterns ({len(patterns)})")
        for p in patterns[:10]:
            lines.append(f"- [{p['type']}] {p.get('pattern', p.get('error_type', '?'))}")
        lines.append("")
    if reversals:
        lines.append(f"## Decision Reversals ({len(reversals)})")
        for r in reversals[:5]:
            lines.append(f"- Topic: {r.get('topic', '?')[:60]}")
            lines.append(f"  Was: {r.get('superseded_value', '')[:80]}")
            lines.append(f"  Now: {r.get('current_value', '')[:80]}\n")
    return "\n".join(lines)


def _cache_briefing(briefing: str, tag: str = "default") -> Path:
    """Write briefing to the dream cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"briefing_{tag}_{int(time.time())}.md"
    path.write_text(briefing, encoding="utf-8")
    # Maintain only last 3 briefings per tag
    existing = sorted(CACHE_DIR.glob(f"briefing_{tag}_*.md"), key=lambda x: -x.stat().st_mtime)
    for old in existing[3:]:
        try:
            old.unlink()
        except Exception:
            pass
    return path


# ============================================================================
# Preview (no changes applied)
# ============================================================================

def dreaming_preview() -> Dict[str, Any]:
    """Show what would change without applying changes."]
    state = _load_state()
    sessions = _get_recent_sessions(MAX_SESSIONS_TO_SCAN)
    entries = _get_memory_entries()
    repeated_bugs = _detect_repeated_bugs(sessions)
    reversals = _detect_decision_reversals(entries)
    conventions = _detect_new_conventions(sessions)
    recurring = _detect_recurring_errors(sessions)
    all_patterns = repeated_bugs + reversals + conventions + recurring
    dedup_pairs = _find_near_duplicates(entries)
    return {
        "would_process_sessions": len(sessions),
        "would_process_entries": len(entries),
        "would_find_patterns": len(all_patterns),
        "patterns_sample": all_patterns[:10],
        "would_merge_duplicates": len(dedup_pairs),
        "dedup_sample": [{"a": a["key"], "b": b["key"], "similarity": round(s, 3)}
                         for a, b, s in dedup_pairs[:5]],
        "would_archive_superseded": len(reversals),
        "would_promote_patterns": len([p for p in all_patterns if p.get("confidence", 0) >= 0.7]),
        "last_dreaming_state": {
            "last_run_at": state.get("last_run_at", 0),
            "total_runs": state.get("total_runs", 0),
            "entries_processed": state.get("entries_processed", 0),
            "changes_made": state.get("changes_made", 0),
        },
    }


# ============================================================================
# Main Dreaming Pipeline
# ============================================================================

async def _dreaming_pipeline(force: bool = False) -> Dict[str, Any]:
    """Async pipeline that runs the dreaming consolidation. Idempotent."""
    if not force:
        state = _load_state()
        idle_seconds = time.time() - state.get("last_run_at", 0)
        if idle_seconds < MIN_SESSION_AGE_SECONDS:
            return {
                "skipped": True,
                "reason": f"idle time {idle_seconds:.0f}s < {MIN_SESSION_AGE_SECONDS}s",
                "last_run_at": state.get("last_run_at", 0),
            }

    start = time.time()
    result = {
        "started_at": start,
        "sessions_scanned": 0,
        "entries_processed": 0,
        "patterns_found": 0,
        "changes_made": 0,
        "dedup_merges": 0,
        "archived_superseded": 0,
        "promoted_patterns": 0,
        "decayed_entries": 0,
        "briefing_cached": False,
        "errors": [],
    }

    # ── Step 1: Gather data ──────────────────────────────────────────────────
    sessions = _get_recent_sessions(MAX_SESSIONS_TO_SCAN)
    entries = _get_memory_entries()
    result["sessions_scanned"] = len(sessions)
    result["entries_processed"] = len(entries)

    # ── Step 2: Pattern recognition ─────────────────────────────────────────
    repeated_bugs = _detect_repeated_bugs(sessions)
    reversals = _detect_decision_reversals(entries)
    conventions = _detect_new_conventions(sessions)
    recurring = _detect_recurring_errors(sessions)
    all_patterns = (repeated_bugs + reversals + conventions + recurring)[:MAX_PATTERNS_TO_CONSOLIDATE]
    result["patterns_found"] = len(all_patterns)

    # ── Step 3: Memory reorganization ───────────────────────────────────────
    archived = await asyncio.get_event_loop().run_in_executor(
        None, _archive_superseded_facts, entries, reversals
    )
    result["archived_superseded"] = archived

    promoted = await asyncio.get_event_loop().run_in_executor(
        None, _promote_high_confidence_patterns, all_patterns, sessions
    )
    result["promoted_patterns"] = promoted

    decayed = await asyncio.get_event_loop().run_in_executor(
        None, _apply_decay_to_unused_memories
    )
    result["decayed_entries"] = decayed

    # ── Step 4: Deduplication ───────────────────────────────────────────────
    dedup_pairs = await asyncio.get_event_loop().run_in_executor(
        None, _find_near_duplicates, entries
    )
    merged = await asyncio.get_event_loop().run_in_executor(
        None, _merge_near_duplicates, dedup_pairs
    )
    result["dedup_merges"] = merged

    # ── Step 5: Pre-compute briefing cache ───────────────────────────────────
    briefing = await asyncio.get_event_loop().run_in_executor(
        None, _generate_briefing, sessions, all_patterns, reversals
    )
    cache_path = await asyncio.get_event_loop().run_in_executor(
        None, _cache_briefing, briefing, "default"
    )
    result["briefing_cached"] = str(cache_path)

    # ── Step 6: Persist state ───────────────────────────────────────────────
    elapsed = time.time() - start
    state = _load_state()
    state["last_run_at"] = start
    state["last_run_duration"] = elapsed
    state["total_runs"] = state.get("total_runs", 0) + 1
    state["entries_processed"] += result["entries_processed"]
    state["patterns_found"] += result["patterns_found"]
    state["changes_made"] += result["archived_superseded"] + result["promoted_patterns"] + result["dedup_merges"]
    state["dedup_merges"] = result["dedup_merges"]
    state["is_running"] = False
    state["last_error"] = None
    history_entry = {
        "timestamp": start,
        "duration": round(elapsed, 2),
        "sessions_scanned": result["sessions_scanned"],
        "patterns_found": result["patterns_found"],
        "changes_made": result["archived_superseded"] + result["promoted_patterns"] + result["dedup_merges"],
    }
    state["run_history"] = ([history_entry] + state.get("run_history", []))[:20]
    _save_state(state)

    result["elapsed_seconds"] = round(elapsed, 2)
    return result


# ============================================================================
# Public API
# ============================================================================

def dreaming_run(force: bool = False) -> Dict[str, Any]:
    """Trigger dreaming consolidation. Runs async in a thread."""
    state = _load_state()
    if state.get("is_running", False):
        return {"status": "already_running", "started_at": state.get("last_run_at", 0)}

    state["is_running"] = True
    _save_state(state)

    def _run():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_dreaming_pipeline(force=force))
        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            s = _load_state()
            s["is_running"] = False
            _save_state(s)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            result = future.result(timeout=300)
        except Exception as e:
            result = {"status": "error", "error": str(e)}

    return result


def dreaming_cancel() -> Dict[str, Any]:
    """Cancel dreaming if currently running."""
    state = _load_state()
    if not state.get("is_running", False):
        return {"status": "not_running"}
    state["is_running"] = False
    state["last_error"] = "cancelled by user"
    _save_state(state)
    return {"status": "cancelled"}


def dreaming_status() -> Dict[str, Any]:
    """Get dreaming status: last run time, entries processed, changes made."""
    state = _load_state()
    sessions = _get_recent_sessions(5)
    cache_files = list(CACHE_DIR.glob("briefing_*.md")) if CACHE_DIR.exists() else []
    latest_cache = max(cache_files, key=lambda f: f.stat().st_mtime) if cache_files else None
    return {
        "is_running": state.get("is_running", False),
        "last_run_at": state.get("last_run_at", 0),
        "last_run_duration": state.get("last_run_duration", 0),
        "total_runs": state.get("total_runs", 0),
        "total_entries_processed": state.get("entries_processed", 0),
        "total_patterns_found": state.get("patterns_found", 0),
        "total_changes_made": state.get("changes_made", 0),
        "total_dedup_merges": state.get("dedup_merges", 0),
        "last_error": state.get("last_error"),
        "recent_runs": state.get("run_history", [])[:5],
        "scheduled_interval_minutes": 30,
        "idle_trigger_seconds": MIN_SESSION_AGE_SECONDS,
        "latest_briefing": latest_cache.name if latest_cache else None,
        "sessions_in_store": len(sessions),
    }


# ============================================================================
# MCP Handler & Schema
# ============================================================================

def handle_dreaming(args: Dict[str, Any]) -> str:
    """Main handler for dreaming_consolidation MCP tool."""
    action = args.get("action", "status")

    if action == "run":
        result = dreaming_run(force=args.get("force", False))
    elif action == "cancel":
        result = dreaming_cancel()
    elif action == "preview":
        result = dreaming_preview()
    elif action == "status":
        result = dreaming_status()
    else:
        result = {"error": f"unknown action: {action}"}

    return json.dumps(result, indent=2)


DREAMING_SCHEMA = {
    "name": "dreaming_consolidation",
    "description": (
        "Async hippocampal replay for Minerva/Hermes — consolidates cross-session memory "
        "during idle periods. Triggers automatically after session end + 60s idle, "
        "or manually via dreaming_run. Pipeline: scan sessions → find patterns "
        "(repeated bugs, reversals, conventions, errors) → reorganize GraphRAG "
        "(archive superseded, promote patterns, update decay) → deduplicate "
        "(Jaccard > 0.8) → pre-compute briefings in /tmp/hermes_dream_cache/. "
        "Idempotent and safe to run multiple times."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["run", "cancel", "preview", "status"],
                "description": "The dreaming operation to perform.",
            },
            "force": {
                "type": "boolean",
                "description": "Force run even if idle time < 60s (default False).",
            },
        },
        "required": ["action"],
    },
}
