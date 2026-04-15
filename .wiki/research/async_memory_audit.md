# Async Compliance & Memory Architecture Audit

**Date:** 2026-04-14
**Scope:** core/, tools/, handlers/, computer_agent/, ext/skills/
**Excluded:** tests/, .venv/, .wiki/, mirofish/backend/ (isolated microservice)

---

## 1. Blocking I/O Sites

### 1.1 Confirmed `time.sleep` / `threading.Thread` in project code

| File | Line | Pattern | Severity |
|------|------|---------|----------|
| `computer_agent/shell.py` | 193 | `time.sleep(delay_seconds)` | **HIGH** |
| `ext/skills/design/scripts/icon/generate.py` | 398 | `time.sleep(1)` | LOW (design script) |
| `ext/skills/design/scripts/logo/generate.py` | 293 | `time.sleep(2)` | LOW (design script) |
| `tools/mirofish/backend/` | 15+ files | `time.sleep`, `threading.Thread` | ACCEPTABLE (isolated microservice) |

**`computer_agent/shell.py:193` — `restart_bot()`:**
```python
def restart_bot(delay_seconds: float = 1.0) -> None:
    logger.info("Bot restarting via os.execv...")
    time.sleep(delay_seconds)          # ← BLOCKING
    os.execv(sys.executable, [...])     # process replacement
```
This is a **sync** function called `restart_bot`. It is not itself async, but if any caller invokes it directly from an async context without `run_in_executor`, it blocks the event loop. No async wrapper exists for it.

### 1.2 Async Methods Calling Synchronous I/O Directly

**`core/memory/memory_manager.py`** — `MemoryManager` singleton:

```python
async def save(self, content: str, ...) -> int:
    mem_id = self.archival.store(...)  # ← sync I/O (SQLite) in async fn, NO executor
    ...

async def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
    results = self.archival.search(...)  # ← sync I/O in async fn, NO executor
    ...
```

Methods `save()` and `search()` are declared `async` but delegate to fully synchronous SQLite operations (`ArchivalMemory.store`, `ArchivalMemory.search`) without `await loop.run_in_executor(...)`. This blocks the aiogram event loop on every memory save or search. The same applies to `add_conversation_turn()` (sync) and `build_context_block()` (sync).

**Count: 2 confirmed async-blocking violations** in `core/memory/memory_manager.py`.

---

## 2. Memory Architecture Pattern Usage

### 2.1 Three Distinct Memory Layers

| Layer | Module | Purpose |
|-------|--------|---------|
| Tier 1 — Core/Archival/Recall/Profile | `core/memory/memory_manager.py` (`MemoryManager`) | Tiered FTS SQLite (core + archival + recall + profile) |
| Tier 1 — Semantic (mem0) | `core/memory_manager.py` (`LegionSemanticMemory`) | Async façade wrapping `tools.mem0_client` for RAG |
| Tier 2 — Unified RAG compositor | `core/legion_memory_facade.py` (`LegionMemoryFacade`) | Combines mem0 + wiki + Screenpipe into context blocks |

`core/memory/memory_manager.py` (139 lines) is the **original tiered FTS manager** — SQLite-based with `CoreMemory`, `ArchivalMemory`, `RecallMemory`, `UserProfile` tiers.

`core/memory_manager.py` (65 lines) is a **separate module** — a semantic layer wrapping mem0 for long-term vector memory. It explicitly notes: *"Does not replace `core.memory.memory_manager.MemoryManager` (tiered FTS); keep the two distinct."*

`core/legion_memory_facade.py` (62 lines) is the **unified RAG surface** used by orchestration, combining mem0 semantic results + wiki + Screenpipe.

### 2.2 Facade Coverage — Direct mem0 Bypasses

**VIOLATION: "All memory goes through facade" rule is widely bypassed.**

Direct `tools.mem0_client` imports found outside the intended facade chain:

| File | Function | Direct mem0 call | Route |
|------|----------|-----------------|-------|
| `tools/memory.py` | `add_memory()` L193 | `mem0_add()` | Bypasses `MemoryManager` |
| `tools/memory.py` | `search_memory()` L218 | `mem0_search()` | Bypasses `MemoryManager` |
| `tools/memory.py` | L353 | `mem0_search()` (again) | Bypasses `MemoryManager` |
| `tools/proactive_initiator.py` | L156 | `mem0_search()` | Bypasses ALL facades |
| `tools/mindbus_router.py` | L75 | `mem0_search()`, `build_mem0_context()` | Bypasses ALL facades |

**Clean usages (through facade):**
- `core/memory_manager.py` — imports from `tools.mem0_client` but IS the semantic façade
- `core/legion_memory_facade.py` — uses `LegionSemanticMemory` correctly
- `core/orchestrator.py` — uses `get_memory_facade()` correctly
- `core/skills/builtin/memory.py` — uses `memoryos_client` (separate system, OK)
- `handlers/memory_commands.py` — uses `memory.get_memory_stats()` via `core.memory.memory_manager`

### 2.3 Name Collision Risk

`core/memory_manager.py` and `core/memory/memory_manager.py` are two **different files** with overlapping "memory manager" naming. `core/memory/memory_manager.py` exports `get_memory()` → `MemoryManager` singleton. `core/memory_manager.py` exports `LegionSemanticMemory` (not a singleton). This causes import confusion throughout the codebase:
- `llm_client/__init__.py:35` imports `from core.memory.memory_manager import MemoryManager`
- `core/system_prompt_builder.py:34` imports `from core.memory.memory_manager import MemoryManager`
- `core/legion_memory_facade.py:24` imports `from core.memory_manager import LegionSemanticMemory`

---

## 3. Summary Assessment

| Category | Status | Count |
|----------|--------|-------|
| Blocking `time.sleep` in async context | ⚠️ 1 violation | `computer_agent/shell.py:193` |
| Async method calling sync I/O without executor | ⚠️ 2 violations | `memory_manager.py:save()`, `memory_manager.py:search()` |
| Direct `mem0_add/mem0_search` bypassing facade | ❌ VIOLATION | 5+ sites |
| `threading.Thread` in project code | ⚠️ confined | mirofish only (acceptable isolation) |
| Facade architecture (correct usage) | ✅ | `orchestrator.py`, `legion_memory_facade.py` |

### Key Risks
1. **Event loop blocking** on every `MemoryManager.save()` and `MemoryManager.search()` call in async handlers — affects all `/remember`, auto-extract, and context-building paths.
2. **Facade bypass** — `tools/memory.py`, `proactive_initiator.py`, and `mindbus_router.py` call `mem0_*` directly, meaning there is **no unified memory policy** enforced. Audit/memory stats from `memory_commands.py` will not reflect these bypassed writes.
3. **Name collision** between `core/memory_manager.py` and `core/memory/memory_manager.py` creates import ambiguity.

### Recommended Actions
1. Wrap `self.archival.store()` and `self.archival.search()` in `MemoryManager.save()/search()` with `asyncio.get_event_loop().run_in_executor(None, ...)` or convert tiers to async SQLite.
2. Add a lint rule (ruff) to flag direct `from tools.mem0_client import` in non-facade modules.
3. Rename `core/memory_manager.py` → `core/semantic_memory.py` to eliminate the name collision.

---

*Sources: `core/memory/memory_manager.py`, `core/memory_manager.py`, `core/legion_memory_facade.py`, `tools/mem0_client.py`, `tools/memory.py`, `computer_agent/shell.py`, grep outputs for blocking I/O and mem0 imports.*
