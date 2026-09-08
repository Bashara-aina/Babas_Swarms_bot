# Plan C: Detection Head Rebuild

**Date:** 2026-08-01
**Agent:** Agent 3 (Detection Head Rebuild)
**Mission:** Rebuild the detection head so the unified model can hit 0.30+ mAP50.
**Priorities:** Detection > Activity > PSR > Pose
**Constraint:** DO NOT make any code changes. This document is the plan only.
**Output:** This file only.

---

## 1. Current State: Detection on the Unified Model

### 1.1 Honest Numbers

| Configuration | Backbone | mAP50 | Source | Verdict |
|---|---|---|---|---|
| Single-task YOLOv8m | YOLOv8m CSPDarkNet | 0.995 | d1r/weights/best.pt | **VERIFIED ceiling** |
| Multi-task v3.41_safe | MViTv2-S (34.3M) | 0.214 | eval_e3_b0.json | **VERIFIED multi-task best** |
| Multi-task unified (ConvNeXt-Tiny) | ConvNeXt-Tiny (28.6M) | 0.00009 | d1_yolov8m/metrics.json | **VERIFIED pathology** |
| Biased subsample artifact | ConvNeXt-Tiny | 0.5734 | 250-batch class-balanced, 15/24 classes | **WITHDRAWN as artifact** |

The 0.5734 claim has been withdrawn by Agents 2, 3, 4, and 5 across files 13, 19, 20, 21. It was a biased 250-batch class-balanced subsample with only 15 of 24 classes present. The epoch 17 checkpoint that produced it was never saved.

### 1.2 Architecture Details

**Current DetectionHead (13 state dict keys):**
```
cls_head.0.weight  Conv2d(256, 256, 3, padding=1)
cls_head.1.weight  GroupNorm(32, 256)
cls_head.2         ReLU(inplace=True)
cls_head.3.weight  Conv2d(256, 24, 1)        # 24 classes
cls_head.3.bias    Conv2d(256, 24, 1).bias
reg_head.0.weight  Conv2d(256, 256, 3, padding=1)
reg_head.1.weight  GroupNorm(32, 256)
reg_head.2         ReLU(inplace=True)
reg_head.3.weight  Conv2d(256, 64, 1)        # 4 * 16 anchors
reg_head.3.bias    Conv2d(256, 64, 1).bias
running_pos_ratio  scalar buffer (prior_prob=0.01 EMA)
```

**v4_fixed Detection Head (103 state dict keys):**
```
YOLOv8-style cv2/cv3 pattern:
  cv2.0.0.bn.weight, cv2.0.0.conv.weight, cv2.0.1.bn.weight, cv2.0.1.conv.weight,
  cv2.0.2.cv2.0.0.bn.weight, cv2.0.2.cv2.0.0.conv.weight, ...
  cv3.0.0.bn.weight, cv3.0.0.conv.weight, ...
```
These architectures are **fundamentally incompatible** -- they cannot share weights.

**LightweightFPN outputs (256-channel, BiFPN-style):**
| Level | Input Channels | Spatial Size (224x224 input) | Notes |
|-------|---------------|------------------------------|-------|
| P2 | 96 (C2) | 56x56 | Dedicated 3x3 p2_lateral Conv3d |
| P3 | 192 (C3) | 28x28 | 1x1 lateral projection |
| P4 | 384 (C4) | 14x14 | 1x1 lateral projection |
| P5 | 768 (C5) | 7x7 | 1x1 lateral projection |

DetectionHead operates on temporally-pooled (mean over T) FPN features at `[B, 256, H, W]`.

### 1.3 Why Detection Collapsed (99.99% on ConvNeXt-Tiny)

Three root causes identified by the 5-agent debate (files 07-11) and cascade analysis:

1. **Feature competition.** The shared ConvNeXt backbone must serve detection (spatially precise, high-resolution), activity (global-semantic), PSR (per-pixel component state), and pose (keypoint regression) simultaneously. ConvNeXt-Tiny, pretrained on ImageNet-1K static images, allocates capacity toward global-semantic tasks. Detection receives degraded features. Evidence: activity linear probe on frozen ConvNeXt = 0.2169 vs 0.2217 majority baseline (zero signal above chance).

2. **Gradient conflict.** Detection loss (CIoU + focal) conflicts with PSR BCE loss and activity cross-entropy. Kendall homoscedastic uncertainty weighting (5 learnable log_vars) cannot resolve this conflict. The detection head receives contradictory gradient directions.

3. **Training signal starvation.** Without DET_GT_FRAME_FRACTION (defaults to 0.0), GT-bearing frames appear at natural density (~0.7%). The detection head sees zero positive examples in ~99.3% of training steps. Even with the fix enabled at 0.4, 60% of frames are still empty.

### 1.4 The Decode Formula Inconsistency (CRITICAL Finding)

There is a **decode formula mismatch** between the MViTv2 training path and the "fixed" evaluate.py:

