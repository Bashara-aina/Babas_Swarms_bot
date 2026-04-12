---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/007-maskrcnn-he-2017.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.021536"
}
---

---
paper_id: "007"
title: "Mask R-CNN"
authors: "Kaiming He, Georgia Gkioxari, Piotr Dollár, Ross Girshick"
year: 2017
venue: "ICCV 2017"
arxiv: "1703.06870"
citations: 23351
tier: 1
tags: ["instance-segmentation", "object-detection", "mask", "roi-align", "panoptic"]
popw_relevance: 10
---

## Why This Paper Matters for POPW

Mask R-CNN extends Faster R-CNN with a **parallel mask prediction branch** — the standard for instance segmentation. For assembly understanding, POPW needs to segment individual parts and objects. Mask R-CNN provides the framework: detect bbox → predict mask per instance. The key innovation **RoIAlign** replaced RoIPool, fixing misalignment issues that hurt mask quality. POPW's segmentation head is a direct descendant.

## Core Contribution

Extended Faster R-CNN with a third branch for **instance mask prediction** in parallel with existing bbox detection branch. Key technical contribution: **RoIAlign** layer that eliminates harsh quantization of RoIPool by using bilinear interpolation. Achieved top results on COCO instance segmentation, detection, and keypoint detection tracks.

## Key Technical Details

**Mask R-CNN architecture:**
1. ResNet-FPN backbone (papers 001, 002)
2. RPN region proposal network
3. RoIAlign (not RoIPool) → shared feature extraction
4. Two parallel heads: bbox regression + classification AND mask prediction
5. Mask head: 4 conv layers + final deconv 2x → binary mask per class

**RoIAlign (key innovation):**
- Removes 2-step quantization in RoIPool (spatial alignment)
- Uses bilinear interpolation to compute feature values at continuous locations
- Divides ROI into k×k cells (default 7)
- Samples 4 points per cell using bilinear interpolation
- Aggregates with max/avg pooling

**Mask loss formulation:**
- Per-class sigmoid loss (not softmax)
- Loss only on positive (foreground) regions
- Each class predicts binary mask independently
- Final output picks class with highest classification score

## Critical Results

| Task | Mask R-CNN Result |
|------|-------------------|
| Instance Segmentation (COCO) | 37.1% AP |
| Object Detection (COCO) | 39.2% AP |
| Person Keypoint Detection | 63.1% AP |

Outperformed all existing single-model entries on all three COCO tracks.

## What POPW Can Steal Directly

- **File**: `models/detectors/maskrcnn.py` — POPW's instance segmentation model
- **RoIAlign**: Better spatial alignment for mask prediction
- **Parallel head architecture**: Mask + bbox + classification simultaneously
- **Mask loss formulation**: Per-class binary sigmoid
- **Multi-task training**: Combined classification + box + mask loss

## Failure Modes

1. **Instance vs semantic ambiguity** — masks can overlap, need NMS for instances
2. **Small objects** — masks at 28x28 resolution miss fine details
3. **Occlusion** — overlapping masks hard to separate
4. **Speed vs accuracy** — ResNeXt-101-FPN backbone is slow (5 fps)

## Key Equations

**Mask loss (per class):**
$$L_{mask} = -\frac{1}{K} \sum_{i,j} y_{ij} \log(\hat{y}_{ij}^k)$$

where $\hat{y}_{ij}^k$ is the predicted probability for class $k$ at pixel $(i,j)$, $y_{ij}$ is the ground truth.

**RoIAlign bilinear sampling:**
$$\text{feature}(x,y) = \sum_{i,j} \text{input}[i,j] \cdot \frac{1}{|x-i||y-j|}$$

(interpolated from 4 nearest input pixels)

## Researcher Intelligence

- **Kaiming He**: Meta AI (FAIR), ResNet (001). The collaboration with Ross and Piotr continued.
- **Georgia Gkioxari**: Meta AI, now at other positions. PhD from UC Berkeley.
- **Ross Girshick**: Meta AI (FAIR). Started R-CNN family at Berkeley.
- **Piotr Dollár**: Microsoft Research. Created COCO, FPN (002).

**Motivation**: Instance segmentation needed both detection and segmentation. Previous approaches (SDS, MNC) were complex multi-stage pipelines. Mask R-CNN shows a simple extension to Faster R-CNN with RoIAlign achieves SOTA.

## Key Papers That Cite This

1. **Cascade R-CNN** — Multi-stage refinement built on Mask R-CNN
2. **PANet** — Path aggregation network for better mask prediction
3. **TensorMask** — Dense sliding window instance segmentation
4. **PointRend** — Adaptive subdivision for finer masks
5. **YOLACT** — Real-time instance segmentation
6. **BlendMask** — Blending with attention for masks

## Engineer's Implementation Notes

**Secrets not in paper:**
- Mask head uses 4 conv layers (256-ch) + deconv (256→256→num_classes)
- Mask output is 28x28 for all ROIs (scaled up later)
- Use stride 1 in mask head (no downsampling in mask branch)
- RoIAlign uses 4 sampling points per bin (bilinear)
- Mask loss computed on positive ROI only, ground truth mask is resized to 28x28

**RoIAlign vs RoIPool:**
```
RoIPool:  floor(position/stride) — harsh quantization
RoIAlign: continuous sampling with bilinear interpolation
```

This 1-2 pixel difference matters for masks at 28x28 output.

**Implementation tips:**
- Mask head: conv(256) → conv(256) → conv(256) → deconv(256, 2x) → sigmoid
- Each class has its own binary mask — prediction picks mask for predicted class
- Training: minibatch 16 images, 512 ROIs per image, 0.5/0.5 pos/neg ratio

## Connections to Other Wiki Papers

- Built on **001 ResNet** backbone
- Uses **002 FPN** for multi-scale features
- Related to **006 Focal Loss** — RetinaNet and Mask R-CNN both evolved from FPN
- Same family as Faster R-CNN (not in POPW wiki but conceptually connected)
- Person keypoint detection in Mask R-CNN connects to **008 Simple Baselines** and **009 HRNet**

## POPW Action Item

- Verify POPW uses RoIAlign (not RoIPool) for segmentation quality
- Check mask head architecture matches 4-conv + deconv design
- Consider mask resolution — 28x28 may be insufficient for POPW parts
- Evaluate ResNet-50 vs ResNeXt-101 trade-off for POPW latency requirements
- For assembly segmentation, might need higher resolution mask output (56x56)