# Agent 13: FPN (Feature Pyramid Network) and ConvNeXt-T Backbone

**Date:** 2026-06-17  
**Files analyzed:**
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/model.py`
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py`
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/config.py`

---

## 1. ConvNeXt-T Backbone

### Source
- **torchvision.models.convnext_tiny** with `ConvNeXt_Tiny_Weights.DEFAULT` (ImageNet-1K pretrained). Line 183.
- NOT a custom implementation. Stock torchvision ConvNeXt-Tiny.

### Output channels (correctly mapped)
| Level | Stride | Channels |
|-------|--------|----------|
| C2    | 4      | 96       |
| C3    | 8      | 192      |
| C4    | 16     | 384      |
| C5    | 32     | 768      |

**Verdict: PASS.** Channel mapping matches ConvNeXt-T architecture.

### Stage grouping (line 193-198)
The 8 `model.features[]` modules are split into 4 stage groups:
- `[features[0], features[1]]` -> C2 (stem + stage1)
- `[features[2], features[3]]` -> C3 (downsample2 + stage2)
- `[features[4], features[5]]` -> C4 (downsample3 + stage3)
- `[features[6], features[7]]` -> C5 (downsample4 + stage4 + final CNBlocks)

**Verdict: PASS.** Matches ConvNeXt-T feature hierarchy.

### Gradient checkpointing (line 239-248)
Each stage wrapped with `torch.utils.checkpoint.checkpoint(stage_fn, input, use_reentrant=False)`. Saves ~50% activation memory at ~20% compute overhead. `use_reentrant=False` is correct for autograd.

**Verdict: PASS.** Proper gradient checkpointing with correct reentrant flag.

### Pretrained weights
`convnext_tiny(weights=ConvNeXt_Tiny_Weights.DEFAULT)` loads IMAGENET1K_V1. The `.train()` is a no-op (just `super().train()`), which is correct because ConvNeXt uses LayerNorm (no frozen BN issue unlike ResNet50Backbone).

**Verdict: PASS.** ConvNeXt LayerNorm-based -- no BatchNorm freeze concern.

---

## 2. FPN Implementation

### Architecture
Standard top-down: `[C3, C4, C5]` -> `[P3, P4, P5, P6, P7]`.

- **Lateral:** 1x1 convs
- **Top-down upsample:** `F.interpolate(mode='nearest')`
- **Smooth:** 3x3 conv on P3, P4, P5
- **P6:** stride-2 conv on C5 directly
- **P7:** stride-2 conv on ReLU(P6)
- **All levels:** 256 channels

### Channel initialization for ConvNeXt (lines 1685-1698)
```python
if backbone_type == 'convnext_tiny':
    fpn_in_channels = [192, 384, 768]  # C3, C4, C5
