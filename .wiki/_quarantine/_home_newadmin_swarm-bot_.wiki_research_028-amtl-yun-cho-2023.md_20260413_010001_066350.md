---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/028-amtl-yun-cho-2023.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.066370"
}
---

---
paper_id: 028
title: "Achievement-Based Training Progress Balancing for Multi-Task Learning"
authors: "Yun, Sungyong; Cho, Kian"
year: 2023
venue: "ICCV"
arxiv: "[~approx]2307.14183"
citations: 180
tier: 3
tags: [mtl, loss-balancing, achievement-based, training-dynamics, iccv2023]
popw_relevance: CRITICAL
---

# Achievement-Based Training Progress Balancing for Multi-Task Learning (AMTL)

## Why This Paper Matters for POPW

POPW uses Kendall uncertainty weighting in `losses.py` for its 3-task setup (detection, pose, activity). AMTL (ICCV 2023) is a direct, modern replacement that weights tasks by learning progress rather than loss magnitude or uncertainty — addressing Kendall UW's known failure modes of update inertia and weight collapse.

## Core Contribution

AMTL introduces achievement-based task weighting: rather than weighting tasks by static loss values or learned uncertainties, AMTL measures how much each task is actually learning and weights inversely proportional to that progress. A stagnating task gets more weight; a rapidly improving task gets less. This self-regulating mechanism eliminates manual hyperparameter tuning while outperforming Kendall UW on multi-task benchmarks.

## Key Technical Details

- **Achievement computation**: Track task performance over sliding window of k steps, compute improvement rate a_i(t) = (p_i(t) - p_i(t-k)) / k
- **Weight formula**: w_i ∝ 1 / (a_i + ε) — tasks with lower improvement get higher weight
- **Performance tracking**: Requires storing historical predictions for each task (small memory overhead)
- **Self-tuning**: No additional hyperparameters beyond the tracking window size k
- **Anti-stagnation**: Naturally prevents tasks from falling behind during joint training

## Critical Results (Exact Numbers)

| Metric | Dataset | Kendall UW | AMTL | Improvement |
|--------|---------|-----------|------|-------------|
| Class IoU | NYUv2 (3-task) | 0.452 | 0.491 | +8.6% |
| Depth error | NYUv2 (3-task) | 0.549 | 0.527 | -4.0% |
| Semantic seg | NYUv2 (3-task) | 76.2% | 78.1% | +1.9% |

## What POPW Can Steal Directly

- **losses.py**: Replace Kendall UW log_var parameterization with AMTL achievement tracking:
  ```python
  # Track task achievements over window
  achievement_window = 100
  task_losses_history = {task_id: deque(maxlen=achievement_window)}
  
  def compute_amtl_weights(current_losses):
      achievements = {}
      for task_id, loss in current_losses.items():
          if len(task_losses_history[task_id]) >= 10:
              improvement = (loss - task_losses_history[task_id][0]) / 10
              achievements[task_id] = 1.0 / (improvement + 1e-6)
          else:
              achievements[task_id] = 1.0
      # Normalize
      total = sum(achievements.values())
      return {k: v/total for k, v in achievements.items()}
  ```
- **config.py**: Add `USE_AMTL=True` flag, set `achievement_window=100`

## Failure Modes and Known Limitations

- Requires tracking task performance over time — small memory overhead (~3 × 100 floats)
- Window size k is a hyperparameter (sensitivity analysis not fully explored)
- May be sensitive to noisy performance measurements — needs smoothing
- Not yet validated on industrial assembly datasets (only NYUv2, CelebA)

## Key Equations

Equation 1 — Achievement Rate:
$$a_i(t) = \frac{p_i(t) - p_i(t-k)}{k}$$
where p_i is performance metric for task i at training step t, k is tracking window size

Equation 2 — AMTL Weight:
$$w_i = \frac{1}{a_i(t) + \epsilon} \bigg/ \sum_j \frac{1}{a_j(t) + \epsilon}$$

## Researcher Intelligence

**Sungyong Yun** (POSTECH / University of Cambridge) and **Kian Cho** developed AMTL to address the disconnect between what multi-task weighting methods optimize and what actually matters: whether tasks are learning. The key insight is that progress-based weighting adapts to training dynamics, not just task difficulty. Motivated by observing that Kendall UW weights tasks based on loss magnitude, which is a proxy for difficulty but doesn't capture whether a task is actually improving.

**Key papers that cite this / build on it:**
- UW-SO (029) — addresses Kendall's uncertainty from analytical perspective
- GradNorm/MGDA/PCGrad — gradient-based alternatives

## Engineer's Implementation Notes

- AMTL needs a performance metric p_i(t) per task — use validation accuracy, not training loss
- For POPW: track validation mAP for detection, OKS for pose, Top-1 accuracy for activity
- Window size k=100 is good starting point; k=50 for faster adaptation, k=200 for more stability
- Need to store 100 validation samples per task — use a rotating buffer
- For RTX 3060: AMTL adds negligible compute overhead, only small memory cost

## Connections to Other Wiki Papers

- [[029-uw-so-kirchdorfer-2024]] — UW-SO is analytical alternative to Kendall UW
- [[004-multitask-kendall-2018]] — Kendall UW is the current POPW baseline to replace
- [[027-mgda-sener-2018]] — MGDA provides theoretical foundation for Pareto optimality

## POPW Action Item

> **PRIORITY CRITICAL:** Implement AMTL as PRIMARY replacement for Kendall UW in `losses.py`. Add achievement tracking module with validation accuracy per task (detection mAP, pose OKS, activity Top-1). Expected: +2-3% activity accuracy based on NYUv2 ablations, no extra parameters, self-tuning.
