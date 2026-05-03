---
title: Review 2026 04 22 Architecture Vit Vs Mamba3
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Review: Architecture Analysis: ViT vs. Mamba-3 for POPW Multi-Task Industrial Dataset
Date: 2026-04-22
Reviewer: @reviewer
Loop: #1 (first review)

### Independent Verification
```
find .wiki/ -name "*.md" | sort          # What files actually exist?
git diff --stat HEAD                    # What actually changed?
git status                             # Any uncommitted files?
```
- File: `/home/newadmin/swarm-bot/project/popw/working/code/industreal/ARCHITECTURE_ANALYSIS_ViT_vs_Mamba3.md` — EXISTS
- Git status: untracked file (new document, not yet committed)
- File size: 64KB, 1030 lines, 13 sections, ~7,800 words

---

### ✅ Passed
- [x] **Document structure**: 13 well-organized sections, clear taxonomy of ViT vs Mamba paths
- [x] **ASCII diagrams**: Arch diagrams in Sections 3d, 4d are clear and illustrate the data flow correctly
- [x] **Code snippets conceptually correct for Swin-T integration**: `SwinToFPNAdapter` in Section 3g correctly maps Swin-T's [96, 192, 384, 768] channels to FPN's 256ch inputs
- [x] **Decision matrix is evidence-based**: Weighted scoring across 7 criteria, recommendation (Swin-T near-term, Mamba temporal future) is balanced and justified
- [x] **Weaknesses are genuinely comparative**: Each weakness explicitly contrasts ViT vs Mamba vs ResNet (e.g., ViT's quadratic attention vs Mamba's linear; Mamba's gradient spikes vs ViT's smooth gradients)
- [x] **Phased implementation plan**: 3 phases with risk assessment is practical and actionable
- [x] **No hardcoded secrets or API keys**: Document is architecture analysis only

---

### ⚠️ Warnings (non-blocking)

1. **Kendall weighting description slightly simplified**: Section 10.1 says `log_var_act` ramps via "warmup ramp" but doesn't mention the actual mechanism (whether it's a linear ramp, step decay, or learned). Minor — the training code would clarify.

2. **"Mamba-3" naming**: The architecture is referred to as "Mamba-3" throughout, but the actual paper is "Mamba: Linear-Time Sequence Modeling with Selective State Spaces" (ICLR 2024 Outstanding Paper). Mamba-2 introduced SSD. "Mamba-3" is not the formal name. This is a naming clarity issue, not a factual error about the architecture.

3. **Section 4b table, row "Architecture"**: "SSD (state space duality)" under Mamba-3 column — this is Mamba-2's contribution. The relationship between Mamba-2 SSD and Mamba-3 is not clearly distinguished.

---

### ❌ Blockers (must fix before APPROVED)

#### FIX #1:
**File**: `ARCHITECTURE_ANALYSIS_ViT_vs_Mamba3.md`, Section 3f, Table row "Swin-T (patch 8)"
**Problem**: The GFLOPs claim of **~6.4 G** for Swin-T at 1280×720 is incorrect. 6.4G is the widely-cited FLOPs for Swin-T at **224×224** (from the original paper). At 1280×720:
- Swin-T patch size is 4 (not 8 as stated in table heading)
- Number of tokens scales from 3136 (56×56 at 224) to 57,600 (320×180 at 1280)
- With window attention O(N) scaling, Swin-T FLOPs at 1280×720 would be approximately **6.4 × 18.4 ≈ 118G**, not 6.4G

**Required change**: Correct the Swin-T GFLOPs entry. Either:
- State 6.4G is at 224×224 and estimate ~40–60G at 1280×720 (conservative given window attention efficiency), OR
- Remove the 1280×720 claim entirely and note that Swin-T's window attention scales O(N) but with significant constant factors

**Verify with**: `timm` library benchmark or Swin-T paper FLOPs table for 384×384 or 512×512 extrapolation

---

#### FIX #2:
**File**: `ARCHITECTURE_ANALYSIS_ViT_vs_Mamba3.md`, Section 3f, Table row "DeiT-S/16"
**Problem**: The **27 GFLOPs** estimate for DeiT-S/16 at 1280×720 is significantly too low.
- DeiT-S/16 at 224×224: 4.6G (confirmed)
- At 1280×720: N = 80×45 = 3,600 tokens vs 196 at 224×224
- Self-attention FLOPs scale as O(N²), so attention alone is (3600/196)² ≈ 338× more expensive
- Even ignoring the MLP/embed overhead: 4.6G × 338 ≈ 1555G just for attention
- 27G is physically impossible for DeiT-S at this resolution

**Required change**: Either:
- Remove DeiT-S from the 1280×720 GFLOPs table (not viable at this resolution without aggressive approximation), OR
- Add a note that DeiT-S at 1280×720 would be computationally prohibitive (~150G+ GFLOPs) and suggest Swin-T (patch 4) as the practical alternative

