---
tags: [segmentation, foundation-model, zero-shot, promptable, sam, iccv2023, best-paper]
sources: [arxiv:2304.02643, openaccess:ICCV2023/Kirillov]
created: 2026-04-11
updated: 2026-04-11
paper_num: "067"
---

# Segment Anything Model (SAM)

**Kirillov*, Mintun*, Ravi*, et al. | ICCV 2023 (Best Paper Honorable Mention) | [arXiv:2304.02643](https://arxiv.org/abs/2304.02643)

## Overview

**SAM (Segment Anything Model)** is a foundation model for image segmentation that can segment any object in any image given appropriate prompts. Trained on the SA-1B dataset of 11M images and 1B masks, SAM demonstrates remarkable zero-shot generalization capabilities.

The three main components are:
1. **Task**: Promptable segmentation (generate segmentation from any prompt type)
2. **Model**: Vision Transformer-based architecture with prompt encoder
3. **Dataset**: SA-1B, the largest segmentation dataset ever created

## Architecture

### Promptable Segmentation Task

SAM accepts multiple prompt types:
- **Points**: Single point indicating object center
- **Boxes**: Bounding box for object location
- **Masks**: Partial mask as prior
- **Text**: Natural language description (in later versions)

The model outputs a valid segmentation mask for any prompt, enabling flexible use cases.

### Model Architecture

```
┌─────────────────────────────────────────────────┐
│              Image Encoder (ViT)                │
│    (ViT-B/L/H depending on model size)          │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│            Prompt Encoder                       │
│  (Points, Boxes, Masks → Token Embeddings)      │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              Mask Decoder                       │
│  (Cross-attention, upsample, IoU prediction)    │
└─────────────────────────────────────────────────┘
```

### Three Model Sizes

| Model | Parameters | Encoder | Speed (A100) |
|-------|------------|---------|--------------|
| SAM-B | 93M | ViT-B | 12ms/img |
| SAM-L | 308M | ViT-L | 23ms/img |
| SAM-H | 640M | ViT-H | 87ms/img |

## SA-1B Dataset

- **11M images** from diverse sources
- **1B masks** generated via data engine (semi-automated annotation)
- Diversity across domains, object types, and contexts
- Used for training robust zero-shot generalization

## Key Results

### Zero-Shot Transfer

| Task | Previous SOTA | SAM Zero-Shot |
|------|---------------|---------------|
| Edge Detection | 0.75 mIoU | 0.72 mIoU |
| Instance Segmentation | 32.9 mAP | 46.6 mAP |
| SOM | — | 24.2 mIoU |
| Text-to-Mask | — | 0.73 mIoU |

SAM achieves strong zero-shot performance across diverse segmentation tasks without any task-specific training.

### Interactive Segmentation

Given a single point prompt, SAM produces masks comparable to real-time interactive segmentation systems (e.g., RITM) with substantially better efficiency.

## POPW Relevance

> [!CRITICAL]
> **SAM is the most important paper for POPW pseudo-GT bootstrapping.** As stated in deepresearch.md, POPW uses pseudo-GT from Mask R-CNN for unlabeled frames. SAM is the zero-shot furniture segmenter for pseudo-GT bootstrapping — it can generate high-quality masks for any furniture type without task-specific training.

**POPW Implementation Insights from SAM:**
1. **Zero-shot segmentation**: SAM can segment unseen furniture categories
2. **Prompt-based refinement**: SAM outputs can be refined via box/point prompts
3. **Foundation model**: Pre-trained on massive data, no furniture-specific fine-tuning needed
4. **Quality comparison**: SAM produces higher quality masks than 12 overfitted Mask R-CNNs per deepresearch.md

## Code Availability

- Project Page: https://segment-anything.com
- GitHub: https://github.com/facebookresearch/segment-anything
- Demo: https://segment-anything.com/demo
- SA-1B Dataset: Available for research

## See Also

- [[066-pointrend]] — PointRend (same first author, architectural foundations)
- [[061-pointly-supervised]] — Pointly-Supervised IS (same author group)
- [[062-s4m]] — S⁴M leverages SAM for semi-supervised instance segmentation
