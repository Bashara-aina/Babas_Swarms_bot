---
name: writing-plans
description: >-
  Break approved designs into bite-sized executable tasks. Each task is 2-5
  minutes with exact file paths, code, and verification steps. Use after
  brainstorming produces an approved spec.
---

## Checklist

1. **Read the spec** — load `.superpowers/specs/YYYY-MM-DD--design-slug.md`
2. **Decompose into tasks** — each task independently executable, 2-5 minutes
3. **Each task must have**: title (imperative), exact file paths, code to write, verification steps, dependencies
4. **Save plan** — write to `.superpowers/plans/YYYY-MM-DD--design-slug--plan.md`
5. **Print task list** — show the user the plan
6. **Offer to execute** — ask if user wants to invoke `executing-plans` now

## Plan Template

```markdown
# Plan: [Design Title]

## Tasks

### Task 1: [Imperative title]
**Files:** `path/to/file.py`
**Depends on:** None
**Code:**
```python
# exact code to write
```
**Verify:** Run `pytest path/to/test_file.py::test_name`

### Task 2: [Imperative title]
**Files:** `path/to/file2.py`
**Depends on:** Task 1
**Code:**
```python
# exact code to write
```
**Verify:** Run `make check`

### Task 3: ...
```
