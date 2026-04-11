---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/041-sener-assembly101-2022.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-11T18:14:42.434718"
}
---

---
paper_id: "041"
title: "Assembly101: A Large-Scale Multi-View Video Dataset for Understanding Procedural Activities"
authors: "Sener, Fadime; Chatterjee, Dibyadip; Shelepov, Daniel; He, Kun; Singhania, Dipika; Wang, Robert; Yao, Angela"
year: 2022
venue: "CVPR 2022"
arxiv: "2203.14712"
doi: "10.48550/arXiv.2203.14712"
citations: "405+"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "Foundational dataset for procedural activity understanding; multi-view egocentric + static cameras"
key_contribution: "First multi-view action dataset with simultaneous static (8) and egocentric (4) recordings; 4321 videos, 100K+ action segments"
tags:
  - multi-view dataset
  - procedural activities
  - egocentric video
  - assembly understanding
  - toy vehicle assembly
dataset_stats:
  videos: 4321
  duration: "513 hours"
  action_segments: "100K+ coarse, 1M+ fine-grained"
  3d_hand_poses: "18M"
  num_objects: 101
  num_views: "8 static + 4 egocentric"
key_features:
  - "Multi-view: static AND egocentric cameras"
  - "Unscripted assembly/disassembly of 101 toy vehicles"
  - "Rich natural variations in action ordering"
  - "Mistake detection annotations"
  - "Long-tailed action distributions"
tasks_enabled:
  - "Action recognition"
  - "Action anticipation"
  - "Temporal segmentation"
  - "Mistake detection"
dataset_url: "https://assembly-101.github.io/"
---

# Summary

Assembly101 is a foundational procedural activity dataset featuring 4,321 videos of people assembling and disassembling 101 different "take-apart" toy vehicles. The dataset introduces the unique recording format of simultaneous static (8 views) and egocentric (4 GoPro cameras) video, capturing natural variations in how people perform assembly procedures.

## Key Contributions

1. **First Multi-View Egocentric Dataset**: Combines static surveillance-style cameras with wearable egocentric cameras
2. **Natural Variation Capture**: People work without fixed instructions, leading to variations in order, mistakes, and corrections
3. **Comprehensive Annotations**: 100K+ coarse and 1M+ fine-grained action segments, plus 18M 3D hand poses

## Dataset Characteristics

- **Content**: Assembly and disassembly of 101 toy vehicle types
- **Views**: 8 static cameras + 4 egocentric cameras (12 total views)
- **Scale**: 4,321 videos, 513 hours of synchronized video
- **Annotations**: Action segments, 3D hand poses, mistake annotations

## Relevance to POPW

Assembly101 provides a critical benchmark for evaluating procedural understanding. Its multi-view nature enables study of view-invariant action recognition. POPW should demonstrate competitive performance on Assembly101 alongside IKEA ASM.

## Citation

```bibtex
@article{sener2022assembly101,
  title={Assembly101: A Large-Scale Multi-View Video Dataset for Understanding Procedural Activities},
  author={Sener, Fadime and Chatterjee, Dibyadip and Shelepov, Daniel and He, Kun and Singhania, Dipika and Wang, Robert and Yao, Angela},
  journal={arXiv preprint arXiv:2203.14712},
  year={2022},
  note={CVPR 2022}
}
```
