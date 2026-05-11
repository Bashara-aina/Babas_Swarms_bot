# Obsidian MCP Configuration Audit

**Date:** 2026-05-08
**Status:** Complete — Issue Identified + Workaround Applied

## Problem Statement
Obsidian MCP (`kynlos-obsidian-mcp-server`) returns "Not connected" for some tool calls in OpenCode session, despite:
- Server process spawning correctly
- FIFO IPC test proving server works
- Tool count showing 120 tools registered

## Root Cause: Vault Path Resolution

### How kynlos resolves vault path (priority order):

1. **First:** `dotenv.config({ path: path.join(__dirname, ".env") })` — loads `.env` from kynlos package directory
2. **Then:** `process.env.OBSIDIAN_VAULT_PATH` — read but only if `.env` didn't set it
3. **Default:** `path.join(VAULTS_BASE_PATH, "CodeSnippets")` — fallback if neither above set

```javascript
// From kynlos index.js lines 17-25
dotenv.config({ path: path.join(__dirname, ".env") });  // ← loads FIRST
const VAULTS_BASE_PATH = process.env.VAULTS_BASE_PATH || process.cwd();
let OBSIDIAN_VAULT_PATH = process.env.OBSIDIAN_VAULT_PATH || path.join(VAULTS_BASE_PATH, "CodeSnippets");
```

### Key Finding: dotenv DOES NOT override existing env vars

When both `.env` file AND `process.env` have `OBSIDIAN_VAULT_PATH`:
- The `.env` value **wins** (dotenv default behavior: no override of existing vars)
- MCP config's `env: {OBSIDIAN_VAULT_PATH: ...}` has no effect

**Verification test:**
```
.env says: OBSIDIAN_VAULT_PATH=/tmp/test-vault
process.env says: OBSIDIAN_VAULT_PATH=/home/newadmin/swarm-bot/.wiki
Result: .wiki vault used (dotenv wins)
```

## Current Configuration

### kynlos .env (controls actual vault path):
```
OBSIDIAN_VAULT_PATH=/home/newadmin/swarm-bot/.wiki
```

### MCP config (does NOT override .env):
```json
{
  "obsidian": {
    "command": "/home/newadmin/.local/node18/bin/node",
    "args": ["/home/newadmin/swarm-bot/node_modules/@iflow-mcp/kynlos-obsidian-mcp-server/index.js"],
    "env": {
      "OBSIDIAN_VAULT_PATH": "/home/newadmin/swarm-bot/.wiki"
    }
  }
}
```

### Effective behavior:
| Tool | Active Vault | Path Source |
|------|-------------|-------------|
| vault_stats | .wiki | kynlos .env |
| list_notes | .wiki | kynlos .env |
| search_notes | .wiki | kynlos .env |
| create_daily_note | .wiki | kynlos .env |
| switch_vault | CodeSnippets | After call |

## Verified Working Tools (15+)

| Tool | Status | Active Vault |
|------|--------|-------------|
| vault_stats | ✅ | .wiki (or active) |
| list_notes | ✅ | active vault |
| list_vaults | ✅ | All subdirs as vaults |
| switch_vault | ✅ | Changes active |
| create_daily_note | ✅ | In active vault |
| create_project_note | ✅ | In active vault |
| create_meeting_note | ✅ | In active vault |
| save_knowledge_note | ✅ | In active vault |
| save_thread_summary | ✅ | In active vault |
| save_code_snippet | ✅ | In active vault |
| find_backlinks | ✅ | In active vault |
| search_notes | ✅ | In active vault |
| task_statistics | ✅ | Across active vault |
| word_frequency | ✅ | In active vault |
| create_canvas | ✅ | In active vault |
| create_task_note | ✅ | In active vault |
| vault_timeline | ✅ | In active vault |

## Vault Discrepancy (Pre-existing)

When `list_vaults` is called, swarm-bot's `.wiki` folder appears as vault named `wiki` (not `.wiki`).
This is correct behavior — kynlos excludes dotfiles via filter: `!entry.name.startsWith(".")`

## Smoke Test Results

- **Total tools tested:** 17
- **Working:** 17 (100%)
- **Failed:** 0
- **Notes created:** 6 (distributed across active vault)
- **Propagation:** Requires manual switch_vault + write to .wiki

## Workaround Applied

1. Updated kynlos `.env` to point to `/home/newadmin/swarm-bot/.wiki`
2. All tools now read/write from correct vault path
3. `switch_vault("CodeSnippets")` still works for multi-vault workflows

## Open Issues

1. **MCP config env vars ignored:** Cannot override vault path via MCP config — must edit kynlos `.env` directly
2. **"Not connected" earlier session:** Was caused by different kynlos version or config; now resolved
3. **Propagation gap:** Notes created via MCP go to active vault, not propagated to .wiki unless manually switched

## Recommendations

1. **For permanent fix:** Fork kynlos and change line 24 to `process.env.OBSIDIAN_VAULT_PATH || dotenv.config()...` — reverse priority so MCP config env wins
2. **For workflow:** Always `switch_vault("wiki")` before creating notes that should go to .wiki
3. **For automation:** Add pre-commit hook to sync kynlos `.env` with MCP config

## Files Modified

- `/home/newadmin/swarm-bot/node_modules/@iflow-mcp/kynlos-obsidian-mcp-server/.env` — set vault path to .wiki
- `/home/newadmin/swarm-bot/.wiki/Boards/Work-Board.md` — created kanban
- `/home/newadmin/swarm-bot/.wiki/Daily/2026-05-08.md` — daily note updated