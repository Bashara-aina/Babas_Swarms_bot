---
title: tools-inventory
domain: tools-skills
impact_score: 9
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 595
---

# Tools Inventory

## ONE-LINE SUMMARY
Every tool Legion can execute — status, trigger, error handling, and output format.

## FACTS
- 77 tools in tools/ directory (74 .py files, plus subdirectories) — many untested or legacy
- Tools use multiple invocation patterns: direct function call, message handler routing, skill dispatch, composio
- Chunking strategy: handlers/shared.py send_chunked() uses chunk_output() at 4000-char Telegram limit
- Output truncation: long outputs are truncated with "..." but truncation point varies by tool
- Async strategy: mixed — some tools use asyncio, others use blocking subprocess.run
- Error handling: most tools fail silently with try/except/pass — only errors logged at DEBUG level
- Timeout strategy: no uniform timeout — subprocess tools use 5–30s timeouts, LLM calls use 60–120s
- Tool output for Telegram: wrapped in _format_for_telegram_html() which converts markdown → HTML

## LEGION BEHAVIOR RULES
1. All new tools must be async — no time.sleep(), no blocking subprocess.run without asyncio.to_thread()
2. All tools must have try/except with specific exception types — no bare except
3. All tools must respect timeout — default 30s for shell tools, 120s for LLM tools
4. Tool output to Telegram: use _format_for_telegram_html() — never raw markdown
5. Long output: use send_chunked() with 4000-char chunk limit
6. Error to user: wrap in humanize_error_for_display() — never raw exception strings
7. Tool must log: logger.info("[TOOL_NAME] ...") on success, logger.warning(...) on failure
8. No tool should crash the bot — wrap entire tool in try/except

## EXAMPLES
Bashara: "/scrape https://example.com" → Playwright screenshot + page text, chunked if >4000 chars
Bashara: "pakai tool git" → Routes to git_tools.py, shows recent commits if GITHUB_TOKEN set
Bashara: "cek gpu status" → nvidia-smi parsed: temperature, VRAM used/total, GPU util %

## ANTI-PATTERNS
1. Silent failures: most tools log only at DEBUG — user sees nothing
2. No timeout uniformization: a hanging tool blocks the entire handler
3. Duplicate tools: browser_agent.py, web_browser.py, scraper_tool.py all do similar things
4. Blocking subprocess in async context: subprocess.run() blocks event loop
5. Markdown in output: _format_for_telegram_html() strips fences but may corrupt code blocks

## DEBATE RECORD
Advocate: 9 | Skeptic: 5 | Judge: WRITE 9
