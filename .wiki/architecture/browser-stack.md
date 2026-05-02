---
title: Browser Stack
tags: [architecture, browser, browser-use, minimax, agent-browser, crawl4ai]
created: 2026-05-02
---

# Browser Intelligence Stack

## Components
- **browser-use** (0.12.6) — Python AI agent loop, MiniMax-powered, Playwright/Chromium
- **agent-browser** (0.26.0) — Rust CLI for fast snapshots, screenshots, and CLI browser tasks
- **crawl4ai** (0.8.6) — existing MCP server for bulk static scraping
- **steel-browser** — NOT AVAILABLE (Docker not accessible on this host)

## MCP Server
- Name: `browser-use`
- Registered in: `.opencode/opencode.json`
- Module: `tools.mcpServers.browser_use_mcp.server`
- Tools: `browser_open`, `browser_click`, `browser_fill`, `browser_scroll`, `browser_wait`, `browser_screenshot`, `browser_get_text`, `browser_get_html`, `browser_close`, `browser_run_task`
- Model: `minimax/MiniMax-M2.7` via `http://localhost:4000`

## Routing
| Task | Tool |
|------|------|
| Dynamic/interactive/login | `browser_run_task` (browser-use MCP) |
| Static/bulk | `crawl4ai_crawl` |
| CLI snapshot / screenshot | `agent_browser_safe.sh` |

## Key Files
- `tools/mcpServers/browser_use_mcp/server.py` — MCP server (358 lines)
- `tools/browser_task_router.py` — auto-routing logic (crawl4ai vs browser-use)
- `scripts/browser_use_safe.sh` — MiniMax-safe env wrapper
- `scripts/browser_use_runner.py` — Python runner (CLI interface)
- `scripts/agent_browser_safe.sh` — CLI wrapper for agent-browser
- `browser-use.json` — project config (headless, model, domains)
- `.opencode/command/browser.md` — slash command
- `.opencode/command/browse.md` — quick browse alias

## Agent Department
`.opencode/agents/browser/`:
- `browser-automation.md` — autonomous browser agent
- `web-researcher.md` — research agent (Exa + crawl4ai + browser-use)

## MiniMax Policy
- All browser LLM calls: MiniMax-M2.7 via localhost:4000
- Forbidden: claude, anthropic, gpt-4, openai, gemini, groq, together
- Guard script: `scripts/browser_use_safe.sh` — hard-blocks forbidden models at startup

## Artifacts
- `.opencode/logs/browser-artifacts/` — screenshots, traces, state files
- `.opencode/logs/browser-e2e-test.txt` — verification results
- `.opencode/logs/browser-stack-status.md` — install status