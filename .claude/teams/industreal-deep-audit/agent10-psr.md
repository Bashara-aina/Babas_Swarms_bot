# Agent 10/20 — PSR (Phase Space Reconstruction) Head Audit

## 1. PSR Architecture

### Dimension Flow
```
FPN P3 [B, 256, H/8, W/8]  --+
FPN P4 [B, 256, H/16, W/16] --+-- concat(768) -> MLP -> [B, 256] -> Transformer -> Heads
FPN P5 [B, 256, H/32, W/32] --+
```

- **Input**: 256ch FPN P3+P4+P5 (3 scales), each GAP-pooled -> concat = **768-D**
- **Per-frame MLP**: `Linear(768, 512)` -> LayerNorm -> GELU -> Dropout(0.1) -> `Linear(512, 256)` -> LayerNorm
- **Causal Transformer**: 3 layers, 4 heads, d_model=256, FFN=1024, pre-norm, GELU, dropout=0.2
- **Per-component heads**: 11 separate `Sequential(Linear(256,64), GELU, Dropout(0.06), Linear(64,1))`
- **Output**: `[B, 12]` where `[..., :11]` = component logits, `[..., 11:]` = confidence (max sigmoid)

### Key Hyperparameters
| Parameter | Value | Notes |
|-----------|-------|-------|
| `PSR_SEQUENCE_LENGTH` | **2** | Causal context window = 2 frames |
| `PSR_SEQ_EVERY_N_BATCHES` | **2** | Every 2nd batch is a sequence batch |
| `PSR_FOCAL_GAMMA` | 1.0 | Per-frame focal (was 1.5, reduced) |
| `PSR_FOCAL_ALPHA` | 0.25 | Focal alpha |
| `PSR_WEIGHT` | 10.0 | Multiplier before Kendall weighting |
| `PSR_SEQ_LOSS_SCALE` | 1.5 | Sequence batch loss multiplier |
| `PSR_LOSS_CAP` | 20.0 | Smooth cap on PSR loss |
| `USE_PSR_TRANSITION` | **False** | Transition objective DISABLED |
| `USE_PSR_ORDER_PRIOR` | **False** | Procedure-order prior DISABLED |

---

## 2. PSR_DEBUG Output Analysis

Two debug paths exist in `model.py`:

### Non-sequence path (line 1542-1553)
Prints at steps 0, 1, 10, 100, 200, 500:
```
[PSR_DEBUG step=N] pre_linear:  mean=... std=... min=... max=...
[PSR_DEBUG step=N] post_linear64: mean=... std=... min=... max=...
[PSR_DEBUG step=N] post_gelu:   mean=... std=... min=... max=...
[PSR_DEBUG step=N] post_dropout: mean=... std=... min=... max=...
```
Measures **output_heads[0]** on the transformer output. Key indicators:
- **pre_linear std < 0.01**: Transformer output has collapsed -> dead gradient
- **post_gelu all negative**: Bias init of Linear(256,64) at +0.1 should prevent this
- **post_linear64 near-zero variance**: Output head first layer is saturated

### Sequence path (line 1991-1999)
Same structure but for the flattened `[BT, 256]` tensor in sequence mode:
```
[PSR_DEBUG_seq step=N] pre_linear:  mean=... std=...
[PSR_DEBUG_seq step=N] post_linear64: mean=... std=...
[PSR_DEBUG_seq step=N] post_gelu:   mean=... std=...
```

### Liveness output (losses.py ~line 1478)
```
[LIVENESS step=N] psr=X.XXe-X DEAD/ALIVE | psr_c=min/max/mean | mem=X.XX/X.XXG
```
- DEAD if PSR loss < 10 * 1e-4 (floor) or non-finite
- The per-component breakdown `psr_c=min/max/mean` reveals which components are getting signal

---

## 3. Gradient Flow: detach-psr-fpn

### Current behavior (DETACH_PSR_FPN=False by default):
- PSR gradients flow into shared FPN features -> backprop into backbone
- **Risk**: PSR loss spikes (~23.9 at step ~850) corrupt detection features

### When DETACH_PSR_FPN=True (line 1957-1960):
- **Sequence path**: `p3_t.detach()`, `p4_t.detach()`, `p5_t.detach()` at each time step
- **Non-sequence path**: `psr_pyramid = {k: v.detach() for k in ('p3','p4','p5')}` (line 2011)
- **Effect**: PSR head learns from fixed FPN features, cannot improve its own feature extractor

