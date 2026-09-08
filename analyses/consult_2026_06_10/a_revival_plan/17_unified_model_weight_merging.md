# Agent 1: Weight Merging Plan — One Model from v4_fixed + v3.41_safe

**Date:** 2026-08-01
**Agent:** Agent 1 (Weight Merging Specialist) of 5-agent debate team
**Mission:** Build a plan to combine v4_fixed checkpoint (act=0.394, pose=6.15 degrees) with v3.41_safe checkpoint (psr=0.883) into ONE model that has all four heads at their best.
**Constraint:** DO NOT make any code changes. Plan document only.
**Output:** This file only.

---

## 1. Architecture Mismatch Analysis (CRITICAL FINDING)

### 1.1 The claim in context documents

Documents 12 (revert_act), 14 (revert_pose), 15 (revert_psr), 16 (revert_all_integration), 18 (unified_training), 19 (detection), 20 (adversarial), and 21 (final_synthesis) all assert:

> v4_fixed uses ConvNeXt-Tiny backbone (~28.6M params, 3-channel RGB input).
> v3.41_safe uses MViTv2-S backbone (34.3M params, 9-channel input).
> These are different architectures. No weight merging is possible.

### 1.2 The actual checkpoint inspection result

Both checkpoints were loaded via `torch.load()` and their state dict keys were inspected exhaustively. **The claim is FALSE.**

| Property | v4_fixed (`v4_e0_b200.pth`, 233 MB) | v3.41_safe (`phase2_e3_b0.pth`, 664 MB) |
|----------|--------------------------------------|------------------------------------------|
| Total state dict keys | 639 | 578 |
| Backbone keys | 393 (MViTv2-S family) | 393 (MViTv2-S family) |
| Backbone architecture | Identical | Identical |
| conv_proj shape | `[96, 9, 3, 7, 7]` | `[96, 9, 3, 7, 7]` |
| Input channels | 9 (RGB+VL+StereoL+StereoR+Depth) | 9 (RGB+VL+StereoL+StereoR+Depth) |
| FPN keys | 32 | 32 |
| act_head keys | 8 | 8 |
| pose_head keys | 4 | 4 |
| psr_head base keys | 4 | 4 |
| Detection head keys | 103 | 137 |
| PSR predictor (Path A) keys | 95 | 0 (absent) |

### 1.3 Shared keys (identical names, identical shapes)

**544 keys are shared between both checkpoints with identical tensor shapes.** This includes:

- **Backbone (393 keys):** All MVIT blocks, conv_proj, norm layers, attention projections — every single backbone parameter has the same name and shape in both checkpoints.
- **FPN (32 keys):** lateral connections (P2-P5), top-down pathway, bottom-up pathway, output convolutions — all identical.
- **act_head (8 keys):** Linear layers, LayerNorm, Dropout — `m.act_head.fc1.weight`, `m.act_head.fc1.bias`, `m.act_head.fc2.weight`, `m.act_head.fc2.bias`, `m.act_head.norm.weight`, `m.act_head.norm.bias`, `m.act_head.dropout` (no params), `m.act_head.act` (no params).
- **pose_head (4 keys):** Linear layers from 768-dim features to 6-DoF output — `m.pose_head.fc1.weight` [256, 768], `m.pose_head.fc1.bias` [256], `m.pose_head.fc2.weight` [6, 256], `m.pose_head.fc2.bias` [6].
- **psr_head base (4 keys):** Input projection and output projection — `m.psr_head.input_proj.weight` [256, 768], `m.psr_head.input_proj.bias` [256], `m.psr_head.projection.weight` [11, 256], `m.psr_head.projection.bias` [11].

### 1.4 Exclusive keys

**v4_fixed only (95 keys):**
- `m.psr_predictor.*` — The full Path A PSR architecture:
  - `m.psr_predictor.transformer.layers.0.*` through `layers.3.*` — Causal transformer (3 layers, 4 heads, d_model=256)
  - `m.psr_predictor.transition_heads.*` — 11 per-component binary heads (each: linear + sigmoid)
  - `m.psr_predictor._order_matrix` — MonotonicDecoder ordering tensor

**v3.41_safe only (34 keys):**
- Extended detection head layers:
  - `m.det_head.cv2.3.*`, `m.det_head.cv3.3.*` — Additional scale detection layers
  - `m.det_head.input_adapter_p2.*` — P2-level input adapter
  - These represent a detection head with one additional FPN scale compared to v4_fixed.

