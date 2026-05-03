---
title: Obsidian Audit Findings
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Obsidian MCP Server Audit Findings

**Audit Date:** 2026-04-22
**Auditor:** Worker Agent

## Summary

Package name inconsistency detected across three MCP configuration files.

---

## Findings

### 1. opencode.json
```json
"obsidian": {
  "type": "local",
  "command": ["npx", "-y", "@iflow-mcp/kynlos-obsidian-mcp-server", "/home/newadmin/swarm-bot/.wiki"]
}
```
**Package:** `@iflow-mcp/kynlos-obsidian-mcp-server`
**Vault path:** `/home/newadmin/swarm-bot/.wiki` ✅

### 2. .vscode/mcp.json
```json
"obsidian": {
  "command": "npx",
  "args": [
    "-y",
    "@iflow-mcp/kynlos-obsidian-mcp-server",
    "/home/newadmin/swarm-bot/.wiki"
  ]
}
```
**Package:** `@iflow-mcp/kynlos-obsidian-mcp-server`
**Vault path:** `/home/newadmin/swarm-bot/.wiki` ✅

### 3. config/mcp_config.json
```json
{
  "name": "obsidian",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-obsidian", "/home/newadmin/swarm-bot/.wiki"],
  "env": {},
  "enabled": false
}
```
**Package:** `@modelcontextprotocol/server-obsidian` ❌
**Vault path:** `/home/newadmin/swarm-bot/.wiki` ✅

---

## Issue

| Config File | Package Name | Status |
|-------------|--------------|--------|
| `.opencode/opencode.json` | `@iflow-mcp/kynlos-obsidian-mcp-server` | ✅ |
| `.vscode/mcp.json` | `@iflow-mcp/kynlos-obsidian-mcp-server` | ✅ |
| `config/mcp_config.json` | `@modelcontextprotocol/server-obsidian` | ❌ MISMATCH |

**Inconsistency:** `config/mcp_config.json` uses a different (MCP protocol official) package name, while the other two use the custom `@iflow-mcp/kynlos-obsidian-mcp-server`.

### Vault Path Consistency
All three config files point to the same vault path: `/home/newadmin/swarm-bot/.wiki` ✅

---

## Recommendation

Harmonize `config/mcp_config.json` to use `@iflow-mcp/kynlos-obsidian-mcp-server` to match the other configs, or investigate which package is the authoritative one.

---

## Raw grep output

```
# opencode.json
    "obsidian": {
      "type": "local",
      "command": ["npx", "-y", "@iflow-mcp/kynlos-obsidian-mcp-server", "/home/newadmin/swarm-bot/.wiki"]
    },

# .vscode/mcp.json
    "obsidian": {
      "command": "npx",
      "args": [
        "-y",
        "@iflow-mcp/kynlos-obsidian-mcp-server",
        "/home/newadmin/swarm-bot/.wiki"
      ]
    },

# config/mcp_config.json
      "name": "obsidian",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-obsidian", "/home/newadmin/swarm-bot/.wiki"],
```