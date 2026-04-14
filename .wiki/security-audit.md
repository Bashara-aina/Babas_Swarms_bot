---
title: Security Audit
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- security-audit.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Every security vulnerability found — severity, fix status, and remediation.
wikilinks: []
confidence: medium
source: research
---

# Security Audit

## ONE-LINE SUMMARY
Every security vulnerability found — severity, fix status, and remediation.

## FACTS
- Raw subprocess.run() found in 26 locations across 14 source files (excluding .wiki/, openaugi, quarantine) — most are read-only commands but 4 modify crontab unsandboxed
- SandboxExecutor in core/shell/sandbox.py wraps asyncio.create_subprocess_shell with blocklist + allowed_dirs — GOOD
- tools/project_manager.py subprocess.run() modifies crontab — writes to system — NOT sandboxed
- tools/n8n_bridge.py subprocess.run() modifies crontab — NOT sandboxed
- core/daily_harvester/cron_setup.py subprocess.run() modifies crontab — NOT sandboxed
- handlers/admin_handlers.py has its own ALLOWED_USER_ID = int(os.getenv(...)) — separate from shared.py — potential inconsistency
- handlers/business_handler.py, handlers/whatsapp_handler.py, handlers/github_intel_handler.py each re-read ALLOWED_USER_ID independently — 4 separate sources of truth
- handlers/overnight_handler.py imports ALLOWED_USER_ID from shared.py — CORRECT pattern
- handlers/admin_handlers.py and handlers/debate_handlers.py use their own ALLOWED_USER_ID with same value — inconsistency risk
- Unknown user sends message: is_allowed() returns False → handler exits silently → no message sent → user gets no feedback — potential UX issue but not security hole (no data leaked)
- No ALLOWED_USER_ID on 3 handlers: need to verify all handlers check is_allowed() — grep shows 17 matches but 45+ handlers exist
- Telegram webhook: no webhook verification secret — anyone can send fake updates
- Bot token logged in plaintext in bot.log if TELEGRAM_BOT_TOKEN is logged — must not log token values
- _trim_log_text() in main.py limits log to 1200 chars — good but doesn't scrub tokens

## LEGION BEHAVIOR RULES
1. CRITICAL: All shell write operations (crontab, systemctl, git push) must use sandbox.py or be explicitly allowed with comment explaining why
2. CRITICAL: All handlers must call is_allowed(msg) or equivalent check before processing — verify at implementation time
3. HIGH: Consolidate ALLOWED_USER_ID to single source: handlers/shared.py ALLOWED_USER_ID only
4. HIGH: Bot token must never appear in logs — add scrubber for TELEGRAM_BOT_TOKEN in _trim_log_text()
5. MEDIUM: Webhook verification secret should be implemented for Telegram webhook endpoint
6. MEDIUM: Unknown user messages should receive brief "Legion is private" response instead of silent drop
7. LOW: Add audit log for all write operations (crontab, systemctl) to _audit_logger
8. LOW: Document which subprocess.run() calls are intentionally unsandboxed and why

## EXAMPLES
Attack scenario: Malicious user sends crafted message to trigger /cmd "rm -rf /"
Fix: computer_agent.py uses SandboxExecutor — command blocked by blocklist pattern rm\\s+-rf\\s+/ — ✅ SAFE

Attack scenario: Unknown user asks /budget
Fix: is_allowed() returns False — handler exits silently — no data leaked — ✅ SAFE (but poor UX)

Attack scenario: Attacker floods bot with messages
Fix: Telegram API rate limits protect bot — no per-user rate limit in Legion code

Attack scenario: Raw subprocess in tools/project_manager.py runs "crontab -" with user-controlled input
Fix: Input is hardcoded cron lines — not directly user-controlled — MEDIUM risk if cron_setup.py logic has bugs

## ANTI-PATTERNS
1. Circular import risk in handlers that re-import shared — handlers/admin_handlers.py imports from shared but also defines its own ALLOWED_USER_ID — creates split brain
2. Unreviewed subprocess.run() calls added without sandbox consideration — need code review gate
3. Logging user message without token scrubbing — _trim_log_text() truncates but doesn't scrub — possible token in error messages

## DEBATE RECORD
Advocate: 9 | Skeptic: 5 | Judge: WRITE 9
Judge note: Security gaps in crontab writes and multiple ALLOWED_USER_ID sources are confirmed issues — high impact.
