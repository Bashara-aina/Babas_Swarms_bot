# Testing Anti-Patterns

## 1. Testing Implementation, Not Behavior

**Bad:** Testing that a specific function was called with specific args.
**Good:** Testing that the system produces the correct output for given input.

```python
# BAD — tests implementation detail
def test_save_user_calls_database():
    user_service.save_user(data)
    assert db.insert.called_once_with(data)

# GOOD — tests behavior
def test_save_user_persists_data():
    user_id = user_service.save_user(data)
    saved = db.get_user(user_id)
    assert saved.email == data.email
```

## 2. Mocking Everything

**Bad:** Mocking databases, APIs, filesystems, time — tests pass but don't verify real behavior.
**Good:** Mock at system boundaries only (external APIs, hardware). Use real implementations for internal components.

## 3. Testing Happy Path Only

**Bad:** Only test the "everything works" case.
**Good:** Test: empty inputs, invalid inputs, network errors, auth failures, rate limits, concurrent access.

## 4. Brittle Assertions

**Bad:** Asserting exact strings, exact timestamps, order-dependent results.
**Good:** Asserting structural properties, content presence, behavioral outcomes.

## 5. Flaky Tests

**Bad:** Tests that pass 90% of the time. Sleep-based timing. Network-dependent tests without retry.
**Good:** Deterministic tests. Use condition-based waiting. Isolate external dependencies.

## 6. Test Pollution

**Bad:** Tests that modify shared state and don't clean up.
**Good:** Each test creates its own data and cleans up after itself. Use fixtures with proper teardown.

## 7. Missing Edge Cases

Always test:
- Empty/missing input
- Maximum input size
- Concurrent access
- Error responses from dependencies
- Type mismatches
- Timeouts

## 8. Over-Mocking Setup

**Bad:** 50 lines of mock setup for 5 lines of test logic.
**Good:** If you need lots of mock setup, reconsider the architecture. Use integration tests for complex scenarios.
