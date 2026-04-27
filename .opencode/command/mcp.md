---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <mcp-server-name>
description: "Discover and use MCP tools. Lists available servers, their tools, and usage patterns."
---

# /mcp — MCP server management

Discover and query Model Context Protocol servers.

## Usage
```
/mcp list
/mcp gitnexus
/mcp fetch
```

## Subcommands

### list — Show all available MCP servers
```bash
# Lists: gitnexus, fetch, Filesystem, Obsidian, etc.
```

### <server-name> — Show tools for a specific server
```
/mcp gitnexus
→ gitnexus_query, gitnexus_context, gitnexus_impact,
  gitnexus_detect_changes, gitnexus_rename, gitnexus_cypher
```

### query — Run a query against an MCP server
```
/mcp fetch https://api.github.com/repos/owner/repo
```

## Swarm-Bot MCP Servers

| Server | Tools | Purpose |
|--------|-------|---------|
| gitnexus | query, context, impact | Code intelligence |
| fetch | url, prompt | Web scraping |
| filesystem | (native tools) | File operations |
| claude_code | (native tools) | Claude Code bridge |

## Constraints
- MCP servers depend on .mcp.json configuration
- Some servers require API keys
- Rate limits may apply to external services
