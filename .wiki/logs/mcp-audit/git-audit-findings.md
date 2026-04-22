# Git MCP Server Audit Findings

**Date:** 2026-04-22  
**Status:** CONFIRMED DUPLICATE

## Config Files Analyzed

| File | Package | Command |
|------|---------|---------|
| `.opencode/opencode.json` | `@mseep/git-mcp-server` | `npx -y @mseep/git-mcp-server` |
| `.vscode/mcp.json` | `@modelcontextprotocol/server-git` | `npx -y @modelcontextprotocol/server-git --repository /home/newadmin/swarm-bot` |
| `config/mcp_config.json` | (git not configured) | — |

## Confirmed Issues

### Duplicate Git MCP Servers
Two different git MCP server packages are configured across the workspace:

1. **`@mseep/git-mcp-server`** — configured in `.opencode/opencode.json`
2. **`@modelcontextprotocol/server-git`** — configured in `.vscode/mcp.json`

These are distinct packages from different publishers:
- `@mseep/git-mcp-server` — by @mseep (not official)
- `@modelcontextprotocol/server-git` — official Model Context Protocol implementation

### Repository Path Inconsistency
- `.vscode/mcp.json` passes `--repository /home/newadmin/swarm-bot`
- `.opencode/opencode.json` does not specify a repository path

## Active Server Determination

Without knowing which editor/tool is actively invoking these configs at runtime, **both could be loaded simultaneously** if:
- VS Code loads `.vscode/mcp.json`
- OpenCode loads `.opencode/opencode.json`

## Recommendations

1. **Deduplicate**: Choose one canonical git MCP server (prefer official `@modelcontextprotocol/server-git`)
2. **Consistency**: If keeping both, ensure repository paths are consistent
3. **Disable unused**: Set `enabled: false` in `config/mcp_config.json` for any server not in active use

## Raw Config Excerpts

```json
// .opencode/opencode.json
"git": {
  "type": "local",
  "command": ["npx", "-y", "@mseep/git-mcp-server"]
}

// .vscode/mcp.json
"git": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-git", "--repository", "/home/newadmin/swarm-bot"]
}
```
