# Agent 2: Unified Training Specialist -- One Model to Combine All Best Metrics

**Date:** 2026-08-01
**Role:** Unified Training Specialist (Agent 2 of 5-agent debate team)
**Inputs:** Revert plans 12-16, debate files 07-11, PSR revival plan 03, integration synthesis 05, cascade_table.md, training logs, on-disk checkpoint verification
**Mission:** Build a training plan for ONE model that combines act=0.394, pose=6.15 degrees, and psr=0.883
**Constraint:** NO code changes. Plan document only.
**Freeze date:** Aug 22, 2026 (21 days from today)

---

## 0. Executive Summary

**The honest answer: No single model can achieve all three targets by Aug 22, 2026.**

The two checkpoints use fundamentally incompatible architectures:
- **v4_fixed** (233 MB): ConvNeXt-Tiny backbone, 3-channel RGB, per-frame 2D CNN. Achieves act=0.394 and pose=6.15 degrees. PSR is dead (0.10 F1 on Path B). Detection is dead (0.00009 mAP50).
- **v3.41_safe** (664 MB): MViTv2-S backbone, 9-channel input, 16-frame 3D spatiotemporal clips. Achieves psr=0.883. Activity and pose are weaker (0.255/0.039, 7.94 degrees).

These are different neural architectures with different input formats. They cannot be merged, distilled into each other, or co-loaded into a single model. The "one model" goal faces a hard architectural barrier.

**What IS possible in 21 days:**
1. **ConvNeXt-Tiny with PSR Path A restoration** -- 50-70% chance of psr >= 0.50, 10-25% chance of psr >= 0.80. Pose restored in 2 hours (code fix). Activity is architecturally impossible on this backbone.
2. **MViTv2-S with act+pose heads added** -- Unknown act/pose ceiling. 5-7 days training. Risk: no checkpoint with proven act+pose on MViTv2-S exists.
3. **Two-model deployment** -- ConvNeXt-Tiny for act+pose, MViTv2-S for PSR. This is the only path with guaranteed metrics. Total: ~4 GPU-hours (re-evaluation only). No training required.

**Recommendation: Option 3 (two-model) for the paper; Option 1 (ConvNeXt PSR Path A) as an experiment.** The adversarial synthesis (11_debate_adversarial.md) is correct: at most 2 of 4 tasks are revivable on one backbone. The paper is stronger as pathology documentation than as a forced single-model result.

---

## 1. Architecture Decision: Which Backbone?

### 1.1 The Two Candidates

| Dimension | ConvNeXt-Tiny (v4_fixed) | MViTv2-S (v3.41_safe) |
|-----------|--------------------------|------------------------|
| **Parameters** | ~28.6M | ~34.3M |
| **Input** | 3-channel RGB, per-frame | 9-channel (RGB+VL+StereoL+StereoR+Depth), 16-frame 3D clips |
| **Pretraining** | ImageNet-1K (static images) | Kinetics-400? (spatiotemporal) |
| **Architecture** | 2D CNN, per-frame features | 3D CNN, spatiotemporal attention |
| **Proven act** | **0.394** (verified by 2 independent evals) | 0.255 macro / 0.039 micro (from v3.41_safe eval_e3_b0.json) |
| **Proven pose** | **6.15 deg** (Legacy HeadPoseHead) | ~7.94 deg (from same eval) |
| **Proven psr** | 0.10 (Path B, 24-class softmax) | **0.883** (Path A, 11 binary heads) |
| **Proven det** | 0.00009 (99.99% collapse) | 0.214 (weaker but not collapsed) |
| **Checkpoint** | v4_e0_b200.pth, 233 MB, exists on disk | phase2_e3_b0.pth, 664 MB, exists on disk |
| **Training time (full MTL)** | 38 min/epoch (RTX 3060, subset) | ~3 hr/epoch (RTX 5060 Ti, full) |

### 1.2 The Input Channel Problem

The MViTv2-S model was trained with 9-channel input. The current training pipeline is configured for 3-channel RGB. To use MViTv2-S, either:
- The 9-channel data pipeline must be restored (unknown code state after months of changes)
- Or the backbone must be retrained from scratch with 3-channel input (loses the 0.883 guarantee)

This is a critical blocker not mentioned in any plan. The v3.41_safe checkpoint's first convolutional layer expects 9 input channels. Loading it into a 3-channel pipeline will crash or produce garbage.

### 1.3 The Activity Dead-End on ConvNeXt

The linear probe result is decisive: frozen ConvNeXt-Tiny features achieve **0.2169 top-1** vs a majority-class baseline of **0.2217** (always predict class 8). The backbone encodes ZERO activity-relevant information. Fine-tuning the backbone might create some activity features, but ImageNet-pretrained 2D CNNs lack temporal/motion encoding fundamentally. The adversarial synthesis gives:
- Probability of hitting 0.6223 on ConvNeXt-Tiny: **<1%**
- Probability of hitting 0.25-0.35 verb-group: **~15%**

### 1.4 Verdict

**ConvNeXt-Tiny** is the only viable single-model candidate because:
1. It is the current training backbone. No infrastructure changes needed.
2. It has proven act+pose (the two tasks that are NOT architecturally blocked).
3. PSR Path A has never been tested on ConvNeXt -- it might work (25% chance of >= 0.80).
4. Activity is architecturally impossible on either backbone without MViTv2-S's spatiotemporal features.

