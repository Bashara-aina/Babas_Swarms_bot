---
description: Native browser automation using browser-use with MiniMax only
---

Use `scripts/browser_use_safe.sh` or `scripts/browser_use_runner.py` for browser tasks.
The safe wrapper enforces MiniMax-only LLM policy — no Claude, no OpenAI, no cloud fallbacks.

## Preferred workflow

1. Start at a URL (explicit target prevents wandering).
2. Inspect page state via snapshot/screenshot.
3. Act using click/fill/scroll — prefer refs over CSS selectors.
4. Re-check page state after each important action.
5. Save screenshot + trace artifacts to `./output/`.

## Quick start

```bash
# Direct Python runner (MiniMax via LiteLLM proxy)
python -m scripts.browser_use_runner \
  --task "Click the login button and check the page title" \
  --json

# Shell wrapper with safe MiniMax enforcement
bash scripts/browser_use_safe.sh python -m scripts.browser_use_runner \
  --task "Open https://example.com and find the main heading" \
  --headless

# Full workflow with screenshot
python -m scripts.browser_use_runner \
  --task "Find pricing for plan X on the website" \
  --domain example.com \
  --no-screenshot \
  --json
```

## Rules

- MiniMax only — never use Claude, OpenAI, Gemini, Groq, or Together.
- Lock browser to the target domain when a URL is explicit.
- Use `--json` for machine-parseable output.
- Prefer refs over CSS selectors for stability.
- Fallback chain: browser-use → nanobrowser_agent (3-agent crew) → crawl4ai → playwright direct.

## Architecture

- `scripts/browser_use_safe.sh` — env enforcement wrapper
- `scripts/browser_use_runner.py` — async task runner (ChatOpenAI → LiteLLM → MiniMax)
- `browser-use.json` — project-wide defaults
- `tools/nanobrowser_agent.py` — 3-agent crew (Planner/Navigator/Validator) for complex tasks
- `tools/browser_agent.py` — site health + browse_task (browser-use or Playwright fallback)

## When to use what

| Task | Tool |
|------|------|
| Autonomous multi-step browsing | browser-use via runner |
| Complex multi-agent navigation | nanobrowser_agent |
| Fast static content extraction | crawl4ai |
| Site health / smoke test | check_site_health() |
| Login flows, forms, SPAs | browser-use runner |
| Bulk scraping | crawl4ai |