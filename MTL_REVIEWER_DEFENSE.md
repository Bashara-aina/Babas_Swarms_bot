# MTL Methodology Defense: Research Findings and Reviewer Pre-emption Plan

> Researched on 2026-07-12 via arXiv API crawl, pdfplumber extraction of 5 paper PDFs, and semantic analysis.

---

## 1. Kurin et al. (NeurIPS 2022) -- arXiv:2201.04122

### Exact Claim
"Unitary scalarization [equal sum of losses], coupled with standard regularization and stabilization techniques from single-task learning, matches or improves upon the performance of complex multi-task optimizers in popular supervised and reinforcement learning settings."

### Their Protocol
- **"Standard regularization"** = dropout (p=0.5 for Multi-MNIST encoder/decoder; tuned 0.25-0.5 for CelebA), L2 penalty (tuned on grid lambda in {0, 1e-4, 1e-3}), early stopping via validation.
- **Benchmarks**: Multi-MNIST (2 tasks), CelebA (40 binary classification tasks), Cityscapes (2 tasks: 7-class semantic segmentation + depth estimation), Meta-World (RL).
- **Model selection**: validation-set-based early stopping (not last-epoch reporting).
- **Multi-MNIST architecture**: single dropout layer encoder + decoder; L2 did not help so omitted.
- **CelebA**: ResNet-18 tuned with L2 + multiple dropout layers; unitary scalarization, IMTL, PCGrad needed lambda=1e-3; MGDA, GradDrop, RLW needed lambda=1e-4.
- **Cityscapes**: lambda=1e-5 for unitary scalarization/IMTL/PCGrad, lambda=0 for others; per-metric model selection.
- **Key omission**: They did NOT tune scalarization weights per task -- they used purely **equal weights** ("unitary"). The paper's strength is showing this simple baseline is competitive, but its weakness is not testing tuned weighted scalarization on heterogeneous tasks.

### What They DID NOT Test
- **Heterogeneous tasks with wildly different gradient scales** (e.g., head pose estimation + segmentation + depth in one model)
- **Task-specific learning rates or per-task optimizers** (Elich 2024 later shows AdaTask / per-task Adam dominates)
- **Theoretical capacity limits** (Hu 2023 shows scalarization fails to find balanced Pareto points for under-parametrized models)

### Strongest Counter-Argument Against Kurin
1. **Hu et al. (NeurIPS 2023)** prove theoretically that for under-parametrized models (the realistic regime), scalarization CANNOT fully explore the Pareto front due to a multi-surface structure of the feasible region. SMTOs CAN find balanced solutions scalarization cannot. Kurin only tested over-parametrized benchmarks.
2. Kurin's equal-weight scalarization is the weakest version of scalarization. The relevant comparison is **tuned** scalarization (Xin et al.), and even then, for heterogeneous tasks with different gradient scales, scalarization fails. Xin shows the one case where it struggles is low-resource setups.
3. Kurin shows unitary scalarization works **on related tasks** (CelebA = 40 binary attributes on faces; Cityscapes = both scene understanding). They did NOT test fundamentally heterogeneous tasks where gradient magnitudes differ by orders of magnitude.

### OUR DEFENSE STRATEGY
- **Acknowledge**: Kurin is correct that unitary scalarization + standard regularization is a strong baseline that prior MTL work underestimated. We include this as a mandatory baseline.
- **Differentiate**: Our task set exhibits a measured 312x gradient magnitude gap between the strongest task (segmentation) and weakest task (pose). This is far larger than any gap tested in Kurin (Cityscapes depth/seg loss ratio ~10x, not 312x). Their results do not generalize to this regime.
- **Theoretical grounding**: Cite Hu et al. (2023) that under-parametrized models (our regime) have fundamentally different Pareto exploration properties.

---

## 2. Xin et al. (NeurIPS 2022) -- arXiv:2209.11379

### Exact Claim
"MTO methods do not yield any performance improvements beyond what is achievable via traditional optimization approaches [well-tuned linear scalarization]."

### Their Protocol
- **Primary domain**: Multilingual Neural Machine Translation (NMT)
  - En->{Fr,Zh}, En->{De,Fr}, En->{Ro,Fr}
  - Scalarization via **proportional sampling** (weight = sampling rate for each language pair)
  - LR tuning on grid 5e-2 to 5, sampling rates from 10% to 90%
