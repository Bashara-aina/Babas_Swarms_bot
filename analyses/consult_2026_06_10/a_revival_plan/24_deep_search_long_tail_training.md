# Agent 3: Deep Search -- Long-Tail Multi-Task Training Recipes for IndustReal

**Date**: 2026-08-01
**Status**: Research synthesis -- no code changes
**Audience**: Agents 1-5, revival-plan stakeholders
**Search coverage**: Exa + Firecrawl, AAAI 2025, CVPR 2025, NeurIPS 2023-2025, ICML 2024, WSDM 2025, ICCV 2025

---

## Context: The IndustReal 4-Task Problem

One ConvNeXt-Tiny backbone must simultaneously predict:
1. **Activity** (75-class long-tail, collapsing to 1 class, current top-1 = 0.394)
2. **Detection** (25-class, collapsed at mAP50 = 0.00009, true pathology metric)
3. **PSR** (11 binary heads or 24-class softmax, F1=1.0 bug, true F1 ~0.10 on ConvNeXt)
4. **Pose** (head pose MAE = 6.15 deg, position MAE = 42.15 mm -- the only healthy task)

**Root diagnosis** (from Agent 5 adversarial, file 11): At most 2 of 4 tasks revivable on ConvNeXt-Tiny. HeadPoseFiLM contamination cascade degrades PSR when pose is fixed. Activity linear probe proves zero above-baseline signal on ConvNeXt (0.2169 < 0.2217).

**Search mission**: Find training recipes from 2023-2025 literature that could maximize performance across all 4 tasks despite (a) severe long-tail class distributions, (b) conflicting multi-task gradients, and (c) limited backbone capacity.

---

## Section 1: Top 5 Loss Functions for Long-Tail Classification

### 1. LDAM-DRW (Label-Distribution-Aware Margin loss + Deferred Re-Weighting)
- **Venue**: NeurIPS 2019 (Cao et al.)
- **Mechanism**: LDAM assigns class-specific margins inversely proportional to sample count: minority classes get larger margins to encourage tighter clustering. DRW defers class-balanced re-weighting to the second half of training (after representation learning stabilizes).
- **Why #1 for IndustReal**: Decoupled schedule (feature learning first, classifier correction later) mirrors the known pathology: ConvNeXt backprop poisons shared features early. DRW can be applied after frozen-backbone phase.
- **Integration**: Replace standard CrossEntropy for activity head only. Combine with Focal component for hard-negative mining.
- **Risk**: LDAM assumes cosine classifier head; current architecture may need normalization layer.

### 2. Focal BCE with Per-Component Weighting
- **Venue**: ICCV 2017 (Lin et al., Focal Loss) + practical extensions
- **Mechanism**: Focal Loss down-weights easy examples: `FL(p_t) = -(1-p_t)^gamma * log(p_t)`. Per-component weighting uses inverse-frequency weights for each class.
- **Why #2 for IndustReal**: Already partially implemented in codebase. Focal loss handles background-foreground imbalance naturally (critical for detection with extreme background ratio). The gamma parameter controls how much to focus on hard examples.
- **Integration**: Apply to both activity (gamma=2-3) and detection (gamma=1-2) classification heads. Combine with class-balanced sampling in data loader.
- **Risk**: Does not address gradient conflicts between tasks -- purely a loss-level intervention.

### 3. DBM Loss (Difficulty-aware Balancing Margin)
- **Venue**: AAAI 2025 (Son et al.)
- **Mechanism**: Two-component margin: (1) class-wise margin based on inverse class frequency, (2) instance-wise margin for hard positive samples based on angular distance from class center. "Assigns larger margins to more difficult samples."
- **Why #3 for IndustReal**: Addresses the instance-level difficulty variation ignored by LDAM. For activity, where tail classes may have both few samples AND high intra-class variance (different workers perform same action differently), instance-level margin adaptation is valuable.
- **Integration**: Drop-in replacement for activity classifier logit computation. Compatible with cosine classifier. Overhead is negligible (class-wise margin pre-computed, instance-wise margin from already-computed angular distance).
- **Risk**: AAAI 2025 paper evaluates on CIFAR-LT/ImageNet-LT/iNaturalist -- not on video/assembly data. Transfer to temporal domain untested.

