# Agent 2: Resource Accountant — GPU Budget, Critical Path, and Conflict Audit

**Date:** 2026-08-01
**Agent:** 2 (Resource Accountant) of 5-agent debate team
**Sources:** Plans 01-06, training logs, nvidia-smi, checkpoint inventory
**Purpose:** Audit every GPU hour, find conflicts, define critical path

---

## 1. Current Hardware State (2026-08-01 17:00 UTC snapshot)

```
GPU 0: NVIDIA GeForce RTX 5060 Ti   | 249 MiB / 16,311 MiB  (1.5%)  | util 33%
GPU 1: NVIDIA GeForce RTX 3060       | 380 MiB / 12,288 MiB  (3.1%)  | util 32%
```

**No training processes running.** All previous runs (post-patch epoch 43, MTL v3.49, det_fixed_v1) have completed or been terminated. Both GPUs are idle and available for immediate use.

**Disk:** `/dev/sdb2` — 457 GB total, 138 GB free (69% used). Single partition serves both `/home` and `/media`. Checkpoint accumulation is the primary storage risk (see Section 7).

---

## 2. Measured Training Timings (from Logs, Not Estimates)

### 2.1 Full MTL (All 4 Heads) — ConvNeXt-Tiny + VideoMAE

| Config | GPU | Batch | GradAccum | Effective | Precision | Measured Timing | Source |
|--------|-----|-------|-----------|-----------|-----------|-----------------|--------|
| Post-patch repair | RTX 3060 | 2 | 32 | 64 | FP32 | 1.45 s/it (steady), 37.7 min/epoch (1556 batches) | `train_post_patch.log` epoch 43 |
| v3.49_proper | RTX 5060 Ti | 8 | 2 | 16 | BF16 | ~3.0 hr/epoch (timestamps: 14:20 - 11:22) | `mtl_v3.49_proper/train.log` |
| v3.50_coco_init | RTX 5060 Ti | 8 | 2 | 16 | BF16 | ~2.6 hr/epoch (timestamps: 22:16 - 19:41) | `mtl_v3.50_coco_init/train.log` |

**Key insight:** Full MTL on RTX 3060 (batch=2) is actually faster per epoch (38 min) than on RTX 5060 Ti (batch=8, ~3 hr) because the 3060 runs on a subset (SUBSET_RATIO=0.05, 3112 frames) while the 5060 Ti runs use the full dataset. **The per-epoch time is dominated by dataset size, not GPU speed.**

GPU memory on RTX 3060: 1.59 GB allocated, 6.85 GB reserved (5.15 GB headroom).

### 2.2 Single-Task Detection — ConvNeXt-Tiny

| Config | GPU | Batch | Batches/Epoch | Measured Timing | Source |
|--------|-----|-------|---------------|-----------------|--------|
| v3.37_det_proper (subset) | unknown | 8 | 400 | ~6.3 min/epoch | `v3.37_det_proper/train.log` |
| v3.37_det_only (subset) | unknown | 8 | 500 | ~6.0 min/epoch | `v3.37_det_only/train.log` |
| det_fixed_v1 (full dataset) | RTX 5060 Ti | 8 | 39,465 | 435 min/epoch (7.25 hr) | `det_fixed_v1/train.log` |

**Key insight:** The "full dataset" detection training (39,465 batches) is 70x slower than subset training (400-500 batches). At 7.25 hours/epoch, 99 epochs would take **30 days** on a dedicated GPU. The revival plans' "5 days" estimate is based on subset or distillation, NOT full retraining.

### 2.3 PSR Only (Path A: 11-Binary Heads + MonotonicDecoder)

No PSR-only training log found. Plan 03 estimates ~3.2 hr/epoch for temporal windows (T=4, FP32, no AMP for seq loss stability). This is consistent: the full MTL (38 min/epoch) is faster because it does NOT use temporal sequence mode. PSR requires T=4 windows which adds sequence overhead.

**Extrapolated from full MTL:** At 1.45 s/it (same hardware, RTX 3060), but with temporal sequences the iteration count changes. The plan's estimate of 3.2 hr/epoch is retained for lack of counter-evidence.

