# Memory System Architecture

> Document version: 1.0 | Status: active | Updated: 2026-04-21

This document describes the four-tier memory architecture used by Legiona/SwarmBot to persist knowledge across sessions, support progressive context retrieval, and maintain consistency between semantic stores.

---

## Tier Overview

The memory system is composed of four distinct tiers, each with different capacity, latency, and retention characteristics:

| Tier | Name | Capacity | Latency | Persistence | Backing |
|------|------|----------|---------|-------------|---------|
| 1 | **CoreMemory** | ~4000 chars | Immediate | Permanent (until evicted) | JSON file |
| 2 | **ArchivalMemory** | Unlimited | ~ms | Permanent | SQLite + FTS5 |
| 3 | **RecallMemory** | Unlimited | ~ms | Permanent | SQLite |
| 4 | **UserProfile** | ~2000 chars | Immediate | Permanent | JSON file |

---

## Tier 1: CoreMemory — Always-in-Context Priority Memory

**File:** `core/memory/tiers.py::CoreMemory`

**Purpose:** High-priority, always-editable facts that fit in the agent's context window. Persists across sessions via JSON file at `~/.legionswarm/memory/core_memory.json`.

**Characteristics:**
- Maximum ~4000 characters enforced by `_save()`
- Auto-trim: when cap exceeded, oldest/lowest-importance entries are evicted first
- Key-value store: arbitrary key names derived from fact summaries
- `importance >= 0.85` triggers promotion from ArchivalMemory to CoreMemory key

**API surface:**
```python
core.get(key: str) -> str | None
core.set(key: str, value: str) -> None
core.delete(key: str) -> None
core.to_prompt_block() -> str  # formatted for injection into context
core.all() -> dict[str, str]
```

**Prompt block format:**
```
[CORE MEMORY — always remember these]
  key: value
  project_facts: aiogram 3.4+ async Telegram bot, litellm 1.57+ ...
```

---

## Tier 2: ArchivalMemory — Long-Term Searchable Store

**File:** `core/memory/tiers.py::ArchivalMemory`

**Purpose:** Full-text searchable, timestamped long-term memory. Backed by SQLite with FTS5 (Full-Text Search) for sub-millisecond keyword and semantic search.

**Schema:**
```sql
CREATE TABLE memories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     TEXT NOT NULL,
    summary     TEXT,
    tags        TEXT,          -- comma-separated
    importance  REAL DEFAULT 0.5,
    created_at  TEXT DEFAULT (datetime('now')),
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0,
    source      TEXT
)

CREATE VIRTUAL TABLE memories_fts USING fts5(content, summary, tags)
-- FTS triggers maintain index on INSERT/UPDATE/DELETE
```

**Key features:**
- **FTS5 full-text search**: `SELECT ... FROM memories m JOIN memories_fts fts ON m.id = fts.rowid WHERE memories_fts MATCH ?`
- **Timestamp tracking**: `created_at` (write time), `last_accessed` + `access_count` (read stats)
- **Importance scoring**: affects retrieval ordering, CoreMemory promotion threshold
- **Source field**: provenance of the stored information (see Pillar 6)

**API surface:**
```python
archival.store(content, summary, tags, importance, source) -> mem_id
archival.search(query, limit) -> list[dict]  # FTS5-powered
archival.get_recent(n) -> list[dict]
archival.total_count() -> int
```

---

## Tier 3: RecallMemory — Permanent Conversation History

**File:** `core/memory/tiers.py::RecallMemory`

**Purpose:** Permanent, session-scoped conversation history for pattern analysis and context reconstruction. Does NOT use FTS — ordered retrieval by ID, no semantic search.

**Schema:**
```sql
CREATE TABLE conversations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    role         TEXT NOT NULL,         -- 'user' | 'assistant' | 'system'
    content      TEXT NOT NULL,
    agent_used   TEXT,
    emotion_state TEXT,
    timestamp    TEXT DEFAULT (datetime('now')),
    session_id   TEXT,
    importance   REAL DEFAULT 0.5
)
```

**Key features:**
- Session-scoped retrieval via `session_id` filter
- Importance auto-assigned: `0.7` if `?` in content, `0.9` if trigger words (`remember`, `important`, `always`, `never`)
- `get_patterns(n_sessions)` extracts last N sessions of user content for pattern analysis

**API surface:**
```python
recall.add(role, content, agent_used, emotion_state, session_id, importance)
recall.get_recent(n, session_id) -> list[dict]
recall.get_patterns(n_sessions) -> str  # concatenated recent user messages
```

---

## Tier 4: UserProfile — Preferences and Interaction Patterns

**File:** `core/memory/user_profile.py`

**Purpose:** Structured storage of user preferences, known facts, and interaction patterns. Synthesized from auto-extracted signals during conversation.

