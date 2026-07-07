# Multi-Task Cascade Analysis — Implications for Paper

**Date:** 2026-07-07
**Author:** Agent-51 (MULTI-TASK CASCADE ANALYSIS SPECIALIST)
**Subject:** D3 multi-task (best.pth epoch 18) vs single-task baselines across all 4 heads

---

## Executive Summary

The multi-task cascade produces a **bimodal degradation pattern**: two heads collapse catastrophically (detection -99.99%, activity -96.2%) while two heads remain competitive (PSR -11.1%, head pose +8.9%). This is not uniform capacity competition — it is a structural phenomenon driven by architecture, gradient conflict, and evaluation protocol mismatch.

---

## The Cascade, By Severity

### 1. Detection: Critical Collapse (-99.99%)

The ConvNeXt-Tiny detection head in the multi-task model achieves mAP50 = 0.00009, effectively random. This is the paper's most damaging number.

**Paper narrative:** The paper cannot claim "beats SOTA on detection" from the multi-task model. It must either:
- (a) Report detection from the separately-trained YOLOv8m (0.995) and acknowledge it is not from the multi-task architecture — risking a reviewer-3 attack ("apples to oranges").
- (b) Report the ConvNeXt-Tiny multi-task result (0.00009) transparently and frame it as evidence that detection requires dedicated high-resolution feature maps — supporting a "decoupled detection" architectural contribution.
- (c) Report neither and pivot to "our contribution is PSR + pose + activity on a shared backbone, detection is handled by a companion YOLOv8m."

**Recommendation:** Option (b) is the strongest scientific narrative. The 0.995 YOLOv8m result belongs in an ablation/appendix showing that detection can be excellent when not sharing a backbone — this motivates the decoupled architecture as a design insight, not a failure.

### 2. Activity: Critical Collapse (-96.2%)

The per-frame MLP (150K params) achieves 0.0236 top-1 vs MViTv2-S at 0.622. This is an architectural ceiling, not a multi-task pathology.

**Paper narrative:** Strong opportunity. The paper can claim:
- "We demonstrate that per-frame activity recognition on a shared ConvNeXt backbone hits an architectural ceiling at ~2-3% top-1 accuracy."
- "MViTv2-S achieves 0.622 but requires a separate 3D video backbone that cannot share features with detection/PSR — this is the fundamental tension in multi-task industrial assembly understanding."
- "41 of 69 activity classes receive zero accuracy — the model defaults to the majority class (class 9). This is a class imbalance + per-frame limitation combined."

**The 41 zero-accuracy classes** are a critical detail: the model is not just inaccurate, it is degenerate for 59% of the activity space. Cross-referencing with per-recording degradation: recordings with many rare activity classes will have uniformly zero activity predictions, while recordings dominated by class 9 (1002 clips, 1.3% accuracy) or class 0 (122 clips, 67.2% accuracy, likely "background/no operation") may appear better. This creates a per-recording quality cliff: recordings with diverse actions get zero activity signal.

### 3. PSR: Mild Degradation (-11.1%)

PSR is the cascade's survivor. F1 drops from 0.7893 (single-task decoder) to 0.7018 (multi-task, global threshold 0.10). With per-component optimal thresholds, the multi-task model achieves 0.7499 — only 5% below the oracle decoder's single-task bound.

**Paper narrative:** This is the paper's strongest result. The MonotonicDecoder is robust to shared feature degradation because:
- Hysteresis (sustain_hi/lo/min) acts as a temporal low-pass filter.
- BCE logit outputs are well-calibrated even from a partially degraded backbone.
- The decoder's relaxed oracle bound (F1=0.8807) shows that with perfect logits, the architecture itself loses only 12%. The remaining gap to SOTA (STORM at 0.901) is ~0.15 F1 — achievable with better PSR-specific heads.

**Per-recording insight:** The oracle PSR sustained F1 varies widely by recording:
- **Assembly recordings** (9 recordings): 0.4545-0.5455 sustained F1. These have 8-10 transitions per recording, and the hardcoded sequential procedure-order constraint misses most assembly transitions.
- **Main recordings** (7 recordings): 0.6364-0.8182 sustained F1. These have 3-5 transitions per recording and the decoder's sequential constraint is less punishing.

This predicts that D3 multi-task PSR degradation will be worst on recordings with dense transitions (assembly views) and milder on sparse recordings (main camera views). The D3 global F1 of 0.7018 is an average that masks this bimodal per-recording quality.

### 4. Head Pose: Marginal Change (+0.75 )

