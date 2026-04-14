---
title: Worker Fix Get Relationship Context
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Task**: Fix missing import for `get_relationship_context`'
wikilinks: []
confidence: medium
source: research
---
# Worker Fix Log: get_relationship_context Import

**Date**: 2026-04-12  
**Task**: Fix missing import for `get_relationship_context`

## Root Cause
`llm_client/__init__.py` line 1114 used `get_relationship_context` but the function was never imported. The function is defined in `core/relationship_memory.py` line 164.

## Change Made
**File**: `llm_client/__init__.py`  
**Location**: Import section (line 39)

Added import:
```python
from core.relationship_memory import get_relationship_context
```

## Verification
```
pytest tests/ -x --asyncio-mode=auto -q
============================= 373 passed in 28.51s =============================
```

## Status: ✅ Complete
