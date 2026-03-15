# Debugging Playbook (LegionSwarm)

Use this protocol for production-safe debugging in this codebase. It merges tactical debugging + root-cause strategy and is optimized for `aiogram 3.x`, `litellm`, `systemd`, `Supabase`, async Python, and Linux desktop control.

## 1) Triage in 5 minutes

1. Confirm impact scope: one command, one router, or full bot outage.
2. Capture exact failure path from logs (first error, not last cascade).
3. Classify failure type:
	 - Boot/import error
	 - Runtime handler error
	 - External API failure (LLM, Supabase, web)
	 - OS tool/display failure (`scrot`, `DISPLAY`, `XAUTHORITY`)
4. Verify reproducibility with a single minimal command.
5. Add a temporary marker log around suspect function entry/exit.

## 2) Root-cause protocol

### A. Import / startup crashes
- Check `journalctl -u swarm-bot -n 80 --no-pager`.
- Find first `Traceback` frame inside project files.
- Validate symbol existence (`from X import Y` must match real module exports).
- Watch for module/package shadowing (`agents.py` vs `agents/`).
- Fix import source, then restart and recheck logs.

### B. Handler runtime errors
- Validate aiogram nullability:
	- `msg.from_user` can be `None`
	- `msg.text` can be `None`
	- `msg.bot` can be `None`
- Wrap fragile Telegram ops in try/except:
	- `edit_text`, `delete`, `answer_photo`.
- Ensure long-running helper tasks (`_keep_typing`) are canceled in `finally`.

### C. LLM/tool-call errors
- Verify model chain and key availability (`/keys`).
- Confirm function signature at call site (`chat(..., user_id=...)`).
- If parse errors occur, isolate JSON parsing with strict `JSONDecodeError` handling.
- For rate limits, use fallback chain + bounded retry only.

### D. Desktop/screenshot failures
- Validate environment in service context (not shell context):
	- `DISPLAY`, `XAUTHORITY`, `scrot`, `gnome-screenshot`.
- Use multi-backend screenshot fallback (`scrot -> import -> gnome-screenshot -> xwd`).
- If systemd environment differs, set explicit service env and restart.

## 3) Async correctness checklist

- Every async call is awaited.
- No blocking I/O inside async path unless delegated to executor.
- Every subprocess has timeout + stdout/stderr capture.
- Background tasks are stored/canceled or intentionally daemonized with guard logs.
- Exceptions in loops are surfaced (not silently swallowed forever).

## 4) Database/Supabase debugging

- Always check configuration before client creation.
- When HTTP fails, surface Supabase JSON `message/error` to user.
- Validate table/RPC existence before assuming app bug.
- Prefer fail-open for optional DB features in chat flows.

## 5) Reliability patterns to apply immediately

- Use “narrow fallback” first (same provider alternate model) then broad fallback.
- Keep retries bounded and exponential (`2^attempt`) for transient failures only.
- Use defensive defaults:
	- `user_id="0"` for system/internal LLM tasks.
	- safe string handling with `(msg.text or "")`.
- Prefer idempotent handlers where possible.

## 6) Patch quality gate (must pass before shipping)

1. Reproduce bug before patch.
2. Implement smallest root-cause fix.
3. Verify syntax/errors for changed files.
4. Restart service and monitor logs for 30–60s.
5. Re-run failing command from Telegram.
6. Confirm no new warnings/errors introduced.

## 7) Common anti-patterns (do not do)

- Don’t “fix” by broad `except Exception: pass` in core paths.
- Don’t restart service automatically on uncertain install/pull failures.
- Don’t keep conflicting command handlers for same command.
- Don’t use shell-only assumptions when service runs under systemd.
- Don’t add retries for deterministic errors (bad import/signature/auth).

## 8) Incident report template (after fix)

- Symptom: what user saw.
- Root cause: exact file + condition.
- Fix: code change summary.
- Verification: command/log evidence.
- Prevention: guard/test/check added.

## 9) Fast commands

- `sudo systemctl status --no-pager swarm-bot`
- `sudo journalctl -u swarm-bot -n 120 --no-pager`
- `sudo journalctl -u swarm-bot -f`
- `python -m pytest -q` (targeted tests first)

If uncertain between two possible causes, instrument both with short-lived logs, validate one hypothesis at a time, and remove debug noise after confirmation.