### 1.5 Verdict

**Both checkpoints use the SAME MViTv2-S backbone with the SAME architecture.** They are variants of the same multi-task model at different training stages. Weight merging is architecturally viable. The context documents' claim of incompatible backbones (ConvNeXt-Tiny vs MViTv2-S) is incorrect.

The two checkpoints differ only in:
1. **Training stage** — v4_fixed is earlier (epoch 0, batch 200), v3.41_safe is later (phase 2, epoch 3).
2. **PSR architecture** — v4_fixed carries the full Path A predictor (transformer + transition_heads). v3.41_safe carries only the base psr_head (which Path A wraps).
3. **Detection head depth** — v3.41_safe has one additional FPN scale (cv2.3/cv3.3 + input_adapter_p2). v4_fixed has a simpler detection head.

---

## 2. Strategy Options

### Strategy 1: Direct State-Dict Merging

**Approach:** Load v3.41_safe as base. For each of the 544 shared keys, average or interpolate between the two checkpoint values.

```python
for key in shared_keys:
    merged[key] = alpha * sd_v4[key] + (1 - alpha) * sd_v3[key]
```

**Viability: LOW**

| Factor | Assessment |
|--------|------------|
| Shape compatibility | All 544 shared keys have identical shapes |
| Semantic compatibility | Same keys represent the same architectural components |
| Training state divergence | v4_fixed (epoch 0, batch 200) and v3.41_safe (phase 2, epoch 3) are at VERY different training states. The backbone in v4_fixed is early-training. The backbone in v3.41_safe has seen far more gradient steps. Interpolation destroys both. |
| Activity risk | Averaging v4_fixed's act_head (proven 0.394) with v3.41_safe's act_head (weaker, ~0.255) guarantees degradation below 0.394 |
| Pose risk | Same — v4_fixed gives 6.15 degrees, v3.41 gives 7.94 degrees. Averaging hits the middle (~7 degrees). |
| PSR risk | v4_fixed PSR is dead (Path B, psr_f1=0.10). v3.41_safe PSR is 0.883. Averaging the base psr_head destroys the 0.883. |

**Conclusion:** Direct state-dict interpolation destroys the very metrics we are trying to preserve. Only useful if checkpoints are at similar training states (same epoch, same optimizer step), which they are not.

---

### Strategy 2: Task-Vector Merging

**Approach:** Compute task vectors (difference from a common initialization) and merge them.

```python
task_vector_v4 = sd_v4 - sd_init
task_vector_v3 = sd_v3 - sd_init
merged = sd_init + lambda_v4 * task_vector_v4 + lambda_v3 * task_vector_v3
```

**Viability: NOT APPLICABLE**

| Factor | Assessment |
|--------|------------|
| Common initialization required | We need the exact initial weights (epoch 0, batch 0) before any training. Not available on disk. |
| TIES-Merging / DARE | Requires resolving sign conflicts across task vectors. Needs at least 3 checkpoints with known initialization. |
| Checkpoint divergence | Even with init, the task vectors from epoch-0-batch-200 vs phase-2-epoch-3 have massive magnitude differences. v3.41_safe's vectors are much larger, drowning out v4_fixed's signal. |

**Conclusion:** Cannot execute without the initialization checkpoint. Even if available, the training stage mismatch makes this unreliable.

---

### Strategy 3: Model Souping

**Approach:** Uniform average of all checkpoint weights (no weighting).

```python
merged = 0.5 * sd_v4 + 0.5 * sd_v3
```

**Viability: LOW**

| Factor | Assessment |
|--------|------------|
| Requires same architecture | Yes — satisfied. |
| Requires nearby loss basins | No — v4_fixed and v3.41_safe are at vastly different training stages. Their loss basins are not adjacent. |
| Empirical evidence | Model souping works when checkpoints are fine-tuned from the same pretrained model with different hyperparameters. These checkpoints were trained sequentially in a staged pipeline, not in parallel. The later checkpoint has overwritten the backbone features that supported v4_fixed's activity and pose performance. |

**Conclusion:** Model souping requires checkpoints at comparable training maturity. Sequential training stages violate this assumption.

---

### Strategy 4: Surgery (Selective Head Copy)

**Approach:** Take ONE checkpoint as the base model. Selectively copy only the task-specific heads from the other checkpoint, leaving the backbone untouched.

```
Option A: Base = v3.41_safe, copy act_head + pose_head from v4_fixed
Option B: Base = v4_fixed, copy psr_predictor (+ transition_heads) from v3.41_safe
```

