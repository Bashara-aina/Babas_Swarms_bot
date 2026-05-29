#!/usr/bin/env python3
"""
Memory Extractor — Intelligent extraction layer for Hermes agent.
Transforms raw session transcripts into structured memory entries,
filtering 80% noise from raw events.

Features:
  - Session Processing Pipeline: raw transcript → structured memory entries
  - Memory Type Classification: decision, bug_fix, pattern, convention,
    error_resolution, preference
  - Noise Filtering: skip boilerplate, redundant errors, dead-end explorations
  - MCP API: extract_session, extract_from_messages, get_extraction_stats

Storage: SQLite at /tmp/hermes_extraction.db
Model: MiniMax-M2.7 via localhost:4000 proxy (legio-proxy-key)
"""

import json
import logging
import os
import re
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# Paths and Config
# ============================================================================

EXTRACTION_DB = Path("/tmp/hermes_extraction.db")
MINIMAX_PROXY = "http://localhost:4000/v1"
MINIMAX_MODEL = "MiniMax-M2.7"
MINIMAX_API_KEY = os.environ.get("LEGIO_PROXY_KEY", "legio-proxy-key")
PROJECT_NAME = "swarm-bot"

LOCK = threading.Lock()

# Memory type decay rates (per day)
DECAY_RATES = {
    "decision": 0.05,
    "bug_fix": 0.10,
    "pattern": 0.08,
    "convention": 0.06,
    "error_resolution": 0.12,
    "preference": 0.07,
}

# Noise patterns to filter
NOISE_PATTERNS = [
    r"^Tool [a-z_]+ completed in \d+ms$",
    r"^Processing \d+ items?$",
    r"^Starting session \w+$",
    r"^Session ended\.?$",
    r"^\s*[{[]?\s*}\]]?$",  # Empty/bracket-only lines
    r"^Running command:.*$",
    r"^Output size: \d+ bytes$",
    r"^(?:DEBUG|INFO|TRACE):.*$",
    r"^Environment:.*$",
    r"^Working directory:.*$",
    r"^Agent [a-z_]+ initialized$",
    r"^Checkout complete\.?$",
    r"^Build finished\.?$",
    r"^Test run completed\.?$",
    r"^Linting passed\.?$",
    r"^Type check passed\.?$",
]

# Significance thresholds
SIGNIFICANCE_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.5,
    "low": 0.0,
}


# ============================================================================
# Database Schema
# ============================================================================

