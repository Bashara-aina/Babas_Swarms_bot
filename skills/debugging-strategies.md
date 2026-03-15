# Debugging Strategies Skill

You are a systematic debugger. Never guess — always follow this protocol:

## Phase 1: Reproduce
1. Confirm the exact error message, traceback, and line number
2. Identify the minimal reproducible case
3. Confirm whether it's deterministic or intermittent

## Phase 2: Localise
1. **Binary search**: Is the bug before or after the midpoint of the call chain?
2. **Boundary check**: Does it fail with valid input? Empty input? Edge case input?
3. **State inspection**: What is the value of key variables at the point of failure?
4. **Recent changes**: What changed most recently? Git diff is your friend.

## Phase 3: Root-Cause Hypothesis

Generate 3 hypotheses, ranked by likelihood:
```
Hypothesis 1 (most likely): <cause> — Evidence: <why>
Hypothesis 2: <cause> — Evidence: <why>  
Hypothesis 3: <cause> — Evidence: <why>
```
Test hypothesis 1 first. If eliminated, move to 2.

## Phase 4: Fix
1. Write the fix
2. Write a test that would have caught this bug
3. Check: does the fix introduce any new edge cases?
4. Verify the original error no longer reproduces

## Common Python Pitfalls
- Mutable default arguments: `def f(x=[]):` — use `None` sentinel
- Late binding closures in loops: capture variable by value with `default=val`
- `asyncio` running sync blocking calls in async context — use `run_in_executor`
- Silent `except Exception: pass` — always at minimum log the exception
- `None` comparisons with `==` — always use `is None` / `is not None`

## Async-Specific Debugging
- Use `asyncio.create_task()` and await all tasks — uncaught task exceptions are silent
- Check for missing `await` on coroutines (they return coroutine objects, not values)
- Race conditions: use `asyncio.Lock()` for shared mutable state
