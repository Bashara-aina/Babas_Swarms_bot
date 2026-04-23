---
name: agents-init-lint-fix
description: Fix lint errors in agents/__init__.py — import sorting and undefined Coroutine type
type: feedback
---

## Fix Applied

**File:** `agents/__init__.py`

**Errors fixed:**
1. `I001` — Import block un-sorted: added blank line after `from __future__ import annotations`
2. `F821` — Undefined name `Coroutine`: added `from collections.abc import Coroutine` and simplified return type annotation from `Coroutine[str, str, str]` to bare `Coroutine`

**Root cause:** `Coroutine` is defined in `collections.abc`, not a builtin. The old annotation syntax `Coroutine[X, Y, Z]` is only valid when using `from __future__ import annotations` in Python 3.9+ but the bare `Coroutine` without type params was still undefined.

**How to avoid:** Use `from collections.abc import Coroutine` for async return type annotations in this codebase.