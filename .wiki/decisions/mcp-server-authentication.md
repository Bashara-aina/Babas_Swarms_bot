---
title: MCP Server Authentication
type: decision
status: active
tags: ["mcp", "server", "authentication", "api"]
created: 2026-04-13
updated: 2026-04-13
summary: Activated base environment and investigated MCP server authentication failure. Decided to disable authentication temporarily until API is available.
wikilinks:
  - [[concepts/environment-management]]
  - [[entities/conda]]
  - [[decisions/mcp-api-decision]]
confidence: high
source: claude-code
---

To solve the MCP server authentication issue, activate the base environment using `conda activate base`. Investigate the authentication failure by reviewing the pasted text. The list of APIs to fill is not explicitly stated, but it is recommended to disable authentication temporarily until the API is available. This decision was made to prevent further disruptions. To disable authentication, set `yes` to `false`.