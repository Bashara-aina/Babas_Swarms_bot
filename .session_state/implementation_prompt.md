# MTL IMPLEMENTATION — Tier 1 Code Changes
## Based on Claude Science Consultation (IMPLEMENTATION_PLAN.md)

PROJECT_ROOT="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved"

### CRITICAL RULES
- Read the file before editing it. Run `gitnexus_impact` before any symbol change.
- Run `make check` after each change. Commit after each working item with a clear message.
- VERIFY every change: after implementing, run a quick syntax check with `python3 -c "compile(open(X).read(), X, 'exec')"`.
- ANTI-HALLUCINATION: Do not infer method details. Every formula and parameter comes from the plan below. If something is unclear, ask.

---

## ORDER OF EXECUTION (Follow strictly)

### ITEM 1: UW-SO Loss Weighting (Priority Score: 56.7)
**File:** `src/models/mvit_mtl_model.py`
**Impact:** 85 — Eliminates weight collapse pathology. Drop-in replacement for Kendall UW.

**Implementation:**
1. Read the current loss weighting in the training loop (`scripts/train_mtl_mvit.py` — find the `losses` dict and `weighted_loss` computation)
2. Create a new function/loss module at `src/losses/uw_so.py`:
   ```python
   def uw_so_loss(losses: Dict[str, torch.Tensor], temperature: float = 1.0) -> torch.Tensor:
       """Uncertainty-Weighted Softmax Ordinal weighting.
       weights = softmax(-detach(losses) / temperature)
       """
       loss_tensor = torch.stack(list(losses.values()))
       with torch.no_grad():
           weights = F.softmax(-loss_tensor / temperature, dim=0)
       return (loss_tensor * weights).sum()
   ```
3. In `train_mtl_mvit.py`: Replace the Kendall uncertainty weighting block with `uw_so_loss()`.
4. Delete the 4 learnable log-var parameters (`self.log_vars`).
5. Remove the log-var EMA capping logic.
6. Add `--loss-weighting` argument with options: `kendall-uncapped` (keep for ablation), `uw-so` (new default).
7. Add temperature parameter `--uw-temperature 1.0`.
8. Rollback: Keep `--loss-weighting kendall-uncapped` flag for ablation comparison.

**Verify:** `python3 -c "compile(open('src/losses/uw_so.py').read(), 'src/losses/uw_so.py', 'exec')"`

---

### ITEM 2: Per-Task Learning Rates (Priority Score: 45.0)
**File:** `scripts/train_mtl_mvit.py` (optimizer section)

**Implementation:**
1. Read the current optimizer setup (parameter groups for backbone, heads, log-vars).
2. After removing log-vars (Item 1), create 5 parameter groups:
   - Backbone: `lr_backbone` (default 1e-4)
   - Detection head: `lr_head * 1.0`
   - Activity head: `lr_head * 1.0`
   - PSR head: `lr_head * 0.3`
   - Pose head: `lr_head * 0.3`
3. Add `--task-lr-mult` argument: `{'psr': 0.3, 'pose': 0.3, 'detection': 1.0, 'activity': 1.0}`.
4. Group head parameters by task name (use naming convention: `det.*`, `act.*`, `psr.*`, `pose.*`).

**Verify:** Print parameter groups and LR values at startup.

---

### ITEM 3: Balanced Softmax for Activity Head (Priority Score: 30.0)
**File:** `src/models/mvit_mtl_model.py` (ActivityHead class, around line 272)
**Impact:** 30 — Replaces hand-tuned CE + logit_adj + sqrt_tamed_weights with principled long-tail loss.

**Implementation:**
1. Read the current ActivityHead loss computation (in the `forward` method or training loop).
2. Create `src/losses/balanced_softmax.py`:
   ```python
   class BalancedSoftmaxLoss(nn.Module):
       def __init__(self, class_priors: torch.Tensor):
           super().__init__()
           self.register_buffer('class_priors', class_priors)
       
       def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
           # Balanced Softmax: shifts logits by log(prior) per class
           logits_shifted = logits + torch.log(self.class_priors.unsqueeze(0))
           return F.cross_entropy(logits_shifted, targets)
   ```