**Verify with**: Standard ViT FLOPs formula: O(N²·D) per layer × number of layers

---

#### FIX #3:
**File**: `ARCHITECTURE_ANALYSIS_ViT_vs_Mamba3.md`, Section 4a
**Problem**: The paper reference **"Mamba-3: Adaptive Computation with Selective State Space Models" (2024)** does not exist. The actual Mamba paper is:
- **"Mamba: Linear-Time Sequence Modeling with Selective State Spaces"** — ICLR 2024 Outstanding Paper
- **"Mamba-2: Structured State Space Duality"** — arXiv 2024

The name "Mamba-3" is used throughout the document (in section titles, text, and the table) as if it were a published architecture. This is a factual error.

**Required change**: 
- Replace all occurrences of "Mamba-3" with "Mamba (selective SSM)" or "Mamba-2/3 architecture"
- Update the reference in Section 13 to point to the correct paper titles and arXiv IDs
- Add the correct Mamba arXiv reference: `arXiv:2405.21060` for Mamba-2

**Verify with**: Check arXiv/state-spaces/mamba GitHub repository — the official model is called "Mamba" not "Mamba-3"

---

#### FIX #4:
**File**: `ARCHITECTURE_ANALYSIS_ViT_vs_Mamba3.md`, Section 4c, `TemporalMamba3` class (lines ~497–527) and Section 4g, `TemporalMamba3` implementation (lines ~658–693)
**Problem**: The **bidirectional processing via `.flip(0)` is NOT true bidirectional SSM**.

Mamba is a **causal (unidirectional) model** — it processes sequences left-to-right, where hidden state h_t depends only on x_0 through x_t. Flipping the input sequence and passing through the same forward SSM, then flipping the output, does NOT give you a backward SSM that sees future context. It simply reverses the order of processing through the same causal structure.

True bidirectional SSM (as in Vim/VMamba) requires two separate SSM passes:
- **Forward SSM**: h_fwd[t] depends on x[0..t] 
- **Backward SSM**: h_bwd[t] depends on x[t..T-1] (requires a separate backward-direction SSM scan)

The flip trick works for Transformers (which have bidirectional attention) but NOT for causal SSMs.

**Required change**: In the `TemporalMamba3.forward()` method, clarify that Mamba processes sequentially in each direction and the flip approach approximates backward processing only if the SSM itself is time-invertible (which it generally is not). Either:
- Add a separate `BackwardMamba` module that explicitly processes reversed sequences, OR
- Document this as an approximation and note that true bidirectional VMamba uses different architecture (cross-scan module)

**Verify with**: Liang et al., "Vim" (2024) — the Vision Mamba paper uses a Cross-Scan Module (CSM) that processes 2D spatial patches in both forward and backward directions as separate passes, not a simple flip trick.

---

#### FIX #5:
**File**: `ARCHITECTURE_ANALYSIS_ViT_vs_Mamba3.md`, Section 3f, Table row "Swin-S (patch 8)"
**Problem**: Swin-S uses **patch 4** (not patch 8). Swin-T uses patch 4 with window size 7. DeiT uses patch 16. The table says "patch 8" for Swin-T and Swin-S, which is incorrect — Swin variants use patch 4.

**Required change**: Fix the patch size column: Swin-T → patch 4, Swin-S → patch 4

**Verify with**: Swin Transformer paper (Liu et al., ICCV 2021) — "Swin Transformer uses a 4×4 patch size"

---

### Decision

❌ **CHANGES REQUIRED** — 5 blockers, see FIX directives above

**Summary of blockers:**
1. **Swin-T GFLOPs** (6.4G): Wrong resolution — should be ~40–60G at 1280×720
2. **DeiT-S GFLOPs** (27G): Physically impossible (~150G+ at 1280×720)
3. **Mamba-3 paper reference**: Non-existent paper name
4. **Bidirectional Mamba code**: Flip trick is not true bidirectional SSM
5. **Swin patch size**: Says patch 8, should be patch 4

### Loop Status
This is loop 1 of 3 maximum.

---

### Recommendations for @worker

The document has **strong structure and analysis** — the decision matrix, phased implementation plan, and comparative weakness sections are well-done. The GFLOPs errors and the Mamba naming issue are the most critical to fix before this document can be used for engineering decisions.

Priority fixes:
1. **FIX #3** (Mamba naming) is easiest — just search/replace and fix references
2. **FIX #4** (bidirectional code) requires a code design decision — clarify whether the flip is an approximation or needs a proper backward SSM
3. **FIX #1** (Swin-T GFLOPs) — verify with `timm` benchmarks at higher resolution
4. **FIX #2** (DeiT GFLOPs) — either remove from table or explain why it's not viable
5. **FIX #5** (patch size) — simple correction
