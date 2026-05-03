---
title: Swarm 2026 04 23 Popw Benchmark Setup
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Swarm Run: benchmark metric system setup

**Date:** 2026-04-23
**Type:** FEATURE
**Task:** Align POPW codebase evaluation metrics so training results can be directly compared against benchmark papers in BENCHMARK_PAPERS.md and BENCHMARK_TABLES.md

## Pipeline Summary

| Stage | Agent | Status |
|-------|-------|--------|
| Context | @memory | ✅ No prior memory found — fresh task |
| Context | @explorer | ✅ Full codebase structure mapped |
| Planning | @planner | ✅ 5 contracts produced |
| Execution | @worker | ✅ All 5 contracts complete |
| Verification | @reviewer | ✅ APPROVED — 0 blockers |

## Contracts Executed

| # | Contract | Files | Status |
|---|----------|-------|--------|
| 1 | Fix PSR POS aliased to edit_score | industreal/evaluate.py | ✅ |
| 2 | Add mcAP + rename CLI metrics | popw_main/evaluate.py | ✅ |
| 3 | Create IKEA ASM benchmark_comparison.py | popw_main/benchmark_comparison.py | ✅ |
| 4 | Create IndustReal benchmark_comparison.py | industreal/benchmark_comparison.py | ✅ |
| 5 | Final documentation and footnotes | both scripts | ✅ |

## Files Changed

| File | Change | Size |
|------|--------|------|
| popw_main/evaluate.py | Added compute_activity_mcAP(), renamed Top-1/Top-5/AP@0.5 | 36,523B |
| popw_main/benchmark_comparison.py | New — 11 IKEA ASM metrics, ASCII comparison table | 15,424B |
| working/code/industreal/evaluate.py | Added independent psr_pos computation | 36,447B |
| working/code/industreal/benchmark_comparison.py | New — 6 IndustReal metrics, ASCII comparison table | 11,104B |

## Key Findings

1. **Memory**: POPW benchmark system was NOT in prior memory — new context established
2. **Symlink structure**: working/code/ is symlinked from /media/newadmin/master/POPW/working/code/
3. **psr_pos bug**: was aliased to psr_edit_score — now independently computed
4. **mcAP**: added compute_activity_mcAP() using existing all_act_logits/all_act_gt
5. **Temporal localization**: mAP@0.5 is N/A — POPW lacks temporal localization head
6. **arXiv corrections applied**: STEPs=2301.00794, STORM-PSR=2510.12385, PTMA=2508.17025

## Benchmark Targets Summary

**IKEA ASM** (11 metrics in popw_main/benchmark_comparison.py):
- Top-1 targets: 64.15% (RGB+pose), 60.4% (RGB front), 47.0% (all views)
- Pose: PCK@10px >64.3%, PCK@0.2 >88.0%
- Detection: AP@0.5 >85.3%
- Phase Classification: >37.02% (STEPs)
- Temporal: Kendall's Tau >0.91, mAP@0.5 >20.0% (⚠️ N/A)
- mcAP comparison: PTMA=84.47% csv, MiniROAD=80.84% cs

**IndustReal** (6 metrics in working/code/industreal/benchmark_comparison.py):
- Activity: Top-1 >66.45%, Top-5 >88.43%
- ASD Detection: mAP@0.5 >83.8%
- Head Pose: vs raw GT (⚠️ N/A)
- PSR F1 >0.901, PSR POS >0.812 (STORM-PSR, NOT B3 rule-based)

## Git Commit

`e221e85` — feat(popw): add benchmark comparison system for IKEA ASM and IndustReal