3. Remove the existing: `logit_adj`, `sqrt_tamed_weights`, `tau` parameters from ActivityHead.
4. Compute `class_priors` from the dataset (frequency of each of the 75 classes).
5. Replace the loss computation: `loss_act = balanced_softmax(logits, targets)`.

---

### ITEM 4: Gradient Clipping (Priority Score: 30.0)
**File:** `scripts/train_mtl_mvit.py` (after loss.backward(), before optimizer.step())

**Implementation:**
1. Add `--grad-clip-norm 1.0` argument.
2. Before `optimizer.step()`:
   ```python
   torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.grad_clip_norm)
   ```
3. If current clip norm is different (e.g. 5.0), keep existing as `--grad-clip-norm 5.0` default for rollback.

---

### ITEM 5: EMA Warmup Start at Epoch 5 (Priority Score: 24.0)
**File:** `scripts/train_mtl_mvit.py` or wherever EMA is configured

**Implementation:**
1. Find the EMA initialization line (likely `ema_start_epoch=0`).
2. Change to `ema_start_epoch=5` (or add `--ema-start-epoch 5`).
3. This gives the model 10% of training (5/50 epochs) to stabilize before averaging.

---

### ITEM 6: LDAM-DRW for Activity Head (Priority Score: 20.0)
**File:** New file `src/losses/ldam_drw.py` + modify ActivityHead

**Implementation:**
1. Create `src/losses/ldam_drw.py`:
   ```python
   class LDAMLoss(nn.Module):
       def __init__(self, cls_num_list: List[int], max_m: float = 0.5, s: float = 30, 
                    reweight_epoch: int = 35):
           super().__init__()
           m_list = 1.0 / torch.sqrt(torch.sqrt(torch.tensor(cls_num_list, dtype=torch.float)))
           m_list = m_list * (max_m / m_list.max())
           self.register_buffer('m_list', m_list)
           self.s = s
           self.reweight_epoch = reweight_epoch
           self.is_drw = False
       
       def forward(self, logits: torch.Tensor, targets: torch.Tensor, epoch: int) -> torch.Tensor:
           if epoch >= self.reweight_epoch:
               self.is_drw = True  # Switch to re-weighted CE after LR drop
           # LDAM: subtract margin from logits for each class
           index = torch.zeros_like(logits, dtype=torch.bool)
           index.scatter_(1, targets.view(-1, 1), 1)
           index_float = index.float()
           batch_m_list = self.m_list.unsqueeze(0) * index_float
           logits_m = logits - batch_m_list * self.s
           if self.is_drw:
               # Class-balanced weighting: weight = 1 / sqrt(n_y)
               weights = 1.0 / torch.sqrt(torch.tensor(cls_num_list, dtype=torch.float))
               weights = weights / weights.sum() * len(cls_num_list)
               return F.cross_entropy(logits_m, targets, weight=weights.to(logits.device))
           return F.cross_entropy(logits_m, targets)
   ```
2. Pass `cls_num_list` (class counts for 75 classes) from dataset.
3. DRW activates at epoch 35 (when LR drops in 50-epoch schedule with cosine annealing).

---

### ITEM 7: SWA Window 5 → 10 Epochs (Priority Score: 16.0)
**File:** training config / script

**Implementation:**
1. Find `SWA_WINDOW=5` or similar.
2. Change to `SWA_WINDOW=10` or add `--swa-window 10`.

---

### ITEM 8: ASL (Asymmetric Loss) for PSR (Priority Score: 14.0)
**File:** New file `src/losses/asymmetric_loss.py` + modify PSRHead

**Implementation:**
1. Create `src/losses/asymmetric_loss.py`:
   ```python
   class AsymmetricLoss(nn.Module):
       def __init__(self, gamma_neg: float = 4.0, gamma_pos: float = 0.0, 
                    clip: float = 0.05, eps: float = 1e-8):
           super().__init__()
           self.gamma_neg = gamma_neg
           self.gamma_pos = gamma_pos
           self.clip = clip
           self.eps = eps
       
       def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
           # ASL: hard-thresholds negative gradients so ultra-easy negatives contribute nothing
           prob = torch.sigmoid(logits)
           prob = torch.clamp(prob, self.clip, 1 - self.clip)
           targets = targets.float()
           pos_mask = targets == 1
           neg_mask = targets == 0
           
           pos_loss = -targets * torch.log(prob) * torch.pow(1 - prob, self.gamma_pos)
           neg_loss = -(1 - targets) * torch.log(1 - prob) * torch.pow(prob, self.gamma_neg)
           
           return (pos_loss + neg_loss).mean()
   ```