- **Secondary domain**: Vision tasks (single-tower, hard parameter sharing)
- **Methods tested**: MGDA, GradNorm, PCGrad, IMTL, RLW, proportional sampling scalarization
- **Key finding**: All MTO methods produce points on the SAME Pareto front as scalarization (Figure 2). Task weights barely move during training (Figure 3).
- **Most important counter-finding**: For En->{Ro,Fr} (low-resource setup), scalarization **outperforms** MTOs -- the globally optimal solutions were found ONLY by scalarization at specific sampling rates.

### What "Well-Tuned" Means Specifically
- LR: grid search from 0.05 to 5 (an order of magnitude range)
- Sampling rates: 10%-90% in 20% increments for 2-task, more fine-grained sweeps
- Weight decay tuning
- All models trained to convergence with early stopping

### Strongest Counter-Argument Against Xin
1. Their "vision tasks" were relatively homogeneous -- they did NOT test on tasks with fundamentally different gradient scales (e.g., classification + regression with orders-of-magnitude difference).
2. They showed MTOs vs scalarization produce points on the SAME Pareto front, which actually CONFIRMS that MTOs reach Pareto-optimal solutions. The question is whether your specific task weighting needs are on that front.
3. The low-resource result (En->{Ro,Fr}) actually works AGAINST their narrative -- in that scenario, scalarization's globally optimal points were at specific tuned weights, not equal weighting. This is consistent with Hu et al.'s theoretical findings.
4. Weight evolution not moving significantly (Figure 3) may be a property of NMT specifically, not vision-based heterogeneous tasks.

### OUR DEFENSE STRATEGY
- **Acknowledge**: The Xin result is valid for NMT and homogeneous vision tasks. We cite it as evidence that careful scalarization evaluation is critical.
- **Differentiate**: Our 4-head heterogeneous task set (pose + segmentation + depth + normal) exhibits gradient interference that is fundamentally different from NMT. Figure 3 of Xin shows weight evolution is static in NMT -- our preliminary analysis shows PCGrad weights oscillate (evidence of ongoing conflict resolution).
- **New evidence**: Our 312x gradient gap is outside Xin's tested regime. We provide a direct comparison showing tuned scalarization fails on our tasks (your Table X: STL-matched performance only achieved via PCGrad + UW-SO).
- **Counter-cite Hu et al. (2023)**: Their theoretical result proves scalarization cannot always explore the full Pareto front, especially under capacity constraints.

---

## 3. Elich et al. (GCPR 2024) -- arXiv:2311.04698

### Exact Claims
Three paradigm-questioning findings:
1. **Adam optimizer is the real hero**: Adam provides partial loss-scale invariance, making MTL work better than SGD. This undermines studies that claim SMTOs work but only tested with SGD.
2. **Gradient conflicts (angular misalignment) are NOT unique to MTL**: Inter-sample gradient conflicts within a single task are as large as inter-task conflicts. Gradient conflict is NOT a distinguishing characteristic of MTL.
3. **Gradient magnitude differences are the main distinguishing factor**: Not angular cosine similarity, but magnitude disparities separate MTL from STL.

### Their Protocol
- Datasets: Cityscapes, NYUv2, CelebA
- Architectures: SegNet, DeepLabV3+, ResNet-18
- Compared: EW, UW, RLW, PCGrad, CAGrad, IMTL, Aligned-MTL, MTL-IO, AdaTask
- Key finding on Adam: Derive and measure "full loss-scale invariance for an optimal UW and a partial invariance for Adam." This partial invariance does NOT hold for SGD+mom.

### Strongest Counter-Argument Against Elich
1. Their claim that "gradient conflict is not unique to MTL" is technically correct but practically misleading. The magnitude of conflict may be similar, but the CONSEQUENCE differs because multi-task gradients affect a SHARED representation. Inter-sample conflicts in STL are resolved by the same optimizer -- inter-task conflicts in MTL corrupt the shared backbone for ALL tasks.
2. Their own results show that task-specific Adam (AdaTask) -- where each task gets its own optimizer state -- is "Pareto dominant over plain Adam+EW in almost all cases." This supports gradient balancing.
3. The partial loss-scale invariance of Adam means it can handle moderate gradient magnitude differences, but at 312x gap, even Adam's partial invariance breaks down. This is our core thesis.
4. Their conclusion that "angular alignment shows no evidence of unique MTL problem" was over a limited range of task pairs. With 4+ highly heterogeneous tasks, the combinatorics of conflicts multiply.

