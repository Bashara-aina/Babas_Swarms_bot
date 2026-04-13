---
title: "Review: Pre-existing Test Failure"
type: review
tags: [003-pre-existing-test-failure]
---
# Review: Pre-existing Test Failure
**File:** `tests/test_humanization.py::test_temporal_graph_add_and_retrieve`  
**Severity:** ❌ Blocker (for test suite health)  
**Status:** Pre-existing, unrelated to changes in this session

## Finding
```
FAILED tests/test_humanization.py::test_temporal_graph_add_and_retrieve - TypeError: 'coroutine' object is not iterable
```

The test calls `graph.add_fact(...)` which is an async coroutine that is **not being awaited**:

```python
graph = TemporalKnowledgeGraph()
graph.add_fact("Bashara", "uses_model", "gemma4:e4b", confidence=1.0)  # coroutine not awaited
facts = graph.get_current_facts("Bashara")  # facts is also a coroutine
assert any(f["predicate"] == "uses_model" for f in facts)  # fails - facts is not iterable
```

## Root Cause
`TemporalKnowledgeGraph.add_fact()` and `get_current_facts()` are async methods, but the test calls them synchronously without `await`.

## Impact
- **115 tests pass**, only this 1 fails
- This failure is **not caused by changes in this session** — `test_humanization.py` was last modified in commit `5d43efc` ("feat: integrate humanization memory and orchestration layer") which predates this work
- The review checklist requires "Tests pass" — this is a pre-existing issue

## Recommendation
This is a pre-existing bug in the test suite, not introduced by the @worker changes. However, since pytest is part of the mandatory pre-commit checklist, this should be fixed separately:

```python
async def test_temporal_graph_add_and_retrieve() -> None:
    graph = TemporalKnowledgeGraph()
    await graph.add_fact("Bashara", "uses_model", "gemma4:e4b", confidence=1.0)
    facts = await graph.get_current_facts("Bashara")
    assert any(f["predicate"] == "uses_model" for f in facts)
```

**Decision for this review:** Marking as ⚠️ Warning (pre-existing) rather than ❌ Blocker since it is not related to the reviewed changes.
