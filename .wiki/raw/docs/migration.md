---
title: Migration
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- docs
created: '2026-04-14'
updated: '2026-04-14'
summary: Phase 3 introduces webhook infrastructure, MCP (Model Context Protocol) support,
  architecture refactoring (swarm layer extraction, /run and /think command extraction),
  and a new skills registry. Al...
wikilinks: []
confidence: medium
source: research
---
# Legion v4 → v5 Migration Guide

## Overview

Phase 3 introduces webhook infrastructure, MCP (Model Context Protocol) support, architecture refactoring (swarm layer extraction, /run and /think command extraction), and a new skills registry. All changes are backward-compatible; no existing functionality is removed.

---

## New Dependencies

Install with:

```bash
pip install aiohttp crawl4ai yt-dlp python-pptx ebooklib
```

| Package | Purpose |
|---|---|
| `aiohttp` | Async HTTP client/server for webhook server |
| `crawl4ai` | Web content extraction for research tasks |
| `yt-dlp` | YouTube/audio download for media tasks |
| `python-pptx` | PowerPoint file generation |
| `ebooklib` | E-book parsing |

---

## New Environment Variables

| Variable | Default | Description |
|---|---|---|
| `WEBHOOK_PORT` | `8743` | Port for the webhook server |
| `WEBHOOK_SECRET_GITHUB` | — | HMAC-SHA256 secret for GitHub webhook signature validation |
| `WEBHOOK_SECRET_SYSTEM` | — | Secret for system alert webhooks |
| `MCP_BRAVE_ENABLED` | `0` | Enable Brave Search MCP server |
| `MCP_GITHUB_ENABLED` | `0` | Enable GitHub MCP server |
| `MCP_FILESYSTEM_ENABLED` | `0` | Enable Filesystem MCP server |
| `MCP_FILESYSTEM_PATH` | `.` | Root path for Filesystem MCP server |
| `MCP_OBSIDIAN_ENABLED` | `0` | Enable Obsidian MCP server |
| `MCP_OBSIDIAN_VAULT_PATH` | — | Path to Obsidian vault |
| `MCP_SUPABASE_ENABLED` | `0` | Enable Supabase MCP server |
| `MCP_BROWSER_ENABLED` | `0` | Enable Browser (Playwright) MCP server |

### GitHub Webhook Setup

To receive PR merged notifications:

1. Go to GitHub repo → Settings → Webhooks → Add webhook
2. Payload URL: `https://your-domain.com/webhook/github`
3. Content type: `application/json`
4. Secret: set to `WEBHOOK_SECRET_GITHUB` env var value
5. Events: Pull requests

---

## New Skills (28 Total)

Installed in `core/skills/builtin/`:

### System (5)
- `shell.py` — Shell command execution
- `code_runner.py` — Sandboxed code execution
- `file_ops.py` — File read/write/append operations
- `search_replace.py` — Find and replace in files
- `task_tracker.py` — Task monitoring and scheduling

### Media (4)
- `image_gen.py` — AI image generation
- `tts.py` — Text-to-speech conversion
- `transcriber.py` — Audio/video transcription
- `video_downloader.py` — YouTube/video download

### Personal (4)
- `email_handler.py` — Email reading/sending
- `calendar_ops.py` — Calendar management
- `notes.py` — Note creation and retrieval
- `habits.py` — Habit tracking

### Productivity (4)
- `doc_writer.py` — Document creation
- `spreadsheet_ops.py` — Spreadsheet operations
- `presentation.py` — PowerPoint generation
- `pdf_ops.py` — PDF generation and manipulation

### Memory (3)
- `remember.py` — Long-term memory storage
- `recall.py` — Memory retrieval
- `context_manager.py` — Context window management

### GitHub (3)
- `repo_stats.py` — Repository statistics
- `pr_monitor.py` — Pull request monitoring
- `code_search.py` — GitHub code search

### Research (3)
- `web_search.py` — Web search
- `paper_search.py` — Academic paper search
- `webpage_summarizer.py` — Webpage content extraction

### Web (2)
- `scraper.py` — General webpage scraping
- `api_caller.py` — REST API calls

---

## Migration Steps

### 1. Webhook Server Wiring (main.py)

The webhook server is now initialized in `on_startup`. Previously there was no webhook server. Add to `on_startup`:

```python
# Webhook server (GitHub, system alerts, etc.)
try:
    from core.webhooks import WEBHOOK_SERVER
    from core.webhooks.handlers import github, system

    WEBHOOK_SERVER.register("github", github.handle_github_pr_merged)
    WEBHOOK_SERVER.register("system", system.handle_system_alert)
    asyncio.create_task(WEBHOOK_SERVER.start())
    logger.info("Webhook server started on port %d", WEBHOOK_SERVER.port)
except Exception as e:
    logger.warning("Webhook server init failed (non-fatal): %s", e)
```

### 2. MCP Manager Wiring (main.py)

MCP servers are started via `MCP_MANAGER.start_all()` in `on_startup`:

```python
# MCP servers (Brave, GitHub, Filesystem, Obsidian, Supabase, Browser)
try:
    from core.mcp import MCP_MANAGER

    await MCP_MANAGER.start_all()
    logger.info("MCP manager started")
except Exception as e:
    logger.warning("MCP manager init failed (non-fatal): %s", e)
```

### 3. Swarm Layer Extraction (main.py)

The swarms_bot initialization was extracted to `core/swarm.py::init_swarm_layer()`. Replace the inline initialization with:

```python
try:
    from core.swarm import init_swarm_layer

    init_swarm_layer()
except Exception as e:
    logger.warning("swarms_bot init failed (non-fatal): %s", e)
```

### 4. Bot Reference in shared.py

The bot instance is now accessible via `handlers.shared._bot`. This was added to enable webhook handlers and other modules to send Telegram messages without circular imports:

```python
_shared._bot = bot  # in on_startup
```

### 5. /run and /think Extraction (handlers/ai.py)

The implementations were moved to `core/agent.py`:

- `cmd_think_impl()` — layered extended thinking with adversarial critique
- `cmd_run_impl()` — LLM chat only (no computer access)

`handlers/ai.py` now delegates to these implementations:

```python
@router.message(Command("think"))
async def cmd_think(msg: Message) -> None:
    raw = (msg.text or "").removeprefix("/think").strip()
    from core.agent import cmd_think_impl

    await cmd_think_impl(
        msg, raw,
        is_allowed_fn=is_allowed,
        keep_typing_fn=_keep_typing,
        send_chunked_fn=send_chunked,
    )
```

### 6. Skills Registry

The skills registry is initialized in `on_startup` via `core.skills.get_skill_registry()`. Skills auto-fire based on keyword matching in `intent_router.py`. No additional configuration required.

### 7. Heartbeat Daemon

The heartbeat daemon is wired in `on_startup`:

```python
from core.heartbeat.daemon import _heartbeat

asyncio.create_task(_heartbeat.start(bot, ALLOWED_USER_ID))
```

---

## Backward Compatibility

All existing commands, handlers, and configurations remain functional. The new components (webhooks, MCP, skills) are purely additive and non-breaking. All new initializations are wrapped in `try/except` to ensure failures are non-fatal.