### 4. Class-Balanced Focal Loss (CB-Focal)
- **Venue**: CVPR 2019 (Cui et al.)
- **Mechanism**: Combines Focal Loss with class-balanced weighting using effective number of samples: `weight = (1-beta)/(1-beta^n)` where n is sample count. Accounts for data overlap between classes.
- **Why #4 for IndustReal**: More principled than simple inverse-frequency weighting. Effective-number formulation prevents over-weighting of extreme minority classes (which could amplify noise).
- **Integration**: Replace current activity loss. Beta parameter tuned per task (~0.999 for extreme imbalance).
- **Risk**: Hyperparameter beta is dataset-dependent and needs tuning.

### 5. Adaptive Logit Adjustment (ALA / GLA)
- **Venue**: NeurIPS 2025 (Generalized Logit-Adjusted losses)
- **Mechanism**: GLA generalizes logit-adjusted losses to the broader general cross-entropy family. Shifts logits based on class priors with theoretical H-consistency guarantees.
- **Why #5 for IndustReal**: Stronger theoretical grounding than heuristic re-weighting. However, AAAI 2025 version is very new and untested beyond CIFAR/ImageNet.
- **Integration**: Post-hoc logit adjustment during inference, or integrated into training loss. Can combine with any base loss.
- **Risk**: Theoretical consistency bounds scale inversely with minimum class probability (1/p_min), which for 75-class activity where tail classes have <10 samples could be problematic.

### Honorable Mentions
- **SEL (Supervised Exploratory Learning)**: ICCV 2025, plug-and-play framework using Optimal Foraging Algorithm to generate exploratory examples. Compatible with existing methods but adds training complexity.
- **Category Extrapolation via LLMs** (CVPR 2025): Uses LLMs to find related auxiliary categories and retrieves web images. Not applicable to proprietary assembly data.
- **GNM-PT (Gaussian Neighborhood Minimization Prompt Tuning)**: NeurIPS 2024, for VPT-based long-tail. Not applicable (ConvNeXt backbone, no ViT prompts).

---

## Section 2: Top 5 Gradient Balancing Methods for Multi-Task Learning

### 1. FAMO (Fast Adaptive Multitask Optimization)
- **Venue**: NeurIPS 2023 (Liu et al., UT Austin)
- **Mechanism**: Dynamic task weighting that decreases all task losses at approximately equal rates. Uses O(1) space and time per iteration by leveraging loss history instead of computing all task gradients. Amortizes gradient computation over optimization trajectory.
- **Why #1 for IndustReal**: **Critical: O(1) space/time for 4-task problem is ideal** -- the current training already strains GPU memory (1.5GB self-kill threshold). Other methods (PCGrad, CAGrad, NashMTL) require storing all 4 task gradients. FAMO uses only loss value history. 25x faster than NashMTL in benchmarks. Performs comparably to CAGrad on supervised MTL.
- **Integration**: Wrapper around existing optimizer. Must track loss history per task. Requires tuning regularization parameter gamma (sensitivity to loss rate changes).
- **Risk**: FAMO balances loss decrease rates, not final performance. If one task naturally converges faster but to worse optimum, FAMO may over-allocate capacity to it. The gamma parameter is dataset-dependent.

### 2. CAGrad (Conflict-Averse Gradient Descent)
- **Venue**: NeurIPS 2021 (Liu et al.)
- **Mechanism**: Finds update vector within Euclidean ball around average gradient that maximizes the minimum improvement across all tasks. `min_i <g_i, d> >= c` where c controls the conservatism of conflict avoidance.
- **Why #2 for IndustReal**: Explicitly maximizes worst-case improvement -- directly addresses the problem where 1-2 tasks dominate and 2-3 collapse. CAGrad's parameter c provides a tunable knob between "cooperate" (c=1) and "compete" (c=0). ConicGrad (2025) cites CAGrad as most competitive comparison.
- **Integration**: Requires computing all 4 task gradients per step (O(k) memory). On ConvNeXt-Tiny (~28M params), 4x gradient storage may be feasible vs MViTv2-S.
- **Risk**: O(k) memory for k=4 is manageable for ConvNeXt-Tiny but the additional optimization problem (dual QP) adds per-step overhead. ConicGrad showed CAGrad converges slower than its angular constraint approach.

