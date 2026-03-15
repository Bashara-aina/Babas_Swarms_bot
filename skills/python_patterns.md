# Python Patterns (Async + Aiogram + Reliability)

Use these patterns for all Python changes in LegionSwarm. Priorities: async-safe I/O, explicit error paths, Telegram reliability, and predictable behavior under systemd.

## 1) Async-first architecture

### Rule set
- In `async def`, avoid blocking calls (`requests`, `subprocess.run`, direct heavy file I/O).
- Use async libraries (`aiohttp`, `httpx.AsyncClient`, `aiofiles`, `aiosqlite`).
- Bound every network/process operation with explicit timeout.
- Batch independent I/O with `asyncio.gather(..., return_exceptions=True)`.

### Pattern: bounded await
```python
result = await asyncio.wait_for(coro(), timeout=30)
```

### Pattern: cancel-safe background task
```python
task = asyncio.create_task(worker())
try:
	...
finally:
	task.cancel()
	with contextlib.suppress(asyncio.CancelledError):
		await task
```

## 2) Aiogram 3.x defensive handlers

### Nullability guards
- `msg.from_user` may be `None`.
- `msg.text` may be `None`.
- `msg.bot` may be `None`.

### Pattern
```python
if not msg.from_user:
	return
text = (msg.text or "").strip()
if msg.bot:
	await msg.bot.send_chat_action(msg.chat.id, "typing")
```

### Telegram mutation calls
Always wrap in try/except:
- `edit_text`
- `delete`
- `answer_photo`

Reason: message can be deleted/expired, or edit may violate Telegram constraints.

## 3) Error handling style

### Rules
- Catch specific exceptions first.
- Use boundary catches only for user-facing safety.
- Preserve useful context in logs (`logger.exception(...)` or structured details).
- Never silently swallow exceptions in core logic.

### Good boundary pattern
```python
try:
	data = await fetch()
except httpx.TimeoutException:
	return "timeout"
except httpx.HTTPError as e:
	return f"http error: {e}"
except Exception as e:
	logger.exception("unexpected fetch error")
	return f"unexpected error: {e}"
```

## 4) JSON and parsing safety

- Wrap `json.loads()` with `except json.JSONDecodeError`.
- Strip markdown code fences before decode when parsing LLM output.
- Validate shape before key access (`dict`/`list` checks).

## 5) File I/O safety

- Use `Path` APIs; avoid ad-hoc string paths.
- Handle `FileNotFoundError` and `PermissionError` where user paths are accepted.
- For async path, use `aiofiles` or `run_in_executor` for heavy sync libraries.

## 6) Typing conventions for this repo

- All public functions: full parameter + return type annotations.
- Prefer `typing.Optional`, `typing.Dict`, `typing.List`, `typing.Tuple` for Python 3.9 compatibility.
- Use `from __future__ import annotations` when forward references are present.

## 7) LLM call integration pattern

- Always pass `user_id` when calling `chat()`.
- Unpack tuple return values explicitly: `result, model = await chat(...)`.
- For system/internal calls without Telegram context, use `user_id="0"`.
- Use fallback-safe message handling for large responses via chunking.

## 8) Subprocess pattern (safe)

```python
proc = await asyncio.create_subprocess_shell(
	cmd,
	stdout=asyncio.subprocess.PIPE,
	stderr=asyncio.subprocess.PIPE,
)
try:
	out, err = await asyncio.wait_for(proc.communicate(), timeout=20)
except asyncio.TimeoutError:
	proc.kill()
	raise
```

## 9) Global state caution

Allowed for this single-owner bot, but still protect mutable globals:
- keep keys scoped by `user_id`
- avoid long-lived stale references
- clean up entries when tasks complete

## 10) Definition of done for Python changes

1. Type/syntax checks pass on changed files.
2. Async tasks are cancellation-safe.
3. Timeouts exist for external calls.
4. Handler guards cover aiogram nullable fields.
5. Service restart + log sanity check completed.

## 11) Aiogram command implementation checklist

- Parse command text from `(msg.text or "")` only.
- Avoid accessing `msg.from_user.id` without guard.
- Keep status/progress messages optional (edit may fail).
- If handler spins a typing task, cancel+await in `finally`.
- Chunk long answers to avoid Telegram size/format errors.

## 12) Service-safe startup patterns

- Avoid import-time side effects that require env secrets.
- Initialize optional integrations inside startup `try/except` blocks.
- Mark optional failures as non-fatal with clear log context.
- Keep mandatory env var validation explicit with fail-fast errors.

## 13) Anti-patterns to reject in review

- bare `except:` in business logic.
- unbounded `while True` loops without break/timeout path.
- global mutable state updates without user scoping.
- hidden retries that mask deterministic auth/schema failures.
- function signatures changed without updating call sites.

## 14) Refactor safety rules

- Preserve public function contracts unless all call sites are migrated.
- Prefer additive compatibility shims before removing legacy APIs.
- Keep handler behavior stable for existing commands.
- Avoid unrelated refactors in incident fixes.

## 15) Minimal telemetry conventions

- Log action + result + model/provider where relevant.
- Avoid user private content in logs.
- Include enough context for postmortem (command, component, duration).
- Use warning level for recoverable issues, error for failed user action.
