# Agent 18/20: TMA (Temporal Memory Assembly) & Temporal Bank -- Audit Report

## Files Examined
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/model.py` -- FeatureBank (L1126-1228), TemporalConvBlock (L979-1027), ViTTemporalBlock (L1030-1120), ActivityHead (L1230-1390), POPWMultiTaskModel forward (L1805-2104)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py` -- Nan-reset handler (L1116, L1491), config hash (L2692)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/config.py` -- temporal flags (L100-103), presets, FEATURE_BANK_DETACH/SLOT_OVERWRITE (L649-652)

---

## 1. Architecture: What TMA and Temporal Bank Actually Are

### The naming mismatch (CRITICAL FINDING)

Config comment: `USE_TMA_CELL = True  # GRU-based Temporal Masked Attention Cell`

**There is no GRU in the temporal path.** Searching model.py for `GRU`/`gru`/`tma_cell`/`USE_TMA_CELL` yields zero matches in the activity/temporal code. The only `gru_hidden` references are in **PSRHead** (line 1454), which is a separate Transformer-based head.

**Use_TMA_CELL and USE_TEMPORAL_BANK are NEVER checked in model.py.** Both components (FeatureBank, TCN, ViT blocks) are ALWAYS instantiated and always run in the forward pass. The flags only affect the `update_dynamic_paths()` output directory naming in config.py (line 1295) and appear in the config hash (train.py line 2692).

### What actually exists (the real TMA)

| Component | File:Line | Purpose |
|-----------|-----------|---------|
| **FeatureBank** | model.py:1126 | Sliding-window ring buffer, stores `[f_{t-T+1}, ..., f_t]`, keyed by (video_id, camera_view). T=16 (FEATURE_BANK_WINDOW). |
| **TemporalConvBlock** | model.py:979 | Depthwise Conv1d (k=5) + pointwise 1x1 conv. Captures velocity/acceleration. LayerNorm + residual + DropPath. |
| **ViTTemporalBlock x2** | model.py:1030 | Learnable pos-embed + 8-head MHSA (d_k=64) + FFN (512->2048->512). CLS token for cross-attention pooling. DropPath 0.1/0.15. |
| **ActivityHead** | model.py:1230 | Orchestrates all three: FeatureBank->TCN->2xViT->CLS->classifier. |

The pipeline inside ActivityHead.forward():
```
proj_feat [B, 512]
    |
FeatureBank (always runs) --> bank_seq [B, 16, 512]
    |  (slot-1 overwrite: bank_seq[:,-1,:] = proj_feat)
    v
TCN (depthwise Conv1d k=5 + pointwise 1x1)
    |
    v
Concat [CLS; bank_seq] -> [B, 17, 512]
    |
    v
ViTTemporalBlock x2 (8-head MHSA, FFN)
    |
    v
CLS token -> classifier -> act_logits [B, 75]
```

---

## 2. FeatureBank: Detailed Mechanism

### Memory Structure
```python
self._bank: Dict[Tuple[str, str], List[torch.Tensor]] = {}
```
- Key: `(video_id, camera_view)` -- supports multi-video, multi-camera sequences.
- Value: Python list of `[512]` feature tensors, up to `window_size` (16) entries.
- **Per-entry memory**: 512 float32 = 2 KB per frame. Per-video bank: 16 x 2 KB = 32 KB.
- **Total worst-case**: ~448 MB if all ~7000 training videos x 2 cameras are live simultaneously, but in practice only batch-size videos are live per step.

### Update Mechanism (forward, line 1141)
1. **Batch mode** (input dim=3 [B, T, 512]): Returned as-is with NaN guard. Used during PSR sequence-mode batches.
2. **Per-frame mode** (input dim=2 [B, 512]): Each item is appended to its video's ring buffer. Oldest entry is popped when `len > window_size`.
3. **Padding**: If `len < window_size`, left-pads with copies of the current feature (or last valid feature).
4. **Slot -1 overwrite** (`FEATURE_BANK_SLOT_OVERWRITE=True`, default): After the bank returns `[B, T, 512]`, the live `proj_feat` overwrites `bank_seq[:, -1, :]` in ActivityHead (line 1358). This forces the last slot to always reflect the current frame.

### Initialization
- **ZERO-based**: Bank starts as an empty dict. On the first frame of a new video_id, `key not in self._bank` triggers initialization:
  - If `feat_is_valid`: bank is populated with `window_size` copies of the current feature.
  - If `feat_is_valid=False` (NaN): bank is populated with `window_size` copies of `torch.zeros_like(feat)`.

### Reset Triggers
FeatureBank IS reset during training:
- **NaN loss recovery** (train.py:1116, 1491): `model.feature_bank.reset()` when a loss or gradient is NaN/Inf. This clears ALL video banks globally.
- **No epoch-level reset**: The bank is NOT reset between videos or epochs during normal operation. Temporal state persists across the entire training run. This means frames from video A can contaminate video B's initial bank state if video B shares the same batch.

---

## 3. Gradient Flow Through Temporal Components

### FeatureBank: Detach behavior (CRITICAL)

Key flag: `FEATURE_BANK_DETACH` (config.py:649, default `True`)

When `True` (legacy behavior):
```python
_stored = feat_i.detach().clone()  # [L1199] -- NO gradient through bank entries
```
- Stored features are detached from the computation graph.
- The ONLY gradient path to `proj_feat` is through the slot -1 overwrite in ActivityHead (line 1358): `bank_seq[:, -1, :] = proj_feat`.
- TCN+ViT gradients flow: `act_logits -> ... -> bank_seq[:, -1, :] -> proj_feat -> backbone`.
- **Temporal gradient from frames t-15 through t-1 is ZERO.** Only the current frame contributes to the backbone gradient.

