---
date: "2026-04-12"
investigator: "@planner"
status: "Root Cause Identified"
---
# Image Analyzer Bug Investigation

## 1. Which Handler Processes Image Messages

**Handler:** `handlers/media_tools.py`  
**Function:** `handle_photo` (line 306-357)

```python
@router.message(F.photo)
async def handle_photo(msg: Message) -> None:
```

**Router registration:** `handlers/__init__.py` line 76
```python
media_tools.router,  # /imagine /search /speak + F.photo (MiniMax media tools)
```

---

## 2. Call Flow

```
User sends photo
    ↓
handle_photo() [media_tools.py:306]
    ↓
_download_photo() [media_tools.py:54] - downloads to temp file
    ↓
understand_image(prompt, tmp_path) [tools/minimax_media.py:53]
    ↓
MCPClient.call_tool("minimax", "CodingPlan_understand_image", ...)
    ↓
send_chunked() [handlers/shared.py:154]
```

---

## 3. Root Cause

### Primary Bug: Error Detection is Too Narrow

**File:** `handlers/media_tools.py`  
**Lines:** 339-348

```python
result = await understand_image(prompt=prompt, image_path=tmp_path)

if result.startswith("Error:"):
    await status.edit_text(f"❌ {result}")
    return

await status.delete()
await send_chunked(
    msg,
    f"🖼️ <b>Image Analysis</b>\n\n{result}",
    parse_mode="HTML",
)
```

**Problem:** The check `result.startswith("Error:")` only catches error strings that begin with `"Error:"`. However, `MCPClient.call_tool()` in `core/mcp_client.py` returns error strings that do NOT start with "Error:":

- Line 92: `return f"MCP server '{server_name}' not in config."`
- Line 94: `return f"MCP server '{server_name}' is disabled in config."`
- Line 101: `return "MCP Python SDK not installed (pip install mcp)."`
- Line 105: `return f"MCP server '{server_name}' has no command configured."`
- Line 118: `return f"MCP error ({server_name}/{tool_name}): {exc}"`

**Result:** When the MiniMax MCP server is not configured (which it isn't - see below), `understand_image()` returns `"MCP server 'minimax' not in config."` which does NOT start with "Error:". The code then:

1. DELETES the status message (`await status.delete()`)
2. Passes the error string to `send_chunked()` which tries to format it as HTML

### Secondary Issue: MCP Server Not Configured

**File:** `config/mcp_config.json`

```json
{
  "servers": [
    {"name": "example-filesystem", ...},
    {"name": "example-fetch", ...}
  ]
}
```

There is NO `minimax` server configured. The default server name is `"minimax"` (from `LEGION_MCP_MINIMAX_SERVER` env var, defaulting to `"minimax"`).

### Why the Bot Appears to "Disconnect"

1. Bot sends "🖼️ Analyzing image…"
2. `understand_image()` returns `"MCP server 'minimax' not in config."`
3. `handle_photo()` doesn't detect this as an error (wrong prefix check)
4. Status message is deleted
5. `send_chunked()` receives the unescaped error string
6. When `msg.answer()` is called with `parse_mode="HTML"` and the error string, Telegram may reject the message due to HTML parsing issues (unclosed tags, invalid entities)
7. The fallback exception handler in `send_chunked()` eventually tries sending without HTML, but by this point the user perceives the bot as having "disconnected"

---

## 4. Specific Files/Lines to Fix

### Fix 1: `handlers/media_tools.py` lines 339-348

**Current code:**
```python
if result.startswith("Error:"):
    await status.edit_text(f"❌ {result}")
    return

await status.delete()
await send_chunked(
    msg,
    f"🖼️ <b>Image Analysis</b>\n\n{result}",
    parse_mode="HTML",
)
```

**Fix:** Check for error indicators more broadly:
```python
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

await status.delete()
await send_chunked(
    msg,
    f"🖼️ <b>Image Analysis</b>\n\n{result}",
    parse_mode="HTML",
)
```

### Alternative Fix: Add "Error:" prefix to all error returns in `core/mcp_client.py`

**Lines 92, 94, 101, 105, 118** should return strings starting with `"Error:"` to match the existing check pattern.

### Fix 2: Add MiniMax MCP server configuration

**File:** `config/mcp_config.json` needs a proper MiniMax MCP server entry, OR the user needs to set `LEGION_MCP_MINIMAX_SERVER` environment variable to point to an existing MCP server.

---

## 5. Summary

| Item | Details |
|------|---------|
| **Handler** | `handle_photo` in `handlers/media_tools.py:306` |
| **Root Cause** | Error detection check `result.startswith("Error:")` is too narrow; `MCPClient.call_tool()` returns error strings that don't match this pattern |
| **Why bot "disconnects"** | Error string passed to `send_chunked()` with HTML mode, Telegram rejects malformed HTML, user sees status message deleted with no response |
| **Files to fix** | `handlers/media_tools.py:339-348` (primary fix), `core/mcp_client.py` lines 92,94,101,105,118 (secondary fix) |
| **MCP server** | Not configured in `config/mcp_config.json` |

---

## 6. Recommended Fix

**Primary fix (media_tools.py):** Broaden error detection to catch all MCP error strings.

**Secondary fix (mcp_client.py):** Prefix all error returns with `"Error:"` for consistency.

**Note:** Even after fixing the error handling, image analysis won't work until a MiniMax MCP server is properly configured in `config/mcp_config.json`.