| File | Formula | Style |
|------|---------|-------|
| `mvit_mtl_model.py:265` (docstring) | `cx = grid_cx + dx * 0.1` | YOLOv8 fixed-scale |
| `ciou.py:26` (training loss) | `cx = anchor_cx + dx * 0.1` | YOLOv8 fixed-scale |
| `losses.py:240` (training loss) | `cx = dx * a_w + a_cx` | Faster R-CNN anchor-scaled |
| `model.py:2207` (training loss) | `cx = dx * a_w + a_cx` | Faster R-CNN anchor-scaled |
| `evaluate.py:833,2410` (eval, "FIXED") | `cx = dx * a_w + a_cx` | Faster R-CNN anchor-scaled |
| `eval_real_map_fast.py:98` (eval) | `cx = anchor_cx + dx * 0.1` | YOLOv8 fixed-scale |

**The "dx*0.1 fix" in evaluate.py changed the decode from YOLOv8-style (`dx * 0.1`) to Faster R-CNN-style (`dx * a_w`).** If the model was trained with YOLOv8-style encoding (`dx * 0.1` in ciou.py and mvit_mtl_model.py), then the "fixed" evaluate.py uses the **wrong** decode formula, producing systematically incorrect box centers for large anchors (where `a_w >> 0.1`). Conversely, if the model was trained with `losses.py:240` (`dx * a_w`), then the "fixed" evaluate.py is correct and the old eval was broken.

**This ambiguity must be resolved before any training.** The correct decode must match the training encode, whichever formula was actually used during training. A `dx * 0.1` training encode decoded with `dx * a_w` produces boxes shifted by up to 16x for the largest anchors (a_w=1.6 vs 0.1), which alone could explain near-zero mAP.

### 1.5 Anchor Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| num_anchors | 16 | Per spatial location |
| Anchor sizes | Guess-based, NOT k-means calibrated | Significant risk |
| Spatial grid | 1280x720 input -> varies by FPN level | 173,088 total anchors at P2-P5 |
| Decode | `cx = grid_cx + dx * 0.1` (per docstring) | See Section 1.4 for ambiguity |

### 1.6 Realistic Multi-Task Detection Ceilings

| Configuration | mAP50 | Delta from single-task |
|---|---|---|
| Single-task YOLOv8m | 0.995 | -- |
| Multi-task MViTv2-S (v3.41_safe) | 0.214 | -78.5% |
| Multi-task ConvNeXt-Tiny | 0.00009 | -99.99% |
| **Realistic MViTv2-S target** | **0.30-0.45** | -55 to -70% |
| **Optimistic MViTv2-S target** | **0.45-0.55** | Requires ASFF + P2 + k-means anchors |

The gap from 0.214 (current multi-task best) to 0.30+ is +0.086 mAP50. This is achievable through: (a) decode formula resolution, (b) k-means calibrated anchors, (c) ASFF neck, (d) P2-level detection, (e) YOLOv8-style DFL head.

---

## 2. Option A: Distillation from d1r YOLOv8m Teacher

### 2.1 Description

Use the single-task YOLOv8m (mAP50=0.995 on D1R) as a teacher to distill detection knowledge into the multi-task student. The teacher's soft targets (box regression + class probabilities) replace hard GT labels during training, potentially bypassing gradient conflict by providing richer training signal.

### 2.2 Evidence

| Factor | Assessment |
|--------|-----------|
| Teacher quality | 0.995 mAP50 -- excellent |
| Teacher availability | yolov8m_industreal.pt exists on external workstation |
| Distillation gap | 0.00009 -> 0.995 = 10,000x. No precedent for closing this gap via distillation. |
| Similar-architecture distillation | Typically closes 10-30% of the teacher-student gap |
| Cross-architecture distillation | YOLOv8m (CSPDarkNet) -> ConvNeXt-Tiny student. Fundamentally different feature hierarchies. |
| Single-task student baseline | Unknown. ConvNeXt D3 training was at epoch 43/99 on Jul 7. If single-task ConvNeXt < 0.20, distillation is pointless. |

### 2.3 Prerequisites

