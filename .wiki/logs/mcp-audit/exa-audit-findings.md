---
title: Exa Audit Findings
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Exa MCP Server Configuration Audit

**Date:** 2026-04-22  
**Auditor:** Bashara

## Summary

Configuration inconsistency **CONFIRMED** — Exa MCP server is configured differently across OpenCode and VS Code.

---

## Findings

### OpenCode (`.opencode/opencode.json`)

```json
"exa": {
  "type": "remote",
  "url": "https://mcp.exa.ai/mcp?exaApiKey=2f2f6644-9907-4444-bb6b-c507b32c4820"
}
```

- **Type:** `remote`
- **Connection:** Direct URL to `https://mcp.exa.ai/mcp` with embedded API key
- **Execution:** Runs as a remote HTTP endpoint

---

### VS Code (`.vscode/mcp.json`)

```json
"exa": {
  "command": "npx",
  "args": [
    "-y",
    "exa-mcp-server"
  ],
  "env": {
    "EXA_API_KEY": "2f2f6644-9907-4444-bb6b-c507b32c4820"
  }
}
```

- **Type:** `local` (implicit via `command` + `args` pattern)
- **Connection:** Spawns local subprocess via `npx -y exa-mcp-server`
- **Execution:** Runs locally as Node.js process

---

## Key Differences

| Aspect | OpenCode | VS Code |
|--------|----------|---------|
| **Type** | `remote` | `local` (npx spawn) |
| **Transport** | HTTP to mcp.exa.ai | Local subprocess |
| **API Key Handling** | URL query param | Environment variable |
| **Runtime** | Remote server | Local npm package |

---

## Risks

1. **Behavior divergence** — Same MCP tool may return different results depending on which host runs it
2. **API key exposure** — OpenCode embeds key in URL; VS Code uses env var (better)
3. **Latency differences** — Remote will have network latency; local is faster
4. **Version mismatch** — Local `exa-mcp-server` npm package may differ from remote endpoint

---

## Recommendation

Align both configurations. Pick one approach:
- **Preferred:** Keep `remote` in OpenCode (already working); update VS Code to use remote URL too
- **Alternative:** Use `local` everywhere (requires npm package install)

Current OpenCode remote config is acceptable for production use.