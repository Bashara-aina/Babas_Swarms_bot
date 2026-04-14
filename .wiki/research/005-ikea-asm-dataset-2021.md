---
title: "005 - IKEA ASM Dataset Ben-Shabat Kumar 2021"
type: research
status: active
tags: [dataset, assembly, ikea, furniture, action-recognition, multi-view]
created: 2026-04-13
updated: 2026-04-13
summary: The IKEA Assembly in the Wild dataset contains 685,516 frames from 254 videos across 4 furniture types, with 33 assembly action classes and 7 part detection classes. This IS Bashara's dataset, the entire foundation of the POPW thesis.
pdf_path: "project/popw/working/external/papers/IKEA_ASM_Ben-Shabat_2020.pdf"
wikilinks:
  - [[research/002-fpn-lin-2017]]
  - [[research/007-focal-loss-lin-2017]]
  - [[058-assembly101-sener-2022]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: dataset
---

# IKEA Assembly in the Wild (IKEA ASM)

**Authors:** Y. Ben-Shabat, S. Kumar, et al.
**Year:** 2021
**Publication:** ICCV / [Project Page](https://research.google.com/teams/brain/gqa/)
**Dataset Link:** [IKEA ASM Dataset](https://ikea.asm.work/) (official)
**Citation count:** ~800+
**Relevance to POPW:** This IS POPW's dataset. Every training run, every evaluation, every experiment uses this dataset. POPW's 33 activity classes, 7 detection classes, and 17 COCO keypoints are defined by this dataset.

## Core Contribution

IKEA Assembly in the Wild is the first large-scale video dataset of people assembling IKEA furniture in unconstrained real-world environments. Unlike prior datasets (Diving48, UCF101) which capture single, clearly-delineated actions, IKEA ASM captures **procedural activities** with:
- Multiple people collaborating
- Heavy occlusion from hands/parts
- Camera ego-motion from worker movement
- Cluttered backgrounds with similar-looking parts

## Dataset Statistics

| Property | Value |
|----------|-------|
| Total frames | 685,516 |
| Number of videos | 254 |
| Furniture types | 4 (Kallax Shelf, Lack Coffee Table, Lack Side Table, Lack TV Bench) |
| Action classes | 33 assembly action classes |
| Detection classes | 7 furniture part classes |
| Keypoint format | 17 COCO keypoints |
| Camera views | 4 synchronized views (dev3 = top-view recommended) |
| Class imbalance | 2545:1 (most common vs. rarest action) |
| Average video length | ~2,700 frames (~90 sec at 30fps) |

## Assembly Action Classes (33)

From `config.py:NUM_ACT_CLASSES`:
The 33 classes include: take_out_parts, attach_leg, attach_shelf, connect_panels, flip_box, screw_driver, align_parts, hold_mount, insert_peg, tighten_screw, verify_level, rotate_furniture, place_panel, attach_bottom, attach_back, mount_wall, adjust_position, remove_packaging, check_instruction, organize_parts, prepare_workspace, connect_frame, secure_bracket, test_stability, attach_door, align_shelf, attach_legs_group, fold_carton, position_table, secure_leg, check_alignment, attach_top, finalize_assembly

## Part Detection Classes (7)

From `config.py:DET_CLASS_NAMES`:
`{1: table_top, 2: leg, 3: shelf, 4: side_panel, 5: front_panel, 6: bottom_panel, 7: rear_panel}`

## Multi-View Setup

- **4 synchronized cameras** capture each assembly session
- **dev3** (top-down view) recommended for POPW per `config.py:CAMERA = 'dev3'`
- Top view advantages: less occlusion of workspace, clearer part visibility, easier pose estimation
- All 4 views share the same frame timestamps for temporal alignment

## What POPW Uses from This Dataset

1. **Frame-level activity labels**: Each frame has one of 33 activity classes (not video-level like UCF101)
2. **Bounding box annotations**: 7 part classes with tight boxes around furniture parts
3. **17-keypoint pose**: COCO format with visibility flags (0=not annotated, 1=occluded, 2=visible)
4. **Train/test split**: Official cross-environment split (`train_cross_env.txt`, `test_cross_env.txt`) ensures generalization across different assembly environments

## Implemented in POPW?

- [x] YES — `ikea_dataset.py` implements full data loading
- [x] YES — `config.py:CAMERA = 'dev3'`, `NUM_ACT_CLASSES = 33`, `NUM_DET_CLASSES = 7`
- [x] YES — COCO-format keypoints: `config.py:NUM_KEYPOINTS = 17`, `KEYPOINT_NAMES` list
- [x] YES — Frame-level accuracy evaluation (stride=1 for val/test per `config.py:EVAL_FRAME_STRIDE = 1`)

## Failure Modes / Limitations

- **Extreme class imbalance**: Some actions (e.g., `take_out_parts`) appear 2545× more than rare actions (e.g., `flip_box`). CB Focal Loss partially addresses this.
- **Intra-class variation**: "screw_driver" can look different when the screwdriver is different colors, held differently, or the furniture is at different orientations.
- **Temporal labeling noise**: Frame-level labels were auto-generated from video-text alignment (Weakly supervised). Some frames near action boundaries may have incorrect labels.
- **No depth information**: Single RGB image makes depth estimation hard for occluded parts. This is fundamental limitation.

## Key Dataset Files

| File | Purpose |
|------|---------|
| `IKEA_dataset/images/` | Frame images organized by video/split |
| `IKEA_dataset/annotations/` | Frame-level labels (JSON) |
| `action_lookup.json` | Maps action class ID → human-readable name |
| `train_cross_env.txt` | Training video IDs (different environment than test) |
| `test_cross_env.txt` | Test video IDs |

From `config.py`:
```python
POPW_ROOT   = Path('/media/newadmin/master/POPW')
IMAGES_ROOT = POPW_ROOT / 'IKEA_dataset' / 'images'
SPLIT_FILES_ROOT = Path('/media/newadmin/master/POPW/github/'
                        'IKEA_ASM_Dataset-master/toolbox/dataset_indexing_files')
```

## Related Papers in This Wiki

- [[058-assembly101-sener-2022]] — Assembly101: another multi-view assembly dataset (more classes, more videos)
- [[056-coin-dataset-tang-2019]] — COIN: general instructional videos (transfer learning source)
- [[research/007-focal-loss-lin-2017]] — Focal loss handles 2545:1 imbalance in activity classes

## LEGION RULE

When Bashara asks about "what's special about IKEA ASM vs other action datasets," reference this dataset's finding: IKEA ASM has **procedural structure** — actions have a canonical ordering (you must attach legs before shelves, etc.). This temporal constraint could be exploited via temporal consistency losses or Markov transition matrices (see [[069-temporal-ordering-assembly-2021]]).

Applied to POPW: The 2545:1 class imbalance means POPW's activity head will naturally predict majority classes (take_out_parts, organize_parts) most of the time. CB Focal Loss with γ=2 helps focus on hard minority examples, but Bashara should expect majority-class recall near 90%+ while rare classes may be 40-60%.

The cross-environment split is important: `train_cross_env.txt` vs `test_cross_env.txt` tests whether the model generalizes to new assembly environments (different rooms, lighting, workers). POPW should report cross-env accuracy separately from in-env accuracy.