1. Single-task ConvNeXt-Tiny D3 training must complete and achieve mAP50 > 0.30.
2. Distillation loss script must exist (referenced in PR #6, not verified in swarm-bot repo).
3. Teacher checkpoint must be loadable with current code.
4. DET_GT_FRAME_FRACTION must be enabled.

### 2.4 Pros and Cons

**Pros:**
- Uses existing high-quality teacher (already trained, verified).
- Does not require architectural changes to the multi-task model.
- Distillation script reportedly exists (PR #6).

**Cons:**
- No precedent for 10,000x gap closure.
- Gated on unknown single-task ConvNeXt D3 baseline.
- 5-7 GPU-days on RTX 5060 Ti.
- Does not fix feature competition -- backbone still serves 4 heads.
- Teacher (detection-optimized neck) and student (classification backbone) have fundamentally different architectures.

### 2.5 Probability Assessment

| Outcome | Probability | Condition |
|---------|------------|-----------|
| det > 0.30 | ~5% | Requires single-task ConvNeXt > 0.50 (unlikely) |
| det > 0.20 | ~15% | Requires single-task ConvNeXt > 0.30 |
| det > 0.10 | ~25% | Requires single-task ConvNeXt > 0.20 |
| det stays near 0 | ~60% | Single-task ConvNeXt < 0.20 or distillation fails |

**Assessment from file 07 (Agent 1):** ~20% probability of reaching 0.30-0.45 via distillation, gated on single-task baseline. **Assessment from file 19 (Agent 3):** 15-20% for det > 0.20, gated on single-task baseline > 0.30.

---

## 3. Option B: Pose-Derived Detection (PDD)

### 3.1 Description

Extract geometric bounding boxes from the pose head's predicted skeleton keypoints. From the 9-DoF pose output `[forward(3), up(3), position(3)]`, compute a bounding box around the operator's working area. No trainable parameters -- purely geometric inference.

### 3.2 Evidence

| Factor | Assessment |
|--------|-----------|
| Implementation complexity | Trivial. 2-4 hours, zero GPU. |
| Pose head quality | 6.15 degrees angular MAE on v4_fixed (500-frame), 11.75 on current unified model (38k-frame). |
| Box-target mismatch | PDD produces worker body boxes. Detection GT is assembly state component boxes (screw holes, connectors). These don't overlap. |
| Classification | PDD produces ONE box per frame. Cannot classify 24 assembly states. |
| mAP ceiling | Limited by worker-body to component-box IoU, likely < 0.05. |

### 3.3 Prerequisites

1. Unified model with working pose head.
2. Inference on D3 validation set.
3. Geometric box extraction from keypoints (min/max of x,y).
4. COCO mAP evaluation against detection GT.

### 3.4 Pros and Cons

**Pros:**
- Fastest option: 2-4 hours, zero GPU.
- Uses existing unified model with no changes.
- Demonstrates genuine multi-task synergy (pose output used for detection proxy).
- Non-zero detection number from a different modality.

**Cons:**
- PDD boxes cover worker body, not assembly state components.
- Cannot distinguish 24 classes -- single "person" box.
- mAP will be near-zero due to box-target mismatch.
- Does NOT make the detection head work; sidesteps the problem entirely.
- Paper contribution: "safety region detection," not object detection.

### 3.5 Probability Assessment

| Outcome | Probability |
|---------|------------|
| det > 0.30 | 0% (geometric limit) |
| det > 0.20 | 0% (box-target mismatch) |
| det > 0.10 | <5% (requires body boxes overlapping assembly component GT) |
| det > 0.05 | ~10% |

PDD is a **diagnostic tool**, not a detection solution. It answers: "Is there ANY spatial signal in the backbone?" If PDD produces >0.05, there is weak spatial signal. If PDD produces 0.0, spatial features are completely absent.

---

## 4. Option C: New YOLOv8m-Style Head on MViTv2-S FPN Features

### 4.1 Description

Replace the current 13-key DetectionHead with a YOLOv8-style DFL (Distribution Focal Loss) detection head that operates on MViTv2-S FPN features. The YOLOv8DetectHead uses anchor-free detection with integral box regression (`reg_max=16`), which is the architecture that achieves 0.995 in single-task mode. The MViTv2-S FPN already outputs 256-channel features at P2-P5 -- the exact input the YOLOv8 head expects.

### 4.2 Architecture Compatibility

The MTLMViTModel class (mvit_mtl_model.py lines 570-815) already has built-in support:

```python
use_yolov8_head: bool = False  # line 586
reg_max: int = 16              # line 587

if use_yolov8_head:            # line 624
    from src.models.yolov8_det_head import YOLOv8DetectHead
    self.det_head = YOLOv8DetectHead(
        in_channels=fpn_channels,  # 256
        num_classes=num_det_classes,  # 24
        reg_max=self.reg_max,       # 16
        use_p2=use_p2_level,
        prior_prob=det_prior_prob,
        logit_bias_scale=logit_bias_scale,
    )
```

**This is a config change (`use_yolov8_head=True`), not a code change.** The model class already imports and constructs YOLOv8DetectHead when this flag is set. The forward pass (line 710) already handles both head types:

- Legacy 3x3 head: iterates FPN levels, temporal-pools, calls `self.det_head(pooled)` per level
- YOLOv8 head: collects P3/P4/P5 (and optionally P2) features as a list, temporal-pools, calls `self.det_head(level_feats)` once

### 4.3 What Makes This Different from Current DetectionHead

| Property | Current DetectionHead | YOLOv8DetectHead |
|----------|----------------------|-------------------|
| Anchor scheme | 16 anchors per location, fixed sizes | Anchor-free |
| Classification | Conv2d(256,24,1) per level | Shared across levels |
| Regression | 4 * 16 = 64 channels (dx,dy,dw,dh) | 4 * reg_max = 64 channels (DFL bins) |
| Box decode | `cx = grid_cx + dx * 0.1` | Integral over DFL distribution |
| Heads | Per-level `cls_head` + `reg_head` | Shared `cv2` (cls) + `cv3` (reg) across P3/P4/P5 |
| State dict keys | 13 | ~103 (v4_fixed style) |
| Proven mAP50 | 0.214 (multi-task MViTv2-S) | 0.995 (single-task YOLOv8m) |
| Training stability | prior_prob init + bias EMA | DFL integral + task-aligned assigner |

The key architectural advantage: YOLOv8DetectHead uses **anchor-free detection** with DFL-based box regression, eliminating the 16-anchor-per-location design. This reduces false positives from 173,088 candidate anchors and simplifies the assignment problem from 24 classes x 16 anchors to 24 classes x 1 location.

### 4.4 Additional Improvements Available (Config-Only)

All of the following are existing config flags or env vars in the current codebase -- no code changes required:

| Improvement | Flag/Env Var | Expected Gain | Status |
|---|---|---|---|
| YOLOv8 DFL head | `use_yolov8_head=True` | +5-10% mAP | In model __init__, untested in multi-task |
| P2 detection level | `use_p2_level=True` | +3-5% mAP (small objects) | In model __init__, p2_lateral already built |
| ASFF neck | `USE_ASFF=1` env var | +2-4% mAP | ASFFNeck import at line 620 |
| GT frame fraction | `DET_GT_FRAME_FRACTION=0.4` | Enables training signal | Config parameter, defaults OFF |
| Detach reg FPN | `detach_reg_fpn=True` | Reduces gradient conflict | Config parameter, exists but untested with GT_FRAME_FRACTION |
| k-means anchors | N/A (anchor-free with YOLOv8 head) | +2-5% mAP | Not applicable with YOLOv8 head (anchor-free) |
| Kendall fixed weights | `KENDALL_FIXED_WEIGHTS=True` | Prevents PSR suppression of det | Config parameter, referenced in file 27 |

### 4.5 Training Configuration

```
Phase C (epochs 1-30):
  Model: MViTv2-S backbone + LightweightFPN (256ch) + YOLOv8DetectHead
  Frozen: Activity head, PSR head, Pose head (preserve existing quality)
  Training: Backbone (last 4 blocks) + FPN + YOLOv8DetectHead
  Loss: CIoU box loss + DFL + BCE classification (YOLOv8 default)
  LR: 1e-3 with cosine to 1e-5
  Effective batch: 32 (batch_size=2, grad_accum=16, RTX 3060 limit)
  DET_GT_FRAME_FRACTION: 0.4
  USE_ASFF: 1 (env var)
  use_p2_level: True
  Mixed precision: AMP (autocast + GradScaler)
  Epochs: 30 (10 for head-only warmup, 20 for joint FPN+head)

  Monitoring per epoch:
    - det_mAP50 (primary)
    - det_mAP50_pc (class-balanced)
    - act/pose/psr metrics (must not degrade >5%)
    - Per-level detection loss (P2/P3/P4/P5)
    - Gradient norm ratio det vs other heads
```

### 4.6 Ablation Gates

| Gate | Epoch | Condition | Action on Fail |
|------|-------|-----------|----------------|
| G_C1: Head warmup | 5 | det_mAP50 > 0.05 | If <0.05: decode formula is likely wrong, resolve Section 1.4 ambiguity |
| G_C2: FPN unfreeze | 10 | det_mAP50 > 0.10 | If <0.10: backbone features lack detection signal. Try DETACH_REG_FPN=True. |
| G_C3: Mid-training | 20 | det_mAP50 > 0.20 | If <0.20: check ASFF activation, P2 level. Try LR warm restart. |
| G_C4: Target | 30 | det_mAP50 > 0.30 | If 0.20-0.30: accept as partial success, document ceiling. If <0.20: Option C failed. |

### 4.7 Probability Assessment

| Outcome | Probability | Rationale |
|---------|------------|-----------|
| det > 0.45 | ~15% | Requires all improvements working synergistically |
| det > 0.30 | ~40% | YOLOv8 head + ASFF + P2 on MViTv2-S is architecturally proven for detection |
| det > 0.20 | ~65% | v3.41_safe already hit 0.214 with inferior 13-key head on MViTv2-S |
| det > 0.10 | ~80% | MViTv2-S backbone proven to support detection in multi-task (0.214 evidence) |
| det stays < 0.05 | ~15% | Decode formula mismatch or catastrophic gradient conflict |
| OOM / cannot train | ~5% | 16-frame clips + MViTv2-S + YOLOv8 head may exceed 12GB VRAM |

The primary risk is VRAM. MViTv2-S (34.3M) + FPN + 4 heads + 16-frame clips may exceed RTX 3060 12GB. Mitigation: reduce batch_size to 1, increase grad_accum to 32, use `_grad_checkpoint=True` (already supported in model code).

### 4.8 Why MViTv2-S Works for Detection (When ConvNeXt-Tiny Does Not)

MViTv2-S has three properties that ConvNeXt-Tiny lacks, making it viable for multi-task detection:

1. **Spatiotemporal attention.** 3D pooling attention preserves spatial structure through 16 transformer blocks. ConvNeXt-Tiny's 2D convolutions progressively downsample, losing fine-grained spatial information by C5.

2. **Kinetics-400 pretraining.** Video action recognition requires detecting moving objects and their spatial relationships. This transfers to assembly state detection (components, tools, hands). ImageNet-1K classification on static images provides no analogous transfer.

3. **Multi-scale feature hierarchy.** MViTv2-S naturally produces C2-C5 features at stride 4/8/16/32 with 96/192/384/768 channels. ConvNeXt-Tiny's feature hierarchy is designed for classification, not detection -- C5 features are 7x7 semantic embeddings, not spatial feature maps.

Evidence: On the same data (D3 IndustReal), the same 4-head architecture, MViTv2-S achieves 0.214 mAP50 while ConvNeXt-Tiny achieves 0.00009. The 2,378x difference is entirely attributable to backbone architecture.

---

## 5. Option D: Hybrid -- YOLOv8m Head + MViTv2-S Backbone + Surgical Transplant

### 5.1 Description

Combine the best of all worlds: use the single-task YOLOv8m head (0.995 proven) transplanted onto the MViTv2-S backbone with FPN features, then fine-tune the head and FPN while keeping other task heads frozen. This is Option C taken to its logical extreme -- use the actual trained YOLOv8m head weights rather than a fresh initialization.

### 5.2 Transplant Feasibility

The YOLOv8m head from `yolov8m_industreal.pt` expects:
- Input: List of feature maps at strides 8, 16, 32 (from CSPDarkNet backbone)
- Channel dimensions: typically 128/256/512 (YOLOv8m neck output)

The MViTv2-S FPN outputs:
- Input: Dict of P3(256ch,28x28), P4(256ch,14x14), P5(256ch,7x7)
- Channel dimensions: 256 at all levels

**Channel mismatch:** YOLOv8m neck outputs vary by level (128/256/512), but MViTv2-S FPN outputs uniform 256. The YOLOv8DetectHead in the codebase expects `in_channels=256` (the `fpn_channels` parameter), so this specific YOLOv8DetectHead class is already configured for 256-channel input. The transplant is from YOLOv8DetectHead(256ch) to YOLOv8DetectHead(256ch) -- **architecturally compatible**.

However, the key question is: does `yolov8m_industreal.pt` contain a YOLOv8DetectHead with 256-channel input? The d1r YOLOv8m was trained as a standalone model, likely with standard YOLOv8m neck channels (not 256). If so, direct weight transplant fails due to channel mismatch.

### 5.3 Two Sub-Options

**D1: Full YOLOv8m head transplant (if channel-compatible)**
- Load yolov8m_industreal.pt, extract detection head weights
- Verify channel dimensions match MViTv2-S FPN output (256)
- Copy weights into MTLMViTModel with `use_yolov8_head=True`
- Evaluate immediately (0 GPU hours)
- Expected: mAP50 = 0.15-0.25 (partial transfer, FPN distribution shift)
- Fine-tune 5-10 epochs to adapt FPN → 0.30-0.45

**D2: Initialize YOLOv8DetectHead from scratch (Option C with weight init)**
- Use `use_yolov8_head=True` with fresh random init
- Pre-train detection head on frozen MViTv2-S backbone for 10 epochs
- Then joint fine-tune with FPN for 20 epochs
- Same as Option C, but framed as "fresh YOLOv8 head"

### 5.4 Probability Assessment

| Outcome | D1 (Transplant) | D2 (Fresh init) |
|---------|-----------------|-----------------|
| det > 0.45 | ~10% (if compatible) | ~15% |
| det > 0.30 | ~25% (if compatible) | ~40% |
| det > 0.20 | ~40% (if compatible) | ~65% |
| Channel incompatible | ~60% probability | N/A |

The dominant risk for D1 is channel incompatibility (~60% probability), which would force D2 (Option C) anyway.

---

## 6. Recommended Approach

### 6.1 Decision Matrix

| Option | Cost | Time | Best-Case mAP50 | Probability >0.30 | Code Changes |
|--------|------|------|-----------------|-------------------|--------------|
| A: Distillation | 5-7 GPU-days | 1-2 weeks | 0.35 | ~15% | Moderate (distill script) |
| B: PDD | 0 GPU-hours | 4 hours | 0.10 | 0% | None |
| C: YOLOv8 Head on MViTv2-S | 3-5 GPU-days | 1 week | 0.45 | ~40% | None (config only) |
| D1: Transplant | 2-4 GPU-days | 3-5 days | 0.40 | ~25% | None (if compatible) |
| D2: Fresh Init (= Option C) | 3-5 GPU-days | 1 week | 0.45 | ~40% | None |

### 6.2 Recommended Strategy: Tiered Execution

**Tier 1: Immediate Verification (0 GPU, 4-6 hours)**
1. Resolve the decode formula ambiguity (Section 1.4). Determine which training encode was actually used: `dx * 0.1` (ciou.py/mvit_mtl_model.py) or `dx * a_w` (losses.py/model.py). Fix evaluate.py to match.
2. Run pose-derived detection (Option B) as a diagnostic. If PDD > 0.05, there is spatial signal in the backbone.
3. Verify whether `YOLOv8DetectHead` class exists in the accessible codebase and whether yolov8m_industreal.pt's head is channel-compatible with the 256-channel FPN.
4. Run `use_yolov8_head=True` smoke test: instantiate MTLMViTModel with the flag, verify no import errors, verify forward pass produces output tensors with correct shapes.

**Tier 2: Option C -- New YOLOv8 Head on MViTv2-S (3-5 GPU-days)**
1. Set `use_yolov8_head=True`, `use_p2_level=True`, `USE_ASFF=1`, `DET_GT_FRAME_FRACTION=0.4`.
2. Freeze activity, PSR, pose heads. Freeze backbone blocks 0-10. Train detection head + FPN for 10 epochs.
3. Monitor G_C1 at epoch 5, G_C2 at epoch 10.
4. If G_C2 passes (mAP50 > 0.10): unfreeze all backbone blocks, continue training to epoch 30. Monitor G_C3 and G_C4.
5. If G_C2 fails: test `detach_reg_fpn=True`. If still fails: Option C has failed, accept.

**Tier 3: Option D1 -- Transplant (if channel-compatible, 2-4 GPU-days)**
1. Load yolov8m_industreal.pt, extract detection head weights.
2. Verify channel compatibility. If compatible, transplant into MViTv2-S model.
3. Evaluate immediately. If mAP50 > 0.10: fine-tune 5-10 epochs.
4. If not compatible: fall back to Tier 2 (Option C already in progress).

**Tier 4: Option A -- Distillation (if all above fail, 5-7 GPU-days)**
1. Only if single-task ConvNeXt D3 achieves > 0.30 mAP50.
2. Implement distillation loss (scripts/ referenced in PR #6).
3. Train with YOLOv8m teacher, MViTv2-S student.

**Tier 5: Accept Pathology (if all options fail)**
1. Report detection as 0.00009 on ConvNeXt-Tiny, 0.214-0.30 on MViTv2-S.
2. The multi-task detection cost (78-99% depending on backbone) becomes a paper contribution.
3. Companion single-task YOLOv8m (0.995) provides practical detection.

### 6.3 The Honest Assessment

**The fastest evidence-backed path to det > 0.30 is Option C: YOLOv8-style DFL head on MViTv2-S FPN features.** This is the only option with >40% probability of success, and it requires zero code changes -- only config flags that already exist in the model class (`use_yolov8_head=True`, `use_p2_level=True`, `USE_ASFF=1`).

Option A (distillation) is gated on the single-task ConvNeXt D3 baseline, which is unknown and likely poor. Option B (PDD) cannot reach 0.30 due to geometric limits. Option D1 (transplant) is gated on channel compatibility (~40% chance).

The ConvNeXt-Tiny backbone is architecturally incapable of supporting detection in a multi-task setting. The 0.00009 measurement is not a bug -- it is a fundamental limitation. The MViTv2-S backbone has demonstrated 0.214 in the identical multi-task configuration, proving the task is solvable with the right backbone.

---

## 7. Timeline

### 7.1 MViTv2-S Path (Recommended)

| Day | Phase | Activity | GPU Hours | Milestone |
|-----|-------|----------|-----------|-----------|
| 1 | Tier 1 | Decode formula resolution, PDD eval, YOLOv8 head smoke test | 0 | Gating decisions made |
| 2-3 | Tier 2 Phase 1 | Head warmup (10 epochs), G_C1 check | 20 | det > 0.05 confirmed |
| 4-6 | Tier 2 Phase 2 | FPN + backbone unfreeze, ASFF, P2 training (20 epochs) | 50 | G_C3: det > 0.20 |
| 7-8 | Tier 2 Phase 3 | Final convergence, LR decay | 20 | G_C4: det > 0.30 target |
| 9 | Tier 3 | Transplant attempt (if compatible) | 5 | D1 eval |
| 10 | Eval | Full 38k-frame D3 evaluation | 4 | Final metrics |
| 11-12 | Buffer | Retries, ablations | 20 | Contingency |
| **Total** | **12 days** | | **~119 GPU-hours** | |

### 7.2 If MViTv2-S is Not Available (ConvNeXt-Tiny Only)

| Day | Phase | Activity | GPU Hours | Milestone |
|-----|-------|----------|-----------|-----------|
| 1 | Tier 1 | Decode formula resolution, PDD eval | 0 | Gating decisions |
| 2-3 | Tier 2 | Head-only fine-tuning on frozen ConvNeXt, 5 epochs | 10 | G_C1: probably fails |
| 4-6 | Option A | Distillation from YOLOv8m (if single-task baseline > 0.30) | 50 | det > 0.10? |
| 7 | Accept | Report 0.00009 with pathology framing | 0 | Paper-ready |
| **Total** | **7 days** | | **~60 GPU-hours** | |

### 7.3 Risk-Adjusted Timeline

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| YOLOv8DetectHead class not in accessible codebase | 30% | +2 days (implement/wire) | Verify in Tier 1 smoke test |
| Decode formula mismatch corrupts all evals | 40% | +1 day (fix + re-eval) | Resolve in Tier 1 |
| OOM with YOLOv8 head + MViTv2-S | 20% | +2 days (grad checkpoint, batch=1) | Test memory in Tier 1 smoke test |
| ASFFNeck import fails | 15% | +1 day (implement or skip) | Skip ASFF, lose 2-4% mAP |
| External drive unavailable, checkpoints not accessible | 10% | Blocks Tier 3 (transplant) | Fall back to Option C fresh init |
| All options fail on ConvNeXt-Tiny | ~60% | Accept pathology framing | Already prepared (Section 6.3) |

---

## 8. Cross-References to Companion Files

### 8.1 File 27: Plan A -- Reach Realistic Max with Current Architecture

**Status:** EXISTS. Read and incorporated.

Key findings relevant to this plan:
- File 27 confirms MViTv2-S backbone (544 shared keys between v4_fixed and v3.41_safe), contradicting earlier ConvNeXt-Tiny claims.
- File 27's detection plan (Section 4) proposes surgical transplant of v3.41_safe's 137-key detection head. This plan's Option C (fresh YOLOv8 head) is a more aggressive alternative -- rather than transplanting the older 13-key head, build a new anchor-free YOLOv8 head.
- File 27's sequential execution order places detection at Phase 3 (Day 6-7), after activity and PSR. This plan agrees: detection should be trained with other heads frozen to preserve their quality.
- File 27's realistic detection range (0.15-0.21) is conservative. This plan targets 0.30+ through the YOLOv8 DFL head upgrade, which is not considered in file 27.
- File 27's estimate for PDD (0.05-0.10) matches this plan's assessment.
- File 27's distillation plan (0.10-0.15 expected) is slightly more optimistic than this plan's assessment (~25% for >0.10).

**Where this plan diverges from file 27:**
- File 27 treats detection as Phase 3 (after PSR and activity). This plan recommends detection first (after Tier 1 verification) because it is the hardest task and gates the entire multi-task viability.
- File 27 does not consider the YOLOv8 DFL head option (`use_yolov8_head=True`), which this plan identifies as the highest-probability path to 0.30+.
- File 27 does not identify the decode formula inconsistency (Section 1.4), which this plan flags as a critical pre-requisite.

### 8.2 File 28: Cross-Task Gradient Analysis

**Status:** DOES NOT EXIST as of 2026-08-01.

Anticipated content and how this plan would use it:
- Gradient cosine similarity between detection head and activity/PSR/pose heads. If similarity < -0.3 for any task pair, gradient surgery (PCGrad/GradNorm) should be used instead of Kendall weighting.
- Per-layer gradient magnitude for detection head vs other heads. If detection gradients are 100x smaller, the head is being starved regardless of loss weighting.
- Whether `detach_reg_fpn=True` reduces gradient conflict measurably. If yes, this becomes a Tier 2 fallback.
- This plan's monitoring (gradient norm ratio, per-head loss magnitudes) would be calibrated against file 28's findings.

### 8.3 File 30: Detection Architecture Comparison

**Status:** DOES NOT EXIST as of 2026-08-01.

Anticipated content and how this plan would use it:
- Detailed comparison of 13-key legacy head vs 103-key v4_fixed head vs YOLOv8DetectHead.
- Whether the v3.41_safe model's detection head uses the 13-key or YOLOv8-style architecture (this is ambiguous -- the codebase evolved between v3.41 and v4).
- Anchor quality analysis: k-means calibrated anchors vs guess-based anchors.
- This plan's Option C (YOLOv8 DFL head) may be redundant with file 30's recommended architecture. If file 30 independently recommends the same thing, confidence increases.

### 8.4 File 31: Final Integration and Paper Strategy

**Status:** DOES NOT EXIST as of 2026-08-01.

Anticipated content and how this plan would use it:
- Paper submission deadline (likely Aug 22 based on file 27).
- Which metrics to report: single-model numbers vs per-head-best numbers.
- Paper narrative: "multi-task cost as contribution" vs "unified model achieving all targets."
- This plan's Tier 5 (accept pathology) aligns with the "multi-task cost" narrative. If file 31 recommends a different framing (e.g., "we achieved all targets"), this plan's targets become minimum requirements rather than stretch goals.
- If file 31's deadline is firm (Aug 22), this plan's 12-day timeline (Aug 1-12) leaves 10 days for paper writing and buffer.

### 8.5 Other Key References

| File | Relevance | Key Takeaway |
|------|-----------|--------------|
| [02_detection_revival.md](02_detection_revival.md) | Root cause analysis, bug inventory | Detection collapse is 99.99%. Distillation architecture detailed. |
| [07_debate_feasibility.md](07_debate_feasibility.md) | Agent 1 feasibility assessment | Detection: <2% probability for 0.5734, ~20% for 0.30-0.45 via distillation. |
| [19_unified_model_detection.md](19_unified_model_detection.md) | Agent 3 detection strategy | Three-tier approach: PDD -> head-only -> MViTv2-S switch. |
| [20_unified_model_adversarial.md](20_unified_model_adversarial.md) | Agent 4 adversarial risks | "Detection has NEVER worked in any multi-task configuration on any backbone." |
| [21_unified_model_final_synthesis.md](21_unified_model_final_synthesis.md) | Agent 5 final synthesis | Detection held at 0.00009 as honest pathology. |
| [STATE_OF_TRUTH_20260801.md](../../master/POPW/working/code/industreal_improved/code/industreal_improved/STATE_OF_TRUTH_20260801.md) | Honest metrics | det best eval = 0.4684, act best = 0.19, dx*0.1 fix applied. |
| [AUDIT_TRUTHFULNESS.md](../../master/POPW/working/code/industreal_improved/code/industreal_improved/AUDIT_TRUTHFULNESS.md) | Fabricated numbers catalog | 0.5734, 0.3584, PSR F1=1.0, activity 0.6223 all withdrawn. |
| [mvit_mtl_model.py](../../master/POPW/working/code/industreal_improved/code/industreal_improved/src/models/mvit_mtl_model.py) | Model architecture | Lines 256-373 (DetectionHead), 137-248 (LightweightFPN), 570-815 (MTLMViTModel). |

---

## 9. Action Items (Ordered by Priority)

### Immediate (Today, No GPU) -- Tier 1 Verification

1. [ ] **Resolve decode formula ambiguity (Section 1.4).** Check which training script was used for the model being evaluated. If ciou.py (YOLOv8-style `dx*0.1`), revert evaluate.py to `dx * 0.1`. If losses.py (Faster R-CNN-style `dx*a_w`), keep current evaluate.py. ~2 hours.

2. [ ] **Run PDD diagnostic (Option B).** Extract pose keypoints from current unified model. Compute geometric boxes. Evaluate against detection GT. ~2 hours.

3. [ ] **Smoke test YOLOv8 head import.** Instantiate MTLMViTModel with `use_yolov8_head=True`. Verify YOLOv8DetectHead imports. Run dummy forward pass. Check VRAM. ~1 hour.

4. [ ] **Verify yolov8m_industreal.pt channel compatibility.** Load checkpoint, inspect detection head weight shapes. Determine if transplant (Option D1) is viable. ~30 min.

5. [ ] **Verify k-means anchor calibration.** Check if current anchors were derived from training data or guessed. If guessed, note this as an additional improvement vector. ~1 hour.

### Short-Term (Days 2-6) -- Tier 2: Option C

6. [ ] Set config: `use_yolov8_head=True`, `use_p2_level=True`, `USE_ASFF=1`, `DET_GT_FRAME_FRACTION=0.4`.
7. [ ] Freeze activity, PSR, pose heads. Freeze backbone blocks 0-10.
8. [ ] Train detection head + FPN, 30 epochs. Monitor gates G_C1 through G_C4.
9. [ ] If G_C1 fails (epoch 5, mAP50 < 0.05): abort, re-examine decode formula and backbone features.

### Medium-Term (Days 7-9) -- Tier 3/4

10. [ ] If channel-compatible: transplant YOLOv8m head (Option D1), evaluate, fine-tune if promising.
11. [ ] If Option C achieves 0.20-0.30 but not 0.30: tune LR schedule, add k-means anchors, or accept ceiling.
12. [ ] If all options fail on MViTv2-S: distill from YOLOv8m teacher (Option A).

### Final (Days 10-12)

13. [ ] Full 38k-frame D3 evaluation with correct decode formula.
14. [ ] Per-class AP breakdown for all 24 detection classes.
15. [ ] Multi-task cost calculation: (single_task_mAP - multi_task_mAP) / single_task_mAP.
16. [ ] Prepare metrics table for paper.

---

## 10. What NOT to Do

1. **Do not chase 0.5734.** This number was a biased 250-batch class-balanced subsample artifact. It has been formally withdrawn by Agents 2, 3, 4, and 5. Any plan targeting 0.5734 is chasing a ghost.

2. **Do not train detection on ConvNeXt-Tiny.** The 0.00009 measurement is not a training artifact. Activity linear probe (0.2169 < 0.2217 baseline) and the 99.99% detection collapse both confirm ConvNeXt-Tiny cannot support detection in a multi-task setting. Training more on ConvNeXt-Tiny wastes GPU hours.

3. **Do not implement new architecture code.** The `use_yolov8_head=True` flag already exists in MTLMViTModel. The ASFFNeck import already exists. The `use_p2_level` flag already exists. Use config, not code.

4. **Do not train detection before fixing the decode formula.** If evaluate.py decodes with `dx * a_w` but the model was trained with `dx * 0.1` (or vice versa), all mAP numbers are wrong. This MUST be resolved first.

5. **Do not train all heads simultaneously from scratch.** The other three heads (activity, PSR, pose) have known-good configurations. Freeze them. Detection is the only head being rebuilt. Joint fine-tuning can come after detection independently reaches >0.20.

6. **Do not report per-head-best as a unified model result.** If detection reaches 0.30 on a config where activity drops to 0.0, that's not a unified model -- it's a detection-only model with dead heads. All 4 heads must be measured on the same checkpoint.

---

## 11. Success Criteria

### 11.1 Minimum Viable Detection (Gate G_C3)

- det_mAP50 >= 0.20 on full 38k D3 eval
- All 4 heads functional (act > 0.15, psr > 0.50, pose < 12 deg)
- Single checkpoint, single forward pass
- No temperature scaling or calibration tricks on detection

### 11.2 Target Detection (Gate G_C4)

- det_mAP50 >= 0.30 on full 38k D3 eval
- At least 18 of 24 classes have non-zero AP
- All 4 heads within 15% of their individual best metrics
- Reproducible: two independent eval runs agree within 0.02 mAP50

### 11.3 Stretch Detection

- det_mAP50 >= 0.45 on full 38k D3 eval
- All 24 classes have non-zero AP
- Detection + activity + PSR + pose all within 10% of individual bests
- This is competitive with the single-task YOLOv8m (0.995) given the multi-task overhead

---

**Agent 3 (Detection Head Rebuild) signing off.** The path to det > 0.30 exists. It requires: (1) resolving the decode formula, (2) switching to the YOLOv8 DFL head that already has a config flag, (3) training on MViTv2-S with other heads frozen. The probability is ~40% because MViTv2-S has already demonstrated det=0.214 in multi-task mode with a weaker head architecture. The remaining gap from 0.214 to 0.30 is bridgeable through anchor-free detection, ASFF fusion, and P2-level features -- all of which are existing config flags, not new code.
