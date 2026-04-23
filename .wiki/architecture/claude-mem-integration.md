---
title: Claude-Mem Integration Master Prompt
type: architecture
status: draft
tags: [memory, integration, claude-mem, progressive-disclosure, obsidian, hook-system]
created: 2026-04-16
updated: 2026-04-16
summary: Master prompt for implementing claude-mem's automatic capture + progressive disclosure into Legion's memory system across Claude Code, OpenCode, and LegionBot.
wikilinks:
 - [[./concepts/swarm-bot-architecture]]
 - [[./entities/obsidian]]
 - [[./concepts/llm-cost-routing]]
 - [[./decisions/adr-2026-04-12-legion-wiki-loop]]
confidence: high
source: analysis
---

# Claude-Mem Integration Master Prompt

## Purpose

Implement the **automatic capture + progressive disclosure** pattern from [claude-mem](https://github.com/thedotmack/claude-mem) into Legion's memory system. This is not a replacement — it's a bridge layer that adds session-level automatic observation capture while our Obsidian knowledge graph handles long-term synthesis.

**What we're adding (from claude-mem):**
1. PostToolUse hook → automatic observation capture per tool call
2. Progressive disclosure → 3-tier retrieval (index → timeline → full)
3. `<private>` tag stripping → privacy at write time
4. Observation types → taxonomy for filtering (decision, bugfix, discovery…)
5. Session summary synthesis → structured `<request>/<learned>/<next_steps>` blocks

**What's staying ours:**
- Obsidian knowledge graph with wikilinks
- Schema-enforced articles (YAML frontmatter, TL;DR, ≥1 wikilink)
- Joint brain architecture across 3 systems
- 80+ ADRs, 20 wisdom domains, research synthesis

---

## Architecture Overview

```
Session happens (Claude Code / OpenCode / LegionBot)
 ↓
HOOK LAYER (core/builtin_hooks.py — new section)
 ↓
Automatic observation capture (tool_name, input, output, narrative)
 ↓
Observation queue → async worker (core/memory/observation_worker.py)
 ↓
AI compression → SQLite + FTS5 (core/memory/observation_store.py)
 ↓
Progressive disclosure retrieval ← replaces build_context_block()
 ↓
Session summary → synthesis pipeline → Obsidian wiki articles
 ↓
Wikilinks added when new articles reference existing graph
```

---

## Phase 1: Hook Layer — Automatic Observation Capture

### 1.1 New File: `core/memory/observation_capture.py`

```python
"""Observation capture from tool usage — mirrors claude-mem PostToolUse hook."""

from __future__ import annotations

import re
import os
from dataclasses import dataclass, field
from typing import Optional

PRIVATE_TAG_RE = re.compile(r"<private>.*?</private>", re.DOTALL | re.IGNORECASE)

@dataclass
class ToolObservation:
 """A single tool execution captured as an observation."""

 session_id: str
 tool_name: str
 tool_input: dict
 tool_output: dict
 narrative: str = ""
 facts: list[str] = field(default_factory=list)
 concepts: list[str] = field(default_factory=list)
 observation_type: str = "change" # decision | bugfix | feature | refactor | discovery | change
 files_read: list[str] = field(default_factory=list)
 files_modified: list[str] = field(default_factory=list)
 created_at_epoch: float = 0.0

 @classmethod
 def from_tool_use(
 cls,
 session_id: str,
 tool_name: str,
 tool_input: dict,
 tool_output: dict,
 ) -> "ToolObservation":
 """Create observation from a tool use event."""
 obs = cls(
 session_id=session_id,
 tool_name=tool_name,
 tool_input=tool_input,
 tool_output=tool_output,
 )
 obs._generate_narrative()
 obs._classify_type()
 obs._extract_files()
 return obs

 def _strip_private(self, text: str) -> str:
 """Remove <private>...</private> tags before storage."""
 return PRIVATE_TAG_RE.sub("", text)

 def _generate_narrative(self) -> None:
 """Generate human-readable narrative from tool input/output."""
 # Strip private tags from all text fields
 input_str = str(self.tool_input)
 output_str = str(self.tool_output)

 # Generate narrative based on tool type
 if self.tool_name == "Edit":
 file_path = self.tool_input.get("file_path", "unknown")
 old = self.tool_input.get("old_string", "")[:100]
 new = self.tool_input.get("new_string", "")[:100]
 self.narrative = f"Edited {file_path}: changed '{old}' → '{new}'"
 elif self.tool_name == "Bash":
 cmd = self.tool_input.get("command", "")[:80]
 success = self.tool_output.get("exit_code", -1) == 0
 self.narrative = f"Ran shell: {cmd} → {'success' if success else 'failed'}"
 elif self.tool_name == "Read":
 file_path = self.tool_input.get("file_path", "unknown")
 self.narrative = f"Read file: {file_path}"
 self.files_read.append(file_path)
 elif self.tool_name == "Write":
 file_path = self.tool_input.get("file_path", "unknown")
 self.narrative = f"Wrote file: {file_path}"
 self.files_modified.append(file_path)
 else:
 self.narrative = f"Tool {self.tool_name}: {str(tool_input)[:100]}"

 def _classify_type(self) -> None:
 """Classify observation type from tool and context."""
 #decision keywords
 if any(k in self.narrative.lower() for k in ["chose", "decided", "selected", "", ""]):
 self.observation_type = "decision"
 # bugfix keywords
 elif any(k in self.narrative.lower() for k in ["fix", "bug", "error", "issue", "", "bugfix"]):
 self.observation_type = "bugfix"
 # discovery keywords
 elif any(k in self.narrative.lower() for k in ["found", "discovered", "learned", "realized", ""]):
 self.observation_type = "discovery"
 # refactor
 elif any(k in self.narrative.lower() for k in ["refactor", "simplify", "clean", "rename", ""]):
 self.observation_type = "refactor"
 # feature
 elif any(k in self.narrative.lower() for k in ["add", "implement", "new", "create", "", ""]):
 self.observation_type = "feature"
 # default
 else:
 self.observation_type = "change"

 def _extract_files(self) -> None:
 """Extract file paths from tool input."""
 if self.tool_name in ("Edit", "Write"):
 fp = self.tool_input.get("file_path", "")
 if fp and fp not in self.files_modified:
 self.files_modified.append(fp)
 if self.tool_name == "Read":
 fp = self.tool_input.get("file_path", "")
 if fp and fp not in self.files_read:
 self.files_read.append(fp)

 def to_dict(self) -> dict:
 """Serialize for storage."""
 return {
 "session_id": self.session_id,
 "tool_name": self.tool_name,
 "tool_input": {k: self._strip_private(str(v)) for k, v in self.tool_input.items()},
 "tool_output": {k: self._strip_private(str(v)) for k, v in self.tool_output.items()},
 "narrative": self._strip_private(self.narrative),
 "facts": [self._strip_private(f) for f in self.facts],
 "concepts": self.concepts,
 "observation_type": self.observation_type,
 "files_read": self.files_read,
 "files_modified": self.files_modified,
 "created_at_epoch": self.created_at_epoch,
 }
```

### 1.2 Integrate into `core/builtin_hooks.py`

```python
# Add to on_startup() in main.py — register PostToolUse observation capture

async def _register_observation_hooks() -> None:
 """Register automatic observation capture on tool use."""
 from core.memory.observation_capture import ToolObservation

 # Hook into existing hook system via asyncio event
 # This fires after every tool use without blocking the tool
 # Pattern mirrors claude-mem's fire-and-forget HTTP to worker

 async def on_tool_use(session_id: str, tool_name: str, tool_input: dict, tool_output: dict) -> None:
 obs = ToolObservation.from_tool_use(session_id, tool_name, tool_input, tool_output)
 # Fire-and-forget to observation queue — never blocks
 asyncio.create_task(_enqueue_observation(obs))

 # Wire into existing hook registry
 _tool_use_observers.append(on_tool_use)

async def _enqueue_observation(obs: ToolObservation) -> None:
 """Enqueue observation to worker — async, non-blocking."""
 try:
 from core.memory.observation_queue import observation_queue
 await observation_queue.enqueue(obs)
 except Exception as e:
 logger.warning("[Observation] Failed to enqueue: %s", e)
```

### 1.3 Observation Queue: `core/memory/observation_queue.py`

```python
"""Async observation queue — worker-side buffer from claude-mem pattern."""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ObservationQueue:
 """Async queue for observations — consumed by worker process."""

 def __init__(self, maxsize: int = 1000) -> None:
 self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
 self._worker_task: Optional[asyncio.Task] = None
 self._running = False

 async def enqueue(self, obs: "ToolObservation") -> None:
 """Add observation to queue (non-blocking)."""
 try:
 self._queue.put_nowait(obs)
 except asyncio.QueueFull:
 logger.warning("[ObservationQueue] Queue full — dropping oldest")
 try:
 self._queue.get_nowait()
 except asyncio.QueueEmpty:
 pass
 self._queue.put_nowait(obs)

 async def start_worker(self) -> None:
 """Start background worker to process observations."""
 self._running = True
 self._worker_task = asyncio.create_task(self._worker_loop())

 async def _worker_loop(self) -> None:
 """Process observations from queue — AI compression happens here."""
 while self._running:
 try:
 obs = await asyncio.wait_for(self._queue.get(), timeout=1.0)
 await self._process_observation(obs)
 except asyncio.TimeoutError:
 continue
 except Exception as e:
 logger.error("[ObservationQueue] Worker error: %s", e)

 async def _process_observation(self, obs: "ToolObservation") -> None:
 """Process single observation — store + optionally compress."""
 from core.memory.observation_store import observation_store
 await observation_store.insert(obs)
```

---

## Phase 2: Storage — SQLite + FTS5 Observation Store

### 2.1 New File: `core/memory/observation_store.py`

```python
"""SQLite + FTS5 observation store — mirrors claude-mem's db schema.

Location: ~/.claude-mem/claude-mem.db (shared) or data/observations.db (legion-only)
We use: data/observations.db (legion-only, owner-access only)
"""

import aiosqlite
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = Path("data/observations.db")

class ObservationStore:
 """SQLite-backed observation store with FTS5 for full-text search."""

 def __init__(self) -> None:
 self._db: Optional[aiosqlite.Connection] = None

 async def connect(self) -> None:
 """Open DB connection and create schema if needed."""
 DB_PATH.parent.mkdir(parents=True, exist_ok=True)
 self._db = await aiosqlite.connect(str(DB_PATH))
 self._db.execute("PRAGMA journal_mode=WAL")
 await self._create_schema()

 async def _create_schema(self) -> None:
 """Create tables and FTS5 virtual tables."""
 await self._db.executescript("""
 CREATE TABLE IF NOT EXISTS observations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 session_id TEXT NOT NULL,
 tool_name TEXT NOT NULL,
 tool_input TEXT NOT NULL, -- JSON
 tool_output TEXT NOT NULL, -- JSON
 narrative TEXT NOT NULL,
 facts TEXT NOT NULL, -- JSON list
 concepts TEXT NOT NULL, -- JSON list
 observation_type TEXT NOT NULL,
 files_read TEXT NOT NULL, -- JSON list
 files_modified TEXT NOT NULL, -- JSON list
 created_at_epoch REAL NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
 );

 CREATE INDEX IF NOT EXISTS idx_obs_session ON observations(session_id);
 CREATE INDEX IF NOT EXISTS idx_obs_type ON observations(observation_type);
 CREATE INDEX IF NOT EXISTS idx_obs_tool ON observations(tool_name);
 CREATE INDEX IF NOT EXISTS idx_obs_epoch ON observations(created_at_epoch);

 CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
 narrative, facts, concepts,
 content='observations',
 content_rowid='id'
 );

 CREATE TRIGGER IF NOT EXISTS obs_ai AFTER INSERT ON observations BEGIN
 INSERT INTO observations_fts(rowid, narrative, facts, concepts)
 VALUES (new.id, new.narrative, new.facts, new.concepts);
 END;

 CREATE TABLE IF NOT EXISTS session_summaries (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 session_id TEXT NOT NULL UNIQUE,
 request TEXT NOT NULL,
 investigated TEXT NOT NULL,
 learned TEXT NOT NULL,
 completed TEXT NOT NULL,
 next_steps TEXT NOT NULL,
 notes TEXT NOT NULL,
 files_read TEXT NOT NULL, -- JSON list
 files_modified TEXT NOT NULL, -- JSON list
 created_at_epoch REAL NOT NULL,
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
 );

 CREATE VIRTUAL TABLE IF NOT EXISTS summaries_fts USING fts5(
 request, investigated, learned, completed, next_steps, notes,
 content='session_summaries',
 content_rowid='id'
 );
 """)
 await self._db.commit()

 async def insert(self, obs: "ToolObservation") -> int:
 """Insert observation, return rowid."""
 row = (
 obs.session_id,
 obs.tool_name,
 json.dumps(obs.tool_input),
 json.dumps(obs.tool_output),
 obs.narrative,
 json.dumps(obs.facts),
 json.dumps(obs.concepts),
 obs.observation_type,
 json.dumps(obs.files_read),
 json.dumps(obs.files_modified),
 obs.created_at_epoch or time.time(),
 )
 cursor = await self._db.execute(
 """INSERT INTO observations
 (session_id, tool_name, tool_input, tool_output, narrative,
 facts, concepts, observation_type, files_read, files_modified, created_at_epoch)
 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
 row,
 )
 await self._db.commit()
 return cursor.lastrowid or 0

 async def search(self, query: str, limit: int = 10, obs_type: str | None = None) -> list[dict]:
 """Layer 1: Compact index search — returns ~50-100 token result metadata."""
 sql = """
 SELECT o.id, o.session_id, o.tool_name, o.observation_type,
 o.narrative, o.created_at_epoch,
 snippet(observations_fts, 0, '<b>', '</b>', '...', 20) as snippet
 FROM observations o
 JOIN observations_fts f ON o.id = f.rowid
 WHERE observations_fts MATCH ?
 """
 params: list = [query]
 if obs_type:
 sql += " AND o.observation_type = ?"
 params.append(obs_type)
 sql += " ORDER BY o.created_at_epoch DESC LIMIT ?"
 params.append(limit)

 rows = await self._db.execute_fetchall(sql, params)
 return [
 {
 "id": r[0],
 "session_id": r[1],
 "tool_name": r[2],
 "type": r[3],
 "narrative": r[4][:80], # compact — ~50-100 tokens
 "created_at": r[5],
 "snippet": r[6],
 }
 for r in rows
 ]

 async def timeline(
 self,
 anchor_id: int | None = None,
 query: str | None = None,
 depth_before: int = 3,
 depth_after: int = 3,
 ) -> list[dict]:
 """Layer 2: Timeline context — ~155 tokens per observation."""
 if anchor_id:
 row = await self._db.execute_fetchall(
 "SELECT created_at_epoch FROM observations WHERE id = ?", (anchor_id,)
 )
 if not row:
 return []
 anchor_epoch = row[0][0]
 sql = """
 SELECT id, tool_name, observation_type, narrative,
 substr(narrative, 1, 120) as short_narrative,
 created_at_epoch
 FROM observations
 WHERE created_at_epoch BETWEEN ? - 3600 AND ? + 3600
 ORDER BY created_at_epoch
 """
 rows = await self._db.execute_fetchall(sql, (anchor_epoch, anchor_epoch))
 elif query:
 rows = await self._db.execute_fetchall(
 f"""
 SELECT id, tool_name, observation_type, narrative,
 substr(narrative, 1, 120) as short_narrative,
 created_at_epoch
 FROM observations
 WHERE narrative LIKE ?
 ORDER BY created_at_epoch DESC
 LIMIT ?
 """,
 (f"%{query}%", depth_before + depth_after),
 )
 else:
 return []

 return [
 {
 "id": r[0],
 "tool_name": r[1],
 "type": r[2],
 "narrative": r[3],
 "short_narrative": r[4], # ~155 tokens
 "created_at": r[5],
 }
 for r in rows
 ]

 async def get_observations(self, ids: list[int]) -> list[dict]:
 """Layer 3: Full observation details — ~500-1000 tokens per result."""
 placeholders = ",".join(["?"] * len(ids))
 sql = f"""
 SELECT id, session_id, tool_name, tool_input, tool_output,
 narrative, facts, concepts, observation_type,
 files_read, files_modified, created_at_epoch
 FROM observations
 WHERE id IN ({placeholders})
 """
 rows = await self._db.execute_fetchall(sql, ids)
 return [
 {
 "id": r[0],
 "session_id": r[1],
 "tool_name": r[2],
 "tool_input": json.loads(r[3]),
 "tool_output": json.loads(r[4]),
 "narrative": r[5],
 "facts": json.loads(r[6]),
 "concepts": json.loads(r[7]),
 "observation_type": r[8],
 "files_read": json.loads(r[9]),
 "files_modified": json.loads(r[10]),
 "created_at": r[11],
 }
 for r in rows
 ]

 async def insert_summary(self, session_id: str, summary: dict) -> None:
 """Store structured session summary (from Stop hook)."""
 await self._db.execute(
 """INSERT OR REPLACE INTO session_summaries
 (session_id, request, investigated, learned, completed,
 next_steps, notes, files_read, files_modified, created_at_epoch)
 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
 (
 session_id,
 summary.get("request", ""),
 summary.get("investigated", ""),
 summary.get("learned", ""),
 summary.get("completed", ""),
 summary.get("next_steps", ""),
 summary.get("notes", ""),
 json.dumps(summary.get("files_read", [])),
 json.dumps(summary.get("files_modified", [])),
 time.time(),
 ),
 )
 await self._db.commit()

 async def close(self) -> None:
 """Close DB connection."""
 if self._db:
 await self._db.close()

# Singleton instance
observation_store = ObservationStore()
```

---

## Phase 3: Progressive Disclosure — Replacing `build_context_block()`

### 3.1 New Method in `memory_manager.py`

```python
# Add to MemoryManager in core/memory/memory_manager.py

async def progressive_search(self, query: str, depth: str = "index") -> str:
 """3-tier progressive disclosure retrieval.

 Args:
 query: Natural language search query
 depth: "index" | "timeline" | "full"

 Returns:
 Layer 1 (index): ~50-100 tokens/result — IDs, titles, types
 Layer 2 (timeline): ~155 tokens/result — chronological context
 Layer 3 (full): ~500-1000 tokens/result — complete observation
 """
 from core.memory.observation_store import observation_store

 if depth == "index":
 # Layer 1: Compact index — used at session start (~800 tokens total)
 results = await observation_store.search(query, limit=8)
 if not results:
 return ""
 block = "[OBSERVATION INDEX]\n"
 for r in results:
 block += f" #{r['id']} [{r['type']}] {r['tool_name']}: {r['narrative'][:80]}\n"
 block += "\nUse `get_observations([id, ...])` to fetch full details."
 return block

 elif depth == "timeline":
 # Layer 2: Timeline around relevant observations
 results = await observation_store.timeline(query=query, depth_before=3, depth_after=3)
 if not results:
 return ""
 block = "[OBSERVATION TIMELINE]\n"
 for r in results:
 block += f" #{r['id']} {r['short_narrative']}\n"
 return block

 else: # full
 # Layer 3: Full details (called on-demand, not at session start)
 results = await observation_store.search(query, limit=5)
 if not results:
 return ""
 ids = [r["id"] for r in results]
 full = await observation_store.get_observations(ids)
 block = "[OBSERVATIONS]\n"
 for obs in full:
 block += f"## #{obs['id']} ({obs['observation_type']}) — {obs['tool_name']}\n"
 block += f"narrative: {obs['narrative']}\n"
 if obs['facts']:
 block += f"facts: {', '.join(obs['facts'])}\n"
 if obs['files_read']:
 block += f"read: {', '.join(obs['files_read'])}\n"
 if obs['files_modified']:
 block += f"modified: {', '.join(obs['files_modified'])}\n"
 block += "\n"
 return block
```

---

## Phase 4: Session Summary Synthesis → Obsidian Wiki

### 4.1 Session Summary Hook: `core/memory/session_summary_synthesizer.py`

```python
"""Generate structured session summary (Stop hook) → write to Obsidian."""

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

async def synthesize_session(
 session_id: str,
 session_transcript: list[dict],
 llm_client, # our llm_client.chat()
) -> dict:
 """Generate structured summary from session transcript.

 Mirrors claude-mem's Stop hook → structured <request>/<learned>/etc.

 Returns:
 dict with keys: request, investigated, learned, completed,
 next_steps, notes, files_read, files_modified
 """
 # Build compact transcript for LLM
 tool_events = [
 f"[{t.get('tool_name', '?')}] {t.get('narrative', '')}"
 for t in session_transcript
 if t.get("tool_name")
 ]
 transcript_brief = "\n".join(tool_events[-50:]) # last 50 tool uses

 prompt = f"""You are Legion's memory synthesizer. From the tool use transcript below,
generate a structured session summary. Use the exact XML-like tags shown.

TRANSCRIPT:
{transcript_brief}

Generate a summary with these exact fields (empty string if nothing found):
<request>What the user asked for in this session</request>
<investigated>What was researched, explored, or analyzed</investigated>
<learned>Key technical findings, patterns, or decisions made</learned>
<completed>What was successfully finished</completed>
<next_steps>What should happen next (specific, actionable)</next_steps>
<files_read>List of file paths read</files_read>
<files_modified>List of file paths modified</files_modified>
<notes>Any other noteworthy things</notes>

Return ONLY the structured summary, no preamble."""

 response = await llm_client.chat(
 prompt,
 model="groq/llama-3.3-70b-versatile",
 system="You are a precise technical summarizer. Return only the structured format.",
 )

 # Parse response into dict (simple tag extraction)
 summary = _parse_summary_response(response.content)

 # Store in SQLite
 from core.memory.observation_store import observation_store
 await observation_store.insert_summary(session_id, summary)

 # Write to Obsidian wiki
 await _write_session_article(session_id, summary)

 return summary

def _parse_summary_response(text: str) -> dict:
 """Extract fields from structured summary response."""
 fields = ["request", "investigated", "learned", "completed",
 "next_steps", "notes", "files_read", "files_modified"]
 result = {}
 for field in fields:
 start = text.find(f"<{field}>")
 end = text.find(f"</{field}>")
 if start != -1 and end != -1:
 val = text[start + len(f"<{field}>"):end].strip()
 if field in ("files_read", "files_modified"):
 # May be JSON or comma-separated
 try:
 result[field] = json.loads(val)
 except Exception:
 result[field] = [x.strip() for x in val.split(",") if x.strip()]
 else:
 result[field] = val
 else:
 result[field] = ""
 return result

async def _write_session_article(session_id: str, summary: dict) -> None:
 """Write session summary as Obsidian article in joint-brain/."""
 date_str = time.strftime("%Y-%m-%d")
 slug = session_id.replace(" ", "-").lower()[:50]

 content = f"""---
title: Session {date_str} — {summary.get('request', 'memory')[:50]}
type: session
status: active
tags: [session, memory, {date_str}]
created: {date_str}
updated: {date_str}
summary: > {summary.get('completed', summary.get('learned', 'Session summary'))[:150]}
wikilinks: []
confidence: high
source: synthesis
---

# Session {date_str}

## Request
{summary.get('request', 'N/A')}

## Investigated
{summary.get('investigated', 'N/A')}

## Learned
{summary.get('learned', 'N/A')}

## Completed
{summary.get('completed', 'N/A')}

## Next Steps
{summary.get('next_steps', 'N/A')}

## Notes
{summary.get('notes', 'N/A')}

## Files
**Read:** {', '.join(summary.get('files_read', [])) or 'none'}
**Modified:** {', '.join(summary.get('files_modified', [])) or 'none'}
"""

 wiki_path = Path(f".wiki/joint-brain/sessions/session-{date_str}-{slug}.md")
 wiki_path.parent.mkdir(parents=True, exist_ok=True)
 wiki_path.write_text(content)
 logger.info(f"[Synthesizer] Wrote session article: {wiki_path}")
```

---

## Phase 5: `<private>` Tag Privacy

### 5.1 Add to `episodic_store.py` and `observation_capture.py`

```python
# In core/memory/episodic_store.py, add to Episode dataclass:

@dataclass
class Episode:
 # ... existing fields ...

 def __post_init__(self) -> None:
 """Strip private tags on creation."""
 self.summary = self._strip_private(self.summary)
 self.detail = self._strip_private(self.detail)

 @staticmethod
 def _strip_private(text: str) -> str:
 """Remove <private>...</private> tags from text."""
 return re.sub(r"<private>.*?</private>", "", text, flags=re.DOTALL | re.IGNORECASE)
```

And add to `memory_manager.save()`:

```python
async def save(self, content: str, summary: str = "", tags: list[str] | None = None,
 importance: float = 0.5, source: str = "agent") -> int:
 # Strip private tags before storing
 content = re.sub(r"<private>.*?</private>", "", content, flags=re.DOTALL | re.IGNORECASE)
 summary = re.sub(r"<private>.*?</private>", "", summary, flags=re.DOTALL | re.IGNORECASE)
 # ... rest of save
```

---

## Implementation Priority

| Phase | Component | Priority | Complexity |
|-------|-----------|----------|------------|
| 1 | `observation_capture.py` — capture from tool events | **P0** | Medium |
| 1 | `observation_queue.py` — async non-blocking queue | **P0** | Medium |
| 2 | `observation_store.py` — SQLite + FTS5 | **P0** | High |
| 3 | `progressive_search()` in memory_manager | **P1** | Medium |
| 4 | `session_summary_synthesizer.py` → Obsidian | **P2** | High |
| 5 | `<private>` tag stripping | **P2** | Low |

---

## 3-System Implementation Notes

### Claude Code (this repo)
- Add to `core/builtin_hooks.py` in `on_startup()`
- Observation queue starts with main bot
- Writes session summaries to `.wiki/joint-brain/sessions/`

### OpenCode (`.opencode/`)
- Requires OpenCode hook support OR IPC to LegionBot
- Can share `observation_store.py` via `.opencode/agents/legiona/` shared path
- OpenCode sessions write to same SQLite at `data/observations.db`

### LegionBot (Telegram)
- No direct hook system — receives commands via Telegram
- `progressive_search()` method in memory_manager is the query interface
- Session summaries from `/run` commands get synthesized into wiki

---

## Key Files to Create/Modify

**New files:**
- `core/memory/observation_capture.py`
- `core/memory/observation_queue.py`
- `core/memory/observation_store.py`
- `core/memory/session_summary_synthesizer.py`

**Modified files:**
- `core/memory/memory_manager.py` — add `progressive_search()` method
- `core/memory/episodic_store.py` — add `_strip_private()` to Episode
- `core/builtin_hooks.py` — register observation capture hooks
- `main.py` — start observation queue in `on_startup()`

---

## Test Plan

```python
# tests/test_observation_capture.py
@pytest.mark.asyncio
async def test_private_tag_stripping():
 from core.memory.observation_capture import ToolObservation
 obs = ToolObservation(
 session_id="test-123",
 tool_name="Edit",
 tool_input={"file_path": "test.py", "old_string": "secret", "new_string": "<private>hidden</private>"},
 tool_output={"success": True},
 )
 assert "<private>" not in obs.narrative
 assert "hidden" not in obs.narrative

@pytest.mark.asyncio
async def test_observation_type_classification():
 obs = ToolObservation(
 session_id="test-123",
 tool_name="Edit",
 tool_input={"file_path": "fix.py", "old_string": "bug", "new_string": "fixed"},
 tool_output={"success": True},
 )
 assert obs.observation_type == "bugfix"

# tests/test_progressive_disclosure.py
@pytest.mark.asyncio
async def test_index_returns_compact():
 from core.memory.memory_manager import MemoryManager
 mm = MemoryManager()
 result = await mm.progressive_search("authentication", depth="index")
 assert len(result) < 500 # should be ~50-100 tokens/result
 assert "get_observations" in result

@pytest.mark.asyncio
async def test_timeline_returns_context():
 result = await mm.progressive_search("auth", depth="timeline")
 assert "short_narrative" in result
```

---

## Smoke Tests

After implementing each phase:
```bash
# Phase 1+2
python -c "
import asyncio
from core.memory.observation_store import observation_store
asyncio.run(observation_store.connect())
asyncio.run(observation_store.search('test'))
print('observation_store OK')
"

# Phase 3
python -c "
import asyncio
from core.memory.memory_manager import MemoryManager
mm = MemoryManager()
result = asyncio.run(mm.progressive_search('authentication', depth='index'))
print(f'progressive_search returned {len(result)} chars')
print(result[:200])
"

# Phase 5
python -c "
from core.memory.episodic_store import Episode
e = Episode(id='1', user_id='test', episode_type='fact', summary='test <private>secret</private> test', detail='', tags=[], ts=0.0)
assert '<private>' not in e.summary
print('private tag stripping OK')
"
```

---

## Comparison: Before vs. After

| Before | After |
|--------|-------|
| `build_context_block()` injects full articles (500-2000 tokens) | Progressive 3-tier: index (50-100/t) → timeline (155/t) → full (500-1000/t) |
| Manual write-after-act for memory | Automatic PostToolUse capture |
| No session summaries | Structured `<request>/<learned>/<next_steps>` per session |
| Flat episodic entries | Observation taxonomy: decision, bugfix, feature, refactor, discovery, change |
| No privacy tags | `<private>` stripped at write time |
| Single-tier retrieval | 3-tier progressive disclosure |
| Session context inferred from conversation turns | Session context synthesized + stored explicitly |

---

## References

- [claude-mem repo](https://github.com/thedotmack/claude-mem) — the source system
- [[./concepts/swarm-bot-architecture]] — our current architecture
- [[./concepts/llm-cost-routing]] — token budget considerations
- [[./decisions/adr-2026-04-12-legion-wiki-loop]] — prior wiki integration decision