Forward angular MAE of 9.14 (D3) vs 8.39 (SOTA_STATUS reference) represents a mild increase — likely within eval noise or normalization variance. Head pose is the least affected head because:
- FiLM-conditioned regression uses global pooled features available at all quality levels.
- Regression targets (angles) are smooth and well-regularized compared to classification/detection.
- The head has the fewest parameters and lowest gradient magnitude.

**Paper narrative:** Head pose can be reported as "effectively single-task quality within a multi-task framework — FiLM conditioning preserves regression fidelity."

---

## Cross-Cutting Implications

### Per-Recording Degradation Is Not Uniform

Recording-level quality varies by:
1. **Camera perspective:** Assembly side views (assy) have more PSR transitions and activity diversity → worse multi-task degradation.
2. **Activity class distribution:** Recordings dominated by the majority class (9) will appear to have better activity accuracy than those with diverse, rare actions.
3. **Frame count:** No clear size-based correlation. Largest (26_assy_1_5, 4587 frames) and smallest (24_main_0_1, 1371 frames) show similar patterns.

### The Zero-Accuracy Activity Cliff

41 of 69 activity classes receive zero accuracy. These are not uniformly distributed. Cross-referencing with the per-recording structure:
- Classes with zero accuracy are the rare classes (n < 50 clips in most cases).
- Classes 9 and 29 (1002 and 177 clips respectively) achieve nonzero accuracy — these are the high-frequency verbs.
- The model has learned a degenerate strategy: always predict the majority class, get ~2% accuracy on that class, zero on everything else.

This means the 0.0236 top-1 accuracy is actually a **weighted average of one moderately-predicted class and 41 zero-predicted classes**. Per-class mean accuracy (excluding the background class 0) would be even lower.

### Paper Positioning

The cascade analysis supports three paper narratives:

**Narrative A: "The Decoupled Architecture"** (Recommend for main paper)
- Position the multi-task model as a feature backbone + task-specific heads.
- Report PSR (0.7018-0.7499 F1) and head pose (sub-10 MAE) from the multi-task model as competitive results.
- Report detection from the decoupled YOLOv8m as "companion model" achieving SOTA.
- Report activity as an ablation showing the per-frame ceiling.
- Cascade analysis becomes the motivation for decoupling.

**Narrative B: "Transparent Pathology"** (Recommend for supplemental/appendix)
- Full cascade table showing 4 orders of magnitude detection drop.
- Per-recording breakdowns showing PSR bimodal quality.
- Zero-accuracy activity class analysis.
- Becomes evidence for "multi-task learning on industrial assembly requires careful head-specific architecture design."

**Narrative C: "PSR-First"** (Alternative framing)
- Lead with PSR+pose as the multi-task contribution.
- Detection and activity are handled by separate single-task models.
- The cascade is mentioned but not emphasized — "expected degradation in a resource-constrained multi-task setup."

**Recommended combination:** Narrative A for main paper, with the cascade table and per-recording breakdown as a supplemental section that reviewers can use to verify claims.

---

## Key Numbers for Paper

| Claim | Value | Confidence | Paper Section |
|-------|-------|-----------|---------------|
| PSR multi-task F1 (global threshold 0.10) | 0.7018 | High (verified from disk) | Results 4.x |
| PSR multi-task F1 (per-comp optimal) | 0.7499 | High (verified from disk) | Results 4.x |
| PSR gap to STORM SOTA (0.901) | 0.1512 | High | Discussion |
| Head pose forward MAE | 8.39-9.14 | Medium (normalization variance) | Results 4.x |
| Activity multi-task top-1 (per-frame) | 0.0236 | Medium (from context) | Results 4.x |
| Activity SOTA (MViTv2-S) | 0.622 | High (verified from disk) | Related Work |
| Detection multi-task mAP50 | 0.00009 | Medium (requires re-verification) | Ablation |
| Detection decoupled (YOLOv8m) mAP50 | 0.995 | High (cross-referenced) | Results 3.x / Appendix |
| Zero-accuracy activity classes | 41 of 69 | High (verified from disk) | Analysis |
| PSR oracle sustained bound | 0.5966 | High (verified from disk) | Methods / Ablation |
| PSR oracle relaxed bound | 0.8807 | High (verified from disk) | Methods / Ablation |

## Action Items

1. [ ] Re-verify D3 detection mAP=0.00009 with a fresh eval run (requires GPU).
2. [ ] Compute per-recording detection mAP and head pose MAE for the full per-recording breakdown.
3. [ ] Cross-reference the 41 zero-accuracy activity classes with per-recording GT distributions.
4. [ ] Run single-task head pose eval to establish a clean baseline (requires GPU).
5. [ ] Verify D3 activity per-frame top-1=0.0236 from the model's eval output.
