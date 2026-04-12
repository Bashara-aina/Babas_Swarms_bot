---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/003-film-perez-2018.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.864127"
}
---

---
paper_id: "003"
title: "FiLM: Visual Reasoning with a General Conditioning Layer"
authors: "Ethan Perez, Florian Strub, Harm de Vries, Vincent Dumoulin, Aaron Courville"
year: 2018
venue: "AAAI 2018"
arxiv: "1709.07871"
citations: 4001
tier: 1
tags: ["film", "conditioning", "visual-reasoning", "modulation", "reasoning"]
popw_relevance: 8
---

## Why This Paper Matters for POPW

FiLM provides the **conditional computation paradigm** that POPW uses to modulate feature maps based on task/state input. The $\beta$ and $\gamma$ affine transformation enables POPW to dynamically adjust what the network focuses on given assembly context. Halved the state-of-the-art error on CLEVR visual reasoning — showing conditioning can fundamentally change network behavior without architectural overhaul.

## Core Contribution

Introduced **Feature-wise Linear Modulation (FiLM)** — a simple, general-purpose conditioning method where a conditioning network generates $\gamma$ (scale) and $\beta$ (shift) parameters that apply affine transformations to CNN features: $FiLM(x) = \gamma \cdot x + \beta$. The network learns to generate these parameters based on conditioning information (e.g., question embeddings, task IDs, state vectors).

## Key Technical Details

**FiLM block:**
$$z = \gamma(c) \odot x + \beta(c)$$
- $x \in \mathbb{R}^{C \times H \times W}$: input feature map
- $c$: conditioning input
- $\gamma(c), \beta(c) \in \mathbb{R}^C$: generated per-channel scalars
- $\odot$: broadcasting multiply

**Conditioning network**: Produces $\gamma$ and $\beta$ from conditioning input. Can be any network (FC, RNN, attention, etc.) — the paper uses simple MLP for CLEVR questions.

**Where to apply FiLM**: After batch norm, before activation — or after activation if activation is gated.

## Critical Results

| Benchmark | FiLM Result | Previous Best |
|-----------|-------------|---------------|
| CLEVR Accuracy | 97.6% | ~50% (before FiLM halved it) |
| CLEVR-Humans | 95.6% | — |
| VQA-CP v2 | SOTA | — |
| Zero-shot generalization | Strong | — |

FiLM halved the error rate on CLEVR visual reasoning benchmark.

## What POPW Can Steal Directly

- **File**: `models/modules/film.py` — POPW's FiLM conditioning layer
- **Affine transformation pattern**: $\gamma \cdot x + \beta$ applied per-channel
- **Conditioning signal integration**: How POPW injects assembly state into visual features
- **Multi-layer FiLM stacking**: Multiple FiLM layers for deeper conditioning

## Failure Modes

1. **Gradient flow issues** — generating $\gamma, \beta$ from weak signals can cause gradient vanishing
2. **Over-conditioning** — too much conditioning can dominate features, losing original information
3. **Channel independence assumption** — doesn't model inter-channel relationships
4. **Requires sufficient conditioning information** — can't modulate without meaningful conditioning signal

## Key Equations

**FiLM transformation:**
$$y_{c,h,w} = \gamma_c \cdot x_{c,h,w} + \beta_c \quad \forall c \in [1, C]$$

**Conditioning network output:**
$$\gamma, \beta = f_\theta(c)$$
where $f_\theta$ is a neural network (often MLP or GRU).

## Researcher Intelligence

- **Ethan Perez**: Now at Google DeepMind (Constitutional AI, Anthropic work). PhD from Université de Montréal / MILA under Aaron Courville.
- **Aaron Courville**: Professor at Université de Montréal, core contributor to deep learning research in Canada
- **Vincent Dumoulin**: Research scientist, known for work on convolutional architectures
- **Florian Strub**: PhD student at the time, visual reasoning research

**Motivation**: Visual reasoning tasks (CLEVR) require multi-step, high-level reasoning. Standard CNNs without explicit reasoning modulation struggle. FiLM allows the network to "ask questions" of itself via conditioning — generating parameters that tell the network what to pay attention to.

## Key Papers That Cite This

1. **Self-conditioning** — FiLM concept extended to model self-conditioning
2. **Modular few-shot learning** — FiLM for task-conditioned few-shot
3. **Visual question answering** — VQA adapted FiLM conditioning
4. **NLP conditioning methods** — FiLM-style conditioning in language models
5. **GAN conditioning** — FiLM used in BigGAN and similar conditioning schemes

## Engineer's Implementation Notes

**Secrets not in paper:**
- FiLM works best when applied AFTER batch norm but BEFORE ReLU — batch norm provides normalized baseline for scaling/shifting
- $\gamma$ and $\beta$ initialization matters: start small (near 1 and 0) so FiLM doesn't dominate early training
- Can apply multiple FiLM layers at different depths — earlier layers affect low-level features, later layers affect semantic features
- Conditioning network should have same depth as feature extractor — shallow conditioning network can't drive deep modulation
- Use $\gamma$ initialization = 0.01, $\beta$ = 0 to start (nearly identity)

**Implementation gotchas:**
- FiLM is applied per-channel: $\gamma$ and $\beta$ have shape [C] not [B, C]
- Broadcasting happens automatically in PyTorch/TF when multiplying [C] with [B, C, H, W]
- Keep original paper's MLP architecture for conditioning network: 2-layer with ReLU

## Connections to Other Wiki Papers

- **001 ResNet**: FiLM layers can be inserted into ResNet blocks — after each BN
- **002 FPN**: FiLM conditioning can happen at each pyramid level
- **004 Multi-Task**: Both papers address multi-task learning with conditional parameters
- POPW likely uses FiLM for assembly-state-conditioned feature modulation

## POPW Action Item

- Build FiLM module with proper $\gamma, \beta$ generation
- Find where conditioning signal comes from in POPW (task ID? state vector?)
- Test FiLM insertion points: after each ResNet block vs after FPN
- Verify $\gamma, \beta$ initialization with small values
- Confirm conditioning network has sufficient capacity