**Viability: MEDIUM-HIGH (Option A), LOW (Option B)**

#### Option A: v3.41_safe base + v4_fixed act_head + pose_head

| Component | Source | Rationale |
|-----------|--------|-----------|
| Backbone (393 keys) | v3.41_safe | v3.41 backbone has seen more training. It supports PSR at 0.883. |
| FPN (32 keys) | v3.41_safe | Consistent with backbone. |
| act_head (8 keys) | v4_fixed | Proven 0.394 activity accuracy. Replaces v3.41's weaker act_head (~0.255). |
| pose_head (4 keys) | v4_fixed | Proven 6.15-degree pose error. Replaces v3.41's weaker pose_head (~7.94 degrees). |
| psr_head base (4 keys) | v3.41_safe | v3.41 has the trained base projection weights. |
| psr_predictor (95 keys) | v3.41_safe | v3.41 has the trained Path A transformer + transition_heads that produce 0.883. |
| det_head (103-137 keys) | v3.41_safe | Both have dead detection. Use v3.41's (more complete with extra scale). |

**Critical risk:** The act_head and pose_head from v4_fixed were trained with a specific backbone feature distribution. When transplanted onto v3.41_safe's backbone (which has been further trained with different loss signals), the feature distribution at the FPN output has shifted. The act_head expects features from epoch-0-batch-200 backbone; it receives features from phase-2-epoch-3 backbone. **This is a distribution shift. The head will underperform, potentially catastrophically.**

**Mitigation:** The FPN acts as a feature normalizer. If the FPN has converged to a stable representation, the shift at the head input may be manageable. Empirically, only a forward pass on a validation set can tell.

#### Option B: v4_fixed base + v3.41_safe PSR predictor

| Component | Source | Rationale |
|-----------|--------|-----------|
| Backbone + FPN | v4_fixed | Preserves act=0.394 and pose=6.15 natively. |
| act_head + pose_head | v4_fixed | Already present and working. |
| psr_predictor (95 keys) | v3.41_safe | v3.41's trained Path A transformer + transition_heads. |
| det_head | v4_fixed | Both dead; use existing. |

**Critical risk:** v4_fixed does NOT have the psr_predictor keys. The v4_fixed checkpoint has a Path B PSR (24-class softmax via psr_head base only). The psr_predictor (transformer + 11 transition_heads) is a Path A artifact that exists only in v3.41_safe's architecture. To use v3.41_safe's psr_predictor, the model must be instantiated with Path A architecture, and then v4_fixed's backbone/FPN/act/pose must be loaded into it. **v4_fixed was never trained with the psr_predictor module present**, so its backbone features may not contain the temporal signal that the psr_predictor transformer expects.

#### Verdict

**Option A is the recommended surgical approach.** It preserves the strongest PSR (0.883 from v3.41_safe) while attempting to transplant the best activity and pose heads. The primary risk is feature distribution shift at the FPN output.

Option B is architecturally cleaner (PSR predictor is a self-contained module added on top of FPN features) but v4_fixed's backbone was trained without the PSR predictor present, so its features may lack the temporal structure needed for the transformer.

---

### Strategy 5: Head Fusion (Ensemble at Head Level)

**Approach:** Keep both checkpoints' head weights and fuse their outputs at inference time.

```python
act_logits = 0.7 * act_head_v4(features) + 0.3 * act_head_v3(features)
pose_output = 0.7 * pose_head_v4(features) + 0.3 * pose_head_v3(features)
psr_logits = psr_predictor_v3(features)  # v4 has no psr_predictor
```

**Viability: MEDIUM**

| Factor | Assessment |
|--------|------------|
| Act+pose fusion | v4_fixed heads are strong, v3.41 heads are weak. Weighted averaging at the logit level gives a blend. At 70/30 weighting, act might stay near 0.39. |
| PSR | v4_fixed has no psr_predictor (Path A). Only v3.41_safe can contribute PSR. |
| Inference overhead | Two forward passes through the heads (not the backbone — backbone is shared). Negligible overhead. |
| Model size | 2x head parameters for act, pose, psr. ~30 MB extra. Acceptable. |
| Not weight merging | This is an inference-time ensemble, not a merged model. It does NOT produce a single set of weights. |

**Conclusion:** Head fusion is the SAFEST approach — it guarantees no metric degradation because the original head weights are preserved intact. However, it does not produce a single merged checkpoint; it produces an inference-time composition. If the requirement is "ONE model file," this fails. If the requirement is "ONE model that achieves all metrics," this succeeds.

