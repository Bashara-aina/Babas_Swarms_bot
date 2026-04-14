---
title: Planner 2026 04 13 Popw Architecture Improvement
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
summary: '- Existing LaTeX paper skeleton at `/home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex`
  (384 lines)'
wikilinks: []
confidence: medium
source: research
---
## Plan: Improve POPW Paper Skeleton Architecture Description
Date: 2026-04-13
Type: RESEARCH

## Context Gathered
- Existing LaTeX paper skeleton at `/home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex` (384 lines)
- mxGraphModel XML specification provides precise architectural details not fully captured in current skeleton:
  - ResNet-50 Backbone: C2–C5 feature map dimensions, BN frozen, ImageNet pretrained
  - FPN: lateral 1×1 conv, top-down upsampling, 3×3 smooth, P3–P7
  - Detection Head: cls subnet (4×Conv 3×3+ReLU → Conv(9×7)) and reg subnet (4×Conv 3×3+ReLU → Conv(9×4)), 3 aspect ratios × 3 scales, base 32–512px, 7 classes, Focal Loss + SmoothL1
  - Pose Head: ConvTranspose2d(k=4,s=2,p=1) → GroupNorm(32) + ReLU → heatmaps [B,17,120,160] → soft-argmax → keypoints [B,17,2], Wing Loss
  - Activity Head: GAP(C5_mod)[B,2048] + GAP(P4)[B,256] → concat[B,2304] → Residual MLP(2304→512→256→512, skip 2304→512, BN+ReLU+Dropout(0.3), out:512→33), CB-Focal Loss
  - PoseFiLM: confidence extraction, pose_flat[B,51], γ-net(51→512→2048, 1+tanh∈(0,2)), β-net(51→512→2048, linear), C5_mod = γ·C5 + β, GAP(C5_mod)
  - Kendall UW: full equation with exp(−s)·L + s terms, s_t = clamp(log σ², −4, 2), init s_det=0, s_pose=−1, s_act=0, act_ramp = min(1, epoch/5)
- Color legend: #1e6fa8=Detection, #1a7a4a=Pose/FPN, #c0392b=Losses, #b8860b=FiLM, #6a0dad=C5/semantic

## Risk Assessment
- LaTeX equations must be syntactically valid (easy to break)
- The skeleton already compiles (has .pdf) — must not break compilation
- Color legend is for diagram description in text, not actual TikZ — lower risk

## Approach
Decompose into 5 focused contracts to revise each section of the Method (Section 3):
1. Backbone+FPN section (lines 106-116) — add lateral conv, top-down, P3-P7 dims
2. Detection Head section (lines 136-143) — add cls/reg subnet specifics, anchor details
3. Pose Head section (lines 118-134) — add ConvTranspose2d params, GroupNorm, Wing Loss details
4. Activity Head section (lines 145-156) — add full Residual MLP architecture, CB-Focal details
5. PoseFiLM section (lines 158-179) — add γ-net/β-net layer dimensions

## Note: This is a RESEARCH/TEXT task, not a code test. No pytest needed.

---

## Contracts

### CONTRACT #1: Tighten Backbone+FPN section with precise layer specs

WHAT:
  Read popw_paper_skeleton.tex lines 106-116 and revise the Backbone and FPN section to add
  missing specifics: lateral 1×1 conv, top-down upsampling, 3×3 smooth conv, P6/P7 generation
  from C5 via stride-2 conv, and explicit FPN output dimensions for P3-P7.

FILES:
  READ:  /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex
  WRITE: /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex

DONE_WHEN:
  - LaTeX file contains the phrase "lateral 1×1 convolution" within Section 3.2
  - LaTeX file contains "top-down upsampling" within Section 3.2
  - LaTeX file contains "3×3 smooth" or "3×3 smoothing" within Section 3.2
  - LaTeX file explicitly lists P3, P4, P5, P6, P7 dimensions (e.g., P3: 256×60×80 through P7: 256×2×2)
  - P6/P7 generation from C5 via stride-2 conv is mentioned

PROOF_FORMAT:
  grep -n "lateral\|top-down\|3×3 smooth\|P3\|P4\|P5\|P6\|P7" /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex | head -20
  → output must show mentions of all above terms within lines 106-135

BLOCKER_IF:
  - Any change introduces syntax errors that prevent LaTeX compilation

DEPENDS_ON: none

---

### CONTRACT #2: Revise Detection Head section with cls/reg subnet layer details

WHAT:
  Read popw_paper_skeleton.tex lines 136-143 and replace the Detection Head text with
  RetinaNet-style description specifying: cls subnet (4×Conv 3×3+ReLU → Conv(9×7)) producing
  [B,N,7], reg subnet (4×Conv 3×3+ReLU → Conv(9×4)) producing [B,N,4], 3 aspect ratios × 3 scales,
  base anchor sizes 32-512px, 7 part classes, Focal Loss (α=0.25, γ=2) + SmoothL1.

FILES:
  READ:  /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex
  WRITE: /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex

DONE_WHEN:
  - LaTeX file mentions "cls subnet" and "reg subnet" explicitly
  - LaTeX file mentions "4 convolutional layers" or "4×Conv 3×3+ReLU" for each subnet
  - LaTeX file mentions the final 1×1 conv producing [B,N,7] for cls and [B,N,4] for reg
  - LaTeX file mentions "3 aspect ratios × 3 scales" or "3×3" in anchor context
  - LaTeX file mentions anchor base sizes "32–512" pixels
  - LaTeX file specifies Focal Loss (α=0.25, γ=2) and SmoothL1

