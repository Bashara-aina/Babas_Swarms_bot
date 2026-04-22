# Firecrawl MCP Server Configuration Audit

**Date:** 2026-04-22  
**Status:** ✅ PASSED — Configuration Consistent

---

## Findings

### 1. Command Configuration
| Config File | Command | Status |
|-------------|---------|--------|
| `.opencode/opencode.json` | `["npx", "-y", "firecrawl-mcp"]` | ✅ |
| `.vscode/mcp.json` | `"npx"` with `["-y", "firecrawl-mcp"]` | ✅ |

**Result:** Both configs use local `npx -y firecrawl-mcp` — CONSISTENT

### 2. API Key Consistency
| Config File | API Key Variable | Value |
|-------------|------------------|-------|
| `.opencode/opencode.json` | `FIRECRAWL_API_KEY` | `fc-09da51dd5e5c46b5b73d7b1ca5cb4c74` |
| `.vscode/mcp.json` | `FIRECRAWL_API_KEY` | `fc-09da51dd5e5c46b5b73d7b1ca5cb4c74` |

**Result:** API key values MATCH — CONSISTENT

### 3. Configuration Format Differences
- **opencode.json**: Uses `environment` object inside the server definition
- **mcp.json**: Uses `env` object inside the server definition
- Both serve the same purpose; this is schema-level difference, not a functional discrepancy

---

## Verification Commands Used
```bash
grep -A8 '"firecrawl"' /home/newadmin/swarm-bot/.opencode/opencode.json
grep -A8 '"firecrawl"' /home/newadmin/swarm-bot/.vscode/mcp.json
```

---

## Conclusion

✅ **All checks passed.** Firecrawl MCP server is configured consistently between both config files. No discrepancies found in command execution or API key values.