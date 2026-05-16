# Swarm-bot Memory Stack + MCP Fix Session — 2026-05-12

## What Was Done

### 1. Fixed `run_nightly()` in `core/memory/consolidator.py`
Same async bug that was in `deduplicate()` was also in `run_nightly()`:
- `_fetch_old()` was a sync `def` calling `archival.conn.execute().fetchall()` without await
- `_store_summary()` was sync `def` calling `archival.store()` (async) without await
- `_mark_archived()` was sync `def` calling `archival.conn.execute()` without await

**Fixes applied:**
- `_fetch_old()` → `_fetch_old_async()` using `async with archival.conn.execute() as cursor` + `await cursor.fetchall()` with positional row indexing
- `_store_summary()` → `_store_summary_async()` using `await archival.store()`
- `_mark_archived()` → `_mark_archived_async()` using `await archival.conn.execute()` + `await archival.conn.commit()`
- Changed model from `minimax/MiniMax-Text-01` (deprecated) to `minimax/MiniMax-M2.7`

### 2. Tested all memory functions
- `deduplicate()`: works (0 removed)
- `run_nightly()`: works (4 clusters consolidated from 16 old entries)
- `promote_important()`: works

### 3. Consolidated memories verified in DB
New consolidated entries stored with importance=0.9 and tags: `consolidated,long_term,<topic>`
- verification_task_contexts
- personal_messages_to_hani
- rtx_3060_gpu_specifications
- ai_identity_and_research_work

### 4. Created `scripts/start-opencode-mcp.sh`
Standalone launcher for OpenCode + all 12 MCP servers. No VS Code terminal needed.
- Kills existing instances on port 4096
- Starts `opencode serve --port 4096` as background daemon
- Registers all MCP servers via `opencode mcp list` config

### 5. Updated `scripts/legion-boot.sh`
- Section 6 now starts OpenCode serve via `start-opencode-mcp.sh`
- Section 7 (new) checks all 12 MCP servers via `opencode mcp list`
- Removed old naive MCP server checks

### 6. Fixed `scripts/legion-system-check.sh`
- Replaced `while IFS= read` loop with BASH_REMATCH that had eval/quoting issues
- New approach: count `✓` and `✗` symbols with `grep -c`

### 7. Added OpenCode MCP to crontab reboot
```
@reboot cd /home/newadmin/swarm-bot && bash scripts/start-opencode-mcp.sh >> ~/.legion/opencode-mcp.log 2>&1
```

## System Check Results (all passing)
```
L1 Memory: PASS
L2 Memory: PASS
L3 Memory: PASS
LiteLLM Proxy: PASS
Ollama: PASS (3 models)
OpenCode Agent: PASS
MCP Servers: 12 connected, 0 disconnected
Telegram Bot: PASS
ChromaDB storage: PASS
Obsidian Wiki: 2797 documents
✓ ALL SYSTEMS OPERATIONAL
```

## Key Technical Notes
- `aiosqlite.Connection.execute()` is async, returns `aiosqlite.Cursor`, must `await` then `await cursor.fetchall()`
- `async with conn.execute(sql) as cursor:` is the correct pattern (context manager)
- `minimax/MiniMax-Text-01` is deprecated; use `minimax/MiniMax-M2.7` instead
- OpenCode MCP servers are children of the OpenCode UI process (PID 11178 in pts/2)
- `asyncio.to_thread()` wrapper masks async bugs; always make inner functions true `async def` coroutines
- The `Event loop is closed` thread warning from aiosqlite is cosmetic - happens when Python exits while aiosqlite background thread is still running; doesn't affect correctness

## Files Modified
- `core/memory/consolidator.py` — run_nightly() async fixes, model update
- `scripts/legion-boot.sh` — OpenCode + MCP sections
- `scripts/legion-system-check.sh` — MCP check fix
- `scripts/start-opencode-mcp.sh` — NEW (standalone launcher)
- Crontab — added @reboot for OpenCode MCP