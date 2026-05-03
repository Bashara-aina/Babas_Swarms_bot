---
title: Planner 2026 04 23 Popw Benchmark Alignment
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Execution Order
Serial (must run in sequence):
  1. Contract #1 — Fix PSR POS in IndustReal evaluate.py
  2. Contract #2 — Add mcAP + rename IKEA ASM CLI metrics
  3. Contract #3 — Create popw_main/benchmark_comparison.py
  4. Contract #4 — Create industreal/benchmark_comparison.py
  5. Contract #5 — Add explanatory notes / fix PSR naming in comparison scripts

Parallel (can run simultaneously): none — all contracts have dependencies

Final gate (must run last): Contract #5

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PSR POS computation is ambiguous — POS formula may not match STORM-PSR paper | H | M | Use the most defensible definition: fraction of correctly ordered consecutive segment pairs. Add comment explaining the formula and citing STORM-PSR arXiv:2510.12385 |
| Temporal localization N/A may confuse users expecting full benchmark coverage | H | L | Add explicit "⚠️ N/A — POPW lacks temporal localization head" note in both the eval script and comparison script footer with recommended next steps |
| PTMA/MiniROAD mcAP naming collision — mcAP may not be comparable to act_mean_per_class_acc | M | M | Clearly label mcAP as "mcAP (PTMA/MiniROAD comparison)" and note the protocol difference (csv/cs vs standard) |
| Benchmark arXiv IDs in comparison scripts may go stale | L | L | All arXiv IDs sourced from BENCHMARK_PAPERS.md which has explicit correction table; use the corrected IDs (STEPs: 2301.00794, STORM-PSR: 2510.12385) |
| evaluate.py changes (Contract #2) may break existing training val loop | L | H | Only add mcAP as an additional dict key — do NOT modify existing metric computation paths; test by running evaluate.py with existing checkpoint |
| Import errors in benchmark_comparison.py when running standalone | M | M | Use try/except around imports; if config.py fails, read results from a pre-saved JSON fallback path |
