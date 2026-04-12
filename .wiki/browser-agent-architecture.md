---
title: browser-agent-architecture
domain: tools
impact_score: 8
last_updated: 2026-04-12
injects_into: tool-output-formatting.md
tokens_estimated: 590
---

# Browser Agent Architecture

## Executive Summary

`tools/browser_agent.py` provides two browser automation modes: (1) `check_site_health()` using raw Playwright for lightweight health checks, and (2) `browse_task()` using the `browser-use` library for LLM-driven autonomous browsing with a 3-tier fallback chain.

**Architecture**: Playwright (headless chromium) → browser-use (LangChain + LLM) → Crawl4AI → raw Playwright
**URL allowlist**: **NONE — NO SSRF PROTECTION IMPLEMENTED**
**Key risk**: No domain restriction on any mode. Any URL passed to `browse_task()` or `check_site_health()` will be fetched.

---

## 2. Mode 1: Site Health Check

```python
async def check_site_health(url: str | None = None) -> dict[str, Any]
```

**What it does**: Launches a headless Chromium browser, navigates to target URL, measures load time, extracts title, checks for error phrases in page content.

**Stack**: `playwright.async_api` — chromium launched with `--no-sandbox --disable-setuid-sandbox`

**Timeout**: 15 seconds for `page.goto(wait_until="domcontentloaded")`. Total elapsed time tracked with `time.monotonic()`.

**SSRF exposure**: 
- Function accepts any URL via `url` param or `RUMAHLABUH_URL` env var fallback
- No allowlist, no scheme check, no hostname validation
- `RUMAHLABUH_URL` defaults to `https://rumahlabuh.com` — external site

**Output dict keys**: `url`, `status` (ok|degraded|unreachable), `http_status`, `load_time_ms`, `title`, `error`, `source`

**Error phrases detected** (case-insensitive):
- "error 500"
- "application error"
- "503 service"
- "502 bad gateway"

**Degraded status**: If any error phrase found in page content → `status: "degraded"`

**Fails**: Returns `{"url": target, "error": "...", "status": "unreachable"}` — never raises.

---

## 3. Mode 2: Autonomous Browsing (`browse_task`)

```python
async def browse_task(task: str, max_steps: int = 20) -> dict[str, Any]
```

**What it does**: Launches a full LLM-driven browser agent that can click, type, scroll, and extract information autonomously across multiple steps.

**Stack**: `browser-use` library + LangChain `ChatOpenAI` + configurable LLM via `BROWSER_USE_MODEL` env var.

**LLM Configuration** (via `BROWSER_USE_MODEL` env var):
- Format: `provider/model-id` (e.g., `openrouter/google/gemini-flash-1.5`)
- If provider is `openrouter`: uses `ChatOpenAI` with `base_url=https://openrouter.ai/api/v1` and `OPENROUTER_API_KEY`
- Otherwise: generic OpenAI-compatible endpoint
- Fallback model: `gpt-4o-mini` if env var not set

**BrowserConfig**: `headless=True, disable_security=False` (security NOT disabled — this means CORS, SameSite cookies, etc. enforced normally)

**Max steps**: Default 20 actions. Each step can perform up to 5 actions (click, type, scroll, etc.).

**Fallback chain** (when `browser-use` not installed):
1. **Crawl4AI** preferred — calls `AsyncWebCrawler.arun(url)`, returns `result["markdown"][:4000]`
2. **Raw Playwright** — extracts text from DOM elements (h1, h2, h3, p, li, td, th) up to 80 elements, truncated to 3000 chars

**URL extraction**: Falls back to extracting first URL from `task` string via regex `https?://[^\s'"]+`

**Timeouts**: No explicit timeout on `agent.run()` — depends on `max_steps` (20 steps × assumed 10s/step = 200s potential runtime)

**Output dict keys**: `success`, `result`, `source` (browser_use|crawl4ai|playwright_fallback), `url`, `note`

---

## 4. Telegram Formatting

```python
def format_health_for_prompt(health: dict[str, Any]) -> str
```

Format for bot response:
```
[Site Health — {url}]: {status_icon} {status} | HTTP {http_status} | Load {load_time_ms}ms | Title: {title}
```

Status icons: ✅ ok, ⚠️ degraded, ❌ unreachable, ❓ unknown

---

## 5. Timeout Strategy

| Operation | Timeout |
|-----------|---------|
| `page.goto()` (health check) | 15s |
| `browser-use agent.run()` | No hard limit (governed by `max_steps`) |
| Crawl4AI | No explicit timeout |

---

## 6. SSRF Risk Assessment

**Finding: NO SSRF PROTECTION EXISTS anywhere in browser_agent.py**

- No URL allowlist
- No hostname validation
- No scheme restriction (could pass `file://`, `ftp://`, `dict://`, etc.)
- `check_site_health()` accepts arbitrary URLs from user input
- `browse_task()` accepts arbitrary URLs extracted from task string
- Internal network access via `http://10.x.x.x`, `http://192.168.x.x`, `http://localhost` not blocked
- `file://` scheme would be passed to chromium's `page.goto()` — potential local file read

**Comparable protection**: `sandbox.py` has SSRF-prevention-like directory restrictions for shell commands, but browser_agent.py has no equivalent.

**Recommendation**: Add URL allowlist. At minimum: block `file://`, `ftp://`, `dict://`, and private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8).

---

## 7. Temp File Cleanup

- `check_site_health()` — no temp files created (browser context cleaned up in `finally` block)
- `browse_task()` — no temp files created
- `_playwright_fallback()` — no temp files created
- `_transcribe_video_audio()` in video.py — creates temp audio files, cleaned in `finally` block

---

## 8. Fail-Silent vs Error-Return Patterns

| Scenario | Behavior |
|----------|----------|
| Playwright not installed | Returns `{"error": "playwright not installed", "status": "unknown"}` |
| browser-use not installed | Falls back to Crawl4AI/Playwright (success path) |
| Site unreachable | Returns `{"status": "unreachable", "error": "...", "url": target}` |
| Error phrase in page | Sets `status: "degraded"` — still returns ok |
| yt-dlp fails | Returns error string message |
| Audio transcription fails | Returns empty string `""` — no error shown to user |

---

## 9. Dependencies

```bash
pip install playwright browser-use langchain-openai crawl4ai
playwright install chromium
```

`check_site_health()` only needs `playwright`. `browse_task()` additionally needs `browser-use` and a configured `BROWSER_USE_MODEL` env var.

---

tokens_estimated: 650
inject_into: tool-output-formatting.md (browser agent section)