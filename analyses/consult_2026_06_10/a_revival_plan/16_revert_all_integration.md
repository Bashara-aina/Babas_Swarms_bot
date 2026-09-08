# Agent 5: Integration Plan to Revert All 4 Heads

**Date:** 2026-08-01
**Role:** Integration Specialist (Agent 5 of 5-agent revival team)
**Inputs:** Agent 1 plan (12_revert_act_0.394.md), Agent 2 plan (13_revert_det_0.5734.md), Agent 3 plan (14_revert_pose_6.15.md -- not yet posted), Agent 4 plan (15_revert_psr_0.883.md), SOTA history, COMPUTE_SCHEDULE.md, on-disk checkpoint verification
**Output:** Single coherent execution plan to revert all 4 historical metrics
**Constraint:** DO NOT make any code changes. This is a plan document only.

---

## Executive Summary

**Only 3 of 4 targets are revertable.** Detection 0.5734 was a biased 250-batch subsample artifact (`n_present=15`, class-balanced sampler). The true multi-task detection number from the same model is **mAP50 = 0.00009**. No checkpoint was saved at the epoch that produced the 0.5734 measurement. The closest checkpoint (epoch 11, `best.pth`) produced 0.5063, not 0.5734.

**Three targets are verified and revertable from two checkpoints:**

| Target | Value | Checkpoint | Backbone | Verdict |
|--------|-------|-----------|----------|---------|
| act (top-1) | **0.394** | v4_fixed (`v4_e0_b200.pth`, 233 MB) | ConvNeXt-Tiny | VERIFIED -- 2 independent evals, byte-identical |
| pose (angular MAE) | **6.15 deg** | v4_fixed (`v4_e0_b200.pth`, 233 MB) | ConvNeXt-Tiny | VERIFIED -- same checkpoint as act |
| psr (F1) | **0.883** | v3.41_safe (`phase2_e3_b0.pth`, 664 MB) | **MViTv2-S** | VERIFIED -- eval_e3_b0.json, cross-eval consistency |
| det (mAP50_pc) | **0.5734** | NONE PRESERVED | ConvNeXt-Tiny (rf_stages) | **UNREVERTABLE** -- biased subsample artifact, no checkpoint |

**Critical architectural incompatibility:** v4_fixed (act+pose) uses ConvNeXt-Tiny backbone. v3.41_safe (psr) uses MViTv2-S backbone with 9-channel input. These are different models. There is no single checkpoint that achieves all targets simultaneously.

---

## 1. Required Artifacts (Inventory)

### 1.1 Checkpoints -- Verified on Disk

| # | File | Full Path | Actual Size | Reported Size | Date | Status |
|---|------|----------|-------------|---------------|------|--------|
| 1 | `v4_e0_b200.pth` | `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/v4_fixed/v4_e0_b200.pth` | **233 MB** (244,203,344 bytes) | 244 MB | 2026-07-30 | EXISTS, VERIFIED |
| 2 | `phase2_e3_b0.pth` | `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth` | **664 MB** (695,992,320 bytes approx) | 695 MB | 2026-07-28 | EXISTS, VERIFIED |

**Detection note:** `best.pth` (epoch 11, 738 MB) exists at `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/rf_stages/checkpoints/best.pth` and produced det_mAP50_pc=0.5063 (not 0.5734). Epoch 17 (which produced 0.5734) was never saved as a .pth file. Detection 0.5734 cannot be reverted.

### 1.2 Total Disk Space Required

| Item | Size | Keep? |
|------|------|-------|
| v4_e0_b200.pth (act+pose) | 233 MB | YES -- minimal required |
| phase2_e3_b0.pth (psr) | 664 MB | YES -- minimal required |
| v3.41_safe ALL checkpoints (25 files) | ~16 GB | Optional -- only if full training lineage needed |
| best.pth (epoch 11, det evidence) | 738 MB | Optional -- historical evidence only |
| Config files (resolved_config.json, train.log) | ~15 MB | YES -- needed for eval reproducibility |
| **Minimal disk requirement** | **~1 GB** | 2 checkpoints + configs |
| **Full preservation (all v3.41 checkpoints)** | **~17 GB** | 25 checkpoints + configs |
| **Complete archive (all rf_stages + v3.41)** | **~25 GB** | Every preserved checkpoint |

