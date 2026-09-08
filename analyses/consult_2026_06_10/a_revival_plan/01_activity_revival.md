# Agent 1: Activity Revival Plan -- Frame-Level Top-1 to 0.6223

**Date:** 2026-08-01
**Role:** Activity Revival Specialist (Agent 1 of 5-agent debate team)
**Target:** Revive frame-level activity top-1 to 0.6223 (achieved 2026-07-08 in `src/runs/rf_stages/checkpoints/t3_full_eval.json`)
**Constraint:** DO NOT make any code changes. This is a strategy document only.
**Codebase:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/`

---

## Executive Summary: The 0.6223 Is Architecturally Incompatible

**The 0.6223 frame-level activity top-1 was produced by a completely different model than the current multi-task system.** Specifically:

- **MViTv2-S (WACV 2024 Meccano pretrained)**: A video-level model processing 16-frame clips with 3D convolutions and spatiotemporal self-attention. 34.3M parameters. Single-task (activity only). Clip-level inference on 916 val clips using 69-group (hybrid) class mapping.
- **ConvNeXt-Tiny (current multi-task)**: A per-frame 2D CNN backbone (~28.6M params). Activity handled by a simple MLP (LayerNorm-Linear(512,256)-GELU-Dropout(0.3)-Linear(256,num_classes), ~672K params in simple mode). Per-frame prediction on shuffled frames. Best frame-level top-1: 0.1288 (d3_full_eval, 38k frames).

**The gap between 0.6223 and 0.1288 is not a training issue -- it is an architectural gap.** The MViTv2-S processes temporal video clips with 3D attention; the ConvNeXt-Tiny sees individual frames in isolation. "Reviving" 0.6223 on ConvNeXt-Tiny is impossible. The realistic target is to make the ConvNeXt-Tiny activity head produce non-random predictions, then evaluate whether a separate video-level model (MViTv2-S or VideoMAE) is needed for competitive activity recognition.

---

## 1. Root Cause Analysis

### 1.1 What EXACTLY Produced 0.6223

The entire chain was traced. Every claim below is verified by reading the source files.

**Checkpoint:**
- Path: `/media/newadmin/master/POPW/datasets/industreal/action_recognition_model_weights/mvit_rgb_meccano_pretrained.pyth`
- Type: MViTv2-S pretrained on Meccano dataset (WACV 2024), Kinetics-400 initialized
- Architecture: 16 MultiScaleBlock layers (96->768 dims), patch_embed (3D conv, stride=2/4/4), CLS token, head_projection (Linear(768,75))
- Params: 34,287,819 (397 keys loaded out of 397)

**Eval script:**
- File: `src/evaluation/eval_mecanno_mvitv2.py` (549 lines, standalone)
- Command-line: `python eval_mecanno_mvitv2.py --split val --out /tmp/t3_full_eval.json`
- This is NOT the production eval script (`scripts/eval/eval_activity_75class.py`). It is a standalone script that re-implements the entire MViTv2 architecture from scratch (lines 1-548) to match the Meccano pretrained weights.

**Config:**
- 75-class raw output -> remapped to 69 groups via `act_remap_75_to_69.json`
- 16-frame clips extracted from AR_labels.csv (uniform temporal sampling over action span)
- 224x224 CenterCrop, normalize mean=[0.45,0.45,0.45], std=[0.225,0.225,0.225]
- NO calibration (tau), NO temperature scaling -- this is RAW accuracy
- 916 clips across 16 recordings from val split

**Architecture (MViTv2-S, from eval_mecanno_mvitv2.py lines 309-384):**
```
Input: [B, 3, 16, 224, 224]
  patch_embed_proj: Conv3d(3, 96, kernel=(3,7,7), stride=(2,4,4))
  -> [B, 96, 8, 56, 56]
  CLS token prepended -> [B, 8*56*56+1, 96]
  16x MultiScaleBlock layers (combined QKV, 3D pooling, rel_pos_spatial+temporal):
    Block  0: dim=96->96,   nH=1,  Q=(1,1,1), KV=(1,8,8)
    Block  1: dim=96->192,  nH=2,  Q=(1,2,2), KV=(1,4,4)
    Block  2: dim=192->192, nH=2
    Block  3: dim=192->384, nH=4,  Q=(1,2,2), KV=(1,2,2)
    Blocks 4-13: dim=384->384, nH=4 (10 layers)
    Block 14: dim=384->768, nH=8,  Q=(1,2,2), KV=(1,1,1)
    Block 15: dim=768->768, nH=8
  LayerNorm(768) -> CLS token -> Linear(768, 75)
  softmax -> 75-class probs
  remap_75_to_69 (via act_remap_75_to_69.json): sum probs over group members
  argmax for top-1 prediction
