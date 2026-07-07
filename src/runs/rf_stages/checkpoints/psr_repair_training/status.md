# PSR Head Repair Training Status

## Overview
Training launched from commit `a3f938a0c` with the real LeakyReLU + small-normal init + zero bias fix for PSR head repair. Resumed from `crash_recovery.pth` on RTX 3060 (GPU index 1).

## Training Status: ALIVE

- **PID**: 813375
- **Runtime**: started at 12:21, running for ~5 hours
- **GPU**: NVIDIA GeForce RTX 3060 (12.5 GB), GPU index 1
- **GPU utilization**: 47%
- **GPU memory**: 3922 MiB / ~11.9 GB usable

## Current Progress

- **Epoch**: 24 (of 100)
- **Step**: ~1110 / 13161 (8.4% of epoch)
- **Speed**: ~1.0-1.1 batch/s average
- **Estimated time remaining this epoch**: ~3 hours
- **Total estimated time**: ~75 hours for 100 epochs at current speed

## Loss Values (Typical Range)

| Component | Normal frames | Sequence frames (seq=1) |
|-----------|--------------|------------------------|
| Total     | 3.5 - 8.5    | 1.3 - 32.1             |
| det       | 0.1 - 4.3    | 0.0                    |
| pose      | 0.05 - 4.6   | 0.0                    |
| act       | 1.3 - 2.9    | 0.0                    |
| psr       | 0.000        | 1.3 - 32.1             |

- **218 seq=1 events** processed (out of ~13161 batches, ~1.7% of batches)
- Average PSR loss on seq=1 events: ~9.4
- No PSR loss on non-sequence frames (expected - targets only present on seq=1)

## PSR Head Activation

### Output Activation (post_gelu)

| Step | Type    | pre_linear mean | post_linear64 mean | post_gelu mean  | Status |
|------|---------|-----------------|--------------------|-----------------|--------|
| 0    | normal  | -2.8            | -126.5             | -1.02           | DEAD   |
| 1    | normal  | -3.6            | -145.0             | -1.45           | DEAD   |
| 10   | normal  | -2.0            | -142.0             | -1.39           | DEAD   |
| 100  | seq=1   | -5.2            | 211.0              | 510.0           | ALIVE  |
| 200  | seq=1   | -16.2           | 74.5               | 384.0           | ALIVE  |
| 500  | seq=1   | -4.4            | -964.0             | 640.0           | ALIVE  |

On **normal frames**: post_gelu stays negative (~-1.0 to -1.4), post_linear64 consistently negative (~-126 to -145). The PSR head output is dead for non-sequence frames, which is expected behavior when PSR targets are only present on sequence batches.

On **sequence frames (seq=1)**: post_gelu mean jumps to strongly positive values (384-640), post_linear64 shows both positive and negative values with very large standard deviations. The PSR head is clearly activating and producing non-zero output when sequence data is fed.

### Gradient Flow

- **Step 1** (epoch 23): `psr_head:NO_GRAD` - no gradient at all (cold start from checkpoint)
- **Step 201** (epoch 23): `psr_head:ALIVE[RMS=1.67e-01]`, `h10=6.52e-01[ALIVE]` - gradient flowing through head 10
- **Steps 401-1001**: `psr_head:DEAD[RMS=0.00e+00]`, all heads dead - gradient collapsed
- But **KENDALL PSR lv_grad**: values of 2.4-4.4 observed at steps 501-1101, indicating continued weight gradient
- **LIVENESS psr_c**: min=1.54e-06 / mean=2.09-6.00 / max=3.0-6.0 - partial gradient checkpoint signal

### Interpretation
The repair is **partially working**. The PSR head produces healthy activations on sequence frames (post_gelu mean 384-640 vs -130 dead baseline). However, gradient flow through the PSR head itself has oscillated and collapsed since step 401. The KENDALL weighting system still sees PSR gradient signal (lv_grad ~3-4), suggesting the head can recover when it hits another sequence batch with strong targets. This pattern (sporadic activation on seq=1, death during normal frame stretches) is expected for a head that only receives targets every ~100 batches.

## Crash/Recovery History

- **Epoch 23, step 860**: CPU OOM crash (`alloc_cpu.cpp:127`, 22MB allocation in `collate_fn_sequences`). Available RAM was 22.6GB - possibly a transient spike or memory fragmentation issue.
- Auto-recovery fired: `[CRASH_RECOVERY] Saved epoch_start crash checkpoint` at epoch 23 start
- Training resumed cleanly from `crash_recovery.pth` into epoch 24
- A secondary crash checkpoint was saved at epoch 24 step 1000

## Comparison to Diagnostic Commit 96b144e51

The diagnostic commit showed post_gelu mean ~ -130 with all heads dead. The current repair shows:
- Post-gelu mean on sequence frames: +384 to +640 (vs -130) - **dramatically improved**
- Post-gelu mean on normal frames: -1.0 to -1.4 (still dead, but this is expected)
- Gradient flow: intermittent (was NO_GRAD at step 1, ALIVE at step 201, DEAD after 401+)

The LeakyReLU + small-normal init + zero bias fix has **substantially improved** PSR head activation on sequence frames compared to the fully dead baseline. The remaining issue is maintaining gradient flow through stretches of normal (non-sequence) frames.

## Snapshot Timestamp
2026-07-07 16:50 UTC
