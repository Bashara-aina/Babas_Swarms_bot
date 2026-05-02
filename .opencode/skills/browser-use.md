---
name: browser-use
description: "Use when the user wants to browse websites, interact with web pages, click buttons, fill forms, login, scroll, take screenshots, extract content from dynamic pages, test user flows, automate multi-step browser tasks, or do anything requiring an autonomous AI browser agent. Examples: \"Open example.com\", \"Click the login button\", \"Fill out the form\", \"Take a screenshot\", \"Test the checkout flow\", \"Automate browser task\", \"Browse to URL and extract data\", \"scroll down\", \"wait for page to load\", \"login to site\", \"submit form\". This skill is MiniMax-native with automatic retry and fallback handling. Auto-routes search queries to crawl4ai and interactive tasks to browser-use."
---

# browser-use

Python library for autonomous browser agents powered by LLMs. In this stack, all browser LLM calls route directly to the MiniMax API at `https://api.minimax.io/v1`.

## Quick start

```python
from tools.browser_runner import run_browser_task

result = run_browser_task(
    task="Find the contact email on example.com",
    max_steps=20,
    headless=True,
)
# result = {"success": bool, "result": str, "steps": int, "elapsed_ms": float, "url": str, "error": str|None}
```

## Using the Agent class directly

```python
import os
from browser_use.agent import Agent
from browser_use.llm.litellm import ChatLiteLLM
from browser_use.controller import Controller
from browser_use.browser import BrowserProfile, BrowserSession

llm = ChatLiteLLM(
    model="minimax/MiniMax-M2.7",
    api_key=os.environ.get("AI_GATEWAY_API_KEY", "your-api-key"),
    api_base="https://api.minimax.io/v1",
    temperature=0.3,
    max_tokens=4096,
)

profile = BrowserProfile(headless=True)
session = BrowserSession(browser_profile=profile)
controller = Controller()

agent = Agent(
    task="Click login and report the page title",
    llm=llm,
    browser=session,
    controller=controller,
    use_vision=True,
    max_steps=20,
)

history = agent.run_sync(max_steps=20)
print(history[-1].result)
```

## LLM signature

`ChatLiteLLM(model, api_key, api_base, temperature, max_tokens, max_retries, metadata)`

- `api_key` is `os.environ.get("AI_GATEWAY_API_KEY", "your-api-key")`
- `api_base` is `"https://api.minimax.io/v1"` (direct, not via LiteLLM proxy)
- `model` is `"minimax/MiniMax-M2.7"`

## Decision matrix

| Use case | Tool |
|---|---|
| Multi-step autonomous browsing (login, forms, SPAs) | `run_browser_task()` (browser-use) |
| Deterministic CLI automation with refs | `scripts/agent_browser_safe.sh` (agent-browser CLI) |
| Fast static content extraction | `crawl4ai` |
| QA smoke test | `tools/browser_agent.py` → `check_site_health()` (Playwright direct) |

## Policy

- **MiniMax only** — All browser LLM calls must use `minimax/MiniMax-M2.7` via `https://api.minimax.io/v1`
- **Forbidden models**: claude, anthropic, gpt-4, openai, gemini, groq, together — any invocation is a violation
- `scripts/browser_use_safe.sh` enforces this at the shell level for CLI usage
- `tools/browser_task_router.py` enforces this in Python code

## Output files

Browser traces and screenshots are saved to:
- `./output/browser_trace.txt` — step-by-step trace
- `./output/*.png` — screenshots on failure

## Related

- `tools/browser_task_router.py` — auto-routing between browser-use, crawl4ai, and agent-browser
- `tools/browser_runner.py` — this module
- `scripts/browser_use_safe.sh` — shell-level MiniMax guard for browser-use CLI
- `scripts/agent_browser_safe.sh` — shell-level MiniMax guard for agent-browser CLI
- `.opencode/skills/agent-browser.md` — agent-browser CLI skill