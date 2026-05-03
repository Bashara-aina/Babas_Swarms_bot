---
title: Reviewer Approved 2026 04 23 Popw Benchmark Metrics
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## ✅ APPROVED — POPW benchmark metrics alignment
Date: 2026-04-23
Reviewer: @reviewer
Task: POPW benchmark metrics alignment (PSR POS fix + mcAP + benchmark_comparison scripts)

### Verdict
**APPROVED ✅** — all 7 checklist criteria pass, 0 blockers.

---

### Checklist Results

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | PSR POS independently computed, not aliased to edit_score | ✅ PASS | `psr_pos` via `_find_runs()` + run-pair ordering (lines 540–592); `edit_score` via Levenshtein distance (lines 503–533) — completely separate code paths |
| 2 | mcAP function exists and produces per-class AP | ✅ PASS | `compute_activity_mcAP()` at line 194 of `popw_main/evaluate.py`; called at line 701 |
| 3 | CLI output uses "Top-1", "Top-5", "AP@0.5" naming | ✅ PASS | `evaluate.py` line 887 (`Top-1`), line 895 (`Top-5`), line 918 (`AP@0.5`) |
| 4 | benchmark_comparison.py scripts produce correct tables | ✅ PASS | Both scripts print properly formatted tables with Beat/Below/N/A status |
| 5 | STORM-PSR arXiv ID is 2510.12385 | ✅ PASS | All references in both benchmark_comparison.py files use `arXiv:2510.12385`; no old ID `2405.02505` in any changed file |
| 6 | Temporal localization marked N/A with explanation | ✅ PASS | `is_na: True` + explicit `na_note` in popw_main/benchmark_comparison.py lines 94–102 |
| 7 | All scripts pass syntax check | ✅ PASS | All 4 files: `python -m py_compile` → exit 0 |

---

### Files Reviewed

| File | Lines | Syntax |
|------|-------|--------|
| `project/popw/working/code/industreal/evaluate.py` | 985 | ✅ |
| `project/popw/working/code/popw_main/evaluate.py` | 927 | ✅ |
| `project/popw/working/code/popw_main/benchmark_comparison.py` | 475 | ✅ |
| `project/popw/working/code/industreal/benchmark_comparison.py` | 368 | ✅ |

---

### Non-blocking Warnings
- Unused variables `run_a_end`, `run_b_start`, `run_b_end` in `compute_psr_metrics` — correct behavior unaffected

### Review Loop
Loop 1 of 3 — approved without revisions.

---
PIPELINE COMPLETE ✅ — ready for git commit
