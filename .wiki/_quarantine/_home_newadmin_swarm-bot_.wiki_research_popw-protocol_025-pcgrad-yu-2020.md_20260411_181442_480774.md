---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/popw-protocol/025-pcgrad-yu-2020.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-11T18:14:42.480805"
}
---

---
tags: [mtl, gradient-surgery, gradient-conflict, pcgrad, multi-task-learning]
sources: [popw-protocol, arxiv:2001.06782]
created: 2026-04-11
updated: 2026-04-11
popw-tier: 3
---

# Paper 025 — PCGrad: Gradient Surgery for Multi-Task Learning

## Metadata

| Field | Value |
|-------|-------|
| **Tier** | 3 — Multi-Task Learning Methods |
| **Citation** | Yu et al. (2020). *Gradient Surgery for Multi-Task Learning*. NeurIPS 2020, arXiv:2001.06782 |
| **Authors** | Tianhe Yu, Saurabh Kumar, Abhishek Gupta, Sergey Levine, Karol Hausman, Chelsea Finn |
| **Venue** | NeurIPS 2020 |
| **Code** | https://github.com/tianheyu927/PCGrad |

---

## Abstract

While deep learning and deep reinforcement learning (RL) systems have demonstrated impressive results in domains such as image classification, game playing, and robotic control, data efficiency remains a major challenge. Multi-task learning has emerged as a promising approach for sharing structure across multiple tasks to enable more efficient learning. However, the multi-task setting presents a number of optimization challenges, making it difficult to realize large efficiency gains compared to learning tasks independently. The reasons why multi-task learning is so challenging compared to single-task learning are not fully understood. In this work, we identify a set of three conditions of the multi-task optimization landscape that cause detrimental gradient interference, and develop a simple yet general approach for avoiding such interference between task gradients. We propose a form of gradient surgery that projects a task's gradient onto the normal plane of the gradient of any other task that has a conflicting gradient.

---

## Key Contributions

1. **Identifies three gradient interference conditions**:
   - **Conflicting gradients**: Gradients point in opposite directions
   - **Squared cosine similarity**: Measures gradient direction conflict
   - **Dominant tasks**: One task's gradient overwhelms others

2. **PCGrad algorithm**: Projects conflicting gradients onto the normal plane of other task gradients

3. **Theoretical analysis**: Proves PCGrad converges to a stationary point

4. **Versatile**: Works with both supervised learning and RL

---

## Method Details

### Gradient Conflict Detection
For tasks $i$ and $j$ with gradients $g_i$ and $g_j$:
- Cosine similarity: $cos(\theta) = \frac{g_i \cdot g_j}{\|g_i\| \|g_j\|}$
- Conflicting when $cos(\theta) < 0$ (opposite directions)

### PCGrad Operation
When gradient $g_i$ conflicts with $g_j$ (i.e., $g_i \cdot g_j < 0$):

$$g_i' = g_i - \frac{g_i \cdot g_j}{\|g_j\|^2} g_j$$

This removes the component of $g_i$ that's against $g_j$, projecting $g_i$ onto the normal plane of $g_j$.

### Algorithm
```
For each task i:
    g_i = gradient of L_i
    
For each other task j:
    if g_i conflicts with g_j:
        g_i = PCGrad(g_i, g_j)
        
Update with combined g_i
```

### Key Properties
- **Gradient direction repair**: Unlike GradNorm (magnitude only), PCGrad fixes direction conflicts
- **Task-agnostic**: No task-specific hyperparameters
- **Composable**: Can be combined with other loss balancing methods

---

## POPW Relevance

**Critical relevance** — PCGrad directly addresses a key limitation of Kendall UW:

**Kendall UW problem**: Assumes tasks are independent; doesn't handle gradient direction conflicts

**What PCGrad adds**:
- Detects and resolves gradient direction conflicts
- Works in conjunction with loss weighting methods
- More principled than heuristic loss scaling

**For POPW integration**:
1. PCGrad + AMTL (028) or UW-SO (029): Combine gradient surgery with modern loss weighting
2. Both operate on different aspects (direction vs magnitude)
3. Complementary improvements

**Implementation consideration**:
- Requires per-task gradient computation
- Can increase compute overhead
- May need to batch gradient operations for efficiency

---

## Limitations

1. **Compute overhead**: Requires computing gradients for each task separately
2. **Assumes pairwise conflicts**: Treats conflicts between pairs of tasks, not global conflicts
3. **No learning rate adaptation**: Doesn't adapt per-task learning rates
4. **Projection can amplify noise**: Removing gradient components may introduce noise

---

## References

- Yu et al. (2020). [arXiv:2001.06782](https://arxiv.org/abs/2001.06782)
- Related: [[024-gradnorm|Paper 024 — GradNorm]], [[027-mgda|Paper 027 — MGDA]], [[032-cagrad|Paper 032 — CAGrad]]

---

## POPW Protocol Context

**Used in**: POPW gradient conflict resolution strategies  
**Strength**: Handles gradient direction conflicts that Kendall UW misses  
**Complementary with**: AMTL (028), UW-SO (029) for loss weighting  
**Recommendation**: Essential reading for understanding why Kendall UW is insufficient
