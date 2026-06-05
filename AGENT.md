# AGENT — Aider Self-Fix Loop for OpenCode Integration

## SCOPE — READ THIS FIRST, STRICTLY ENFORCED

You are ONLY authorized to read, edit, and fix files within these paths:
- `swarms_bot/`
- `agents/`
- `core/`
- `bridges/`
- `scripts/aider_fix_loop.py`
- `.opencode/`
- `task_orchestrator.py`
- `router.py`
- `llm_client.py`
- `llm_client/`
- `requirements.txt`
- `pyproject.toml`

**ABSOLUTE FORBIDDEN PATHS — NEVER TOUCH:**
- `cekwajar/` — separate SaaS project
- `cekwajar.id` — production symlink
- `cekwajar.id-*/` — backup zips/dirs
- `legion/` — separate Legion system
- `meeting/` — meeting notes
- `papers/` — research PDFs
- `design-system/` — UI project
- `supabase/` — database migrations
- `computer_agent/` — separate agent
- `popwadditional/` — unrelated project
- `project` — unrelated project
- Any `.zip`, `.pdf`, `.flatpak` file

If a file path is ambiguous or outside the above allowlist, **stop and ask** before editing.

## PRIMARY MISSION

Maintain and self-correct the **Swarms ↔ OpenCode integration layer** only.
This means:
1. Swarms bot correctly calls OpenCode via subprocess or API
2. OpenCode sessions start, receive tasks, and return results cleanly
3. Model routing (Minimax) works without errors
4. `aider_fix_loop.py` runs on boot and self-corrects test failures autonomously

## AIDER FIX LOOP — HOW IT WORKS

The script `scripts/aider_fix_loop.py` is the self-healing engine:
- Runs `pytest tests/test_integrations.py` → on failure, feeds stderr to aider `--message` (non-interactive)
- Model: MiniMax-M3 ONLY — no cascade, no fallback
- Escalates on API/auth error ONLY (not on test failure)
- Max retries: 10
- NOTE: `test_integration.py` excluded — it imports `minisweagent` which is not in the venv

## AUTOSTART BEHAVIOR

This loop starts automatically on system boot via systemd service:
`/etc/systemd/system/aider-fix-loop.service`
Logs are at: `/home/newadmin/swarm-bot/logs/aider_fix_loop.log`

## RULES FOR EDITS

- Always run `pytest tests/test_integrations.py -x --tb=short -q` before and after any edit
- Never run the full test suite (`pytest tests/`) — it will catch tests from other projects and import errors
- Never install packages globally — use the venv at `.venv/`
- Never modify `.env` directly — use `.env.example` as reference only
- After each fix, append a one-line summary to `FAILURES.md` with date + what was fixed

## WHEN TESTS KEEP FAILING

If 3 consecutive fix attempts fail on the same error:
1. Log the error to `FAILURES.md` with full traceback
2. Escalate to the next model in cascade
3. If all models exhausted, write `BLOCKED: <error>` to `logs/aider_fix_loop.log` and stop
Do NOT loop infinitely on the same unfixable error.