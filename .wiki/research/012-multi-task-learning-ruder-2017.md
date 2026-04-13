---
title: "012 - Multi-Task Learning Ruder 2017"
type: research
status: active
tags: [multi-task, survey, transfer-learning, hard-parameter-sharing, soft-sharing]
created: 2026-04-13
updated: 2026-04-13
summary: "Ruder 2017 provides the definitive survey of multi-task learning (MTL) approaches, categorizing them as: hard parameter sharing (all tasks share encoder), soft parameter sharing (tasks have separate encoders with regularization), and auxiliary tasks (helper tasks enhance main task). POPW is a 3-task hard sharing model (detection + pose + activity via ResNet-50-FPN backbone)."
wikilinks:
  - [[001-resnet-he-2016]]
  - [[003-film-perez-2018]]
  - [[004-kendall-uncertainty-2018]]
  - [[025-cross-stitch-misra-2016]]
  - [[026-mtan-liu-2019]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# An Overview of Multi-Task Learning in Deep Neural Networks

**Author:** Sebastian Ruder
**Year:** 2017
**Venue:** JMLR (survey/tutorial)
**ArXiv/DOI:** [arXiv:1706.05098](https://arxiv.org/abs/1706.05098)
**Citation count:** ~8,000+
**Relevance to POPW:** POPW's architecture is a direct instantiation of hard parameter sharing — single ResNet-50-FPN encoder shared by 3 task heads. This survey explains WHY hard sharing works (features learned for one task are useful for others) and documents the trade-offs that led to Kendall/FiLM being aspirational in POPW.

## Core Contribution

This paper provides the taxonomy that every MTL paper references:
1. **Hard Parameter Sharing** (HPS): All tasks share the same encoder (lowest layers). Simple, effective, prevents overfitting via implicit regularization.
2. **Soft Parameter Sharing** (SPS): Each task has its own encoder, but parameters are regularized to be similar (Cross-stitch, MTAN).
3. **Auxiliary Tasks**: Additional tasks that help the main task without being the primary optimization target.

POPW uses **hard parameter sharing** with 3 task heads after a shared ResNet-50 + FPN backbone.

## Key Technical Details

- **Why MTL works** (from this survey):
  - **Implicit regularization**: Shared encoder can't overfit to any single task
  - **Feature learning redundancy**: Features useful for task A are likely useful for tasks B, C
  - **Attention to under-represented tasks**: Gradient from all tasks prevents single-task dominance
  - **Representational bias**: The model learns task-agnostic features that generalize better
- **When MTL helps most**: Tasks are related but have different noise levels; tasks have complementary structural information
- **When MTL hurts**: Tasks are conflicting (gradient directions oppose); one task dominates the loss

## MTL Taxonomy

```
Multi-Task Learning
├── Hard Parameter Sharing
│   └── All tasks share encoder (lowest N layers)
│       POPW: ResNet-50 + FPN shared, 3 heads separated
├── Soft Parameter Sharing
│   ├── Cross-Stitch (Misra 2016) [[025-cross-stitch-misra-2016]]
│   ├── MTAN (Liu 2019) [[026-mtan-liu-2019]]
│   ├── FiLM (Perez 2018) [[003-film-perez-2018]] (modulation-based)
│   └── LwF (Learning without Forgetting)
└── Auxiliary Tasks
    ├── Symmetric tasks (pose helps detection)
    ├── Adversarial tasks (gradient reversal for domain)
    └── Hint regression (intermediate supervision)
```

## POPW's MTL Architecture

```
Input Image
    ↓
ResNet-50 (ImageNet pretrained, all 3 tasks share)
    ↓
FPN Neck (256 channels, P3-P7, all 3 tasks share)
    ↓
┌───────┴───────┐
↓               ↓
Detection Head   Pose Head
(7 classes)      (17 COCO keypoints)
    ↓
    ↓
    Activity Head
    (33 classes, uses FPN C5 features)
```

This is **hard parameter sharing**: one ResNet-50, one FPN, three task-specific heads.

## What POPW Can Steal Directly

1. **Hard sharing is the simplest stable baseline**: POPW's shared ResNet-50-FPN architecture is intentionally conservative — it avoids the gradient conflict issues that plague soft-sharing approaches.
2. **Loss weighting is the main tuning knob**: With hard sharing, the only way to balance tasks is loss weighting (hence Kendall, GradNorm, etc. — see [[004-kendall-uncertainty-2018]], [[045-gradnorm-chen-2018]])
3. **Equal weighting works for POPW**: Since Kendall is disabled, POPW uses equal loss weights. The survey notes that equal weighting is surprisingly competitive with learned weighting methods.

## Implemented in POPW?

- [x] YES — POPW is hard parameter sharing (ResNet-50 + FPN shared, 3 task heads)
- [x] YES — `improved/model.py` implements the shared encoder architecture exactly as described

## Failure Modes / Limitations

- **Task interference**: When tasks require contradictory features (e.g., detection needs coarse features, pose needs fine-grained), hard sharing forces a compromise.
- **Gradient imbalance**: If detection loss is 10× larger than pose loss, detection gradients dominate — equal weighting partially addresses this by design.
- **Fixed architecture**: Hard sharing requires deciding at design time which layers are shared. POPW's ResNet-50 is frozen (ImageNet pretrained) and only FPN + heads are trained — this is a common refinement to pure hard sharing.

## Key Equations (Survey Framework)

**Hard parameter sharing:**
```
θ_shared = shared_encoder(image)
θ_det = detection_head(θ_shared)
θ_pose = pose_head(θ_shared)
θ_act = activity_head(θ_shared)
L_total = L_det(θ_det) + L_pose(θ_pose) + L_act(θ_act)
```

**Soft parameter sharing (cross-stitch):**
```
h_det = α_dd · h_shared + α_dp · h_pose
h_pose = α_pp · h_shared + α_pd · h_det
where α_ij are learnable cross-stitch coefficients
```

## Related Papers in This Wiki

- [[001-resnet-he-2016]] — ResNet-50 is POPW's shared encoder
- [[003-film-perez-2018]] — FiLM is POPW's aspirational soft-sharing (DISABLED)
- [[004-kendall-uncertainty-2018]] — Kendall is POPW's aspirational loss weighting (DISABLED)
- [[025-cross-stitch-misra-2016]] — Cross-stitch networks for soft parameter sharing
- [[026-mtan-liu-2019]] — MTAN (Masked Adaptive Transfer Network)
- [[100-popw-protocol-self-analysis]] — Documents POPW's hard sharing architecture

## LEGION RULE

When Bashara asks about "why not use soft sharing or learn loss weights instead of hard sharing," reference this paper's survey findings: Hard parameter sharing remains the most stable MTL approach — it generalizes better with limited data, trains faster, and doesn't have the gradient conflict issues of soft sharing. The survey found that even with learned loss weighting (Kendall's approach), equal weighting was competitive in most scenarios. POPW's hard sharing is not a limitation — it's the correct choice for 3 tasks on 685K frames.

Applied to POPW: The shared ResNet-50-FPN encoder learns task-agnostic visual features (edges, textures, parts) that benefit all 3 heads. The detection head benefits from pose features (parts have spatial relationships), and the activity head benefits from both detection (what parts are present) and pose (how the person is interacting with parts). This synergy is the key motivation for hard sharing.

The only tuning lever with hard sharing is loss weighting. POPW uses equal weights. If activity accuracy is lagging, increase `config.py:ACT_LOSS_WEIGHT` relative to other weights — this is safer than re-enabling Kendall.
