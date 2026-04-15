## Plan: POPW Better Alternatives Research

Date: 2026-04-15
Type: RESEARCH
Task: Find BETTER alternatives to Feature Bank and MAMBA-3 in POPW paper (pose-conditioned multi-task architecture for IKEA assembly)

## Context Gathered

### Existing POPW Architecture (from .wiki/):
- **Backbone**: ResNet-50-FPN → C5 (2048 channels)
- **Pose Conditioning**: PoseFiLMModule modulates C5 → C5_mod using 17-keypoint pose
- **Feature Bank**: Sliding-window deque storing C5_mod features for T=8 frames (poses the key innovation)
- **Temporal Head**: BiGRU (2.44M params, O(T·D·H)) or Mamba-3 (0.15M params, O(T·D·N))
- **Current Results**: improved4_film achieves 37.9% activity top-1, 0.600 detection mAP@0.5, 99.9% pose PCK@0.1

### Already Discussed in POPW Research (2019-2025 literature):
1. **BiGRU** (baseline): 2.44M params, O(T·D·H) complexity
2. **Mamba** (Gu & Dao 2023): 0.15M params, O(T·D·N), selective SSM
3. **Feature Bank**: LFB-style (CVPR 2019 Wu et al.), deque-based caching of C5_mod
4. **TSM** (ICCV 2019 Lin et al.): Zero-param temporal shift, 74.1% K400
5. **Video Swin Transformer** (CVPR 2022 Liu et al.): 86.7% K400, window attention
6. **SlowFast** (NeurIPS 2019): Dual pathway, 79% K400
7. **Non-Local** (CVPR 2018 Wang et al.): Self-attention blocks

### Research Gaps Identified in mamba-pose-activity-survey.md:
- No SSM + Pose-FiLM combination exists in literature
- Assembly-specific motions (screw, hammer) understudied
- Bidirectional pose↔activity communication not fully explored

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Academic papers have inconsistent metrics reporting | H | M | Focus on papers with complete params/GFLOPs/accuracy |
| Novel alternatives may not beat Mamba on POPW's small dataset | M | H | Prioritize approaches validated on small datasets (<300 videos) |
| Many SSM papers focus on skeleton input, not vision features | H | M | Focus on vision-feature-domain alternatives |
| GFLOPs often reported at different resolutions/batch sizes | H | L | Note resolution context, normalize where possible |

## Approach

1. **Contract 1-2**: Research feature bank alternatives (attention-based retrieval, memory networks, temporal pooling)
2. **Contract 3-4**: Research SSM alternatives (linear Transformers, recurrent mechanisms, hybrid approaches)
3. **Contract 5**: Synthesize comparison table with specific numbers from papers

## Key Questions to Answer
1. What temporal feature retrieval methods exist besides deque-based feature bank?
2. What linear-time sequence models exist besides Mamba (2023)?
3. Which alternatives have BETTER params/GFLOPs/accuracy tradeoffs for pose-aware activity recognition?