**Available space:**
- System drive (`/home/newadmin/swarm-bot`): 138 GB free (457 GB total, 297 GB used) -- sufficient for minimal
- External drive (`/media/newadmin/master`): 630 GB free (3.6 TB total, 2.8 TB used) -- sufficient for full archive

**Recommendation:** Copy only the 2 key checkpoints (~900 MB) to a local directory for active use. Keep the full archive on the external drive.

### 1.3 Required Eval Scripts

All eval scripts live on the external training workstation at `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/`. The swarm-bot repo contains `full_eval_inprocess.py` but is missing its dependency `evaluate.py`.

#### For v4_fixed (act + pose):

| Script | Path on External Drive | Purpose | Lines |
|--------|----------------------|---------|-------|
| `eval_unified_v4.py` | `code/industreal_improved/eval_unified_v4.py` | Unified 4-head evaluation | unknown |
| `evaluate.py` | `code/industreal_improved/evaluate.py` | Core eval logic (imported by all others) | 6,966 |
| `model.py` | `code/industreal_improved/model.py` | POPWMultiTaskModel definition | unknown |
| `full_eval_inprocess.py` | `../swarm-bot/src/evaluation/full_eval_inprocess.py` | NaN-safe in-process eval runner (in swarm-bot repo) | 711 |

**Alternative:** The existing eval JSONs already confirm the numbers:
- `runs/eval/final_v4_fixed_v4_e0_b200.json` -- act=0.394, pose=6.15, det=0.096, psr=1.0 (fake)
- `runs/eval/v4_fixed_v3.34.json` -- byte-identical act=0.394

#### For v3.41_safe (PSR):

| Script | Path on External Drive | Purpose |
|--------|----------------------|---------|
| `eval_v3.34_psr_sweep.py` | (on training workstation) | Per-class threshold sweep PSR eval |
| `eval_v3.49_psr.py` | (on training workstation) | Current-version PSR eval (yields 0.820, -0.063 delta) |
| `eval_mtl_9ch.py` | `code/industreal_improved/eval_mtl_9ch.py` | 9-channel input eval for MViTv2-S |
| `eval_mtl_PSR_event_f1.py` | `code/industreal_improved/eval_mtl_PSR_event_f1.py` | PSR event F1 evaluation |

**Existing eval evidence:**
- `runs/mtl_v3.41_safe/eval_e3_b0.json` -- psr_f1=0.8827, det=0.214, act=0.255/0.039, pose=7.94
- `runs/mtl_v3.41_safe/eval_e3_b0_v3.49.json` -- psr_f1=0.820 (cross-eval with current script)

### 1.4 Critical Missing Dependencies

The swarm-bot repo (`/home/newadmin/swarm-bot`) does NOT contain:
- `evaluate.py` (6,966 lines, core eval logic imported by `full_eval_inprocess.py`)
- `model.py` (model architecture definitions)
- Config files for the historical runs

**These must be copied from the external training workstation before evaluation can proceed.**

---

## 2. Execution Order

### Phase A: Preserve Checkpoints (NOW, No GPU)

```
Step A1: Copy v4_fixed checkpoint to local safe storage
  cp /media/.../runs/v4_fixed/v4_e0_b200.pth → /home/newadmin/swarm-bot/checkpoints/v4_e0_b200.pth
  Size: 233 MB  |  Time: < 1 minute  |  Risk: LOW

Step A2: Copy v3.41_safe checkpoint to local safe storage
  cp /media/.../runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth → /home/newadmin/swarm-bot/checkpoints/phase2_e3_b0.pth
  Size: 664 MB  |  Time: < 2 minutes  |  Risk: LOW

Step A3: Record SHA256 checksums of both checkpoints
  sha256sum v4_e0_b200.pth phase2_e3_b0.pth > checkpoints/SHA256SUMS

Step A4: Copy config artifacts from external drive
  resolved_config.json, train.log → checkpoints/configs/
  Size: ~15 MB  |  Time: < 1 minute

Total disk used after Phase A: ~912 MB
```

