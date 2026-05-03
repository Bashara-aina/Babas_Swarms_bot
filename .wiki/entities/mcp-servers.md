---
title: "MCP Servers"
created: 2026-05-03
tags: [mcp, tools, integration]
wikilinks: []
---

# MCP Servers

> ⚠️ STUB — Full content pending. Created 2026-05-03 by audit v2.

## 12 MCP Servers (from opencode.json)

| Server | Type | Command | Purpose |
|--------|------|---------|---------|
| ruflo | local | python3 -m mcp_servers.ruflo_mcp_server | Agent orchestration |
| gitnexus | local | pnpm dlx gitnexus | Code intelligence |
| obsidian | local | npx @iflow-mcp/kynlos-obsidian-mcp-server | Wiki access |
| filesystem | local | npx @modelcontextprotocol/server-filesystem | File operations |
| git | local | npx @mcp/git | Git operations |
| exa | remote | HTTPS | Web search |
| crawl4ai | local | python3 tools/mcpServers/crawl4ai_mcp/server.py | Web crawling |
| symphony | local | python3 -m mcp_servers.symphony_server | Linear orchestration |
| latex | local | python3 -m mcp_servers.texlab_bridge | LaTeX editing |
| browser-use | local | python3 mcp_servers/browser_use_server.py | Autonomous browser |
| hermes | local | python3 -m mcp_servers.hermes_mcp_server | Messaging bridge |
| sequential-thinking | local | stdio | Chain-of-thought reasoning |

## See Also

- `.opencode/opencode.json` — full MCP configuration
- `core/integrations/mcp_bridge.py` — MCP bridge implementation