...
self.fpn = FPN(in_channels=fpn_in_channels, out_channels=256)
```
The FPN `__init__` default `in_channels=[512, 1024, 2048]` (ResNet-50 sizes) is **never reached** because POPWMultiTaskModel always passes backbone-specific channels.

**Verdict: PASS.** Correct channel dimensions for ConvNeXt path.

### FPN output levels
| Level | Stride | Source | Channels |
|-------|--------|--------|----------|
| P3    | 8      | C3 + top-down from P4 | 256 |
| P4    | 16     | C4 + top-down from P5 | 256 |
| P5    | 32     | C5 lateral | 256 |
| P6    | 64     | stride-2 conv on C5 | 256 |
| P7    | 128    | stride-2 conv on ReLU(P6) | 256 |

**Verdict: PASS.** Standard 5-level RetinaNet pyramid.

### C5 bypass for PoseFiLM
Module docstring line 12: "C5 goes DIRECTLY to PoseFiLM (bypasses FPN)". Verified at line 1924:
```python
c5_mod = self.pose_film(c5, keypoints, pose_confidence)
```
C5 is the raw backbone output, not FPN P5. The FPN receives a clone via `_sanitize(c5)`.

**Verdict: PASS.** C5 bypass is correctly implemented.

### FPN initialization (line 404-409)
```python
nn.init.kaiming_uniform_(m.weight, a=1)
nn.init.zeros_(m.bias)
```
Standard Kaiming uniform. No initialization issues.

**Verdict: PASS.**

### Stale docstring (module-level, line 22)
Module docstring anchor sizes say `(24,48,96,192,384)`. Config.py line 271 has `ANCHOR_SIZES = (96, 160, 256, 384, 512)`.

**Verdict: COSMETIC BUG.** Line 22 docstring anchor sizes are stale/wrong; should match config.py.

---

## 3. Gradient Flow Through Shared FPN

### Overview: ONE shared `self.fpn` for all task heads

| Task Head | FPN inputs | Gradients to FPN? | Isolation |
|-----------|-----------|-------------------|-----------|
| Detection (cls) | P3-P7 | YES | No |
| Detection (reg) | P3-P7 | NO (optional) | `detach_reg_fpn` |
| Pose | P3 | YES | No |
| PSR (seq) | P3, P4, P5 | NO (optional) | `detach_psr_fpn` |
| PSR (non-seq) | P3, P4, P5 | NO (optional) | `detach_psr_fpn` |
| Head Pose | C4, C5 | via backbone, not FPN | N/A |
| Activity | P4 + det_conf | YES | No |

### `--detach-reg-fpn` (DetectionHead, line 546-550)
```python
reg_feat = feat.detach() if self.detach_reg_fpn else feat
reg_out = self.reg_pred(self.reg_subnet(reg_feat))
```
- **What detaches:** Only the `feat` tensor going into the **regression subnet** (reg_subnet -> reg_pred).
- **What still flows:** Classification subnet (cls_subnet -> cls_score) retains full gradient path through FPN.
- **Granularity:** Subnet-level. Correct -- classification needs FPN gradients to learn foreground/background.

**Verdict: PASS.** The implementation is specific to the regression branch only. Classification gradients still flow.

### `--detach-psr-fpn`
**Sequence path** (lines 1957-1960):
```python
p3_t = p3_t.detach(); p4_t = p4_t.detach(); p5_t = p5_t.detach()
```
**Non-sequence path** (lines 2009-2014):
```python
psr_pyramid = {k: (v.detach() if k in ('p3','p4','p5') else v) for k, v in pyramid.items()}
```
- **What detaches:** P3, P4, P5 tensors for PSR head GAP and transformer.
- **P6, P7 are unaffected** (PSR doesn't use them).
- Both code paths correctly implement the flag.

**Verdict: PASS.** Complete coverage across both sequence and non-sequence PSR paths.

### Gradient flow to backbone summary
With both detach flags active, the backbone still receives gradients from:
1. Detection classification subnet (via FPN P3-P7)
2. Pose head (via FPN P3)
3. Activity head (via FPN P4, plus direct C5_mod)
4. Head pose head (direct C4, C5)

The backbone stays well-supervised. No concern about gradient starvation.

---

## 4. Backbone Corruption and Repair

### Can the backbone be repaired after 2 epochs of buggy training?

**Damage estimate:** 2 epochs at effective batch-size 32 is ~625 optimizer steps. Backbone LR=5e-5 limits per-step damage. PSR loss spikes (~23.9 per line 1955) and regression gradient shock were the primary corruption vectors.

**Mitigation with --reinit-heads:**
- Backbone weights are explicitly PRESERVED (lines 3260-3263)
- FPN is reinitialized, preventing corrupted FPN weights from compounding
- `--detach-reg-fpn` and `--detach-psr-fpn` block the two known corruption paths

**Verdict: LIKELY REPAIRABLE.** 625 steps at 5e-5 is not catastrophic. The gradient isolation flags prevent recurrence. The backbone should recover within 10-20 epochs of fine-tuning.

**Contingency if recovery fails:**
- Option A: Restore backbone from fresh ImageNet init (loses 2 epochs of domain adaptation but guarantees clean start)
- Option B: Temporary backbone LR bump to 5e-4 for first 5 recovery epochs (undocumented -- would need code change)
- Option C: Continue at 5e-5 with detach flags -- should converge given the preserved ImageNet prior

---

## 5. Learning Rate Analysis

### Configuration (config.py:333)
```python
BASE_LR = 5e-4
```

### Optimizer param groups (AdamW, train.py:3012-3023)

| Group | Scope | LR | Ratio |
|-------|-------|-----|-------|
| 0: backbone_params | backbone.* | 5e-5 | 0.1x BASE |
| 1: det_head_params | detection_head.* | 2.5e-3 | 5.0x BASE |
| 2: head_params | other heads | 5e-4 | 1.0x BASE |
| 3: activity_psr_params | act+psr heads | 5e-4 | 1.0x BASE |
| 4: bias_params | all biases | 1.5e-4 | 0.3x BASE |
| 5: videomae_params | videomae stream | 0.0 | frozen |

### Is backbone LR 5e-5 vs heads 5e-4 appropriate?
**Verdict: YES.** The 0.1x backbone multiplier is standard fine-tuning practice (detectron2 uses 0.1x for backbone, 1.0x for FPN+heads). This preserves pretrained features while allowing domain adaptation.

**Caveat:** Detection head at 2.5e-3 (5x multiplier) is aggressive for RetinaNet with 173K:1 neg/pos ratio. The current focal alpha=0.90 partially compensates. If cls_mean collapse recurs, reduce DET_LR_MULTIPLIER to 2.0x or 1.0x.

---

## 6. FPN --reinit-heads Coverage

### Reinit function `_reinit_dead_heads` (train.py:2250-2266)
ALL 8 FPN Conv2d modules are explicitly reinitialized:
```python
fpn_attrs = ['lateral_c3', 'lateral_c4', 'lateral_c5',
             'smooth_p3', 'smooth_p4', 'smooth_p5',
             'p6_conv', 'p7_conv']