### Phase B: Quick-Win Re-Evaluation (v4_fixed -- act + pose)

```
Step B1: Verify evaluate.py dependency is available
  - Copy evaluate.py from external drive if missing from swarm-bot
  - Verify full_eval_inprocess.py can import it without errors
  GPU: NONE  |  Time: 15 minutes  |  Risk: LOW

Step B2: Run full_eval_inprocess.py against v4_fixed checkpoint on FULL validation set
  Command: python src/evaluation/full_eval_inprocess.py \
    --checkpoint checkpoints/v4_e0_b200.pth \
    --output runs/eval/v4_fixed_full_re_eval.json \
    --n-frames 0  # 0 = all 38,036 frames
  GPU: RTX 3060 or 5060 Ti  |  Time: ~2 hours  |  Risk: LOW
  Expected: act ~= 0.39, pose ~= 6.15 deg
  Note: The historical evals used n_samples=500 (smoke test).
        Full 38,036-frame eval may differ slightly due to class distribution.

Step B3: Verify act and pose match historical numbers within tolerance
  - act tolerance: +/- 0.01 (class distribution differences on full vs. 500-frame subset)
  - pose tolerance: +/- 0.5 deg
  GPU: NONE  |  Time: 5 minutes  |  Risk: LOW
```

### Phase C: PSR Re-Evaluation (v3.41_safe checkpoint)

```
Step C1: Confirm MViTv2-S backbone and 9-channel input dependencies
  - Verify MViTv2-S pretrained weights accessible at: ~/.cache/torch/hub/checkpoints/mvit_v2_s-ae3be167.pth
  - Verify 9-channel input: RGB(ch0-2) + VL(ch3) + StereoL/R(ch4-5) + Depth(ch6-8)
  - Verify eval_mtl_9ch.py exists on external drive and can load the checkpoint
  GPU: NONE  |  Time: 30 minutes  |  Risk: MEDIUM
  Risk note: The 9-channel input path requires VL/Stereo/Depth data that may
             not be available in all eval environments. This is a data dependency,
             not just a code dependency.

Step C2: Run PSR threshold-sweep eval on v3.41_safe checkpoint (2000 frames)
  Command: python eval_v3.34_psr_sweep.py \
    --checkpoint checkpoints/phase2_e3_b0.pth \
    --n-frames 2000
  GPU: RTX 3060  |  Time: ~2 hours  |  Risk: MEDIUM
  Expected: psr_f1 = 0.8827 (threshold=0.05), per-class sweep = 0.9136

Step C3 (optional): Run v3.49 cross-eval for consistency check
  Command: python eval_v3.49_psr.py \
    --checkpoint checkpoints/phase2_e3_b0.pth \
    --n-frames 2000
  GPU: RTX 3060  |  Time: ~2 hours  |  Risk: LOW
  Expected: psr_f1 = 0.820 (known -0.063 delta from evaluator differences)
```

### Phase D: Detection -- Document the Truth

```
Step D1: Accept that 0.5734 cannot be reverted
  - No checkpoint was saved at epoch 17 (the epoch that produced 0.5734)
  - The number was a biased 250-batch class-balanced subsample artifact
  - True multi-task detection on full D3: mAP50 = 0.00009

Step D2: Document the detection lineage in the paper
  - Single-task YOLOv8m: mAP50 = 0.995 (beats SOTA)
  - Multi-task ConvNeXt-Tiny: mAP50 = 0.00009 (99.99% cost)
  - Biased subsample artifact: 0.5734 (NOT a valid detection metric)
  - The 99.99% multi-task cost is the paper's detection contribution

GPU: NONE  |  Time: N/A  |  Risk: N/A
```

### 2.1 Execution Order Diagram