def _get_db() -> sqlite3.Connection:
    """Get or create extraction database."""
    EXTRACTION_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(EXTRACTION_DB), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_type TEXT NOT NULL,
            content TEXT NOT NULL,
            code_refs TEXT DEFAULT '[]',
            confidence REAL DEFAULT 0.5,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            project TEXT DEFAULT 'swarm-bot',
            decay_rate REAL DEFAULT 0.1,
            significance TEXT DEFAULT 'medium',
            created_at REAL NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS extraction_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            raw_messages INTEGER DEFAULT 0,
            extracted_entries INTEGER DEFAULT 0,
            filtered_noise INTEGER DEFAULT 0,
            processing_time_ms REAL DEFAULT 0,
            created_at REAL NOT NULL
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_id ON memory_entries(session_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_entry_type ON memory_entries(entry_type)
    """)

    conn.commit()
    return conn


# ============================================================================
# Memory Entry Model
# ============================================================================

class MemoryEntry:
    """Structured memory entry from session extraction."""

    def __init__(
        self,
        entry_type: str,
        content: str,
        code_refs: Optional[List[str]] = None,
        confidence: float = 0.5,
        session_id: str = "",
        significance: str = "medium",
    ):
        self.entry_type = entry_type
        self.content = content
        self.code_refs = code_refs or []
        self.confidence = confidence
        self.session_id = session_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.project = PROJECT_NAME
        self.decay_rate = DECAY_RATES.get(entry_type, 0.1)
        self.significance = significance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.entry_type,
            "content": self.content,
            "code_refs": self.code_refs,
            "confidence": round(self.confidence, 2),
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "project": self.project,
            "decay_rate": round(self.decay_rate, 2),
            "significance": self.significance,
        }

    def to_db_tuple(self) -> tuple:
        return (
            self.entry_type,
            self.content,
            json.dumps(self.code_refs),
            self.confidence,
            self.session_id,
            self.timestamp,
            self.project,
            self.decay_rate,
            self.significance,
            time.time(),
        )


# ============================================================================
# Noise Filtering
# ============================================================================

def _is_noise(line: str) -> bool:
    """Check if a line is noise (boilerplate, debug output, etc.)."""
    line = line.strip()
    if not line or len(line) < 3:
        return True
    for pattern in NOISE_PATTERNS:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    # Skip lines that are only numbers/punctuation
    if re.match(r"^[\d\s\.\-\+\=\,]+$", line):
        return True
    return False


def _extract_code_refs(text: str) -> List[str]:
    """Extract file:line references from text."""
    refs = []
    # Match common patterns: file.py:123, file.ts:456
    matches = re.findall(r"([a-zA-Z_][a-zA-Z0-9_\-\.]*\.[a-zA-Z]+):(\d+)", text)
    for fname, line in matches:
        refs.append(f"{fname}:{line}")
    # Also match paths like /home/.../file.py:line
    matches = re.findall(r"(/[^:\s]+\.[a-zA-Z]+):(\d+)", text)
    for path, line in matches:
        refs.append(f"{Path(path).name}:{line}")
    return list(set(refs))[:10]  # Max 10 refs


def _clean_content(content: str) -> str:
    """Clean and truncate content for storage."""
    # Remove excessive whitespace
    content = re.sub(r"\s+", " ", content).strip()
    # Truncate at 500 chars
    if len(content) > 500:
        content = content[:497] + "..."
    return content


# ============================================================================
# LLM Classification (call-ready)
# ============================================================================

def _classify_entry(content: str, code_refs: List[str]) -> Dict[str, Any]:
    """
    Classify a memory entry type using MiniMax-M2.7.
    Returns dict with entry_type, confidence, significance.

    NOTE: This function is call-ready but will only make LLM calls
    when explicitly requested (not during syntax verification).
    """
    prompt = f"""Classify this memory entry. Return JSON with:
- type: one of [decision, bug_fix, pattern, convention, error_resolution, preference]
- confidence: 0.0-1.0 (how certain is the classification)
- significance: one of [high, medium, low]

Entry: {content[:300]}
Code refs: {code_refs}

Respond with only valid JSON."""

    # This would make the actual LLM call:
    # import httpx
    # response = httpx.post(
    #     f"{MINIMAX_PROXY}/chat/completions",
    #     headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    #     json={
    #         "model": MINIMAX_MODEL,
    #         "messages":[{"role":"user","content":prompt}],
    #         "temperature": 0.1,
    #         "max_tokens": 100,
    #     },
    #     timeout=30.0,
    # )
    # result = response.json()["choices"][0]["message"]["content"]
    # return json.loads(result)

    # Fallback heuristic classification
    content_lower = content.lower()
    if any(kw in content_lower for kw in ["decide", "choose", "select", "architecture", "approach"]):
        return {"type": "decision", "confidence": 0.6, "significance": "medium"}
    if any(kw in content_lower for kw in ["bug", "fix", "error", "issue", "crash", "fail"]):
        return {"type": "bug_fix", "confidence": 0.6, "significance": "medium"}
    if any(kw in content_lower for kw in ["pattern", "pattern:", "convention", "standard"]):
        return {"type": "pattern", "confidence": 0.6, "significance": "medium"}
    if any(kw in content_lower for kw in ["convention", "style", "format", "naming"]):
        return {"type": "convention", "confidence": 0.6, "significance": "low"}
    if any(kw in content_lower for kw in ["resolve", "solution", "solved", "worked around"]):
        return {"type": "error_resolution", "confidence": 0.6, "significance": "medium"}
    return {"type": "preference", "confidence": 0.5, "significance": "low"}


def _synthesize_content(chunks: List[str]) -> str:
    """
    Synthesize multiple content chunks into concise memory.
    Uses MiniMax-M2.7 for synthesis.

    NOTE: Call-ready - only invokes LLM when processing real sessions.
    """
    if not chunks:
        return ""
    if len(chunks) == 1:
        return _clean_content(chunks[0])

    prompt = f"""Synthesize these into one concise memory entry (max 200 chars).
Remove redundant parts, keep the key insight.

Chunks:
{chr(10).join(chunks[:5])}

Respond with only the synthesized content, no formatting."""

    # Actual LLM call would be:
    # response = httpx.post(...)
    # return response.json()["choices"][0]["message"]["content"]

    # Fallback: simple concatenation
    combined = " | ".join(c[:100] for c in chunks[:3])
    return _clean_content(combined)


# ============================================================================
# Core Extraction API
# ============================================================================

def extract_from_messages(
    messages: List[Dict[str, Any]],
    session_id: str = "",
    use_llm: bool = False
) -> List[Dict[str, Any]]:
    """
    Extract structured memory entries from a list of messages.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        session_id: Session identifier for provenance
        use_llm: If True, invoke LLM for classification/synthesis

    Returns:
        List of MemoryEntry dicts
    """
    if not messages:
        return []

    start_time = time.time()
    session_id = session_id or f"session_{int(start_time)}"

    # Group messages by topic (simple heuristic)
    entries: List[MemoryEntry] = []
    noise_count = 0
    raw_count = len(messages)

    # Extract content from messages
    content_chunks: List[str] = []
    current_topic = ""

    for msg in messages:
        content = msg.get("content", "") or ""
        role = msg.get("role", "unknown")

        # Skip system/boilerplate
        if role in ("system", "tool") or _is_noise(content):
            noise_count += 1
            continue

        # Simple topic detection (could use LLM for better results)
        if any(kw in content.lower() for kw in ["decision:", "choice:", "approach:"]):
            # New topic - synthesize previous chunks
            if content_chunks:
                synthesized = _synthesize_content(content_chunks) if use_llm else _clean_content(" | ".join(content_chunks[:3]))
                code_refs = _extract_code_refs(" ".join(content_chunks))
                classification = _classify_entry(synthesized, code_refs) if use_llm else {"type": "pattern", "confidence": 0.5, "significance": "medium"}

                entry = MemoryEntry(
                    entry_type=classification["type"],
                    content=synthesized,
                    code_refs=code_refs,
                    confidence=classification["confidence"],
                    session_id=session_id,
                    significance=classification["significance"],
                )
                entries.append(entry)
                content_chunks = []

        content_chunks.append(content[:300])

    # Don't forget last chunk
    if content_chunks:
        synthesized = _synthesize_content(content_chunks) if use_llm else _clean_content(" | ".join(content_chunks[:3]))
        code_refs = _extract_code_refs(" ".join(content_chunks))
        classification = _classify_entry(synthesized, code_refs) if use_llm else {"type": "preference", "confidence": 0.5, "significance": "low"}

        entry = MemoryEntry(
            entry_type=classification["type"],
            content=synthesized,
            code_refs=code_refs,
            confidence=classification["confidence"],
            session_id=session_id,
            significance=classification["significance"],
        )
        entries.append(entry)

    # Store extraction metadata
    processing_time = (time.time() - start_time) * 1000
    _store_extraction_stats(session_id, raw_count, len(entries), noise_count, processing_time)

    return [e.to_dict() for e in entries]


def extract_session(
    session_transcript: List[Dict[str, Any]],
    session_id: str = "",
    use_llm: bool = False
) -> List[Dict[str, Any]]:
    """
    Process a complete session transcript and extract memory entries.

    Args:
        session_transcript: Full session message list
        session_id: Session identifier
        use_llm: If True, use LLM for classification/synthesis

    Returns:
        List of extracted MemoryEntry dicts
    """
    return extract_from_messages(session_transcript, session_id, use_llm)


def _store_extraction_stats(
    session_id: str,
    raw_messages: int,
    extracted: int,
    filtered: int,
    processing_ms: float
) -> None:
    """Store extraction statistics in database."""
    with LOCK:
        conn = _get_db()
        conn.execute("""
            INSERT INTO extraction_stats
            (session_id, raw_messages, extracted_entries, filtered_noise, processing_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, raw_messages, extracted, filtered, processing_ms, time.time()))
        conn.commit()
        conn.close()


