# Agent 5: Integration & Debate Synthesis

**Date:** 2026-08-01
**Role:** Integration & Debate Specialist (Agent 5 of 5-agent debate team)
**Inputs:** AAIML planning corpus (files 130, 132, 133, 134, 135, 145), cascade analysis, training logs, true-signal analysis, decoder-vs-head comparison, D4 retune results
**Output:** Single coherent revival execution plan resolving all inter-plan conflicts

**Note on inputs:** The 4 agent-specific planning files (01-04) do not yet exist in `a_revival_plan/`. This synthesis treats the AAIML planning corpus as de facto agent plans: Agent 1 (PSR, plan 130 P1.1 + debate 2.3), Agent 2 (Detection, plan 130 P2.1/P1.3 + strategy 5), Agent 3 (Activity, plan 130 P1.4 + strategy 2), and Agent 4 (Integrity/Diagnostic, plan 132/135). The 52 days between the last AAIML document (July 7) and today (August 1) have yielded critical ground-truth results that are incorporated.

---

## 1. Conflict Matrix

### 1.1 Which plans need each other? Which are independent?

```
Agent 1 (PSR repair)  <-- NEEDS --> Agent 4 (diagnostics)
       |                      |
       |   CONFLICTS          |   CONFLICTS
       v                      v
Agent 2 (Detection KD)    Agent 3 (TCN+ViT activity)
       |                      |
       +------- SHARES -------+
            GPU 0 (RTX 5060 Ti)
```

