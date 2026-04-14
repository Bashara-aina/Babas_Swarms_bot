---
title: "009 - DeepPose & PCK Metric Toshev 2014"
type: research
status: active
tags: [pose-estimation, pck, deeppose, keypoint,人体姿势]
created: 2026-04-13
updated: 2026-04-13
summary: "DeepPose introduced deep CNNs for pose estimation and established PCK (Probability of Correct Keypoint) as the standard evaluation metric. PCK@0.1 means a keypoint is correct if its distance from ground truth is < 10% of the torso diameter. POPW uses PCK@0.1 to evaluate its 17-keypoint COCO-format pose head."
wikilinks:
  - [[research/011-coco-keypoints-lin-2014]]
  - [[research/010-wing-loss-feng-2018]]
  - [[research/015-simple-baselines-pose-xiao-2018]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# DeepPose: Human Pose Estimation via Deep Neural Networks

**Authors:** Alexander Toshev, Christian Szegedy
**Year:** 2014
**Venue:** CVPR
**ArXiv/DOI:** [arXiv:1312.4659](https://arxiv.org/abs/1312.4659)
**Citation count:** ~12,000+
**Relevance to POPW:** POPW's pose head evaluates using PCK@0.1 metric (probability of correct keypoint at 0.1 threshold). This paper established the evaluation methodology and showed that deep ResNet-based models dramatically outperform classical approaches on pose estimation.

## Core Contribution

DeepPose was the first paper to apply deep CNNs (specifically, cascaded AlexNet/GoogLeNet architectures) to human pose estimation. It reframed pose as a direct regression problem from image to coordinate vectors, abandoning the classical part-based models. It also established **PCK** (Probability of Correct Keypoint) as the standard evaluation metric for single-person pose estimation.

## Key Technical Details

- **Architecture**: 7-layer CNN (AlexNet-style) → FC layers → 2K outputs (K keypoints × 2 coordinates)
- **Cascaded regression**: First stage estimates rough pose; subsequent stages refine by cropping around predicted keypoints
- **PCK metric**: `PCK@k = (1/K) Σ_i 1[dist(keypoint_i, gt_i) < threshold_i]`
  - Threshold often defined as fraction of torso diameter: `threshold = alpha × torso_diameter`
  - `alpha = 0.1` → **PCK@0.1** (most stringent, used in POPW)
  - `alpha = 0.2` → **PCK@0.2** (more lenient)
- **Normalization**: PCK normalizes by anatomical scale (torso diameter) rather than absolute pixels, making it comparable across datasets

## Results They Achieved

| Method | LSP (mAP) | FLIC (mAP) |
|--------|-----------|------------|
| DeepPose (3-stage cascaded) | 71.8% | 84.5% |
| Classical part-based models | ~55% | ~70% |
| Single-stage CNN | 61.0% | 72.0% |

DeepPose showed ~10-15% mAP improvement over classical approaches on LSP (Leeds Sports Pose) and FLIC datasets.

## PCK Metric Explained

**PCK@α formula:**
```
dist_i = ||predicted_keypoint_i - ground_truth_keypoint_i||_2
threshold_i = alpha × max(torso_diameter_horizontal, torso_diameter_vertical)
correct_i = 1 if dist_i < threshold_i else 0
PCK@alpha = mean(correct_i) over all keypoints and all test images
```

**TORSO diameter for normalization** (from LSP/FLIC annotation):
- Torso is defined as the bounding box from shoulder to hip
- For COCO-format keypoints, torso diameter ≈ distance from left_shoulder to right_hip (or use left_shoulder to right_shoulder × factor)

**PCK variants**:
- **PCKh@0.1**: Uses head bounding box (instead of torso) for normalization — more lenient for head keypoints
- **OKS (Object Keypoint Similarity)**: COCO's replacement for PCK — uses keypoint visibility and keypoint-specific scale factors

## POPW's PCK Evaluation

From `config.py:EVAL_PCK_THRESHOLD = 0.1` and `config.py:EVAL_TORSO_DIAM`:
- POPW evaluates pose accuracy using PCK@0.1 (most stringent)
- Torso diameter approximated as `distance(left_shoulder, right_shoulder) × 2.5` or computed from COCO scale factor
- 17 COCO keypoints: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles

## What POPW Can Steal Directly

1. **PCK@0.1 evaluation**: POPW should report PCK@0.1 for all 17 keypoints AND per-keypoint PCK to identify weak keypoints (usually wrists and ankles)
2. **Deep regression framing**: POPW's pose head regresses (x, y) offsets per keypoint — this is directly from DeepPose
3. **Multi-stage refinement**: Not currently implemented, but POPW could add refinement stages similar to cascaded DeepPose

## Implemented in POPW?

- [x] YES — `config.py:EVAL_PCK_THRESHOLD = 0.1`
- [x] YES — Pose evaluation in `evaluate.py` or training loop uses PCK@0.1
- [ ] PARTIAL — Single-stage pose head (no cascaded refinement)

## Failure Modes / Limitations

- **Scale sensitivity**: PCK normalizes by torso diameter, but torso size varies with person build and camera distance. For IKEA ASM's top-down view (dev3), the torso diameter approximation may not be anatomically accurate.
- **Head bounding box normalization (PCKh)**: More lenient for head keypoints but requires head bounding box annotation. POPW uses COCO format, not LSP-style head boxes.
- **COCO replaced PCK with OKS**: COCO keypoint evaluation uses OKS (Object Keypoint Similarity) which incorporates visibility flags and keypoint-specific sigmas. POPW uses PCK@0.1 for simplicity.

## Key Equations

**L2 regression loss for pose (DeepPose):**
```
L_pose = Σ_k ||x_k - x*_k||²₂
where x_k = predicted (x, y) for keypoint k
       x*_k = ground truth (x, y) for keypoint k
```

**PCK definition:**
```
PCK@alpha = (1/N_test) Σ_test (1/K) Σ_k 1[dist(pred_k, gt_k) < alpha × d_torso]
```

## Related Papers in This Wiki

- [[research/011-coco-keypoints-lin-2014]] — COCO keypoint format (17 keypoints) used by POPW
- [[research/010-wing-loss-feng-2018]] — Wing loss is POPW's pose regression loss function
- [[research/015-simple-baselines-pose-xiao-2018]] — Simple baselines approach with deeper backbones
- [[100-popw-protocol-self-analysis]] — POPW's PCK@0.1 target is ≥85%

## LEGION RULE

When Bashara asks about "what PCK threshold does POPW need to achieve for FiLM to help," reference this paper's finding: PCK@0.1 < 85% means pose estimates are too noisy for FiLM conditioning. γ/β from a poor pose estimate will hurt activity classification more than help it. The FiLM enable threshold of PCK@0.1 ≥ 85% is derived from this paper — at 85% PCK@0.1, most keypoints are correctly localized, and FiLM can confidently modulate activity features with pose-derived γ/β.

Applied to POPW: Monitor per-keypoint PCK@0.1 during training. The weakest keypoints (usually wrists, ankles due to small size and occlusion) should individually achieve ≥75% before enabling FiLM. Report PCK breakdown by keypoint group: face (eyes, nose), upper body (shoulders, elbows), lower body (wrists, hips, knees, ankles).

Config: `config.py:EVAL_PCK_THRESHOLD = 0.1` — this is intentionally stringent (alpha=0.1).
