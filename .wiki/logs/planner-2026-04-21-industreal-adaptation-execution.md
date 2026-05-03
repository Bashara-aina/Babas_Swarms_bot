---
title: Planner 2026 04 21 Industreal Adaptation Execution
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Execution Order
Serial (must run in sequence): 1 → 2 → 3 → 4 → 5 → 6 → 7
Parallel (can run simultaneously): none (each contract depends on the previous)
Final gate (must run last): Contract #7

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PSR head architecture is novel (not in IKEA) — may need iterative design | HIGH | HIGH | Start with simple MLP per-frame classification; temporal convolutions can be added later |
| Head pose format in IndustReal (euler angles + gaze) differs from COCO 17-keypoint | HIGH | MEDIUM | Replace PoseHead entirely with head pose regression MLP (3 DoF + gaze) |
| ASD (assembly state detection) COCO format differs slightly from IKEA COCO format | MEDIUM | LOW | Use same parsing logic; verify category IDs match 1-24 range |
| Class counts for PSR (36 steps) may differ between recordings | MEDIUM | MEDIUM | Load PSR_labels.csv during init to determine max step ID |
| Train.py may OOM with full 3-task joint training | MEDIUM | HIGH | Use gradient accumulation; validate with batch_size=4 first |
| Multiple hardcoded IKEA paths in evaluate.py | HIGH | MEDIUM | Systematic find-and-replace; verify all paths use config vars |

## Notes
- Contract #2 (model.py) is the most complex due to PSR head design
- Contract #3 (dataset) is the most file-heavy due to 5 annotation formats
- losses.py should be mostly copy with PoseHead/WingLoss removed
- benchmark.py is almost entirely copy (just model class name changes)
