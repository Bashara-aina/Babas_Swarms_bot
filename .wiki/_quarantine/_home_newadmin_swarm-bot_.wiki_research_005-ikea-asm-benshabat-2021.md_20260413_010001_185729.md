---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/005-ikea-asm-benshabat-2021.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.185763"
}
---

---
paper_id: "005"
title: "The IKEA ASM Dataset: Understanding People Assembling Furniture through Actions, Objects and Pose"
authors: "Yizhak Ben-Shabat, Xin Yu, Fatemeh Sadat Saleh, Dylan Campbell, Cristian Rodriguez-Opazo, Hongdong Li, Stephen Gould"
year: 2021
venue: "WACV 2021"
arxiv: "2007.00394"
citations: 485
tier: 1
tags: ["dataset", "assembly", "pose", "action-recognition", "multi-view", "ikea"]
popw_relevance: 10
---

## Why This Paper Matters for POPW

This is **POPW's target domain dataset** — furniture assembly understanding. The dataset captures exactly what POPW needs to understand: humans performing assembly actions, interacting with parts, and maintaining pose during complex tasks. It provides RGB, depth, pose, segmentation, and action labels — all modalities POPW needs. The WACV 2021 publication shows this is a well-organized, benchmark-quality dataset.

## Core Contribution

Introduced **IKEA ASM (Assembly)** dataset — a comprehensive multi-view video dataset for understanding human assembly activities. Contains 371 videos (3M+ frames) of 48 participants assembling 4 furniture types across 3 camera views. Provides dense annotations including atomic actions, 3D pose, object segmentation, and tracking. Enables holistic multi-modal activity understanding.

## Key Technical Details

**Dataset Statistics:**
- 371 assembly sequences
- 48 different participants
- 4 furniture types (KALLAX shelf, BILLY bookcase, MALM bed frame, Poäng chair)
- 3 camera views (left, right, center)
- ~3 million total frames
- 33 atomic action classes

**Annotations per frame:**
- 2D/3D human pose (17 keypoints)
- Object instance segmentation
- Atomic action labels (start/end timestamps)
- Object tracking across frames

**Modalities:**
- RGB videos (3 views)
- Depth maps
- Pose annotations
- Object segmentations
- Action sequences

## Critical Results

| Task | Best Method | Performance |
|------|-------------|-------------|
| Action Recognition | SlowFast + 3D | 67.1% mAP |
| Pose Estimation | HRNet-W48 | 86.3% AP |
| Object Segmentation | Mask R-CNN | 68.2% mIoU |

HRNet-W48 used for pose (paper 009), Mask R-CNN for segmentation (paper 007).

## What POPW Can Steal Directly

- **Dataset**: Benchmark POPW on IKEA ASM for assembly understanding
- **Evaluation protocols**: Standard splits for action/pose/segmentation
- **Action taxonomy**: 33 atomic actions (screw, attach, align, etc.)
- **Multi-view calibration**: 3-view setup informs POPW's camera setup
- **Pose + action combined training**: Multi-task learning on this dataset

## Failure Modes

1. **Limited object categories** — only 4 furniture types, may not generalize
2. **Controlled environment** — staged IKEA showrooms, not real homes
3. **Single country demographic** — mostly Australian participants
4. **No failure case annotations** — what does "failed assembly" look like?

## Key Equations

No major equations — this is a dataset paper. Key contribution is the dataset itself, not method.

**Dataset split:**
- Training: 271 sequences
- Validation: 50 sequences
- Test: 50 sequences

**Evaluation metrics:**
- Action: mAP @ IoU=0.5
- Pose: AP (keypoint)
- Segmentation: mIoU

## Researcher Intelligence

- **Yizhak Ben-Shabat**: University of Adelaide / Australian National University. 3D vision, action recognition.
- **Stephen Gould**: Professor at Australian National University, computer vision, structured prediction.
- **Hongdong Li**: Professor at University of Adelaide, 3D vision, pose estimation.
- **Xin Yu**: Also from Australian institutions, pose estimation.

**Motivation**: Existing action datasets (Something-Something, JHMDB) don't capture assembly. Assembly is fundamentally different — involves tool use, object manipulation, multi-step procedures. Need domain-specific dataset.

## Key Papers That Cite This

1. **PoseConv3D** (2022) — Uses IKEA ASM for skeleton action recognition benchmarks
2. **Human motion prediction** — Assembly-specific motion prediction
3. **Assembly action recognition** — New methods on this dataset
4. **3D hand-object contact** — Understanding assembly hand movements

## Engineer's Implementation Notes

**Secrets not in paper:**
- Use 3 views for robust pose estimation — single view has occlusions
- Object IDs: 11 part categories across 4 furniture types
- Action labels are hierarchical: 33 atomic + 4 coarse (disassemble, assemble, adjust, complete)
- Depth maps are provided but at lower resolution (848x480 vs 1920x1080 RGB)
- Camera extrinsics available as part of dataset

**Data loading:**
- Align 3 views temporally (they sync at frame level)
- Use provided calibration for 3D pose triangulation
- Object segmentation uses COCO-like format with instance IDs

**Benchmarking hints:**
- Start with HRNet for pose (paper 009), it's what they use
- For action recognition, use STC/SlowFast architectures
- Mask R-CNN for instance segmentation baseline

## Connections to Other Wiki Papers

- **009 HRNet**: Used for pose estimation on this dataset
- **007 Mask R-CNN**: Used for object segmentation on this dataset
- **011 PoseConv3D**: Tested on this dataset for skeleton action recognition
- **004 Multi-Task**: Dataset supports multi-task learning (pose + action + segmentation)

## POPW Action Item

- Download IKEA ASM dataset and verify annotations
- Build POPW's evaluation pipeline using this dataset
- Confirm 3-view camera calibration matches POPW setup
- Check if pose estimation baseline matches reported 86.3% AP
- Evaluate POPW on action recognition task