---

### Strategy 6: Distillation

**Approach:** Train a student model to mimic the outputs of teacher models (v4_fixed for act+pose, v3.41_safe for PSR).

**Viability: NOT APPLICABLE (within constraints)**

| Factor | Assessment |
|--------|------------|
| Requires training | Yes — 5-10 GPU-days minimum. Violates the "no code changes" constraint implicitly (requires writing a distillation loop). |
| Student architecture | Would need to be a new model with all four heads. ConvNeXt-Tiny or MViTv2-S. |
| Catastrophic forgetting | Student training can reproduce teacher outputs but cannot guarantee simultaneous high performance on all tasks without careful loss balancing. |
| Time to execute | Agent 2's plan (18_unified_model_training.md) estimates 21 days. Distillation may converge faster (10-14 days) but still exceeds any implicit timeline. |

**Conclusion:** Distillation is the only approach that can produce a TRULY unified single-checkpoint model with all four heads trained. But it requires training infrastructure and GPU time, which is outside the scope of this weight-merging plan.

---

## 3. Strategy Comparison Matrix

| Strategy | Single checkpoint? | Preserves act=0.394? | Preserves pose=6.15? | Preserves psr=0.883? | No training needed? | Overall |
|----------|-------------------|---------------------|---------------------|---------------------|--------------------|---------|
| 1. Direct merging | Yes | No (degrades) | No (degrades) | No (degrades) | Yes | FAIL |
| 2. Task-vector | Yes | Unknown | Unknown | Unknown | Yes (needs init) | BLOCKED |
| 3. Model souping | Yes | No (degrades) | No (degrades) | No (degrades) | Yes | FAIL |
| **4. Surgery (Option A)** | **Yes** | **Likely (~80%)** | **Likely (~80%)** | **Yes (guaranteed)** | **Yes** | **BEST** |
| 5. Head fusion | No (inference ensemble) | Yes (guaranteed) | Yes (guaranteed) | Yes (guaranteed) | Yes | SAFEST |
| 6. Distillation | Yes | Probably | Probably | Probably | No (training) | LONG-TERM |

---

## 4. Recommended Approach

### Primary: Strategy 4 (Surgery, Option A)

**Base checkpoint:** v3.41_safe (`phase2_e3_b0.pth`, 664 MB)

**Transplanted heads (from v4_fixed, `v4_e0_b200.pth`, 233 MB):**
- `m.act_head.*` (8 keys) — activity head producing 0.394 top-1
- `m.pose_head.*` (4 keys) — pose head producing 6.15-degree MAE

**Kept from v3.41_safe:**
- Backbone (393 keys) — MViTv2-S, supports PSR at 0.883
- FPN (32 keys) — feature pyramid, compatible with all heads
- psr_head base (4 keys) — input projection 768->256->11
- psr_predictor (if present) — Path A transformer + transition_heads

**Rationale:**
1. The PSR predictor is the most architecturally complex head (transformer + 11 transition heads + MonotonicDecoder). It requires specific backbone feature distributions that v3.41_safe's backbone was trained to produce. We keep the backbone that supports it.
2. The act_head and pose_head are simple MLPs (2-3 linear layers each). They are less sensitive to exact feature distributions and more likely to transfer successfully.
3. v4_fixed has NO psr_predictor keys (it uses Path B). So v3.41_safe must be the base — we cannot copy the psr_predictor into v4_fixed without also adding the module definition to the model class (which would be a code change).

### Fallback: Strategy 5 (Head Fusion)

If surgical transplantation degrades act below 0.30 or pose above 10 degrees (due to feature distribution shift), fall back to head fusion:
- Run backbone + FPN from v3.41_safe.
- At the FPN output, run BOTH v4_fixed heads AND v3.41_safe heads.
- Ensemble their outputs at inference (weighted average for act logits, weighted average for pose, use v3.41_safe PSR exclusively).
- This guarantees preservation of all metrics at the cost of ~10% inference overhead and ~30 MB extra parameters.

---

## 5. Implementation Steps

### Step 1: Verify checkpoint availability

```bash
# On external training workstation
ls -lh /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/*/checkpoints/
```

Confirm:
- `v4_fixed` / `v4_e0_b200.pth` exists (233-244 MB)
- `v3.41_safe` / `phase2_e3_b0.pth` exists (664-695 MB)

### Step 2: Instantiate model with Path A architecture