When `False` (enables temporal learning):
- Stored features retain graph connections: `_stored = feat_i.clone()`.
- Gradient flows back through ALL bank entries to their original `proj_feat` inputs.
- **This is a form of truncated BPTT** (truncation length = window_size = 16).

**Current status in all presets**: `feature_bank_detach: True`. The paper_run preset explicitly has `feature_bank_detach: True` with a comment:
> "keep detached -- gradient through bank causes double-backward crash (#3092789)"

This means there was a known crash when temporal gradient was enabled, and it's currently blocked.

### TCN + ViT Gradient Flow

The TCN and ViT blocks DO receive gradients:
```
act_logits -> classifier -> cls_out [B, 512]
  -> ViT blocks -> TCN -> bank_seq [B, 16, 512]
  -> ONLY slot -1 influences proj_feat (when detach=True)
  -> proj_feat -> activity_proj -> c5_mod (FiLM output)
  -> backbone (via c5)
```

### PSR Sequence Mode: Backbone Gradient Zeroing

When PSR sequence mode fires (every N batches), train.py (lines 1124-1131) **zeros all backbone and FPN gradients** after the backward pass:
```python
for _p in model.backbone.parameters():
    if _p.grad is not None: _p.grad = None
for _p in model.fpn.parameters():
    if _p.grad is not None: _p.grad = None
```
Only PSR head weights update on seq steps. The backbone is intentionally isolated from PSR gradients to prevent feature corruption.

---

## 4. Sequence Length Handling

### Fixed vs Variable
- **FeatureBank**: Supports variable-length sequences. The ring buffer naturally accumulates whatever number of frames have been seen (up to window_size=16).
- **ActivityHead**: Expects a fixed `[B, T=16, 512]` input. If the bank has fewer frames, it pads left. If more, it truncates to the last 16.
- **PSR sequence mode**: Uses `PSR_SEQUENCE_LENGTH=2` (config.py:619). Was 4, reduced due to OOM.

### PSR Sequence vs Temporal Bank Interaction
- PSR sequence mode batches produce `[B, T, C, H, W]` images. The FeatureBank handles this via the dim=3 guard (line 1153: `if projected_features.dim() == 3: return as-is`).
- During seq batches, the FeatureBank is bypassed (returns the input unchanged). Temporal processing for activity on seq batches is just the TCN+ViT on the current batch's T frames.

---

## 5. Memory Usage Concerns

### FeatureBank
- **Per-video**: 16 x 512 float32 = 32 KB per (video_id, camera_view) key.
- **Batch-time**: Only batch_size keys are actively updated per step (plus stale keys from previous steps).
- **Growth**: The dict never shrinks unless `reset()` or `reset_sequence()` is called. Over a full training run with random sampling, the dict grows to one entry per (video_id, camera_view) ever seen. For ~7000 videos x 1 camera = ~7000 entries x 32 KB = ~224 MB peak. Acceptable on 64 GB RAM system.
- **VRAM**: The bank output is `[B, 16, 512]` = 32 KB per batch (FP32). Negligible.

### TemporalConvBlock + ViTTemporalBlock
- TCN: Embed_dim=512, Conv1d depthwise k=5 + pointwise = ~2.6K params. Negligible.
- ViT blocks: 2 x (embed_dim=512, 8 heads, ff_dim=2048) = ~16.8M params each, ~33.6M total. Non-trivial. This is the main VRAM cost of temporal modeling.

---

## 6. Task-Specific Benefit Analysis

The temporal components serve primarily **activity recognition** (AR), not all tasks:

- **Activity Head (AR)**: Directly benefits. The FeatureBank provides 16-frame context; TCN captures motion dynamics; ViT blocks provide long-range attention.
- **Detection (ASD)**: No benefit. Detection head receives only per-frame FPN pyramid features.
- **Pose**: No benefit. Pose head processes single-frame features only.
- **Head Pose**: No benefit. Head pose head processes single-frame c4/c5 features.
- **PSR**: Has its OWN temporal model (CausalTransformer in PSRHead, separate from FeatureBank/TCN/ViT). Does not use the FeatureBank.

**Conclusion**: TMA/TemporalBank benefits only activity recognition. For detection, pose, and PSR, the temporal components increase VRAM and compute without contributing gradient.

---

## 7. Summary of Issues Found

| Issue | Severity | Detail |
|-------|----------|--------|
| USE_TMA_CELL is a dead flag | Medium | Config says "GRU-based" but there is no GRU. The flag is never checked in code. Temporal blocks are always created. |
| USE_TEMPORAL_BANK only affects naming | Medium | FeatureBank is always instantiated and always runs. The flag only changes output dir names. |
| No epoch-level bank reset | Medium | Bank persists across videos and epochs. Features from video A can contaminate the first 16 frames of video B if they share a batch. |
| FEATURE_BANK_DETACH=True disables temporal learning | High | The only gradient path is through slot -1 (current frame). All 15 context frames contribute zero gradient to the backbone. The TCN+ViT blocks learn from 16-frame context, but the backbone sees no temporal signal. |
| Double-backward crash when DETACH=False | Critical | Blocked by comment "#3092789". The bank's dual use (batched seq-mode + per-frame accumulation) creates a graph that crashes on .backward() when detach=False. |
| Temporal components add ~33.6M params for AR only | Medium | Only activity recognition benefits. Detection, pose, head pose, and PSR do not use the temporal path. |