### Seq-batch gradient isolation (train.py lines 1121-1131):
- After `scaler.scale(loss_seq).backward()`:
  - `model.backbone` gradients explicitly zeroed
  - `model.fpn` gradients explicitly zeroed
- Only PSR head + PSR transformer weights update on seq steps

### Key finding:
PSR has **TWO independent gradient isolation mechanisms**: (a) DETACH_PSR_FPN at the feature level, and (b) post-hoc backbone/FPN grad zeroing on seq batches. When both are active, PSR can ONLY update its own parameters -- no shared feature improvement possible from PSR signal.

---

## 4. PSR Loss Computation

### Per-frame path (dim==2, both USE_PSR_TRANSITION=True and False):
- When `USE_PSR_TRANSITION=True` and dim==2: **loss_psr = zero** (line 1317) -- skip entirely
- When `USE_PSR_TRANSITION=False`: `binary_focal_loss(psr_logits, psr_labels)` from losses.py
  - Logits clamped to [-8, 8] before sigmoid (gradient-safe range)
  - -1 labels (error states) masked out
  - `per_component_alpha` from prevalence (clamped min=0.1)
  - `comp_weights` (inverse prevalence, up to 5.03x for rare components)
  - p_t clamped to [1e-6, 1-1e-6] for numerical stability

### Sequence path (dim==3):
- When `USE_PSR_TRANSITION=True`: converts fill-forward labels to Gaussian-smeared targets (sigma=3.0)
- When `USE_PSR_TRANSITION=False`: same per-frame focal loss applied to [BT, 11] flattened view

### Sensitivity penalty (per-frame only, dim==2, batch > 1):
- `-log(mean(per-component-std))` penalizes constant output
- Weighted by `PSR_SENSITIVITY_WEIGHT=0.01`
- At std=0.0: loss contribution ~0.046 (very weak deterrent for collapse)

### Temporal smooth loss (sequence only, dim==3):
- Signed mean temporal diff for preds (tanh) vs labels (raw)
- MSE between change rates
- Weighted by `PSR_TEMPORAL_SMOOTH_WEIGHT=0.05`

### The "seq=1" flag (train.py line 1145):
```
f"psr={loss_dict_seq.get('psr', 0.0):.3f} seq=1"
```
This is a **progress-bar marker** indicating the current step is a sequence batch -- NOT a PSR parameter. It means "seq_batch=1". When USE_PSR_TRANSITION is enabled, the per-frame batches (seq=0) show `psr=0.000` because PSR loss is skipped on those batches.

---

## 5. Numerical Stability

### Clamp chain (binary_focal_loss in losses.py):
1. `logits.clamp(-8, 8)` -- prevents sigmoid saturation
2. `p_t.clamp(1e-6, 1-1e-6)` -- prevents log(0)=NaN in focal weight
3. -1 labels masked: p_t=1.0, ce=0, loss=0 for those entries
4. per_component_alpha clamped to `max=1.0`

### Loss NaN guards (MultiTaskLoss.forward):
1. **Pre-Kendall**: non-finite loss_psr -> replaced with 1e-4 fallback
2. **Smooth cap**: `PSR_LOSS_CAP=20.0` with differentiable `cap*(1+log(x/cap))` for x>cap
3. **Post-smooth-cap double check**: non-finite loss_psr -> 1e-4 sentinel with `[PSR_NAN]` warning
4. **Kendall total NaN guard**: rebuild from finite components if total is non-finite

### Critical: Silent NaN replacement
PSR loss fires `[PSR_NAN]` warnings and substitutes 1e-4 when non-finite. If this fires frequently (>1% of batches), it means PSR produces NaN signals regularly and is learning from surrogate values. The diagnostic block (line 859-872 in losses.py) prints when loss < 1e-4 or non-finite:
```
[PSR_DIAG] loss=... finite=... | shape=... total=... valid=... neg1=... |
logits[min/max/mean]=... | target counts: zeros=... ones=... neg1=...
```

---

## 6. Sequence Length Handling

| Mode | Sequence Length | Gradients to | Effect |
|------|----------------|--------------|--------|
| Per-frame (T=1) | 1 | PSR head + backbone (unless detached) | No temporal signal |
| Sequence (T=2) | 2 seq * every 2nd batch | PSR head only (backbone/FPN zeroed) | Limited context |
| Cache (eval) | Up to 32 | N/A (eval) | Reasonable eval context |

