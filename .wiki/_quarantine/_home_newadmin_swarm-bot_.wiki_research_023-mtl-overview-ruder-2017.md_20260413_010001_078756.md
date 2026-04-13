---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/023-mtl-overview-ruder-2017.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.078778"
}
---

---
tags: [mtl, multi-task-learning, survey, deep-learning, ruder, bayes, uncertainty]
sources: [popw-protocol, arxiv:1706.05098]
created: 2026-04-11
updated: 2026-04-11
popw-tier: 3
---

# Paper 023 — An Overview of Multi-Task Learning in Deep Neural Networks

## Metadata

| Field | Value |
|-------|-------|
| **Tier** | 3 — Multi-Task Learning Methods |
| **Citation** | Ruder, S. (2017). *An Overview of Multi-Task Learning in Deep Neural Networks*. arXiv:1706.05098 |
| **Authors** | Sebastian Ruder (University of Oxford, DeepMind) |
| **Venue** | arXiv (submitted Jun 2017) |
| **Code** | https://ruder.io/mtl/ |

---

## Abstract

Multi-task learning (MTL) has led to successes in many applications of machine learning, from natural language processing and speech recognition to computer vision and drug discovery. This article aims to give a general overview of MTL, particularly in deep neural networks. It introduces the two most common methods for MTL in deep learning, gives an overview of the literature, and discusses recent advances. In particular, it seeks to help ML practitioners apply MTL by shedding light on how MTL works and providing guidelines for choosing appropriate auxiliary tasks.

---

## Key Contributions

1. **Comprehensive survey** of MTL methods in deep neural networks
2. **Taxonomy of MTL methods** into two categories:
   - **Hard parameter sharing**: Share hidden layers between tasks (most common)
   - **Soft parameter sharing**: Separate task-specific parameters with regularization
3. **Guidelines for auxiliary task selection**:
   - Related tasks with correlated features work best
   - Multi-task works well when tasks have complementary representations
   - Auxiliary tasks can help regularize main tasks
4. **Analysis of when MTL helps**:
   - Implicit regularization through shared representations
   - Attention focusing effects
   - Eavesdropping (one task learning information another needs)
   - Representation bias transfer

---

## Method Details

### Hard Parameter Sharing
```
Input → Shared Encoder → Task-Specific Heads
                          ↓           ↓
                      Task A      Task B
```
- Single shared hidden layers across all tasks
- Task-specific output layers
- Most widely used due to strong regularization effect
- Tends to overfit less than single-task learning

### Soft Parameter Sharing
- Each task has its own parameters
- Regularization encourages task parameters to be similar
- Examples: Cross-stitch networks, sluice networks
- More flexible but higher risk of overfitting

### MTL Mechanisms
1. **Inductive bias**: Shared representations provide inductive bias
2. **Attention focusing**: MTL helps model focus on important features
3. **Eavesdropping**: One task can "teach" another
4. **Representation learning**: Shared layers learn more general features

---

## POPW Relevance

**Direct relevance** — This survey is foundational reading for POPW's loss weighting research:

- **Kendall UW baseline**: Current POPW uses Kendall et al.'s uncertainty weighting (Paper 021). Ruder's survey explains *why* uncertainty-based weighting works: tasks with higher uncertainty should receive lower loss weights because they're inherently harder to learn.

- **Loss balancing gap**: The survey identifies that naive loss balancing (equal weighting) often fails because different tasks have different:
  - Loss scales
  - Learning rates
  - Gradient magnitudes

- **What to replace Kendall with**: Papers 028 (AMTL) and 029 (UW-SO) in this tier address this exact gap — moving from uncertainty-based weighting to achievement-based or analytically-grounded weighting.

**Key insight**: Hard parameter sharing with proper loss balancing outperforms soft sharing. POPW's approach aligns with this finding.

---

## Limitations

1. Survey focuses on 2017 state-of-art; many newer methods (PCGrad, CAGrad) not covered
2. Limited theoretical analysis — mostly empirical observations
3. Guidelines for auxiliary task selection are heuristic rather than principled
4. Does not address the problem of negative transfer in depth

---

## References

- Ruder, S. (2017). [arXiv:1706.05098](https://arxiv.org/abs/1706.05098)
- Related: [[021-kendall-uncertainty-mtl-2018|Kendall et al. (2018) — Uncertainty MTL]]

---

## POPW Protocol Context

**Used in**: POPW loss function design decisions  
**Replaces**: None (foundational baseline)  
**Next steps**: Read papers 028 (AMTL) and 029 (UW-SO) for modern alternatives to Kendall weighting