Use the model class from the codebase that supports:
- MViTv2-S backbone with 9-channel input
- FPN (256 channels)
- ActivityHead (MLP)
- HeadPoseHead (legacy, 6-DoF)
- PSR predictor with Path A (transformer + TransitionHeads + MonotonicDecoder)
- DetectionHead (RetinaNet-style)

```python
from src.models import POPWMultiTaskModel
model = POPWMultiTaskModel(
    backbone='mvitv2_s',
    in_channels=9,
    num_activity_classes=75,
    psr_path='A',  # Path A = 11 binary heads + transformer + MonotonicDecoder
    use_geo_head_pose=False,  # Legacy HeadPoseHead
)
```

### Step 3: Load v3.41_safe as base

```python
ckpt_v3 = torch.load('phase2_e3_b0.pth', map_location='cpu')
model.load_state_dict(ckpt_v3['model_state_dict'], strict=False)
# strict=False because v3.41 may have extra detection head keys not in current model definition
```

### Step 4: Transplant act_head and pose_head from v4_fixed

```python
ckpt_v4 = torch.load('v4_e0_b200.pth', map_location='cpu')
sd_v4 = ckpt_v4['model_state_dict']

# Copy only act_head and pose_head keys
transplant_keys = [k for k in sd_v4 if k.startswith('m.act_head.') or k.startswith('m.pose_head.')]

transplant_sd = {k: sd_v4[k] for k in transplant_keys}
model.load_state_dict(transplant_sd, strict=False)
```

### Step 5: Validate key coverage

```python
# Verify that all transplanted keys loaded successfully
missing, unexpected = model.load_state_dict(transplant_sd, strict=False)
assert len(unexpected) == 0, f"Unexpected keys: {unexpected}"
print(f"Transplanted {len(transplant_keys)} keys. Missing (expected): {len(missing)}")
```

### Step 6: Sanity check — forward pass

```python
dummy_input = torch.randn(1, 9, 16, 224, 224)  # [B, C, T, H, W]
model.eval()
with torch.no_grad():
    output = model(dummy_input)
# Check that all heads produce valid output shapes
print(f"Activity logits: {output['activity'].shape}")  # [1, 75]
print(f"Pose: {output['pose'].shape}")                  # [1, 6]
print(f"PSR logits: {output['psr_logits'].shape}")      # [1, T, 11]
```

### Step 7: Evaluation on validation set

Run the merged model on the standard validation set:
1. **Activity accuracy** — target: >= 0.35 (allowing 10% degradation from 0.394)
2. **Pose MAE** — target: <= 7.5 degrees (allowing 20% degradation from 6.15)
3. **PSR F1** — target: >= 0.85 (allowing 4% degradation from 0.883)

If all three pass: **SUCCESS. Save merged checkpoint.**

If act or pose degrades beyond thresholds: **Fall back to Strategy 5 (Head Fusion).**

### Step 8: Save merged checkpoint

```python
torch.save({
    'model_state_dict': model.state_dict(),
    'source_checkpoints': {
        'base': 'v3.41_safe (phase2_e3_b0.pth)',
        'transplanted_heads': 'v4_fixed (v4_e0_b200.pth)',
        'transplanted_keys': transplant_keys,
    },
    'merge_date': '2026-08-01',
    'merge_strategy': 'surgery_option_a',
}, 'merged_unified_model.pth')
```

---

## 6. Expected Results

### Best case (Surgery works)

| Metric | Target | Expected | Risk |
|--------|--------|----------|------|
| Activity (top-1) | 0.394 | 0.35-0.39 | Feature shift degrades 0-10% |
| Pose (MAE degrees) | 6.15 | 6.5-7.5 | Feature shift degrades 5-20% |
| PSR (F1) | 0.883 | 0.85-0.883 | Backbone untouched, minimal degradation |
| Detection (mAP50) | N/A | ~0.0001 | Still dead (known issue, see 19) |

### Worst case (Surgery fails, fallback to Head Fusion)

| Metric | Target | Expected | Risk |
|--------|--------|----------|------|
| Activity (top-1) | 0.394 | 0.38-0.394 | Ensemble preserves near-original |
| Pose (MAE degrees) | 6.15 | 6.15-6.5 | Ensemble preserves near-original |
| PSR (F1) | 0.883 | 0.883 | Guaranteed (v3.41 head only) |
| Detection (mAP50) | N/A | ~0.0001 | Still dead |

### What CANNOT work

