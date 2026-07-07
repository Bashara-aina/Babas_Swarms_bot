# Single-Task ConvNeXt-Tiny Detection Training Status

**Date:** 2026-07-07 ~18:47
**GPU:** NVIDIA GeForce RTX 5060 Ti (GPU 0)
**Checkpoint path:** `src/runs/full_multi_task_tma_tbank_benchmark/checkpoints/crash_recovery.pth`

## Training Status: ALIVE

- **Process:** PID 811481, started 12:21, running continuously
- **GPU utilization:** 76% | VRAM: 5.0 GiB / 16.6 GiB
- **No OOM events or crashes in current instance**
- **Heartbeat:** Confirmed at step 1430, gpu_alloc=1.56GB, reserved=3.51GB

## Current Progress

- **Epoch:** 43 / 99 (11% through epoch, step 1440 / 13161)
- **Global step:** resumed from _global_step=90216
- **Training config:** batch_size=2, no-staged-training, DET only (HEAD_POSE/ACT/PSR disabled), Kendall HP prec cap active

## Detection Loss Values (per-batch, epoch 43)

| Component | Typical Range | Notes |
|-----------|--------------|-------|
| total     | 0.1 - 3.3   | High variance per batch |
| det       | 0.0 - 2.7   | Classification + regression |
| det_cls   | 0.1 - 2.0   | Classification component |
| det_reg   | 0.0 - 0.5   | Regression component |
| pose/act/psr | 0.0      | Not trained |

Loss shows high per-batch variance with frequent near-zero values (likely background or heavily augmented frames). No upward trend detected; loss is in a healthy range for detection training at this stage.

## Speed

- **Current sustained speed:** ~1.2 batch/s (varies 1.0-1.6)
- Periodically drops due to `DET_POS_ANCHOR_PROBE` every 1000 steps
- GPU 0 at 76% suggests CPU-bound data pipeline limits throughput

## Estimated Completion

- **Per epoch:** ~2.9 hours at 1.25 batch/s average
- **Remaining epochs (44-99):** 56 epochs
- **Current epoch remaining:** ~2.5 hours
- **Total estimated time remaining:** ~7 days (168 hours)

## Training History

This run auto-resumed from `crash_recovery.pth` (saved from a SIGTERM during a
previous epoch 42 run at 10:16 today). The log files contain traces of multiple
prior launch attempts:

- Instance at epoch 34: trained ~1080 batches, then killed
- Instances at epochs 35-41: launched but crashed immediately
- Instance at epoch 42: trained ~220 batches, then SIGTERM'd
- **Current instance at epoch 43: active, progressing**

The repeated restarts were due to stale PID killing from the launch script -
each new launch killed the previous instance's PID and started fresh. The
current instance has been stable since 12:21.

## No detection mAP is being computed

No validation mAP logging detected. This is expected for a training-only run.
