---
title: Review Phase3 2026 04 13
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: 1. **Circular dependency fix** — `handlers/shared.py:70` defines `_bot =
  None`, `main.py:455` sets `_shared._bot = bot` in `on_startup`. Webhook handlers
  (`github.py`, `system.py`) access it via `i...
wikilinks: []
confidence: medium
source: research
---
1. **Circular dependency fix** — `handlers/shared.py:70` defines `_bot = None`, `main.py:455` sets `_shared._bot = bot` in `on_startup`. Webhook handlers (`github.py`, `system.py`) access it via `import handlers.shared as _shared` then `_shared._bot` — correct lazy-access pattern, no circular import risk.

2. **Webhook HMAC validation** — `WebhookServer._validate_github()` at `server.py:32-37` uses `hmac.compare_digest(expected, signature)` — ✅ timing-safe. Secret read from `os.getenv(secret_key)` never hardcoded.

3. **`core/swarm.py` preserves error handling** — `init_swarm_layer()` wraps all imports and initialization in `try/except Exception` with `logger.warning()` — same non-fatal semantics as the original inline code.

4. **`core/agent.py` properly wired from `handlers/ai.py`** — `cmd_think_impl` (line 44) and `cmd_run_impl` (line 60) receive correct callable references: `is_allowed_fn=is_allowed`, `keep_typing_fn=_keep_typing`, `send_chunked_fn=send_chunked`, `execute_chat_fn=_execute_chat`.

5. **No hardcoded secrets** — All secrets via `os.getenv()`. Webhook uses `WEBHOOK_SECRET_{source.upper()}`, MCP uses `MCP_{name.upper()}_ENABLED`, `BRAVE_API_KEY`, etc.

6. **Webhook handler guards against `_bot` being `None`** — Both `github.py:29` and `system.py:30` check `if _shared._bot and _shared.ALLOWED_USER_ID` before calling `send_message`.

7. **Webhook handlers use `try/except` wrapping on send** — `github.py:31` and `system.py:32` catch `Exception` and log warning, ensuring handler errors don't crash the webhook server.
---


#### ⚠️ Warnings

1. **`MCPManager.stop_all()` not called on shutdown** — `main.py:877` `on_shutdown()` stops `_harvester_scheduler` but never calls `MCP_MANAGER.stop_all()`. MCP subprocesses (`asyncio.create_subprocess_exec`) spawned by `MCPClient.start()` will be orphaned on bot shutdown. Not critical (process-level cleanup will reclaim them) but leaves zombie subprocesses until process exit.

2. **Import sorting (I001)** — Three files have unsorted imports auto-detected by ruff:
   - `core/mcp/servers/__init__.py:3` — `from` imports unsorted
   - `core/swarm.py:41` — `from` imports unsorted  
   - `core/webhooks/server.py:3` — `from __future__ import annotations` should precede other imports
   All fixable with `ruff check --fix`.

3. **`MCPClient.stop()` — stdin not explicitly closed** — `client.py:57` calls `proc.terminate()` then `await proc.wait()` but does not close `proc.stdin`. For some MCP servers that may not matter, but it's cleaner to call `proc.stdin.close()` before `terminate()`. Low severity.

4. **No timeout on `MCPClient.list_tools()` during startup** — `manager.py:46` calls `await client.list_tools()` when starting each MCP server. If a server doesn't respond, this hangs the entire `start_all()` coroutine indefinitely. Consider wrapping with `asyncio.wait_for()` with a 10-15s timeout.

5. **`WEBHOOK_SECRET_SYSTEM` defined in MIGRATION.md but not used** — `server.py:48` only validates signature for `source == "github"`. System webhook handlers don't perform HMAC validation, which is intentional (internal source), but the env var is documented as if it gates something. Misleading but not a bug.

---

#### ❌ Blockers

**None.** All critical items pass. The codebase is safe to merge.

---

#### Summary

Phase 3 changes are well-structured. The webhook server uses correct timing-safe HMAC validation, the MCP client properly initializes subprocesses with async stdio, and the swarm layer extraction preserves the original non-fatal error handling semantics. The only substantive issue is that `MCP_MANAGER.stop_all()` is never called on shutdown (Warning #1), which is a cleanup gap rather than a correctness bug. Import sorting is the only lint violation and is auto-fixable.
