---
title: Adr 003 Main Py Orphaned Except
type: decision
status: stub
tags: [decisions, general]
created: 2026-04-13
updated: 2026-04-13
summary: Stub — needs enrichment. Auto-added frontmatter during QC restructure.
wikilinks: []
confidence: low
source: migration
project: general
---

# ADR-003: Main.py Orphaned Except Block

**Date**: 2026-04-12  
**Status**: Accepted  
**Deciders**: Worker agent (audit task)

## Context

`main.py` contained an orphaned `except Exception as e:` block at lines 481-482 with no matching `try` block. This was:
- A syntax error that somehow passed CI
- A pre-existing bug not caught by tests

## Decision

Fixed the try/except structure to properly nest each except with its corresponding try block.

**Before**:
```python
try:
    # conversation history DB init
# Initialize session transcript store
try:
    # session transcript store init
except:
    ...
except:  # ORPHANED
    ...
```

**After**:
```python
try:
    # conversation history DB init
except:
    ...

try:
    # session transcript store init
except:
    ...
```

## Consequences

**Positive**:
- Syntax error resolved
- Proper error handling for each initialization step

**Negative**:
- None

## References

- `main.py:465-482` — fixed location
