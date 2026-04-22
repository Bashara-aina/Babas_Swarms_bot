## Swarm Run: MCP Tools Audit
Date: 2026-04-22
Type: RESEARCH/AUDIT
Contracts: 5 total, 5 succeeded, 0 retried, 0 failed
Loops: 0 review loops
Agents used: memory, explorer, planner, worker, reviewer
Files changed: 7 files (5 audit findings + 1 review issue + 1 reviewer approval)
Final status: COMPLETE ✅

## Summary
Audit of all MCP tools connected to OpenCode (exa, filesystem, obsidian, firecrawl, gitnexus, git).

### Key Findings
- **Git**: Duplicate servers - `.opencode/opencode.json` uses `@mseep/git-mcp-server` while `.vscode/mcp.json` uses `@modelcontextprotocol/server-git`
- **Exa**: Architecture mismatch - opencode.json uses remote URL, vscode/mcp.json uses local npx
- **Obsidian**: Package mismatch - `config/mcp_config.json` references wrong package (`@modelcontextprotocol/server-obsidian`) but is disabled; active configs use `@iflow-mcp/kynlos-obsidian-mcp-server`
- **Firecrawl**: CONSISTENT - API key matches across configs
- **Filesystem/GitNexus**: CONSISTENT - paths and commands match

### Audit Files Created
- `git-audit-findings.md`
- `exa-audit-findings.md`
- `obsidian-audit-findings.md`
- `firecrawl-audit-findings.md`
- `filesystem-gitnexus-audit-findings.md`
