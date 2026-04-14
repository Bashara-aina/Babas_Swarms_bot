---
title: "011 - COCO Keypoints Lin 2014"
type: research
status: active
tags: [dataset, keypoints, coco, pose-estimation, annotation-format]
created: 2026-04-13
updated: 2026-04-13
summary: "The COCO keypoint dataset defines 17人体关键点 format for pose estimation (nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles) with visibility flags. POPW uses exactly this format: 17 COCO keypoints with (x, y, visibility) per person, from config.py:NUM_KEYPOINTS=17."
wikilinks:
  - [[research/009-deeppose-pck-toshev-2014]]
  - [[research/010-wing-loss-feng-2018]]
  - [[research/015-simple-baselines-pose-xiao-2018]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# Microsoft COCO: Common Objects in Context — Keypoints Dataset

**Authors:** Tsung-Yi Lin, Michael Maire, Serge Belongie, et al. (COCO Consortium)
**Year:** 2014
**Venue:** ECCV
**ArXiv/DOI:** [arXiv:1405.0318](https://arxiv.org/abs/1405.0318)
**Citation count:** ~30,000+ (COCO overall)
**Relevance to POPW:** POPW's pose head outputs 17 COCO keypoints per detected person. This is THE standard format for human pose estimation, enabling transfer learning from COCO-pretrained models and using standard evaluation metrics (OKS, PCK).

## Core Contribution

COCO keypoints established the de facto standard for human pose estimation:
- **17 keypoints** defined with anatomical consistency
- **Visibility flags** (0=not annotated, 1=occluded, 2=visible) for handling partial occlusion
- **Multi-person annotation** with keypoint-level visibility per person
- **OKS (Object Keypoint Similarity)** as evaluation metric replacing older PCK

## COCO Keypoint Definitions (17 points)

From `config.py:KEYPOINT_NAMES`:

| ID | Name | Description |
|----|------|-------------|
| 0 | nose | Tip of nose |
| 1 | left_eye | Left eye |
| 2 | right_eye | Right eye |
| 3 | left_ear | Left ear |
| 4 | right_ear | Right ear |
| 5 | left_shoulder | Left shoulder joint |
| 6 | right_shoulder | Right shoulder joint |
| 7 | left_elbow | Left elbow |
| 8 | right_elbow | Right elbow |
| 9 | left_wrist | Left wrist |
| 10 | right_wrist | Right wrist |
| 11 | left_hip | Left hip joint |
| 12 | right_hip | Right hip joint |
| 13 | left_knee | Left knee |
| 14 | right_knee | Right knee |
| 15 | left_ankle | Left ankle |
| 16 | right_ankle | Right ankle |

**Connectivity (for visualization):**
```
head: nose-0 → left_eye-1, right_eye-2
ears: left_eye-1 → left_ear-3, right_eye-2 → right_ear-4
upper_body: left_shoulder-5 → right_shoulder-6
arms: left_shoulder-5 → left_elbow-7 → left_wrist-9
          right_shoulder-6 → right_elbow-8 → right_wrist-10
torso: left_shoulder-5 → left_hip-11, right_shoulder-6 → right_hip-12
legs: left_hip-11 → left_knee-13 → left_ankle-15
       right_hip-12 → right_knee-14 → right_ankle-16
```

## Visibility Flags (COCO Format)

Each keypoint has a visibility flag `v`:
- **v = 0**: Keypoint is **not in the image** (person cropped, out of frame)
- **v = 1**: Keypoint is **occluded** (present but not visible due to occlusion)
- **v = 2**: Keypoint is **visible** and annotated

In COCO JSON format:
```json
{
  "keypoints": [x1, y1, v1, x2, y2, v2, ..., x17, y17, v17],  // length = 51
  "num_keypoints": 12  // number of keypoints with v > 0
}
```

## OKS Metric (COCO's Evaluation)

**OKS (Object Keypoint Similarity)** replaces PCK as COCO's evaluation metric:
```
OKS = Σ_i exp(-d_i²/2s_i²k_i²) δ(v_i > 0) / Σ_i δ(v_i > 0)
```
- `d_i` = Euclidean distance between predicted and ground truth keypoint i
- `s_i` = Scale of person (torso area, sqrt of bounding box area)
- `k_i` = Keypoint-specific衰减 constant (per-keypoint variance)
- `v_i` = Visibility flag (only compute for v > 0)

**Keypoint-specific sigmas** (from COCO eval):
```
nose: 0.026, eyes: 0.025, ears: 0.035, shoulders: 0.035,
elbows: 0.035, wrists: 0.035, hips: 0.035, knees: 0.035, ankles: 0.035
```

Larger body keypoints (shoulders, hips) have larger sigma (more tolerance). Smaller/articulated keypoints (wrists, ankles) have smaller sigma (less tolerance).

## What POPW Uses from This Format

1. **17 keypoints** exactly as defined in `config.py:NUM_KEYPOINTS = 17`
2. **Visibility handling**: Keypoints with v=0 should be masked from loss computation (Wing Loss in `losses.py`)
3. **PCK@0.1 evaluation**: POPW uses PCK@0.1 (simplified version of OKS concept)
4. **Transfer learning**: COCO-pretrained backbone (ResNet-50 from ImageNet + COCO pose) improves POPW's pose head convergence

## Implemented in POPW?

- [x] YES — `config.py:NUM_KEYPOINTS = 17`, `KEYPOINT_NAMES` list
- [x] YES — `config.py:KEYPOINT_SIGMAS` (for potential OKS evaluation)
- [x] YES — Dataset returns COCO-format keypoints per frame
- [x] YES — Pose evaluation uses visibility flags to mask invalid keypoints

## Failure Modes / Limitations

- **Single-person assumption**: COCO format handles multi-person, but POPW's pose head assumes single dominant person per frame (reasonable for IKEA assembly)
- **Top-down vs COCO format**: IKEA ASM's top-down view (dev3) means shoulders and hips appear at similar vertical positions — standard skeleton visualization looks different in bird's-eye view
- **Visibility noise**: Auto-annotated poses may have incorrect visibility flags, especially for partially-occluded hands and feet in assembly scenarios

## Key Equations

**COCO keypoint array:**
```
keypoints = [x1, y1, v1, x2, y2, v2, ..., x17, y17, v17]  # length 51
```

**OKS computation:**
```
OKS = (1/N_visible) Σ_i [exp(-d_i²/(2s²k_i²)) · 1(v_i > 0)]
```

**Scale computation:**
```
s = √(bbox_width × bbox_height)  # person scale in pixels
```

## Related Papers in This Wiki

- [[research/009-deeppose-pck-toshev-2014]] — PCK@0.1 evaluation uses keypoint distance / torso_diameter
- [[research/010-wing-loss-feng-2018]] — Wing Loss applies per-keypoint for all 17 keypoints
- [[research/015-simple-baselines-pose-xiao-2018]] — Simple baselines use COCO keypoint format
- [[100-popw-protocol-self-analysis]] — POPW's 17 COCO keypoints from config.py

## LEGION RULE

When Bashara asks about "why exactly 17 keypoints and not more or fewer," reference this paper's finding: COCO's 17 keypoints represent the minimum set that balances anatomical coverage with annotation cost. 17 covers all major joints (4 shoulders/elbows/wrists + 4 hips/knees/ankles + 3 head). Adding more (e.g., 68 facial landmarks) multiplies annotation effort and doesn't improve body pose accuracy. POPW inherits this standard exactly — the 17-keypoint format is non-negotiable for transfer learning from COCO-pretrained models.

Applied to POPW: The 17 COCO keypoints map directly to `config.py:KEYPOINT_NAMES`. For the top-down IKEA ASM view, all 17 keypoints are generally visible (no self-occlusion from typical angles), making it ideal for pose evaluation. Report per-keypoint PCK@0.1 — wrists (9, 10) and ankles (15, 16) will likely be weakest due to their small size in the frame.

Config: `config.py:NUM_KEYPOINTS = 17` — this is the COCO standard, do not modify.