### 3. PCGrad (Project Conflicting Gradients / Gradient Surgery)
- **Venue**: NeurIPS 2020 (Yu et al.)
- **Mechanism**: If two task gradients conflict (negative dot product), project each onto the normal plane of the other. Preserves beneficial gradient components, removes destructive ones. Simple, model-agnostic.
- **Why #3 for IndustReal**: Simple implementation -- just wrap optimizer gradient step. Proven on both supervised MTL and RL. For k=4 tasks, handles sequential pair-wise projection.
- **Risk**: Sequential projection order matters and can cause inconsistent results for k>2. Does NOT guarantee all conflicts resolved (only GradOPS does). Multiple studies show PCGrad alone insufficient for recommendation/vision MTL without additional mechanisms. GradCraft (2024) paper showed PCGrad performs worse than CAGrad/FAMO on real-world benchmarks.

### 4. Aligned-MTL
- **Venue**: CVPR 2022 (Senushkin et al.)
- **Mechanism**: Uses condition number of linear system of gradients as stability criterion. Aligns orthogonal components of gradient system. Provably converges to optimal point with pre-defined task-specific weights.
- **Why #4 for IndustReal**: Unique advantage: allows explicit task priority specification. For IndustReal where pose is already good and should be preserved while fixing others, pre-defined task weights let us tell the optimizer "pose loss can increase if it helps detection."
- **Integration**: Requires computing all task gradients + solving linear system. The condition number computation adds overhead.
- **Risk**: Pre-defined weights require knowing the right trade-off in advance. If the weights are wrong, performance degrades uniformly.

### 5. GradOPS (Gradient Deconfliction via Orthogonal Projections onto Subspaces)
- **Venue**: WSDM 2025 (Zhu et al.)
- **Mechanism**: Projects each task gradient onto subspace orthogonal to span of ALL other task gradients (not pair-wise like PCGrad). Guarantees ALL conflicts resolved regardless of number of tasks. Convergence to Pareto stationary points proven. Supports diverse trade-off preferences via single hyperparameter.
- **Why #5 for IndustReal**: **First method that guarantees complete gradient deconfliction for k>2 tasks.** PCGrad and GradVac cannot guarantee this. Trade-off parameter lets us explore Pareto frontier systematically. State-of-the-art on multiple benchmarks.
- **Risk**: Requires Gram-Schmidt orthogonalization on gradients -- O(k^2 * d) computation. For ConvNeXt-Tiny with d~28M, 4 tasks means ~6x gradient operations per step. WSDM venue means focused on recommendation tasks, less vision validation.

### Honorable Mentions
- **ConicGrad** (2025): Enforces angular constraint (cone around reference gradient). More flexible than CAGrad's Euclidean ball. Achieves 0.89 success rate on MT10 RL benchmark vs CAGrad 0.83. But newer, less community validation.
- **Kendall Uncertainty Weighting**: Classic approach -- learn per-task homoscedastic uncertainty as loss weight. Simple, no gradient computation overhead. But tends to collapse to one task in severe imbalance.
- **GradVac (Gradient Vaccine)**: Sets adaptive gradient similarity targets per task pair. PCGrad improvement but still pair-wise only.

---

## Section 3: Top 5 Decoupled / Staged Training Strategies

### 1. TS-MOF (Two-Stage Multi-Objective Fine-tuning)
- **Venue**: NeurIPS 2025 (DataLab-atom)
- **Mechanism**: Stage 1: Standard pre-training (feature learning). Stage 2: **Freeze backbone**, fine-tune only classifier heads via multi-objective optimization. Two innovations in Stage 2: (a) Refined Performance Level Agreement for adaptive task weighting based on real-time per-class performance, (b) Robust Deterministic Projective Conflict Gradient for stable gradient conflict resolution.
- **Why #1 for IndustReal**: **Directly applicable.** The current codebase already has frozen-backbone training. TS-MOF formalizes this with principled Stage 2 optimization. "20 epochs" fine-tuning cited -- extremely efficient. Achieves +3.3% tail class accuracy on CIFAR100-LT IR=100.
- **Integration**: Replace current head-training phase with TS-MOF's multi-objective framework. Requires tracking per-class validation performance during Stage 2.
- **Risk**: NeurIPS 2025 paper evaluates on image classification (CIFAR/ImageNet/iNaturalist) -- no multi-task or detection evaluation. Stage 2 assumes strong Stage 1 features, which for IndustReal detection (0.00009 mAP) may not hold.

