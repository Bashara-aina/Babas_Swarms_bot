---

title: "ADR-2026-04: Conference Submission Strategy"
type: decision
status: active
tags: [popw, conference, submission, strategy, timeline]
created: 2026-04-13
updated: 2026-04-13
summary: "Conference submission strategy for POPW research targeting mid-to-late 2026 venues focused on computer vision, human activity recognition, or industrial AI. Primary target: CV/PRCV workshop on multi-task learning; secondary: ICRA/IROS for industrial robotics audience."
wikilinks:
  - [[projects/popw-research]]
  - [[concepts/film-modulation]]
  - [[concepts/pose-derived-detection]]
confidence: high
source: research
project: popw

---


# ADR-2026-04: Conference Submission Strategy

## Status

Draft: April 2026
Target submission: Mid-to-late 2026

## Context

POPW research is approaching publication-ready state after 14 weekly meetings (November 2025 – April 2026). Key results:

- **95.2% activity accuracy** on 33-class IKEA ASM atomic actions
- **78.1% pose PCK** on 17 COCO keypoints
- **PDD architecture** — mathematically derived detection from pose (O(1) verification)
- **FiLM modulation** — pose-conditioned activity recognition at O(d) compute
- **Efficiency argument**: achieves HA4M-level recognition without HA4M-level data scale

Target venues must cover: multi-task learning, pose estimation, activity recognition, or industrial AI.

## Decision

**Target venue hierarchy (in order of fit):**

| Priority | Venue | Rationale |
|----------|-------|-----------|
| 1st | CVPR/PRCV Workshop on Multi-Task Learning | Direct fit: multi-task pose+detection+activity |
| 2nd | ICRA/IROS Workshop on Human-Robot Collaboration | Industrial assembly, robotics, pose |
| 3rd | ACCV or BMVC | General computer vision, activity recognition |
| 4th | NeurIPS or ICCV (pose/activity workshops) | Large venue, specialized workshops |

## Submission Timeline (April 2026 onwards)

### Now → +2 weeks (mid-April)
- [ ] Implement temporal attention in activity head
- [ ] Complete ablation training (FiLM vs no-FiLM, PDD vs neural detection)
- [ ] Draft skeleton paper outline

### +3-4 weeks (early May)
- [ ] Run Assembly101 + IndustReal dataset experiments
- [ ] Gather all paper visualizations
- [ ] Complete first draft

### +5-8 weeks (late May–June)
- [ ] Paper revision and co-author review
- [ ] Submit to 1st priority venue
- [ ] Prepare supplementary materials (video demonstration)

### +9-12 weeks (July–August)
- [ ] Rebuttal period (if required)
- [ ] Camera-ready revision
- [ ] Prepare presentation

## Paper Structure

### Proposed Sections

1. **Introduction**: Multi-task learning for industrial assembly monitoring
2. **Related Work**: IKEA ASM, HA4M, Assembly101 baselines
3. **WorkerNet Architecture**: Backbone + FPN + 3 heads
4. **FiLM Modulation**: Pose-conditioned feature recalibration
5. **PDD (Pose-Derived Detection)**: Mathematical bounding box derivation
6. **Experiments**: IKEA ASM benchmarks, ablation studies
7. **Discussion**: Efficiency argument vs HA4M-scale data
8. **Conclusion**: Industrial applicability

### Key Claims to Defend

| Claim | Evidence |
|-------|----------|
| Pose-conditioned multi-task > separate models | FiLM + late fusion = 95.2% activity |
| PDD eliminates detection gradient conflict | IoU = f(PCK), no neural uncertainty |
| Efficiency: ~50K frames vs 4M (HA4M) | Same accuracy, 80× less data |
| Interpretable outputs | Keypoint math, not black-box |

## Budget Consideration

| Item | Cost | Note |
|------|------|------|
| GPU training (ablation) | ~50 GPU-hours | RTX 3060, ~$5–10 |
| Dataset licensing | Free (academic) | IKEA ASM, Assembly101 |
| Paper submission | $0–100 | Venue-dependent |
| Video demonstration | $0 | Screenpipe capture |

Total publication cost: <$100

## Related

- [[projects/popw-research]]
- [[concepts/film-modulation]]
- [[concepts/pose-derived-detection]]
- [[entities/ikea-asm]]
- [[entities/assembly101]]
