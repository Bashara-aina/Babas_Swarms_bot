# Agent 17: Numerical Stability Audit — IndustReal Pipeline

**Audit date**: 2026-06-17
**Files examined**:
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/losses.py` (1685 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py` (~2100+ lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/model.py` (~2192 lines)

**Risk levels**: CRITICAL = NaN guaranteed under normal conditions; HIGH = NaN likely;
MEDIUM = NaN possible under edge conditions; LOW = theoretical only;
INFO = design note, not a stability bug

---

## FINDING 1: SoftArgmax softmax overflow [CRITICAL]

**File**: `model.py`, lines 100-128 (`SoftArgmax.forward`)
**Pattern**: softmax/sigmoid overflow (large logits -> exp overflow -> NaN)

```python
weights = F.softmax(flat / self.temperature, dim=-1)  # line 110
```

`temperature=0.1` (set at line 95/1708). This effectively multiplies heatmaps by 10x before softmax. `F.softmax` internally computes `exp(x_i - max(x))` for each spatial position. FP32 `exp(x)` overflows to inf when `x > ~88.7`. With T=0.1, any heatmap value > 8.87 produces `exp(88.7) -> inf`. The heatmap head uses ConvTranspose2d + GroupNorm + ReLU (lines 581-591), producing UNBOUNDED positive values — ReLU has no upper bound. During training, as the network learns sharper keypoint peaks, heatmap values grow without limit.

**Impact**: NaN propagates from soft-argmax -> keypoints -> PoseFiLM -> c5_mod -> activity head, PSR head -> ALL losses NaN. This would cause the Kendall guard to fire, replacing all losses with 1e-4 fallback, effectively deadening all gradient signal.

**Fix**: Clamp heatmap values before soft-argmax: `heatmaps = heatmaps.clamp(min=-10.0, max=10.0)` or use the `_sanitize` pattern already used elsewhere in the model.

---

## FINDING 2: Non-Kendall staged training gradient disconnection [HIGH]

**File**: `train.py`, lines 1428-1472
**Pattern**: gradient computation / NaN propagation through detach

```python
loss = torch.tensor(_det_val / float(accum_steps), dtype=torch.float32, device=device)
loss.requires_grad_(True)  # line 1429 — creates leaf tensor with NO grad_fn
```

When `staged_training=True` AND `not criterion.use_kendall`, the code replaces the original `loss` tensor (which was connected to the model via autograd) with a NEW leaf tensor constructed from detached Python float values. `requires_grad_(True)` on a new tensor makes it a leaf that accumulates grad from nothing — its backward produces `0 * gradient` for all model parameters. **No training occurs on this code path.**

**Impact**: The entire non-Kendall staged mode produces zero gradient. This path is entered when `not criterion.use_kendall` and `STAGED_TRAINING=True` (the default). If someone ever sets `USE_KENDALL=False`, the model silently stops learning.

**Fix**: Either (a) remove the non-Kendall staged path as dead code, or (b) use in-place masking on the original loss tensor instead of creating a new one.

---

## FINDING 3: CB-Focal loss p_t unclamped -> gradient vanishing [MEDIUM]

**File**: `losses.py`, line 710 (`ClassBalancedFocalLoss.forward`)
**Pattern**: focal loss (1-p_t)^gamma when p_t very close to 1

```python
focal_weight = (1 - p_t) ** self.gamma  # line 710 — no clamp on p_t
```

`p_t` is computed via softmax gather (line 707) or smooth-target sum (line 703). When the model is confident (p_t > 0.999), `(1 - p_t) ** 2.0` can produce values as small as `(1e-14)`. In FP32 this is representable (~1e-14 > 1e-38 min), so no NaN — but gradient is essentially zero (underflow to 0 for practical purposes).

**Contrast with detection FocalLoss** (line 297, 299): `p = torch.sigmoid(cls_pred).clamp(1e-7, 1.0-1e-7)` and `p_t = p * cls_target + (1-p) * (1-cls_target)` — p_t IS implicitly bounded by the sigmoid clamp, but `p_t` itself is NOT clamped, so could still be ~1 or ~0.

**Contrast with binary_focal_loss** (line 832): `p_t = p_t.clamp(min=1e-6, max=1.0-1e-6)` — GOOD, explicit clamp.

**Impact**: Gradient vanishing for confident predictions in CB-Focal loss. The LDAM-DRW path (preferred path when `USE_LDAM_DRW=True`) uses `F.cross_entropy` internally which is numerically stable and does not have this issue. So this only affects the non-LDAM path.

**Fix**: Add `p_t = p_t.clamp(min=1e-6, max=1.0 - 1e-6)` before the focal weight computation.

---

## FINDING 4: log(0) in Wing Loss coefficient [LOW — theoretical]

**File**: `losses.py`, line 385 (`WingLoss.__init__`)
**Pattern**: log(very_small_number) without epsilon guard

```python
self.C = omega - omega * math.log(1 + omega / epsilon)  # line 385
```

`omega=0.05, epsilon=0.005`. `1 + 0.05/0.005 = 11`. `log(11) ~ 2.398`. Fine at init time. At forward (line 392), `torch.log(1 + diff / self.epsilon)` — when diff=0, `log(1) = 0`. When diff is large but finite (e.g., 100), `log(1 + 100/0.005) = log(20001) ~ 9.9`. No NaN risk. This is only theoretical because the loss weight is `0.001 * WingLoss`, making the output O(0.001) — below typical FP32 precision floor for additive losses.

**Verdict**: Safe as-is.

---

## FINDING 5: Division by zero guards present [OK / INFO]

**File**: `losses.py`
- Line 458: `np.maximum(cls_num_list, 1e-8)` — guard against zero class count
- Line 514: `1.0 / np.maximum(effective, 1e-8)` — guard against zero effective samples
- Line 515: `weights / weights.sum()` with `weights.shape[0]` — sum is non-zero due to previous clamp
- Line 1647: `ws = a_det + a_hp + a_act + a_psr + 1e-8` — guard in Kendall normalization

**File**: `train.py`
- Line 2022: `mae_safe = max(mae_head_pose, 1e-6)` — guard in combined metric
- No unguarded divisions found.

**Verdict**: Division-by-zero guards are comprehensive. No issues.

---

## FINDING 6: NaN propagation through detach/stop_gradient [INFO]

**File**: `model.py`
- Line 1928: `with torch.no_grad(): det_conf = torch.sigmoid(cls_preds.max(dim=1)[0])` — det_conf is detached before activity head. If cls_preds has NaN, det_conf will be NaN, but it's under `no_grad()` so no gradient flow anyway. The NaN guard at line 2067-2087 catches this.
- Line 2034: `c5_mod = self.headpose_film(c5_mod, head_pose.detach())` — stop_grad per paper spec. If head_pose has NaN from unbounded MLP (lines 1411-1421, no output activation), NaN propagates to c5_mod via FiLM multiplication.
- Line 689: `conf_flat = confidence.detach()` — PoseFiLM detaches confidence. If confidence has NaN, the NaN propagates through gamma_net and beta_net to c5_mod.
- Line 1957-1960: `DETACH_PSR_FPN` — gradient isolation, good.

**Key risk**: head_pose MLP (HeadPoseHead, lines 1411-1421) produces unbounded 9-DoF output (no tanh/sigmoid). If intermediate activations overflow (GELU at 512-dim can produce large values), head_pose contains NaN, which propagates through headpose_film to c5_mod and all downstream heads. **No guard on head_pose output before FiLM.**

---

## FINDING 7: FP32 vs FP16 numerical ranges [MEDIUM]

**File**: `train.py`
- Line 1247-1248: outputs cast to float() AFTER AMP autocast — good
- Line 1047: `with amp.autocast('cuda', enabled=C.MIXED_PRECISION)` — FP16 when enabled
- Line 1563: `scaler.scale(loss).backward()` — proper AMP scaling
- Line 1193: `scaler.step(optimizer)` / `scaler.update()` — at line 1671 for non-seq path

**Key risk**: While outputs are cast to float() for loss computation, internal model operations run in FP16 within the autocast region. ConvNeXt-Tiny with FP16 AMP is generally stable, but:
- SoftArgmax (Finding 1) is more likely to overflow in FP16 (max safe value ~65504, but with T=0.1, heatmap values > 6550.4 would overflow — less likely but still possible when autocast applies)
- Gradient scaler may silently skip steps (RC-29 telemetry tracks this at lines 1669-1679)

**Verdict**: Code is mostly well-designed for FP16/FP32 coexistence. The FP16 risk is secondary to the SoftArgmax issue (Finding 1).

---

## FINDING 8: Pyramid and backbone NaN sanitization [OK]

**File**: `model.py`, lines 1836-1854

```python
def _sanitize(x, bound=100.0):
    if torch.isfinite(x).all():
        return x.clamp(-bound, bound)
    return torch.where(torch.isfinite(x), x.clamp(-bound, bound), torch.zeros_like(x))

_c3, _c4, _c5 = _sanitize(c3), _sanitize(c4), _sanitize(c5)
pyramid = self.fpn(_c3, _c4, _c5)

for _k in pyramid:
    if not torch.isfinite(pyramid[_k]).all():
        pyramid[_k] = torch.where(
            torch.isfinite(pyramid[_k]),
            pyramid[_k].clamp(-100.0, 100.0),
            torch.zeros_like(pyramid[_k]),
        )
    else:
        pyramid[_k] = pyramid[_k].clamp(-100.0, 100.0)
```

**Note**: In the `else` branch, `pyramid[_k] = pyramid[_k].clamp(-100.0, 100.0)` creates a new tensor via clamp, meaning even the non-NaN path goes through a copy. This is fine for safety but has minor performance cost. `torch.where` preserves gradient flow for finite entries. Good design.

**Verdict**: Comprehensive. Both backbone outputs and pyramid levels are sanitized before any head processes them.

---

## FINDING 9: Output-level NaN guard (last resort) [INFO]

**File**: `model.py`, lines 2067-2087

```python
for _out_name, _out_val in [
    ('cls_preds', cls_preds), ('reg_preds', reg_preds), ...
]:
    if _out_val is not None and not torch.isfinite(_out_val).all():
        _out_val = torch.zeros_like(_out_val)
        # reassign to local variable
```

This zeros ALL head outputs if they contain NaN. While this prevents NaN from reaching the loss, it also **breaks gradient flow for those outputs** — the loss sees zeros and produces zero gradient for that head. This is intentional as a last-resort safety net. The training loop's NaN loss check (train.py lines 1474-1493) then catches the resulting zero-loss and skips the step entirely.

**Risk**: If NaN outputs are persistent (e.g., the SoftArgmax overflow in every frame), every step is skipped and training stops completely. Combined with finding 1, this is the failure mode: SoftArgmax overflows -> head outputs zeroed -> loss zero -> step skipped.

---

## FINDING 10: log_var clamp_ does NOT fix NaN — but code handles it correctly [OK]

**File**: `train.py`, lines 2063-2069

```python
if not torch.isfinite(_p.data).all():
    logger.warning(f'  [KENDALL_NAN] {_param} was NaN — resetting to 0.0')
    _p.data.fill_(0.0)
_lo, _hi = _bounds.get(_param, (-4.0, 2.0))
_p.data.clamp_(_lo, _hi)
```

The code correctly detects NaN log_vars and resets them to 0.0. Note: `torch.clamp_` on its own does NOT fix NaN (IEEE 754: NaN comparisons always return False, so `clamp_` silently passes NaN through). The explicit `isfinite` check + `fill_(0.0)` fixes this. **This pattern is correct**, unlike a naive `clamp_` that would preserve NaN.

**Verdict**: Correct implementation. No issue.

---

## FINDING 11: `grad.norm().item()` with NaN gradients in diagnostic [LOW]

**File**: `train.py`, lines 2119-2121

```python
gn = param.grad.norm().item()
```

`torch.norm()` of a NaN-containing gradient produces NaN (not inf). The diagnostic function `_log_per_head_grad_norm` would log `NaN` as the gradient norm value. The ALIVE/DEAD threshold check `NaN > 1e-6` correctly returns False (DEAD), so the diagnostic logic is correct, but the displayed value is misleading.

**Fix**: Use `torch.norm(torch.where(torch.isfinite(param.grad), param.grad, torch.zeros_like(param.grad)))` or check `isfinite` before computing norm.

---

## FINDING 12: `_safe` lambda negative-clamp (blocks negative GIoU) [INFO]

**File**: `losses.py`, line 1429

```python
_safe = lambda l, z: ... torch.where(l < 0, z, l) ...
```

The `torch.where(l < 0, z, l)` creates a non-differentiable boundary at 0. Gradient for elements below 0 is zero (replaced by constant `z`). This is a hard gradient clamp applied post-hoc to individual losses. Makes sense as a last-resort guard before Kendall assembly, but the gradient discontinuity at 0 could cause optimization issues if a loss frequently crosses zero.

**Impact**: GIoU loss IS negative (range [-1, 1]). When GIoU is negative (boxes don't overlap), `loss_det` can be negative (cls_loss ~0 + giou_weight * negative_giou). The `_safe` clamp replaces negative loss_det with `z=0.0`, meaning **negative GIoU gradients are completely suppressed**. This is intentional (line 1115-1120: `NEG_SLOPE = 0.0`), but means the detection head gets NO signal when GIoU is negative.

---

## FINDING 13: Binary focal loss -1 target masking [OK — well designed]

**File**: `losses.py`, lines 808-848

```python
if (targets < 0).any():
    ignore_mask = (targets < 0).float()
    targets_safe = targets.clone().masked_fill_(ignore_mask.bool(), 0)
    ...
    alpha_t = alpha_t * (1 - ignore_mask)  # 0 for -1 targets
    p_t = p_t.masked_fill(ignore_mask.bool(), 1.0)
    ce = ce.masked_fill(ignore_mask.bool(), 0.0)
p_t = p_t.clamp(min=1e-6, max=1.0 - 1e-6)
```

Sets -1 targets to produce loss=0: alpha_t=0, p_t=1 (focal weight = 0), ce=0. Then correctly computes mean over only valid (non--1) entries at line 847: `loss = per_elem.masked_select(valid_mask).mean()`. Also handles the all--1 edge case at line 845-846.

**Verdict**: Comprehensive, correct, numerically safe.

---

## FINDING 14: Gradient accumulation scaling [INFO]

**File**: `train.py`, lines 1403, 1112

```python
loss = loss / float(accum_steps)  # line 1403 — main path
loss_seq = loss_seq / float(accum_steps)  # line 1112 — seq path
```

Loss is divided by accum_steps before backward. GradScaler scales loss before backward. The unscale happens at line 1581 before clipping. This is the standard AMP gradient accumulation pattern. Correct.

**Note**: `accum_steps=8` (default from C.GRAD_ACCUM_STEPS). With effective batch size = 4 * 8 = 32.

---

## FINDING 15: Integer overflow in large tensor operations [LOW]

**File**: `model.py`, line 469 (AnchorGenerator)

```python
cell_anchors = torch.tensor(cell_anchors, device=device, dtype=torch.float32)
```

Anchor coordinates are always float32. No integer overflow risk.

**File**: `train.py`, line 329

```python
bytes_per_image = 3 * C.IMG_HEIGHT * C.IMG_WIDTH * 4
```

With 1280x720 images: `3 * 720 * 1280 * 4 = 11,059,200` bytes (~10.5 MB). Well within int32 range.

**File**: `model.py`, line 1881

```python
max_idx = top_conf.argmax().item()
```

`argmax()` returns an index into the flattened anchor tensor (173K anchors). Within int32 range (~2.1B). Safe.

**Verdict**: No integer overflow risks identified.

---

## FINDING 16: LDAM margin with label_smoothing [OK]

**File**: `losses.py`, lines 609-615

```python
logits_safe = (self.s * x_m).clamp(-50.0, 50.0)
return (w * F.cross_entropy(
    logits_safe, hard_targets, reduction='none',
    label_smoothing=0.1
)).mean()
```

`F.cross_entropy` internally uses `log_softmax` which subtracts the max logit before exp, avoiding overflow. The pre-clamp to [-50, 50] is an additional safety layer. With `s=30` and `x_m` already clamped to [-10, 10], the effective range is [-300, 300], but then clamped again to [-50, 50]. Correct.

---

## SUMMARY TABLE

| # | Finding | Risk | File | Line(s) |
|---|---------|------|------|---------|
| 1 | SoftArgmax softmax overflow (T=0.1 -> exp overflow) | CRITICAL | model.py | 110 |
| 2 | Non-Kendall staged path gradient disconnection | HIGH | train.py | 1428-1472 |
| 3 | CB-Focal p_t unclamped -> gradient vanishing | MEDIUM | losses.py | 710 |
| 4 | Wing Loss log coefficient — theoretical only | LOW | losses.py | 385 |
| 5 | Division-by-zero guards present | OK | various | various |
| 6 | NaN propagation through detach (head_pose -> FiLM) | MEDIUM | model.py | 2034 |
| 7 | FP16/FP32 AMP handling | OK | train.py | 1047, 1247 |
| 8 | Pyramid/backbone NaN sanitization | OK | model.py | 1836-1854 |
| 9 | Output-level NaN zeroing | INFO | model.py | 2067-2087 |
| 10 | log_var clamp handles NaN correctly | OK | train.py | 2063-2069 |
| 11 | grad.norm().item() with NaN grads in diagnostic | LOW | train.py | 2121 |
| 12 | _safe lambda negative clamp (blocks negative GIoU) | INFO | losses.py | 1429 |
| 13 | Binary focal loss -1 target masking | OK | losses.py | 808-848 |
| 14 | Gradient accumulation with AMP | OK | train.py | 1403, 1112 |
| 15 | Integer overflow | OK | various | various |
| 16 | LDAM margin with label_smoothing | OK | losses.py | 609-615 |

---

## PRIORITY ACTIONS

1. **[CRITICAL] Fix SoftArgmax overflow** — Add heatmap clamp before soft-argmax in `model.py` line 110. 10 lines, immediate payoff.
2. **[HIGH] Fix non-Kendall staged training path** — Either add gradient reconnection or remove dead code in `train.py` lines 1428-1472.
3. **[MEDIUM] Clamp p_t in CB-FocalLoss** — Add `p_t = p_t.clamp(min=1e-6, max=1.0-1e-6)` at `losses.py` line 710.
4. **[MEDIUM] Guard head_pose output before FiLM** — Add `_sanitize` or clamp on head_pose output at `model.py` line 1427.
5. **[LOW] Fix grad.norm() NaN diagnostic** — Use safe norm in `train.py` line 2121.
