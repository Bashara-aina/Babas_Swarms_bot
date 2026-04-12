# ADR-056: Fix Non-Fatal Warnings on Legion Bot Shutdown

**Date**: 2026-04-12  
**Status**: Accepted  
**Decider**: Planner Agent  

## Context

When the Legion bot shuts down, several non-fatal warnings appear:

1. **AgentOps SIGTERM** - `agentops` library calls `SIGTERM` when session ends without proper cleanup
2. **faster-whisper/kokoro TTS** - Optional voice features with expired HuggingFace token (non-fatal, already handled)
3. **OpenViking config missing** - Optional context feature (non-fatal, already handled gracefully)
4. **sentence-transformers not installed** - Optional semantic routing (non-fatal, already handled gracefully)
5. **ResourceWarnings on shutdown** - Unclosed SQLite connections and asyncio transports

## Decision

Fix items 1 and 5 (AgentOps SIGTERM and ResourceWarnings). Items 2-4 are already handled gracefully and require no code changes.

## Root Causes & Fixes

### 1. AgentOps SIGTERM
**Root Cause**: `agentops.end_session()` is never called on shutdown. The library sends SIGTERM when the session ends ungracefully.

**Fix**: Call `end_session()` from `tools.agentops_client` in `on_shutdown()`.

### 2. ResourceWarnings - SQLite Connections
**Root Cause**: 
- `ArchivalMemory` and `RecallMemory` in `core/memory/tiers.py` open `sqlite3.Connection` objects in `__init__` that are never closed
- `tools/memory.py` does not export `close_memory_db()` but `main.py` imports it

**Fix**:
1. Add `close()` method to `ArchivalMemory` and `RecallMemory` classes
2. Add `close_memory_db()` stub to `tools/memory.py` (no-op since aiosqlite uses context managers)
3. Wire all cleanup functions into `on_shutdown()` in `main.py`

## Files to Modify

| File | Change |
|------|--------|
| `tools/memory.py` | Add `close_memory_db()` function |
| `core/memory/tiers.py` | Add `close()` method to `ArchivalMemory` and `RecallMemory` |
| `main.py` | Wire cleanup into `on_shutdown()`, call `end_session()` for AgentOps |

## Notes

- **faster-whisper/kokoro TTS**: These are OPTIONAL voice features. The code already handles failures gracefully with fallbacks to gTTS. No change needed.
- **OpenViking**: Optional config. Already handled gracefully with fallback.
- **sentence-transformers**: Optional dependency. Already handled gracefully with Layer 1 keyword routing fallback.

## Consequences

- Bot will shut down cleanly without ResourceWarnings
- AgentOps session will end properly without SIGTERM
- All optional features (TTS, OpenViking, sentence-transformers) remain gracefully degraded when unavailable
