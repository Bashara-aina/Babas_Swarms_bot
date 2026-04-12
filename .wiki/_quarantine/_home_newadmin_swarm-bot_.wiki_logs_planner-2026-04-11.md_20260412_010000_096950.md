---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/planner-2026-04-11.md",
  "reason": "daily_fast_scan: score=0.150 < 0.3",
  "score": 0.15000000000000002,
  "quarantined_at": "2026-04-12T01:00:00.096978"
}
---

# POPW-PROTOCOL Research Wiki Construction Plan
> Created: 2026-04-11 | Planner: Bashara | Task: 100 Research Paper Wiki Pages

## Task Overview
- **Goal**: Write 100 research paper wiki pages for POPW (Multi-task Assembly Action Recognition)
- **Output**: `.wiki/research/popw/` directory with 100 markdown files + INDEX.md
- **Template**: YAML-frontmatter + markdown structure

## POPW Architecture Context
- ResNet-50 + FPN + 3 heads (detection, pose, activity)
- FiLM conditioning for multi-task learning
- Dataset: IKEA ASM (685K frames, 254 videos, 33 classes, 2545:1 imbalance)
- SOTA Target: >75% Top-1 activity accuracy

---

## Tier Assignments

### SUBTASK 1: Tier 1 (001-012) — Foundation Papers → @worker-1
**Papers**: ResNet, FPN, FiLM, Kendall MTL, IKEA ASM, Focal Loss, Mask R-CNN, etc.
**Files**: `popw/001-resnet.md` through `popw/012-mask-rcnn.md`

### SUBTASK 2: Tier 2 (013-022) — FiLM Variants → @worker-2
**Papers**: FiLM conditioning variants and extensions
**Files**: `popw/013-film-variant-1.md` through `popw/022-film-variant-10.md`

### SUBTASK 3: Tier 3 (023-035) — Multi-Task Learning → @worker-3
**Papers**: GradNorm, PCGrad, IMTL, AMTL, UW-SO, etc.
**Files**: `popw/023-gradnorm.md` through `popw/035-uwsn.md`

### SUBTASK 4: Tier 4 (036-048) — Assembly Domain → @worker-4
**Papers**: Assembly/Industrial Action Recognition
**Files**: `popw/036-assembly-action-1.md` through `popw/048-assembly-action-13.md`

### SUBTASK 5: Tier 5 (049-058) — Class Imbalance → @worker-5
**Papers**: Class Imbalance and Long-Tail Learning
**Files**: `popw/049-long-tail-1.md` through `popw/058-long-tail-10.md`

### SUBTASK 6: Tier 6 (059-067) — Semi-Supervised → @worker-6
**Papers**: Semi-Supervised Detection and Pseudo-GT
**Files**: `popw/059-semi-supervised-1.md` through `popw/067-pseudo-gt-9.md`

### SUBTASK 7: Tier 7 (068-078) — Video Temporal → @worker-7
**Papers**: Video Understanding and Temporal Modeling
**Files**: `popw/068-video-temp-1.md` through `popw/078-video-temp-11.md`

### SUBTASK 8: Tier 8 (079-085) — Pose Estimation → @worker-8
**Papers**: Pose Estimation
**Files**: `popw/079-pose-est-1.md` through `popw/085-pose-est-7.md`

### SUBTASK 9: Tier 9 (086-093) — Training Optimization → @worker-9
**Papers**: FP16, Gradient Checkpointing, AdamW, etc.
**Files**: `popw/086-fp16-training.md` through `popw/093-training-opt-8.md`

### SUBTASK 10: Tier 10 (094-100) + INDEX → @worker-10
**Papers**: Novelty Defense and Related Work
**Files**: `popw/094-novelty-1.md` through `popw/099-novelty-6.md` + `popw/INDEX.md`

---

## Worker Instructions (Per Paper)

For each paper, the worker must:
1. **web_search** to verify paper exists and gather details (title, authors, year, venue, arxiv, citations)
2. **Fetch additional details** from arxiv.org or semanticscholar
3. **Write the wiki file** following the exact template:
   ```yaml
   ---
   title: "[Paper Title]"
   authors: "[Authors]"
   year: [Year]
   venue: "[Venue/Journal]"
   arxiv: "[arXiv ID]"
   citations: [Count]
   tier: [Tier Number]
   domain: "[Domain]"
   relevance: "[Relevance to POPW]"
   key_contribution: "[One sentence]"
   methodology: "[Brief methodology]"
   results: "[Key results]"
   connection_to_popw: "[How it connects to POPW]"
   ---
   ```

---

## Dependency Constraints
- All 10 workers can run **in parallel**
- **No inter-worker dependencies** — each tier is independent
- Worker-10 should complete after workers 1-9 (for INDEX aggregation)
- All workers write to same `popw/` subdirectory — no conflicts expected

## Execution Order
```
[All Workers 1-9] ──┬── parallel execution ──→ 
[Worker-10 INDEX]  ─┘ after all complete ──→ Final INDEX.md
```

---

## Tracking
- Progress logged to: `.wiki/logs/planner-2026-04-11.md`
- Per-worker logs: `.wiki/logs/worker-[n]-2026-04-11.md`
