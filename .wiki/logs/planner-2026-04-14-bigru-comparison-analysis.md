---
title: Planner 2026 04 14 Bigru Comparison Analysis
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '- Existing temporal-attention-alternatives.md covers 6 methods (Mamba, S4,
  MS-TCN++, MMN, ToTMNet, ATSS) with deep technical analysis'
wikilinks: []
confidence: medium
source: research
---
## Plan: POPW BiGRU Temporal Attention Comparison
Date: 2026-04-14
Type: RESEARCH

## Context Gathered
- Existing temporal-attention-alternatives.md covers 6 methods (Mamba, S4, MS-TCN++, MMN, ToTMNet, ATSS) with deep technical analysis
- popw-activity-head-temporal-alternatives-2026-04-14.md provides POPW-specific TSM vs BiGRU comparison and recommendation
- popw-model-comparison.md shows current baseline (improved4_film: 37.9% activity top-1, detection mAP@0.5=0.600, pose PCK@0.1=99.9%)
- popw-training-pipeline.md documents RTX 3060 12GB memory budget (batch 15, effective 60, FP16)
- projects/popw-research.md establishes FiLM architecture and PDD innovation context

## Risk Assessment
- Writing to new file (not editing existing) — low risk of breaking anything
- All analysis is synthesis from existing wiki content — no web fetch needed
- Must not hallucinate; all claims must trace to existing source material

