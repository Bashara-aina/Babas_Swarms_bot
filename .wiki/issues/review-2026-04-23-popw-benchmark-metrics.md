## Review: POPW benchmark metrics alignment
Date: 2026-04-23
Reviewer: @reviewer
Loop: #1

### Independent Verification

**Files verified to exist:**
- `/home/newadmin/swarm-bot/project/popw/working/code/industreal/evaluate.py` (985 lines, last modified Apr 23 05:05)
- `/home/newadmin/swarm-bot/project/popw/working/code/popw_main/evaluate.py` (927 lines, last modified Apr 23 05:07)
- `/home/newadmin/swarm-bot/project/popw/working/code/popw_main/benchmark_comparison.py` (475 lines, last modified Apr 23 05:12)
- `/home/newadmin/swarm-bot/project/popw/working/code/industreal/benchmark_comparison.py` (368 lines, last modified Apr 23 05:12)

**Syntax check (all exit 0):**
- `industreal/evaluate.py` ✅
- `popw_main/evaluate.py` ✅
- `popw_main/benchmark_comparison.py` ✅
- `industreal/benchmark_comparison.py` ✅

**git status:** Working tree has uncommitted changes across the swarm-bot repo. The 4 POPW files are all modified (staged or unstaged in the working/code submodule).

---

### ✅ Passed

| # | Criterion | Evidence |
|---|-----------|----------|
| 1 | **PSR POS independently computed, not aliased to edit_score** | `psr_pos` (line 592) is computed via `_find_runs()` and run-pair ordering comparison (lines 540–592), completely separate from `edit_score` which uses Levenshtein distance (lines 503–533). Distinct code paths. |
| 2 | **mcAP function exists and produces per-class AP** | `compute_activity_mcAP()` at line 194 of `popw_main/evaluate.py`. Iterates per class (lines 220–248), uses 11-point interpolation, returns mean. Called at line 701: `results['act_mcAP'] = compute_activity_mcAP(...)`. |
| 3 | **CLI output uses "Top-1", "Top-5", "AP@0.5" naming** | `popw_main/evaluate.py` line 887: `Top-1 (Activity Recognition)`. Line 895: `Top-5`. Line 918: `AP@0.5 (Object Segmentation)`. `industreal/benchmark_comparison.py` uses `Top-1`, `Top-5`, `mAP@0.5` consistently. |
| 4 | **benchmark_comparison.py scripts produce correct tables** | `popw_main/benchmark_comparison.py` — `print_comparison_table()` (lines 328–385) iterates `BENCHMARK_TARGETS`, maps keys to metrics, formats status. 12 benchmark rows covering all metrics. `industreal/benchmark_comparison.py` — `print_comparison_table()` (lines 133–260) with 6 benchmark rows. Both produce tabular output with Beat/N/A status. |
| 5 | **STORM-PSR arXiv ID is 2510.12385** | Verified in both benchmark_comparison.py files — all references use `arXiv:2510.12385`. No instance of old ID `2405.02505` found in any of the 4 changed files. |
| 6 | **Temporal localization marked N/A with explanation** | `popw_main/benchmark_comparison.py` lines 94–102: `is_na: True`, `na_note` explicitly states "POPW does not include a temporal action localization head". CLI output line 896: `⚠️ N/A — POPW does not include temporal localization head`. |
| 7 | **All scripts pass syntax check** | All 4 files: `python -m py_compile` returned exit code 0. |

---

### ⚠️ Warnings (non-blocking)

| # | Warning | Detail |
|---|---------|--------|
| 1 | Unused variable | `run_a_end` and `run_b_end` in `industreal/evaluate.py` line 577–578 are extracted from GT runs but never used (only `val_a`/`val_b` used). Non-blocking — correct behavior still. |
| 2 | Unused variable | `run_b_start` in `industreal/evaluate.py` line 578 extracted but never used. Non-blocking. |

---

### ❌ Blockers

None found.

---

### Decision
APPROVED ✅ — 0 blockers, all 7 checklist criteria pass.

### Loop Status
This is loop 1 of 3 maximum.