**Auto-extraction triggers** (from `memory_manager.py::auto_extract_and_save`):
```
"my name is", "i prefer", "i use", "i have", "i'm working on",
"always", "never", "remember that", "i live", "my gpu", "my setup",
"i hate", "i love", "don't forget", "by the way"
```

**Content:**
- `known_facts`: user-provided biographical/preference facts
- `interaction_patterns`: derived from preference-signal keywords

---

## MemoryManager — Unified Interface

**File:** `core/memory/memory_manager.py::MemoryManager`

Singleton that coordinates all four tiers:

```python
class MemoryManager:
    core: CoreMemory
    archival: ArchivalMemory
    recall: RecallMemory
    profile: UserProfile
```

**Key orchestration methods:**

### `save(content, summary, tags, importance, source)`
- Stores to ArchivalMemory
- If `importance >= 0.85`, promotes to CoreMemory key

### `build_context_block()`
Returns a formatted string from all three memory tiers (core + profile + recent recall) for context injection.

### `progressive_search(query, limit, type_filter)`
3-layer progressive retrieval:
- **Layer 1 (index)**: Compact results ~50-100 tokens each — always fetched
- **Layer 2 (timeline)**: Contextual results ~200-300 tokens — on demand
- **Layer 3 (full)**: Full detail for top 3 results ~500-1000 tokens — only for selected IDs

This replaces `build_context_block()` with token-efficient progressive disclosure.

### `validate_consistency(user_id, sample_size, drift_threshold)`
Runs semantic alignment check between mem0 and Chroma. Returns:
```python
{
    "status": "ok" | "drift_detected",
    "average_drift": float,   # cosine similarity-derived drift
    "max_drift": float,
    "threshold": float,       # default 0.15
    "sample_size": int
}
```

When `status == "drift_detected"`, treat stored memories as `UNCERTAIN`.

### `auto_extract_and_save(user_message, assistant_response)`
Scans user message for preference signals; if found, saves to ArchivalMemory with `importance=0.75`, source=`auto-extract`, tags=`[auto-extracted, user-preference]`. Also updates UserProfile.

---

## Observation Store — Extended Memory

**File:** `core/memory/observation_store.py`

Extends the base archival layer with timeline queries and observation-level metadata:

- `search(query, type_filter, limit)` — returns compact index results
- `timeline(query, type_filter, limit)` — returns timeline-contextual results with subtitle
- `get_observations(ids)` — returns full details for specific observation IDs
- `get_stats()` — returns aggregate observation counts by type

**Used by** `progressive_search()` to implement Layer 1/2/3 retrieval.

---

## Semantic Cache and Consolidation

**Files:**
- `core/memory/semantic_cache.py` — Chroma-backed semantic embedding cache for long-term memory
- `core/memory/consolidator.py` — Memory consolidation logic for long-term store coherence

**Semantic cache** stores embeddings in Chroma for fast similarity search on memories.

---

## Storage Locations

All memory files are stored under `~/.legionswarm/memory/`:

| File | Contents |
|------|----------|
| `core_memory.json` | CoreMemory JSON store |
| `archival.db` | ArchivalMemory SQLite + FTS5 |
| `recall.db` | RecallMemory conversation history |
| `observations.db` | Observation store |
| `user_profile.json` | UserProfile JSON |

---

## Interaction With Anti-Hallucination System

| Memory Tier | Anti-Hallucination Role |
|-------------|-------------------------|
| CoreMemory | Always-available verified facts — P1/P2 confidence |
| ArchivalMemory | Timestamped evidence — supports Pillar 6 (provenance) and Pillar 8 (decay) |
| RecallMemory | Conversation history — source for Pillar 7 (consistency verification) |
| UserProfile | User preferences — must be tagged `[INFERRED]` if unverified |

---

## Cross-Session Persistence

- `lib/legiona/memory/global_memory.md` — cross-session facts about the project, updated by `evolve()` after each agent run
- `lib/legiona/memory/rules.md` — operational rules synced from agent sessions by `evolve()`
- `lib/legiona/memory/sessions.jsonl` — session metadata for historical reference

These files are NOT part of the four-tier system above — they are markdown/JSONL files that survive across all Claude Code sessions and are read by the Legiona system prompt.

---

## Related Documentation

- `.wiki/ANTI_HALLUCINATION.md` — 8-pillar anti-hallucination protocol (Pillar 6: Source Provenance, Pillar 7: Consistency Verification, Pillar 8: Temporal Decay Awareness)
- `lib/legiona/memory/rules.md` — operational rules including source attribution requirements
- `lib/legiona/memory/global_memory.md` — project facts maintained by evolve()
- `core/memory/memory_manager.py` — MemoryManager singleton and all tier coordination