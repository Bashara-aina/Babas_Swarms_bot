---
title: Ha4M Dataset 2022
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
summary: HA4M (Human Action Multi-Modal Monitoring in Manufacturing) is a comprehensive
  multi-modal dataset for assembly action recognition. It features 217 videos of 41
  subjects performing assembly of an E...
wikilinks: []
confidence: medium
source: research
---

# Summary

HA4M (Human Action Multi-Modal Monitoring in Manufacturing) is a comprehensive multi-modal dataset for assembly action recognition. It features 217 videos of 41 subjects performing assembly of an Epicycloid Gear Train (EGT), recorded using a Microsoft Azure Kinect camera providing six synchronized data modalities.

## Key Contributions

1. **Six Modalities Simultaneously**: RGB, Depth, IR, RGB-D-Aligned, Point Clouds, and Skeleton data
2. **Realistic Assembly Task**: 12 action types for assembling an EGT with variations in execution order
3. **Multi-laboratory Acquisition**: Data collected in Italy and Spain for increased diversity

## Dataset Characteristics

- **Task**: Assembly of Epicycloid Gear Train (13 components, 12 action types)
- **Subjects**: 41 participants (15 female, 26 male), ages 23-60
- **Actions**: Fine-grained assembly actions with natural variations in order
- **Data Volume**: ~4.1 TB total

## Relevance to POPW

HA4M provides a standardized benchmark for multi-modal action recognition in manufacturing. POPW's multi-modal approaches should be evaluated on this dataset alongside IKEA ASM.

## Citation

```bibtex
@article{ha4m2022,
  title={The HA4M dataset: Multi-Modal Monitoring of an assembly task for Human Action recognition in Manufacturing},
  author={Cicirelli, Grazia and Marani, Roberto and Romeo, Laura and García Domínguez, Manuel and Heras, Jónathan and Perri, Anna G. and D'Orazio, Tiziana},
  journal={Scientific Data},
  volume={9},
  year={2022}
}
```
