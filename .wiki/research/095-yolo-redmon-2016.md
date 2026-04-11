---
paper_id: 095
title: "You Only Look Once: Unified, Real-Time Object Detection"
authors: "Joseph Redmon, Santosh Divvala, Ross Girshick, Ali Farhadi"
year: 2016
venue: "CVPR 2016"
doi: ""
arxiv: "1506.02640"
citation_count: "~45,000+ (estimated)"
popw_relevance: HIGH
tags:
  - object-detection
  - real-time
  - deep-learning
  - one-stage
  - yolo
---

# Paper 095 — YOLO: Real-Time Object Detection (CVPR 2016)

## 📋 Paper Summary

**YOLO (You Only Look Once)** reframes object detection as a single regression problem —直接从图像像素预测边界框坐标和类别概率。Unlike prior detection systems that repurposed classifiers, YOLO processes the entire image in one forward pass, achieving real-time speed while maintaining competitive accuracy. This single-stage approach directly inspired one-stage action recognition pipelines.

## 🎯 Problem Statement

Prior object detection systems (R-CNN, Fast R-CNN) used a two-stage approach:
1. **Region proposals**: Find ~2000 candidate bounding boxes
2. **Classification**: Classify each proposal

This was too slow for real-time applications.

## 💡 Core Contribution

**Single regression pipeline**:
```
Input Image → CNN (single forward pass) → [Grid Cells → Bounding Boxes + Class Probabilities]
```

Each grid cell predicts:
- B bounding boxes (x, y, w, h, confidence)
- C class probabilities

Final predictions via non-maximum suppression (NMS).

## 🔑 Key Architectural Insights

1. **Single forward pass** for entire image — no region proposals
2. **Grid-based prediction** — spatial decomposition of detection task
3. **Real-time performance** — 45 fps on Titan X, 155 fps on faster architectures
4. **Global context** — sees entire image during training (vs. limited context in two-stage)

## 📊 Results

| Method | mAP (VOC 2012) | FPS |
|--------|----------------|-----|
| DPM v5 | 33.7% | ~1 |
| R-CNN | 66.0% | ~0.05 |
| Fast R-CNN | 70.0% | ~3 |
| **YOLO** | **63.4%** | **45** |

YOLO trades 6.6% mAP for ~15x speed improvement.

## 🔗 YOLO Evolution (Relevant to POPW)

```
YOLO v1 (2016)     → Simple grid + FC layers
YOLO v2 (2017)     → Anchor boxes, batch norm, higher resolution
YOLO v3 (2018)     → Multi-scale, 3 scales per feature map
YOLO v4/v5/v7/v8   → Heavy engineering, not academic interest
```

**For POPW**: Single-stage architectures are directly relevant because IKEA ASM action recognition can be framed as detecting "assembly actions" in spatiotemporal volumes.

## 🏛️ Architectural Implications for POPW

POPW's action recognition head draws from YOLO's **single-stage philosophy**:

```
Video Frames → Shared Backbone → Spatio-Temporal Feature Maps
                                            ↓
                          ┌─────────────────────────────┐
                          ↓                             ↓
                     Action Head                  Detection Head
                 (action classification)      (optional: object localization)
```

However, POPW differs importantly:
- **YOLO has no temporal modeling** — POPW uses 3D convolutions/LSTM for temporal sequences
- **YOLO is purely feedforward** — POPW requires sequential reasoning for assembly steps
- **POPW has pose conditioning** via FiLM — YOLO has no equivalent

## 📈 Why HIGH Relevance for POPW

1. **IKEA ASM action recognition** can use single-stage detection framing
2. **Real-time requirement** — POPW aims for real-time assembly action recognition
3. **End-to-end training** principle applies: POPW trains pose + action jointly, not as separate stages
4. **Multi-scale detection** inspiration for handling varying action durations

## ⚠️ Limitations

- Lower mAP than two-stage methods
- Struggles with small objects
- Limited localization precision
- No explicit temporal modeling (v1)
- Grid cell constraints limit detection of multiple objects in same cell

## 🔗 Connection to Other Papers

| Paper | Connection |
|-------|------------|
| 096 (DETR) | Alternative end-to-end detection approach |
| 097 (Attention Is All You Need) | Transformer attention can be added to YOLO (YOLOv8+) |
| 001-050 (Earlier tiers) | Many video understanding papers use single-stage principles |

---

*Recorded: 2026-04-11 | Source: arXiv:1506.02640 + CVPR 2016*
