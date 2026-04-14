---
title: Web Scraping Patterns
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- web-scraping-patterns.md
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Two web scraping approaches are currently **operational** in this codebase:'
wikilinks: []
confidence: medium
source: research
---

# Web Scraping Patterns

## Executive Summary

Two web scraping approaches are currently **operational** in this codebase:

| Approach | Library | Best For | Speed |
|----------|---------|----------|-------|
| Autonomous browsing | browser-use | Multi-step tasks, form fills | Slow |
| Simple fetch + health | Playwright | Health checks, quick extracts | Fast |

Crawl4AI is available as an **implementation detail** of the browser-use fallback chain but is **not independently callable** from intent routing.

---

## 2. Pattern A: browser-use (Autonomous Agent)

**File**: `tools/browser_agent.py` — `browse_task()`

**What it is**: LLM-driven browser agent. Receives a task string, performs up to 20 steps of 5 actions each (click, type, scroll, extract).

**Setup**:
```bash
pip install browser-use
export BROWSER_USE_MODEL="openrouter/google/gemini-flash-1.5"
```

**Fallback chain** (when browser-use ImportError):
1. Crawl4AI (preferred) — returns `result["markdown"][:4000]`
2. Raw Playwright — extracts DOM text, 3000 char limit

**Speed**: ~5-20s/step × 20 steps = potentially minutes

**When to use**: Multi-page navigation, form filling, content requiring judgement calls.

**When NOT to use**: Simple content extraction, high-frequency requests, untrusted URLs (no SSRF protection).

---

## 3. Pattern B: Playwright Direct

**Files**: `tools/browser_agent.py` — `check_site_health()` and `_playwright_fallback()`

**Install**: `pip install playwright && playwright install chromium`

### 3a. Health Check (`check_site_health`)

```python
response = await page.goto(target, wait_until="domcontentloaded", timeout=15000)
title = await page.title()
# Error phrase detection: "error 500", "application error", "503 service", "502 bad gateway"
```

Returns: `url`, `status` (ok|degraded|unreachable), `http_status`, `load_time_ms`, `title`

**Degraded condition**: Any error phrase found in page content → `status: "degraded"` but still returns ok.

### 3b. Text Extraction (`_playwright_fallback`)

DOM selector evaluation for text extraction:
```python
text = await page.evaluate("""
    () => document.querySelectorAll('h1, h2, h3, p, li, td, th')
        .map(el => el.innerText?.trim())
        .filter(t => t && t.length > 10)
        .slice(0, 80)
        .join('\\n')
""")
# Returns first 3000 chars
```

**Timeout**: 15s hard limit

**Speed**: Fast — single page load, no LLM overhead

---

## 4. Comparison Matrix

| Criteria | browser-use | Playwright Direct |
|----------|-------------|-------------------|
| Setup complexity | High (LLM config) | Low |
| Speed | Slow (min) | Fast |
| Interactive | ✅ Full | ✅ Limited |
| LLM-driven | ✅ | ❌ |
| SSRF protection | ❌ None | ❌ None |
| Timeout | ~200s (20 steps) | 15s hard |
| Output format | text/JSON | raw HTML/text |

---

## 5. Selection Decision Tree

```
Is the task a health/availability check?
  → YES: Use check_site_health() — fastest, returns HTTP status + load time

Does the task require multi-step interaction (forms, clicks, dialogs)?
  → YES: Use browse_task() via browser-use (if LLM configured)
         If browser-use unavailable: falls back to Crawl4AI then Playwright

Is the URL untrusted (user-supplied)?
  → YES: Add URL validation before passing to any browser tool
         Block: file://, ftp://, dict://, javascript://, private IPs (10.x, 192.168.x, 127.x)

Default for simple content extraction: browse_task() with Playwright fallback (no LLM needed)
```

---

## 6. Crawl4AI: Implementation Detail, Not Independent Tool

**Finding**: Crawl4AI only executes when:
1. `browse_task()` is called
2. `browser-use` raises `ImportError` (not installed)
3. URL is extracted from task string via regex

It is **not** registered as a skill, not in the skill registry, and cannot be invoked directly from intent routing.

**To call Crawl4AI directly**, you would need to:
1. Register in `skill_registry.py`
2. Add route in intent router
3. Configure `AsyncWebCrawler` with explicit timeout

This page does not recommend Crawl4AI as a primary approach because it is not currently independently callable.

---

## 7. SSRF Risk (All Patterns)

**No URL validation exists in any mode.**

- `file://` URLs passed to chromium — potential local file read
- Private IP ranges accessible (10.x, 192.168.x, 127.x)
- No domain allowlist

**Required mitigation**: Add URL validator before any browser fetch. Block: `file://`, `ftp://`, `dict://`, `javascript://`, and private IP ranges.

---

## 8. Dependencies

```bash
pip install playwright && playwright install chromium  # all modes
pip install browser-use langchain-openai              # autonomous mode
```

---

tokens_estimated: 545
inject_into: browser-agent-architecture.md (cross-reference), tool-output-formatting.md (scraping section)