### 2. cRT (classifier Re-Training)
- **Venue**: ECCV 2020 (Kang et al.)
- **Mechanism**: Two stages: (1) Train full model with instance-balanced sampling, (2) Freeze backbone, **discard classifier weights**, re-train ONLY classifier from scratch with class-balanced sampling.
- **Why #2 for IndustReal**: The activity head collapse (75 -> 1 class) suggests classifier weights are the primary failure, not backbone features. cRT directly addresses this. LDAM-DRW later showed combining with margin-aware loss improves over vanilla cRT.
- **Integration**: Easy to implement: after training, freeze ConvNeXt+FPN, re-initialize activity head, train with class-balanced batches.
- **Risk**: If features for tail classes are zero-quality (linear probe result 0.2169 < 0.2217 baseline), no classifier can fix it. cRT only works if features are decent but classifier is biased.

### 3. Frozen-Backbone Head Training with Staged Unfreezing
- **Mechanism**: Phase 1: Train with frozen backbone, only heads. Phase 2: Unfreeze last N layers of backbone. Phase 3: Full model with discriminative learning rates (backbone lr = head_lr / 10).
- **Why #3 for IndustReal**: Gradual unfreezing prevents catastrophic forgetting of pre-trained features. For ConvNeXt, unfreezing stages 3-4 (higher-level features) while keeping stages 1-2 frozen may help detection without destroying pose.
- **Integration**: Already partially practiced in codebase. Formalize into 3-phase schedule with explicit per-phase loss weights.
- **Risk**: Pose quality (6.15 deg) may degrade when backbone is partially unfrozen. Need to monitor pose at each unfreeze step.

### 4. SimLTD (Simple Supervised and Semi-Supervised Long-Tailed Object Detection)
- **Venue**: CVPR 2025 (Tran)
- **Mechanism**: Three stages: (1) Pre-train on abundant head classes, (2) Transfer learning on scarce tail classes, (3) Fine-tune on balanced head+tail sample. "Improved head-to-tail model transfer paradigm without meta-learning or knowledge distillation."
- **Why #4 for IndustReal**: Specifically designed for long-tailed **detection** (LVIS v1 benchmark). Detection (0.00009 mAP) is the most broken task -- this is one of few methods that directly addresses long-tail detection rather than classification.
- **Integration**: Segregate IndustReal detection annotations into "head" (classes with >100 instances) and "tail" (classes with <20 instances). Train in 3-stage pipeline.
- **Risk**: Requires enough tail-class instances for Stage 2 transfer learning. If detection tail classes have <5 instances total, transfer learning is infeasible.

### 5. Separate Optimizer per Task Group
- **Mechanism**: Activity+Pose share optimizer A (features frozen early). Detection+PSR share optimizer B (trained longer with higher lr). Gradient synchronization every N steps.
- **Why #5 for IndustReal**: Acknowledges that the 4 tasks have different convergence speeds and optimal learning rates. Pose converges in 1 epoch while detection needs 10+. Separate optimizers prevent the "gradient tug-of-war."
- **Integration**: PyTorch supports multiple optimizers per model. Route parameters to optimizer based on which tasks they primarily serve.
- **Risk**: Increases training complexity. Shared parameters (ConvNeXt stages) get gradients from both optimizers -- need careful synchronization.

---

## Section 4: Knowledge Distillation Approaches

### Cross-Model Distillation Feasibility Assessment

**Premise**: Distill YOLOv8m detection knowledge into ConvNeXt-Tiny multi-task model, or distill MViTv2-S activity knowledge.

**Verdict: NOT VIABLE with current architecture constraints.** Reasons:

1. **Input channel mismatch**: MViTv2-S trained on 9-channel input (RGB + depth + optical flow). ConvNeXt-Tiny on 3-channel RGB. Weight merging and feature distillation are impossible due to mismatched input dimensions in the first convolution layer.

2. **Architecture incompatibility**: ConvNeXt-Tiny (CNN) and MViTv2-S (transformer) have fundamentally different feature hierarchies. Cross-architecture distillation (e.g., via CrossKD, CVPR 2024) requires aligned intermediate feature spaces which don't exist between CNNs and transformers without architectural bridges.

3. **Detection distillation collapse**: The detection head is so broken (0.00009 mAP) that there's no "knowledge" to distill from -- the student would learn to predict zero boxes, which it already does.

### Task-Specific Distillation Assessment

