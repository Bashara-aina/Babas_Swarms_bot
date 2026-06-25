# Failure Trajectory Log
**Project:** Babas Agency Swarm | **File:** FAILURES.md
**Purpose:** M2.7 Evaluation Set Seed — all failure trajectories.
Every mistake captured once, never again. Feed back into every session.

---

## Template (copy this for each failure)

```markdown
### [DATE] — [Short Title]
Task: what was attempted
Approach: what was tried
Failure mode: what went wrong and why
Root cause: the actual underlying problem
Fix applied: what resolved it
Prevention rule: what would stop this happening again
Tags: [legion, memory, intent-router, ...]
```

---

## Existing Known Issues (seeded from CLAUDE.md Section 11)

### 2026-04-13 — TelegramBadRequest: can't parse entities
Task: User-facing Telegram responses with Markdown
Approach: Used parse_mode="Markdown" for bot messages
Failure mode: Bot crashed with TelegramBadRequest when special characters appeared in user text
Root cause: parse_mode="Markdown" silently fails on `<`, `>`, `&`, `_` in user content
Fix applied: Switched ALL handlers to parse_mode="HTML" + html.escape() on all user-sourced text
Prevention rule: Never use bare parse_mode="Markdown". Use parse_mode="HTML" or parse_mode="MarkdownV2" with full escaping.
Tags: [telegram, handlers, security]

### 2026-04-13 — Ollama VRAM overflow on multi-model chains
Task: Sequential LLM calls with multiple Ollama models
Approach: Loaded gemma3:12b then phi4 sequentially in same session
Failure mode: CUDA out of memory — VRAM not released between models
Root cause: Ollama doesn't auto-release VRAM when model is swapped; RTX 3060 12GB insufficient for loaded models
Fix applied: `ollama stop <model>` before loading next. Sequential chains only, never parallel on VRAM-limited hardware.
Prevention rule: Always run `ollama stop <model>` before loading a different model on RTX 3060. Budget VRAM carefully.
Tags: [ollama, vram, gpu]

### 2026-04-13 — sentence-transformers v5 cache mismatch
Task: Semantic routing with sentence-transformers embeddings
Approach: Installed latest sentence-transformers (v5) on existing project
Failure mode: All cached embeddings failed to load — v5 cache format incompatible with v4
Root cause: sentence-transformers v5 breaks v4 cache format on disk
Fix applied: `rm -rf ~/.cache/huggingface/hub/` and re-download all models
Prevention rule: Pin sentence-transformers to a known-working version. Check cache compatibility before upgrading.
Tags: [ml, embeddings, dependencies]

### 2026-04-13 — browser-use silent failure
Task: Autonomous web browsing with Playwright + browser-use
Approach: Deployed browser-agent without verifying Playwright installation
Failure mode: browser-use called Playwright which wasn't installed — silent failure, no screenshots returned
Root cause: browser-use requires `playwright install chromium` after pip install; no error surfaced to user
Fix applied: `playwright install chromium` added to deployment checklist. Now part of setup script.
Prevention rule: After pip install browser-use, always run `playwright install chromium --with-deps`. Verify with test screenshot.
Tags: [browser, playwright, deployment]

### 2026-04-13 — systemd GPU not visible to bot
Task: Running swarm-bot as systemd service on GPU machine
Approach: Installed and started service without CUDA configuration
Failure mode: All Ollama/vision operations failed in service context — GPU not accessible
Root cause: systemd services don't inherit user environment variables including CUDA_VISIBLE_DEVICES
Fix applied: Added `Environment="CUDA_VISIBLE_DEVICES=0"` to systemd service override
Prevention rule: Systemd services need explicit GPU configuration. Always test service mode separately from shell mode.
Tags: [systemd, gpu, deployment]

### 2026-04-13 — /cmd shell injection risk
Task: User command execution via /cmd handler
Approach: Passed user input directly to subprocess shell
Failure mode: Potential shell injection if user sent `; rm -rf /`
Root cause: User input not sanitized before shell execution
Fix applied: asyncio.wait_for(proc, timeout=30) + input sanitization + allowed command list only
Prevention rule: All /cmd input goes through allowlist + timeout. Never pass raw user input to shell.
Tags: [security, shell, handlers]

### 2026-04-14 — Groq returns XML instead of JSON for tools
Task: Tool-calling LLM calls via Groq provider
Approach: Standard json.loads() on Groq tool responses
Failure mode: Groq occasionally returned XML-formatted error instead of JSON, causing json.JSONDecodeError
Root cause: Groq has a known quirk where certain tool call failures return XML instead of JSON
Fix applied: `_parse_groq_xml_tool_call()` in llm_client.py detects XML and recovers gracefully
Prevention rule: Always wrap json.loads() in try/except. Check for XML patterns in error recovery paths.
Tags: [llm, groq, error-handling]

### 2026-04-14 — Rate limit loop without backoff
Task: High-volume LLM request loop via litellm
Approach: Fire-and-forget retry on RateLimitError
Failure mode: Got stuck in tight retry loop — 60 failed requests in 30 seconds, API banned
Root cause: No cooldown between retries on litellm.RateLimitError
Fix applied: 60-second cooldown + next provider fallback chain implemented in llm_client.py
Prevention rule: Always implement exponential backoff on rate limit errors. Never retry immediately.
Tags: [llm, reliability, rate-limits]

### 2026-04-14 — Intent router silent default
Task: Message classification for routing
Approach: If all intent scores below threshold, silently default to general agent
Failure mode: Unclassifiable messages always routed to general — even when they were security-sensitive
Root cause: No explicit handling for low-confidence classification
Fix applied: Confidence threshold at 0.35 — if all below, route to general but log with warning flag
Prevention rule: Never silently default on ambiguous input. Always log low-confidence decisions.
Tags: [intent-router, reliability]

---

## Accumulated Failures (append new entries below)

<!-- Add new failures above this line. Group by root cause when patterns emerge. -->
