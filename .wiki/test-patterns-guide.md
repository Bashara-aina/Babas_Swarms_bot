---
title: Test Patterns Guide
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- test-patterns-guide.md
created: '2026-04-14'
updated: '2026-04-14'
summary: pytest-asyncio patterns, fixtures, and mocking strategies used in Legion's
  test suite.
wikilinks: []
confidence: medium
source: research
---

# TEST PATTERNS GUIDE

## ONE-LINE SUMMARY
pytest-asyncio patterns, fixtures, and mocking strategies used in Legion's test suite.

## TEST FRAMEWORK

### Core Stack
- **pytest** 8+ with **pytest-asyncio** plugin
- `asyncio_mode = "auto"` — coroutines auto-awaited without explicit `@pytest.mark.asyncio` (but decorators are still used for clarity)
- **pytest-cov** for coverage reporting
- **pytest-mock** available in CI

### Run Commands
```bash
# Standard run
pytest tests/ -x --asyncio-mode=auto -q

# With coverage
pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing -x

# Specific file
pytest tests/test_rate_limiter.py -v --tb=short

# Single test
pytest tests/test_rate_limiter.py::TestRateLimiter::test_blocks_over_limit -v
```

### CI Configuration
```yaml
# .github/workflows/ci.yml
- name: Run tests
  env:
    TELEGRAM_BOT_TOKEN: "0:test"
    ALLOWED_USER_ID: "12345"
  run: |
    python -m pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing \
      --ignore=tests/test_computer_control.py -x
```

Minimum coverage threshold: **10%** (CI gate only; engineering standard is 70%+).

---

## FIXTURES (conftest.py)

### Shared Fixtures Location
`tests/conftest.py` — module-scoped fixtures for Telegram mocks, LLM mocks, event loop.

### mock_bot
```python
@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(username="LegionBot", id=123))
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot
```

### mock_message
```python
@pytest.fixture
def mock_message(mock_bot):
    msg = AsyncMock()
    msg.bot = mock_bot
    msg.from_user = MagicMock(id=99999, username="testuser", first_name="Test")
    msg.chat = MagicMock(id=99999)
    msg.text = "/test"
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    msg.reply = AsyncMock()
    return msg
```

### mock_llm_response
```python
@pytest.fixture
def mock_llm_response():
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = "Mock LLM response"
    resp.choices[0].message.tool_calls = None
    resp.choices[0].finish_reason = "stop"
    resp.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    return resp
```

### mock_acompletion
```python
@pytest.fixture
def mock_acompletion(mock_llm_response):
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_llm_response) as m:
        yield m
```
Use this fixture to run any test that would otherwise call the LLM — fully offline.

### event_loop
```python
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

---

## ASYNC TEST PATTERNS

### Pattern 1: @pytest.mark.asyncio (explicit)
```python
@pytest.mark.asyncio
async def test_blocks_over_limit(self, limiter):
    for _ in range(3):
        await limiter.allow(user_id=1)
    assert await limiter.allow(user_id=1) is False
```

### Pattern 2: asyncio.run() in sync test
```python
def test_gather_jarvis_bundle_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEGION_JARVIS_MEMORY", "0")
    from core.jarvis_orchestrator import gather_jarvis_bundle
    b = asyncio.run(gather_jarvis_bundle("fix the training script", "4242"))
    assert b["goal"] == "fix the training script"
```

### Pattern 3: tmp_path fixture
```python
@pytest.mark.asyncio
async def test_quarantine_response(tmp_path: pytest.Fixture) -> None:
    import legion.anti_slop.core as core_module
    original_quarantine = core_module._QUARANTINE_DIR
    core_module._QUARANTINE_DIR = tmp_path / "_quarantine"
    try:
        path = await quarantine_response(content, query, result)
        assert path.exists()
    finally:
        core_module._QUARANTINE_DIR = original_quarantine
```

---

## MOCKING EXTERNAL DEPENDENCIES

### Mock litellm calls
```python
# With fixture
async def test_with_llm_mock(mock_acompletion):
    result = await some_llm_function("test prompt")
    mock_acompletion.assert_called()
    assert result is not None

# Inline patch
@pytest.mark.asyncio
async def test_openai_agents_bridge_handoff() -> None:
    with patch("core.openai_agents_bridge.chat", new=AsyncMock(return_value=("ok", "mock/model"))):
        from core.openai_agents_bridge import run_with_handoffs
        result = await run_with_handoffs("Say hello", start_agent="general")
        assert result.topology_used == "openai_agents_handoff"
```

### Mock DB with tmp_path
```python
@pytest.mark.asyncio
async def test_init_db(mock_db_path):
    with patch("tools.persistence.DB_PATH", mock_db_path):
        from tools import persistence
        await persistence.init_db()
        async with aiosqlite.connect(mock_db_path) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = await cursor.fetchall()
```

### Mock env vars with monkeypatch
```python
def test_meet_join_url_empty_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEGION_JARVIS_MEET_URL", "")
    # ... test behavior with unset env
```

---

## SMOKE TESTS

`tests/test_main.py` contains import-based smoke tests that run without pytest infrastructure:

```python
def test_imports():
    """Test that critical imports work."""
    try:
        import main
        import agents
        import llm_client
        import computer_agent
        from handlers import shared
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_config_loaded():
    from dotenv import load_dotenv
    load_dotenv()
    assert os.getenv("TELEGRAM_BOT_TOKEN") is not None
```

---

## PARAMETRIZED TESTS

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("topology", ["sequential", "mixture", "graph", "spreadsheet"])
async def test_swarm_topology(topology: str) -> None:
    with patch("core.swarm_topologies.chat", new=AsyncMock(return_value=("ok", "mock/model"))):
        from core.swarm_topologies import run_topology
        result = await run_topology("Summarize this task", topology=topology, agent_names=["general"])
        assert result.topology_used in {...}
```

---

## SKIP CONDITIONS

```python
def test_prompt_injection_detected(self, guard):
    try:
        from swarms_bot.security.guard import SecurityGuard
        guard = SecurityGuard()
    except ImportError:
        pytest.skip("SecurityGuard not available")
```

---

## ANTI-PATTERNS

1. **`time.sleep()` in async tests** — use `await asyncio.sleep()` instead
2. **Bare `except Exception`** — always use `pytest.raises()` for expected exceptions
3. **Blocking I/O in async tests** — use `run_in_executor()` or `await` directly
4. **Global mutable state** — use fixtures + `tmp_path` for isolation
5. **Testing implementation details** — prefer integration-style tests over mocking internal functions

---

## COVERAGE GAPS (Current)

| Area | Status |
|------|--------|
| Handlers (45+ routers) | Minimal smoke tests only |
| Core agent orchestration | Moderate coverage |
| Tools (65+ tools) | Sparse coverage |
| Memory / Mem0 | Limited integration tests |
| Security guard | Good coverage (test_security.py) |
| Quality gates | Good coverage (test_legion_quality.py) |
| Persistence | Good coverage (test_persistence.py) |

---

## ADDING NEW TESTS

1. Place in `tests/test_*.py` (one file per module)
2. Import from source using relative path or `sys.path.insert(0, ...)`
3. Use existing fixtures from `conftest.py`
4. Mark async tests with `@pytest.mark.asyncio`
5. Use `tmp_path` for file-system tests
6. Mock LLM calls with `mock_acompletion` fixture
7. Run: `pytest tests/ -x --asyncio-mode=auto -q`