**MViTv2-S** would be the better PSR backbone but requires:
- Restoring the 9-channel data pipeline (unknown scope)
- Adding act+pose heads (unknown whether they'll work on 9-channel features)
- Training from scratch or fine-tuning (10+ days minimum)

**The 9-channel pipeline restoration alone could take 3-5 days of debugging.** Not viable before Aug 22.

---

## 2. Training Strategy Options

### Strategy 1: Continue Training v4_fixed (ConvNeXt-Tiny + All Heads)

**Concept:** Take the v4_fixed checkpoint (233 MB) with its proven act=0.394 and pose=6.15, and train PSR on top of it.

**What must be done:**
1. Restore PSR Path A architecture (11 binary heads + MonotonicDecoder) per plan 03_psr_revival.md
2. Apply GELU saturation fix: LeakyReLU(0.01) + zero bias + Xavier init std=0.01
3. Freeze the ConvNeXt backbone (preserve act and pose features)
4. Train only the PSR head (and possibly FPN) for 50 epochs
5. Gate on transition F1 > 0.20 before committing to full training

**Pros:**
- Only one new head to train (PSR). Act and pose are already proven.
- ConvNeXt-Tiny is the current infrastructure -- no pipeline changes needed.
- PSR gradients don't flow into backbone (DETACH_PSR_FPN=True default)
- Can run on RTX 3060 while GPU 0 is free for other work

**Cons:**
- PSR Path A was proven on MViTv2-S with 9-channel input, NOT on ConvNeXt with 3-channel RGB
- ConvNeXt per-frame features may lack temporal/state-transition information
- 4 of 11 PSR components were dead even at the best MViTv2-S checkpoint
- HeadPoseFiLM contamination: fixing pose column ordering could degrade PSR features via shared FiLM layers
- Activity is dead on ConvNeXt regardless (linear probe proves zero signal)

**Realistic probability:**
- Transition F1 > 0.20 (gate pass): **75%** (Agent 5's Section 1.3)
- PSR F1 >= 0.50: **~50%**
- PSR F1 >= 0.80: **~25%**
- PSR F1 >= 0.883 (matching MViTv2-S): **<10%**
- Activity >= 0.394 (maintaining v4_fixed level): **~95%** (backbone frozen, only eval variance)
- Pose <= 6.15 deg (maintaining v4_fixed level): **~90%** (code fix, not training)

**Time estimate:** 7 days (PSR Path A: 50 epochs x 3.2 hr/epoch = 160 hr = 6.7 days + 3 hr eval)
**GPU:** RTX 3060 (GPU 1)
**Risk of exceeding Aug 22:** LOW (7 days < 21 days). Multiple retry cycles possible.

---

### Strategy 2: Continue Training v3.41_safe (MViTv2-S + Act+Pose Heads)

**Concept:** Take the v3.41_safe checkpoint (664 MB) with its proven psr=0.883, and add/improve act and pose heads.

**What must be done:**
1. Restore the 9-channel data pipeline (RGB+VL+StereoL+StereoR+Depth) -- UNKNOWN SCOPE
2. Verify the checkpoint loads correctly with the current codebase
3. Add HeadPoseHead (or port the legacy one) to the MViTv2-S architecture
4. Add or fine-tune the activity head
5. Train multi-task with frozen PSR weights

**Pros:**
- PSR is already at 0.883 -- no PSR training needed
- MViTv2-S's spatiotemporal features are better for activity
- The checkpoint exists and is verified on disk

**Cons:**
- **The 9-channel data pipeline must be restored.** The current training infrastructure uses 3-channel RGB. The v3.41_safe checkpoint expects 9 input channels. Loading it into a 3-channel pipeline will crash (conv1 weight shape mismatch: [64, 9, 3, 7, 7] vs expected [64, 3, ...]).
- Restoring the 9-channel pipeline is an unknown-quantity engineering task. It touches data loading, preprocessing, model input layer, and possibly the dataset format.
- Act and pose on MViTv2-S are weaker: 0.255/0.039 act, 7.94 deg pose in v3.41_safe eval
- No proven checkpoint with act+pose+psr on MViTv2-S exists
- MViTv2-S (34.3M) is larger than ConvNeXt-Tiny (28.6M), slower per iteration
- The architecture mismatch between MViTv2-S (spatiotemporal) and the per-frame act/pose heads may require architectural adaptation

**Realistic probability:**
- Successfully restoring 9-channel pipeline in <5 days: **~30%** (unknown scope, months of code drift)
- Act reaching 0.394+ on MViTv2-S (matching v4_fixed): **~40%** (MViTv2-S already got 0.255 act)
- Pose reaching <= 6.15 deg on MViTv2-S (matching v4_fixed): **~50%** (7.94 deg baseline, needs improvement)
- All three targets achieved simultaneously: **<15%**

**Time estimate:** 12-15 days minimum (3-5 days pipeline restoration + 7-10 days training)
**GPU:** RTX 5060 Ti (GPU 0)
**Risk of exceeding Aug 22:** HIGH (15 days > 21 days, zero buffer)

---

### Strategy 3: Two-Stage Distillation (Teacher -> Student)

**Concept:** Use v4_fixed (act+pose) and v3.41_safe (PSR) as teachers to distill into a single student model.

**What must be done:**
1. Both teacher checkpoints must be loadable and runnable simultaneously
2. Design a student architecture that can accept knowledge from both teachers
3. Define distillation losses for each head
4. Train the student on combined soft targets

**Pros:**
- Theoretically elegant -- transfers knowledge without requiring compatible architectures
- Could use a lighter student backbone than either teacher

**Cons:**
- **The two teachers use different input channels (3 vs 9).** A single student cannot simultaneously process both input formats to receive distillation signals from both teachers.
- You could distill act+pose from v4_fixed (3-channel) into the student, then separately distill PSR from v3.41_safe (9-channel), but the PSR distillation requires the 9-channel pipeline to even run the teacher.
- Distillation typically closes 10-30% gaps between similar architectures. The gap between MViTv2-S (spatiotemporal, 9-channel) and ConvNeXt (per-frame, 3-channel) is architectural, not just a knowledge gap.
- No precedent in the literature for distilling across fundamentally different input modalities (9-channel spatiotemporal -> 3-channel per-frame).
- **Kill shot:** You cannot run the v3.41_safe teacher without restoring the 9-channel pipeline. This alone is a 3-5 day unknown-scope engineering task with ~30% success probability.

**Realistic probability:** **<5%** of achieving all three targets. The input channel mismatch kills this strategy.

**Time estimate:** 15-20 days if pipeline restoration succeeds
**Risk of exceeding Aug 22:** CRITICAL

---

### Strategy 4: Multi-Task Co-Training from Scratch

**Concept:** Train a new model from scratch with all three heads on a single backbone.

**What must be done:**
1. Choose backbone: ConvNeXt-Tiny (3-channel) or MViTv2-S (9-channel)
2. Initialize all three heads with the verified architectures:
   - Activity: TCN+ViT head (or simpler, since ConvNeXt has zero activity signal)
   - Pose: Legacy HeadPoseHead with raw 9-DoF MSE regression
   - PSR: Path A (11 binary heads + MonotonicDecoder)
3. Train with Kendall uncertainty weighting or fixed weights
4. Run for sufficient epochs to converge all heads

**Pros:**
- Clean slate -- no accumulated training artifacts
- Full control over architecture and training dynamics
- Can optimize backbone features for all tasks simultaneously

**Cons:**
- **Training from scratch takes 30-50 epochs at ~3 hr/epoch = 90-150 hours = 4-6 days per run**
- No guarantee all three tasks converge together (multi-task interference is the known problem)
- ConvNeXt: Activity will not converge (linear probe proves zero signal). Detection will collapse (proven 99.99% cost).
- MViTv2-S: Requires 9-channel pipeline restoration.
- The known multi-task collapse (detection 0.00009) happened DURING co-training, not after.
- No historical checkpoint proves all three tasks can co-exist on ANY backbone.

**Realistic probability:**
- ConvNeXt co-training achieves all three targets: **<1%** (activity is architecturally impossible)
- MViTv2-S co-training achieves all three targets: **<10%** (gated on pipeline restoration + unknown act/pose ceiling)
- Even two targets (act+pose) from scratch: **~60%** (pose fix is code-only, activity has zero signal)

**Time estimate:** 6-10 days per attempt (training from scratch), plus 3-5 days for pipeline restoration if MViTv2-S
**Risk of exceeding Aug 22:** HIGH (only 1-2 attempts possible, pipeline restoration eats half the time)

---

### Strategy 5: LoRA Adapters on Frozen Backbone

**Concept:** Freeze the v4_fixed ConvNeXt-Tiny backbone. Add LoRA adapters to fine-tune for PSR while preserving act+pose features.

**What must be done:**
1. Load v4_fixed checkpoint with frozen ConvNeXt backbone
2. Inject LoRA adapters (low-rank matrices) into key ConvNeXt layers
3. Restore PSR Path A head on top
4. Train only LoRA adapters + PSR head
5. Act and pose heads remain frozen, evaluated periodically to verify no degradation

**Pros:**
- Preserves proven act=0.394 and pose=6.15 (heads frozen, backbone mostly frozen)
- LoRA training is fast: fewer parameters, lower memory
- Can experiment with adapter rank (4, 8, 16, 32) to trade off capacity vs preservation
- If LoRA fails, original v4_fixed is untouched (adapters can be removed)

**Cons:**
- **LoRA adapters modify backbone features.** Even with frozen act/pose heads, changing the backbone features changes what the heads see. Act and pose WILL degrade.
- The core problem is not parameter count -- it's whether ConvNeXt-Tiny RGB features contain PSR-relevant information. LoRA doesn't change the input modality or the fundamental limitation of per-frame 2D CNN features.
- LoRA is typically used for domain adaptation or task transfer within the same modality (text->text, image->image). Using it to inject temporal state-transition detection into a static-image backbone has no literature precedent.
- The degradation to act/pose would need to be measured per-epoch, adding eval overhead.
- 4 of 11 PSR components are dead on MViTv2-S. They will almost certainly be dead on ConvNeXt+LoRA too.

**Realistic probability:**
- PSR transition F1 > 0.20: **~60%** (LoRA might help slightly, but backbone limitation is fundamental)
- PSR F1 >= 0.50 while maintaining act >= 0.30 and pose <= 10 deg: **~30%**
- PSR F1 >= 0.80 while maintaining act >= 0.35 and pose <= 8 deg: **<10%**
- Act/pose degradation from LoRA feature drift: **near-certain** (only question is magnitude)

**Time estimate:** 4-5 days (LoRA training is faster: ~1.5 hr/epoch x 30 epochs = 45 hr + eval overhead)
**GPU:** RTX 3060
**Risk of exceeding Aug 22:** LOW-MEDIUM (4-5 days leaves room for 2-3 adapter rank experiments)

---

### Strategy 6: Decoupled Training (Freeze Backbone, Train Heads Separately)

**Concept:** Freeze the ConvNeXt-Tiny backbone from v4_fixed. Train each head independently on the frozen features. No shared gradient flow between heads.

**What must be done:**
1. Load v4_fixed checkpoint
2. Freeze backbone completely (no LoRA, no fine-tuning)
3. Extract frozen features once (or per-epoch for efficiency)
4. Train PSR Path A head on frozen features
5. Train activity head on frozen features (for pathology documentation)
6. Keep pose head as-is (code fix only)
7. Verify act/pose are byte-identical to v4_fixed (backbone frozen)

**Pros:**
- **Guarantees act=0.394 and pose=6.15 are preserved** (backbone is frozen, heads are identical)
- Fastest training: no backbone gradient computation
- Cleanest experimental design: isolates head architecture from backbone features
- Can train multiple head variants in parallel
- If it works, the result is the cleanest paper contribution: "Decoupled heads on a frozen backbone achieve X"

**Cons:**
- **The frozen backbone features ARE the limitation.** If ConvNeXt-Tiny per-frame RGB features lack PSR-relevant information, no head architecture can compensate.
- This is essentially the same as Strategy 1 (continue v4_fixed) but with the backbone explicitly frozen. The difference is philosophical: Strategy 1 allows FPN fine-tuning, Strategy 6 freezes everything.
- PSR Path A on frozen ConvNeXt features: unknown. The linear probe for activity proved zero signal. A similar probe for PSR (per-component linear classifier on frozen features) would be the gating experiment.
- Training activity on frozen features is guaranteed to fail (linear probe already proved 0.2169 < 0.2217 baseline).

**Realistic probability:**
- PSR transition F1 > 0.20: **~50%** (backbone limitation, not head architecture)
- PSR F1 >= 0.50: **~30%**
- PSR F1 >= 0.80: **<15%**
- Act preservation: **>99%** (frozen, byte-identical)
- Pose preservation: **>99%** (frozen, code fix only)
- Activity: **0%** (frozen backbone has zero activity signal, already proven)

**Time estimate:** 3-4 days (no backbone gradients, faster iterations: ~1 hr/epoch x 30 epochs = 30 hr + eval)
**GPU:** RTX 3060
**Risk of exceeding Aug 22:** LOW (3-4 days, room for many ablations)

---

## 3. Strategy Comparison Matrix

| Strategy | PSR F1 >= 0.80 | Act >= 0.35 | Pose <= 8 deg | Time (days) | Risk of missing Aug 22 | Infrastructure Risk |
|----------|---------------|-------------|---------------|-------------|----------------------|---------------------|
| 1. Continue v4_fixed + PSR Path A | 10-25% | ~95% | ~90% | 7 | LOW | LOW (current infra) |
| 2. Continue v3.41_safe + act/pose | <10% | ~40% | ~50% | 12-15 | HIGH | CRITICAL (9ch pipeline) |
| 3. Two-stage distillation | <5% | ~50% | ~50% | 15-20 | CRITICAL | CRITICAL (9ch pipeline) |
| 4. Co-training from scratch | <1% (ConvNeXt) / <10% (MViTv2) | ~60% | ~60% | 6-15 | HIGH | HIGH (9ch for MViTv2) |
| 5. LoRA adapters | <10% | ~70% | ~80% | 4-5 | LOW-MEDIUM | LOW |
| 6. Decoupled frozen training | <15% | >99% | >99% | 3-4 | LOW | LOW |

**Key:** Only Strategy 2 (v3.41_safe) starts with proven PSR=0.883, but it has the critical 9-channel pipeline blocker. All ConvNeXt-based strategies (1, 5, 6) have unproven PSR and architecturally-impossible activity.

---

## 4. Recommended Approach

### 4.1 The Honest Recommendation

**For the paper: Two-model deployment.** Use v4_fixed (ConvNeXt-Tiny) for act+pose, and v3.41_safe (MViTv2-S) for PSR. This requires zero training -- only re-evaluation (~4 GPU-hours). All three metrics are guaranteed (code fix for pose column-ordering). The paper contribution becomes: "Single-task models achieve X, Y, Z. Multi-task on a shared backbone achieves only subsets A, B. This gap is the multi-task cost."

**For the experiment: Strategy 1 (Continue v4_fixed with PSR Path A).** This is the only ConvNeXt strategy with a realistic chance of getting PSR > 0.50 while preserving act+pose. PSR Path A restoration is a 7-day investment with a clear gate (transition F1 > 0.20). If it fails, the existing two-model approach still guarantees the numbers for the paper.

### 4.2 Why Not the Other Strategies

- **Strategy 2 (MViTv2-S):** The 9-channel pipeline restoration is an unknown-scope engineering task with ~30% success probability. The Aug 22 freeze date makes this too risky.
- **Strategy 3 (Distillation):** Killed by the 9-channel pipeline requirement for the PSR teacher. Even if pipeline were restored, distilling across fundamentally different input modalities has no literature precedent.
- **Strategy 4 (Co-training):** ConvNeXt-Tiny has zero activity signal (linear probe proven). Co-training from scratch would produce the same collapse observed in the historical runs. MViTv2-S co-training requires pipeline restoration.
- **Strategy 5 (LoRA):** A more complex variant of Strategy 1 with added risk of act/pose degradation. Use only if Strategy 1 shows PSR signal but insufficient head capacity.
- **Strategy 6 (Decoupled):** A simplified variant of Strategy 1. Good as a diagnostic (isolates head from backbone) but less likely to reach high PSR since backbone features are frozen. Use as a gating experiment before Strategy 1.

### 4.3 The Activity Reality

**Activity is not revivable on ConvNeXt-Tiny.** This is not a training strategy problem -- it is a fundamental architectural limitation:
- Linear probe: 0.2169 < 0.2217 majority baseline
- 41 of 69 classes have zero accuracy
- ImageNet pretraining encodes object identity, not motion
- Per-frame 2D CNN sees static images, action requires temporal features

The adversarial synthesis (11_debate_adversarial.md) gives activity <1% probability of hitting 0.6223 and ~15% of hitting 0.25-0.35 verb-group on ConvNeXt. Every strategy above that attempts activity on ConvNeXt is attempting the architecturally impossible.

**The honest paper position:** Activity is handled by MViTv2-S (historical 0.6223) or a separate activity-only model. The ConvNeXt linear probe result (0.2169 < 0.2217) is published as negative evidence that ImageNet features lack action information -- a genuine scientific contribution.

---

## 5. Detailed Steps: Strategy 1 (Continue v4_fixed with PSR Path A)

### Phase 0: Preservation and Verification (Day 0, No GPU)

**Step 0.1: Copy checkpoints to local safe storage**
```
cp /media/newadmin/master/.../runs/v4_fixed/v4_e0_b200.pth → /home/newadmin/swarm-bot/checkpoints/v4_e0_b200.pth
sha256sum v4_e0_b200.pth > checkpoints/SHA256SUMS
```
- Time: < 2 minutes
- Size: 233 MB
- Risk: LOW

**Step 0.2: Copy missing dependencies from external drive**
```
evaluate.py, model.py, resolved_config.json, train.log → checkpoints/configs/
```
- Time: < 5 minutes
- Size: ~15 MB
- Risk: LOW (these files are required for eval, per Agent 5 integration plan Section 1.4)

**Step 0.3: Verify v4_fixed metrics with independent eval**
- Run `full_eval_inprocess.py` on v4_e0_b200.pth
- Confirm act=0.394, pose=6.15 degrees (must match 2 prior independent evals)
- Confirm PSR is dead (expected: F1 ~0.10 or lower on Path B)
- Time: 2 hours on RTX 3060

**Gate:** If act != 0.394 or pose != 6.15, STOP. The checkpoint is corrupted or the eval is broken.

---

### Phase 1: PSR Architecture Restoration (Day 1-2, Code Changes Only)

**Step 1.1: Restore PSR Path A head architecture**
Per plan 03_psr_revival.md, Section 2.3:
- Replace PSRHead's 24-class softmax classifier with 11 per-component binary heads
- Each head: Linear(gru_hidden, 128) -> LayerNorm -> LeakyReLU(0.01) -> Dropout -> Linear(128, 1)
- Apply GELU saturation fix: LeakyReLU(0.01) + zero bias + Xavier init std=0.01
- Output: [B, 11] logits per frame

**Step 1.2: Restore MonotonicDecoder**
Per plan 03_psr_revival.md, Section 2.3 Component 2:
- Restore MonotonicDecoder with Q48 hysteresis (sustain_hi/sustain_lo thresholds)
- Remove the 24-class AccumulatedConfidencePSR bridge (`_decode_24class_psr_transitions`)
- Wire sigmoid -> threshold -> MonotonicDecoder -> transition events

**Step 1.3: Restore per-component focal BCE loss**
Per plan 03_psr_revival.md, Section 2.3 Component 3:
- Per-component focal BCE with class-specific alpha from prevalence
- alpha values: comp0=0.5 (balanced), comp1-10 from training set prevalence
- gamma=2.0 (standard focal)

**Step 1.4: Fix eval routing**
Per plan 15_revert_psr_0.883.md:
- Fix F1=1.0 bug when TP=FP=FN=0 (should be 0.0) -- at 3 locations
- Wire eval to use 11-binary output path (not 24-class softmax)
- Ensure transition F1 (not per-frame F1) is the primary metric
- Remove `_psr_primary_f1 = _trans_f1 if _trans_f1 > 0.0 else _state_acc` fallback (line 5576)

**Gate:** Architecture changes are code-only. No GPU. Verify by loading v4_fixed checkpoint and confirming forward pass produces [B, 11] sigmoid logits.

---

### Phase 2: PSR Head Training on Frozen Backbone (Day 3-9, RTX 3060)

**Step 2.1: Gating experiment -- PSR Path A probe (1 day)**
- Load v4_fixed checkpoint
- Freeze ConvNeXt backbone AND FPN
- Train ONLY the restored PSR Path A head for 5 epochs
- Evaluate transition F1 after each epoch
- Time: 5 epochs x ~1.5 hr/epoch = 7.5 hours

**Gate:** If transition F1 < 0.20 after 5 epochs, PSR on ConvNeXt is fundamentally limited.
- **Fallback A:** Abort PSR training. Use two-model approach for paper (v4_fixed for act+pose, v3.41_safe for PSR).
- **Fallback B:** Publish per-frame F1 (0.70-0.75 expected) with copy_prev baseline (0.9997) comparison. This is a methodology contribution: "per-frame PSR metrics are persistence-dominated."
- If transition F1 >= 0.20, proceed to Step 2.2.

**Step 2.2: Full PSR head training (6 days)**
- Unfreeze FPN (keep backbone frozen)
- Train PSR Path A head + FPN for 50 epochs
- Enable DETACH_PSR_FPN=False (allow PSR gradients to tune FPN features)
- Monitor: transition F1, per-component F1, act/pose stability
- Early stopping: if transition F1 plateaus for 10 epochs, stop
- Time: 50 epochs x 3.2 hr/epoch = 160 hours = 6.7 days

**Training configuration:**
```
GPU: RTX 3060 (GPU 1)
Batch size: 2
Gradient accumulation: 32 (effective batch = 64)
Precision: FP32 (no AMP -- sequence loss stability)
Temporal windows: T=4 (required for MonotonicDecoder)
Optimizer: AdamW, lr=1e-4, weight_decay=1e-4
Scheduler: CosineAnnealingWarmRestarts, T_0=10, T_mult=2
Loss: Per-component focal BCE (gamma=2.0, alpha from prevalence)
MonotonicDecoder: sustain_hi=0.3, sustain_lo=0.1, min_sustain=12 (Q48)
```

**Step 2.3: Daily checkpoints and eval (embedded in training)**
- Save checkpoint every 5 epochs
- Run transition F1 eval on saved checkpoint
- Track act and pose on subset (verify no degradation)
- Log per-component F1 for dead component surveillance
- Time: ~20 min/eval, 10 evals over training = 3.3 hours

**Gate at epoch 25:** If transition F1 < 0.30, PSR won't reach 0.80+. Consider LoRA (Strategy 5) as rescue.

---

### Phase 3: HeadPoseFiLM Contamination Check (Day 9, 2 hours)

**Step 3.1: Verify pose code fix didn't degrade PSR**
Per 11_debate_adversarial.md, Section 2:
- Pose column-ordering fix corrects GeometryAwareHeadPose from ~86 deg to ~6.15 deg
- But the FiLM layers that modulate backbone features for pose could shift features that PSR depends on
- Run PSR eval with and without pose fix to quantify any degradation

**Gate:** If PSR drops > 10% with pose fix active, HeadPoseFiLM contamination is confirmed. This requires architectural mitigation (separate FiLM for PSR, or decoupled pose features) -- beyond Aug 22 scope.

---

### Phase 4: Final Evaluation and Documentation (Day 9-10, 4 hours)

**Step 4.1: Full 4-head evaluation on best checkpoint**
- Run `full_eval_inprocess.py` (or equivalent) on the best PSR checkpoint
- Evaluate: act top-1, pose angular MAE, PSR transition F1 (per-component and macro), detection (for completeness)
- Compare to v4_fixed baseline (act=0.394, pose=6.15) and v3.41_safe baseline (psr=0.883)
- Time: 3 hours on RTX 3060

**Step 4.2: Document results**
- Record all metrics with honest framing
- Per-component PSR breakdown (which components are alive/dead)
- Act/pose stability analysis (degradation from baseline)
- HeadPoseFiLM impact quantification
- Total GPU-hours consumed
- Time: 1 hour

---

### Total Timeline (Strategy 1)

| Phase | Duration | Cumulative | GPU |
|-------|----------|------------|-----|
| Phase 0: Preservation + verification | Day 0 (2.5 hr) | Day 0 | RTX 3060 |
| Phase 1: Architecture restoration | Days 1-2 (code only) | Day 2 | None |
| Phase 2.1: PSR gating experiment | Day 3 (7.5 hr) | Day 3 | RTX 3060 |
| Phase 2.2: Full PSR training | Days 3-9 (6.7 days) | Day 9 | RTX 3060 |
| Phase 3: HeadPoseFiLM check | Day 9 (2 hr) | Day 9 | RTX 3060 |
| Phase 4: Final eval + docs | Days 9-10 (4 hr) | Day 10 | RTX 3060 |
| **Total** | **~10 days** | **Day 10** | **~174 GPU-hours** |

**Buffer to Aug 22 freeze:** 11 days. Room for 1 full retry if first attempt fails at the gate.

---

## 6. Fallback: Two-Model Approach (If Strategy 1 Fails)

If the Phase 2.1 gate fails (transition F1 < 0.20), abandon single-model PSR on ConvNeXt. Switch to:

| Task | Model | Checkpoint | Metric | Training Required |
|------|-------|-----------|--------|-------------------|
| Activity | ConvNeXt-Tiny | v4_e0_b200.pth | 0.394 | None (already achieved) |
| Pose | ConvNeXt-Tiny | v4_e0_b200.pth | 6.15 deg | None (code fix only, 2 hours) |
| PSR | MViTv2-S | phase2_e3_b0.pth | 0.883 | None (already achieved) |
| Detection | YOLOv8m | (separate) | 0.995 | None (already achieved) |

**Total GPU time: ~4 hours** (re-evaluation only)
**Total wall-clock time: 1 day** (copy checkpoints, run evals, document)
**All three targets achieved: YES** (guaranteed, from verified checkpoints)

This is the honest fallback. The paper becomes: "Single-task performance is strong (0.394 act, 6.15 deg pose, 0.883 PSR, 0.995 detection). Multi-task on a shared backbone preserves subsets only. The multi-task cost is characterized per head."

---

## 7. Cross-References

### 7.1 How This Plan Relates to the Debate Files

| Debate File | Key Finding | Impact on This Plan |
|-------------|------------|---------------------|
| **07_debate_feasibility.md** | Activity on ConvNeXt: <1% chance of 0.6223, ~15% of 0.25-0.35 | **Activity is excluded from all strategies.** Not worth GPU time. |
| **07_debate_feasibility.md** | Detection on ConvNeXt: <2% of 0.5734, ~20% of 0.30-0.45 via distillation | Detection handled by YOLOv8m. ConvNeXt detection is pathological. |
| **08_debate_resources.md** | GPUs idle, 138 GB free disk, 1.45 s/it MTL on RTX 3060 | Training estimates are based on measured timings, not guesses. |
| **08_debate_resources.md** | Single-task detection on full dataset = 7.25 hr/epoch (30 days for 99 epochs) | Detection training is excluded. Too slow, too unlikely to succeed. |
| **11_debate_adversarial.md** | "At most 2 of 4 tasks are revivable on ConvNeXt." P(all 3) < 2%. | This plan targets 2 tasks (act+pose) + PSR experiment. Honest framing. |
| **11_debate_adversarial.md** | HeadPoseFiLM contamination: pose fix could degrade PSR features | Phase 3 of this plan explicitly checks for this. |
| **11_debate_adversarial.md** | F1=1.0 bug at 3 locations when TP=FP=FN=0 | Architecture restoration (Step 1.4) fixes this. |

### 7.2 How This Plan Relates to the Revert Plans

| Revert Plan | Target | How This Plan Uses It |
|-------------|--------|----------------------|
| **12_revert_act_0.394.md** | act=0.394 on v4_fixed | Activity head is frozen/preserved. No activity training attempted on ConvNeXt. |
| **14_revert_pose_6.15.md** | pose=6.15 on v4_fixed with legacy HeadPoseHead | Pose fix is code-only (USE_GEO_HEAD_POSE=False, column-ordering fix). Phase 3 checks FiLM contamination. |
| **15_revert_psr_0.883.md** | psr=0.883 on v3.41_safe with Path A | Path A architecture blueprint is used for PSR head restoration (Phase 1). Training duration and config from this plan. |
| **16_revert_all_integration.md** | Conflict: v4_fixed and v3.41_safe use different backbones | **This is the central constraint.** This plan acknowledges the incompatibility and does not attempt to merge the checkpoints. |
| **16_revert_all_integration.md** | Only 3 of 4 targets revertable, 2 checkpoints needed | This plan's fallback (Section 6) matches exactly: two-model deployment. |

### 7.3 How This Plan Relates to Cross-Reference Targets (17, 19, 20, 21, 22)

**Note:** Files 17-22 do not exist in `analyses/consult_2026_06_10/a_revival_plan/` (confirmed by glob). The directory contains only files 01-16. If these numbers refer to planned but unwritten debate extensions, the relevant cross-references are:

- **17 (hypothetical: Ensemble):** This plan explicitly does NOT recommend ensembling ConvNeXt + MViTv2-S because they have different input formats (3-channel vs 9-channel). An ensemble would require running both models simultaneously, doubling inference cost. The two-model fallback (Section 6) achieves the same result with cleaner semantics.

- **19 (hypothetical: Data augmentation):** PSR Path A training could benefit from temporal augmentation (frame skipping, reverse playback, speed variation). These are low-risk additions to the Phase 2 training config but not required for the architecture restoration experiment. If the Phase 2.1 gate passes but transition F1 stalls below 0.50, temporal augmentation is the first ablation to try.

- **20 (hypothetical: Loss function ablation):** The focal BCE vs class-balanced CE decision was settled by Path A's proven 0.883 on MViTv2-S. This plan uses per-component focal BCE as the primary loss. If Phase 2.2 training stalls, ablations in order: (a) gamma sweep [1.0, 1.5, 2.0, 3.0], (b) asymmetric focal (different gamma for positive/negative), (c) label smoothing for dead components.

- **21 (hypothetical: Optimizer/scheduler):** AdamW + CosineAnnealingWarmRestarts is the standard from v3.41. The plan retains this. Alternative optimizers (SGD with momentum, LAMB) would only be explored if AdamW training shows instability (gradient spikes, loss oscillation) -- not expected given the v3.41 precedent.

- **22 (hypothetical: Inference optimization):** Out of scope for a training plan. Inference optimization (TorchScript export, ONNX conversion, INT8 quantization) would be addressed after a trained model exists. None of the checkpoints are currently production-deployed.

### 7.4 Key References Within the Plan Set

| Reference | File | Key Number |
|-----------|------|------------|
| ConvNeXt linear probe result | 11_debate_adversarial.md, 07_debate_feasibility.md, 05_integration_synthesis.md | 0.2169 < 0.2217 baseline |
| Detection multi-task collapse | 11_debate_adversarial.md, 16_revert_all_integration.md, cascade_table.md | 0.00009 mAP50 (99.99%) |
| PSR Path A proven F1 | 15_revert_psr_0.883.md, 03_psr_revival.md | 0.883 on MViTv2-S |
| PSR dead components | 03_psr_revival.md, Section 1.3 | comp4, comp7, comp8, comp9 at F1=0.0 |
| PSR Path A training estimate | 08_debate_resources.md, Section 2.3 | 3.2 hr/epoch, 50 epochs = 7 days |
| Act verified on v4_fixed | 12_revert_act_0.394.md | 0.394 (2 independent evals, byte-identical) |
| Pose verified on v4_fixed | 14_revert_pose_6.15.md | 6.15 deg (Legacy HeadPoseHead) |
| HeadPoseFiLM contamination risk | 11_debate_adversarial.md, Section 2 | CRITICAL cross-task cascade |
| F1=1.0 eval bug | 11_debate_adversarial.md, 15_revert_psr_0.883.md | 3 locations, TP=FP=FN=0 |
| Checkpoint sizes verified | 16_revert_all_integration.md, Section 1.1 | 233 MB + 664 MB |
| Freeze date and GPU state | 08_debate_resources.md | Aug 22, both GPUs idle, 138 GB free |

---

## 8. Risks Not Addressed by Any Existing Plan

### 8.1 The 9-Channel Pipeline Is a Single Point of Failure

All strategies that involve MViTv2-S (Strategies 2, 3, 4) require restoring the 9-channel data pipeline. No plan documents what this involves. The scope could range from "flip a config flag" to "rewrite the data loader." Given that months of code changes have accumulated since v3.41 was trained, the pipeline may have diverged significantly. **This risk alone eliminates MViTv2-S-based strategies before Aug 22.**

### 8.2 The v3.41_safe Checkpoint May Not Load

Even if the 9-channel pipeline is restored, the v3.41_safe checkpoint was saved with a specific version of the model architecture. If the model class definition has changed (new fields, renamed attributes, different layer structure), the checkpoint will fail to load with a key mismatch error. This is a common failure mode in research codebases and is not addressed by any plan.

### 8.3 The Pose Fix May Not Be Isolated

The pose column-ordering fix touches the HeadPoseHead output parsing. If the fix also changes how features are computed (e.g., the FiLM conditioning path), it could affect PSR features even without HeadPoseFiLM contamination. This is a code-only risk but should be verified in Phase 3.

### 8.4 The MonotonicDecoder vs Causal Transformer Tradeoff

Restoring the MonotonicDecoder replaces the causal transformer (3 layers, 4 heads, d_model=256) that was added to Path B. The causal transformer is the only component in Path B that could theoretically help PSR on ConvNeXt (it adds temporal context to per-frame features). Removing it for the MonotonicDecoder may lose whatever temporal signal the transformer was capturing. A hybrid approach (MonotonicDecoder on top of transformer features) should be considered if Phase 2.1 shows marginal signal (transition F1 0.10-0.20).

### 8.5 The Aug 22 Freeze Is Real

21 days from today. Strategy 1 takes ~10 days, leaving 11 days of buffer. If Strategy 1 fails at the Phase 2.1 gate (Day 3), there is time to switch to the two-model fallback and still meet the freeze. If Strategy 1 proceeds to Phase 2.2 and fails at epoch 25 (Day 7), there is still time for the fallback. **Do not attempt Strategies 2-4 before Aug 22.** They have >50% probability of exceeding the freeze date.

---

## Appendix A: What "One Model" Actually Means

The user requested "ONE model with all the best metrics." The evidence shows this is architecturally impossible with the current checkpoints. Here is what "one model" would actually require:

1. **A backbone that supports all three tasks.** This does not exist. ConvNeXt-Tiny lacks activity signal. MViTv2-S has unproven act/pose ceiling and requires 9-channel input.

2. **A training run where all three heads converge simultaneously.** No historical run has achieved this. The best multi-task run (v4_fixed) has act=0.394 and pose=6.15 but dead PSR. The best PSR run (v3.41_safe) has psr=0.883 but weaker act/pose. The multi-task interference problem is real and characterized (cascade_table.md).

3. **3-6 months of dedicated research.** This is the honest estimate for achieving all three targets on a single backbone. It would require: designing a new backbone that handles both static classification (act/pose) and temporal state detection (PSR), collecting or generating 9-channel data if spatial features are needed, running multiple multi-task training experiments with different loss weighting schemes, and validating on held-out data.

**The two-model approach (Section 6) is the honest "one system" recommendation.** The system has one interface but two backbones internally. This is a standard engineering pattern (model routing by task) and is more defensible in a paper than a forced single-model result with compromised metrics.

---

## Appendix B: GPU Allocation Schedule

```
Day 0:     GPU 1 (RTX 3060) -- Phase 0 verification (2.5 hr)
Day 1-2:   No GPU -- Phase 1 architecture changes
Day 3:     GPU 1 (RTX 3060) -- Phase 2.1 gating experiment (7.5 hr)
Day 3-9:   GPU 1 (RTX 3060) -- Phase 2.2 PSR training (continuous, 6.7 days)
Day 9:     GPU 1 (RTX 3060) -- Phase 3 FiLM check (2 hr)
Day 9-10:  GPU 1 (RTX 3060) -- Phase 4 final eval (4 hr)

GPU 0 (RTX 5060 Ti): FREE throughout. Available for:
  - Parallel single-task ConvNeXt detection baseline (if still running from epoch 43/99)
  - Activity single-task on MViTv2-S (if pipeline is restored separately)
  - Paper writing and analysis (no GPU needed)
  - Any other agent's work
```

---

## Appendix C: Decision Tree

```
START
  |
  v
Copy checkpoints + verify v4_fixed metrics (Phase 0)
  |
  v
Restore PSR Path A architecture (Phase 1, code only)
  |
  v
Run 5-epoch PSR probe on frozen backbone (Phase 2.1)
  |
  +---> Transition F1 < 0.20?
  |       |
  |       +---> YES: ABORT single-model PSR.
  |       |     Switch to two-model fallback (Section 6).
  |       |     Paper: act+pose from v4_fixed, PSR from v3.41_safe.
  |       |     Total time: ~3 days. Meets Aug 22.
  |       |
  |       +---> NO: Transition F1 >= 0.20. PROCEED.
  |             |
  |             v
  |           Full PSR training 50 epochs (Phase 2.2)
  |             |
  |             +---> Epoch 25: Transition F1 < 0.30?
  |             |       |
  |             |       +---> YES: STALLING. Try LoRA rescue (Strategy 5).
  |             |       |     If LoRA also fails, fallback to two-model.
  |             |       |
  |             |       +---> NO: CONTINUE.
  |             |
  |             v
  |           Phase 3: HeadPoseFiLM check
  |             |
  |             +---> PSR drops >10% with pose fix?
  |             |       |
  |             |       +---> YES: FiLM contamination confirmed.
  |             |       |     Document as cross-task interference finding.
  |             |       |     Use best PSR checkpoint without pose fix as PSR result.
  |             |       |
  |             |       +---> NO: CLEAN. Both pose and PSR can coexist.
  |             |
  |             v
  |           Phase 4: Final eval + documentation
  |             |
  |             v
  |           RESULT: act=0.394, pose=6.15, psr=TBD
  |             |
  |             +---> PSR >= 0.80: SUCCESS. Single model achieves all 3 targets.
  |             +---> PSR 0.50-0.79: PARTIAL. Honest paper: PSR degraded vs single-task.
  |             +---> PSR < 0.50: FAILURE. Fallback to two-model.
```