| Plan A | Plan B | Relationship | Evidence | Verdict |
|--------|--------|-------------|----------|---------|
| Agent 1 (PSR head repair + fixed weights) | Agent 4 (diagnostic-first) | **Dependency** — Agent 4's diagnostics must gate Agent 1's training investment | PSR activation diagnostic (reported in `psr_repair_training/status.md`) confirmed the GELU saturation hypothesis from debate 2.3/Opus Q1. The repair (LeakyReLU + zero bias) shows post_gelu mean jumping from -130 to +384-640 on sequence frames. This proves the head WAS dead — exactly what Agent 4 argued must be verified first. | **Agent 4 is correct.** Diagnostics save 2+ wasted GPU-days by proving the failure mechanism before investing in training. |
| Agent 1 (Kendall fixed weights) | Agent 1 (PSR head repair) | **Sequencing conflict within same plan** — Plan 130 P1.1 runs fixed weights concurrently with head. Opus Q1 proved they must be sequential. | Plan 130 P1.1 says "Train PSR with KENDALL_FIXED_WEIGHTS=1...head repair as afterthought." Opus ruling: log_var_psr=-0.04 gives precision ~1.04 — a 4-8% down-weight cannot produce exactly-zero RMS gradients on all 11 sub-heads. The zero-gradient is a dead forward path (ReLU saturation at `psr_transition.py:216-237`), not a loss-weighting problem. | **Opus Q1 is correct.** The plan 130 sequence is inverted. Fix the ReLU first, THEN test Kendall fixed weights as an ablation. Running fixed weights on a dead head proves nothing. |
| Agent 2 (detection distillation) | Agent 3 (TCN+ViT activity) | **Resource conflict** — Both require RTX 5060 Ti (GPU 0) for multi-day training | Single-task ConvNeXt-Tiny detection (epoch 43/99, ~7 days remaining on RTX 5060 Ti) already occupies GPU 0. PSR repair occupies GPU 1 (RTX 3060). Both distillation and TCN+ViT need the 5060 Ti. | **Must be serialized.** Detection distillation first (it's a known-working technique: YOLOv8m teacher at 0.995 exists). TCN+ViT second, gated on activity linear probe result. |
| Agent 2 (detection ratio framing) | Agent 4 (honest disclosures) | **Agreement** — Both endorse "36% of ceiling, 64% multi-task cost" framing | File 134 confirms 0.358/0.995 = 36% of ceiling. File 132/135 endorse cost framing. No conflict. | **Both correct.** Adopt ratio framing. |
| Agent 3 (TCN+ViT activity training) | Agent 4 (linear probe first) | **Direct conflict** — Agent 3 wants to train TCN+ViT immediately (plan 130 P1.4, "2-3 days compute"). Agent 4 demands linear probe as gate (file 132 Q4, "probe first, then decide") | Linear probe results (from `145_PAPER_NARRATIVE_V3.md`): "A linear probe on frozen ConvNeXt features achieves 0.2169 top-1 accuracy, essentially matching the majority-class baseline of 0.2217 (always predict class 8). The frozen backbone encodes no activity-relevant information." | **Agent 4 is decisively correct.** The linear probe proves the ConvNeXt backbone has zero activity signal. TCN+ViT on the same backbone is dead on arrival. Agent 3's plan would waste 2-3 GPU-days. The TCN+ViT must run on a DIFFERENT backbone (e.g., MViTv2-S pretrained). |
| Agent 2 (D3 full eval NaN fix) | Agent 4 (results freeze protocol) | **Dependency** — Full eval numbers are needed before any freeze can happen. | Plan 130 P1.3 (in-process eval, `EVAL_MAX_BATCHES=0`) has been attempted. The D3 38k full-eval result is now known: mAP50=0.00009 (effectively zero). This was confirmed in `multi_task_cascade/analysis.md`. | **This conflict is resolved by ground truth.** The full eval works (or a number exists). The result is catastrophic (0.00009) but it IS the number. Freeze it. |
| Agent 1 (PSR F1 target 0.83) | Reality (true-signal analysis) | **Plan-reality gap** — Agent 1 expects PSR F1 from 0.7499 to ~0.83. True-signal analysis reveals both 0.7013 (global) and 0.7499 (per-comp) are BELOW the copy_prev baseline of 0.9997. | `psr_true_signal/true_signal_analysis.md`: "The copy_prev baseline achieves 0.9997 because assembly states are nearly constant from frame to frame... The model's thresholded sigmoid outputs are less reliable than simple persistence." | **Agent 1's target is meaningless in the current metric.** Per-frame F1 is dominated by label persistence. Transition F1 (currently 0.00 for both head and decoder, per `psr_decoder_vs_head/recommendation.md`) is the correct metric. The 0.83 target should use transition F1, not per-frame F1. |
| Agent 1/2/3 (multi-head revival) | Agent 4 (single-head salvage) | **Strategic divergence** — Agents 1-3 try to fix all heads. Agent 4's "transparent pathology" narrative (file 145) accepts that detection and activity heads will NOT recover on the current ConvNeXt backbone. | `multi_task_cascade/cascade_table.md`: detection collapses 99.99%, activity collapses 96.2%. PSR degrades only 11.1%. Head pose actually improves (+8.9%). The bimodal degradation pattern means the backbone is selective about what it supports. | **Agent 4's framing is the honest one.** Revival should target PSR + Head Pose on the shared ConvNeXt backbone, with detection and activity handled by separate single-task models. A 2-head revival is achievable; a 4-head revival on one backbone is not. |

### 1.2 Independent work (parallelizable)

| Task | GPU | Can run with |
|------|-----|-------------|
| PSR head repair training (ongoing) | RTX 3060 (GPU 1) | Anything not on GPU 1 |
| Single-task ConvNeXt detection training (ongoing) | RTX 5060 Ti (GPU 0) | PSR repair (different GPU) |
| Null-model POS baselines | CPU (cached logits) | Everything |
| Transition-F1 re-evaluation | CPU (cached logits) | Everything |
| Per-recording up-vector breakdown | CPU (cached logits) | Everything |
| LOO-CV threshold stability | RTX 3060 (if GPU 0 busy) | Before PSR repair finishes |
| Paper writing (P4.1-P4.4) | None | Everything |

---

## 2. Critical Path

### 2.1 What must be done first (sequential dependencies)

```
STEP 0 (COMPLETED, Jul 7): Diagnostic phase
  [DONE] PSR head activation diagnostic (confirmed GELU saturation)
  [DONE] Activity linear probe (confirmed zero backbone signal: 0.2169 vs 0.2217 baseline)
  [DONE] Null-model POS baselines (copy_prev = 0.9997, model = 0.7013)
  [DONE] D4 threshold re-tune (YOLOv8m → decoder: F1 rose from 0.00 to 0.07 — marginal)
  [DONE] Transition-F1 on cached logits (both head and decoder = near-zero)
  [DONE] True-signal analysis (per-frame F1 dominated by persistence)

STEP 1 (IN PROGRESS): Head repair + single-task baselines
  [IN PROGRESS] PSR head repair (LeakyReLU + zero bias, RTX 3060, from epoch 18)
      Status: Epoch 24/100 at Jul 7. Estimated completion: ~Aug 1-2.
      Key metric: transition F1 after repair MUST be > 0 to justify further PSR work.
  [IN PROGRESS] Single-task ConvNeXt-Tiny detection on D3 (RTX 5060 Ti, from epoch 18)
      Status: Epoch 43/99 at Jul 7. Estimated completion: ~Jul 14.
      Purpose: Isolate dataset effect (D3 vs D1R) from multi-task effect for detection.

STEP 2 (GATED): PSR transition-F1 validation
  Prerequisite: STEP 1 PSR repair completes with transition F1 > 0
  Action: Re-run decoder-vs-head comparison on repaired checkpoint
  Decision gate: If transition F1 < 0.20, PSR head is fundamentally limited on ConvNeXt.
    Fallback: Publish per-frame F1 (0.70-0.75) with honest persistence-baseline comparison.
    If transition F1 >= 0.20, proceed to STEP 3 KENDALL_FIXED_WEIGHTS ablation.

STEP 3 (GATED): KENDALL_FIXED_WEIGHTS ablation
  Prerequisite: STEP 2 transition F1 >= 0.20
  Action: Launch training with KENDALL_FIXED_WEIGHTS=1 env var from repaired checkpoint.
  Duration: 2-3 days on RTX 3060
  Purpose: Prove/disprove whether Kendall uncertainty weighting hurts PSR.
  Note: Opus Q1 argues it doesn't — this is a NEGATIVE RESULT experiment.
    Even if Kendall has no effect, the ablation is publishable.

STEP 4 (GATED): Knowledge distillation for detection
  Prerequisite: STEP 1 single-task detection completes (gives D3 single-task baseline)
  Action: YOLOv8m teacher → ConvNeXt-Tiny student distillation on detection only.
  Duration: 5 days on RTX 5060 Ti
  Decision gate: If single-task ConvNeXt on D3 achieves mAP > 0.5, distillation is unnecessary
    (the bottleneck was multi-task interference, not backbone capacity).
    If single-task ConvNeXt on D3 achieves mAP < 0.3, distillation may help but is unlikely
    to close the 0.995-to-0.3 gap (the backbone is the bottleneck).

STEP 5 (GATED): TCN+ViT activity head
  Prerequisite: Activity linear probe already showed zero backbone signal (STEP 0).
  Decision: **TCN+ViT on ConvNeXt-Tiny is DEAD ON ARRIVAL.**
  Alternative: Train TCN+ViT on MViTv2-S pretrained backbone (plan 130 P5.1).
  This is a new model, not a head repair. Requires:
    - Kinetics-400 pretrained MViTv2-S weights
    - 16-frame clip sampling from IndustReal
    - 5-7 days on RTX 5060 Ti
  Priority: LOW. Activity is the farthest from SOTA (gap = 0.5984 top-1).

STEP 6: Results freeze
  Date: End of Week 4 after STEP 1 completion (approximately Aug 28, 2026).
  All reported numbers must trace to a specific freeze checkpoint (commit hash + config hash).
  No more training after freeze date. Any incomplete experiment is "ongoing work."
```

### 2.2 Execution order diagram

```
Week 1 (Aug 1-7): Complete in-flight training
  RTX 5060 Ti: Finish single-task ConvNeXt detection (epochs 44-99, ~7 days)
  RTX 3060:   Finish PSR head repair (epochs 25-100, ~9 days remaining at Jul 7)
               → If repair completes earlier, evaluate transition F1 immediately

Week 2 (Aug 8-14): Transition-F1 validation + Kendall ablation
  RTX 3060:   Evaluate PSR repair checkpoint → compute transition F1
               IF transition F1 >= 0.20: Launch KENDALL_FIXED_WEIGHTS ablation (2-3 days)
               IF transition F1 < 0.20: PSR revival FAILS → salvage analysis
  RTX 5060 Ti: Evaluate single-task detection checkpoint → compute mAP on D3
               Run null-model POS baselines, per-recording breakdowns (CPU)
               Paper writing: P4.1-P4.4 (disclosures, naming, reframing)

Week 3 (Aug 15-21): Detection distillation (IF gated)
  Prerequisite: Single-task D3 detection mAP < 0.5 AND PSR revival succeeding
  RTX 5060 Ti: Implement + train YOLOv8m → ConvNeXt distillation (5 days)
  RTX 3060:   LOO-CV PSR threshold stability (1-2 days, CPU-friendly)

Week 4 (Aug 22-28): Evaluation + freeze
  Re-run ALL reported evals against freeze checkpoint
  Commit all metrics.json, eval logs, SOTA_STATUS.md
  Freeze paper numbers — no more training
```

---

## 3. Resource Allocation

### 3.1 GPU allocation

| GPU | VRAM | Current occupant | ETA to free | Next assignment | Priority |
|-----|------|-----------------|-------------|-----------------|----------|
| RTX 5060 Ti (GPU 0) | 16 GB | Single-task ConvNeXt-Tiny detection (epoch 43/99) | ~Aug 7 | Detection distillation OR TCN+ViT evaluation | P2 |
| RTX 3060 (GPU 1) | 12 GB | PSR head repair training (epoch 24/100) | ~Aug 7 | PSR transition-F1 eval → Kendall ablation | P1 |

**Constraint:** Only one training run per GPU at a time. With batch_size=2 and grad_accum=16 (effective batch 32), memory is tight. RTX 5060 Ti uses ~5 GB for single-task detection (can fit distillation with teacher in eval mode). RTX 3060 uses ~3.9 GB for PSR repair (room for LOO-CV eval sweeps).

### 3.2 Batch size configuration

| Experiment | batch_size | grad_accum | effective_batch | GPU | Notes |
|-----------|------------|------------|-----------------|-----|-------|
| PSR repair | 2 | 16 | 32 | RTX 3060 | Current config, stable at 3.9 GB VRAM |
| Single-task detection | 2 | 16 | 32 | RTX 5060 Ti | Current config, stable at 5.0 GB VRAM |
| Kendall ablation | 2 | 16 | 32 | RTX 3060 | Same as repair — no change needed |
| Detection distillation | 2 | 16 | 32 | RTX 5060 Ti | +YOLOv8m in eval mode (~2 GB extra) — monitor for OOM |
| TCN+ViT (16 frames) | 1 | 32 | 32 | RTX 5060 Ti | 16 frames at batch=2 would OOM. Reduce to batch=1, double grad_accum |
| MViTv2-S activity (stretch) | 1 | 32 | 32 | RTX 5060 Ti | 3D conv memory — batch=1 minimum |

**OOM risk:** 4 CUDA crashes have occurred. Plan 130 acknowledges this (batch 2 works, batch 3/4/5 cause crashes). All training MUST use batch_size=2 (or 1 for temporal models). Mitigation: `OMP_NUM_THREADS=4` env var, vm.overcommit=2, OOM killer tuned.

### 3.3 Checkpoint inventory

| Checkpoint | Size | Architecture | Epoch | Usable for |
|-----------|------|-------------|-------|-----------|
| `crash_recovery.pth` (benchmark dir) | ~670 MB | ConvNeXt-Tiny, 69-class activity | 18 | PSR repair resume, Kendall ablation, all multi-task evals |
| `best.pth` (rf_stages dir) | ~670 MB | ConvNeXt-Tiny, 75-class activity | 18 (promoted at epoch 11 via broken metric) | **DO NOT USE** — AC-1 contamination. Epoch 11 was promoted by a broken metric. |
| `d1r/weights/best.pt` | ~50 MB | YOLOv8m | 25 | Detection teacher for distillation |
| PSR repair checkpoint | ~670 MB | ConvNeXt-Tiny (LeakyReLU) | 24+ | PSR transition-F1 eval, next-stage training |

**Critical:** The epoch-11 vs epoch-18 checkpoint confusion (AC-1) contaminated prior SOTA claims. Adopt Q10's freeze protocol: every number in the paper must trace to a specific checkpoint identified by commit hash + config hash.

---

## 4. Time Budget

### 4.1 Wall-clock time to reach all 4 targets

| Target | Current | Goal | Required step | Optimistic (days) | Pessimistic (days) | Most likely (days) |
|--------|---------|------|---------------|-------------------|-------------------|-------------------|
| PSR transition F1 | 0.00 | >= 0.20 | Repair training (already running) + eval | 7 | 14 | 10 |
| PSR transition F1 | >= 0.20 | >= 0.50 | Kendall ablation (2-3 days) | 10 | 21 | 14 |
| Detection mAP50 (multi-task ConvNeXt) | 0.00009 | >= 0.30 | Single-task baseline first (7 days) → if bottleneck is multi-task, distillation (5 days) | 0 (abandon multi-task detection) | 14 | 0 (abandon) |
| Head pose up-vector resolved | 26.20/7.78 | median+IQR per-recording | Per-recording breakdown (CPU, 1 day) | 1 | 2 | 1 |
| Activity top-1 | 0.0236 | >= 0.10 | MViTv2-S pretrained backbone (5-7 days) OR abandon | 7 | 14 | Abandon on ConvNeXt |
| **TOTAL (all 4 heads on one backbone)** | — | — | — | N/A | N/A | **IMPOSSIBLE** |

### 4.2 Realistic time budget (2-head revival: PSR + Head Pose)

```
Phase 1 (already in-flight):    0 days  (completes ~Aug 7, 2026)
  PSR repair finishing:         ~7 days from Jul 7
  Single-task detection eval:   ~7 days from Jul 7

Phase 2 (PSR validation):      3-5 days (Aug 7-12, 2026)
  Transition-F1 eval:           1 day
  Kendall ablation:             2-3 days
  LOO-CV threshold stability:   1 day (parallel)

Phase 3 (Detection decision):  0-5 days (Aug 12-17, 2026)
  IF single-task ConvNeXt D3 mAP > 0.5: skip distillation
  IF < 0.5: distillation (5 days)

Phase 4 (Freeze + write):      5 days (Aug 17-22, 2026)
  Re-run all evals:             2 days
  Audit + commit artifacts:     1 day
  Paper writing (P4.1-P4.4):    2 days

TOTAL WALL CLOCK: 21-27 days from July 7 ≈ Aug 1-7, 2026 (already past)
  → Realistic completion: Aug 22, 2026
  → With current date Aug 1: 21 days remaining
```

### 4.3 What the time budget excludes

- **4-head revival on one backbone:** Not achievable. Detection collapses 99.99%, activity collapses 96.2%. These are architectural failures, not training issues.
- **Activity SOTA (0.622):** Requires MViTv2-S or VideoMAE backbone with Kinetics-400 pretraining. This is a new project (1-2 months), not a revival.
- **Detection SOTA (0.838):** Requires separate YOLOv8m. Already achieved (0.995) but on single-task, not multi-task. No path to multi-task detection SOTA on ConvNeXt-Tiny.
- **PSR STORM SOTA (0.901):** Gap is 0.15 F1. Current decoder oracle relaxed bound is 0.8807 (the architecture loses 12% even with perfect logits). The remaining 0.02 gap requires a better decoder architecture.

---

## 5. Rollback Plan

### 5.1 What if the revival fails?

**Tier 1 failure: PSR transition F1 stays at 0.00 after repair**
- Likelihood: 30% (GELU saturation fix may not restore transition detection if backbone features are permanently shaped)
- Rollback: Publish per-frame F1 (0.70-0.75) with honest persistence-baseline comparison. "The PSR head computes state labels but does not detect transitions." This is a methodology contribution (the MonotonicDecoder assumption is falsified by the data).
- Impact: Paper degrades from "PSR revival" to "PSR limitation documentation." Still publishable as the first per-frame PSR baseline on IndustReal.

**Tier 2 failure: Kendall ablation shows no improvement**
- Likelihood: 60% (Opus Q1 evidence strongly suggests Kendall is NOT the bottleneck)
- Rollback: Publish the negative result: "Kendall uncertainty weighting does not suppress PSR. The gradient starvation originates from dead ReLU paths, not loss weighting." This is a positive paper contribution (Pathology 1: ReLU saturation).
- Impact: Saves other researchers from wasting time on Kendall tuning for PSR-like tasks.

**Tier 3 failure: Single-task ConvNeXt detection on D3 < 0.3 mAP**
- Likelihood: 40% (D3 is 38k frames with sparser annotations than D1R's 8k; ConvNeXt-Tiny may simply be too small)
- Rollback: Detection is handled by the companion YOLOv8m (0.995). The paper's detection claim is: "Single-task detection is near-perfect (0.995). Multi-task detection collapses to 0.00009. This is a 99.99% cost that motivates decoupled architectures."
- Impact: No change to paper narrative. The collapse IS the contribution.

**Tier 4 failure: All 4 heads irrecoverable on ConvNeXt-Tiny**
- Likelihood: 15% (two heads already work: PSR [moderate] and Head Pose [good])
- Rollback: Publish the "Transparent Pathology" narrative (file 145 Narrative A). Three contributions remain:
  1. First ego-pose baseline on IndustReal (head pose forward 9.14 deg, up 7.78 deg) — beats unsourced 15 deg reference
  2. First per-frame PSR baseline with decoder augmentation (F1 0.70-0.79 depending on metric)
  3. Three characterized training pathologies (GELU saturation, gradient starvation, class collapse) with quantitative evidence
- Impact: The paper's contribution shifts from "beat SOTA" to "here is why multi-task SOTA on IndustReal is hard." This is a stronger paper.

### 5.2 Abandonment criteria

Stop and publish immediately if:
1. **PSR repair finishes with transition F1 = 0.** Do NOT launch Kendall ablation. Do NOT launch TCN+ViT. The head is fundamentally broken.
2. **A third OOM crash occurs in the same experiment.** Training instability invalidates any metric. Hardware upgrade needed.
3. **Any reported number cannot be reproduced from the freeze checkpoint** within 2 re-run attempts. The number is noise.

---

## 6. Critical Success Factors

### 6.1 What MUST be true for revival to succeed

| Factor | Rationale | Current Status | Risk |
|--------|-----------|---------------|------|
| **PSR head repair recovers transition detection** | Without transition F1 > 0, PSR revival is impossible. Per-frame F1 is persistence-dominated and not a genuine signal. | LeakyReLU repair activates on sequence frames (post_gelu 384-640) but gradient flow oscillates. Transition F1 not yet evaluated. | **HIGH.** 30% chance transition F1 stays near zero. |
| **PSR transition F1 is separable from persistence** | If transition F1 is just temporal smoothing of per-frame persistence (like the null copy_prev baseline), the PSR head adds nothing. | True-signal analysis shows copy_prev F1 = 0.9997 vs model 0.7013. The model is WORSE than persistence on per-frame. Need transition metric to prove learned signal. | **HIGH.** At 0.2866% transition rate, any temporal smoothing looks like signal on per-frame metric. |
| **Single-task ConvNeXt detection on D3 >= 0.5 mAP** | If ConvNeXt-Tiny achieves reasonable detection single-task, the 0.00009 multi-task result is clearly a multi-task pathology. If single-task is also near-zero, ConvNeXt-Tiny is simply too small for detection on 38k frames, and the paper has no detection contribution. | Training at epoch 43/99. No val mAP being computed during training. | **MEDIUM.** 40% chance of < 0.3. |
| **Kendall ablation produces a publishable negative result** | Even if Kendall has no effect on PSR (the likely outcome per Opus Q1), the ablation is publishable as evidence for the "ReLU saturation, not loss weighting" pathology. This is a positive contribution disguised as a negative result. | Not yet run. | **LOW.** The experiment WILL produce a result, publishable either way. |
| **Results freeze protocol is enforced** | Without a freeze checkpoint, the paper will mix numbers from 3+ checkpoint lineages (epoch 11, epoch 18, repair epoch 24+, single-task epoch 43+). This is exactly what AC-1 documented as the previous failure mode. | No freeze protocol currently in place. | **HIGH.** Enforce immediately. |

### 6.2 Critical infrastructure requirements

| Requirement | Status | Action |
|-------------|--------|--------|
| RTX 5060 Ti available for 21+ days | IN USE (single-task detection) | Complete current run, then schedule sequentially |
| RTX 3060 available for 14+ days | IN USE (PSR repair) | Complete current run, then evaluate |
| No OOM crashes during critical training | 4 prior crashes documented | `batch_size=2` maximum, `OMP_NUM_THREADS=4`, memsafe wrapper |
| All eval artifacts committed to repo | Only d1r 0.995 verifiable in-repo | Commit ALL `metrics.json`, eval logs, `SOTA_STATUS.md` before freeze |
| Checkpoint SHA256 recorded | None recorded | Record at freeze date |

---

## 7. Cross-References: Specific Challenges to Each Agent

### 7.1 Challenge to Agent 1 (PSR Head Specialist)

**Your plan's weakest assumption:** "KENDALL_FIXED_WEIGHTS=1 will raise PSR F1 from 0.7499 to ~0.82" (plan 130 P1.1). The evidence contradicts this. Kendall's log_var_psr=-0.04 gives a precision of ~1.04 — a 4-8% multiplicative weight. This cannot produce the exactly-zero per-component gradients observed across all 11 sub-heads for 3800+ steps. The PSR head has a dead forward path (`psr_transition.py:216-237`, ReLU(inplace=True) with bias=-1.0), and your own debate (2.3 resolution) said "architectural fix needed." The plan then ignored the debate's conclusion and went with Kendall anyway.

**Your plan's riskiest step:** Training for 5-10 epochs from epoch_18 with the dead ReLU architecture. The PSR repair training status shows the repair (LeakyReLU) DOES activate on sequence frames. Running the Kendall toggle without the repair would have been 5-10 epochs of the head producing constant sigmoid(0.27) output with zero gradient — a pure waste of GPU time.

**Conflict with Agent 4:** You want to train first, diagnose later. Agent 4 insists on diagnostics first. The evidence (PSR activation diagnostic confirmed dead ReLU, linear probe confirmed zero backbone activity signal) proves Agent 4 was right. Your sequencing would have wasted 5+ GPU-days.

**Alternative if primary fails (Kendall has no effect):** This is the expected outcome. Your alternative is the correct one: publish the head repair as the fix (bias=0.0, LeakyReLU/GELU instead of ReLU, re-init output layer), and publish Kendall as the negative-result ablation showing loss weighting is NOT the bottleneck. This is a strong paper contribution — it falsifies a common hypothesis (Kendall causes gradient starvation) with controlled evidence.

**Additional challenge:** Your per-frame F1 target of 0.83 uses a metric dominated by label persistence (copy_prev baseline = 0.9997). The transition F1 metric is the correct one. What is your transition F1 target?

---

### 7.2 Challenge to Agent 2 (Detection Specialist)

**Your plan's weakest assumption:** "Knowledge distillation will raise ConvNeXt detection from 0.358 to ~0.65" (plan 130 P2.1, strategy 133-5). The 0.358 number comes from a 250-batch class-balanced subsample whose sampler over-represents rare classes (debate 1.2 "mAP Fairness Reviewer" warning). The full D3 evaluation reveals the true number: mAP50 = 0.00009, not 0.358. Distillation from 0.995 to 0.00009 is a 1000x gap — that is not a training issue, it is an architectural collapse. Distillation closes 10-30% gaps; it does not resurrect a head that produces essentially random predictions (105 predictions per frame, ~0 present classes at standard confidence per `145_PAPER_NARRATIVE_V3.md`).

**Your plan's riskiest step:** Investing 5 days of RTX 5060 Ti training in distillation before knowing the single-task ConvNeXt D3 baseline. If single-task ConvNeXt on D3 also achieves near-zero (which is a real possibility — D3 is 38k frames with sparser annotations than D1R), distillation is targeting a backbone that cannot detect, not a head that needs teacher guidance. The single-task training (currently epoch 43/99 on GPU 0) must complete and evaluate first.

**Conflict with Agent 3:** Both need the RTX 5060 Ti. You want distillation (5 days), Agent 3 wants TCN+ViT (2-3 days). Serial execution order must prioritize the experiment with the higher probability of success. Distillation has a teacher that achieves 0.995 and targets a head that works single-task. TCN+ViT targets a backbone that has zero activity signal. Distillation first.

**Alternative if primary fails (distillation yields < 0.1 mAP):** Detection is handled by companion YOLOv8m (0.995 mAP50). The paper's detection claim becomes: "Detection requires a dedicated backbone; the 99.99% multi-task cost is the central measurement." This is consistent with Agent 4's narrative and with the cascade analysis. The distillation failure strengthens the paper's "decoupled architecture" argument.

**Additional challenge:** Your plan 130 P1.3 (full eval NaN fix) is referenced as "needs 1 day" but the full eval was completed and returned 0.00009. Does your plan acknowledge that the full eval WORKS and the result is catastrophic? Update your D3 numbers immediately.

---

### 7.3 Challenge to Agent 3 (Activity Specialist)

**Your plan's weakest assumption:** "Set ACTIVITY_HEAD_SIMPLE=False, train TCN+ViT for 10 epochs, expect clip-level top1 from 0.028 to ~0.10-0.20" (plan 130 P1.4). This assumption is falsified by the activity linear probe result: a linear classifier on frozen ConvNeXt-Tiny features achieves 0.2169 top-1, which is BELOW the majority-class baseline of 0.2217 (always predict class 8). The backbone encodes ZERO activity-relevant information. Adding temporal context (TCN+ViT) to features that contain no action signal cannot produce a 0.10+ result. The TCN+ViT sits on the same frozen features — it will be just as blind.

**Your plan's riskiest step:** Proposing to spend 2-3 days of RTX 5060 Ti training on an experiment whose premise (the backbone has action-discriminative features) is empirically false. The linear probe was supposed to be P3.4 ("Weeks 5+") but Opus Q4 correctly moved it to Step 0. The result (0.2169 vs 0.2217 baseline) was obtained, and it is decisive. TCN+ViT on ConvNeXt-Tiny is dead on arrival.

**Conflict with Agent 4:** You want TCN+ViT immediately. Agent 4 wants linear probe first. The linear probe was run and it failed. Agent 4 wins this debate by knockout. Your plan must pivot to a different backbone (MViTv2-S with Kinetics-400 pretraining), which is plan 130 P5.1 ("stretch goal," 1 week). This is a new project, not a head repair.

**Alternative if primary fails (which it will):** Activity is abandoned on the shared ConvNeXt-Tiny backbone. The paper reports: (1) per-frame MLP top-1 = 0.0236 vs MViTv2-S SOTA = 0.622, (2) 41 of 69 classes have zero accuracy, (3) linear probe confirms backbone has zero activity signal, (4) "The ConvNeXt-Tiny backbone, ImageNet-pretrained and fine-tuned for detection+pose, does not learn action-discriminative features. This is a fundamental architectural limitation." This is a strong pathology contribution.

**Additional challenge:** Your plan mentions LORT+CurB (strategy 133-2) as a loss function upgrade for activity. If the backbone has zero signal, no loss function can fix that. Loss functions help when the backbone provides weak but non-zero signal. They cannot help when the signal is zero. Acknowledge this.

---

### 7.4 Challenge to Agent 4 (Integrity/Diagnostic Specialist)

**Your plan's weakest assumption:** "All reported numbers will be frozen at end of Week 4" (file 132 Q10). The freeze protocol is correct, but your plan assumes the 4 weeks start when the diagnostic phase completes. That was July 7. The freeze date was therefore ~August 4, 2026. Today is August 1, 2026. We are 3 days from the freeze date and:
- PSR repair is still running (or completed offline)
- Single-task detection is still running (or completed offline)
- Transition-F1 has not been re-evaluated on repaired checkpoint
- Kendall ablation has not been run
- Per-recording breakdowns are not complete

**Your plan's riskiest step:** Trusting that the diagnostic phase results (completed) will be acted upon. The linear probe proved activity is dead. The activation diagnostic proved PSR was dead. The D4 retune showed marginal improvement (F1=0.07). The true-signal analysis proved per-frame F1 is persistence-dominated. Yet plans 130/133 still list TCN+ViT (P1.4) and Kendall-first (P1.1) as active items. The diagnostic results are IN the repository but not yet reflected IN the execution plans. Your plan's risk is being correct but ignored.

**Conflict with Agent 1:** You insist on diagnostics first. Agent 1 wants to train first. You were right. But you were right on July 7, and Agent 1's plan in file 130 has not been amended to reflect the diagnostic results. Push harder.

**Alternative if freeze fails (numbers can't be frozen):** Extend freeze to August 22, 2026 (which is what the time budget in Section 4 requires). Document the extension as a one-time adjustment. After August 22, no more results under any circumstances.

**Additional challenge:** Your 8 honest disclosures (file 135) are enumerated but not written. D1 (D4 backbone swap), D2 (POS structurally inflated), D3 (activity 0.028 vs prior), D4 (multi-task detection 36% of ceiling), D5 (PSR gradient starvation), D6 (per-component thresholds tuned on val), D7 (up-vector MAE unstable), D8 (position units unverified). All 8 require specific numbers in the placeholders. As of today (Aug 1), how many placeholders are filled? If < 4, the freeze date cannot be Aug 4.

---

## 8. Synthesis: The One Coherent Plan

### 8.1 What we actually know (Aug 1, 2026)

1. **Head pose works.** Forward MAE = 9.14 deg, up MAE = 7.78 deg (after normalization fix). Both beat the unsourced 15 deg reference. This is a publishable SOTA result regardless of what happens to the other heads.
2. **PSR partially works.** Per-frame F1 = 0.70-0.75 but is dominated by label persistence (copy_prev baseline = 0.9997). Transition F1 = 0.00 from saturated logits. Repair is in progress. If repair recovers transition detection, PSR becomes a second publishable result. If not, the persistence-dominance finding is itself a methodology contribution.
3. **Detection is architecturally collapsed.** Multi-task ConvNeXt detection: mAP50 = 0.00009. Separately-trained YOLOv8m: mAP50 = 0.995. The 99.99% cost is the cleanest multi-task pathology measurement in the paper.
4. **Activity has zero backbone signal.** Linear probe on frozen ConvNeXt features: 0.2169 vs 0.2217 majority baseline. 41 of 69 classes have zero accuracy. The backbone does not encode action-relevant information.
5. **The multi-task cascade is bimodal.** Detection + Activity collapse catastrophically (-99.99%, -96.2%). PSR degrades mildly (-11.1%). Head pose is unaffected (+8.9%). The backbone selectively supports regression tasks while starving classification/detection tasks.

### 8.2 The single coherent execution order

```
NOW (Aug 1-7):    Complete PSR repair on RTX 3060
                   Complete single-task detection on RTX 5060 Ti
                   Run all CPU diagnostics: per-recording breakdowns, null-model baselines
                   Paper writing: draft P4.1-P4.4 (disclosures)

Aug 8-12:         Evaluate PSR transition F1 on repaired checkpoint
                   Evaluate single-task detection mAP on D3
                   Decision gate: PSR transition F1 > 0? → Kendall ablation
                                 Detection D3 mAP > 0.5? → skip distillation

Aug 13-17:        IF gate passed: Kendall ablation (2-3 days, RTX 3060)
                   IF gate passed: Detection distillation (5 days, RTX 5060 Ti)
                   IF gate failed: Salvage analysis — publish what we have

Aug 18-22:        Re-evaluate ALL metrics on freeze checkpoint
                   Fill 8 honest disclosure placeholders
                   Commit all artifacts to repo
                   FREEZE — no more results after Aug 22

Aug 23+:          Paper writing only. No training. No eval.
```

### 8.3 The paper this plan produces

**Title:** "What Four Tasks Really Cost on One Backbone: Multi-Task Training Pathologies for Industrial Assembly Understanding"

**Headline results:**
1. First ego-pose baseline on IndustReal (head pose forward/up both sub-10 deg)
2. First per-frame PSR baseline with decoder augmentation (F1 0.70-0.75 per-frame; transition F1 TBD)
3. Single-task detection beats SOTA (YOLOv8m mAP50 = 0.995; verified in-repo)
4. Multi-task detection cost: 99.99% (0.995 to 0.00009)
5. Multi-task activity cost: 96.2% (0.622 to 0.0236, with linear probe confirming zero backbone signal)
6. Three characterized training pathologies: GELU saturation, gradient starvation, class collapse
7. 8 honest disclosures with filled placeholders

**What this plan does NOT claim:**
- "Beats SOTA on all heads" — false. Only head pose genuinely beats the reference.
- "Multi-task ConvNeXt detection is competitive" — false. It's 0.00009 mAP.
- "Activity recognition within a multi-task framework" — false. The backbone has zero activity signal.
- "Kendall uncertainty weighting automatically balances tasks" — false. The config has 5 manual guards.

---

## 9. Appendix: Verification Checklist

Before the freeze date (Aug 22), these items must be complete:

- [ ] PSR transition F1 evaluated on repaired checkpoint (with per-recording breakdown)
- [ ] Single-task ConvNeXt D3 mAP50 evaluated
- [ ] KENDALL_FIXED_WEIGHTS ablation run (or decision documented to skip)
- [ ] D4 retune results committed (F1=0.07)
- [ ] All 8 honest disclosure placeholders filled with actual numbers
- [ ] Freeze checkpoint identified by commit hash + config hash
- [ ] All eval artifacts committed to repo (metrics.json, eval logs, optimal_thresholds.json, SOTA_STATUS.md)
- [ ] Per-recording up-vector breakdown available
- [ ] Per-recording activity zero-accuracy class analysis available
- [ ] Activity linear probe result (0.2169) documented in paper
- [ ] Null-model POS baselines (copy_prev, zeros) documented in paper
- [ ] Copy_prev PSR persistence baseline (0.9997) documented alongside model F1

---

**One-sentence synthesis:** Revive PSR + Head Pose on the shared ConvNeXt-Tiny backbone; report detection and activity as characterized pathology measurements with quantitative cost ratios; publish the 8 honest disclosures with all placeholders filled; freeze all numbers by August 22, 2026.
