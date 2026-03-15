# Security Checklist (Telegram + Agentic Bot)

Use this checklist before shipping any handler/tool change.

## 1) Identity and access controls

- Every command handler must enforce single-owner authorization.
- Every callback handler must verify callback user identity.
- Never trust client-provided user IDs in message text.
- In aiogram 3.x, guard nullable identity objects (`from_user is None`).

### Threat: user ID spoofing assumptions
Mitigation:
- Only use `msg.from_user.id`/`cb.from_user.id` from Telegram update objects.
- Reject if user object absent.

## 2) Telegram-specific abuse paths

### Webhook spoofing (if webhook mode used)
- Validate secret token/header.
- Restrict endpoint exposure and verify source when possible.
- Prefer polling in private setups unless webhook security is explicit.

### Callback spinner deadlock
- Always call `cb.answer()` even on failure paths.
- Wrap callback parsing and message edits in try/except.

### Flood control / retry storms
- Handle `RetryAfter` and backoff.
- Avoid recursive resend loops on message failures.

## 3) Command execution safety (`/cmd`, tool shell)

- Block known destructive patterns and shell-pipe execution (`curl|bash`, `rm -rf`).
- Require explicit timeout for all subprocess operations.
- Capture stdout + stderr and sanitize returned output for Telegram.
- Never auto-restart service after ambiguous install/pull failure.

## 4) Secret hygiene

- Read secrets from env only (`os.getenv`).
- Never print full tokens in logs, chat replies, tracebacks.
- Mask keys in diagnostics (`xxxx...last4`).
- Keep `.env` out of git and backups that sync publicly.

## 5) Data and storage safety

- Validate file paths for traversal (`..`, symlink jumps when relevant).
- Restrict write operations to expected directories when possible.
- For uploaded or generated files, enforce size/type checks before processing.

## 6) Supabase/database controls

- Call `is_configured()` before `get_client()`.
- Surface Supabase error detail safely (no raw secret leakage).
- Use least-privilege key by default; reserve service role for privileged ops.

## 7) LLM/tool-call safety

- Treat model tool args as untrusted input.
- Validate tool names and argument schema before execution.
- Guard JSON parsing with `JSONDecodeError` handling.
- Add max-iteration cap for autonomous loops.

## 8) Prompt injection resistance

- Separate system constraints from user content.
- Do not allow user text to override authorization or execution guards.
- For web/doc ingestion, treat extracted content as untrusted and non-authoritative.

## 9) Observability without leakage

- Log event metadata, not private message content.
- Keep audit events for privileged actions (upgrade, shell, db).
- Use clear security-level logs for blocked dangerous operations.

## 10) Pre-deploy security gate

1. Authorization checks verified on all new handlers.
2. Callback handlers include `cb.answer()` on all paths.
3. External calls have timeouts and bounded retries.
4. Secrets never appear in logs/user-facing error strings.
5. Dangerous shell patterns are blocked.
6. Optional integrations fail-open, not crash-on-import.

If any item fails, do not deploy.

## 11) Bot-specific exploit scenarios

### Scenario: callback replay or stale callback misuse
- Risk: user taps old button triggering outdated action.
- Mitigation: verify expected context exists; fail safely with refresh prompt.

### Scenario: upgrade endpoint abuse
- Risk: unauthorized user triggers self-upgrade flow.
- Mitigation: strict user ID gate + explicit audit logging for upgrade requests.

### Scenario: shell command escalation
- Risk: crafted text bypasses weak blocklist.
- Mitigation: expand deny patterns + enforce timeout + no automatic privileged escalation.

### Scenario: rate-limit bypass via command fan-out
- Risk: flood of heavy commands degrades service.
- Mitigation: per-user throttling + bounded concurrent tasks.

## 12) Secure coding reminders for this stack

- Prefer allowlists for command/action routing where feasible.
- Sanitize HTML sent to Telegram (`html.escape`) on untrusted content.
- Avoid unsafe markdown handling that can break rendering or hide text.
- Treat all remote web/doc content as hostile input.

## 13) Incident response minimums

If security issue suspected:
1. disable risky command path (temporary guard)
2. rotate exposed keys
3. collect minimal forensic logs
4. patch root cause
5. add regression guard and deployment note
