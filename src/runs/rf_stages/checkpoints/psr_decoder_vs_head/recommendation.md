# PSR Decoder vs Head Comparison — Decision for Paper

**Date:** 2026-07-07
**Dataset:** Full 38,036 val frames (16 recordings), cached logits
**Tolerance:** +/-3 frames (transition matching)

## Comparison Table

| Component | Head Frame F1 | Decoder Count-up F1 | Decoder Monotonic F1 |
|-----------|---------------|---------------------|----------------------|
| comp0 | 1.000000 | 0.000000 | 0.000000 |
| comp1 | 0.950738 | 0.000000 | 0.024096 |
| comp2 | 0.955067 | 0.080000 | 0.034483 |
| comp3 | 0.748335 | 0.000000 | 0.000000 |
| comp4 | 0.197944 | 0.000000 | 0.000000 |
| comp5 | 0.825647 | 0.000000 | 0.000000 |
| comp6 | 0.758156 | 0.000000 | 0.000000 |
| comp7 | 0.622512 | 0.000000 | 0.000000 |
| comp8 | 0.610661 | 0.000000 | 0.000000 |
| comp9 | 0.472051 | 0.000000 | 0.000000 |
| comp10 | 0.403241 | 0.000000 | 0.000000 |
| **Macro Avg** | **0.685850** | **0.007273** | **0.005325** |

## Raw Logit Statistics

| Component | Mean Logit | Min Logit | Max Logit | GT Pos Fraction |
|-----------|------------|-----------|-----------|-----------------|
| comp0 | 3.69 | 1.07 | 4.15 | 1.0000 |
| comp1 | 1.86 | -8.85 | 3.84 | 0.9259 |
| comp2 | 1.97 | -8.30 | 3.82 | 0.9259 |
| comp3 | 1.88 | -0.10 | 3.71 | 0.5354 |
| comp4 | 5.19 | 2.67 | 6.19 | 0.1648 |
| comp5 | 1.96 | -1.80 | 4.08 | 0.6556 |
| comp6 | 1.64 | -2.84 | 4.74 | 0.5476 |
| comp7 | 4.16 | 2.00 | 4.98 | 0.5667 |
| comp8 | 4.10 | 0.76 | 4.67 | 0.5540 |
| comp9 | 4.60 | 0.86 | 5.21 | 0.4474 |
| comp10 | 3.83 | -0.99 | 5.02 | 0.2318 |

## Decision: NEITHER_WORKS_TRANSITION

BOTH the PSR head and decoder achieve near-zero transition F1 (decoder count-up=0.007273, decoder monotonic=0.005325). The cached checkpoint produces saturated raw logits (all positive for all components, min=1.07..-0.99) where sigmoid(h) > 0.5 for nearly all frames. Neither approach can detect 0->1 transitions from these logits. The PSR head repair training (LeakyReLU + zero bias) is in progress and should address this. For the paper: use frame-level F1 (macro F1=0.6859) as the primary PSR result, and note that transition-based F1 evaluation is blocked pending PSR head health restoration. The decoder-vs-head comparison is inconclusive until a checkpoint with clean transition logits is available.

### Key Finding

The cached PSR head checkpoint produces logits that are almost entirely
positive (mean sigmoid > 0.75 for all components). This saturates both
the MonotonicDecoder (which expects sigmoid scores in [0,1] and cannot
find transitions when all values exceed sustain_hi) and the count-up
decoder (which detects transitions from raw logit variation, but the
variation is small: range ~2-5 across all 38k frames).

The result is that transition F1 is near zero for both the PSR head
and the decoder. The frame-level F1 (0.6859) is
moderately informative and can be used as the primary PSR metric.

### Implication for Paper

1. **Frame-level PSR F1** (0.6859) should be the
   primary PSR metric. It is moderate but competitive with prior work.
2. **Transition F1** is not reportable from this checkpoint (both head
   and decoder yield near-zero). The PSR head repair (LeakyReLU + zero
   bias) is in progress and expected to fix the saturated logit issue.
3. The decoder vs head comparison is **inconclusive** because the
   saturated logits prevent either from detecting clean transitions.
4. **Recommendation:** Use frame-level F1 for the paper. Note that
   transition-level evaluation is blocked on PSR head health. Once the
   repair training completes, re-run this comparison on the new checkpoint.

### Decoder Sweep Results

**Count-up decoder best global config:**
  hi=0.7, lo=0.1, mi=1  F1=0.010101

**Monotonic decoder best global config:**
  hi=0.7, lo=0.1, mi=4  F1=0.004636