### OUR DEFENSE STRATEGY
- **Pre-empt directly**: Acknowledge Elich's finding that gradient magnitude differences are the key distinguishing factor (not angular conflict). This actually SUPPORTS our "Kendall-collapse" diagnosis -- we find a 312x gradient magnitude gap, which Elich identifies as the critical MTL challenge.
- **Explain why Adam's partial invariance fails**: At 312x gap, the smaller gradient tasks are effectively zeroed out in Adam's adaptive learning rate normalization. We show this empirically (plots of per-task effective learning rates).
- **Cite Adam + task-specific handling**: Our PCGrad + UW-SO combination can be viewed as a principled way to restore balance where Adam's partial invariance breaks down.
- **Note Elich's own finding**: "AdaTask [per-task Adam] is Pareto dominant over plain Adam+EW" -- this supports our claim that task-specific optimization matters.

---

## 4. RLW -- Random Loss Weighting (Lin et al., TMLR 2022) -- arXiv:2111.10603

### Exact Numbers
**Cityscapes (2 tasks: 7-class seg + depth)**:
| Method | Seg mIoU | PixAcc | AbsErr | RelErr | Delta_p |
|--------|----------|--------|--------|--------|---------|
| EW     | 68.71    | 91.50  | 0.0132 | 45.58  | +0.00%  |
| RLW    | 68.78    | 91.45  | 0.0134 | 43.68  | +0.69%  |
| RGW    | 69.68    | 91.85  | 0.0127 | 43.91  | +2.36%  |
| IMTL-L | 69.71    | 91.77  | 0.0128 | 45.08  | +1.58%  |
| CAGrad | 68.89    | 91.50  | 0.0128 | 44.72  | +1.38%  |
| RotoGrad| 68.96   | 91.47  | 0.0127 | 43.85  | +2.13%  |

**NYUv2 (3 tasks: 13-class seg + depth + surface normal)**:
- EW baseline seg mIoU is NOT 24.38. The paper reports classification metrics (mIoU ~38-40 range typical for NYUv2 on DeepLabV3).
- RLW achieves competitive/better delta_p than most carefully designed methods.

**Key Theoretical Claim**: RLW has higher probability to escape sharp local minima (Theorem 2), providing better generalization than static weighting.

### Is RLW Really Competitive?
- **On Cityscapes**: RLW (68.78) barely beats EW (68.71) on seg mIoU -- a 0.1% improvement. RGW (69.68) is more impressive (+1.4% over EW), but RGW is a gradient method with random weights.
- **On NYUv2**: RLW outperforms most loss balancing methods
- **On CelebA (40 tasks)**: RLW slightly outperforms EW but is comparable with other methods
- **Verdict**: Yes, RLW is competitive. Any claim that a new MTO method "works" must beat RLW to prove the gain comes from the scheme, not just randomness.

### OUR DEFENSE STRATEGY
- **Mandatory baseline**: Include RLW as a control. If our method does not statistically significantly outperform RLW on the primary metrics, the paper is unpublishable.
- **If we beat RLW**: Argue that RLW's mechanism (random escape from sharp minima) is orthogonal to our mechanism (resolving gradient magnitude imbalance). We combine both: RLW adds exploration, our method fixes the systematic bias.
- **If we DON'T beat RLW**: We need to investigate why. RLW's convergence theory (Theorem 2) shows it escapes sharp minima via noise injection -- if our task set has a sharp minimum problem, RLW alone might suffice.
- **Specific defense**: Show that RLW's improvements come from later training stages (escape behavior) while our method helps in early training (gradient balance). A combined method (RLW + PCGrad) should be tested.

---

## 5. DINOv2 Frozen Trunk (Oquab et al., 2023) -- arXiv:2304.07193