### Key problem: T=2 is too short
A causal transformer with T=2 sees only the current frame and the immediately preceding frame. For assembly transitions spanning 5+ frames, this is insufficient temporal context. Combined with sequence batches only every 2nd step, the PSR head gets temporal signal on only ~50% of training steps.

### Frozen during stages 1-2
In staged training (epochs 1-5 stage 1, 6-15 stage 2), PSR is completely frozen -- zero training for 15 epochs. Stage 3 starts at epoch 16 with `PSR_WARMUP_EPOCHS=0` (config explicit), meaning no warmup ramp for PSR activation. The head goes from frozen to full training instantly.

---

## 7. PSR F1 Score Calculation

### Training F1 (psr_transition.py lines 286-294, used in compute_loss):
- Raw transition detection: compares 0->1 flips in predicted vs true binary logits
- Uses sigmoid > 0.3 threshold, NOT MonotonicDecoder
- Eager metric: per-batch, not comparable to evaluation F1
- **This metric** is what appears in training logs (not the eval metric)

### Evaluation F1 (evaluate.py lines 302-365, compute_psr_metrics):
- Per-recording: decodes logits through MonotonicDecoder -> monotone state sequence
- Computes 0->1 transition frames from both pred and GT
- **Bi-directional greedy match** with +/-tolerance (3 or 5 frames)
- Produces: `psr_overall_f1`, `psr_f1_at_t`, `psr_pos`, `psr_edit_score`
- `psr_f1_at_t` = the real benchmark metric (symmetric F1 at +/-3 tolerance)
- `psr_overall_f1` = macro across 11 components (threshold-based, NOT transition-based)

### Why psr_f1=0.0 appears:
The comment at train.py line 3964:
```
# [FIX 2026-05-31] psr_macro_f1 = psr_overall_f1 = 0.0 (all-ones predictions).
# Use psr_f1_at_t (+/-3-frame F1, the actual benchmark metric) for combined metric.
```

**Root cause**: The model predicts **all-ones** for all 11 components. This gives ~95% per-frame accuracy (components placed 95% of time) but causes:
- GT has a transition at some frame t (0->1)
- Predicted states are all 1s -> NO predicted transitions
- TP = 0, FN = all transitions, FP = 0
- F1 = 0.0 (both overall and at-t)

The fix at line 4021 switched the combined metric from `psr_macro_f1` to `psr_f1_at_t`, but the checkpoint still records `psr_macro_f1=0.0`.

---

## 8. Is the PSR Head Actually Converging?

### Evidence of non-convergence:
1. **psr_f1=0.0 in best checkpoint** -- model predicts all-ones, zero temporal learning
2. **PSR loss floor**: loss consistently at ~0.0001 (the NaN replacement sentinel value, or near-focal-saturation floor)
3. **Per-component alpha starvation**: component 0 (base plate, 95% prevalence) gets alpha=0.1 -> minimal gradient
4. **output_heads bias initialization**: `nn.init.constant_(head[0].bias, 0.1)` (line 1505) pushes GELU into linear regime -- intentional but may mask collapse