```

**Why it works:**
- 16-frame video clips capture motion -- a person picking up a nut looks different from picking up a brace
- 3D convolutions + spatiotemporal attention learn action-specific motion patterns
- Meccano pretraining on assembly actions provides strong domain transfer
- 69-group mapping collapses 75 fine-grained classes into 56/69 groups, reducing the long-tail problem

### 1.2 What Produces the Current 0.1288 (ConvNeXt-Tiny Multi-Task)

**Checkpoint:**
- Path: `src/runs/rf_stages/checkpoints/best.pth` (epoch 18, promoted at epoch 11 via broken metric -- AC-1 contamination)
- Architecture: POPWMultiTaskModel with ConvNeXt-Tiny backbone, 46.5M total params

**Eval script:**
- File: `scripts/eval/eval_activity_75class.py` (813 lines)
- Mode: "checkpoint" mode loads multi-task model, runs per-frame inference
- OR: d3_full_eval via `full_eval_inprocess.py` -> metrics.json

**Config (from resolved_config.json, rf_stages training):**
```
ACTIVITY_HEAD_SIMPLE: True           # Per-frame MLP, bypass TCN+ViT
ACT_CLASS_GROUPING: "hybrid"         # standalone + verb groups
NUM_ACT_OUTPUTS: 56                  # hybrid produces 56 output classes
NUM_ACT_RAW_IDS: 74                  # 75 classes (0-74), class 37 absent
ACT_SAMPLER_MODE: "balanced"         # WeightedRandomSampler per-frame
ACTIVITY_GRAD_BLEND_RATIO: 1.0       # Full gradient to backbone
ACTIVITY_LOSS_WEIGHT: 0.8            # Manual loss weight
ACTIVITY_HEAD_DROPOUT: 0.3           # High dropout for regularization
ACTIVITY_HEAD_GRAD_CLIP: 5.0         # Gradient clipping
BACKBONE: convnext_tiny              # 28.6M params
BATCH_SIZE: 4, GRAD_ACCUM: 8, EFFECTIVE_BATCH: 32
EPOCHS: 2, SUBSET_RATIO: 0.02        # 4 recordings, 2850 train frames
```

**ActivityHead (simple mode, model.py lines 1478-1658):**
```
Input: proj_feat [B, 512] -- fused from GAP(C5_mod, 768) + GAP(P4, 256) + det_conf(24)
  -> Linear(1048, 512) -> proj_feat
ActivityHead:
  LayerNorm(512)
  -> Linear(512, 256) -> GELU -> Dropout(0.3)
  -> Linear(256, 56)  # 56 = NUM_ACT_OUTPUTS in hybrid mode
  -> logits [B, 56]