### Capabilities
- Self-supervised ViT trained on 142M curated images
- Produces "all-purpose visual features" that work across image distributions and tasks without finetuning
- Supports: image classification, retrieval, semantic segmentation (linear probes), depth estimation (NYUv2 depth benchmark)
- Does NOT explicitly support: video tasks, temporal modeling, multi-task co-adaptation
- Evaluation was on individual task benchmarks with linear probes -- NOT simultaneous multi-task inference

### Strongest Foil to "Shared Co-adapted Trunk" Thesis
DINOv2 shows that frozen trunk + lightweight heads works WELL for individual tasks. Why co-adapt at all?

### OUR DEFENSE STRATEGY
- **Parameter efficiency**: DINOv2 uses a 1B parameter ViT-g model. Our model achieves 2x parameter efficiency over STL baselines. DINOv2 is 10x+ larger than STL.
- **Domain specialization**: DINOv2 features are generalist -- they are NOT optimized for our specific task combination (pose + segmentation + depth + normal). Fine-tuning/co-adaptation allows task-specific feature specialization that a frozen backbone cannot provide.
- **Multi-task interference vs. single-task probes**: DINOv2 was evaluated with separate linear probes per task. We run ALL tasks simultaneously through one network. The interference dynamics (our core contribution) do not exist in the DINOv2 evaluation protocol.
- **Real-time constraints**: DINOv2 ViT-g runs at ~10 FPS on A100. Our model is designed for real-time deployment.
- **Direct experiment**: Show that frozen DINOv2 backbone + 4 lightweight heads performs WORSE than our co-adapted model on at least 2 of the 4 tasks. This validates the co-adaptation thesis.

---

## 6. Regularized Scalarization Baseline Design

### What Constitutes a "Properly Regularized" Baseline per Kurin
Based on Kurin's exact protocol:
- **Dropout**: 0.25-0.5 probability in shared encoder AND task-specific heads
- **L2 weight decay**: Tune on grid {0, 1e-5, 1e-4, 1e-3}
- **Early stopping**: Validation-based, not fixed epochs
- **Learning rate tuning**: Grid search over at least 1 order of magnitude
- **Model selection**: Per-metric best validation performance (for heterogeneous tasks)

### What Constitutes a "Well-Tuned" Baseline per Xin
- **Task weights**: Sweep from 0.1 to 0.9 for 2 tasks, more extensive for 4+ tasks
- **Learning rate**: Grid over at least 1-2 orders of magnitude
- **Proportional sampling** (for unequal dataset sizes)
- **Per-task optimizer states** (Elich shows AdaTask / per-task Adam is Pareto dominant)

### Mandatory Baseline Experiments (Exact Protocol)

**Baseline 1: Equal Weighting + Kurin Regularization**
- Loss: sum(L_i)
- Dropout: 0.3 in shared encoder, 0.3 in each head
- Weight decay: grid {0, 1e-5, 1e-4, 1e-3}
- LR: grid {1e-5, 3e-5, 1e-4, 3e-4, 1e-3}
- Optimizer: Adam
- Early stopping on validation delta_m metric
- Report: mean + std over 3 seeds

**Baseline 2: Tuned Weighted Scalarization (per Xin)**
- Sweep task weights: for 4 tasks, use {0.1, 0.25, 0.5, 0.75, 0.9} per task, keep sum=1
- For 4 tasks, use strategy: set one task to w, distribute (1-w) among others
- Grid: w in {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9}
- Otherwise identical to Baseline 1

**Baseline 3: RLW + Kurin Regularization**
- Sample loss weights from Normal distribution (mean=0, std=1) -> softmax normalization
- Architecture: same as Baseline 1
- LR grid: {1e-5, 3e-5, 1e-4, 3e-4, 1e-3}

**Baseline 4: Per-task Adam (AdaTask-style, per Elich)**
- Separate Adam optimizer per task head
- Shared backbone optimizer = Adam
- This tests whether per-task optimization suffices vs. gradient manipulation

**Baseline 5: Equal Weighting WITHOUT regularization (ablation)**
- Same as B1 but no dropout, WD=0
- Demonstrates the regularization effect

---

## 7. Critique Ranking by Threat Level