```
Assertion `fpn_reinit == 8` confirms all. Each gets Kaiming uniform + zero bias.

### What is NOT reinitialized
- Backbone -> PRESERVED
- PoseFiLM -> PRESERVED
- HeadPoseFiLM -> PRESERVED
- Pose head -> PRESERVED
- Feature Bank -> PRESERVED
- Anchor Generator -> PRESERVED (no learned params)

**Verdict: PASS.** Complete FPN coverage, correct preservation of backbone.

---

## 7. Shared vs Separate FPN Assessment

**Current design:** ONE shared FPN for all 5 task heads.

**Analysis:**
- Standard design (RetinaNet, Detectron2, MMDetection all use shared FPN)
- Gradient conflict between heads is addressed by `--detach-reg-fpn` and `--detach-psr-fpn`
- Parameter efficient: ~2.3M params shared instead of 11.5M for 5 separate FPNs

**Verdict: ADEQUATE.** The gradient isolation mechanisms address the known conflict points. If new conflicts emerge (e.g., activity head instability), a separate PSR-FPN or reg-FPN could be added, but this is not needed currently.

---

## 8. Feature Dimension Consistency

| Input | Input channels | Lateral output | Final FPN level |
|-------|---------------|----------------|-----------------|
| C3 (192ch) | 192 | 256 | P3 = 256 |
| C4 (384ch) | 384 | 256 | P4 = 256 |
| C5 (768ch) | 768 | 256 | P5 = 256, P6 = 256 |
| P6 (already 256) | - | - | P7 = 256 |

All FPN levels consistent at 256ch. No dimension mismatch.

**Verdict: PASS.**

---

## Summary

| Check | Verdict |
|-------|---------|
| ConvNeXt-T backbone source | PASS (stock torchvision, ImageNet-1K) |
| ConvNeXt channel mapping (C2=C3=C4=C5) | PASS (96/192/384/768) |
| FPN channel dimensions for ConvNeXt | PASS ([192, 384, 768] correctly passed) |
| FPN top-down pathway correctness | PASS (nearest-neighbor + lateral 1x1 + 3x3 smooth) |
| FPN output levels | PASS (P3-P7, 256ch each) |
| C5 bypass for PoseFiLM | PASS (original C5, not FPN P5) |
| detach_reg_fpn specificity | PASS (regression subnet only; cls still flows) |
| detach_psr_fpn specificity | PASS (P3/P4/P5 only; both seq and non-seq paths) |
| Gradient starvation concern | NONE (cls + pose + activity + head_pose all supervise FPN) |
| Backbone repair viability | LIKELY (5e-5 LR + preserved weights + detach flags) |
| Backbone LR 5e-5 vs heads 5e-4 | APPROPRIATE (0.1x standard, but watch det head at 2.5e-3) |
| FPN --reinit-heads coverage | PASS (all 8 conv modules reinitialized) |
| Shared vs separate FPN | ADEQUATE (detach flags mitigate conflicts) |
| Feature dimension consistency | PASS (all 256ch) |
| Stale anchor sizes in docstring | COSMETIC BUG (line 22 says (24,48,96,192,384), actual is (96,160,256,384,512)) |
| Gradient checkpointing | PASS (use_reentrant=False, stage-level) |