```
HOUR 0:     Phase A (checkpoint preservation) -- CPU only, < 5 min
            ├── A1: Copy v4_e0_b200.pth (233 MB)
            ├── A2: Copy phase2_e3_b0.pth (664 MB)
            ├── A3: SHA256 both checkpoints
            └── A4: Copy config artifacts

HOUR 0-2:   Phase B (v4_fixed re-eval -- act + pose) -- on GPU 0 (RTX 3060)
            ├── B1: Verify evaluate.py dependency
            ├── B2: Run full_eval_inprocess.py on 38,036 frames
            └── B3: Verify act=0.394, pose=6.15

HOUR 2-4:   Phase C (v3.41_safe PSR re-eval) -- on GPU 0 (RTX 3060)
            ├── C1: Verify MViTv2-S and 9-channel dependencies
            ├── C2: Run PSR eval (2000 frames)
            └── C3: Cross-eval with v3.49 (optional)

            Phase D (detection documentation) -- parallel, CPU
            └── D1-D2: Document why 0.5734 is not revertable

TOTAL WALL CLOCK: ~4 hours on a single GPU (can be parallelized across GPUs)
```

---

## 3. GPU Time Budget

### 3.1 Evaluation-Only (No Training Required)

Since all targets are from existing checkpoints, NO training GPU time is needed. Only evaluation.

| Task | GPU | GPU-Hours | Notes |
|------|-----|-----------|-------|
| v4_fixed full eval (38k frames, all 4 heads) | RTX 3060 | ~2 h | One eval run covers act, pose, det, psr |
| v3.41_safe PSR eval (2k frames) | RTX 3060 | ~2 h | Threshold sweep adds compute |
| v3.41_safe cross-eval (v3.49, optional) | RTX 3060 | ~2 h | Redundant but confirms consistency |
| **Total (required)** | | **~4 GPU-h** | |
| **Total (with optional cross-eval)** | | **~6 GPU-h** | |

### 3.2 Comparison to PR #36 Budget

PR #36 allocated **481 GPU-h total** (116h on RTX 3060 + 365h on RTX 5060 Ti) for a full 30-day training + ablation campaign. The 4-6 GPU-h needed for checkpoint re-evaluation is **less than 1.5% of the allocated budget**.

### 3.3 GPU Availability (Current State)

| GPU | VRAM | Used | Free | Can Run |
|-----|------|------|------|---------|
| RTX 3060 (GPU 0) | 12 GB | 369 MiB | 11,535 MiB | YES -- eval fits in <4 GB VRAM |
| RTX 5060 Ti (GPU 1) | 16 GB | 249 MiB | 15,602 MiB | YES -- eval fits easily |

Both GPUs are idle and available for evaluation. No training is running.

### 3.4 What This Budget Does NOT Cover

- **PSR Path A restoration training:** If the v3.41_safe checkpoint is insufficient (e.g., 4 dead components at F1=0.0 are unacceptable), restoring Path A on ConvNeXt-Tiny would require 5-7 days of training (~50-84 GPU-h). This is a NEW experiment, not a revert.
- **Detection revival training:** Detection on ConvNeXt-Tiny is at 0.00009. Any attempt to revive it would require single-task training (7 days, ~50 GPU-h) or distillation (5 days, ~35 GPU-h). Neither is a revert -- the 0.5734 target was fake.
- **Activity MViTv2-S training:** The 0.6223 SOTA number requires MViTv2-S with 16-frame clips (5-7 days, ~50 GPU-h). The 0.394 on ConvNeXt-Tiny is the best achievable on the current backbone.
- **Unified model:** There is no single checkpoint with act=0.394 + pose=6.15 + psr=0.883. Act and pose share ConvNeXt-Tiny. PSR requires MViTv2-S. A unified model training run would be 100 epochs (~50 GPU-h) and may not achieve any of the targets due to multi-task interference.

---

## 4. Risk Assessment

