## Plan: MCP Tools Audit
Date: 2026-04-22
Type: RESEARCH/AUDIT
Context gathered:
- Two MCP config files: `.opencode/opencode.json` and `.vscode/mcp.json`
- Git has duplicate servers: `@modelcontextprotocol/server-git` vs `@mseep/git-mcp-server`
- Exa: local npx in vscode/mcp.json vs remote URL in opencode/opencode.json
- Obsidian package mismatch: `@iflow-mcp/kynlos-obsidian-mcp-server` (opencode) vs should use `@modelcontextprotocol/server-obsidian` per config
- Three configs: opencode.json, vscode/mcp.json, config/mcp_config.json
- .wiki vault exists at /home/newadmin/swarm-bot/.wiki

Risk assessment:
- Duplicate git servers could cause conflicts or branch state issues
- Exa running remotely may bypass local caching/security
- Obsidian may be using wrong package
- Configuration drift between files may cause confusion

Approach: Audit each MCP tool independently, verify configuration consistency, and test basic functionality where possible.
