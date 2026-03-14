# Testing Patterns

## Test Structure (Arrange-Act-Assert)
```python
def test_feature():
    # Arrange: set up preconditions
    data = create_test_data()
    # Act: call the code under test
    result = process(data)
    # Assert: verify the outcome
    assert result.status == "success"
```

## Async Testing
- Use `@pytest.mark.asyncio` for async test functions
- Use `pytest-asyncio` fixture for async setup/teardown
- Mock async functions with `AsyncMock`

## Mocking
- Mock at the boundary (external APIs, databases, file I/O)
- Use `unittest.mock.patch` for temporary replacements
- Verify mock calls with `assert_called_once_with()`
- Use `side_effect` for simulating errors

## What to Test
- Happy path (expected inputs → expected outputs)
- Edge cases (empty input, None, max values, boundary conditions)
- Error paths (invalid input, network failures, timeouts)
- Integration: test component interactions with realistic data

## What NOT to Test
- Third-party library internals
- Private implementation details that may change
- Trivial getters/setters with no logic