### 4.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| External drive disconnected or fails | 15% | CRITICAL -- loses both checkpoints | Copy to local storage immediately (Phase A) |
| `evaluate.py` missing from swarm-bot | 80% | HIGH -- blocks v4_fixed eval | Copy from external drive; verify import before eval |
| v3.41 9-channel data not available | 30% | HIGH -- blocks PSR eval | The VL/Stereo/Depth channels must exist in the dataset; verify before eval |
| Full 38k-frame eval yields different act number than 500-frame smoke test | 40% | MEDIUM -- act may vary by class distribution | Report both numbers; the 500-frame 0.394 is the canonical target |
| MViTv2-S checkpoint incompatible with current codebase | 25% | HIGH -- architecture may have diverged since July 28 | Test-load checkpoint with a dry-run forward pass first |
| v3.41 PSR re-eval yields <0.883 | 50% | MEDIUM -- evaluator differences | The v3.49 eval already showed 0.820 (-0.063 delta). Use canonical v3.34 eval script for the official number |
| v4_fixed pose eval shows >6.15 on full set | 20% | MEDIUM -- 500-frame vs 38k-frame difference | Report both; the historical 6.15 is on 500 frames |
| Both checkpoints are loadable but produce NaN during eval | 5% | HIGH -- would indicate code-architecture mismatch | Test with single-batch dry run first |

### 4.2 Strategic Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Paper reviewers note 0.883 PSR is on MViTv2-S, not ConvNeXt-Tiny | 100% | MODERATE -- requires honest disclosure | Disclose the backbone difference. The paper's claim is "PSR requires spatiotemporal features (MViTv2-S, 0.883); ConvNeXt-Tiny per-frame features are insufficient (0.10)." |
| Paper reviewers note act=0.394 is on 500-frame smoke test, not full 38k | 100% | MODERATE -- requires honest disclosure | Re-evaluate on full set. If number drops, report both. Document the evaluation protocol. |
| Paper reviewers note 0.394 and 6.15 share a checkpoint with dead PSR (F1=1.0 fake) | 80% | LOW -- the trade-off IS the contribution | This is a finding: good pose comes with dead PSR. Multi-task trade-off is the paper's theme. |
| The two checkpoints use different backbones -- no unified model | N/A -- FACT | MODERATE -- paper must be structured as "per-task best" not "single model" | The paper's narrative is "what each head costs." A single unified model achieving all targets was never the goal. |
| Detection 0.5734 cannot be cited as a multi-task detection result | 100% | LOW -- honesty is stronger | The paper's detection contribution is: "Single-task YOLOv8m = 0.995. Multi-task ConvNeXt = 0.00009. Cost = 99.99%." This is a clean, publishable measurement. |

### 4.3 Abandonment Criteria

Stop and document immediately if:

1. **Either checkpoint fails to load** (checksum mismatch, architecture incompatibility). No recovery possible -- the historical numbers become the published record, marked "not independently reproducible from preserved checkpoint."
2. **Re-evaluation yields NaN for any head.** Indicates code-architecture mismatch that cannot be resolved without touching the training code.
3. **Full 38k-frame eval produces act < 0.30.** The 0.394 may be inflated by the 500-frame class distribution. If the true number is substantially lower, the 0.394 is not reproducible at scale.

---

## 5. Quick-Win Path (act + pose from v4_fixed)

### 5.1 What This Delivers

One checkpoint (`v4_e0_b200.pth`, 233 MB) simultaneously achieves:
- **act top-1 = 0.394** (raw, frame-level, ConvNeXt-Tiny + MLP head + FiLM)
- **pose forward_angular_MAE = 6.15 deg** (legacy HeadPoseHead, no geometry-aware module)

Zero GPU training required. Checkpoint already exists and is verified by 2 independent eval JSONs.

### 5.2 Steps

```
1. Copy v4_e0_b200.pth → local checkpoints/
2. Copy evaluate.py from external drive → src/evaluation/
3. Run: python src/evaluation/full_eval_inprocess.py \
     --checkpoint checkpoints/v4_e0_b200.pth \
     --output runs/eval/v4_fixed_38k_re_eval.json \
     --n-frames 0
4. Verify act ≈ 0.39, pose ≈ 6.15
5. Record SHA256 of checkpoint
6. Commit eval JSON to repo
```

**Wall clock:** < 3 hours (2 hours GPU eval + 1 hour setup/verification)
**GPU cost:** ~2 GPU-h on RTX 3060
**Risk:** LOW. Checkpoint verified on disk. Both eval scripts exist.

### 5.3 Caveats

