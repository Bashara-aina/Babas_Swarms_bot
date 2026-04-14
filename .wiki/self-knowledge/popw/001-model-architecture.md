---
title: Model Architecture
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- self-knowledge
created: '2026-04-14'
updated: '2026-04-14'
summary: '- **Path**: `/home/newadmin/Documents/popw-protocol/datasets/`'
wikilinks: []
confidence: medium
source: research
---

# popw Protocol Model Architecture

## Status: PARTIAL EXTRACTION

### Source Location
- **Path**: `/home/newadmin/Documents/popw-protocol/datasets/`
- **Content**: COCO dataset (176MB), not popw model code

### Expected Architecture (Not Found)
Based on typical popw (point-of-work) protocol research:
- **FiLM** (Feature-wise Linear Modulation) — conditioning mechanism
- **ResNet** — Backbone feature extractor
- **FPN** (Feature Pyramid Network) — Multi-scale feature fusion
- **Hyperparameters**: learning rates, batch sizes, augmentation strategies

### Actual Content Found
```
datasets/
├── coco/  (COCO dataset directory)
└── coco2017labels-segments.zip  (176MB COCO annotations)
```

### Note
The popw-protocol research code itself was not found in the expected location. 
The datasets directory only contains the COCO computer vision dataset which is likely
used for training/evaluation but is not the popw model architecture itself.

---
*Extracted: 2026-04-11 by @worker*