PROOF_FORMAT:
  grep -n "cls subnet\|reg subnet\|4.*Conv\|aspect ratio\|anchor\|Focal Loss\|SmoothL1\|1×1" /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex | grep -E "13[6-9]|14[0-3]"
  → output must show all the above terms near lines 136-143

BLOCKER_IF:
  - Loss equation syntax becomes invalid LaTeX

DEPENDS_ON: none

---

### CONTRACT #3: Revise Pose Head section with ConvTranspose2d and GroupNorm specs

WHAT:
  Read popw_paper_skeleton.tex lines 118-134 and replace the Pose Head text with explicit
  ConvTranspose2d(k=4, s=2, p=1) → GroupNorm(32) + ReLU → heatmaps [B,17,120,160] → soft-argmax
  → keypoints [B,17,2]. Add Wing Loss equation with ω=0.05, ε=0.005. Add note about confidence
  extraction: heatmaps → max pool → sigmoid → nan_to_num(0.5), producing pose_flat [B,51].

FILES:
  READ:  /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex
  WRITE: /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex

DONE_WHEN:
  - LaTeX file mentions "ConvTranspose2d" or "transposed convolution" with k=4, s=2, p=1
  - LaTeX file mentions "GroupNorm(32)" explicitly
  - LaTeX file mentions heatmap output [B,17,120,160] or equivalent
  - LaTeX file mentions soft-argmax decoding to keypoints [B,17,2]
  - Wing Loss equation appears with ω=0.05 and ε=0.005
  - Confidence extraction pipeline (max→sigmoid→nan_to_num) is described
  - pose_flat [B,51] dimension is mentioned

PROOF_FORMAT:
  grep -n "ConvTranspose\|GroupNorm\|120.*160\|soft-argmax\|Wing Loss\|0.05\|confidence\|pose_flat\|51" /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex | head -15
  → output must show all the above terms

BLOCKER_IF:
  - New equation introduces LaTeX syntax errors

DEPENDS_ON: none

---

### CONTRACT #4: Revise Activity Head section with full Residual MLP architecture

WHAT:
  Read popw_paper_skeleton.tex lines 145-156 and replace the Activity Head text with explicit
  architecture: GAP(C5_mod) [B,2048] + GAP(P4) [B,256] → concat [B,2304] → Residual MLP
  (2304→512→256→512, skip 2304→512, BN+ReLU+Dropout(0.3), final linear 512→33).
  Add explicit CB-Focal Loss equation with β formula and γ=2.0.

FILES:
  READ:  /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex
  WRITE: /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex

DONE_WHEN:
  - LaTeX file explicitly lists GAP(C5_mod) [B,2048] and GAP(P4) [B,256]
  - LaTeX file mentions concat dimension [B,2304]
  - LaTeX file specifies full Residual MLP: 2304→512→256→512 with skip 2304→512
  - LaTeX file mentions BN+ReLU+Dropout(0.3) within the MLP
  - LaTeX file mentions final linear layer 512→33
  - CB-Focal Loss equation with β formula and γ=2.0 is present

PROOF_FORMAT:
  grep -n "GAP(C5_mod)\|GAP(P4)\|2304\|Residual MLP\|Dropout\|512→33\|CB-Focal\|β" /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex | head -15
  → output must show all the above terms

BLOCKER_IF:
  - LaTeX equation for CB-Focal becomes invalid

DEPENDS_ON: none

---

### CONTRACT #5: Revise PoseFiLM section with γ-net and β-net layer dimensions

WHAT:
  Read popw_paper_skeleton.tex lines 158-179 (PoseFiLM section) and add explicit layer
  dimensions for γ-net (51→512→2048, output 1+tanh∈(0,2)) and β-net (51→512→2048, linear/unbounded).
  Ensure the full PoseFiLM pipeline is described: confidence extraction, pose_flat [B,51]
  (keypoints [B,34] ‖ confidence [B,17]), γ·C5 + β modulation, GAP(C5_mod).

FILES:
  READ:  /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex
  WRITE: /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex

DONE_WHEN:
  - LaTeX file mentions γ-net with 51→512→2048 dimensions
  - LaTeX file mentions γ output constraint 1+tanh ∈ (0,2) or equivalent
  - LaTeX file mentions β-net with 51→512→2048 dimensions  
  - LaTeX file mentions pose_flat [B,51] = keypoints [B,34] ‖ confidence [B,17]
  - LaTeX file mentions C5_mod = γ·C5 + β or equivalent modulation formula
  - Gradient flow interruption (no gradient through pose path) is mentioned

PROOF_FORMAT:
  grep -n "γ-net\|beta-net\|51→512→2048\|1+tanh\|pose_flat\|C5_mod\|γ·C5\|no.grad" /home/newadmin/swarm-bot/project/popw/paper_skeleton/popw_paper_skeleton.tex | head -15
  → output must show all the above terms

BLOCKER_IF:
  - Greek letters (γ, β) cause LaTeX rendering issues

DEPENDS_ON: none

---

## Execution Order
Serial (must run in sequence): #1 → #2 → #3 → #4 → #5
Parallel (can run simultaneously): none
Final gate (must run last): verify LaTeX compiles with `cd /home/newadmin/swarm-bot/project/popw/paper_skeleton && latexmk -pdf popw_paper_skeleton.tex -interaction=batchmode 2>&1 | tail -5`

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LaTeX equation syntax errors | M | H | Use \frac{}{} and \exp{} correctly, verify with grep before compile |
| Greek letter rendering (γ, β) | L | L | Use proper LaTeX math mode $\gamma$, $\beta$ |
| Backward compatibility with existing placeholders | M | M | Only edit text within existing sections, don't touch $[POPW_DETECTION_MAP]$ placeholders |
