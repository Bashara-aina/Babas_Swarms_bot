---
title: Planner 2026 04 21 Industreal Adaptation
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Plan: Adapt POPW code for IndustReal dataset
Date: 2026-04-21
Type: FEATURE (code adaptation)
Context gathered:
- POPW source: /media/newadmin/master/POPW/popw_main/ (8 Python files)
- IndustReal dataset: /media/newadmin/dataset/industreal/ (25 recordings, split CSVs)
- IndustReal has 3 tasks: PSR (temporal segmentation), AR (74 action classes), ASD (24 COCO detection classes)
- Single egocentric camera (rgb/), COCO OD format, head pose + hand joints CSVs
- IKEA POPW has ResNet50-FPN + 3 heads (Detection, Pose, Activity)

Risk assessment:
- HIGH: PSR task (Procedure Step Recognition) is a NEW task type not in IKEA — requires new head architecture
- HIGH: Pose head uses COCO 17-keypoint OpenPose format — IndustReal uses head pose (3 DoF) + hand joints (52 coords)
- MEDIUM: Many imports hardcode IKEA paths/constants — need systematic find-and-replace
- LOW: losses.py, benchmark.py mostly task-agnostic

Approach: 6 contracts split by file dependency order:
1. config.py first (all paths/classes derived from it)
2. model.py second (depends on config)
3. dataset third (depends on config + model structure)
4. losses fourth (minimal changes, depends on config)
5. train.py fifth (depends on all above)
6. evaluate.py sixth (depends on all above)
7. benchmark.py last (minimal changes)

Files not copied: temporal_metrics.py (IKEA-specific imports, but concepts transfer)
