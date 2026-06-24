# Condition-Based Waiting

## Principle

Never use fixed timeouts (`sleep`) when waiting for an async condition. Instead, poll for the actual state change.

## Good

```python
# Wait for file to appear
while not os.path.exists(path) and retries < 30:
    await asyncio.sleep(1)
    retries += 1
```

```python
# Wait for process to complete
process = await asyncio.create_subprocess_exec(...)
await process.wait()
```

## Bad

```python
# Don't do this
await asyncio.sleep(5)  # Hope that 5 seconds is enough
```

## Why

- Fixed timeouts are fragile — they break when latency changes
- They waste time — you wait longer than necessary
- They hide flakiness — tests pass or fail based on timing

## Exceptions

The ONLY acceptable uses of `sleep`:
1. Rate limiting (must have an explicit rate limit reason)
2. Allowing external system time to stabilize (document why)
3. Short debounce (100-300ms for UI debouncing)

## Application

- In tests: use `await` with timeouts, polling for expected state
- In hooks: don't sleep — hooks should be fast and non-blocking
- In async code: use `asyncio.wait_for()` with proper timeout
