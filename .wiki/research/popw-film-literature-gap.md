---
title: POPW Literature Gap — FiLM + Pose + Action Recognition
type: research
status: active
tags: [popw, film-modulation, pose-estimation, action-recognition, literature-review, multi-task-learning, computer-vision]
created: 2026-04-13
updated: 2026-04-13
summary: "Literature review finding: no published work simultaneously uses FiLM-style affine modulation (γ·x+β) with pose/skeleton as conditioning signal for action recognition before 2026. Existing works either use FiLM with language/style conditioning, or use pose with fusion/attention — never both together. POPW's PoseFiLMModule is novel: MLP(kp)→γ,β that modulates C5 features before activity classification."
wikilinks:
  - [[concepts/film-modulation]]
  - [[architecture/worker-net-improved4]]
  - [[projects/popw-research]]
  - [[projects/popw-multi-task-ikea]]
confidence: high
source: research
project: popw
---

# POPW Literature Gap — FiLM + Pose + Action Recognition

## TL;DR

Extensive literature search confirms: **no published work (up to early 2026) uses FiLM-style affine modulation with pose/skeleton as the conditioning signal for action recognition**. Existing FiLM work uses language/vision/style conditions. Existing pose-guided action recognition uses multi-stream fusion, attention, or masking — not feature-wise γ·x+β modulation. POPW's PoseFiLMModule is therefore novel.

---

## 1. Search Scope

Searched across:
- FiLM / conditional normalization literature (2017–2026)
- Skeleton-based action recognition papers (Awesome Skeleton-based Action Recognition list, 2014–2025)
- Pose-guided visual attention papers
- Conditional batch normalization in vision/video

**Constraint tested**: `pose → FiLM → CNN/ResNet features → action classification` — no positive matches found.

---

## 2. Existing FiLM / Conditional Normalization Work

### 2.1 FiLM Original Work

| Paper | Venue | Condition | Task |
|-------|-------|-----------|------|
| FiLM: Visual Reasoning with a General Conditioning Layer (Perez et al.) | arXiv 2017 | Language (VQA) | CNN + GRU → VQA |
| Feature-wise transformations (Dumoulin et al.) | Distill 2018 | Survey | CBN/CIN are FiLM special cases |
| GNN-FiLM (ICML 2020) | ICML 2020 | GNN node features | Graph reasoning |
| TFiLM (NeurIPS 2019) | NeurIPS 2019 | RNN over time | Sequential prediction |

**Key insight**: All FiLM work conditions on discrete labels, language embeddings, latent state, or style — never on raw pose/keypoint coordinates.

### 2.2 Conditional Normalization in Human Motion (Not Recognition)

| Paper | Venue | Condition | Task |
|-------|-------|-----------|------|
| ACT-VAE (IJCV 2023) | IJCV 2023 | **Action label** (discrete) | Video prediction / generation |

ACT-VAE introduces Action Conditional Batch Normalization (ACBN): `γ_A, τ_A = B(A)` where A is a **discrete action label** — not pose.

**Key insight**: Even in human motion synthesis, conditioning is on action labels, not continuous pose vectors.

---

## 3. Pose-Guided Action Recognition (No FiLM)

### 3.1 Representative Works

| Paper | Venue | Pose Usage | Mechanism |
|-------|-------|-----------|-----------|
| PoTion (CVPR 2018) | CVPR 2018 | Heatmap colorization | Pose heatmaps → CNN input |
| PO-GUISE (arXiv 2024) | arXiv 2024 | Keypoint-guided tokens | Token selection via attention |
| IPP-Net / EPP-Net | arXiv 2023–24 | Pose + parsing CNNs | Multi-stream feature ensemble |
| PFME+SR (IEICE 2025) | IEICE 2025 | Feature maps from pose CNN | Alignment + concatenation |

**All use**: multi-stream fusion, attention weighting, or feature concatenation — **not** feature-wise affine modulation.

### 3.2 Skeleton-Based HAR Modulation (Not FiLM)

| Paper | Venue | "Modulation" Type |
|-------|-------|-----------------|
| MMN (ACM MM 2025) | ACM MM 2025 | Motion-guided internal attention + gating on skeleton features |
| Feature Modulation in Self-Supervised Skeleton HAR (Sensors 2025) | Sensors 2025 | Internal modulation of skeleton representations themselves |

**Key insight**: When skeleton-HAR papers say "modulation", they mean gating/attention on skeleton features — not using pose to modulate RGB/CNN features via FiLM.

---

## 4. The Gap: What POPW Does That No One Else Does

```
Existing work:
  Pose → fusion/attention/masking → action classes        (many papers)
  FiLM → language/style/labels → CNN features              (many papers)

POPW (novel):
  Pose → MLP → (γ, β) → γ·C5_features + β → action classes
  ↑
  PoseFiLMModule: MLP(kp_dim=51) → (gamma_net, beta_net)
  modulates C5 [B, 2048, 20, 15] with pose-derived affine parameters
```

The closest matching work is **MMN (ACM MM 2025)** which uses "Motion-guided Feature Modulation" inside skeleton features — but:
1. It modulates skeleton features, not CNN/RGB features
2. The conditioning signal is motion (temporal difference), not pose coordinates

---

## 5. Novelty Argument for POPW

**Claim**: POPW's PoseFiLMModule is novel because it simultaneously satisfies:
1. **Task**: Action recognition (not VQA, video prediction, or synthesis)
2. **Conditioning signal**: Continuous pose/keypoint coordinates
3. **Mechanism**: Explicit FiLM-style affine modulation `γ(pose)·x + β(pose)` on CNN feature maps
4. **Application**: Real-world furniture assembly (not controlled lab datasets)

**Positioning**: Merge (a) multimodal HAR (pose + RGB) with (b) FiLM/conditional-norm ideas from VQA and style transfer.

**Required comparison baselines**:
1. PoTion (CVPR 2018) — pose heatmap aggregation
2. PO-GUISE (arXiv 2024) — pose-guided token attention
3. Pose-guided attention (CS231A 2016) — LSTM attention over regions
4. Multi-stream fusion (no modulation) — baseline without FiLM

---

## 6. Practical Implication

If POPW's PoseFiLMModule is novel, then:
- The conference novelty contribution is the **architecture** (pose-conditioned FiLM on CNN features), not just the task
- Ablation studies (FiLM vs no-FiLM, FiLM vs attention) directly support this claim
- The literature gap justifies not citing a specific "prior pose+FiLM" paper

**Recommended citation framing**:
> "To the best of our knowledge, no prior work has used FiLM-style feature modulation conditioned on continuous pose/keypoint coordinates for action recognition. We propose PoseFiLMModule, which ..."

---

## Related Articles

- [[concepts/film-modulation]] — FiLM as conditional normalization
- [[architecture/worker-net-improved4]] — POPW's implementation of PoseFiLMModule
- [[projects/popw-research]] — Full research context