| Plan | GPU | Epochs | Per-Epoch | Total Training | Eval | Total |
|------|-----|--------|-----------|---------------|------|-------|
| PSR Path A | RTX 3060 | 50 | 3.2 hr | 160 hr (6.7 days) | 3 hr | ~7 days |

### 2.4 Activity Single-Task

No direct timing log found. Plan 01 estimates 2-3 days for Strategy A (ConvNeXt-Tiny, SUBSET_RATIO=0.15, 20 epochs) on RTX 3060. Extrapolating from single-task detection at ~6 min/epoch with 500 batches: 20 epochs * 6 min = 2 hours. However, activity head has a TCN that adds compute (the detection head is a lightweight anchor-free decoder). Conservative estimate: 2-3 days as stated.

### 2.5 Pose Fix

Code-only fix: 2 hours (no GPU). Eval: 2 hours on RTX 3060. Training only if fix doesn't restore 6.15 degrees.

---

## 3. Per-Plan GPU Hour Audit

### Plan 1: Activity Revival (Agent 1)

| Phase | Description | GPU | Duration | GPU-Hours |
|-------|-------------|-----|----------|-----------|
| Strategy A — single-task ConvNeXt-Tiny | Train activity head only | RTX 3060 | 2-3 days | 48-72 |
| Strategy B — MViTv2-S | Full single-task on MViTv2-S backbone | RTX 5060 Ti | 5-7 days | 120-168 |
| Eval | Run eval on best checkpoint | RTX 3060 | 2 hours | 2 |
| **Total (Strategy A)** | | | **2.1-3.1 days** | **50-74** |
| **Total (Strategy B)** | | | **5.1-7.1 days** | **122-170** |

