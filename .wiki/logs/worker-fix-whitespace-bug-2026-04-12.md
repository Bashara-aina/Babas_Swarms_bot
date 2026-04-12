# Worker Fix: Leading Whitespace Bug in enforce_gsa_structure()

**Date:** 2026-04-12  
**Agent:** @worker  
**Task:** Fix off-by-character bug in `core/character_enforcer.py`

## Problem
When input had leading whitespace before a banned opener (e.g., `"  iya, ada masalah"`), the function produced malformed output `", ada masalah"` instead of `"ada masalah"`.

## Root Cause
`lower` was created by stripping `text`, but the slicing `text[len(opener):]` used the original unstripped string, causing an off-by-character error.

## Fix Applied
In `core/character_enforcer.py` (lines 124-131), changed:
```python
def enforce_gsa_structure(text: str) -> str:
    """Strip banned openers and closers from GSA-style responses."""
    stripped = text.lstrip()
    lower = stripped.lower()
    # Kill banned openers
    for opener in GSA_BANNED_OPENERS:
        if lower.startswith(opener):
            text = stripped[len(opener) :].lstrip()
            text = text[0].upper() + text[1:] if text else text
```

Now `stripped` is used consistently for both comparison and slicing.

## Verification
```python
from core.character_enforcer import enforce_gsa_structure
assert "Ada masalah" == enforce_gsa_structure("  iya, ada masalah")
assert enforce_gsa_structure("  ok, mari kita") == "Mari kita"
assert "normal text" == enforce_gsa_structure("normal text")
```

## Test Results
Full smoke test: **305 passed**, 1 warning (unrelated requests library version).

## Status
✅ Complete — no regressions.
