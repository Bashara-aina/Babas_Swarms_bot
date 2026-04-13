---
title: "Change line 46 from:"
created: 2026-04-12
type: review
tags: [review-2026-04-12-legion-wiring-audit]
---
# Change line 46 from:
build_system_prompt = _agents_module.build_system_prompt

# To import from agents/__init__.py directly:
from agents import build_system_prompt
```
Or update the module loading logic to load `agents/__init__.py` instead of `agents.py`.

#### Test Status:
```
FAILED tests/test_main.py::test_imports - AttributeError (pre-existing bug)
PASSED — 221 other tests
```

#### Verification Commands Blocked:
- `python scripts/verify_wiring.py` — fails on import
- `pytest tests/ -x --asyncio-mode=auto -q` — fails on test_imports

---
*Reviewer: @reviewer | Date: 2026-04-12*