## Approach
Decompose into 5 contracts covering each aspect of the comparison:
1. Architecture fit analysis (how each method integrates with POPW's multi-head)
2. Research novelty assessment (contribution to paper narrative)
3. RTX 3060 practical analysis (VRAM, compute, training stability)
4. Comparative summary table (unified reference)
5. Writing the final .wiki/research/bigru-comparison-analysis.md

## Output File
.wiki/research/bigru-comparison-analysis.md (NEW, does not exist)

---

## Contracts

---

### CONTRACT #1: Analyze architecture fit for each temporal method

WHAT:
  Analyze how each of the 6 temporal methods (Mamba, S4, MS-TCN++, MMN, ToTMNet, ATSS)
  integrates with POPW's existing multi-head architecture: ResNet-50 FPN backbone,
  PoseFiLM conditioning (C5_mod = γ·C5 + β), and the activity head's GAP(C5_mod)+GAP(P4)
  → Residual MLP → 33-class CB-Focal pipeline. Focus on integration points and
  data flow changes required.

FILES:
  READ:  .wiki/research/temporal-attention-alternatives.md (all 6 methods)
  READ:  .wiki/architecture/popw-training-pipeline.md (data flow)
  READ:  .wiki/projects/popw-research.md (FiLM architecture)
  WRITE: .wiki/logs/contract1-architecture-fit.md (intermediate)
  RUN:   echo "Architecture fit analysis complete" > /tmp/contract1_done

DONE_WHEN:
  - All 6 methods analyzed for POPW integration compatibility
  - PoseFiLM integration points identified per method
  - Activity head modification requirements catalogued
  - Data flow diagram impact documented per method

PROOF_FORMAT:
  cat .wiki/logs/contract1-architecture-fit.md
  → must contain architecture fit analysis for all 6 methods

BLOCKER_IF:
  - None (synthesis task, no external dependencies)

DEPENDS_ON: none

---

### CONTRACT #2: Assess research novelty for paper contribution

WHAT:
  Evaluate each method's contribution value to the POPW paper narrative.
  Assess: (a) how novel the method is in assembly recognition literature,
  (b) whether it strengthens or dilutes the FiLM+PDD story, (c) comparative
  saturation in the field. Identify which methods provide clearest
  "vs prior art" differentiation for the paper's contributions section.

FILES:
  READ:  .wiki/research/popw-film-literature-gap.md (FiLM novelty)
  READ:  .wiki/research/popw-model-comparison.md (current results baseline)
  READ:  .wiki/research/temporal-attention-alternatives.md (method novelty assessments)
  WRITE: .wiki/logs/contract2-novelty-assessment.md (intermediate)
  RUN:   echo "Novelty assessment complete" > /tmp/contract2_done

DONE_WHEN:
  - Novelty score (1-5) assigned to each method for paper contribution
  - FiLM+PDD story alignment rated per method
  - Assembly-specific applicability documented per method
  - Research gap each method fills identified

PROOF_FORMAT:
  cat .wiki/logs/contract2-novelty-assessment.md
  → must contain novelty scores and rationale for all 6 methods

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #3: Evaluate RTX 3060 practical constraints

WHAT:
  For each method, analyze RTX 3060 12GB VRAM feasibility: parameter count,
  GFLOPs, training memory overhead (gradients + activations + working memory),
  inference latency at 30fps target. Compare against current BiGRU baseline
  (~32 MB, ~4 GFLOPs). Identify which methods fit within budget and which
  require tradeoffs. Note training stability concerns (SSM initialization,
  warmup requirements, NaN risk).

FILES:
  READ:  .wiki/architecture/popw-training-pipeline.md (RTX budget details)
  READ:  .wiki/research/temporal-attention-alternatives.md (memory/compute per method)
  WRITE: .wiki/logs/contract3-rtx3060-analysis.md (intermediate)
  RUN:   echo "RTX 3060 analysis complete" > /tmp/contract3_done

DONE_WHEN:
  - VRAM requirement per method documented (T=16, 256 channels)
  - GFLOPs per frame vs 33ms budget analyzed
  - Training batch size impact quantified
  - Stability/risk notes per method

PROOF_FORMAT:
  cat .wiki/logs/contract3-rtx3060-analysis.md
  → must contain RTX 3060 feasibility for all 6 methods

BLOCKER_IF:
  - None

DEPENDS_ON: none

---

### CONTRACT #4: Create unified comparison table

WHAT:
  Synthesize contracts 1-3 into a single structured comparison covering:
  (1) Architecture Fit Score (1-5), (2) Research Novelty Score (1-5),
  (3) RTX 3060 Feasibility (✅/⚠️/❌), (4) Params/Memory, (5) GFLOPs,
  (6) POPW Integration Complexity (Low/Medium/High), (7) Paper Contribution Value,
  (8) Recommended Role in Architecture (pose head / activity head / backbone replacement).
  Sort by overall recommendation rank.

FILES:
  READ:  .wiki/logs/contract1-architecture-fit.md
  READ:  .wiki/logs/contract2-novelty-assessment.md
  READ:  .wiki/logs/contract3-rtx3060-analysis.md
  WRITE: .wiki/logs/contract4-unified-table.md (intermediate)
  RUN:   echo "Unified table complete" > /tmp/contract4_done

DONE_WHEN:
  - All 6 methods + BiGRU baseline in table
  - 8 comparison dimensions per method
  - Ranked ordering by overall recommendation
  - Clear ✅/⚠️/❌ feasibility verdict per method

PROOF_FORMAT:
  cat .wiki/logs/contract4-unified-table.md
  → must contain full comparison table for all methods

BLOCKER_IF:
  - None

DEPENDS_ON: 1, 2, 3

---

### CONTRACT #5: Write final analysis to .wiki/research/bigru-comparison-analysis.md

WHAT:
  Write comprehensive comparison document to .wiki/research/bigru-comparison-analysis.md
  synthesizing all contracts. Structure: Executive Summary → Method-by-Method Analysis
  (6 methods + BiGRU baseline) → Architecture Fit Analysis → Novelty Assessment →
  RTX 3060 Practical Analysis → Unified Comparison Table → Recommendation with rationale.
  All claims must trace to source documents.

FILES:
  READ:  .wiki/logs/contract1-architecture-fit.md
  READ:  .wiki/logs/contract2-novelty-assessment.md
  READ:  .wiki/logs/contract3-rtx3060-analysis.md
  READ:  .wiki/logs/contract4-unified-table.md
  WRITE: /home/newadmin/swarm-bot/.wiki/research/bigru-comparison-analysis.md (NEW FILE)
  RUN:   echo "done" > /tmp/contract5_done

DONE_WHEN:
  - File exists at .wiki/research/bigru-comparison-analysis.md
  - File contains frontmatter (title, type, tags, created, updated, summary)
  - All 6 methods + BiGRU baseline analyzed
  - Architecture fit, novelty, RTX 3060 analysis sections present
  - Unified comparison table present
  - Recommendation with rationale present
  - Word count > 1500

PROOF_FORMAT:
  wc -l .wiki/research/bigru-comparison-analysis.md && head -20 .wiki/research/bigru-comparison-analysis.md
  → must show file exists with frontmatter and content

BLOCKER_IF:
  - File write fails (disk space, permissions)
  - Any section fails to meet minimum content requirements

DEPENDS_ON: 1, 2, 3, 4

---

## Execution Order

Serial (must run in sequence): #1 → #2 → #3 → #4 → #5
Parallel (can run simultaneously): none
Final gate (must run last): verify file exists and contains all sections

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hallucination of technical details | L | H | All claims must trace to existing wiki sources |
| Incomplete method coverage | L | M | Use temporal-attention-alternatives.md as single source |
| File write fails | L | M | Verify write permissions before contract 5 |
| Missing POPW context | L | M | Use projects/popw-research.md for architecture context |