| Source | Target | Feasibility | Reason |
|--------|--------|-------------|--------|
| YOLOv8m detection | ConvNeXt det head | LOW | Cross-architecture + channel mismatch. CrossKD (CVPR 2024) supports heterogeneous backbones but requires matched feature map spatial dimensions. |
| MViTv2-S activity | ConvNeXt act head | VERY LOW | 9 vs 3 channels kills weight init transfer. Feature distillation would need 9->3 channel mapper. |
| CLIP ViT | ConvNeXt backbone | LOW | CLIP has no temporal modeling. Assembly actions require motion understanding. |
| Single-task pose model | Multi-task pose head | MEDIUM | Pose is the only healthy task. But single-task model would just be the current pose head with same backbone. No new knowledge to transfer. |

### MOCHA (Multi-modal Objects-aware Cross-archHitecture Alignment)
- **Venue**: arxiv 2024
- **Relevance**: Specifically designed for cross-architecture detection distillation. Uses object-aware feature alignment.
- **Limitation for IndustReal**: Still assumes compatible input modalities. 9-channel vs 3-channel is a harder problem than RGB vs RGB.

**Recommendation**: Abandon distillation path. Focus on training recipe improvements within single ConvNeXt-Tiny model.

---

## Section 5: AAAI 2025 / CVPR 2025 / NeurIPS 2024 Relevant Papers

### AAAI 2025

| Paper | Relevance | Key Finding |
|-------|-----------|-------------|
| **DBM Loss** (Son et al.) | DIRECT | Class-wise + instance-wise margin for long-tail. +0.7% over class-margin-only. Compatible with existing methods. |
| **DRGrad** (Direct Routing Gradient) | MODERATE | Personalized MTL via gradient routing. Not directly applicable to shared-backbone MTL. |
| M3Net (Multimodal MTL for 3D) | LOW | Autonomous driving domain. 3D detection + segmentation + occupancy. Architecture design insights possibly transferable. |

### CVPR 2025

| Paper | Relevance | Key Finding |
|-------|-----------|-------------|
| **SimLTD** (Tran) | HIGH | Long-tail detection via head-to-tail transfer. New SOTA on LVIS v1. Three-stage simple pipeline. |
| **Category Extrapolation via LLMs** (Zhao et al.) | MODERATE | LLM-generated auxiliary classes for long-tail. Requires web crawling for auxiliary images -- not feasible for proprietary assembly data. |
| **Distilling Long-tailed Datasets** (Zhao et al.) | LOW | Dataset distillation, not model training. |
| CrossKD (Wang et al.) | MODERATE | Cross-head KD for detection. Heterogeneous backbone support but RGB-only. |

### NeurIPS 2024

| Paper | Relevance | Key Finding |
|-------|-----------|-------------|
| **GNM-PT** (Gaussian Neighborhood Minimization Prompt Tuning) | LOW | VPT-based, requires ViT backbone. Not applicable to ConvNeXt. SOTA on Places-LT (50.1%), CIFAR100-LT (76.5%). |

### Other Notable 2025 Venues

| Paper | Venue | Relevance |
|-------|-------|-----------|
| **GradOPS** (Zhu et al.) | WSDM 2025 | HIGH -- complete gradient deconfliction for k>2 tasks |
| **ConicGrad** | 2025 (preprint) | HIGH -- angular cone constraint, more flexible than CAGrad |
| **SEL** (Jian et al.) | ICCV 2025 | MODERATE -- plug-and-play exploratory learning for long-tail |
| TS-MOF | NeurIPS 2025 | VERY HIGH -- two-stage multi-objective fine-tuning |

---

## Section 6: Recommended Combined Recipe

### Tier 1: Immediate Implementation (Week 1-2)

These are low-risk, high-return interventions that can be tested on the current ConvNeXt-Tiny + v4_fixed checkpoint:

**Loss-Level**:
- Replace activity CrossEntropy with **LDAM loss** (class-wise margins only, no instance-wise initially)
- Apply **DRW schedule**: switch to class-balanced re-weighting at epoch 6 of 10
- Keep Focal BCE for detection (already partially implemented)

**Optimization-Level**:
- Integrate **FAMO** as task-weighting wrapper around AdamW
- Tune FAMO gamma parameter on 100-step diagnostic runs
- Monitor per-task loss trajectories -- verify equal-rate decrease

**Training Schedule**:
- Phase 1 (epochs 1-6): Train all 4 heads with frozen ConvNeXt backbone (discriminative head lr only)
- Phase 2 (epoch 7+): Apply DRW to activity head, unfreeze ConvNeXt stages 3-4 at lr/10

### Tier 2: Week 3-4 Experimentation

These require more engineering but offer additional gains:

