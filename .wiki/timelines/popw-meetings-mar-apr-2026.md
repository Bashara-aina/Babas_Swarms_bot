---
title: POPW Research Meetings — Phase 3 (Mar–Apr 2026)
type: timeline
status: active
tags: [popw, research, meetings, pdd-pivot, temporal-attention, conference-prep]
created: 2026-04-13
updated: 2026-04-13
summary: "Final phase of POPW meetings: PDD pivot officially adopted, temporal attention added to activity head, dataset alternatives analyzed (Assembly101, IndustReal, HA4M, Ego-Exo4D), and conference paper preparation begins with submission target."
wikilinks:
  - [[projects/popw-research]]
  - [[timelines/popw-meetings-jan-mar-2026]]
  - [[concepts/pose-derived-detection]]
  - [[concepts/film-modulation]]
confidence: high
source: research
project: popw
---

# POPW Research Meetings — Phase 3 (Mar–Apr 2026)

## TL;DR

Phase 3 locked in the PDD (Pose-Derived Detection) pivot — removing the neural detection head entirely and deriving bounding boxes mathematically from pose keypoints. Temporal attention was added to the activity head, and dataset alternatives (Assembly101, IndustReal, Ego-Exo4D) were evaluated for training and validation. Conference paper drafting began with a submission target.

## 12th Meeting (continued) — March 15, 2026

**Paper Framing Established**

POPW positioned as addressing the problem of joint detection + pose + activity from a single RGB frame (not video). Key differentiator: **pose-conditioned multi-task architecture** with FiLM modulation.

Three evaluation axes:
1. Action recognition (33 atomic actions)
2. 2D pose estimation (17 COCO keypoints)
3. Detection (7 object classes — but PDD planned)

Target use case: CCTV-based assembly monitoring without marker-based motion capture.

**Why not just use separate models?** (IKEA ASM paper comparison)
- Single backbone = shared representation
- Pose conditions activity = structured inference, not black-box
- Interpretable outputs = can inspect boxes and keypoints

## 13th Meeting — March 25, 2026

**Simultaneous Hypothesis Refined**

The "simultaneous hypothesis" was clarified: the model should consume both visual AND pose features simultaneously at the activity head, forcing structured reasoning rather than visual bias.

Proposed architecture change: Temporal attention in activity head to capture sequential context (activity = sequence, not single frame).

Ablation plan:
- FiLM vs no FiLM
- Temporal attention vs frame-level
- PDD vs neural detection

## 14th Meeting — April 9, 2026

**PDD Pivot Officially Adopted + Dataset Alternatives**

**Architecture finalization**:
- Remove detection head entirely
- Worker box: min-max of 17 keypoints + safety padding
- Bottle box: wrist-anchored fixed radius (industrial logic: bottles only at wrist when holding)
- Activity state: verified via sequence (Checking → Rotation → Storing)

**Dataset alternatives evaluated**:

| Dataset | Strength | POPW Use |
|---------|---------|---------|
| Assembly101 | 133 actions, 51 objects, 3D pose | Secondary benchmark |
| HA4M | 4M frames, industrial | Scale target / efficiency comparison |
| IndustReal | Real factory, screw/bracket | Domain-specific fine-tuning |
| Ego-Exo4D | 1,400hrs egocentric, hand pose | Head-mounted camera validation |
| HA-ViD | 219 actions, generic assembly | Cross-dataset validation |

**Priority schedule** (as of April 9):
- Now (2 weeks): Temporal attention implementation, ablation training
- 3–4 weeks: Assembly101 + IndustReal dataset integration
- 5–6 weeks: Paper visualizations and drafting

**Conference submission target**: Mid-to-late 2026 (specific venue TBD)

## Research Arc: Phase 3

```
Mar 2026: PDD pivot formally adopted
Mar 2026: Temporal attention planned for activity head
Mar 2026: Dataset alternatives evaluated (Assembly101, IndustReal, Ego-Exo4D)
Apr 2026: Ablation training plan (FiLM vs no-FiLM, PDD vs neural detection)
Apr 2026: Paper drafting begins
```

## Final POPW Architecture (April 2026)

```
Input [B,3,480,640]
    ↓
CSPDarkNet-50 Backbone (ImageNet pretrained, BN frozen first 20 epochs)
    ↓
FPN Neck (P3, P4, P5, P6, P7 feature pyramids)
    ↓
    ├── Pose Head (13 COCO keypoints × 2 coords + visibility) → pose context z
    ├── FiLM Generator (z → γ, β ∈ R^256) → modulate P3 features
    ├── Activity Head (GAP over modulated features → 33-class activity)
    ├── Worker Box = min-max(keypoints) + safety padding (PDD)
    └── Bottle Box = wrist_anchor ± fixed_radius (PDD)
```

## Key Decisions from Phase 3

| Decision | Rationale |
|----------|----------|
| Remove detection head | Pose achieves 95% activity; detection redundant |
| PDD replaces detection | Mathematically derived boxes from pose |
| Temporal attention | Capture sequential context for ambiguous activities |
| Assembly101 secondary | More actions but less pose detail than IKEA ASM |
| Ego-Exo4D validation | Only egocentric dataset for head-mounted camera |

## Current Status (End of Phase 3)

POPW is in active paper preparation:
- Architecture: FiLM + PDD + temporal attention (planned)
- Training: ~50 GPU-hours for ablation studies
- Dataset: IKEA ASM primary, Assembly101/IndustReal secondary
- Submission: Conference paper target mid-2026

## Related

- [[projects/popw-research]]
- [[timelines/popw-meetings-jan-mar-2026]]
- [[concepts/pose-derived-detection]]
- [[concepts/film-modulation]]
- [[concepts/wise-iou]]
- [[entities/ikea-asm]]
- [[entities/assembly101]]
- [[entities/ego-exo4d]]
