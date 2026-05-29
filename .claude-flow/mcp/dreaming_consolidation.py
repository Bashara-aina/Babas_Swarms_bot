#!/usr/bin/env python3
"""
Dreaming Consolidation — Hippocampal replay for Minerva/Hermes.
Max 450 lines. Async background reorganizing memory between sessions.
Triggers: session end + idle>60s | manual dreaming_run(force=True) | every 30min.
"""
import asyncio, concurrent.futures, hashlib, json, logging, os, re, sqlite3, time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
STATE_FILE = Path("/tmp/hermes_dreaming_state.json")
CACHE_DIR = Path("/tmp/hermes_dream_cache")
FTS_DB = HERMES_HOME / "sessions" / "fts.db"
MEMORY_DB = HERMES_HOME / "memories" / "cross_session_memory.db"

DECAY_BASE, DECAY_RATE, USAGE_BOOST, MIN_PRI = 0.5, 0.1, 0.05, 0.1  # Ebbinghaus constants
JACCARD = 0.8  # dedup threshold
MIN_IDLE = 60  # idle trigger seconds
MAX_SESSIONS, MAX_PATTERNS, MAX_DEDUP = 50, 100, 50

# ============================================================================
# State
# ============================================================================

_DEFAULT = {"last_run_at": 0.0, "last_run_duration": 0.0, "total_runs": 0,
           "entries_processed": 0, "changes_made": 0, "patterns_found": 0,
           "dedup_merges": 0, "last_error": None, "is_running": False, "run_history": []}

def _load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return _DEFAULT.copy()
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return _DEFAULT.copy()

def _save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ============================================================================
# Session Access (read-only)
# ============================================================================