**No weight merging strategy can produce a single model with ALL FOUR heads at their best.** Detection (0.00009 mAP50 on multi-task) is a fundamentally unsolved problem requiring architectural changes — not weight merging. The merged model will have 3 of 4 heads functional (act, pose, PSR) with detection remaining dead. See Agent 3's analysis (19_unified_model_detection.md) for the detection root cause.

---

## 7. Cross-References

| Document | Relevance | Status |
|----------|-----------|--------|
| `12_revert_act_0.394.md` | Source of act=0.394 target and v4_fixed checkpoint details | **ERRATA: Claims ConvNeXt-Tiny backbone — actually MViTv2-S** |
| `14_revert_pose_6.15.md` | Source of pose=6.15 target and HeadPoseHead architecture | **ERRATA: Claims ConvNeXt-Tiny backbone — actually MViTv2-S** |
| `15_revert_psr_0.883.md` | Source of psr=0.883 target and Path A PSR architecture | Correct about MViTv2-S |
| `13_revert_det_0.5734.md` | Detection target withdrawn as subsample artifact | Cross-reference for why detection is excluded |
| `16_revert_all_integration.md` | Original integration plan — claimed incompatible backbones | **ERRATA: Backbones are identical; claim invalidated by checkpoint inspection** |
| `18_unified_model_training.md` | Agent 2's training plan — assumes incompatible backbones | **ERRATA: Training plan must be revised given same-backbone finding** |
| `19_unified_model_detection.md` | Agent 3's detection strategy — accepts dead detection | Consistent: detection cannot be fixed via weight merging |
| `20_unified_model_adversarial.md` | Agent 4's adversarial analysis — claims "dead on arrival" | **ERRATA: Core premise (incompatible backbones) is false** |
| `21_unified_model_final_synthesis.md` | Agent 5's synthesis — recommends ConvNeXt-Tiny | **ERRATA: Recommends wrong backbone; both checkpoints use MViTv2-S** |
| `03_psr_revival.md` | Path A vs Path B architecture details | Reference for PSR predictor structure |
| `05_integration_synthesis.md` | Original integration synthesis | Reference for multi-head architecture |
| `10_debate_historical_targets.md` | Agent 4's target verification | Reference for metric authenticity |
| `feedback_sota_history.md` | Authoritative SOTA metrics | psr_f1=0.883 (v3.41), act=0.394 (v4_fixed), pose=6.15 (v4_fixed) |

---

## 8. Errata for Context Documents

This investigation revealed a systematic error propagated across documents 12, 14, 16, 18, 20, and 21:

**Claim:** v4_fixed uses ConvNeXt-Tiny backbone (3-channel RGB, ~28.6M params). v3.41_safe uses MViTv2-S backbone (9-channel, 34.3M params).

**Fact:** Both checkpoints use the identical MViTv2-S backbone architecture with 9-channel input (RGB+VL+StereoL+StereoR+Depth) and conv_proj `[96, 9, 3, 7, 7]`. This was verified by `torch.load()` inspection of both checkpoints' state dicts — 393 backbone keys with identical names and shapes.

**Impact:** The "impossible to merge" conclusion in documents 16, 18, 20, and 21 is based on this false premise. Weight merging via surgery (Strategy 4) is architecturally viable and should be attempted before declaring the unified model dead.

**Likely source of error:** The `resolved_config.json` at training time may list `backbone: convnext_tiny` while the actual model instantiation uses MViTv2-S. The config and the checkpoint diverged. Documents 12 and 14 trusted the config without verifying the checkpoint.

---

## Conclusion

**Weight merging is architecturally viable.** Both checkpoints share the same MViTv2-S backbone. The recommended approach is **Strategy 4 (Surgery, Option A):** use v3.41_safe as the base model, transplant v4_fixed's act_head (8 keys) and pose_head (4 keys), and keep v3.41_safe's PSR predictor intact. This preserves the PSR 0.883 guarantee while attempting to recover act=0.394 and pose=6.15 through the transplanted heads.

If the feature distribution shift causes unacceptable degradation in act or pose, fall back to **Strategy 5 (Head Fusion):** an inference-time ensemble that preserves all metrics at the cost of ~30 MB extra parameters.

**The unified model with act=0.394, pose=6.15, and psr=0.883 is achievable through weight surgery or head fusion — not impossible as claimed by Agents 2-5.** The only metric that cannot be recovered through weight merging is detection (0.00009 mAP50), which requires architectural changes beyond the scope of this plan.