- The v4_fixed PSR head is dead (10 of 11 components F1=0.0, comp0=1.0 from always-on). The F1=1.0 in the eval JSON is an artifact of the 500-frame sample having no valid PSR labels for components 1-10. Do NOT report v4_fixed PSR as a metric.
- The v4_fixed detection mAP50 is 0.096 (near-zero). Do NOT report v4_fixed detection as a metric.
- The 500-frame smoke test may over-represent easy classes. The full 38k-frame result may be lower.
- The FiLM conditioning layers in v4_fixed were trained with correct head pose vectors (legacy HeadPoseHead). The current `GeometryAwareHeadPose` with column-ordering bug (86-degree error) would corrupt FiLM if re-training were attempted.

---

## 6. Full Reversion Path (3 of 4 from 2 Checkpoints)

### 6.1 What This Delivers

| Head | Metric | Value | Checkpoint | Status |
|------|--------|-------|-----------|--------|
| Activity | top-1 (raw) | **0.394** | v4_fixed (`v4_e0_b200.pth`) | REVERTABLE |
| Pose | forward angular MAE | **6.15 deg** | v4_fixed (`v4_e0_b200.pth`) | REVERTABLE |
| PSR | F1 @ thresh 0.05 | **0.883** | v3.41_safe (`phase2_e3_b0.pth`) | REVERTABLE |
| Detection | mAP50_pc | **0.5734** | NONE | **NOT REVERTABLE** |

### 6.2 Complete Execution Sequence

```
PHASE A -- CHECKPOINT PRESERVATION (CPU, <5 min)
├── A1: cp v4_e0_b200.pth → checkpoints/ (233 MB)
├── A2: cp phase2_e3_b0.pth → checkpoints/ (664 MB)
├── A3: sha256sum both → SHA256SUMS
└── A4: cp config artifacts → checkpoints/configs/

PHASE B -- QUICK-WIN: act + pose (GPU, ~2h)
├── B1: Verify evaluate.py dependency (15 min, CPU)
├── B2: full_eval_inprocess.py on v4_fixed, 38k frames (2h, GPU)
└── B3: Verify results match historical (5 min, CPU)

PHASE C -- PSR (GPU, ~2h)
├── C1: Verify MViTv2-S + 9ch dependencies (30 min, CPU)
├── C2: PSR eval on v3.41_safe, 2k frames (2h, GPU)
└── C3: Cross-eval v3.49 (optional, 2h, GPU)

PHASE D -- DETECTION: Document truth (CPU, <30 min)
├── D1: Document 0.5734 as biased subsample artifact
└── D2: Document true multi-task detection = 0.00009

Total wall clock: ~4-6 hours (serial), ~2-3 hours (parallel across 2 GPUs)
Total GPU-hours: ~4-6 h
```

### 6.3 Paper Architecture Diagram

```
                 INDUSTREAL MULTI-TASK REVIVAL
                 ==============================

  ┌──────────────────────────────┐   ┌──────────────────────────┐
  │ v4_fixed checkpoint          │   │ v3.41_safe checkpoint    │
  │ ConvNeXt-Tiny backbone       │   │ MViTv2-S backbone        │
  │ RGB input (3-ch)             │   │ 9-ch input (RGB+VL+      │
  │ ~28.6M backbone params       │   │   Stereo+Depth)          │
  │ Legacy HeadPoseHead          │   │ Path A: 11 binary PSR    │
  │ Simple MLP activity head     │   │   heads + MonotonicDec   │
  ├──────────────────────────────┤   ├──────────────────────────┤
  │ act = 0.394   (verified)     │   │ psr = 0.883   (verified) │
  │ pose = 6.15°  (verified)     │   │ det = 0.214   (weak)     │
  │ det = 0.096   (near-zero)    │   │ act = 0.255   (calib.)   │
  │ psr = 1.000   (FAKE)         │   │ pose = 7.94°  (decent)   │
  └──────────────────────────────┘   └──────────────────────────┘
           │                                      │
           │ act + pose                           │ psr
           ▼                                      ▼
    ┌──────────────────────┐          ┌──────────────────────┐
    │ 2-HEAD REVIVAL       │          │ 1-HEAD REVIVAL       │
    │ ConvNeXt-Tiny        │          │ MViTv2-S             │
    │ (shared backbone,    │          │ (separate model,     │
    │  single checkpoint)  │          │  different backbone) │
    └──────────────────────┘          └──────────────────────┘

  ┌──────────────────────────────────────────────────────────────┐
  │ DETECTION: Split Report                                      │
  │ Single-task YOLOv8m: 0.995 mAP50 (beats SOTA)               │
  │ Multi-task ConvNeXt: 0.00009 mAP50 (99.99% cost)            │
  │ Historical 0.5734: biased subsample artifact -- withdrawn    │
  └──────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────┐
  │ ACTIVITY: Split Report                                       │
  │ ConvNeXt-Tiny per-frame: 0.394 top-1 (trained single-task)  │
  │ ConvNeXt-Tiny multi-task: 0.023 top-1 (collapsed)           │
  │ MViTv2-S 16-frame: 0.622 top-1 (SOTA, different model)     │
  │ Linear probe: 0.217 vs majority baseline 0.222 → no signal │
  └──────────────────────────────────────────────────────────────┘
```