def _get_recent_sessions(limit: int = MAX_SESSIONS) -> List[Dict[str, Any]]:
    if not FTS_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(FTS_DB), check_same_thread=False)
        conn.execute("PRAGMA query_only=ON")
        rows = conn.execute("SELECT session_id, timestamp, agent_name, parent_session_id, summary, tool_calls, error_count, message_count FROM sessions_fts ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [{"session_id": r[0], "timestamp": r[1], "agent_name": r[2], "parent_session_id": r[3], "summary": r[4], "tool_calls": r[5], "error_count": r[6], "message_count": r[7]} for r in rows]
    except Exception as e:
        logger.warning("Read sessions failed: %s", e)
        return []

def _session_content(session_id: str) -> str:
    for f in sorted((HERMES_HOME / "sessions").glob("session_*.json"), key=lambda x: -x.stat().st_mtime):
        try:
            data = json.loads(f.read_text())
            if data.get("session_id") == session_id:
                msgs = data.get("messages", [])
                return " ".join(m.get("content", "") for m in msgs[-50:] if isinstance(m.get("content"), str))
        except Exception:
            pass
    return ""


# ============================================================================
# Memory Access (read-only)
# ============================================================================

def _get_memory_entries(include_archived: bool = False) -> List[Dict[str, Any]]:
    if not MEMORY_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("PRAGMA query_only=ON")
        q = "SELECT entry_key, value, version, created_at, updated_at, last_accessed_at, access_count, priority, is_archived, metadata_json, provenance_json FROM memory_entries"
        if not include_archived:
            q += " WHERE is_archived = 0"
        rows = conn.execute(q).fetchall()
        conn.close()
        return [{"key": r[0], "value": r[1], "priority": round(r[7], 4), "is_archived": bool(r[8]),
                 "metadata": json.loads(r[9] or "{}"), "created_at": r[3], "version": r[2]} for r in rows]
    except Exception as e:
        logger.warning("Read memory entries failed: %s", e)
        return []


# ============================================================================
# Pattern Recognition (no LLM)
# ============================================================================

def _tokenize(text: str) -> Set[str]:
    return {t for t in re.sub(r"[^a-z0-9\s]", " ", text.lower()).split() if len(t) > 2}

def _jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0

def _detect_repeated_bugs(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    error_patterns: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    bug_regex = re.compile(r"(?:Error|Exception|Traceback|failed|FAILED|crashed|CRASHED)[^\n]{0,100}", re.IGNORECASE)
    for sess in sessions:
        if sess.get("error_count", 0) == 0:
            continue
        for match in bug_regex.finditer(_session_content(sess["session_id"])):
            pk = hashlib.sha256(match.group().lower().encode()).hexdigest()[:16]
            error_patterns[pk].append((sess["session_id"], sess["timestamp"]))
    return [{"type": "repeated_bug", "pattern_key": pk, "occurrences": len(occ),
             "sessions": [s for s, _ in occ], "first_seen": min(t for _, t in occ), "last_seen": max(t for _, t in occ)}
            for pk, occ in error_patterns.items() if len(occ) >= 2][:MAX_PATTERNS]

def _detect_decision_reversals(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    topic_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        val = entry.get("value", "")
        if isinstance(val, str) and any(ind in val.lower() for ind in ["instead", "prefer", "changed", "updated", "now using", "switched", "migrated", "refactored", "replaced", "new approach"]):
            topic = "|".join(sorted(_tokenize(val)))[:60]
            topic_groups[topic].append(entry)
    reversals = []
    for topic, group in topic_groups.items():
        if len(group) >= 2:
            sg = sorted(group, key=lambda x: x.get("created_at", 0))
            newest, oldest = sg[-1]["value"], sg[0]["value"]
            if newest != oldest and _jaccard(_tokenize(newest), _tokenize(oldest)) < 0.6:
                reversals.append({"type": "decision_reversal", "topic": topic,
                                  "superseded_value": oldest[:200], "current_value": newest[:200]})
    return reversals[:MAX_PATTERNS]

def _detect_new_conventions(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    patterns: Dict[str, Dict[str, Any]] = {}
    for sess in sessions[-10:]:
        for match in re.finditer(r"(?:import|from)\s+([a-zA-Z0-9_\.]+)", _session_content(sess["session_id"])):
            mod = match.group(1)
            if mod not in patterns:
                patterns[mod] = {"pattern": mod, "first_session": sess["session_id"], "seen_count": 1}
            else:
                patterns[mod]["seen_count"] += 1
    return [{"type": "new_convention", "pattern": info["pattern"],
             "first_session": info["first_session"], "confidence": min(1.0, info["seen_count"] / 5.0)}
            for info in patterns.values() if info["seen_count"] >= 2][:MAX_PATTERNS]

def _detect_recurring_errors(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    session_errors: Dict[str, Set[str]] = defaultdict(set)
    for sess in sessions:
        if sess.get("error_count", 0) > 0:
            content = _session_content(sess["session_id"])
            for kw in ["TypeError", "ImportError", "SyntaxError", "AttributeError", "NameError", "ValueError", "RuntimeError", "ConnectionError"]:
                if kw in content:
                    session_errors[kw].add(sess["session_id"])
    return [{"type": "recurring_error", "error_type": et, "affected_sessions": len(sids), "session_ids": list(sids)[:10]}
            for et, sids in session_errors.items() if len(sids) >= 2][:MAX_PATTERNS]

def _find_near_duplicates(entries: List[Dict[str, Any]]) -> List[Tuple[Dict, Dict, float]]:
    active = [e for e in entries if not e.get("is_archived") and e.get("value")]
    pairs, checked = [], set()
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            if len(pairs) >= MAX_DEDUP:
                break
            key = f"{a['key']}|{b['key']}"
            if key not in checked:
                checked.add(key)
                sim = _jaccard(_tokenize(a["value"]), _tokenize(b["value"]))
                if sim > JACCARD:
                    pairs.append((a, b, sim))
    pairs.sort(key=lambda x: -x[2])
    return pairs[:MAX_DEDUP]


# ============================================================================
# Memory Reorganization
# ============================================================================

def _archive_superseded(reversals: List[Dict]) -> int:
    if not MEMORY_DB.exists():
        return 0
    try:
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        archived = 0
        for rev in reversals:
            old_val = rev.get("superseded_value")
            if not old_val:
                continue
            row = conn.execute("SELECT entry_key FROM memory_entries WHERE is_archived = 0 AND value LIKE ? LIMIT 1", (f"%{old_val[:80]}%",)).fetchone()
            if row:
                conn.execute("UPDATE memory_entries SET is_archived = 1, priority = 0, updated_at = ? WHERE entry_key = ? AND is_archived = 0", (time.time(), row[0]))
                archived += 1
        conn.commit()
        conn.close()
        return archived
    except Exception as e:
        logger.warning("Archive superseded failed: %s", e)
        return 0

def _promote_patterns(patterns: List[Dict], session_count: int) -> int:
    if not MEMORY_DB.exists():
        return 0
    confident = [p for p in patterns if p.get("confidence", 0) >= 0.7]
    if not confident:
        return 0
    try:
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        now = time.time()
        promoted = 0
        for p in confident:
            pv, pt, pk = json.dumps(p), p.get("type", "unknown"), p.get("pattern_key") or p.get("error_type", "unknown")
            key = f"pattern:{pt}:{pk}"
            row = conn.execute("SELECT priority FROM memory_entries WHERE entry_key = ? AND is_archived = 0", (key,)).fetchone()
            if row:
                conn.execute("UPDATE memory_entries SET priority = ?, updated_at = ?, metadata_json = ? WHERE entry_key = ?", (min(1.0, row[0] + 0.15), now, pv, key))
                promoted += 1
            else:
                conn.execute("INSERT INTO memory_entries (entry_key, value, version, created_at, updated_at, last_accessed_at, access_count, priority, is_archived, metadata_json, provenance_json) VALUES (?, ?, 1, ?, ?, ?, 0, 0.8, 0, ?, '{}')", (key, pv, now, now, now, json.dumps({"source": "dreaming", "pattern": p, "session_count": session_count})))
                promoted += 1
        conn.commit()
        conn.close()
        return promoted
    except Exception as e:
        logger.warning("Promote patterns failed: %s", e)
        return 0

def _apply_decay() -> int:
    if not MEMORY_DB.exists():
        return 0
    try:
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        now, modified = time.time(), 0
        for key, last_acc, count in conn.execute("SELECT entry_key, last_accessed_at, access_count FROM memory_entries WHERE is_archived = 0").fetchall():
            days = (now - last_acc) / 86400
            new_p = max(0.0, min(1.0, DECAY_BASE ** (days * DECAY_RATE) + min(count * USAGE_BOOST, 0.4)))
            conn.execute("UPDATE memory_entries SET priority = ? WHERE entry_key = ?", (new_p, key))
            if new_p < MIN_PRI:
                conn.execute("UPDATE memory_entries SET is_archived = 1 WHERE entry_key = ?", (key,))
            modified += 1
        conn.commit()
        conn.close()
        return modified
    except Exception as e:
        logger.warning("Apply decay failed: %s", e)
        return 0

def _merge_duplicates(pairs: List[Tuple[Dict, Dict, float]]) -> int:
    if not MEMORY_DB.exists():
        return 0
    merged = 0
    for a, b, sim in pairs:
        winner = a if a.get("priority", 0) >= b.get("priority", 0) else b
        loser = b["key"] if winner["key"] != a["key"] else a["key"]
        try:
            conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            now = time.time()
            conn.execute("UPDATE memory_entries SET metadata_json = ?, priority = ?, updated_at = ? WHERE entry_key = ?", (json.dumps({**winner.get("metadata", {}), "merged_from": loser, "similarity": round(sim, 3), "merged_at": now}), min(1.0, winner["priority"] + 0.05), now, winner["key"]))
            conn.execute("UPDATE memory_entries SET is_archived = 1, priority = 0 WHERE entry_key = ?", (loser,))
            merged += 1
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Merge %s failed: %s", loser, e)
    return merged


# ============================================================================
# Briefing
# ============================================================================

def _generate_briefing(sessions: List[Dict], patterns: List[Dict], reversals: List[Dict]) -> str:
    lines = [f"# Session Briefing — {time.strftime('%Y-%m-%d %H:%M:%S')}\n"]
    if sessions:
        rs = sessions[0]
        lines.extend([f"## Last Session ({rs.get('session_id', '?')[:8]})", f"- Agent: {rs.get('agent_name', 'unknown')}", f"- Summary: {rs.get('summary', 'N/A')[:200]}\n"])
    if patterns:
        lines.append(f"## Active Patterns ({len(patterns)})")
        for p in patterns[:10]:
            lines.append(f"- [{p['type']}] {p.get('pattern', p.get('error_type', '?'))}")
    if reversals:
        lines.append(f"## Decision Reversals ({len(reversals)})")
        for r in reversals[:5]:
            lines.append(f"- {r.get('topic', '?')[:60]}: was={r.get('superseded_value', '')[:60]}, now={r.get('current_value', '')[:60]}")
    return "\n".join(lines)

def _cache_briefing(briefing: str, tag: str = "default") -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"briefing_{tag}_{int(time.time())}.md"
    path.write_text(briefing)
    for old in sorted(CACHE_DIR.glob(f"briefing_{tag}_*.md"), key=lambda x: -x.stat().st_mtime)[3:]:
        try:
            old.unlink()
        except Exception:
            pass
    return path


# ============================================================================
# Preview
# ============================================================================

def dreaming_preview() -> Dict[str, Any]:
    state = _load_state()
    sessions = _get_recent_sessions()
    entries = _get_memory_entries()
    bugs = _detect_repeated_bugs(sessions)
    revs = _detect_decision_reversals(entries)
    convs = _detect_new_conventions(sessions)
    recs = _detect_recurring_errors(sessions)
    all_p = (bugs + revs + convs + recs)[:MAX_PATTERNS]
    dups = _find_near_duplicates(entries)
    return {"would_process_sessions": len(sessions), "would_process_entries": len(entries),
            "would_find_patterns": len(all_p), "patterns_sample": all_p[:10],
            "would_merge_duplicates": len(dups), "dedup_sample": [{"a": a["key"], "b": b["key"], "sim": round(s, 3)} for a, b, s in dups[:5]],
            "would_archive_superseded": len(revs), "would_promote_patterns": len([p for p in all_p if p.get("confidence", 0) >= 0.7]),
            "last_dreaming_state": {"last_run_at": state.get("last_run_at", 0), "total_runs": state.get("total_runs", 0),
                                    "entries_processed": state.get("entries_processed", 0), "changes_made": state.get("changes_made", 0)}}


# ============================================================================
# Async Pipeline
# ============================================================================

async def _pipeline(force: bool = False) -> Dict[str, Any]:
    if not force:
        st = _load_state()
        idle = time.time() - st.get("last_run_at", 0)
        if idle < MIN_IDLE:
            return {"skipped": True, "reason": f"idle {idle:.0f}s < {MIN_IDLE}s", "last_run_at": st.get("last_run_at", 0)}
    start = time.time()
    res = {"started_at": start, "sessions_scanned": 0, "entries_processed": 0, "patterns_found": 0,
           "archived_superseded": 0, "promoted_patterns": 0, "decayed_entries": 0, "dedup_merges": 0, "briefing_cached": False}

    sessions = _get_recent_sessions()
    entries = _get_memory_entries()
    res["sessions_scanned"] = len(sessions)
    res["entries_processed"] = len(entries)

    bugs = _detect_repeated_bugs(sessions)
    revs = _detect_decision_reversals(entries)
    convs = _detect_new_conventions(sessions)
    recs = _detect_recurring_errors(sessions)
    all_p = (bugs + revs + convs + recs)[:MAX_PATTERNS]
    res["patterns_found"] = len(all_p)

    loop = asyncio.get_event_loop()
    res["archived_superseded"] = await loop.run_in_executor(None, _archive_superseded, revs)
    res["promoted_patterns"] = await loop.run_in_executor(None, _promote_patterns, all_p, len(sessions))
    res["decayed_entries"] = await loop.run_in_executor(None, _apply_decay)
    dups = await loop.run_in_executor(None, _find_near_duplicates, entries)
    res["dedup_merges"] = await loop.run_in_executor(None, _merge_duplicates, dups)
    brief = await loop.run_in_executor(None, _generate_briefing, sessions, all_p, revs)
    cache_path = await loop.run_in_executor(None, _cache_briefing, brief, "default")
    res["briefing_cached"] = str(cache_path)

    elapsed = time.time() - start
    chg = res["archived_superseded"] + res["promoted_patterns"] + res["dedup_merges"]
    st = _load_state()
    st.update({"last_run_at": start, "last_run_duration": elapsed, "total_runs": st.get("total_runs", 0) + 1,
               "entries_processed": st.get("entries_processed", 0) + res["entries_processed"],
               "patterns_found": st.get("patterns_found", 0) + res["patterns_found"],
               "changes_made": st.get("changes_made", 0) + chg, "dedup_merges": res["dedup_merges"],
               "is_running": False, "last_error": None,
               "run_history": ([{"timestamp": start, "duration": round(elapsed, 2), "sessions_scanned": res["sessions_scanned"],
                                  "patterns_found": res["patterns_found"], "changes_made": chg}]
                               + st.get("run_history", []))[:20]})
    _save_state(st)
    res["elapsed_seconds"] = round(elapsed, 2)
    return res


# ============================================================================
# Public API
# ============================================================================

def dreaming_run(force: bool = False) -> Dict[str, Any]:
    state = _load_state()
    if state.get("is_running", False):
        return {"status": "already_running", "started_at": state.get("last_run_at", 0)}
    state["is_running"] = True
    _save_state(state)

    def _run():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_pipeline(force=force))
        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            s = _load_state()
            s["is_running"] = False
            _save_state(s)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        try:
            result = ex.submit(_run).result(timeout=300)
        except Exception as e:
            result = {"status": "error", "error": str(e)}
    return result

def dreaming_cancel() -> Dict[str, Any]:
    state = _load_state()
    if not state.get("is_running", False):
        return {"status": "not_running"}
    state.update({"is_running": False, "last_error": "cancelled by user"})
    _save_state(state)
    return {"status": "cancelled"}

def dreaming_status() -> Dict[str, Any]:
    state = _load_state()
    sessions = _get_recent_sessions(5)
    cache_files = list(CACHE_DIR.glob("briefing_*.md")) if CACHE_DIR.exists() else []
    latest = max(cache_files, key=lambda f: f.stat().st_mtime) if cache_files else None
    return {"is_running": state.get("is_running", False), "last_run_at": state.get("last_run_at", 0),
            "last_run_duration": state.get("last_run_duration", 0), "total_runs": state.get("total_runs", 0),
            "total_entries_processed": state.get("entries_processed", 0), "total_patterns_found": state.get("patterns_found", 0),
            "total_changes_made": state.get("changes_made", 0), "total_dedup_merges": state.get("dedup_merges", 0),
            "last_error": state.get("last_error"), "recent_runs": state.get("run_history", [])[:5],
            "scheduled_interval_minutes": 30, "idle_trigger_seconds": MIN_IDLE,
            "latest_briefing": latest.name if latest else None, "sessions_in_store": len(sessions)}


# ============================================================================
# MCP Handler & Schema
# ============================================================================

def handle_dreaming(args: Dict[str, Any]) -> str:
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
    "description": "Async hippocampal replay. Triggers: session end + 60s idle | manual force | 30min-scheduled. Pipeline: scan sessions → find patterns → archive superseded/promote/decay → Jaccard deduplicate → cache briefing.",
    "parameters": {
        "type": "object",
        "properties": {"action": {"type": "string", "enum": ["run", "cancel", "preview", "status"]},
                      "force": {"type": "boolean"}},
        "required": ["action"],
    },
}
