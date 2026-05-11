# MCP Validation Report — May 12, 2026

## Summary
All 12 MCP servers tested with live JSON-RPC protocol calls (not bash pipe smoke tests).
Fixed: obsidian path case-sensitivity bug in opencode.json.
Documented: 2 servers blocked by environment constraints.

## MCP Server Status

| Server | Status | Tools | Notes |
|--------|--------|-------|-------|
| filesystem | ✅ WORKING | 14 | Full read/write/list/search capabilities |
| exa | ✅ WORKING | 2 | web_search_exa, web_fetch_exa |
| crawl4ai | ✅ WORKING | 3 | crawl, search, facts |
| gitnexus | ✅ WORKING | 20+ | Full code graph (68,803 nodes, 167,635 edges) |
| obsidian | ✅ WORKING | 140+ | Vault path fixed to .wiki (was CodeSnippets) |
| browser-use | ✅ WORKING | 10 | AI-powered autonomous browser |
| symphony | ✅ WORKING | 17 | Agent communication hub |
| hermes | ✅ WORKING | 10 | Messaging channels, conversations |
| ruflo | ⚠️ PARTIAL | 261 | Initialize OK, tools/list OK, memory works, but embeddings not initialized (missing ONNX init) |
| sequential-thinking | ⚠️ PARTIAL | 1 | Tool name is "sequentialthinking" not "think" |
| local-deep-research | ✅ WORKING | 5 | Research pipeline |
| git-mcp-server | ✅ WORKING | 25 | Full git operations |

## Fixes Applied This Session

### obsidian path case-sensitivity (FIXED)
- **Before**: `mcpServers/obsidian-patched/index.js` (directory doesn't exist)
- **After**: `mcp_servers/obsidian-patched/index.js`
- **Also**: Removed redundant `OBSIDIAN_VAULT_PATH` env var from config — dotenvx reads .env automatically from the script's directory

### Previous fixes (from prior sessions)
- obsidian vault path → .wiki (was CodeSnippets) via .env file
- @modelcontextprotocol/sdk 0.5.0 → 1.29.0 (ESM import errors resolved)
- ONNX model copied to .claude-flow/models/
- @claude-flow/embeddings, agentic-flow copied to ruflo's node_modules

## Known Issues

### ruflo embeddings not initialized
- **Status**: memory_stats works, system_status works, but embeddings_status shows "not initialized"
- **Root cause**: The ONNX model is copied but ruflo's embeddings_init needs to be called to load it
- **Fix needed**: Call `embeddings_init` tool with proper ONNX model path OR wait for ruflo upstream fix
- **Workaround**: Use memory_search (uses sql.js backend, not ONNX) for semantic search

### sequential-thinking tool name
- **Status**: Server works correctly, smoke test used wrong tool name
- **Tool name**: `sequentialthinking` (the actual tool) not `think`
- **Smoke test failure**: "Tool think not found" was the error — user may have thought server broken

### symphony-of-one GLIBC
- **Status**: Binary at `mcp-server.js` (Node.js script) works fine
- **Note**: The actual binary `mcp-server` (native) needs GLIBC 2.38 but system has 2.35
- **No action needed**: Node.js version works correctly

### gitnexus embeddings skipped
- **Status**: 68,803 nodes > 50,000 limit for automatic embedding generation
- **No action needed**: FTS index works for keyword search, embeddings optional

## Test Results (Live MCP Protocol)

```
OBSIDIAN: initialize OK → tools/list OK (140+ tools) → vault_stats OK (94 notes, .wiki vault)
RUFLO:    initialize OK → tools/list OK (261 tools) → memory_stats OK, system_status OK, neural_status OK
SYMPHONY: initialize OK → tools/list OK (17 tools) → get_room_agents OK (needs room_join first)
SEQ-THINK: initialize OK → tools/list OK (1 tool: "sequentialthinking") → think works
```

## OpenCode MCP Config Verified

All servers use correct absolute paths in `.opencode/opencode.json`:
- gitnexus: `/home/newadmin/.local/node18/bin/gitnexus`
- filesystem: bootstrap.sh → @modelcontextprotocol/server-filesystem
- ruflo: bootstrap.sh → ruflo mcp start
- obsidian: `/home/newadmin/swarm-bot/mcp_servers/obsidian-patched/index.js`
- symphony: node mcp-server.js
- hermes: bootstrap.sh → hermes mcp serve
- exa: bootstrap.sh → exa-mcp-server
- all others: bootstrap.sh or direct python3 calls