---

## 7. Cross-References

### 7.1 Agent 1 (Activity -- 12_revert_act_0.394.md)

**Agreement:** The 0.394 target is verified from v4_fixed. Same checkpoint as pose. The plan to re-evaluate on full 38k frames is correct and necessary.

**Integration note:** Agent 1's plan requires `evaluate.py` from the external drive. This is a shared dependency with pose re-evaluation. Resolve once, use for both.

**Disagreement:** None. Agent 1's factual claims match the on-disk evidence.

### 7.2 Agent 2 (Detection -- 13_revert_det_0.5734.md)

**Agreement:** The 0.5734 is a biased subsample artifact. No checkpoint exists. The target cannot be reverted. The honest number is mAP50 = 0.00009.

**Integration note:** This plan accepts Agent 2's conclusion fully. Detection 0.5734 is withdrawn from all revival claims. The paper's detection contribution shifts from "revive 0.5734" to "document 99.99% multi-task cost."

**Disagreement:** None. Agent 2's investigation is thorough and the conclusion is correct.

### 7.3 Agent 3 (Pose -- 14_revert_pose_6.15.md)

**Not yet posted as of this writing (2026-08-01 20:30).**

**Expected content based on debate documents:** Pose 6.15 deg is verified from v4_fixed (same checkpoint as activity). Trivial fallback: set `USE_GEO_HEAD_POSE=False` to restore legacy HeadPoseHead. The column-ordering bug in GeometryAwareHeadPose currently produces 86-degree error but the legacy head code restores 6.15-degree performance with zero training.

**Pre-emptive integration note:** If Agent 3 recommends the `USE_GEO_HEAD_POSE=False` fallback, this requires NO retraining -- just a config change and re-evaluation. The v4_fixed checkpoint already uses the legacy head, so evaluation against it is sufficient. If Agent 3 recommends fixing the GeometryAwareHeadPose and retraining, that is a NEW experiment (5-7 days, 50 GPU-h) not a revert -- and would require re-validating that other heads still work.

### 7.4 Agent 4 (PSR -- 15_revert_psr_0.883.md)

**Agreement:** The 0.883 target is verified from v3.41_safe (`phase2_e3_b0.pth`). The checkpoint uses MViTv2-S backbone (not ConvNeXt-Tiny). Path A (11 binary heads + MonotonicDecoder) is the proven architecture. Path B (24-class softmax, current code) produces 0.10 F1 and is a regression.

**Integration note:** The MViTv2-S backbone is architecturally incompatible with the ConvNeXt-Tiny backbone used for act+pose. These cannot be merged into a single model. The paper must present PSR as a separate-model result. Agent 4's per-component dead-component analysis (comp4/7/8/9 at F1=0.0) defines the hard ceiling: even with the best checkpoint, 4 of 11 components are dead. The mean F1 of the 7 active components is 0.913.

