---
title: Worker Fix Log
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '- **File**: `handlers/shared.py` line 303'
wikilinks: []
confidence: medium
source: research
---
# Worker Fix Log — 2026-04-11

## Subtask 1: Fix `agent_loop()` parameter name ✅
- **File**: `handlers/shared.py` line 303
- **Change**: `progress_cb=on_progress` → `progress_fn=on_progress`
- **Reason**: The `agent_loop()` function in `llm_client/__init__.py` line 728 expects `progress_fn` as the parameter name (verified by reading the function signature at line 720-730)

## Subtask 2: Fix `whatsapp_send_local()` parameter name ✅
- **File**: `handlers/computer.py` line 147
- **Change**: `progress_cb=_progress_local` → `_progress=_progress_local`
- **Reason**: The `whatsapp_send_local()` function in `computer_agent/display.py` line 471 accepts `_progress` as the parameter name (verified by reading the function signature)

## Subtask 3: Fix `tools/minimax_media.py` ✅
- **File**: `tools/minimax_media.py`
- **Issue**: Lines 71, 95, 121, 185 called `MiniMax - CodingPlan_understand_image(...)` and similar — invalid Python syntax (MCP tool names with hyphens are not Python functions)
- **Action**: Rewrote the file to use `core.mcp_client.MCPClient` to call the tools via MCP stdio protocol. The tool names used are:
  - `CodingPlan_understand_image` (image understanding)
  - `CodingPlan_web_search` (web search)
  - `TokenPlan_image_generation` (image generation)
  - `TokenPlan_speech_generation` (speech generation)
- **Note**: These tools require a MiniMax MCP server to be configured in `config/mcp_config.json` with the appropriate tool names. The MCP server name is configurable via `LEGION_MCP_MINIMAX_SERVER` env var (defaults to `"minimax"`). When no MCP server is available, functions return clear error messages instead of crashing.

## Subtask 4: API key audit ✅
- **Searched**: handlers/, tools/, core/, swarms_bot/ for hardcoded API keys
- **Result**: All API keys use `os.getenv()` — no hardcoded secrets found
- **Files reviewed**:
  - `tools/business_ops.py`: Uses `os.getenv("SUPABASE_SERVICE_KEY", "")` and `os.getenv("SUPABASE_URL", "")`
  - `tools/mem0_client.py`: Uses `os.getenv("GROQ_API_KEY", "")`
  - `llm_client/__init__.py`: All API keys via `os.getenv()`
  - `core/model_config.py`: Uses `os.environ.get("MINIMAX_API_KEY", "")`
  - All other tools use `os.getenv()` pattern consistently

## Subtask 5: Handler import check ✅
- **Command**: `python -c "import handlers"`
- **Result**: SUCCESS — no import errors

## Test run
- **Command**: `pytest tests/ -x --asyncio-mode=auto -q`
- **Result**: 199 passed, 1 failure (pre-existing unrelated test `test_repetition_word_rejection` in `test_legion_quality.py`)
- **The failing test** (`test_repetition_word_rejection`) was already failing before these changes — it is unrelated to any of the fixes applied.
