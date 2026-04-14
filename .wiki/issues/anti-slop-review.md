---
title: Anti Slop Review
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: '| File | Status | Issues |'
wikilinks: []
confidence: medium
source: research
---
| File | Status | Issues |
|
---
---|--------|--------|
| `core.py` | ✅ | Correct |
| `integration.py` | ⚠️ Fix imports | 1 import order issue |
| `monitor.py` | ✅ | Correct |
| `test_legion_quality.py` | ❌ Bugs + imports | 2 test bugs, 1 import issue |
| `nemo_config/config.yml` | ✅ | Correct (reference only) |
| `nemo_config/rails.co` | ✅ | Correct (reference only) |

---

## Detailed Findings

### ✅ `legion/anti_slop/core.py` — PASS

- Imports: stdlib only, correctly ordered (asyncio, json, logging, re, time, dataclasses, datetime, pathlib, typing)
- Async/await: correct — `guard_confidence` is async, `quarantine_response` uses `asyncio.to_thread`
- No hardcoded secrets
- Type hints: complete on all public functions
- Exception handling: specific catches (`json.JSONDecodeError`, `ValueError`, `TypeError`, `ImportError`) at line 207
- Formatting: f-strings only, no `.format()`
- `_update_stats` is private but imported by `integration.py` — this is intentional (internal API)
- Guard 3 `guard_critique`: word repetition check requires `len(w) > 3` — this excludes short words like "is" (len=2) and "need" (len=4). Note: "need" IS caught (len=4 > 3), but "is" is not because len("is")=2. This is a design choice, not a bug.
- `Legdict` cast at line 230: `Verdict(verdict_str)` — safe since we normalize above

---

### ⚠️ `legion/anti_slop/integration.py` — FIX IMPORT ORDER

**Line 20-33**: Imports need reorganization by ruff.

```python
# Current (broken across lines 20-33):
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, Coroutine, TypeVar

from legion.anti_slop.core import (
    QualityResult,
    run_quality_gate,
    quarantine_response,
    get_slop_stats,
    _update_stats,
)
```

Ruff I001: import block is un-sorted. Fix with `ruff check --fix` or manually reorder.

---

### ✅ `legion/anti_slop/monitor.py` — PASS

- Imports: correct (stdlib → third-party none → local)
- Async/await: correct — `_append_to_log` uses async file I/O, `load_historical` reads with `async with asyncio.Lock()` but the `with open()` inside is still sync. This is a **minor issue**: the lock is acquired but the actual I/O is sync, which is inconsistent but not blocking.
- No hardcoded secrets
- Type hints: complete
- `log_event` at line 110: fire-and-forget `asyncio.create_task(self._append_to_log(event))` — correct for non-blocking logging
- Line 156: `with open(log_path, "a") as f` — this is sync I/O inside an async function, but protected by the `async with asyncio.Lock()`. For correctness, this should be `aiofiles.open()` or `asyncio.to_thread()`. However, since this is fire-and-forget (line 138), it's acceptable for this use case.

**Minor warning** (not a blocker): Lines 155-157 could use `asyncio.to_thread()` for true async file I/O, but the lock protects against concurrent writes, so correctness is maintained.

---

### ❌ `tests/test_legion_quality.py` — TWO BUGS FOUND

#### Bug 1: `test_repetition_word_rejection` (line 95-100)

```python
def test_repetition_word_rejection() -> None:
    content = "The problem is is is is is is that we need need need need need to fix fix fix fix fix this"
    rejected, reason = guard_critique(content)
    assert rejected is True  # ❌ FAILS — returns False
```

**Root cause**: `guard_critique` at `core.py:158` requires `len(w) > 3`. The word "is" has len=2, so it doesn't trigger rejection even though it appears 6 times. Words "need" (len=4) and "fix" (len=4) appear 5 times each — also not caught since condition is `> 5`.

**Required fix**: Either:
1. Change condition to `count > 4 and len(w) > 2` (catches "is" x5+)
2. Or update test content to use longer words repeating 6+ times

