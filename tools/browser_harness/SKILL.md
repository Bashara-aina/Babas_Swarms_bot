---
name: browser-harness
description: Direct browser control via CDP. Use when the user wants to automate, scrape, test, or interact with web pages. Connects to the user's already-running Chrome.
---

# browser-harness

Direct browser control via CDP. Read `helpers.py` in `tools/browser_harness/` — that's where the functions live. For setup, install, or connection problems, read `install.md`.

## Usage

```python
from tools.browser_harness.helpers import (
    goto_url, page_info, wait_for_load, capture_screenshot,
    click_at_xy, type_text, press_key, scroll,
    list_tabs, current_tab, switch_tab, new_tab, ensure_real_tab,
    js, http_get, upload_file, dispatch_key,
)

# Start browser harness
from tools.browser_harness.admin import ensure_daemon
ensure_daemon()

# Navigate and interact
goto_url("https://example.com")
wait_for_load()
info = page_info()

# Screenshot to see what's on screen
capture_screenshot("/tmp/page.png")

# Coordinate click (preferred over DOM — works through iframes/shadow DOM)
click_at_xy(x=400, y=300)

# Or find element and click by text
from tools.browser_harness.helpers import js, dispatch_key
dispatch_key("button:has-text('Submit')", "Enter")

# Type text
type_text("hello world")

# Tab management
tabs = list_tabs()
switch_tab(tabs[0])
new_tab("https://google.com")

# Ensure we're on a real user tab (not chrome://)
ensure_real_tab()
```

## Key principles

- **Coordinate clicks default** — `click_at_xy(x, y)` hits whatever is at that pixel. It passes through iframes, shadow DOM, and cross-origin boundaries at the compositor level. No selector hunting needed.
- **Screenshot first** — `capture_screenshot()` to see the current page, find targets visually, then click by coordinate or use the image to decide if you need DOM work.
- **New tab for first navigation** — use `new_tab(url)` for the first navigation so you don't clobber the user's active tab. `goto_url()` rewrites the current tab.
- **wait_for_load() after every navigation** — always call it after `goto_url` or `new_tab`.
- **ensure_real_tab()** — re-attach to a real page when the current tab is stale or an internal URL.
- **http_get() for static pages** — no browser needed for static pages/APIs. Use `ThreadPoolExecutor` for bulk HTTP.
- **Auth walls** — if redirected to login, stop and ask the user. Don't type credentials.

## Available helpers

### Navigation
- `goto_url(url)` — navigate current tab
- `new_tab(url)` — open new tab and switch to it
- `wait_for_load(timeout=15.0)` — poll until document.readyState == 'complete'
- `page_info()` — `{url, title, w, h, sx, sy, pw, ph}` or `{dialog: {...}}` if dialog open

### Input
- `click_at_xy(x, y, button="left", clicks=1)` — coordinate click
- `type_text(text)` — insert text via Input.insertText
- `press_key(key, modifiers=0)` — key events (Enter, Tab, ArrowLeft, etc.)
- `dispatch_key(selector, key, event)` — DOM KeyboardEvent on matched element
- `scroll(x, y, dy=-300, dx=0)` — mouse wheel scroll
- `upload_file(selector, path)` — set files on `<input type=file>`

### Visual
- `capture_screenshot(path="/tmp/shot.png", full=False, max_dim=None)` — PNG screenshot

### Tabs
- `list_tabs(include_chrome=True)` — list all page targets
- `current_tab()` — current tab targetId + url + title
- `switch_tab(target)` — switch by target dict or targetId string
- `ensure_real_tab()` — switch to first non-internal tab (recovery)
- `new_tab(url)` — open new tab

### DOM / JS
- `js(expression, target_id=None)` — run JavaScript, returns value
- `cdp(method, session_id=None, **params)` — raw CDP call

### Utility
- `http_get(url, headers=None, timeout=20.0)` — pure HTTP, no browser
- `drain_events()` — drain CDP event queue
- `wait(seconds)` — sleep

### Admin
- `ensure_daemon()` — idempotent start (auto-starts if needed)
- `daemon_alive()` — check if daemon is running
- `restart_daemon()` — stop daemon
- `run_setup()` — interactive browser attach
- `run_doctor()` — diagnostics

### Remote / Cloud
- `start_remote_daemon(name, profileName, **kwargs)` — start cloud browser
- `stop_remote_daemon(name)` — stop cloud browser
- `list_cloud_profiles()` — list Browser Use cloud profiles
- `sync_local_profile(profile_name, ...)` — sync local Chrome cookies to cloud

## Self-healing

When you need a helper that doesn't exist, **write it** into `helpers.py`. The harness is yours to extend.

```python
# Example: add upload_file capability
def upload_file(selector, path):
    doc = cdp("DOM.getDocument", depth=-1)
    nid = cdp("DOM.querySelector", nodeId=doc["root"]["nodeId"], selector=selector)["nodeId"]
    if not nid: raise RuntimeError(f"no element for {selector}")
    cdp("DOM.setFileInputFiles", files=[path], nodeId=nid)
```

## Domain skills

Site-specific knowledge lives in `tools/browser_harness/domain-skills/`. When you discover non-obvious patterns for a site (selectors, API endpoints, quirks), contribute back by creating a domain skill file.

## Design constraints

- No framework, no retries, no session manager
- Helpers stay short — browser primitives only
- CDP for anything helpers don't cover: `cdp("Domain.method", params)`
- Coordinate clicks + screenshots as the primary interaction model
- Connect to the user's running Chrome — don't launch your own browser