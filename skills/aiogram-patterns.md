# Aiogram 3.x Patterns (Legion)

Apply these patterns for robust Telegram handlers in this project.

## 1) Router architecture

- Keep feature-based routers (`handlers/*.py`).
- Register order matters: specialized routers first, catch-all last.
- Avoid duplicate command handlers across routers.

## 2) Handler safety baseline

For every message/callback handler:
- guard authorization (`is_allowed` / `allowed_cb`)
- guard nullable fields (`from_user`, `text`, `bot`, `message`)
- wrap Telegram mutations (`edit_text`, `delete`, `answer_photo`) in try/except

## 3) FSM for multi-step flows

Use FSM when:
- user input spans multiple sequential prompts
- validation depends on previous step
- cancellation/resume needed

Pattern:
1. set state
2. validate input
3. persist temporary context
4. transition or finish

## 4) Middleware usage

Recommended middlewares:
- auth middleware (single-user or allowlist)
- logging middleware (metadata only, no sensitive payloads)
- throttling middleware for anti-flood

Avoid heavy external I/O in middleware path.

## 5) Inline keyboards + callback parsing

- Keep callback_data short and structured (`prefix:action[:id]`).
- Always handle every callback_data pattern you emit.
- Always `await cb.answer()` to stop spinner.

## 6) Edit vs delete vs answer strategy

- `edit_text`: use for status/progress updates of same message.
- `delete`: use when replacing temporary status message.
- `answer`: use for final output, especially multi-chunk replies.

Fallback rule: if edit/delete fails, send fresh message.

## 7) RetryAfter / flood control

- Catch `RetryAfter` and backoff accordingly.
- Avoid tight loops of retries.
- Chunk long outputs to reduce resend failures.

## 8) File sending patterns

- Local file path: `FSInputFile`
- In-memory bytes: `BufferedInputFile`
- Remote URL: `URLInputFile`

Before send:
- check file exists
- check non-zero size
- sanitize caption length/format

## 9) Polling vs webhook tradeoff

- Polling: simpler ops, ideal for private/single-owner bots.
- Webhook: lower latency, requires endpoint hardening and secret checks.

Current project default: polling with systemd reliability.

## 10) Common aiogram gotchas

1. `from_user` can be `None`.
2. message too old to edit.
3. callback without `message` in some update shapes.
4. `msg.bot` may be unavailable in edge contexts.
5. duplicate command handlers cause routing ambiguity.

## 11) Background task lifecycle

If using `asyncio.create_task` in handlers:
- keep task reference
- cancel in `finally`
- await cancellation (`CancelledError` suppressed)

## 12) Recommended handler skeleton

```python
@router.message(Command("x"))
async def cmd_x(msg: Message) -> None:
    if not is_allowed(msg) or not msg.from_user:
        return
    status = await msg.answer("working...")
    task = asyncio.create_task(_keep_typing(msg))
    try:
        result = await do_work()
        try:
            await status.delete()
        except Exception:
            pass
        await msg.answer(result)
    except Exception as e:
        try:
            await status.edit_text(f"error: {e}")
        except Exception:
            await msg.answer(f"error: {e}")
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
```
