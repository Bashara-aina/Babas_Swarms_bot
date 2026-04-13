# ADR-007: POPW Research Wiki Construction Pipeline

**Date**: 2026-04-11  
**Status**: ACCEPTED  
**Deciders**: Multi-agent pipeline (planner + 10 workers + reviewer)

---

## Context

POPW-PROTOCOL requires 100 research paper wiki pages for a multi-task assembly action recognition project. The papers span 10 tiers from foundational (ResNet, FPN) to domain-specific (IKEA ASM, Frame2Freq-ST) to training optimization (FP16, gradient checkpointing).

**Key POPW Architecture**:
- Backbone: ResNet-50 (ImageNet pretrained)
- Neck: FPN (P2-P5)
- Heads: Object Detection (7 classes) + Pose Estimation (17 COCO keypoints) + Activity Recognition (33 classes)
- Conditioning: FiLM (pose/object features modulate activity head)
- Dataset: IKEA ASM (685,516 frames, 2545:1 class imbalance)
- Hardware: RTX 3060 12GB VRAM

**Research Gap**: No published paper does pose→FiLM→CNN for assembly action recognition. POPW is likely novel.

---

## Decision

Execute full three-agent pipeline:
1. **Planner**: Decompose 100 papers into 10 tier-based subtasks
2. **Workers**: Execute sequentially per tier (10 workers total)
3. **Reviewer**: Verify quality, factual accuracy, template compliance

---

## Rationale

1. **Scale**: 100 papers is too large for single-agent execution
2. **Parallelism**: Tiers 1-9 are independent, can run in parallel
3. **Tier 10 dependency**: Must execute after all other tiers for complete INDEX
4. **Quality gates**: Reviewer enforces YAML template, anti-hallucination, POPW relevance

---

## Consequences

### Positive
- All 100 papers documented with standardized wiki format
- Cross-references between papers enable knowledge graph traversal
- POPW-specific action items directly guide implementation
- Gap analysis (Paper 100) confirms novelty for thesis defense

### Negative
- Some papers unverifiable (wrong arXiv IDs in task list)
- Worker 8 (Pose) skipped 3 papers: UDP (corrected to CVPR 2020), 083 (LivePose found), 084 (PoseConv3D NTU benchmark created)
- Rate limiting on web search caused partial verification for Tier 3

### Mitigations
- UDP paper ID corrected: task listed arXiv:2003.01583 (wrong), actual: 1911.07524 (CVPR 2020)
- All missing files (078, 079, 082-084) were created in continuation phase
- Files consolidated from scattered subdirectories to single `.wiki/research/` directory

---

## Key Decisions Made During Execution

1. **UDP arXiv ID correction**: 2003.01583 → 1911.07524 (CVPR 2020)
2. **VideoMAE V2**: arXiv 2303.16727, CVPR 2023
3. **LivePose**: arXiv 2304.00054, ICCV 2023
4. **PoseConv3D NTU benchmark**: Paper 084 is evaluation of PoseConv3D on NTU (not separate method)
5. **Paper 100 synthesis**: Literature gap analysis confirms POPW novelty

---

## Priority Papers Identified

| Priority | Papers | POPW Impact |
|----------|--------|-------------|
| CRITICAL | 001, 002, 003, 004, 038 | Core architecture + SOTA baseline |
| CRITICAL | 028, 029 | Loss function replacement |
| HIGH | 006, 007, 011, 036, 037 | Detection + pose + assembly |
| HIGH | 049-055 | Class imbalance handling |
| HIGH | 067, 082 | Pseudo-GT + pose encoding |

---

## References

- Pipeline execution logs: `.wiki/logs/worker-*-tier*-complete.md`
- Master INDEX: `.wiki/research/INDEX.md`
- Gap analysis: `.wiki/research/100-synthesis-open-frontier.md`
