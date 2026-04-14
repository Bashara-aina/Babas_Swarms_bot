---
title: Image Analyzer Fix
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
summary: When user sends a picture, bot analyzes but returns no response. Error detection
  in `handlers/media_tools.py` was too narrow - it only checked `result.startswith("Error:")`
  but MCP errors return st...
wikilinks: []
confidence: medium
source: research
---
# Image Analyzer Bug Fix - 2026-04-12

## Bug Summary
When user sends a picture, bot analyzes but returns no response. Error detection in `handlers/media_tools.py` was too narrow - it only checked `result.startswith("Error:")` but MCP errors return strings without that prefix.

## Changes Made

### Primary Fix - `handlers/media_tools.py` (line 337-348)

**Before:**
```python
result = await understand_image(prompt=prompt, image_path=tmp_path)

if result.startswith("Error:"):
    await status.edit_text(f"❌ {result}")
    return
```

**After:**
```python
result = await understand_image(prompt=prompt, image_path=tmp_path)

is_error = (
    result.startswith("Error:") or
    "not in config" in result or
    "is disabled" in result or
    "no command configured" in result or
    "MCP error" in result or
    "not available" in result or
    result.startswith("MCP ")
)
if is_error:
    await status.edit_text(f"❌ {result}")
    return
```

### Secondary Fix - `core/mcp_client.py` (lines 92, 94, 101, 105, 118)

Prefix all error returns with `"Error:"` for consistency:

- Line 92: `f"MCP server '{server_name}' not in config."` → `f"Error: MCP server '{server_name}' not in config."`
- Line 94: `f"MCP server '{server_name}' is disabled in config."` → `f"Error: MCP server '{server_name}' is disabled in config."`
- Line 101: `"MCP Python SDK not installed..."` → `"Error: MCP Python SDK not installed..."`
- Line 105: `f"MCP server '{server_name}' has no command configured."` → `f"Error: MCP server '{server_name}' has no command configured."`
- Line 118: `f"MCP error ({server_name}/{tool_name}): {exc}"` → `f"Error: MCP error ({server_name}/{tool_name}): {exc}"`

## Verification

Ran `python scripts/verify_wiring.py` - All checks passed:
- Handler Wiring: PASS
- Core Imports: PASS
- LLM Client: PASS
- Tools: PASS
- Bridges: PASS
- Skills: PASS
- Agents: PASS
