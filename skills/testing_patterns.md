# Testing Patterns (LegionSwarm)

Testing priority in this project: prevent runtime crashes in handlers, validate async orchestration behavior, and harden integration boundaries (LLM, Supabase, shell/web tools).

## 1) Test pyramid for this bot

- **Unit tests (majority):** pure logic, parsers, formatters, routing decisions.
- **Service-layer tests:** `llm_client`, orchestrator functions with mocked dependencies.
- **Handler tests:** command/callback behavior with mocked `Message`/`CallbackQuery`.
- **Smoke integration tests:** startup and selected commands in controlled environment.

## 2) Async test baseline (`pytest-asyncio`)

```python
import pytest

@pytest.mark.asyncio
async def test_async_case():
    result = await some_async_fn()
    assert result == "ok"
```

Rules:
- Never run event loop manually inside tests.
- Use `AsyncMock` for async collaborators.
- Assert cancellation behavior for background tasks when relevant.

## 3) Aiogram handler testing patterns

### What to validate
- Authorization gate (`is_allowed` / `allowed_cb`).
- Null-safe handling (`from_user`, `text`, `bot`).
- Response behavior on success and on exceptions.
- Callback acknowledgement (`cb.answer`) always called.

### Mock strategy
- Mock `msg.answer`, `msg.answer_photo`, `status_msg.edit_text`, `status_msg.delete`.
- For callbacks, mock `cb.message` and `cb.answer`.
- Assert no crash when Telegram edit/delete fails.

## 4) Supabase test fixtures

Use boundary mocking rather than live cloud DB for most tests.

### Fixture guidelines
- Mock `tools.supabase_client.get_client` per test.
- Stub methods: `query`, `insert`, `update`, `rpc`, `health_check`.
- Return realistic payloads matching PostgREST shape.
- Inject HTTP error payloads to verify surfaced messages.

### Example failure cases
- `401` invalid key
- `404` missing table/RPC
- malformed JSON body
- timeout and retry path

## 5) LLM-facing tests

- Mock `chat()` and `agent_loop()` outputs explicitly (`(text, model)` tuple).
- Assert caller unpacks both values.
- Validate fallback behavior when first model fails.
- Include malformed model output tests (invalid JSON, unexpected schema).

## 6) Reliability test matrix

For each high-risk command (`/do`, `/screen`, `/orchestrate`, `/dbquery`):
1. Happy path.
2. Dependency unavailable.
3. Timeout.
4. Permission denied / not allowed user.
5. Telegram edit/delete exception.

## 7) E2E strategy for this repo

- Keep true E2E minimal and deterministic.
- Prefer one validated “golden path” per feature area.
- Avoid flaky external dependencies; mock unstable APIs where possible.

## 8) Anti-flake rules

- No hard sleep unless unavoidable; prefer awaited conditions.
- Use bounded timeouts in tests.
- Keep filesystem/network side effects isolated with temp dirs/mocks.
- Seed random data where randomness is used.

## 9) Required checks before merge

1. New/changed logic has at least one unit test.
2. Async code paths tested with `pytest.mark.asyncio`.
3. Error path coverage for external boundaries.
4. Tests run locally without needing private secrets.

## 10) Minimal handler test template

```python
@pytest.mark.asyncio
async def test_cmd_screen_not_allowed(monkeypatch):
    msg = AsyncMock()
    monkeypatch.setattr(module, "is_allowed", lambda _m: False)
    await module.cmd_screen(msg)
    msg.answer.assert_not_called()
```

Use this as the default starting point, then add scenario-specific assertions.

## 11) Command coverage protocol

For each command router:
1. Verify command exists in router file.
2. Verify no duplicate command handlers.
3. Verify command listed in README command docs.
4. Validate at least one smoke invocation path.

## 12) Callback coverage protocol

- Enumerate all emitted `callback_data` values.
- Ensure matching callback handlers exist.
- Add tests for unknown callback payload handling.
- Ensure callback always ends with `cb.answer()`.

## 13) Regression test template for bugfixes

When fixing a bug, add:
- one test reproducing pre-fix crash behavior
- one test validating post-fix expected output
- one guard test for nearby edge case

This prevents “fix then re-break” on future refactors.

## 14) Supabase interaction test matrix

- configured + healthy
- configured + unauthorized key
- configured + missing table
- not configured
- rpc installed vs missing fallback path

Assert user-facing messages remain actionable and safe.

## 15) CI expectations

- Fast tests (`-k unit`) run first.
- Integration subset next.
- Flaky network-dependent tests isolated/marked.
- Keep default CI runtime predictable and under practical limits.
