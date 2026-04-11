---
paper_id: 067
title: "Segment Anything Model (SAM)"
authors: "Kirillov, Alexander; Mintun, Eric; Ravi, Nikhila; Mao, Hanzi; Rolland, Chloe; Gustafson, Laura; Xiao, Tete; Whitehead, Spencer; Berg, Alexander C; Lo, Wan-Yi; Dollár, Piotr; Girshick, Ross"
year: 2023
venue: "ICCV"
arxiv: "2304.02643"
citations: 8500
tier: 6
tags: [segmentation, foundation-model, zero-shot, promptable, sam, iccv2023]
popw_relevance: CRITICAL
---

# Segment Anything Model (SAM)

## Why This Paper Matters for POPW

POPW uses pseudo-GT from Mask R-CNN for unlabeled frames. SAM (ICCV 2023 Best Paper Honorable Mention) is the zero-shot furniture segmenter for pseudo-GT bootstrapping — it can generate high-quality masks for any furniture type without task-specific training. As noted in deepresearch.md, SAM produces higher quality masks than 12 overfitted Mask R-CNNs for IKEA ASM.

## Core Contribution

SAM is a foundation model for image segmentation trained on SA-1B (11M images, 1B masks) that can segment any object in any image given appropriate prompts (points, boxes, masks, text). The model demonstrates remarkable zero-shot generalization across diverse object types and contexts. SAM's three main components are: (1) Promptable segmentation task, (2) Vision Transformer-based architecture with prompt encoder, (3) SA-1B dataset for training robust generalization.

## Key Technical Details

- **Architecture**: ViT-based image encoder + prompt encoder + mask decoder with cross-attention
- **Three model sizes**: SAM-B (93M params, 12ms/img), SAM-L (308M params, 23ms/img), SAM-H (640M params, 87ms/img)
- **SA-1B Dataset**: 11M images, 1B masks generated via semi-automated data engine
- **Prompt types**: Points, boxes, masks, text (in later versions)
- **Decoder**: Cross-attention mechanism with iterative refinement and IoU prediction
- **Zero-shot**: Segment anything without task-specific training

## Critical Results (Exact Numbers)

| Task | Previous SOTA | SAM Zero-Shot |
|------|--------------|--------------|
| Instance Segmentation | 32.9 mAP | 46.6 mAP |
| Edge Detection | 0.75 mIoU | 0.72 mIoU |
| Text-to-Mask | — | 0.73 mIoU |
| SOM (Segment Anything Mobile) | — | 24.2 mIoU |

## What POPW Can Steal Directly

- **model.py**: Integrate SAM for pseudo-GT generation:
  ```python
  # SAM for pseudo-GT segmentation
  from segment_anything import sam_model_registry, SamPredictor
  
  sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b.pth")
  predictor = SamPredictor(sam)
  
  def generate_pseudo_gt(image, bbox):
      predictor.set_image(image)
      masks, scores, _ = predictor.predict(
          point_coords=None,
          point_labels=None,
          box=np.array(bbox),
          multimask_output=False
      )
      return masks[0]  # Return highest scoring mask
  ```
- **ikea_dataset.py**: Use SAM-generated masks as pseudo-GT for furniture part detection
- **config.py**: Set `USE_SAM_PSEUDO_GT=True` with SAM checkpoint path
- **Paper note**: SAM-B fits in RTX 3060 for inference, SAM-L/H require more VRAM

## Failure Modes and Known Limitations

- SAM-L (308M params, 23ms/img) is tight for RTX 3060 — SAM-B (93M, 12ms/img) is more practical
- For fine furniture parts (small objects), SAM may over-segment or miss boundaries
- SAM-HQ variant needed for high-quality mask refinement
- Text prompts not useful for POPW (no natural language for furniture parts)

## Key Equations

Equation 1 — Mask Decoder Cross-Attention:
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right)V$$
Where Q comes from prompt tokens, K,V come from image tokens

## Researcher Intelligence

**Alexander Kirillov** (Meta AI Research) led SAM development alongside **Ross Girshick** and **Piotr Dollár**. Motivation: Create a "GPT moment" for segmentation — a foundation model that can segment anything given prompts, trained on massive data. The SA-1B dataset (1B masks) is the largest segmentation dataset ever created, enabling zero-shot generalization. The paper won Best Paper Honorable Mention at ICCV 2023.

**Key papers that cite this / build on it:**
- SAM-HQ (high-quality variant) — improves mask quality for fine boundaries
- S4M (062) — SAM for semi-supervised instance segmentation
- MobileSAM — lightweight variant for edge deployment

## Engineer's Implementation Notes

- SAM-B checkpoint (~375MB) fits on RTX 3060 for inference
- Use `SamPredictor` for box-prompted segmentation (fastest for single-object)
- For IKEA ASM: prompt with furniture part bounding boxes from detection head
- SAM produces better masks than Mask R-CNN for furniture edges
- Run SAM at original image resolution (not resized) for best mask quality
- Batch processing: SAM-B can process ~80 frames/sec on RTX 3060

## Connections to Other Wiki Papers

- [[062-s4m-yoon-2025]] — S4M leverages SAM for semi-supervised instance segmentation
- [[066-pointrend-kirillov-2020]] — PointRend is architectural precursor to SAM decoder
- [[059-soft-teacher-xu-2021]] — Soft Teacher uses pseudo boxes for semi-supervised detection

## POPW Action Item

> **PRIORITY CRITICAL:** Integrate SAM-B for pseudo-GT generation in `model.py`. Use furniture part bounding boxes from detection head as SAM prompts to generate high-quality segmentation masks. Per deepresearch.md, SAM masks outperform 12 overfitted Mask R-CNNs. Expected: significant improvement in detection head quality with minimal labeling cost.