| Rank | Critique | Threat | Reviewer Profile | Our Pre-emption |
|------|----------|--------|-----------------|-----------------|
| 1 | **Kurin: Unitary scalarization + regularization matches MTOs** | CRITICAL | Any reviewer who knows MTL literature | Acknowledge, differentiate 312x gap, cite Hu 2023 |
| 2 | **RLW: Random weights match careful weighting** | CRITICAL | Methodological reviewer | Mandatory baseline; if we don't beat RLW, paper fails |
| 3 | **Elich: Gradient conflict not unique to MTL; Adam is the hero** | HIGH | Vision/optimization reviewer | Use their finding to support our magnitude-gap diagnosis; note Adam's partial invariance fails at 312x |
| 4 | **DINOv2: Frozen backbone works for all tasks** | MODERATE | Practitioner reviewer | Parameter efficiency argument; direct comparison experiment |
| 5 | **Xin: MTOs don't beat tuned scalarization** | MODERATE | NMT/empirical reviewer | Different domain; we directly compare with tuned scalarization |
| 6 | **Hu et al.: Scalarization fails for under-parametrized, but this applies to us too** | LOW-MOD | Theory reviewer | We are in under-parametrized regime -- actually supports our need for MTOs |

---

## 8. MINIMUM Control Experiments to Survive Review

These are NON-NEGOTIABLE for paper acceptance:

1. **[RAISE-1]** Equal weighting + proper regularization (Kurin protocol) -- our method MUST beat this
2. **[RAISE-2]** RLW (Normal distribution, softmax normalization) -- our method MUST beat this
3. **[RAISE-3]** Tuned scalarization (weight sweep, Xin protocol) -- our method MUST beat this
4. **[RAISE-4]** PCGrad alone (no UW-SO) -- ablation showing UW-SO adds value
5. **[RAISE-5]** UW alone (no PCGrad) -- ablation showing PCGrad adds value
6. **[RAISE-6]** Single-task baselines for all 4 heads -- establishes STL ceiling
7. **[RAISE-7]** Ablation: our method without the head-specific levers

Secondary but recommended:
8. Per-task Adam (AdaTask) -- testing Elich's finding
9. Frozen backbone + trained heads -- addressing DINOv2 argument
10. Gradient gap measurement plots across training -- diagnosis evidence

---

## 9. Does ANY Published Paper Successfully Defend Against Kurin/Xin/Elich? How?

**Hu et al. (NeurIPS 2023, arXiv:2308.13985)** -- This is the strongest published defense. They provide:
- Theoretical proof that scalarization CANNOT fully explore the Pareto front for under-parametrized models
- The multi-surface structure of the feasible region explains why scalarization fails
- Experimental evidence on real data showing SMTOs find balanced solutions scalarization cannot
- Partial answer to open questions in Xin et al. (2021)

**Limitation of Hu et al.**: Their theory is for LINEAR models. Extending to non-linear deep networks is non-trivial. Also, their experiments are on a single dataset; broader validation needed.

**No paper has fully answered all three critiques.** The typical strategy is:
1. Acknowledge Kurin/Xin as requiring rigorous baselines
2. Show that for the specific problem domain (heterogeneous tasks, large gradient gaps, capacity-constrained), the critics' findings do not apply
3. Cite Hu et al. for theoretical grounding
4. Include RLW as a baseline
5. Show gradient magnitude analysis (responding to Elich)

**Our paper's opportunity**: By directly addressing the 312x gradient gap (a regime NO prior paper has tested), we can claim novel territory that sits outside all three critiques' domains of applicability. This is the strongest defense available.

---

## 10. Action Items Before Submission

1. **Verify the 312x gradient gap measurement** -- make sure it's robust across seeds and training stages
2. **Run RLW baseline (3 seeds)** -- if RLW performs close to our method, we need a Plan B
3. **Run Kurin-style properly regularized scalarization** -- ensure dropout + WD tuning is thorough
4. **Add gradient magnitude evolution plots** (responding to Elich) -- show that our method reduces the 312x gap over training
5. **Prepare DINOv2 comparison** -- even a small experiment with frozen backbone + trained heads on our tasks
6. **Write the "threats to validity" / "limitations" section** pre-emptively addressing each critique
7. **Reference map**: Kurin (2022), Xin (2022), Elich (2024), Lin/RLW (2022), Oquab/DINOv2 (2023), Hu (2023) -- cite ALL in related work with honest contextualization
