---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/044-ha4m-dataset-2022.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-11T18:14:42.416813"
}
---

---
paper_id: "044"
title: "The HA4M Dataset: Multi-Modal Monitoring of an Assembly Task for Human Action Recognition in Manufacturing"
authors: "Cicirelli, Grazia; Marani, Roberto; Romeo, Laura; García Domínguez, Manuel; Heras, Jónathan; Perri, Anna G.; D'Orazio, Tiziana"
year: 2022
venue: "Scientific Data (Nature)"
doi: "10.1038/s41597-022-01843-z"
citations: "61"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "First multi-modal assembly dataset with 6 data types; enables multi-modal fusion research"
key_contribution: "First multi-modal dataset about assembly containing RGB, Depth, IR, RGB-D-Aligned, Point Clouds, and Skeleton data"
tags:
  - multi-modal dataset
  - manufacturing
  - assembly action recognition
  - RGB-D
  - skeleton data
  - Azure Kinect
dataset_stats:
  videos: 217
  subjects: 41
  actions: 12
  total_annotations: 4124
data_types:
  - "RGB images (2048×1536)"
  - "Depth maps (640×576, 16-bit)"
  - "IR images"
  - "RGB-to-Depth-Aligned images"
  - "Point Clouds (PLY format)"
  - "Skeleton data (32 joints)"
task: "Assembly of Epicycloid Gear Train (EGT)"
dataset_url: "https://baltig.cnr.it/ISP/ha4m"
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