```

**Performance (d3_full_eval/metrics.json):**
- `act_frame_accuracy`: 0.1288 (frame-level top-1, 38,036 val frames)
- `act_macro_f1`: 0.0567 (across 56 output classes)
- Only 3 classes exceed 0.30 per-class accuracy (class 7: 0.422, class 28: 0.484, class 41: 0.363)
- Most classes at or near 0.0

**Performance (activity_clip_ep18, 4436 clips):**
- Clip-level top-1: 0.0282 (majority vote over 8-frame windows)
- Effectively random -- only class 0 dominates (0.672 on 122 clips, likely NA/background)

### 1.3 Why ConvNeXt-Tiny Activity Is Collapsed: Root Causes

**RC-1: Zero backbone signal for activity (FATAL).**
A linear probe on frozen ConvNeXt-Tiny features achieved 0.2169 top-1 vs the majority-class baseline of 0.2217 (always predict class 8). The frozen backbone encodes essentially no activity-relevant features. This is confirmed in `analyses/consult_2026_06_10/AAIML/145_PAPER_NARRATIVE_V3.md` and the Agent 5 synthesis (line 33): "The frozen backbone encodes no activity-relevant information."

Without informative backbone features, even a perfect activity head architecture cannot succeed. The MLP head is classifying noise.

**RC-2: Per-frame prediction without temporal context.**
The current head classifies individual frames. But actions like "tighten_nut" vs "loosen_nut" or "take_partial_model" vs "plug_partial_model" are defined by motion patterns, not individual frames. A static image of a hand near a nut cannot distinguish between tightening and loosening.

The MViTv2-S succeeds because it processes 16-frame clips with 3D convolutions -- it sees the motion. The ConvNeXt-Tiny sees a single frame and guesses.

**RC-3: Shuffled training frames destroy any temporal signal.**
The training uses a WeightedRandomSampler (ACT_SAMPLER_MODE=balanced) that shuffles frames across recordings. Even if the FeatureBank/temporal path were enabled, the "temporal" sequence is just a random collection of frames from different videos -- there is no real temporal signal.

This was explicitly acknowledged in the config comments (config.py lines 1229-1241): "training uses a class-balanced WeightedRandomSampler (per-frame, shuffled), so the FeatureBank ring buffer is fed NON-CONSECUTIVE frames from random videos -- there is no real temporal signal."

**RC-4: 56-class output with extreme class imbalance.**
In hybrid mode, NUM_ACT_OUTPUTS=56, but most classes have <50 training frames (subset_ratio=0.02, 4 recordings = 2850 total train frames). The balanced sampler forces each class to appear equally, but with so few examples per class, the model cannot learn meaningful per-class features. The d3_full_eval results show only 3 classes above 0.30 accuracy.

**RC-5: Multi-task gradient competition.**
With all 4 heads active (TRAIN_DET=True, TRAIN_HEAD_POSE=True, TRAIN_ACT=True, TRAIN_PSR=True) and Kendall uncertainty weighting, the activity head competes for backbone gradient against detection (5.3M params), head pose (1.6M), PSR (3.1M), and FPN (4.5M). The Kendall log_var for activity is clamped to KENDALL_LOG_VAR_MIN_ACT=-0.5, which allows moderate precision boosting, but the backbone gradient is dominated by the other tasks.

**RC-6: The activity head is architecturally too simple.**
At ~672K params (simple MLP), the activity head has 0.014x the capacity of the MViTv2-S's dedicated activity path (34.3M). Even if the backbone produced informative features, a 2-layer MLP with 256 hidden units cannot match a 16-layer transformer with spatiotemporal attention.

### 1.4 Why MViTv2-S Succeeded Where ConvNeXt-Tiny Failed

| Factor | MViTv2-S (0.6223) | ConvNeXt-Tiny (0.1288) |
|--------|-------------------|------------------------|
| **Input** | 16-frame video clips | Single frames |
| **Temporal modeling** | 3D convs + spatiotemporal attention | None (per-frame MLP) |
| **Pretraining** | Meccano (assembly actions) + Kinetics-400 | ImageNet-1K (static images) |
| **Parameters** | 34.3M | 672K (head only, backbone shared) |
| **Task** | Single-task (activity only) | Multi-task (4 heads share backbone) |
| **Class mapping** | 69-group | 56-group (hybrid) |
| **Training frames** | Meccano (large-scale) | 2850 (subset_ratio=0.02) |
| **Eval clips** | 916 (val split, full recordings) | 38,036 frames (d3_full_eval) |

---

## 2. Specific Code Changes Required

**NOTE: This section describes code changes for STRATEGY PURPOSES ONLY. No edits are made.**

### 2.1 Strategy A: Maximize ConvNeXt-Tiny Activity (Achievable Target: 0.25-0.35)

This strategy accepts the architectural constraints and tries to push the current simple MLP head as far as possible. It will NOT reach 0.6223 but can establish whether ConvNeXt-Tiny activity is fundamentally impossible or merely undertrained.

**Change A1: Enable sequence-mode training with real temporal windows.**
- File: `src/config.py`, line ~1360 (SAMPLER_MODE / SEQUENCE_MODE configs)
- Change: Set `SAMPLER_MODE = "sequence"` to use consecutive-frame windows instead of shuffled per-frame samples
- File: `src/models/model.py`, lines 2599-2615 (forward pass, temporal bank logic)
- Reason: Currently `temporal_bank` is `None` in non-staged training, so the activity head uses the "expand" path (replicates proj_feat 16x). With sequence mode, the FeatureBank would contain actual consecutive frames.
- File: `src/config.py`, line 1239
- Change: Set `ACTIVITY_HEAD_SIMPLE = False` to re-enable the TCN+2xViT temporal path
- Risk: 8.2M additional params, 92 MB extra GPU memory. Effective batch size may need reduction from 32 to 16.

**Change A2: Fix the gradient cancellation trap (distribution-matching bias init).**
- File: `src/models/model.py`, lines 1630-1656
- Status: This fix was ALREADY IMPLEMENTED on 2026-08-01 (per the code comments at lines 1630-1656). The distribution-matching logit bias initialization sets `bias = log(class_count / total)` instead of uniform -0.5, breaking the gradient symmetry where per-class CE gradients cancel to near-zero.
- Verification: Check that `_get_act_grouped_counts()` is working and that the bias values are being set correctly. The try/except at line 1655 silently swallows errors -- add logging.

**Change A3: Reduce NUM_ACT_OUTPUTS via verb-only grouping.**
- File: `src/config.py`, line 402
- Change: Set `ACT_CLASS_GROUPING = "verb"` (currently "hybrid")
- Effect: Collapses 75 classes to ~10-13 verb groups (take_*, plug_*, tighten_*, loosen_*, check_*, fit_*, put_*, align_*, browse_*)
- Reason: With 2850 training frames and 56 output classes, most classes have <50 frames. With 10-13 verb groups, each group has 100-400 frames -- learning becomes feasible.
- Tradeoff: The metric is no longer 75-class top-1 -- it's verb-group top-1. This must be clearly labeled in any reported numbers.

**Change A4: Single-task activity training (ablation).**
- File: Training script (e.g., `scripts/train/train_st_act.py` or similar)
- Change: Train ONLY the activity head on frozen ConvNeXt-Tiny backbone features
- Reason: Isolates whether the bottleneck is (a) multi-task gradient competition or (b) backbone features contain zero activity signal
- If single-task on frozen backbone achieves <0.22 (the linear probe result), the backbone is the bottleneck
- If single-task on frozen backbone achieves >0.30, multi-task interference is the bottleneck

**Change A5: Increase training data.**
- File: Training script
- Change: Set `SUBSET_RATIO = 1.0` (use all recordings)
- Effect: 2850 -> ~140K train frames across all recordings
- Reason: Activity is a data-hungry task. 2850 frames for 56 classes = ~51 frames/class on average, with many classes at <10 frames. Full dataset gives ~2500 frames/class.

**Change A6: Activity-specific LR and longer training.**
- File: Training script
- Change: Set `ACTIVITY_LR_MULTIPLIER = 3.0`, `EPOCHS = 20`
- Reason: Activity head is currently trained with same LR as detection (1e-4 base). Give it a higher LR to compensate for the weaker gradient signal from a collapsed head.

### 2.2 Strategy B: Separate Video-Level Activity Model (Achievable Target: 0.45-0.62)

This strategy accepts that per-frame 2D CNN activity recognition on IndustReal is fundamentally limited and builds a separate video-level model. This is the only path to approaching 0.6223.

**Change B1: Implement clip-based training for ConvNeXt-Tiny.**
- File: New script or modification to `scripts/train/train_st_act.py`
- Change: Sample 8-16 consecutive frames per clip, pass through ConvNeXt backbone, temporal-pool (e.g., avg over time), then classify
- This gives the ConvNeXt some temporal context without requiring 3D convolutions
- Expected ceiling: 0.35-0.45 (ConvNeXt can learn per-frame features, temporal pooling adds motion signal)

**Change B2: Use MViTv2-S pretrained weights directly.**
- File: `src/evaluation/eval_mecanno_mvitv2.py` (already exists!)
- Change: Package this as a production inference script rather than a one-off eval
- The weights are at: `/media/newadmin/master/POPW/datasets/industreal/action_recognition_model_weights/mvit_rgb_meccano_pretrained.pyth`
- This gives 0.6223 immediately -- it's the same model that produced t3_full_eval.json
- Limitation: This is single-task (activity only). Cannot be integrated into the multi-task model.

**Change B3: Train a VideoMAE or TimeSformer on IndustReal.**
- File: New training script
- Change: Use a video transformer (VideoMAE V2, TimeSformer) pretrained on Kinetics-400/SSv2, fine-tune on IndustReal
- Expected: 0.50-0.65 top-1 (video transformers benefit from temporal modeling + large-scale pretraining)
- Cost: 5-7 days on RTX 5060 Ti, 16 GB VRAM (batch=1, grad_accum=32)
- This is a new project, not a head repair.

### 2.3 Strategy C: Verb-Group Only (Quick Win, Honest Metric)

This strategy gives up on 75-class accuracy and targets verb-group accuracy. It is the most honest approach given the data constraints.

**Change C1: Switch to verb grouping and report verb-level metrics.**
- File: `src/config.py`, line 402
- Change: `ACT_CLASS_GROUPING = "verb"`
- Effect: Output reduced to ~10-13 verb groups
- File: Eval scripts
- Change: Report "verb-group top-1" as the primary metric, not "75-class top-1"
- Reason: 48/74 classes have <10 frames in the subset. 75-class accuracy is impossible on 2850 frames. Verb-group accuracy on 10-13 groups is achievable.

---

## 3. Training Config

### 3.1 Recommended Configuration for Revival Attempt

```python
# === Activity-Specific Config ===
ACT_CLASS_GROUPING = "verb"          # 10-13 verb groups (instead of 56 hybrid)
ACTIVITY_HEAD_SIMPLE = False         # Enable TCN+2xViT (8.2M params)
ACTIVITY_HEAD_SIMPLE_HIDDEN = 256    # Hidden dim for simple MLP (used as embed_dim for TCN+ViT)
ACTIVITY_HEAD_DROPOUT = 0.2          # Reduced from 0.3 (too aggressive for small dataset)
ACTIVITY_GRAD_BLEND_RATIO = 1.0      # Full gradient to backbone
ACTIVITY_LOSS_WEIGHT = 2.0           # Increased from 0.8 (activity needs stronger signal)
ACTIVITY_LR_MULTIPLIER = 3.0         # Activity head learns 3x faster than backbone
ACTIVITY_HEAD_GRAD_CLIP = 5.0        # Keep gradient clipping
ACT_SAMPLER_MODE = "sequence"        # Use consecutive-frame windows
SUBSET_RATIO = 0.15                  # ~12 recordings, ~25K train frames (up from 4)
SAMPLER_MODE = "balanced"            # Keep balanced sampling for class imbalance

