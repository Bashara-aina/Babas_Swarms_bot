# MonotonicDecoder Oracle Bound (Opus 141 Q46) — CPU Verification

**Date:** 2026-07-07
**Device:** CPU-only (numpy), OOM-safe
**Tolerance:** +/-3 frames
**Hysteresis:** sustain_hi=0.5, sustain_lo=0.3, sustain_min=3

## Summary

| Condition | Oracle Macro F1 | Oracle Micro F1 | GT Transitions | Pred Transitions |
|-----------|----------------|----------------|----------------|------------------|
| **Sustained** (procedure_order=True) | **0.5966** | 0.4439 | 109 | 34 |
| **Relaxed** (procedure_order=False) | **0.8807** | 0.7146 | 109 | 86 |

## Verification vs Agent-25 (GPU)

| Metric | Agent-25 (GPU) | This Run (CPU) | Diff |
|--------|----------------|----------------|------|
| Sustained Macro F1 | 0.5947 | 0.5966 | +0.0019 |
| Relaxed Macro F1 | 0.8750 | 0.8807 | +0.0057 |

**Result: VERIFIED** - CPU oracle matches Agent-25 GPU result within 0.01.

## Per-Component Oracle F1 (Sustained)

| Component | Mean F1 | Std | Min | Max |
|-----------|---------|-----|-----|-----|
| comp0 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp1 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp2 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp3 | 0.9375 | 0.2421 | 0.0000 | 1.0000 |
| comp4 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp5 | 0.0625 | 0.2421 | 0.0000 | 1.0000 |
| comp6 | 0.1250 | 0.3307 | 0.0000 | 1.0000 |
| comp7 | 0.4375 | 0.4961 | 0.0000 | 1.0000 |
| comp8 | 0.5000 | 0.5000 | 0.0000 | 1.0000 |
| comp9 | 0.4375 | 0.4961 | 0.0000 | 1.0000 |
| comp10 | 0.0625 | 0.2421 | 0.0000 | 1.0000 |

## Per-Component Oracle F1 (Relaxed)

| Component | Mean F1 | Std | Min | Max |
|-----------|---------|-----|-----|-----|
| comp0 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp1 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp2 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp3 | 0.9375 | 0.2421 | 0.0000 | 1.0000 |
| comp4 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp5 | 0.6250 | 0.4841 | 0.0000 | 1.0000 |
| comp6 | 0.6250 | 0.4841 | 0.0000 | 1.0000 |
| comp7 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp8 | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| comp9 | 0.9375 | 0.2421 | 0.0000 | 1.0000 |
| comp10 | 0.5625 | 0.4961 | 0.0000 | 1.0000 |

## Interpretation

**Sustained Oracle Macro F1 = 0.5966 < 0.85.** The decoder IS a significant bottleneck when procedure order is enforced. The hardcoded sequential chain (comp0->comp10) suppresses many valid GT transitions.

**Relaxed Oracle Macro F1 = 0.8807 (0.85-0.95).** Hysteresis alone causes mild degradation. Some transitions close together are suppressed by sustain_min=3.

### Bottleneck Analysis

The gap between sustained (0.5966) and relaxed (0.8807) reveals that the hardcoded sequential procedure-order constraint (comp0->comp1->...->comp10) is the primary bottleneck, suppressing ~32% of achievable F1. Hysteresis alone (sustain_min=3) accounts for only 11.9% F1 loss.

## Per-Recording Results (Sustained)

| Recording | Frames | GT Trans | Pred Trans | Macro F1 | Micro F1 |
|-----------|--------|----------|------------|----------|----------|
| 05_assy_0_1 | 2918 | 10 | 3 | 0.4545 | 0.4615 |
| 05_assy_2_2 | 2323 | 10 | 4 | 0.5455 | 0.5714 |
| 05_main_0_1 | 1380 | 4 | 1 | 0.7273 | 0.4000 |
| 14_assy_0_1 | 3005 | 9 | 3 | 0.4545 | 0.5000 |
| 14_main_0_1 | 1685 | 4 | 1 | 0.7273 | 0.4000 |
| 14_main_2_2 | 1404 | 3 | 1 | 0.8182 | 0.5000 |
| 14_main_2_3 | 1679 | 5 | 0 | 0.7273 | 0.0000 |
| 20_assy_0_1 | 2854 | 9 | 3 | 0.4545 | 0.5000 |
| 20_assy_3_6 | 2967 | 8 | 3 | 0.5455 | 0.5455 |
| 20_main_0_1 | 2066 | 4 | 1 | 0.7273 | 0.4000 |
| 24_assy_0_1 | 2158 | 9 | 3 | 0.4545 | 0.5000 |
| 24_assy_2_4 | 2952 | 8 | 3 | 0.5455 | 0.5455 |
| 24_main_0_1 | 1371 | 5 | 1 | 0.6364 | 0.3333 |
| 26_assy_0_1 | 3093 | 9 | 3 | 0.4545 | 0.5000 |
| 26_assy_1_5 | 4587 | 8 | 3 | 0.5455 | 0.5455 |
| 26_main_0_1 | 1594 | 4 | 1 | 0.7273 | 0.4000 |

## Per-Recording Results (Relaxed)

| Recording | Frames | GT Trans | Pred Trans | Macro F1 | Micro F1 |
|-----------|--------|----------|------------|----------|----------|
| 05_assy_0_1 | 2918 | 10 | 10 | 1.0000 | 1.0000 |
| 05_assy_2_2 | 2323 | 10 | 10 | 1.0000 | 1.0000 |
| 05_main_0_1 | 1380 | 4 | 1 | 0.7273 | 0.4000 |
| 14_assy_0_1 | 3005 | 9 | 9 | 1.0000 | 1.0000 |
| 14_main_0_1 | 1685 | 4 | 1 | 0.7273 | 0.4000 |
| 14_main_2_2 | 1404 | 3 | 1 | 0.8182 | 0.5000 |
| 14_main_2_3 | 1679 | 5 | 0 | 0.7273 | 0.0000 |
| 20_assy_0_1 | 2854 | 9 | 9 | 1.0000 | 1.0000 |
| 20_assy_3_6 | 2967 | 8 | 8 | 1.0000 | 1.0000 |
| 20_main_0_1 | 2066 | 4 | 1 | 0.7273 | 0.4000 |
| 24_assy_0_1 | 2158 | 9 | 9 | 1.0000 | 1.0000 |
| 24_assy_2_4 | 2952 | 8 | 8 | 1.0000 | 1.0000 |
| 24_main_0_1 | 1371 | 5 | 1 | 0.6364 | 0.3333 |
| 26_assy_0_1 | 3093 | 9 | 9 | 1.0000 | 1.0000 |
| 26_assy_1_5 | 4587 | 8 | 8 | 1.0000 | 1.0000 |
| 26_main_0_1 | 1594 | 4 | 1 | 0.7273 | 0.4000 |