**Recommendation**: Change `core.py:158` from `count > 5` to `count > 4` — catches more slop patterns including the test case.

#### Bug 2: `test_stats_accumulation` (line 212-226)

```python
async def test_stats_accumulation() -> None:
    reset_slop_stats()
    stats = get_slop_stats()
    assert stats.total_calls == 0  # ✓ passes

    content = "Valid response with specific technical details."
    await run_quality_gate(content, query="test")

    stats = get_slop_stats()
    assert stats.total_calls == 1  # ❌ FAILS — still 0
```

**Root cause**: `run_quality_gate()` does NOT call `_update_stats()`. The stats are only updated via `LegionQualityGateway` (integration.py line 102), not in the core pipeline directly.

**Required fix**: Either:
1. Add `_update_stats(quality_result)` at the end of `run_quality_gate()` in `core.py`
2. Or update the test to use `LegionQualityGateway` instead of calling `run_quality_gate` directly

**Recommendation**: Add `_update_stats(result)` to `run_quality_gate()` — this makes the core pipeline also update stats, which is the expected behavior.

#### Import issue (line 7-21)

Ruff I001: import block needs sorting. Run `ruff check --fix tests/test_legion_quality.py`.

---

## 🚨 Security Issues

**None found.**

- No hardcoded API keys or secrets
- No SQL injection vectors (no database queries)
- No user-input passed to `exec()` or `eval()`
- Quarantine path sanitization: line 315 uses regex to strip unsafe characters from query — safe

---

## Remaining Work (Stages 7, 8, 9)

Per `.wiki/logs/anti-slop-progress.md`, all stages show "⏳" status. The following are not yet complete:

| Stage | Task | Status |
|-------|------|--------|
| 7.1 | Identify handler file for `/slop_stats`, `/anti_slop_on`, `/anti_slop_off` commands | ⏳ NOT DONE |
| 7.2 | Add Telegram commands | ⏳ NOT DONE |
| 8.1 | Create `.github/workflows/quality-gate.yml` | ⏳ NOT DONE |
| 9.1 | Run full test suite | ⏳ NOT DONE |
| 9.2 | Run lint | ⏳ NOT DONE |
| 9.3 | Git commit + tag | ⏳ NOT DONE |

**Suggestion**: Telegram commands should likely live in `main.py` alongside existing `/quality_gate` command, or in `handlers/ecc_compat.py` if that handles bot commands.

---

## Checklist Summary

| Criterion | Status |
|-----------|--------|
| Correct import ordering | ⚠️ 2 files need fixes |
| Async/await correct (no `time.sleep`, no blocking I/O) | ✅ Core correct, monitor minor |
| No hardcoded secrets | ✅ |
| Type hints present | ✅ |
| Specific exception handling (no bare `except`) | ✅ |
| f-strings only (no `.format()`) | ✅ |
| Tests pass | ❌ 2 failures |
| Integration pattern (aiogram) | ✅ Follows gateway pattern |

---

## Required Fixes (Blockers)

1. **`core.py:158`**: Change `count > 5` to `count > 4` to catch word repetition more aggressively
2. **`core.py` or `test_legion_quality.py`**: Add `_update_stats(result)` to `run_quality_gate()` OR change test to use `LegionQualityGateway`
3. **`integration.py:20-33`**: Fix import order (ruff --fix)
4. **`test_legion_quality.py:7-21`**: Fix import order (ruff --fix)

---

## Files that are correct ✅

- `legion/anti_slop/core.py` — Correct implementation, clean architecture
- `legion/anti_slop/monitor.py` — Correct (minor async I/O note, not a blocker)
- `legion/anti_slop/nemo_config/config.yml` — Reference documentation, correct
- `legion/anti_slop/nemo_config/rails.co` — Reference documentation, correct

## Files that need fixes ❌

- `legion/anti_slop/integration.py` — Import order (non-blocking)
- `tests/test_legion_quality.py` — 2 test bugs + import order

## Security 🚨

None.