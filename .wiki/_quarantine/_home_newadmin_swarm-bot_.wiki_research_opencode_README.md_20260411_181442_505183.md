---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/opencode/README.md",
  "reason": "daily_fast_scan: score=0.100 < 0.3",
  "score": 0.1,
  "quarantined_at": "2026-04-11T18:14:42.505224"
}
---

# Awesome Opencode

Source: https://github.com/anomalyco/awesome-opencode

## What This Is
A curated list of plugins, themes, agents, and resources for OpenCode — the AI coding agent for the terminal built by Anomaly.

## Why Legion Cares
- **OpenCode integration**: Legion's `.wiki/` is maintained by OpenCode — understanding OpenCode plugins helps tune the integration
- **Memory plugins**: opencode-mem, opencode-background, opencode-agent-memory for persistent session memory
- **Swarm coordination**: opencode-swarm-plugin for multi-agent coordination
- **Token optimization**: opencode-snip, opencode-tokenscope, opencode-dynamic-context-pruning for cost control

## Key Concepts
- **Memory**: opencode-mem (Letta-style persistent memory), opencode-background (long-running tasks)
- **Context**: dynamic-context-pruning (keep context lean), tokenscope (track/optimize token costs)
- **Plugins**: mcp (MCP server support), envsitter-guard (prevent .env leaks)
- **Swarm**: swarm-plugin + background-agents for parallel multi-agent execution
- **Configuration**: opencode-model-announcer, opencode-workspace (16-component orchestration)

## Detailed Pages (for depth)
- `.wiki/indexes/opencode-index.md` — OpenCode configuration reference
- `.wiki/research/opencode/` subdirectory — full OpenCode documentation
- `.wiki/architecture/PRODUCTION-AGENT-PATTERNS.md` — how OpenCode plugins compose with production agents
