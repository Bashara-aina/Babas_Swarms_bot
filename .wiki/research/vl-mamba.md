---
title: Vl Mamba
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
summary: '- **arXiv**: [2403.13600](https://arxiv.org/abs/2403.13600)'
wikilinks: []
confidence: medium
source: research
---

# VL-Mamba: Multimodal LLM with SSM Fusion

## Paper Info
- **arXiv**: [2403.13600](https://arxiv.org/abs/2403.13600)
- **Authors**: Qiao et al.
- **Venue**: arXiv Mar 2024

## Core Contribution

VL-Mamba demonstrates that **Mamba can replace attention-based fusion** in vision-language models. The key innovation: processing vision tokens (from pretrained vision encoder) and language tokens through a **unified bidirectional SSM** — without cross-attention or attention-based fusion mechanisms.

This validates a future POPW where **pose features + activity features + RGB features** are fused through Mamba rather than concatenation + BiGRU.

## Architecture

```
Vision Encoder (CLIP ViT) → Vision Tokens [T_v, D]
Text Tokenizer → Text Tokens [T_l, D]
                                ↓
              Cross-Modal Projection (linear)
                                ↓
              Concatenated Tokens [T_v + T_l, D]
                                ↓
              Bidirectional Mamba Blocks (N layers)
                                ↓
              Language Decoder (next-token prediction)
```

**Cross-Modal Fusion via SSM**: Unlike LLaVA which uses cross-attention between vision and language, VL-Mamba fuses modalities through the SSM recurrence:
- Forward SSM: processes concatenated vision+text in reading order
- Backward SSM: processes in reverse order for anti-causal context
- The SSM's selective gate (Δ) learns which modality to attend to at each position

## Why VL-Mamba Matters for POPW

POPW currently has **three feature streams**:
1. RGB features (C5 from ResNet-50-FPN)
2. Pose features (keypoints from OpenPose)
3. Activity features (C5_mod after PoseFiLM modulation)

Fusion currently happens through:
- PoseFiLM: γ·C5 + β where γ,β come from pose features
- BiGRU: temporal aggregation of C5_mod across T=8 frames
- Late fusion: Activity head + Detection head + Pose head separate

VL-Mamba suggests **unified SSM fusion** for POPW v2:

```
Vision Tokens [T, C_vis] = ResNet-50-FPN features
Pose Tokens [T, C_pose] = OpenPose keypoints projected to D
Activity Tokens [T, C_act] = C5_mod features

Concatenate: [Vision ⊕ Pose ⊕ Activity] ∈ R^[3T, D]
  → Mamba Blocks (bidirectional SSM)
  → Unified multimodal context H_t ∈ R^D
  → Task-specific heads (pose, detection, activity)
```

**Key advantage**: Mamba's selective mechanism learns which modality matters at each timestep — pose features dominate during tool use, RGB features dominate during object recognition, activity features modulate both.

## VL-Mamba's Fusion Insight for POPW

VL-Mamba shows that SSM can learn **cross-modal attention implicitly** through the selective gate Δ:

```
At each frame t:
  Δ_t = σ(Linear(x_t))  # x_t = concat(vision_t, pose_t, activity_t)
  # Large Δ → modality switch (pose→RGB→activity)
  # Small Δ → steady state (same modality continues)
```

This is more flexible than POPW's current explicit PoseFiLM modulation:
- PoseFiLM: γ·C5 where γ comes ONLY from pose
- VL-Mamba SSM: Δ decides whether to attend to vision OR pose OR activity OR all

## Multimodal Fusion Architectures Compared

| Architecture | Fusion Method | POPW Relevance |
|-------------|--------------|---------------|
| LLaVA | Cross-attention (vision→text) | Detection→Activity via attention |
| Flamingo | Cross-attention (text→vision) | Activity→Pose gating |
| VL-Mamba | Unified SSM (no cross-attention) | Unified pose+RGB+activity SSM |
| POPW current | PoseFiLM + late fusion | Baseline |

## Future POPW v3: Unified Multimodal Mamba

```
Frame t:
  RGB → ResNet-50-FPN → C5_vis ∈ R^2048
  Pose → OpenPose → keypoints ∈ R^17×2
  Detection → Detection Head → object_features ∈ R^N×C

Project all to same dimension D:
  vis_t = Project(C5_vis) ∈ R^D
  pose_t = Project(keypoints→D) ∈ R^D
  det_t = Project(object_features) ∈ R^D

Fuse through Mamba:
  x_t = Concat(vis_t, pose_t, det_t) ∈ R^[3D]
  h_t = Mamba(x_t, h_{t-1})  # selective SSM recurrence

  # Δ_t learned to gate:
  # - Large Δ_t → pose-critical moment (hammer strike)
  # - Small Δ_t → steady assembly (holding parts)

  → Activity Head → 33-class
  → Pose Head → keypoint predictions
  → Detection Head → object bounding boxes
```

## Limitations

VL-Mamba's approach requires:
1. **Large-scale pretraining**: Needs diverse vision-language data
2. **LLM backbone**: Requires large decoder for language generation
3. **POPW data scale**: 254 IKEA videos insufficient for VL-Mamba pretraining

VL-Mamba is a **future POPW v3** aspiration — after collecting larger assembly dataset.

## References

- Qiao et al. (2024). "VL-Mamba: Exploring State Space Models for Multimodal Learning." arXiv:2403.13600