# === Multi-Task Config ===
TRAIN_ACT = True
TRAIN_DET = False                    # FREEZE detection during activity-focused phase
TRAIN_HEAD_POSE = False              # FREEZE head pose during activity-focused phase
TRAIN_PSR = False                    # FREEZE PSR during activity-focused phase
USE_KENDALL = False                  # Disable Kendall -- single-task focus phase
STAGED_TRAINING = False

# === Training Config ===
BATCH_SIZE = 2                       # Reduced from 4 (TCN+ViT uses more VRAM)
GRAD_ACCUM_STEPS = 16                # Effective batch = 32
EPOCHS = 20                          # Longer training (was 2)
BASE_LR = 0.0005                     # Keep base LR
LR_SCHEDULER = "cosine"              # Cosine annealing
LR_WARMUP_EPOCHS = 3                 # Warmup for activity head
MIXED_PRECISION = True               # Enable AMP for memory savings
```

### 3.2 GPU Allocation

| Phase | GPU | VRAM Needed | Duration |
|-------|-----|-------------|----------|
| Activity-focused training (single-task on ConvNeXt) | RTX 3060 | ~6 GB (with TCN+ViT) | 2-3 days |
| Activity eval (full validation set) | RTX 3060 or CPU | 4 GB | 2-4 hours |
| MViTv2-S eval (already done -- 0.6223) | RTX 3060 | 3 GB | 15 minutes |

### 3.3 Checkpoint Strategy

- Start from: `src/runs/full_multi_task_tma_tbank/checkpoints/best.pth` (epoch 15, compatible architecture, 670MB)
- OR: Start from scratch with ConvNeXt-Tiny ImageNet pretrained weights (cleaner, avoids AC-1 contamination)
- Save every epoch: `activity_revival/checkpoints/epoch_N.pth`
- Record SHA256 of each checkpoint before eval

---

## 4. Expected Timeline

### 4.1 Phase-by-Phase Schedule

```
Day 1-2: Configuration + infrastructure
  - Implement ACT_CLASS_GROUPING="verb" and verify NUM_ACT_OUTPUTS
  - Set up single-task activity training script
  - Verify sequence-mode sampler produces consecutive-frame windows
  - Launch training on RTX 3060