### Positive signs:
1. **Reinit heads path** (line 2347-2394): PSR transformer reinit'd with xavier_uniform, output_heads reinit'd with std=0.02. Prevents sigmoid saturation from extreme transformer outputs (measured std~86 with stale checkpoint + reinit'd MLP).
2. **Per-component loss weights** (PSR_COMP_WEIGHTS): component 4 gets 5.03x, component 10 gets 4.61x -- rare components get more gradient.
3. **PSR_WARMUP_INIT_MULT=2.0**: Precision multiplier starts at 2x and decays to 1x over first N steps.

### What would help convergence:
- Enable `USE_PSR_TRANSITION=True` -- Gaussian-smeared transition targets force changepoint learning
- Enable `USE_PSR_ORDER_PRIOR=True` -- procedure-order constraints via MonotonicDecoder
- Increase `PSR_SEQUENCE_LENGTH` from 2 to 4+ (requires more GPU memory or gradient checkpointing)
- Increase `PSR_SENSITIVITY_WEIGHT` from 0.01 to 0.1+ to more strongly penalize constant output

---

## 9. Dead Gradient Risk in PSR Head

### Risk factors (ordered by severity):

1. **Per-frame static labels dominate signal** -- 95% fill-forward labels make constant prediction locally optimal. Focal loss with gamma=1.0 down-weights easy examples, but the transition boundary frames (where predicted probability != label) are only ~5% of the data.

2. **Transformer output collapse** -- If the causal transformer produces near-constant output across all positions, the per-component heads see identical input for every frame. The [AUDIT] bias +0.1 on Linear(256,64) helps but doesn't guarantee diversity.

3. **Sigmoid saturation at output heads** -- With the original checkpoint (before reinit), transformer output std was ~86. This produces extreme logits that saturate sigmoid, making `(1-p_t)^gamma ~= 0` for both positive and negative examples. The reinit path fixes this with xavier_uniform transformer init and std=0.02 output head init.

4. **NaN sentinel replacement** -- If `[PSR_NAN]` fires, the loss is silently replaced with 1e-4 which provides zero useful gradient. The model learns nothing on that batch. If this affects >10% of batches, PSR is effectively dead.

5. **Gradient clipping** -- `GRAD_CLIP_NORM` applies globally. If activity/detection heads produce large gradients, PSR's smaller gradients get clipped to near-zero in the global norm scaling.

6. **Kendall suppression** -- When `KENDALL_LOG_VAR_MAX_PSR=0.0`, PSR precision is capped at exp(0)=1.0. Activity precision can reach exp(4)=54.6x. The effective gradient ratio is ~1:55 PSR:activity before loss magnitudes are even considered.

7. **STAGED_TRAINING freeze** -- 15 epochs of zero PSR training. When Stage 3 activates, the head must learn from scratch while competing with established heads for Kendall precision.

### Currently fixed issues:
- [FIX 2026-06-15] Transformer reinit'd during --reinit-heads (prevents sigmoid saturation)
- [FIX 2026-06-15] Per-component alpha clamped to min=0.1 (prevents component starvation)
- [FIX 2026-06-15] Per-component loss weights applied (rare components upweighted)
- [FIX Bug #11] Alpha_c clamp prevents component 0 starvation (was 0.02, now min 0.1)

---

## 10. Interaction Between PSR and Temporal Bank (FeatureBank)

The FeatureBank (`model.py` line 1126-1228) is used by the **ActivityHead**, NOT the PSR head.

### FeatureBank:
- **Consumer**: ActivityHead only (activity classifier gets history of T=8 projected features)
- **Window**: 8 frames, ring buffer keyed by (video_id, camera_view)
- **Detach**: `FEATURE_BANK_DETACH=True` by default (bank entries stored as `detach().clone()`)

### PSR temporal mechanism:
- PSR has its **own** temporal cache (`PSRHead._cache`) for inference only (lines 1508-1509, 1576-1610)
- During training, PSR gets temporal context from either:
  - **Seq batches** (T=2, every 2nd step): the model receives [B, T, C, H, W] and the PSR forward uses causal transformer on T=2
  - **Per-frame batches**: T=1, transformer is a no-op, no temporal signal

### Interaction points:
1. **No direct PSR-FeatureBank connection**: PSR does not read from or write to FeatureBank
2. **Shared FPN features**: Both PSR and ActivityHead consume FPN pyramid. When PSR gradients flow back through FPN (DETACH_PSR_FPN=False), they can corrupt the features that ActivityHead's FeatureBank reads. This was the original motivation for DETACH_PSR_FPN.
3. **Seq-batch gradient isolation**: On seq batches, backbone and FPN gradients are zeroed specifically to prevent PSR from corrupting features used by ActivityHead's FeatureBank.

### Key finding:
PSR and temporal bank are functionally isolated. PSR learns from the same FPN features but does not contribute to or consume from the FeatureBank. The only interaction is negative: PSR gradients can corrupt FPN features for the bank.

---

## 11. Memory Usage of PSR (Sequence Accumulation)

### Training memory (per seq batch, T=2):
- Input: [B, T, C, H, W] = [4, 2, 3, 1280, 720] = ~70 MB (FP16)
- FPN features at P3: [4*2, 256, 160, 90] = ~55 MB
- Transformer: 3 layers x (d_model=256, FFN=1024) -> ~3.5M params
- Output heads: 11 x (256*64 + 64) = ~180K params
- **Total PSR params**: ~3.7M (negligible vs backbone ~25M)

### Runtime memory (inference cache):
- Per (video, camera_view): seq of up to 32 frames x 256-D features = 32 KB
- For 10 concurrent sequences: 320 KB -- negligible

### With gradient checkpointing:
- Does NOT checkpoint PSR layers specifically; model-level checkpointing saves activation memory for the full forward pass
- PSR_SEQUENCE_LENGTH=2 fits within the ~2.5-3 GB budget (seq batches skipped GradScaler for memory)

### Memory risk:
When `USE_PSR_TRANSITION=True` and `build_transition_targets()` runs, it creates a [B, T, 11] Gaussian target tensor and runs a triple loop (components x batch x frames). For extreme sequence lengths (T>64) this could be slow but memory impact is small.

---

## 12. Root Causes for psr_f1=0.0 in Best Checkpoint

### PRIMARY ROOT CAUSE: Constant-output trivial solution
The per-frame BCE/focal loss on ~95% static fill-forward labels admits a trivial optimum: predict all-ones. This scores ~95% per-frame accuracy but captures zero temporal information. The transition-event F1 (the actual benchmark metric) is 0.0 because all-ones predictions produce no transition events to match.

### SECONDARY CAUSES (ordered by impact):

1. **USE_PSR_TRANSITION=False** -- The most impactful single fix. Transition targets force changepoint learning and prevent the constant-output collapse. Without this, the head has no reason to predict 0s.

2. **PSR_SEQUENCE_LENGTH=2** -- T=2 gives the transformer virtually no temporal context. The causal mask means position 0 sees only itself, position 1 sees positions 0-1. Learning transition timing from 2-frame context is nearly impossible.

3. **STAGED_TRAINING starvation** -- 15 frozen epochs followed by instant full activation (PSR_WARMUP_EPOCHS=0). The head must compete with established detection/activity heads from step 1 of Stage 3.

4. **Gradient imbalance** -- PSR loss (~0.0001-0.01) vs activity loss (~0.5-5.0) means PSR contributes ~0.01-2% of total gradient even with PSR_WEIGHT=10. The Kendall system learns to suppress PSR further.

5. **Sensitivity penalty too weak** -- `PSR_SENSITIVITY_WEIGHT=0.01` adds only ~0.046 loss when output is completely constant. This is insufficient to prevent collapse compared to the 95% per-frame accuracy reward.

6. **Per-component alpha still low for common components** -- Component 0 (95% prevalence) gets alpha_c=0.1. At focal gamma=1.0, a 99% confidence correct prediction contributes `0.1 * 0.01^1 * log(0.99) approx -0.00001` gradient. Essentially zero.

### Prescription for R2.5 (from config analysis):
Config already defines the fixes but they are not enabled:
- Set `USE_PSR_TRANSITION=True` (defined in config, line 629)
- Set `USE_PSR_ORDER_PRIOR=True` (defined in config, line 636)
- Increase `PSR_SEQUENCE_LENGTH` to 4+ with gradient checkpointing
- Increase `PSR_SENSITIVITY_WEIGHT` to 0.1+ to prevent constant-output solution
- Set `PSR_WARMUP_EPOCHS` to 3-5 for staged training (currently 0)
- Reduce `ACTIVITY_LOSS_WEIGHT` further (currently 0.2, PSR still dominated)

---

## Audit Summary Checklist

| Check | Status | Finding |
|-------|--------|---------|
| PSR architecture correct | PASS | 3-layer causal transformer, 11 per-component heads |
| Embedding dimensions | PASS | 768->512->256, d_model=256 in transformer |
| Gradient flow to backbone | CONDITIONAL | Detached when DETACH_PSR_FPN=True; zeroed on seq batches |
| PSR loss computation | PASS | Focal loss with multi-layer numerical safety |
| seq=1 training output | FALSE ALARM | Its a progress-bar marker, not a PSR parameter |
| tanh/sigmoid stability | WARN | [-8,8] clamp, [1e-6,1-1e-6] p_t clamp, NaN sentinel replacement |
| Sequence length handling | FAIL | T=2 is insufficient for transition learning |
| PSR F1 calculation | PASS | Correct transition-based metric; psr_f1_at_t is the real metric |
| PSR convergence | FAIL | All-ones prediction = F1=0.0 on transition events |
| Dead gradient risk | CRITICAL | Multiple overlapping mechanisms cause near-zero gradient |
| PSR-FeatureBank interaction | DECOUPLED | No direct connection; negative interaction via shared FPN |
| Memory usage | PASS | ~3.7M params, inference cache ~32KB per sequence |
| Reinit heads coverage | PASS | Transformer + output_heads + per_frame_mlp all reinitialized |