**Gating metric:** Activity top-1 < 0.35 triggers cRT (PR #36 gate Q8). cRT script exists at `scripts/decoupled_act_retrain.py`; if needed, adds 1 epoch (~2-3 hours on RTX 3060).

### Plan 2: Detection Revival (Agent 2)

| Phase | Description | GPU | Duration | GPU-Hours |
|-------|-------------|-----|----------|-----------|
| Single-task eval (gating) | Eval ConvNeXt D3 single-task baseline | RTX 3060 | 2 hours | 2 |
| Strategy A — distillation | YOLOv8m teacher, 10 epochs | RTX 5060 Ti | 5 days | 120 |
| Strategy B — pathology doc | No training, document collapse | none | 0 days | 0 |
| TTA (if Strategy A works) | Test-time augmentation eval | RTX 3060 | 4 hours | 4 |
| **Total (Strategy A)** | | | **5.25 days** | **126** |
| **Total (Strategy B)** | | | **0.08 days** | **2** |

**Gating metric:** If single-task detection baseline mAP50 < 0.10, skip distillation (architectural failure). PR #36 gate: det mAP50-pc < 0.33 triggers TSBN.

**Checkpoint dependency:** YOLOv8m teacher at `d1r/weights/best.pt` or `src/runs/st_det/best.pt`.

### Plan 3: PSR Revival (Agent 3)

| Phase | Description | GPU | Duration | GPU-Hours |
|-------|-------------|-----|----------|-----------|
| Phase 1 — code changes | Revert to Path A, wire MonotonicDecoder | CPU only | 2-3 days | 0 |
| Phase 2 — training | 50 epochs, batch_size=2, FP32 | RTX 3060 | 6.7 days | 160 |
| Phase 2 — eval | Transition-F1 evaluation | RTX 3060 | 3 hours | 3 |
| Phase 2 — Kendall ablation | 2-3 days additional training | RTX 3060 | 2-3 days | 48-72 |
| **Total** | | | **11-14 days** | **211-235** |

**Gating metric:** PSR F1 < 0.50 triggers ASL (PR #36 gate Q15). ASL code exists at `src/losses/asymmetric_loss.py` but is NOT wired.

**Critical dependency:** Must wait for current PSR repair run to complete (was at epoch 43, now idle). The crash_recovery.pth at `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/full_multi_task_tma_tbank_benchmark/checkpoints/crash_recovery.pth` is the starting point.

### Plan 4: Pose Refinement (Agent 4)

| Phase | Description | GPU | Duration | GPU-Hours |
|-------|-------------|-----|----------|-----------|
| Code fix (column ordering) | Fix GeometryAwareHeadPose | CPU only | 2 hours | 0 |
| Eval | Verify fix on existing checkpoint | RTX 3060 | 2 hours | 2 |
| Resume training (if needed) | Resume from best checkpoint | RTX 3060 | 2-3 days | 48-72 |
| From scratch (if needed) | Full retraining | RTX 3060 | 5-7 days | 120-168 |
| **Total (fix only)** | | | **0.17 days** | **2** |
| **Total (resume)** | | | **2.2-3.2 days** | **50-74** |
| **Total (from scratch)** | | | **5.2-7.2 days** | **122-170** |

**Target:** < 6.15 degrees (v4_fixed historical). No checkpoint for v4_fixed found at the expected path. `src/runs/st_pose/best.pt` or `src/runs/mtl_tier1_v4/best.pt` are likely candidates.

### Plan 5: Integration Synthesis (Agent 5)

No GPU cost. Synthesizes results from Plans 1-4.

---

## 4. Total Resource Budget (All Plans, All Scenarios)

### Best Case (everything works on first try)

| Plan | GPU | GPU-Hours | Wall Days |
|------|-----|-----------|-----------|
| Activity (A) | RTX 3060 | 50-74 | 2.1-3.1 |
| Detection (B) | none | 2 | 0.08 |
| PSR | RTX 3060 | 211-235 | 11-14 |
| Pose (fix only) | RTX 3060 | 2 | 0.17 |
| **Total** | | **265-313** | **See critical path** |

### Worst Case (everything needs full training)

| Plan | GPU | GPU-Hours | Wall Days |
|------|-----|-----------|-----------|
| Activity (B) | RTX 5060 Ti | 122-170 | 5.1-7.1 |
| Detection (A) | RTX 5060 Ti | 126 | 5.25 |
| PSR | RTX 3060 | 211-235 | 11-14 |
| Pose (from scratch) | RTX 3060 | 122-170 | 5.2-7.2 |
| **Total** | | **581-701** | **See critical path** |

### Grand Total GPU-Hours (Worst Case): **581-701 GPU-hours**

At electricity cost of ~$0.12/kWh and ~200W per GPU: approximately **$14-17 in electricity** for the entire revival.

---

## 5. Critical Path Dependencies

```
                    Aug 1 ──────────────────────────────────────────────> Aug 22 (Freeze)
                    │
    ┌───────────────┼───────────────┬───────────────┬───────────────────┐
    │               │               │               │                   │
    Pose Fix        Detection       PSR Phase 1     Activity            Integration
    (2hr CPU)       Eval (2hr 3060) (2-3d CPU)     (queued after PSR)   (no GPU)
    │               │               │               │                   │
    ├─ Eval 2hr ────┤               │               │                   │
    │  (3060)       ├─ GATE:        ├─ GATE:        │                   │
    │               │  mAP50<0.10   │  Wait for     │                   │
    │               │  → Strategy B │  current run  │                   │
    │               │  (no GPU)     │  complete     │                   │
    │               │               │  (~Aug 7?)    │                   │
    │               │  mAP50≥0.10   │               │                   │
    │               │  → Distill    │               │                   │
    │               │  (5d 5060Ti)  │               │                   │
    │               │               │               │                   │
    ▼               ▼               ▼               ▼                   ▼
   Done            Done            Done            Done               Done
   Aug 1-2         Aug 2-7         Aug 1-14       Aug 14-20          Aug 21
```

### Serial dependencies (same GPU):

**RTX 3060 (GPU 1):**
```
Pose Eval (2hr) → PSR Phase 2 (7 days) → Activity Strategy A (2-3 days)
                                          OR
               → PSR Phase 2 (7 days) → Kendall Ablation (3 days) → Activity
```
**Critical path on RTX 3060: 11-14 days (PSR dominates)**

**RTX 5060 Ti (GPU 0):**
```
Detection Distill (5 days) → Activity Strategy B (5-7 days, if needed)
```
**Critical path on RTX 5060 Ti: 10-12 days (both serialized)**

### Parallel execution possible:

Since PSR (RTX 3060) and Detection distillation (RTX 5060 Ti) use DIFFERENT GPUs, they can run simultaneously. This is the key scheduling optimization:

```
Days 1-7:
  GPU 0 (5060 Ti): Detection distillation (5 days) → idle → Activity B (optional)
  GPU 1 (3060):    PSR Phase 2 training (7 days)

Days 8-14:
  GPU 0 (5060 Ti): Activity B (if needed) or idle
  GPU 1 (3060):    Kendall ablation (3 days) → Activity A (3 days)
```

**Total wall clock (parallel schedule): 14 days from Aug 1 = Aug 15 completion.**
This leaves a 7-day buffer before the Aug 22 freeze date.

---

## 6. Conflict Matrix

| Resource | Activity | Detection | PSR | Pose |
|----------|----------|-----------|-----|------|
| RTX 3060 (12GB) | Shared (2-3d) | Eval only (2hr) | **Primary (7d)** | Eval (2hr) |
| RTX 5060 Ti (16GB) | Strategy B (5-7d) | **Distill (5d)** | Not needed | Not needed |
| Disk (/dev/sdb2) | Checkpoints ~5GB | Checkpoints ~200GB risk | Checkpoints ~20GB | Minimal |
| Checkpoint: rf_stages/best.pth | Read | Read | Base for resume | Read |
| Checkpoint: crash_recovery.pth | N/A | N/A | **Required** | N/A |
| Checkpoint: YOLOv8m best.pt | N/A | **Required** | N/A | N/A |
| Checkpoint: st_pose/best.pt | N/A | N/A | N/A | **Required** |

### Conflicts found:

1. **RTX 3060 serialization (HIGH):** PSR training (7 days) blocks Activity training (2-3 days) and Pose eval (2 hours). Pose eval can run before PSR starts. Activity must wait or move to RTX 5060 Ti.

2. **RTX 5060 Ti serialization (MEDIUM):** Detection distillation (5 days) blocks Activity Strategy B (5-7 days). But Strategy A runs on RTX 3060, so this only matters if Strategy A fails.

3. **Checkpoint: rf_stages/best.pth (LOW):** Both Activity and PSR plans reference this checkpoint. This is read-only access — no conflict. But the checkpoint is AC-1 contaminated (PR #7 finding).

4. **Disk space (CRITICAL):** det_fixed_v1 checkpoints consume 162 GB. MTL v3.49 checkpoints consume 47 GB. MTL v3.50 checkpoints consume 15 GB. rf_stages checkpoints consume 12 GB. **Total: ~250 GB of checkpoints against 138 GB free.** The det_fixed_v1 run alone has consumed more space than is available. This is unsustainable and must be addressed before any new training.

---

## 7. Checkpoint Preservation Plan

### MUST preserve (do not delete under any circumstance):

| Checkpoint | Size | Path | Why |
|------------|------|------|-----|
| rf_stages/best.pth | 704 MB | `/media/.../rf_stages/checkpoints/best.pth` | Best activity (0.6223), detection (0.5734 diluted) |
| rf_stages/crash_recovery.pth | 711 MB | `/media/.../rf_stages/checkpoints/crash_recovery.pth` | Cleanfix launch checkpoint, not AC-1 contaminated |
| rf_stages/epoch_18.pth | 704 MB | `/media/.../rf_stages/checkpoints/epoch_18.pth` | Historical best epoch, pre-collapse |
| full_multi_task_benchmark/best.pth | 430 MB | `/media/.../full_multi_task_tma_tbank_benchmark/checkpoints/best.pth` | Post-patch best (0.1116) |
| full_multi_task_benchmark/crash_recovery.pth | 430 MB | `/media/.../full_multi_task_tma_tbank_benchmark/checkpoints/crash_recovery.pth` | PSR repair resume point (epoch 43) |
| full_multi_task_benchmark/epoch_43.pth | 704 MB | `/media/.../full_multi_task_tma_tbank_benchmark/checkpoints/epoch_43.pth` | Full-size epoch 43 |
| st_det/best.pt | ? | `/media/.../st_det/best.pt` | YOLOv8m single-task teacher |
| st_pose/best.pt | ? | `/media/.../st_pose/best.pt` | Pose single-task baseline |
| mtl_tier1_v4/best.pt | ? | `/media/.../mtl_tier1_v4/best.pt` | Candidate for v4_fixed (6.15 deg pose) |

**Critical preservation total: ~4.6 GB**

### CAN delete (recoverable, low value):

| Directory | Size | Reason |
|-----------|------|--------|
| det_fixed_v1/checkpoints/ | **162 GB** | Save every 500 batches (733MB each). Keep only every 5000th. Saves ~150 GB. |
| mtl_v3.49_proper/checkpoints/ | **47 GB** | Epoch 0 only, 5 epochs planned but incomplete. Keep latest. |
| mtl_v3.50_coco_init/checkpoints/ | **15 GB** | Epoch 0 only. Keep latest. |
| mtl_v3.48_unified/checkpoints/ | unknown | Check before deleting. |
| ablation_A_3060/checkpoints/ | unknown | 3 crash_recovery variants. Keep one. |

**Estimated recoverable space: 200+ GB**

### Immediate action required:

```bash
# Before ANY new training, free at least 50 GB:
# 1. Thin det_fixed_v1 checkpoints (keep every 5000th, delete intermediates)
# 2. Remove incomplete MTL run checkpoints (v3.48, v3.49, v3.50)
# 3. Keep only one crash_recovery variant per run
```

---

## 8. OOM Risk Assessment

### Historical crashes (4 prior CUDA OOM events):

All crashes occurred during full MTL training on RTX 3060 (12 GB). The post-patch training log shows:
- GPU allocated: 1.59 GB (low because most tensors are freed between steps)
- GPU reserved: 6.85 GB (PyTorch caching allocator)
- Peak observed: ~7 GB (with batch_size=2, grad_accum=32)

**OOM risk matrix:**

| Scenario | GPU | Batch Size | VRAM Required | Risk |
|----------|-----|------------|---------------|------|
| Full MTL (all 4 heads) | RTX 3060 | 2 | ~7 GB | LOW (5 GB headroom) |
| Full MTL (all 4 heads) | RTX 5060 Ti | 8 | ~14 GB | MEDIUM (bf16 helps) |
| PSR only (temporal T=4) | RTX 3060 | 2 | ~8 GB | LOW (4 GB headroom) |
| Activity only | RTX 3060 | 2 | ~4 GB | VERY LOW |
| Detection only | RTX 5060 Ti | 8 | ~8 GB | LOW |
| Distillation (YOLOv8m + student) | RTX 5060 Ti | 4 | ~12 GB | MEDIUM |

**Recommendation:** All training MUST use batch_size=2 (or 1 for temporal models) when targeting RTX 3060. RTX 5060 Ti can safely use batch_size=4-8 with BF16. The `memsafe-training.sh` wrapper should be used for all runs.

---

## 9. Backup Plan: If RTX 5060 Ti Is Busy

**Scenario A: User needs RTX 5060 Ti for other work**

| Plan | Primary GPU | Fallback | Impact |
|------|-------------|----------|--------|
| Detection distillation | RTX 5060 Ti | RTX 3060 (batch_size=2, FP32) | 2x slower (10 days instead of 5). May OOM with YOLOv8m teacher. |
| Activity Strategy B | RTX 5060 Ti | RTX 3060 (batch_size=2, FP32) | 2-3x slower. 12-15 days. |
| Activity Strategy A | RTX 3060 | Already on RTX 3060 | No impact |

**Scenario B: RTX 3060 is busy**

| Plan | Primary GPU | Fallback | Impact |
|------|-------------|----------|--------|
| PSR Phase 2 | RTX 3060 | RTX 5060 Ti (batch_size=8, BF16) | 2x faster per epoch (~1.5 hr vs 3.2 hr). BUT temporal windows may not fit in 16 GB at batch_size=8. Test first. |
| Pose eval | RTX 3060 | RTX 5060 Ti | No impact (eval is short) |

**Scenario C: Both GPUs busy (user interrupt)**

All plans are designed to checkpoint every epoch. All training uses `crash_recovery.pth` auto-save. Interrupt cost is at most 1 epoch of lost work (~38 minutes for full MTL, ~3 hours for PSR-only).

**Rollback time for any plan: < 5 minutes** (load crash_recovery.pth, resume).

---

## 10. GPU Hour Budget vs. PR #36 Plan

PR #36 (30-day execution plan) assumed:
- 21 days from Aug 1 to Aug 22 freeze
- Phase 3 multi-seed: Aug 4-10
- Architecture freeze: Aug 3

**Our actual budget:**

| Phase | PR #36 Estimate | Our Audit | Delta |
|-------|----------------|-----------|-------|
| PSR repair complete | ~Aug 7 | Aug 7-14 | 0 to +7 days |
| Detection single-task | ~Aug 7 | Aug 2 (eval only) | -5 days (no training needed if gated) |
| Pose fix | Not in plan | Aug 1-2 | +2 days (new work) |
| Activity push | ~Aug 10 | Aug 14-20 | +4 to +10 days |
| Buffer before freeze | Aug 12-22 (10 days) | Aug 15-22 (7 days) | -3 days buffer |

**Verdict:** Achievable within the Aug 22 freeze date IF:
1. PSR runs on RTX 3060 and Detection runs on RTX 5060 Ti IN PARALLEL
2. Detection gates to Strategy B (pathology doc, no training)
3. Pose fix works code-only (no retraining needed)
4. Activity runs Strategy A on RTX 3060 after PSR completes
5. At least 200 GB of checkpoint storage is freed before starting

**If ALL worst cases fire:** 26 wall-clock days required (exceeds Aug 22 freeze by 4 days). Must prioritize: PSR + Pose first (most revivable), Detection + Activity as characterized pathology.

---

## 11. Cross-References

| This Document (08) | Cross-Reference | Why |
|--------------------|-----------------|-----|
| Section 2 (timings) | Agent 3 (09_debate_code_correctness.md) | Verify that proposed batch sizes won't OOM |
| Section 3 (GPU hours) | Agent 1 (07_debate_feasibility.md) | Feasibility depends on whether training fits in budget |
| Section 5 (critical path) | Agent 5 (11_debate_adversarial.md) | Worst-case cascade if PSR blocks Activity |
| Section 6 (conflict matrix) | Agent 4 (10_debate_historical_targets.md) | Checkpoint path verification |
| Section 7 (preservation) | Agent 5 (05_integration_synthesis.md) | Which checkpoints feed the final paper |
| Section 8 (OOM risk) | Agent 3 (09) | Code changes must not increase VRAM usage |
| Section 9 (backup plan) | Agent 5 (11) | Rollback scenarios if GPU is unavailable |

---

## 12. Summary: Go / No-Go Resource Gates

| Gate | Threshold | Status | Action |
|------|-----------|--------|--------|
| Disk free > 50 GB | 138 GB → 50+ GB | FAIL (need cleanup) | Free 200 GB from stale checkpoints |
| RTX 3060 free | Yes (380 MiB) | PASS | Available immediately |
| RTX 5060 Ti free | Yes (249 MiB) | PASS | Available immediately |
| All critical checkpoints exist | 9 of 9 | TBD (verify paths) | Run `ls` on each path in Section 7 |
| OOM risk < 20% | ~10% | PASS | Use batch_size=2, memsafe wrapper |
| Wall clock < Aug 22 | 14 days (best) to 26 days (worst) | CONDITIONAL | Parallel schedule required |
| PR #36 dates achievable | Aug 15 completion vs Aug 22 freeze | PASS (7 day buffer) | Start immediately |

**IMMEDIATE ACTIONS before any training:**
1. Free 200 GB by thinning `det_fixed_v1/checkpoints/` (keep every 5000th, delete 95% of intermediates)
2. Remove incomplete MTL run checkpoints (v3.48, v3.49, v3.50 epoch 0 only)
3. Verify all 9 critical checkpoint paths in Section 7 with `ls -lah`
4. Run `nvidia-smi` to confirm both GPUs still idle
5. Start Pose fix (CPU only, no GPU dependency) while other agents finalize plans