Day 3-5: Training (20 epochs)
  - Monitor activity loss and accuracy each epoch
  - If loss plateaus after epoch 5, abort and diagnose
  - Save checkpoint at best validation accuracy

Day 6-7: Evaluation
  - Run full d3_full_eval on best checkpoint
  - Run clip-level eval (activity_clip.py style)
  - Run per-class breakdown
  - Compare against:
    - Linear probe baseline: 0.2169 (frozen ConvNeXt)
    - Current best multi-task: 0.1288 (d3_full_eval)
    - MViTv2-S ceiling: 0.6223 (separate model)

Day 8: Analysis and decision
  - If verb-group top-1 >= 0.35: Activity revival is successful. Integrate into multi-task model with gradient isolation.
  - If verb-group top-1 < 0.25: ConvNeXt-Tiny activity is fundamentally limited. Abandon multi-task activity on this backbone.
  - Either way: Document the honest numbers with clear labeling (verb-group, not 75-class).
```

### 4.2 Go/No-Go Gates

| Gate | Metric | Threshold | Action if Below |
|------|--------|-----------|-----------------|
| G1 (Day 2) | Training loss decreases in first 500 steps | Loss < ln(13) = 2.56 | Abort -- gradient cancellation trap still active |
| G2 (Day 5) | Val accuracy > majority-class baseline | > 0.25 (verb, 10-13 classes) | Abandon ConvNeXt activity. Use MViTv2-S for activity. |
| G3 (Day 7) | Per-class accuracy on >= 5 verb groups | >= 5 groups with > 0.30 | Activity only works on dominant verbs. Report as partial success. |
| G4 (Day 8) | Verb-group top-1 >= 0.35 | >= 0.35 | If below: activity on ConvNeXt is dead. Publish as negative result. |

---

## 5. Verification Protocol

### 5.1 Before Training

1. **Verify class mapping**: Run `C.get_num_act_outputs()` and confirm it returns ~10-13 for verb mode
2. **Verify sampler**: Log 100 consecutive frame indices from the sequence-mode sampler. Confirm they are from the same recording and temporally consecutive.
3. **Verify head arch**: Print model.activity_head and confirm TCN+ViT+cls_token are created (not None)
4. **Verify bias init**: Log `simple_classifier[-1].bias` values. Confirm they are distribution-matched (not uniform -0.5)
5. **Record baseline**: Run linear probe on frozen ConvNeXt features with verb grouping to establish the frozen-backbone ceiling

### 5.2 During Training

1. **Per-epoch validation**: Compute activity accuracy on a fixed 500-frame validation subset
2. **Gradient monitoring**: Log gradient norms for activity head layers. If any layer has zero gradient for 3+ consecutive epochs, flag as dead.
3. **Loss monitoring**: Activity CE loss should decrease from ~ln(13) = 2.56 towards 0. If it plateaus above 2.0, the head is not learning.
4. **Class distribution**: Log the distribution of predicted classes. If >80% of predictions are a single class, the head has collapsed.

### 5.3 After Training

1. **Full validation eval**: Run `d3_full_eval` on the best checkpoint. Record verb-group top-1, macro-F1, per-class accuracy.
2. **Compare against baselines**:
   - Frozen ConvNeXt linear probe (verb groups)
   - Current best multi-task (0.1288 on hybrid)
   - MViTv2-S (0.6223 on 69-group)
3. **Honest reporting**: All numbers must include:
   - Checkpoint path + SHA256
   - Class grouping mode (verb/hybrid/none)
   - Number of output classes
   - Eval split and number of frames
   - Whether tau calibration was used (it should NOT be for raw accuracy)
4. **Cross-check with Agent 4 (Pose) and Agent 2 (Detection)**: Ensure activity changes don't regress other heads

---

## 6. Risk Assessment

### 6.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ConvNeXt backbone has zero activity signal even after fine-tuning | HIGH (60%) | FATAL -- activity on ConvNeXt is impossible | Fall back to MViTv2-S standalone model. Publish the linear probe result as negative evidence. |
| TCN+ViT head causes OOM with batch_size=2 | MEDIUM (30%) | Delays training by 1-2 days | Reduce to batch=1, grad_accum=32. Disable mixed precision if needed. |
| Verb-only grouping loses too much granularity | MEDIUM (40%) | Paper reviewers may reject verb-level accuracy as insufficient | Keep hybrid mode as comparison. Report both verb and hybrid numbers. |
| Activity improvements regress detection/pose | LOW (15%) | Requires re-tuning other heads | Keep detection/pose frozen during activity-focused phase. Re-enable gradually after activity converges. |
| Training on subset_ratio=0.15 overfits to 12 recordings | MEDIUM (35%) | Val accuracy looks good but doesn't generalize | Use leave-one-recording-out cross-validation. Report per-recording accuracy. |

### 6.2 Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| RTX 3060 occupied by PSR repair training | HIGH (currently in use) | Delays activity training by 5-7 days | Wait for PSR repair to complete (~Aug 7 per Agent 5 synthesis). Queue activity training next. |
| OOM crash during TCN+ViT training | MEDIUM (25%) | Loses 2-12 hours of training | Use memsafe-training.sh wrapper. Save checkpoint every 500 steps. |
| Results not reproducible | LOW (10%) | Invalidates reported numbers | Record SHA256 of checkpoint. Save resolved_config.json. Re-run eval twice on different seeds. |

### 6.3 Strategic Risk

**The biggest risk is that this plan is attempting the impossible.** The linear probe result (0.2169 vs 0.2217 baseline) strongly suggests the ConvNeXt-Tiny backbone, pretrained on ImageNet-1K (static object recognition), does not encode activity-relevant features for IndustReal assembly actions. Fine-tuning the backbone might help, but if the features are fundamentally wrong (object identity vs motion), no amount of fine-tuning will fix it.

**The honest assessment:** This plan is unlikely to achieve 0.6223 or anything close to it on ConvNeXt-Tiny. The realistic best-case outcome is ~0.35 verb-group top-1, which would demonstrate that activity is learnable but severely bottlenecked by the backbone. The most likely outcome is that activity on ConvNeXt-Tiny is abandoned in favor of MViTv2-S or a similar video-level model.

---

## 7. Cross-References to Other Agent Plans

### 7.1 Agent 2: Detection Revival (02_detection_revival.md)
- **Conflict**: Detection currently occupies RTX 5060 Ti for single-task training (epoch 43/99). Activity training should use RTX 3060 (different GPU) -- no resource conflict.
- **Dependency**: If detection revival succeeds and the backbone learns better features, activity may benefit from shared representations. The Agent 2 plan's single-task ConvNeXt detection experiment (Section 5) will reveal whether the backbone is the bottleneck for ALL tasks or just activity.
- **Shared risk**: Both plans face the same fundamental question -- is ConvNeXt-Tiny capable of supporting the task, or is the backbone the bottleneck?

### 7.2 Agent 4: Pose Refinement (04_pose_refinement.md)
- **No conflict**: Pose operates on different features (C4+C5 features for HeadPoseHead) and is the only head that works reasonably well on ConvNeXt-Tiny (7.83 degrees forward_angular_MAE).
- **Lesson from Agent 4**: The legacy HeadPoseHead achieved 6.15 degrees with raw 9-DoF regression and no special architecture. A simple head CAN work if the backbone features are informative. Activity's simple MLP head fails because the backbone features lack activity information, not because the head is too simple.
- **Shared insight**: Agent 4's plan emphasizes the importance of column ordering in the output representation (Section 1.4-1.5). For activity, the analogous concern is the 75-to-56/69 class remapping -- we must verify that the remapping is correct and consistent between training and eval.

### 7.3 Agent 5: Integration Synthesis (05_integration_synthesis.md)
- **Direct conflict**: Agent 5's synthesis (Section 1.1, line 34) states: "Agent 3 (TCN+ViT activity)... The TCN+ViT must run on a DIFFERENT backbone (e.g., MViTv2-S pretrained)." This plan's Strategy B agrees.
- **Resource allocation**: Agent 5's GPU schedule (Section 3.1) allocates RTX 3060 to PSR repair (until ~Aug 7), then to Kendall ablation. Activity training must queue behind PSR repair.
- **Strategic divergence**: Agent 5 recommends abandoning activity on ConvNeXt-Tiny and using a separate MViTv2-S model (Section 2.1, STEP 5). This plan's Strategy A (push ConvNeXt as far as possible) conflicts with that recommendation. The resolution: Strategy A is a 2-3 day diagnostic experiment that either (a) proves activity is impossible on ConvNeXt (negative result, publishable) or (b) discovers that fine-tuning the backbone recovers activity signal (positive result, proceed). Either outcome is valuable.
- **Critical path**: Agent 5's STEP 0 (completed) includes the activity linear probe (0.2169 vs 0.2217 baseline) as diagnostic evidence that "ConvNeXt backbone has zero activity signal." This plan must acknowledge and address this evidence.

### 7.4 The 5 Kendall Bugs (from Agent 5's gradient balancing action plan)

These affect activity training and are listed here for cross-reference:

1. **NaN guard disconnects computation graph** -- If triggered during activity loss computation, activity gradients are zeroed.
2. **Activity head leaks gradients to backbone without stop_grad** -- Mitigated by ACTIVITY_GRAD_BLEND_RATIO=1.0, but this means activity gradients compete directly with detection/pose/PSR.
3. **GIoU per-image normalization dilutes dense-positive frames** -- Detection-specific, but the dilution reduces overall gradient magnitude for ALL tasks sharing the backbone.
4. **Staged training freezes reinit activity head** -- Not applicable if STAGED_TRAINING=False.
5. **ACTIVITY_LOSS_WEIGHT conflicts with KENDALL_LOG_VAR_MIN_ACT** -- ACTIVITY_LOSS_WEIGHT=0.8 multiplies the loss, while KENDALL_LOG_VAR_MIN_ACT=-0.5 controls precision. These two mechanisms can fight each other.

For this plan: Kendall should be DISABLED (Strategy A uses single-task activity training). Bugs 1-5 become irrelevant during the diagnostic phase. If activity is later integrated into the multi-task model, bugs 2 and 5 must be addressed.

---

## 8. Honest Disclosures

### 8.1 What This Plan CANNOT Achieve

- **0.6223 frame-level top-1 on ConvNeXt-Tiny.** That number came from an MViTv2-S model with 3D convolutions and spatiotemporal attention. ConvNeXt-Tiny is a per-frame 2D CNN with no temporal modeling. The architectural gap is fundamental.
- **75-class fine-grained activity recognition on 2850 frames.** With 48/74 classes having <10 frames in the training subset, 75-class accuracy is statistically impossible. Verb-group accuracy is the honest target.
- **Multi-task activity that doesn't regress other heads.** Activity is the most data-hungry head with the weakest signal. Any activity improvement that requires backbone fine-tuning risks regressing detection and pose.

### 8.2 What This Plan CAN Achieve

- **Determine whether ConvNeXt-Tiny activity is fundamentally impossible or merely undertrained.** The diagnostic experiments (Strategy A) will produce a definitive answer.
- **Establish an honest verb-group baseline.** If the linear probe shows zero signal but fine-tuning recovers 0.30-0.35, that's a publishable finding about the importance of backbone fine-tuning for activity.
- **Document the ConvNeXt-Tiny activity ceiling.** Even negative results are valuable for the paper's "transparent pathology" narrative (Agent 5's Tier 4 fallback).

### 8.3 Recommended Paper Framing

Do NOT claim "activity revival to 0.6223" in the paper. Instead:

1. Report the MViTv2-S result (0.6223, 69-group, 916 clips) as evidence that activity IS learnable with video-level architectures.
2. Report the ConvNeXt-Tiny linear probe result (0.2169 vs 0.2217 baseline) as evidence that per-frame 2D CNN features lack activity information.
3. Report the best ConvNeXt-Tiny multi-task result (0.1288) as the current multi-task activity performance.
4. Frame the contribution as: "Activity recognition requires temporal modeling. Per-frame 2D CNNs are architecturally insufficient. Future multi-task systems should incorporate video-level backbones or temporal feature banks."

---

## Appendix A: Key File Inventory

| File | Description |
|------|-------------|
| `src/evaluation/eval_mecanno_mvitv2.py` | Standalone MViTv2-S eval script that produced 0.6223 |
| `src/runs/rf_stages/checkpoints/t3_full_eval.json` | The 0.6223 result (5 lines) |
| `src/runs/rf_stages/checkpoints/t3_full_eval_run.log` | Full eval log showing 62.23% across 916 clips |
| `src/runs/rf_stages/checkpoints/d3_full_eval/metrics.json` | Current best ConvNeXt-Tiny activity: 0.1288 |
| `src/runs/rf_stages/checkpoints/activity_75class_eval/summary.txt` | Linear probe on frozen MViTv2-S: 0.3836 |
| `src/runs/rf_stages/checkpoints/activity_75class_eval/metrics.json` | Linear probe per-class breakdown (75 classes) |
| `src/runs/rf_stages/checkpoints/activity_clip_ep18/activity_clip.json` | Clip-level eval: 0.0282 (essentially random) |
| `src/runs/rf_stages/checkpoints/logs/linprobe.log` | Linear probe training log |
| `src/runs/rf_stages/logs/train.log` | rf_stages training log (ConvNeXt-Tiny multi-task) |
| `src/runs/rf_stages/logs/resolved_config.json` | Full training config (270 keys) |
| `src/models/model.py` (lines 1478-1737) | ActivityHead class definition |
| `src/config.py` (lines 380-470, 1229-1308, 2735-2749) | Activity config + class grouping |
| `scripts/eval/eval_activity_75class.py` | Production activity eval script (813 lines) |
| `scripts/probes/overfit_probe.py` | Overfit diagnostic script (412 lines) |
| `analyses/consult_2026_06_10/AAIML/145_PAPER_NARRATIVE_V3.md` | Paper narrative v3 with activity collapse analysis |
| `AUDIT_TRUTHFULNESS.md` | Truthfulness audit (Finding E: tau calibration inflation) |
| `STATE_OF_TRUTH_20260801.md` | Honest assessment of current vs target metrics |
| `feedback_sota_history.md` | Authoritative SOTA metric history |

## Appendix B: Key Config Values for Activity

| Config Key | Current Value (rf_stages) | Recommended (Revival) | Purpose |
|-----------|--------------------------|----------------------|---------|
| ACT_CLASS_GROUPING | hybrid | verb | Reduce output classes from 56 to ~10-13 |
| NUM_ACT_OUTPUTS | 56 | ~10-13 | Number of output classes |
| ACTIVITY_HEAD_SIMPLE | True | False | Enable TCN+2xViT |
| ACTIVITY_HEAD_SIMPLE_HIDDEN | 256 | 256 | Hidden/embed dim |
| ACTIVITY_HEAD_DROPOUT | 0.3 | 0.2 | Regularization |
| ACTIVITY_GRAD_BLEND_RATIO | 1.0 | 1.0 | Gradient to backbone |
| ACTIVITY_LOSS_WEIGHT | 0.8 | 2.0 | Manual loss weight |
| ACTIVITY_LR_MULTIPLIER | 1.0 | 3.0 | Head vs backbone LR ratio |
| ACTIVITY_HEAD_GRAD_CLIP | 5.0 | 5.0 | Gradient clipping |
| ACT_SAMPLER_MODE | balanced | sequence | Consecutive frames |
| SUBSET_RATIO | 0.02 | 0.15 | More training data |
| EPOCHS | 2 | 20 | Longer training |
| KENDALL_FIXED_WEIGHTS | False | N/A | Disable Kendall |
| TRAIN_ACT | True | True | Keep training |
| TRAIN_DET/PSR/POSE | True | False | Freeze other heads |
