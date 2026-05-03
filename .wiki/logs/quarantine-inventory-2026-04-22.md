---
title: Quarantine Inventory 2026 04 22
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Quarantine Inventory Report

**Date:** 2026-04-22  
**Source:** `.wiki/_quarantine/` analysis via `revive_quarantine.py`

---

## Summary

| Category | Count |
|----------|-------|
| Total `.md` files in quarantine | 1640 |
| **JSON-frontmatter files** | 563 |
| — Good (score > 0.05, revive candidates) | 0 |
| — Bad (score ≤ 0.05, delete candidates) | 563 |
| **YAML-only files** (cannot process) | 1077 |

---

## JSON-Frontmatter Group Statistics

| Metric | Value |
|--------|-------|
| Min score | 0.0 |
| Max score | 0.0 |
| Avg score | 0.000 |

---

## Notes

- **JSON-frontmatter files** have the `{...}` block detected and parsed. All 563 have a score of exactly `0.0`, meaning none meet the `> 0.05` revive threshold.
- **YAML-only files** have frontmatter that does NOT match the JSON `{}` pattern — these are likely pure YAML frontmatter and cannot be auto-processed by `revive_quarantine.py`.
- **Sum check:** 563 + 1077 = 1640 ✅

---

## Action Items

1. All 563 JSON-frontmatter files have `score = 0.0` — **no revive candidates** exist at the current threshold of `0.05`.
2. All 563 JSON-frontmatter files are **delete candidates** (score ≤ 0.05).
3. 1077 YAML-only files require manual inspection or a separate processing path.
