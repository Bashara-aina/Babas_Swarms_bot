# Agent 4: Model Architecture & Weight Initialization Audit

Date: 2026-06-17
Files audited:
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/model.py` (2191 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/industreal_model.py` (7 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/roi_detector.py` (379 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/psr_transition.py` (304 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/video_stream.py` (361 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/head_pose_geo.py` (252 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py` (reinit-heads function, lines 2236-2400)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/config.py` (lines 555-580)

---

## 1. ConvNeXt-T Backbone Setup

**File**: model.py lines 163-251

Source: `torchvision.models.convnext_tiny` with `ConvNeXt_Tiny_Weights.DEFAULT` (NOT timm). Correct.

Stage grouping at lines 193-198 is correct:
- Stage 0: features[0] (stem) + features[1] (stage1, 3 blocks) -> C2, 96ch, stride 4
- Stage 1: features[2] (downsample) + features[3] (stage2, 3 blocks) -> C3, 192ch, stride 8
- Stage 2: features[4] (downsample) + features[5] (stage3, 9 blocks) -> C4, 384ch, stride 16
- Stage 3: features[6] (downsample) + features[7] (stage4, 3 blocks) -> C5, 768ch, stride 32

Gradient checkpointing (lines 239-243): uses `checkpoint.checkpoint` with `use_reentrant=False`. Trades ~20% compute for ~50% activation memory. Correct implementation.

`set_backbone_stage_requires_grad` (lines 253-296): Supports freezing individual stages for synthetic pretrain domain adaptation. Stage mapping is correct for both ConvNeXt and ResNet.

### Issues:
- None critical. Implementation matches torchvision's ConvNeXt-Tiny API exactly.

---

## 2. FPN Implementation

**File**: model.py lines 378-428

Standard FPN: [C3, C4, C5] -> [P3, P4, P5, P6, P7], all 256ch.

Lateral 1x1 convs + top-down nearest-neighbor upsampling + 3x3 smooth convs. P6 from stride-2 conv on C5, P7 from stride-2 conv on ReLU(P6). Standard RetinaNet FPN topology.

Weight init: Kaiming-uniform a=1, zero bias (lines 405-409). No detach calls inside FPN.

### Issues:
- [LOW] Lines 413-415 comments reference ResNet-50 channel counts ("C3(512ch)", "C4(1024ch)", "C5(2048ch)") but for ConvNeXt-Tiny these are 192/384/768. The code uses parameterized `fpn_in_channels` so it functions correctly, but the comments are misleading when ConvNeXt is active.

---

## 3. Detection Head (RetinaNet-style)

**File**: model.py lines 488-555

- Cls subnet: 4x Conv3x3+GroupNorm(8)+ReLU (via `make_subnet()`)
- Reg subnet: same structure (shared `make_subnet()` call)
- `cls_score`: Conv2d(256, 9 anchors * 24 classes, 3x3)
- `reg_pred`: Conv2d(256, 9 anchors * 4, 3x3)

Anchors: 3 ratios x 3 scales = 9 per location on P3-P7 (model.py lines 434-482)

### Weight init (lines 519-534):
- Subnet convs: normal(0.01) weights, zero bias
- `cls_score.bias`: pi=0.03 (`-math.log(0.97/0.03) = -3.48`)
- `reg_pred`: normal(0.01) weights, zero bias

### Issues:
- [LOW] File header docstring line 23 says "pi=0.01" but actual code at line 530 uses pi=0.03. The header is stale/wrong.
- [LOW] --reinit-heads uses pi=0.01 (train.py line 2276) while original init uses pi=0.03 (model.py line 530). Reinit produces a more conservative prior (bias -4.6 vs -3.48), which means reinit and fresh init are intentionally different. Documented behavior but important for reproducibility.

---

## 4. Pose Head

**File**: model.py lines 561-607

Architecture:
- ConvTranspose2d(256->256, k=4, s=2, p=1) + GroupNorm(32) + ReLU
- Heatmap head: Conv2d(256->256, 3x3) + ReLU + Conv2d(256->17, 1x1)
- Soft-argmax(temperature=0.07) -> [B, 17, 2] keypoints + [B, 17] confidence

### Issues:
- [MEDIUM] **No `_init_weights` method**. PoseHead has zero custom initialization. All layers (ConvTranspose2d, Conv2d, GroupNorm) use PyTorch defaults (Kaiming-uniform for conv, ones/zeros for GN). Inconsistent with every other head in the model. The Conv2d(256, 17, 1) heatmap output layer is a key prediction head but uses default Kaiming init instead of small-std normal init used by other heads.
- [LOW] PoseHead is preserved (NOT reinitialized) by --reinit-heads. This is intentional but means if pose ever collapses, there's no recovery path.

---

## 5. Head Pose Head (Legacy 9-DoF)

**File**: model.py lines 1392-1427

Architecture:
- GAP(C4) + GAP(C5) -> concat -> [B, c4_ch + c5_ch]
- MLP: 1152->512->256->9 (for ConvNeXt: 384+768=1152)
- LayerNorm + GELU + Dropout(0.15/0.1) intermediate
- Raw 9-DoF output: [forward(3), position(3), up(3)]

### Issues:
- [HIGH] **No `_init_weights` method.** HeadPoseHead is the only head that completely lacks any weight initialization. All 5 Linear layers and 2 LayerNorm modules use PyTorch defaults, not the documented small-std-normal init. This is inconsistent with:
  - GeometryAwareHeadPose (head_pose_geo.py) which has proper init
  - All other heads in the model
- [LOW] Line 1409 comment says `# 3072` but for ConvNeXt-Tiny (default backbone), total_in = 384+768 = 1152, not 3072. Only correct for ResNet-50 (1024+2048=3072).
- [LOW] HeadPoseHead is NOT reinitialized by --reinit-heads. If head pose degrades, there's no recovery path.

---

## 6. Geometry-Aware Head Pose Head

**File**: head_pose_geo.py lines 94-222

Architecture:
- GAP(C4=384) + GAP(C5=768) -> concat -> [B, 1152]
- Rotation MLP: 1152->512->256->128->6 (6D continuous representation)
- Position MLP: 1152->512->256->128->3
- 6D -> rotation matrix: `rotation_6d_to_matrix` (Zhou et al. CVPR 2019)
- Position: `tanh` output normalized to [-1, 1]

Loss: geodesic angular + cosine + MSE position.

### Issues:
- [LOW] `to_legacy_9dof` at line 215-221: forward direction is column 2 (z-axis), up is column 1 (y-axis). Assumes a specific coordinate system convention. Must match GT convention -- data contract issue.
- [LOW] Guarded by `C.USE_GEO_HEAD_POSE` config flag (model.py line 1731). Default is presumably False since legacy HeadPoseHead is still the default.

---

## 7. Activity Head

**File**: model.py lines 1233-1386

Architecture:
1. `proj_features`: Linear(24+768+256=1048 -> 512)
2. TCN: LayerNorm + Depthwise Conv1d(k=5, groups=512) + Pointwise Conv1d + GELU + Dropout + DropPath(0.1)
3. 2x ViT blocks (8 heads, d_k=64, FFN 512->2048->512, DropPath 0.1/0.15)
4. CLS token + classifier: LayerNorm + Dropout(0.1) + Linear(512 -> 74)
5. Optional VideoMAE fusion

### Issues:
- [LOW] `proj_features` and `activity_classifier` have no explicit `_init_weights`. They use PyTorch default Linear init (Kaiming-uniform).
- [LOW] --reinit-heads reinitializes these with different methods (std=0.02 normal for proj, std=0.01 for classifier with bias=-0.5). Reinit produces a different starting state than fresh init.

---

## 8. PSR Head

**File**: model.py lines 1433-1638

Architecture:
1. Multi-scale GAP(P3+P4+P5) -> 768
2. `per_frame_mlp`: Linear(768->512) + LN + GELU + Dropout + Linear(512->256) + LN
3. Causal Transformer: 3 layers, 4 heads, d_model=256, FFN=1024, pre-norm
4. 11 output heads: Linear(256->64) + GELU + Dropout + Linear(64->1)

Weight init:
- Output heads bias: +0.1 explicitly set on first Linear (lines 1500-1505)
- All other layers: PyTorch defaults. No `_init_weights` method.

### Issues:
- [LOW] PSRHead has no `_init_weights` method. Output head bias at line 1503 is set inline. All other layers use PyTorch defaults.
- [LOW] --reinit-heads reinitializes output heads with zero bias (replacing +0.1). Reinit changes output head bias from +0.1 to 0.0.
- [LOW] Debug `print()` statements at lines 1529-1553 and 1984-1999 fire at steps {0, 1, 10, 100, 200, 500}. Produces stdout noise.

---

## 9. Weight Init Summary -- ALL Heads

| Component | Explicit init? | Init method | Reinit by --reinit-heads? | Reinit method |
|---|---|---|---|---|
| Backbone (ConvNeXt) | N/A (pretrained) | ImageNet weights | NO | Preserved |
| ResNet-50 Backbone | N/A (pretrained) | ImageNet weights | NO | Preserved |
| FPN | YES | Kaiming-uniform a=1, zero bias | YES | Same |
| DetectionHead | YES | normal(0.01) subnets, pi=0.03 cls | YES | pi=0.01 (DIFFERS) |
| PoseHead | NO | PyTorch defaults only | NO | Preserved |
| HeadPoseHead (legacy) | NO | PyTorch defaults only | NO | Preserved |
| GeometryAwareHeadPose | YES | normal(0.01) w/ identity bias | NO (if used) | Preserved |
| ActivityHead | Partial | ViT/TCN explicit; proj/classifier default | YES | Full reinit, diffs |
| PSRHead | Output bias only | Default +0.1 bias on layer 1 | YES | Full reinit, zero bias |
| PoseFiLM | YES | normal(0.01), gamma bias=1 | NO | Preserved |
| HeadPoseFiLM | YES | normal(0.01), gamma bias=1 | NO | Preserved |
| FeatureBank | N/A (no params) | - | - | - |
| VideoMAEStream | N/A (pretrained/frozen) | VideoMAE-K400 checkpoint | NO | Preserved |

---

## 10. Gradient Paths -- detach/stop_grad Map

| Location | Line(s) | What is detached? | Effect |
|---|---|---|---|
| PoseFiLM: confidence | model.py:683 | `confidence.detach()` | Keypoint confidence stop-grad'd |
| Detection: det_conf | model.py:1928-1935 | `with torch.no_grad():` | Always stop-grad'd before ActivityHead |
| FeatureBank (default) | model.py:1198-1199 | Stored features `detach().clone()` | C.FEATURE_BANK_DETACH (default True) |
| HeadPoseFiLM | model.py:2034 | `head_pose.detach()` | Per paper spec |
| Detection regression | model.py:550 | `feat.detach()` when DETACH_REG_FPN | Conditional |
| PSR FPN (sequence) | model.py:1957-1960 | p3,p4,p5 detached when DETACH_PSR_FPN | Conditional |
| PSR FPN (non-seq) | model.py:2010-2014 | Pyramid p3/p4/p5 detached | Same conditional |
| PSR inference cache | model.py:1587 | Cached features detached | Inference only |

### Key gradient flow notes:
1. Classification gradients DO flow into FPN. Only the regression subnet is isolated by --detach-reg-fpn.
2. Detection confidence gradients NEVER reach ActivityHead (stop_grad on det_conf).
3. HeadPoseFiLM receives detached head_pose.
4. FeatureBank gradient flow is optional via C.FEATURE_BANK_DETACH. Default: detached.

---

## 11. --reinit-heads Implementation

**File**: train.py lines 2236-2400 and 3251-3321

### What IS reinitialized:
1. **FPN** (8 Conv2d): Kaiming-uniform a=1, zero bias
2. **Detection head**: cls_score (pi=0.01), reg_pred (std=0.01), cls_subnet + reg_subnet (Kaiming-normal)
3. **Activity head**: proj_features (std=0.02), cls_token (trunc_normal), vit (xavier), classifier (std=0.01, bias=-0.5), tcn (Kaiming)
4. **PSR head**: per_frame_mlp (std=0.02), transformer (xavier), output_heads (std=0.02, zero bias), gap modules (Kaiming)

### What is NOT reinitialized:
Backbone, PoseHead, HeadPoseHead, GeometryAwareHeadPose, PoseFiLM, HeadPoseFiLM, FeatureBank, VideoMAEStream.

### Side-effects:
- Kendall log_vars reset to 0.0
- EMA shadow re-anchored for det/act/psr/fpn params
- AdamW optimizer exp_avg/exp_avg_sq zeroed for det/act/psr/fpn params
- PSR warmup: 200 steps of 2x grad multiplier
- Detection reg warmup: ramp from 1% to 100% over 1000 steps

### Issues:
- [MEDIUM] DetectionHead pi mismatch: original=0.03, reinit=0.01. Different starting bias (differ by ~1.1 nats). Intentionally documented but can cause subtle convergence differences.
- [LOW] PSR output head reinit replaces +0.1 bias with zero bias (train.py:2384).
- [LOW] PSR gap_p3/p4/p5 reinit check (train.py:2387-2394) targets `isinstance(g, nn.Conv2d)` but AdaptiveAvgPool2d has no params. Harmless no-op.

---

## 12. --detach-reg-fpn and --detach-psr-fpn

### --detach-reg-fpn (config.py:567, model.py:550)
- REGRESSION gradients blocked from FPN. Classification gradients STILL flow.
- Rationale: regression gradient shock from freshly reinit'd head encountering GT boxes

### --detach-psr-fpn (config.py:573, model.py:1957-1960/2010-2014)
- PSR gradients blocked from FPN entirely (both sequence and non-sequence paths)
- Prevents PSR loss spikes from corrupting detection features through backbone

### Both default to False. Stage manager auto-enables both when --reinit-heads is active.

---

## 13. Dead / Unused Code Paths

### [HIGH] ROIDetector (roi_detector.py, 379 lines)
The entire `ROIDetector`, `AnchorFreeLocalizer`, and `ROIStateClassifier` classes are NEVER instantiated by `POPWMultiTaskModel`. No `use_roi_detector` flag, no import, no constructor parameter. 379 lines of completely dead code.

### [HIGH] PSRTransitionPredictor (psr_transition.py, 304 lines)
The entire `PSRTransitionPredictor`, `MonotonicDecoder`, and `build_transition_targets` functions are NEVER imported or used by the main model. The model uses `PSRHead` from model.py. 304 lines of dead code.

### [HIGH] K400VideoStream (video_stream.py, 361 lines)
The entire `K400VideoStream`, `_Fallback3DStream`, `_SlowFastWrapper` are NEVER imported or instantiated by `POPWMultiTaskModel`. The model uses `VideoMAEStream` from model.py. Has a CLI `main()` for offline extraction but is disconnected from the training pipeline. 361 lines of dead code.

### [MEDIUM] VideoMAEStream.unfreeze (model.py lines 953-960)
Exists but is never called. Stream frozen at init, `unfreeze()` returns param groups for fine-tuning but no stage/scheduler invokes it.

### [LOW] Unused variables in pseudo-kp branch (model.py lines 1865-1920)
- `top_cls` (line 1869): assigned but never read (acknowledged `# noqa: F841`)
- `scale_kp` (line 1875): assigned but never read (acknowledged `# noqa: F841`)
- `x0` (line 1886): computed but never used (NO `# noqa` annotation -- unintentional)

### [LOW] industriale_model.py (7 lines)
Backward-compat alias only. Intentional.

### [LOW] PSR debug `print()` statements (model.py:1529-1553, 1984-1999)
`print()` calls with `[PSR_DEBUG]` prefix at steps {0,1,10,100,200,500}. Produces stdout noise. Should use `logger.info()`.

---

## 14. Cross-Cutting Issues

### ConvNeXt channel count comments incorrect for ResNet
Inline comments reference ResNet channel counts when ConvNeXt-Tiny is the default:
- model.py:1409: `# 3072` should be `1152` (384+768) for ConvNeXt
- model.py:413-415: FPN forward comments show ResNet channels
- These are misleading but do not affect execution since code is parameterized correctly.

### HeadPoseHead vs GeometryAwareHeadPose dual-path
Two implementations: legacy (no init, raw 9-DoF, MSE loss) and geo-aware (proper init, 6D rotation, geodesic loss). Guarded by `C.USE_GEO_HEAD_POSE`. The legacy path is the default. This dual-path adds maintenance burden -- bugs fixed in one path are not automatically fixed in the other.

### Detection head pi-prior triplicate
Three different pi values exist: 0.03 (fresh init), 0.01 (reinit-heads), and 0.01 (ROI detector, which is dead code). Only two are live, and they differ.

### Total dead code volume
Three complete model files totaling ~1044 lines are NEVER used:
- roi_detector.py: 379 lines
- psr_transition.py: 304 lines  
- video_stream.py: 361 lines
Plus the 7-line alias shim, and several small dead-code fragments in model.py itself. This is roughly 48% of the total `models/` directory codebase that is actively dead.