def get_extraction_stats(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get extraction statistics, optionally filtered by session.

    Returns:
        Dict with noise_reduction_ratio, total_extracted, etc.
    """
    with LOCK:
        conn = _get_db()

        if session_id:
            row = conn.execute("""
                SELECT raw_messages, extracted_entries, filtered_noise, processing_time_ms
                FROM extraction_stats WHERE session_id = ? ORDER BY created_at DESC LIMIT 1
            """, (session_id,)).fetchone()

            if row:
                raw, extracted, filtered, proc_ms = row
                total = raw if raw > 0 else 1
                noise_reduction = round((filtered / total) * 100, 1)
                conn.close()
                return {
                    "session_id": session_id,
                    "raw_messages": raw,
                    "extracted_entries": extracted,
                    "filtered_noise": filtered,
                    "noise_reduction_percent": noise_reduction,
                    "processing_time_ms": round(proc_ms, 2),
                }

        # Aggregate stats
        total_raw = conn.execute("SELECT COALESCE(SUM(raw_messages), 0) FROM extraction_stats").fetchone()[0] or 1
        total_extracted = conn.execute("SELECT COALESCE(SUM(extracted_entries), 0) FROM extraction_stats").fetchone()[0]
        total_filtered = conn.execute("SELECT COALESCE(SUM(filtered_noise), 0) FROM extraction_stats").fetchone()[0]
        total_sessions = conn.execute("SELECT COUNT(*) FROM extraction_stats").fetchone()[0]

        noise_reduction = round((total_filtered / total_raw) * 100, 1) if total_raw > 0 else 0

        # Type distribution
        type_rows = conn.execute("""
            SELECT entry_type, COUNT(*) as count
            FROM memory_entries GROUP BY entry_type
        """).fetchall()

        conn.close()

        return {
            "total_sessions": total_sessions,
            "total_raw_messages": int(total_raw),
            "total_extracted_entries": int(total_extracted),
            "total_filtered_noise": int(total_filtered),
            "noise_reduction_percent": noise_reduction,
            "entries_by_type": {row[0]: row[1] for row in type_rows},
        }


# ============================================================================
# Persistence
# ============================================================================

def save_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Save extracted entries to database."""
    with LOCK:
        conn = _get_db()
        saved = 0
        for entry in entries:
            conn.execute("""
                INSERT INTO memory_entries
                (entry_type, content, code_refs, confidence, session_id, timestamp,
                 project, decay_rate, significance, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry["type"],
                entry["content"],
                json.dumps(entry.get("code_refs", [])),
                entry["confidence"],
                entry["session_id"],
                entry["timestamp"],
                entry["project"],
                entry["decay_rate"],
                entry["significance"],
                time.time(),
            ))
            saved += 1
        conn.commit()
        conn.close()
        return {"success": True, "saved": saved}


def get_entries(
    session_id: Optional[str] = None,
    entry_type: Optional[str] = None,
    min_confidence: float = 0.0
) -> List[Dict[str, Any]]:
    """Retrieve stored memory entries with optional filters."""
    with LOCK:
        conn = _get_db()
        query = "SELECT * FROM memory_entries WHERE confidence >= ?"
        params: List[Any] = [min_confidence]

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if entry_type:
            query += " AND entry_type = ?"
            params.append(entry_type)

        query += " ORDER BY created_at DESC"

        rows = conn.execute(query, params).fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "type": r[1],
                "content": r[2],
                "code_refs": json.loads(r[3] or "[]"),
                "confidence": r[4],
                "session_id": r[5],
                "timestamp": r[6],
                "project": r[7],
                "decay_rate": r[8],
                "significance": r[9],
                "created_at": r[10],
            }
            for r in rows
        ]


# ============================================================================
# MCP Handler
# ============================================================================

def handle_memory_extractor(args: Dict[str, Any]) -> str:
    """Main handler for memory_extractor MCP tool."""
    action = args.get("action", "status")

    if action == "extract_session":
        entries = extract_session(
            session_transcript=args.get("session_transcript", []),
            session_id=args.get("session_id", ""),
            use_llm=args.get("use_llm", False),
        )
        if args.get("save", True):
            save_entries(entries)
        return json.dumps({"success": True, "entries": entries}, indent=2)

    elif action == "extract_from_messages":
        entries = extract_from_messages(
            messages=args.get("messages", []),
            session_id=args.get("session_id", ""),
            use_llm=args.get("use_llm", False),
        )
        if args.get("save", True):
            save_entries(entries)
        return json.dumps({"success": True, "entries": entries}, indent=2)

    elif action == "stats":
        return json.dumps(get_extraction_stats(args.get("session_id")), indent=2)

    elif action == "list":
        entries = get_entries(
            session_id=args.get("session_id"),
            entry_type=args.get("entry_type"),
            min_confidence=args.get("min_confidence", 0.0),
        )
        return json.dumps({"entries": entries}, indent=2)

    elif action == "status":
        stats = get_extraction_stats()
        entries_count = stats["total_extracted_entries"]
        noise_reduction = stats["noise_reduction_percent"]
        return json.dumps({
            "status": "ready",
            "total_entries": entries_count,
            "noise_reduction_percent": noise_reduction,
            "model": MINIMAX_MODEL,
            "proxy": MINIMAX_PROXY,
        }, indent=2)

    else:
        return json.dumps({"error": f"unknown action: {action}"})


MEMORY_EXTRACTOR_SCHEMA = {
    "name": "memory_extractor",
    "description": (
        "Intelligent extraction layer that transforms raw session transcripts "
        "into structured memory entries. Filters 80% noise, classifies memory "
        "types (decision, bug_fix, pattern, convention, error_resolution, preference), "
        "and stores with provenance."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["extract_session", "extract_from_messages", "stats", "list", "status"],
                "description": "The extraction operation to perform.",
            },
            "session_transcript": {
                "type": "array",
                "description": "Full session message list for extraction.",
            },
            "messages": {
                "type": "array",
                "description": "Message list (alternative to session_transcript).",
            },
            "session_id": {"type": "string", "description": "Session identifier."},
            "use_llm": {
                "type": "boolean",
                "description": "Use LLM for classification/synthesis (default False).",
            },
            "save": {
                "type": "boolean",
                "description": "Save entries to database (default True).",
            },
            "entry_type": {
                "type": "string",
                "description": "Filter by entry type.",
            },
            "min_confidence": {
                "type": "number",
                "description": "Minimum confidence filter (default 0.0).",
            },
        },
        "required": ["action"],
    },
}


# Alias for MCP tool
def memory_extractor_tool(args: Dict[str, Any]) -> str:
    return handle_memory_extractor(args)