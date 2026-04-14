---
title: Sener Assembly101 2022
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- research
created: '2026-04-14'
updated: '2026-04-14'
summary: Assembly101 is a foundational procedural activity dataset featuring 4,321
  videos of people assembling and disassembling 101 different "take-apart" toy vehicles.
  The dataset introduces the unique re...
wikilinks: []
confidence: medium
source: research
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
