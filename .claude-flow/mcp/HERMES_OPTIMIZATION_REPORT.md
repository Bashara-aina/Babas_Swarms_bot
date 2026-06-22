# Hermes MCP Server Optimization Report

Date: 2026-06-17

## 1. Dual-Server Problem

**Finding**: Both `hermes-mcp-server.py` (full, 3125 lines, 195 tools) and `hermes-lite-mcp-server.py` (lite, 372 lines, 34 tools) exist, but the lite server **is never started**. Only the full server runs in practice:

- `settings.json` defines `mcpServer=hermes-lite` 
- `mcp_config.json` also defines `hermes` full server via bootstrap
- The full server is what actually launches (from mcp_config.json or other session entrypoints)
- `ps aux` confirms 5 full server instances running, zero lite instances

**Recommendation**: Either remove the full server and activate the lite, or kill the lite file. Running both is wasted code. The lite's schema-stripping (`_strip_schemas`) is good -- adopt that optimization in the full server if keeping it.

## 2. Startup Performance

| Phase | Time |
|---|---|
| FastMCP + stdlib | 1.08s |
| 16 handler modules | 0.10s |
| 5 hermes modules (iteration, hooks, token_meter, approval_gate, context_injector) | 0.39s |
| **Total** | **1.57s** |

Startup is acceptable (~1.6s cold). The 16 handler modules are lightweight (0.1s total). Most cost is in FastMCP bootstrapping and hermes-agent core imports (openai SDK, rich, protobuf, firecrawl). These cannot be lazy-loaded because FastMCP is the server framework.

**No action needed on startup time.**

## 3. Module Bloat (6,775 lines across 10 modules)

| Module | Lines | Opinion |
|---|---|---|
| hermes_hooks.py | 1,052 | Large but functional -- 26-event lifecycle |
| hermes_token_meter.py | 781 | **Overbuilt for current usage** -- pricing table for 20+ models, tiktoken fallback, but no caller feeds it real data |
| hermes_iteration.py | 905 | Goal-loop + RalphWiggum engine -- justified size |
| cross_session_memory.py | 873 | Memory persistence layer -- justified |
| hermes_context_injector.py | 609 | Context assembly -- could be smaller |
| memory_extractor.py | 668 | Session extraction logic |
| graphrag_engine.py | 535 | GraphRAG engine |
| hermes_approval_gate.py | 528 | Approval policy logic |
| coordination_primitives.py | 504 | Agent coordination |
| delegate_orchestrator.py | 320 | Thin -- OK |

**Recommendation**: The token meter at 781 lines is disproportionate to its actual value -- it tracks token counts nobody reads. Either wire it to a persistent dashboard or **remove model pricing table** (keep only the counting logic, drop 200+ lines of USD/model data).

## 4. Token Meter Integration Status

**Finding**: Token meter loads successfully (`TokenMeter` class + `Schema` available), but **no integration feeds it real data**. The `handle_hermes_token_meter` wrapper exists and works, but:
- No tool calls are instrumented to report tokens
- No session-level tracking is wired in
- The schema is exposed as a tool but has no upstream consumers

**Recommendation**: Either (a) wire into FastMCP middleware to auto-count each tool call, or (b) remove the runtime cost (it adds ~0.08s to startup). Half-integrated is worse than not having it.

## 5. Circuit Breaker Configuration

**Finding**: The CircuitBreaker class is session-local, in-memory only, with hardcoded defaults:
- `failure_threshold=5`, `reset_timeout=60` 
- Not configurable, not persistent, not shared across processes
- A crash kills all learning -- next session starts fresh
- `_wrapped_run_cmd` has a bug: on circuit-breaker failure it silently falls back to `_run_cmd` (defeating the purpose)

**Bug in `_wrapped_run_cmd` (line 1607-1615)**:
```python
def _wrapped_run_cmd(cmd, input_data=None, timeout=60):
    def _inner():
        return _run_cmd(cmd, input_data, timeout)
    try:
        return _cb_registry.call(_inner)
    except Exception:
        pass
    return _run_cmd(cmd, input_data, timeout)  # fallback defeats circuit breaker
```
If the circuit is open, `_cb_registry.call(_inner)` raises, the except swallows it, and the fallback runs anyway -- the circuit breaker does nothing.

**Recommendation**: 
1. Fix the fallback bypass -- if circuit is open, return error immediately
2. Make threshold/timeout configurable via env vars (`HERMES_CB_THRESHOLD`, `HERMES_CB_RESET`)
3. Consider persistence via the existing sqlite3 connection for cross-session state

## 6. Heavy Eager Imports

Notable eagerly-loaded dependencies (at module level, not hidden in functions):
- `tiktoken` in `hermes_token_meter.py` (tries import, falls back gracefully -- OK)
- `openai` SDK trees through hermes-agent's model_tools (unavoidable)

No blocking issues here, but for reference: if startup time ever becomes a concern, FastMCP itself (1.08s) is the bottleneck, not the hermes modules.

## 7. Tool Count vs. Usage

Full server: **195 tool definitions** exposed via FastMCP.
Lite server: **34 tools** (29 hermes-native + 5 wrapped externals).

Each tool definition adds ~0.5-2KB to the LLM context (tool schema). 195 tools = potentially 150-400KB of tool schema sent with every LLM request. The lite's 34 tools = ~17-50KB.

**Recommendation**: **Replace full server with lite server** as the primary. The lite already has the critical tools (terminal, file, web, delegate, search, gitnexus, memory, browser, security, obsidian). The 161 removed tools are mostly pass-through wrappers for externals that can be called via `npx` directly when needed.

## Summary of Recommended Actions

1. **HIGH** -- Fix `_wrapped_run_cmd` circuit-breaker bypass bug
2. **HIGH** -- Replace full hermes server with lite (cut 161 tools, save ~100-300KB context per call)
3. **MEDIUM** -- Wire token meter to real data or shrink it
4. **LOW** -- Make circuit breaker configurable + persistent
5. **LOW** -- Remove unused `memory_list` dead code (already commented out)
