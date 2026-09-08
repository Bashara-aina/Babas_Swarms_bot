# PR Review & Existing Fixes — What We Already Have

**Date:** 2026-08-01
**Sources:** Bashara-aina/Industreal_improved PR list (36 PRs total, all merged)
**Purpose:** Inventory fixes already shipped via PR. Avoid re-implementing them.

## Critical PRs (code changes already in main)

### PR #7 — Fix detection death spiral via absolute GT-frame sampling
**Merged:** 2026-06-16
**Files:** `src/config.py` (+41), `src/data/industreal_dataset.py` (+45), `diag_gt_coverage.py` (new), `overfit_one_batch.py` (new)
**Effect:** Added `DET_GT_FRAME_FRACTION=0.40` — guarantees 40% of every batch has detection labels.
**Why it matters:** Without this, the detector sees GT boxes in <1% of training steps, positive logits decay between rare GT batches.
**Already used in:** Cleanfix 20260801 launch (DET_GT_FRAME_FRACTION=0.5)

### PR #10 — fix(detection): detach_reg_fpn=False + honest mAP
**Merged:** 2026-06-21
**Files:** `src/config.py` (+94/-42), `src/evaluation/evaluate.py` (+26/-2), `src/training/train.py` (+33/-2), `src/diag_per_class_truth.py` (new)
**Effect:** Reverts `DET_LR_MULTIPLIER` 2.0→1.0. Surfaces the honest (present-class) detection mAP metric.
**Already used in:** `det_mAP50_pc` metric — this is what we should report instead of diluted 24-class.

### PR #13 — feat: implement GUIDE 1-7 code changes
**Merged:** 2026-06-22
**Files:** 15 files, +1238/-452 lines
**Patches:**
- model.py return dict — added `proj_feat` and `p4` keys
- embedding_cache.py — 3 bugs fixed (output keys, batch counter, recording split)
- evaluate.py detection confusion matrix — 24x24 + PNG export
- stage_manager.py — sanity fixes
**Already used in:** All current code paths.

### PR #19 — fix+docs: round-4 final verification (segment-eval remap)
**Merged:** 2026-07-01
**Files:** `src/data/industreal_dataset.py` (+27), `src/evaluation/evaluate.py` (+13/-2)
**Critical findings:**
1. **Segment eval bug Q5** — `compute_activity_segment_metrics` had a label remap bug. With `ACT_CLASS_GROUPING='hybrid'`, raw_id labels were being compared against grouped output indices. Fixed: remap `label` through `remap_activity_label()` before argmax comparison.
2. **PSR is per-frame, NOT transition** — PR #19 documents: "the causal transformer's mask is a no-op and the temporal-smoothing term computes over T=1 transitions. So this head is a per-frame component-state classifier, not transition detection. The paper must call it per-frame procedure-component recognition, not transition/PSR-order detection."
3. **GIoU range** — `1-GIoU ∈ [0,2]` always non-negative. Floor branches never execute. PR fixed the misleading comment.
**Already used in:** Current eval pipeline.

### PR #36 — AAIML 2027 30-day execution plan
**Merged:** 2026-07-14
**Files:** 6 docs, +933 lines
**Key dates/plan:**
- Aug 3 (Day 21): Architecture freeze
- Aug 4-10: Phase 3 multi-seed
- Aug 22 freeze date (was; we're past this now)
- Oct 10: Submission deadline
**Gates:**
- det mAP50-pc < 0.33 → trigger TSBN (Q7)
- activity top-1 < 0.35 → trigger cRT (Q8)
- PSR F1 < 0.50 → queue ASL (Q15)
- pose/psr grad ratio > 1000× → queue MetaBalance (Q44)

## Code Changes Already In Tree (haven't been used)

### `src/losses/uw_so.py` exists, NOT wired
- UW-SO = softmax weighting with stop-grad, no log-var caps
- Zero references in `src/training/losses.py`, `train.py`, `config.py`
- ~1.5 person-h to wire, ~25 GPU-h to ablate
- **Recommendation:** Wire as Plan A alternative to Kendall

### `src/losses/balanced_softmax.py` exists, NOT wired
- Same as above
- Research shows Balanced Softmax ≈ LDAM-DRW
- **Recommendation:** Skip; LDAM-DRW already active

### `src/losses/asymmetric_loss.py` exists, NOT wired
- Designed for PSR's <0.5% positive-rate regime
- Zero references in training path
- **Recommendation:** Wire only if PSR gate fires

### cRT (decoupled classifier retraining) `scripts/decoupled_act_retrain.py` exists, NOT used
- Stage-2 retrain of activity head from best MTL checkpoint
- Kang ICLR 2020 — +3-8% top-1 on tail classes
- **Recommendation:** Use if LAP+KL fails

### PSR_TRANSITION flag exists, may be `USE_PSR_TRANSITION=True` already
- Could test if PSR is actually doing transition detection vs per-frame
- **Recommendation:** Verify in current config

## Decision Matrix — Existing vs New

| Area | Existing Code | Used? | Need? |
|------|---------------|-------|-------|
| Activity head: distribution-matching bias | PR #404 fix, in main | Yes (current cleanfix) | Try with longer training |
| Activity head: LDAM-DRW | Default config | Yes | Adjust DRW_EPOCH (was 15) |
| Activity head: LAP (Logit Adjust) | NEW (just added) | No | Add to config |
| Activity head: cRT | script exists | No | Use if collapse persists |
| Activity head: Balanced Softmax | unwired | No | Skip |
| Detection: dx*0.1 fix | Eval bug fixed (today) | No | Re-evaluate |
| Detection: TTA | tta_results exist | No | Run TTA on eval |
| Detection: YOLOv8m distillation | script exists | No | Use d1r as teacher |
| PSR: Asymmetric loss | unwired | No | Wire if gate fires |
| PSR: Transition mode | config flag exists | Yes if flag set | Verify |
| Pose: 6.15° was v4_fixed | YES historical | N/A | Find what produced it |
| Pose: Calibration | ? | No | Check eval scripts |

## What this means for the 5 revival plans

**Agent 1 (Activity)**: Already has the bias fix + LDAM-DRW. Needs to add LAP (just added). The cRT script exists as a fallback. NO new code needed.

**Agent 2 (Detection)**: dx*0.1 fix already applied today. Needs TTA + re-eval. The YOLOv8m distillation is optional. NO new code needed.

**Agent 3 (PSR)**: Already wired transition mode. Perp-frame vs transition framing is settled (PR #19). May need to verify USE_PSR_TRANSITION flag. NO new code needed.

**Agent 4 (Pose)**: 6.15° was from v4_fixed. Need to find the eval script that produced it. NO new code needed.

**Agent 5 (Integration)**: Already references all 5 plans. The 30-day execution plan from PR #36 is the execution reference.

## Critical realization

**Most of the "missing" fixes already exist.** The revival is NOT about new code — it's about:
1. Re-running the eval with the existing fixes (dx*0.1, LAP, etc.)
2. Using the right eval script (segment-eval remap)
3. Using the right checkpoint (find the v4_fixed or rf_stages/best one)
4. Following the existing 30-day plan (PR #36)

The "code revival" is largely done. The "results revival" is about running the eval pipeline correctly.