2. Replace the current PSR BCE+focal loss with ASL.
3. Remove the sensitivity penalty cap increase that was compensating for BCE+focal failure.

---

### ITEM 9: Task Head Dropout (Priority Score: 10.0)
**File:** `src/models/mvit_mtl_model.py` (PSRHead and PoseHead)

**Implementation:**
1. In PSRHead (line 362), add after the hidden layer: `self.dropout = nn.Dropout(0.15)`
2. In PoseHead (line 444), add after the hidden layer: `self.dropout = nn.Dropout(0.15)`
3. Apply in forward: `x = self.dropout(x)` before the output projection.

---

### ITEM 10: Huberised Geodesic Loss for Pose (Priority Score: 8.3)
**File:** New file `src/losses/geodesic_loss.py` + modify PoseHead

**Implementation:**
1. Create `src/losses/geodesic_loss.py`:
   ```python
   def huberised_geodesic_loss(pred: torch.Tensor, target: torch.Tensor, 
                                 delta: float = 30.0) -> torch.Tensor:
       """Huberised geodesic loss. Caps outlier gradients from extreme pose errors."""
       # Compute geodesic error (assuming 6D rotation representation)
       error = compute_geodesic_error(pred, target)  # reuse existing function
       # Huber-like: quadratic below delta, linear above
       mask = error < delta
       loss = torch.where(mask, 0.5 * error**2, delta * (error - 0.5 * delta))
       return loss.mean()
   ```
2. Replace the current geodesic loss in PoseHead with this Huberised variant.
3. Delta=30 degrees as default (add `--pose-huber-delta 30`).

---

### ITEMS 11-13: Varifocal, DB-MTL, WIoU (Priority Scores: 8.3, 8.3, 5.0)
**Files:** `src/losses/varifocal_loss.py`, modify detection loss in training loop

11. **Varifocal Loss for Detection Classification:**
    - Create `src/losses/varifocal_loss.py` with the VFL formula.
    - Replace Focal Loss in detection classification branch.
    - VFL formula: `VFL(p, q) = -q * (q * log(p) + (1-q) * log(1-p))` where q is IoU score.

12. **DB-MTL Log-Transform:**
    - Before UW-SO weighting, apply `log(1 + loss)` to each task loss.
    - Add `--db-mtl` flag.
    - ~3 lines in training loop.

13. **WIoU v3 for Detection Box Regression:**
    - Replace CIoU with WIoU v3 formulation.
    - Reference implementation from Tong et al. 2023.

---

## VERIFICATION PROTOCOL

After EACH item is implemented:
1. `python3 -c "compile(open('path/to/changed/file.py').read(), 'path/to/changed/file.py', 'exec')"` — syntax check
2. `python3 -c "import sys; sys.path.insert(0, 'src'); from losses.uw_so import uw_so_loss; print('Import OK')"` — module import check
3. If the model file changed: `gitnexus_impact({target: "mvit_mtl_model.py", direction: "upstream"})`
4. `git add` + `git commit -m "mtl: [ITEM NAME] — [brief description]"`

## EXECUTION ORDER (CRITICAL)

```
Item 1  → UW-SO (must be first — everything depends on loss weighting)
Item 2  → Per-task LR (needs UW-SO done first for clean optimizer groups)
Item 3  → Balanced Softmax (independent)
Item 4  → Gradient clipping (independent)
Item 5  → EMA warmup (independent)
Item 6  → LDAM-DRW (can run parallel with 3, 4, 5)
Item 7  → SWA window (independent)
Item 8  → ASL (PSR-specific, independent)
Item 9  → Task dropout (PSR/Pose-specific, independent)
Item 10 → Huberised geodesic (Pose-specific, independent)
Item 11 → Varifocal loss (Detection-specific, independent)
Item 12 → DB-MTL log-transform (independent)
Item 13 → WIoU v3 (Detection-specific, independent)
```

Items 3-13 can be parallelized after Item 1+2 are done.
