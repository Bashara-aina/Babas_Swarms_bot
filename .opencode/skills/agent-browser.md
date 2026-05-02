---
name: agent-browser
description: "Use when the user wants deterministic browser automation with precise control — no AI involved. Examples: \"open example.com\", \"click the button with ref @e1\", \"fill the login form\", \"take a screenshot\", \"check if element exists\", \"extract text from selector\", \"wait for network idle\", \"scroll down 300px\", \"get the page HTML\", \"list open tabs\", \"capture HAR\". Also for: CLI-based browser testing, scripted browser flows, extracting refs/selectors, network monitoring, tab management. Prefer browser-use for complex multi-step AI tasks."
---

# agent-browser

Use `scripts/agent-browser-safe.sh` for browser automation.
Never call `agent-browser` directly if chat/model config may be inherited from the shell.

## Core workflow
1. `scripts/agent-browser-safe.sh open <url>`
2. `scripts/agent-browser-safe.sh snapshot -i --json`
3. Parse refs like `@e1`, `@e2`
4. Interact using `click`, `fill`, `hover`, `get text`
5. Re-snapshot after page changes

## Preferred usage
- Use `--json` whenever the output is consumed by an agent.
- Use refs from snapshot, not brittle CSS selectors.
- Use `batch` for multi-step deterministic flows.
- Use `wait --load networkidle` before extracting final state.

## Allowed
- open, snapshot, click, fill, type, wait, screenshot, get text, get html, network requests, har, tab, dialog, state save/load, vitals

## Forbidden by default
- `chat` unless AI_GATEWAY_MODEL is explicitly `minimax/MiniMax-M2.7`
- cloud browser providers
- iOS/Appium mode

## Safety
- Prefer `--allowed-domains` when automating third-party sites.
- Prefer `--content-boundaries` to isolate page text from tool output.
- Keep `AGENT_BROWSER_MAX_OUTPUT` capped.