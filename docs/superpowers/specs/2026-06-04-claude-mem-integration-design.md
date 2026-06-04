# Claude-Mem Integration Design (Babas Agency Swarm)

**Date**: 2026-06-04
**Status**: Approved (brainstorming complete, ready for plan)
**Author**: Claude (via brainstorming)
**Predecessor**: `.wiki/architecture/claude-mem-integration.md` (2026-04-16, status: draft)

---

## Purpose

Deeply and correctly implement the claude-mem pattern (automatic tool-observation capture + progressive disclosure) in this Claude Code setting so it works **natively** with the rest of our systems: 6-layer memory, Hermes MCP, GitNexus, the existing hook system, and the auto-memory bridge.

This is NOT a replacement of existing systems. It is a bridge layer that:
1. Captures every tool call as a structured observation (mirrors claude-mem's PostToolUse hook)
2. Stores in SQLite + FTS5 (the claude-mem data model, with our FTS5 trigram pattern from hermes)
3. Exposes 3-tier progressive disclosure (index / timeline / full)
4. Fans out to the rest of our systems via independent, fire-and-forget bridges
5. Synthesizes end-of-session summaries into the existing Obsidian wiki (joint-brain)

---

## Scope

### In scope (v1)
- Audit the existing 1441 LOC of `core/memory/observation_*.py` for correctness
- Wire Phase 4 (synthesizer → `.wiki/joint-brain/sessions/`)
- Wire Phase 5 (`<private>` tag stripping in every write path)
- Build 3 bridges: 6-layer memory, Hermes MCP, GitNexus
- End-to-end smoke test (synthetic observation → all 4 destinations)
- Extend `scripts/verify-memory-pipeline.py` with 5 health checks

### Out of scope (v1)
- Bun worker service / web viewer (real claude-mem has these; we don't need them — SQLite + existing observability is enough)
- Bridge backfill cron (v2)
- Cross-system session replay UI
- Chroma vector search index for observations (rely on the existing 6-layer memory's vector store)

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │  Tool call (Bash/Edit/Write/Read/etc.) │
                    └────────────────┬────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────────┐
                    │  .claude/helpers/hook-handler.cjs       │
                    │  (PostToolUse matcher)                  │
                    └────────────────┬────────────────────────┘
                                     │ asyncio task
                                     ▼
       ┌─────────────────────────────────────────────────────────────┐
       │  core/memory/observation_queue.py                           │
       │  (existing async queue, maxsize=1000, retry+jitter)        │
       └────────────────┬────────────────────────────────────────────┘
                        │ worker loop
                        ▼
       ┌─────────────────────────────────────────────────────────────┐
       │  core/memory/observation_store.py                           │
       │  insert → SQLite (data/observations.db) + FTS5              │
       │  after commit: asyncio.create_task(_fanout(obs))            │
       └────────────────┬────────────────────────────────────────────┘
                        │ fire-and-forget
        ┌───────────────┼──────────────────────────────┐
        ▼               ▼                              ▼
  ┌──────────┐   ┌──────────────┐              ┌──────────────┐
  │ 6-layer  │   │  Hermes MCP  │              │  GitNexus    │
  │ memory   │   │  bridge      │              │  bridge      │
  │ bridge   │   │              │              │              │
  └────┬─────┘   └──────┬───────┘              └──────┬───────┘
       ▼                ▼                             ▼
  chroma +          FTS5 index in               code knowledge
  langmem +         hermes_session_             graph (70149
  graphrag +        archivist                   symbols)
  mem0
```

### What changes in existing code
- `core/memory/observation_store.py`: add `_fanout()` helper called after `await self._db.commit()` (+15 lines)
- `core/memory/session_summary_synthesizer.py`: wire end-of-session synthesis to write to `.wiki/joint-brain/sessions/` (+30 lines)
- `core/memory/observation_capture.py`: ensure `<private>` tag stripping is applied in every code path (+20 lines)
- `.claude/helpers/hook-handler.cjs`: add a `post-tool` matcher that enqueues to observation_queue (+20 lines)
- `scripts/verify-memory-pipeline.py`: add 5 health checks (+40 lines)

### What we don't change
- 6-layer memory internals (we write INTO it, not replace it)
- GitNexus indexer (we add nodes, existing flow unchanged)
- Hermes MCP (we subscribe to its FTS5 for read; we write our own observations to its memory)
- Any existing files in `core/memory/episodic_store.py`, `memory_manager.py` unless audit finds a bug

---

## Bridge Module Design

Location: `core/memory/bridges/` (new subpackage)

Interface contract (`core/memory/bridges/_base.py`):
```python
class ObservationBridge(Protocol):
    name: str
    async def push(self, obs: Observation) -> None: ...
    async def health(self) -> dict: ...
```

### Bridge 1: `core/memory/bridges/six_layer.py` (~120 lines)
- Calls chroma, langmem, graphrag, mem0 `add_*` APIs
- Metadata: `{"source": "observation", "obs_id": obs.id, "session_id": obs.session_id, "type": obs.observation_type, "tool": obs.tool_name}`
- Idempotent: skip if `obs.id` already in layer

### Bridge 2: `core/memory/bridges/hermes.py` (~80 lines)
- Maps observation fields → `mcp__hermes__memory_save(key, value, decay_rate=0.1)`
- Key naming: `obs:{obs.id}` for O(1) lookups
- Session summaries: also `memory_share_write` so swarm agents see them

### Bridge 3: `core/memory/bridges/gitnexus.py` (~100 lines)
- Fires only for `Edit`/`Write`/`MultiEdit`/`NotebookEdit` (code-modifying tools)
- Maps `obs.files_modified` → graph nodes via `mcp__gitnexus__cypher` `MERGE`
- Edge: `Observation-[MODIFIES]->File`
- Skips noise paths: `.obsidian/`, `.wiki/`, `data/`, `__pycache__/`

### Fan-out glue (in `observation_store.py`, not a new file)
```python
from .bridges import get_bridges

async def _fanout(obs: Observation) -> None:
    """Fire-and-forget bridge fan-out. Never raises."""
    for bridge in get_bridges():
        try:
            await asyncio.wait_for(bridge.push(obs), timeout=5.0)
        except Exception as e:
            logger.warning("[bridge:%s] push failed: %s", bridge.name, e)

# In ObservationStore.insert(), after the existing commit:
asyncio.create_task(_fanout(obs))
```

### Idempotency state
- `data/bridges_state.db` with table `bridge_state(bridge_name TEXT, last_pushed_id INTEGER, updated_at REAL, PRIMARY KEY(bridge_name))`
- Loaded on import; updated after each successful push
- At-most-once semantics across restarts

---

## Data Flow & Error Handling

### Happy path timing
- T+0ms: PostToolUse fires
- T+1ms: hook-handler.cjs enqueues to observation_queue
- T+50ms: queue worker picks obs
- T+51ms: observation_store.insert() commits to SQLite
- T+52ms: asyncio.create_task(_fanout(obs))
- T+~200ms: All 3 bridges have the observation
- T+~10s: hook unblocks (within the 10s hook timeout)

### Failure modes
| Failure | Detection | Recovery | User impact |
|---------|-----------|----------|-------------|
| SQLite write fails | exception in `insert()` | existing `_write_with_retry` (20-150ms jitter, 3 attempts) | obs lost if all fail |
| Queue full (1000) | `QueueFull` in `enqueue` | drop oldest, enqueue new (existing) | recent context may be lost |
| Bridge timeout | `wait_for(bridge.push, timeout=5)` | log, continue with other bridges | one system lags, others fine |
| Bridge crash | exception in `bridge.push` | caught in `_fanout`, logged, never raised | that system misses obs |
| Hermes offline | connection error | retry next observation | obs in SQLite, not Hermes |
| GitNexus mid-run | file lock | skip with warning | obs in SQLite, can be backfilled |
| `<private>` leak | regex in `_strip_private` | test suite catches | never written anywhere |
| Duplicate push | `obs.id` in `last_pushed_id` | skip | at-most-once |

### Backpressure (v2, not v1)
- `bridge_backfill.py` cron reads `last_pushed_id` and re-pushes anything new
- Run via existing `daemon-manager.sh` every 6h
- **Not in v1** — adds complexity; can be a clean follow-up

---

## Testing Strategy

### Unit tests (3 new test files, ~290 lines)
- `tests/test_bridges.py` (~150 lines): idempotency, offline-resilience, code-tool filtering
- `tests/test_observation_fanout.py` (~80 lines): `insert()` triggers fan-out
- `tests/test_private_tag_stripping.py` (~60 lines): every bridge strips `<private>` before push

### Integration test (extend `scripts/verify-memory-pipeline.py`)
- `test_e2e_tool_use_to_bridges`: synthetic obs → SQLite + 6-layer + Hermes + GitNexus
- 5 health checks: chroma, langmem, graphrag, mem0, hermes, gitnexus connectivity + `last_pushed_id` advancing

### Live smoke test (post-deploy)
1. Restart bot: `systemctl --user restart swarm-bot`
2. Trigger a real tool use in any session
3. Within 1s check `data/observations.db` has a new row
4. Run `python scripts/verify-memory-pipeline.py` — all 5 checks green
5. Check bridges: `python -c "from core.memory.bridges import X; print(X.health())"` for each

---

## Implementation Order (single PR)

| Step | What | Files | Lines | Test gate |
|------|------|-------|-------|-----------|
| 0 | **Audit** existing 1441 LOC | (read-only) | 0 | Notes doc with findings |
| 1 | Wire Phase 4 (synth → wiki) | `session_summary_synthesizer.py` | +30 | Wiki file appears after Stop |
| 2 | Wire Phase 5 (private tags) | `observation_capture.py` + audit | +20 | `<private>...</private>` test |
| 3 | Create `core/memory/bridges/` | `_base.py`, `__init__.py` | ~55 | Imports succeed |
| 4 | Implement `six_layer.py` | new | ~120 | `test_six_layer_bridge_idempotent` |
| 5 | Implement `hermes.py` | new | ~80 | `test_hermes_bridge_offline_doesnt_block` |
| 6 | Implement `gitnexus.py` | new | ~100 | `test_gitnexus_bridge_skips_non_code_obs` |
| 7 | Wire `_fanout` in `observation_store.py` | existing | +15 | `test_insert_triggers_fanout` |
| 8 | Add `post-tool` matcher to `hook-handler.cjs` | existing cjs | +20 | Live tool use lands in SQLite |
| 9 | Extend `verify-memory-pipeline.py` | existing script | +40 | Script runs all 5 checks green |
| 10 | Live smoke test | (no code) | 0 | All 6 health checks green |

**Totals**: ~480 new lines (4 bridge files + tests) + ~85 lines added to existing files. All under 500 lines/file.

**Single PR**: yes — bridges share `Observation` dataclass + `_base.py` interface, splitting would create 3 broken-commit histories.

---

## Key Design Decisions

1. **Fire-and-forget fan-out** (not pub/sub, not polling) — reuses existing queue's retry/jitter, lowest latency, simplest to reason about.
2. **Per-bridge idempotency state** in a tiny SQLite file — survives restarts, makes recovery trivial.
3. **No Bun worker / web viewer** — we have better observability already (Prometheus-style metrics in `.claude-flow/metrics/`).
4. **Bridges as a subpackage, not a single file** — keeps each under 500 lines, easy to add a 4th later (Telegram, OpenCode, etc.).
5. **Audit reuses existing code as source of truth** — no rewrites, just targeted fixes during wiring.

---

## References

- [claude-mem repo](https://github.com/thedotmack/claude-mem) — upstream inspiration
- [`.wiki/architecture/claude-mem-integration.md`](../../wiki/architecture/claude-mem-integration.md) — 2026-04-16 design doc (this spec is its evolution)
- `core/memory/observation_*.py` — 1441 LOC of existing code to audit + extend
- `.claude/settings.json` — hook configuration (all 5 lifecycle hooks already wired)
- `scripts/verify-memory-pipeline.py` — to be extended with bridge health checks