**Disagreement:** None on the facts. However, this plan notes that the 0.883 on MViTv2-S with 9-channel input is NOT comparable to ConvNeXt-Tiny PSR (0.10 on Path B, ~0.70 per-frame F1 on Path A from earlier checkpoints). The paper must make this backbone comparison explicit.

---

## 8. Paper Integration Recommendations

### 8.1 Recommended Narrative Structure

**Title suggestion:** "What Four Tasks Really Cost on One Backbone: Multi-Task Training Pathologies for Industrial Assembly Understanding"

**Headline Results (post-revert):**

| # | Result | Evidence | Honesty Flag |
|---|--------|----------|--------------|
| 1 | Single-task YOLOv8m detection **mAP50 = 0.995** | beats published SOTA (~0.95) | Clean -- single-task, verified in-repo |
| 2 | Head pose forward MAE **= 6.15 deg** | verified (v4_fixed, ConvNeXt-Tiny) | Clean -- legacy head, 500-frame eval |
| 3 | Per-frame activity top-1 **= 0.394** | verified (v4_fixed, ConvNeXt-Tiny) | Flag: 500-frame smoke test; full 38k may differ |
| 4 | PSR per-frame F1 **= 0.883** | verified (v3.41_safe, MViTv2-S) | Flag: different backbone (MViTv2-S), 4 dead components |
| 5 | Multi-task detection cost: **99.99%** | 0.995 to 0.00009 | Clean -- well-characterized pathology |
| 6 | Multi-task activity cost: **96.2%** | 0.394 to 0.023 | Plus linear probe confirms zero backbone signal |

### 8.2 Required Disclosures (8 from agent debate)

| # | Disclosure | Status |
|---|-----------|--------|
| D1 | D4 backbone swap (YOLOv8m teacher != ConvNeXt student) | FILL -- different models |
| D2 | POS structurally inflated (0.999 with F1=0.0) | FILL -- documented |
| D3 | Activity 0.028 vs prior (clip-level vs frame-level) | FILL -- explained |
| D4 | Multi-task detection 36% of ceiling (now 0%) | FILL -- 99.99% cost |
| D5 | PSR gradient starvation (dead ReLU, not Kendall) | FILL -- characterized |
| D6 | Per-component thresholds tuned on val | FILL -- per-class sweep documented |
| D7 | Up-vector MAE unstable (26.20 deg on eval vs 13.5 on subset) | FILL -- per-recording breakdown exists |
| D8 | Position units unverified | PENDING -- units need verification |

### 8.3 Numbers to Withdraw

| Number | Reason |
|--------|--------|
| det_mAP50_pc = 0.5734 | Biased 250-batch subsample artifact. True number = 0.00009. |
| det_mAP50 = 0.3584 | Same biased subsample. True number = 0.00009. |
| psr_f1 = 1.0 (v4_fixed) | Only class 0 has GT in 500-frame sample. Fake. |
| act_top1 = 0.6223 on "our model" | This was MViTv2-S, not our ConvNeXt-Tiny. Misleading without backbone context. |

---

## 9. Appendix: Verification Checklist

Before the freeze date (Aug 22, 2026):

- [ ] SHA256 recorded for both checkpoints (v4_e0_b200.pth, phase2_e3_b0.pth)
- [ ] Both checkpoints copied to local storage (not external-drive-dependent)
- [ ] `evaluate.py` dependency resolved (copied from external drive to swarm-bot)
- [ ] v4_fixed full 38k-frame eval re-run and committed
- [ ] v3.41_safe PSR eval re-run and committed
- [ ] Detection 0.5734 formally withdrawn with substitution language
- [ ] Cross-backbone limitation (MViTv2-S vs ConvNeXt-Tiny) documented in paper
- [ ] All 8 honest disclosures filled with final numbers
- [ ] Freeze checkpoint paths recorded in paper appendix

**One-sentence synthesis:** Three of four historical targets are recoverable from two existing checkpoints with ~4 GPU-hours of evaluation (zero training); the fourth (detection 0.5734) was an artifact and is replaced with the honest 99.99% multi-task cost measurement; the two checkpoints use different backbones and cannot be merged into a single unified model without new training.