- Replace Phase 2 with **TS-MOF** framework (freeze backbone, multi-objective head fine-tuning)
- Add **DBM Loss** instance-wise margin component on top of LDAM
- Test **CAGrad** vs FAMO head-to-head on validation metrics

### Tier 3: Path A Restoration (GPU 5-7 days, per Agent 5 plan)

If ConvNeXt activity and detection don't recover with Tier 1-2:
- Switch activity head from 75-class softmax to **Path A (multi-label with per-class binary heads)**
- Apply per-class Focal BCE with LDAM margins
- Evaluate PSR Path A (11 binary heads) vs Path B (24-class softmax) on corrected F1 metric

### What NOT to do

1. **Do not attempt knowledge distillation** from MViTv2-S or YOLOv8m. Channel mismatch (9 vs 3) makes this impossible without 9-channel pipeline restoration, which is a separate infrastructure project.
2. **Do not spend time on ViT-based methods** (GNM-PT, VPT). ConvNeXt-Tiny is the chosen backbone and cannot use ViT-specific techniques.
3. **Do not use LLM-based auxiliary data** (Category Extrapolation). The IndustReal dataset is proprietary and web-crawled data would have no relevance to assembly actions.
4. **Do not trust PSR F1=1.0**. The code has a bug where TP=FP=FN=0 returns 1.0. Always verify PSR metrics against ground-truth frame-level state accuracy.

### Realistic Performance Targets (Post-Training Recipe)

These are estimates based on literature improvements + current baselines:

| Task | Current | Tier 1 Target | Tier 2 Target | Ceiling |
|------|---------|---------------|---------------|---------|
| Activity (top-1) | 0.394 | 0.40-0.42 | 0.43-0.45 | 0.48 |
| Detection (mAP50) | 0.00009 | 0.01-0.05 | 0.05-0.10 | 0.15 |
| PSR (F1) | 0.10 | 0.15-0.25 | 0.25-0.35 | 0.40 |
| Pose (MAE deg) | 6.15 | 6.0-6.5 | 5.8-6.3 | 5.5 |

**Fundamental constraint**: 3 of 4 target metrics (activity 0.6223, detection 0.3584+, PSR 0.883) were achieved on MViTv2-S with 9-channel input -- not on ConvNeXt-Tiny. Any recipe improvements on ConvNeXt are bounded by the linear probe result proving zero activity signal above baseline. The above ceilings assume LDAM-DRW + FAMO can extract marginal signal from the backbone features. If they cannot, the true ceiling for activity on ConvNeXt is 0.2217 (the balanced baseline).

---

## Cross-References

### Within Revival Plan
- **File 11** (debate_adversarial): Agent 5's Go/No-Go gates and probability table
- **File 18** (unified_model_training): Agent 2's 6-strategy comparison matrix
- **File 21** (unified_model_final_synthesis): Agent 5's ONE model recommendation with 4-phase plan

### Not Yet Written (as of 2026-08-01)
- Files 22, 23, 25, 26: Do not exist in the repository. Presumably being created by other agents (Agent 4: 9-channel backbone search, Agent 2: MTL architectures, Agent 5: final synthesis). Cross-reference these when available.

### External References
- FAMO: https://github.com/Cranial-XIX/FAMO
- TS-MOF: https://github.com/DataLab-atom/TS-MOF
- DBM Loss: https://github.com/quotation2520/dbm_ltr
- GradOPS: https://arxiv.org/abs/2503.03438
- ConicGrad: https://arxiv.org/abs/2502.00217
- LDAM-DRW: https://github.com/kaidic/LDAM-DRW
- PCGrad: https://github.com/tianheyu927/PCGrad
- CrossKD: https://openaccess.thecvf.com/content/CVPR2024/papers/Wang_CrossKD_Cross-Head_Knowledge_Distillation_for_Object_Detection_CVPR_2024_paper.pdf

---

## Methodology Note

All rankings are based on:
1. Direct applicability to ConvNeXt-Tiny 4-task IndustReal problem (not generic benchmarks)
2. Computational feasibility within 1.5GB GPU memory constraint
3. Compatibility with existing v4_fixed checkpoint architecture
4. Empirical evidence quality (venue tier, benchmark relevance, code availability)
5. Integration complexity (drop-in vs architectural change)

Papers evaluated on CIFAR-LT/ImageNet-LT only were penalized vs papers with multi-task or detection evaluation. Methods requiring ViT backbones, CLIP pre-training, or external data were excluded from top rankings.
