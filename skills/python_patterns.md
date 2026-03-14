# Python Patterns

## Async Best Practices
- Use `async with` for context managers (aiohttp sessions, aiosqlite connections)
- Never call blocking I/O (open(), requests.get()) inside async functions — use aiofiles, httpx
- Use `asyncio.gather()` for concurrent independent operations
- Use `asyncio.wait_for(coro, timeout=N)` to prevent hangs

## Error Handling
- Catch specific exceptions, never bare `except:`
- Use `except Exception as e:` at boundaries, log with `logger.exception()`
- Context managers for cleanup (`async with`, `try/finally`)
- Return early on validation failure

## Type Hints
- All function signatures should have type annotations
- Use `X | None` instead of `Optional[X]` (Python 3.10+)
- Use `from __future__ import annotations` for forward references

## Pythonic Idioms
- List/dict comprehensions over loops for transformations
- F-strings for formatting (never `%` or `.format()`)
- `pathlib.Path` over `os.path`
- Dataclasses for data containers
- Enum for fixed choices
- `contextlib.suppress()` for ignored exceptions
