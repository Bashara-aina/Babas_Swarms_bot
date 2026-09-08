# Assembly State Recognition & PSR SOTA on IndustReal Benchmark

**Agent 5 Research Report**
**Date: 2026-08-01**
**Method: Exa search + arXiv + IEEE Xplore + ScienceDirect + project pages**

**Summary**: The research community on the IndustReal benchmark is concentrated in a single group (TU Eindhoven + ASML Research). Three key papers define the current SOTA. No external groups have published IndustReal benchmark results as of this date.

---

## 1. IndustReal: Original Dataset + Benchmarks

**Paper**: "IndustReal: A Dataset for Procedure Step Recognition Handling Execution Errors in Egocentric Videos in an Industrial-Like Setting"
**Authors**: Tim J. Schoonbeek, Tim Houben, Hans Onvlee, Peter H.N. de With, Fons van der Sommen
**Venue**: WACV 2024 (pp. 4365-4374)
**GitHub**: https://github.com/TimSchoonbeek/IndustReal
**Dataset**: 84 egocentric videos, 27 participants, 36 parts, 5.8h, toy car assembly

### 1A. Action Recognition (AR) Benchmarks

| Model | Modality | Pretrain | Top-1 Acc (%) | Top-5 Acc (%) |
|-------|----------|----------|---------------|---------------|
| SlowFast | RGB | MECCANO | 57.83 | 82.87 |
| SlowFast | RGB | Kinetics | 60.39 | 85.21 |
| MViTv2-S | RGB | MECCANO | 62.43 | 85.62 |
| MViTv2-S | RGB | Kinetics | 65.25 | 87.93 |
| SlowFast | RGB+VL+stereo | Kinetics | 62.34 | 85.97 |
| **MViTv2-S** | **RGB+VL+stereo** | **Kinetics** | **66.45** | **88.43** |

Per-modality MViTv2 (Kinetics pretrained): RGB 65.25/87.93, Depth 49.08/76.51, VL 58.59/83.50, Stereo 58.86/83.55

### 1B. Assembly State Detection (ASD) Benchmarks -- YOLOv8-m

| Training Scheme | mAP (annotated frames) | mAP (all frames) |
|-----------------|------------------------|-------------------|
| COCO pretrain + Synthetic only | 0.573 | 0.341 |
| COCO pretrain + IndustReal | 0.753 | 0.553 |
| Synthetic pretrain + IndustReal finetune | 0.779 | 0.575 |
| **Combined synthetic + real** | **0.838** | **0.641** |

Key error analysis: Best model has **false positive rate 65%** and **AP 0.23** for assembly states containing errors. 27% mAP drop when evaluating entire videos vs. only annotated frames.

### 1C. Procedure Step Recognition (PSR) Baselines

Baselines use ASD model output to infer step completions:
- **B1**: Detect state change -> infer completed steps, assume correct
- **B2**: B1 + accumulate confidence over time until threshold
- **B3**: B2 + restrict possible steps to expected procedure order

| Method | All Recordings | | | Recordings with Errors | | |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| | POS | F1 | tau (s) | POS | F1 | tau (s) |
| B1 | 0.570 | 0.779 | 14.9 | 0.480 | 0.698 | 14.4 |
| B1-S (synth only) | 0.014 | 0.206 | 36.9 | 0.000 | 0.174 | 48.4 |
| B2 | 0.731 | 0.860 | 22.3 | 0.636 | 0.784 | 20.2 |
| B2-S | 0.240 | 0.573 | 44.4 | 0.107 | 0.516 | 60.5 |
| **B3 (best)** | **0.797** | **0.883** | 22.4 | **0.731** | **0.816** | 20.4 |
| B3-S | 0.597 | 0.734 | 49.5 | 0.571 | 0.731 | 71.4 |

**Data stats**: 724 correct step completions (8.6 +/- 1.2 per recording), 38 incorrect completions. 35/84 videos (42%) contain missing/incorrectly completed steps.

---

## 2. Assembly State Recognition: Representation Learning + ISIL

**Paper**: "Supervised Representation Learning towards Generalizable Assembly State Recognition"
**Authors**: Tim J. Schoonbeek, Goutham Balachandran, Hans Onvlee, Tim Houben, Shao-Hsuan Hung, Jacek Kustra, Peter H.N. de With, Fons van der Sommen
**Venue**: IEEE Robotics and Automation Letters (RA-L), Vol. 9, No. 11, pp. 9915-9922, 2024
**GitHub**: https://github.com/TimSchoonbeek/AssemblyStateRecognition
**Data extension**: https://data.4tu.nl/datasets/611adbc7-7935-43a6-8c3f-b2260a508e73

### Key Method
Representation learning framework (ResNet-34 / ViT-S encoders) with **ISIL** (Intermediate-State Informed Loss) modification. ISIL treats unlabeled transitional states as negatives only (not pulling them toward a cluster). Applied to Batch Hard triplet loss and SupCon loss.

### 2A. IndustReal Test Set (results reported as figures, exact values not tabulated)

Key findings from paper text:
- Best contrastive ResNet outperforms classification ResNet by **+12% on F1@1**
- SupCon loss improves over cross-entropy by **+69% on MAP@R(+)**
- ViT w/ cross-entropy scores **16% lower on MAP@R(+)** compared to best contrastive ViT
- ISIL improves clustering: **+5% to +22% on MAP@R(+)** across all backbones/losses
- Best configuration: **SupCon + ISIL** for both ResNet-34 and ViT-S

### 2B. Generalization to Unseen Assembly States (synthetic)

| Metric | Improvement over Classification |
|--------|-------------------------------|
| F1@1 (ResNet) | +21% to +53% |
| MAP@R | +85% to +204% |
| ResNet vs ViT | ResNet backbones outperform ViT on generalization |

### 2C. Error Verification (unseen errors, not trained on errors)

4 error categories annotated: (I) missing component, (II) incorrect orientation, (III) incorrect placement, (IV) part-level errors.

Key numeric findings:
- Best contrastive **ResNet** AP on errors: **6% higher** than best classification ResNet
- Best contrastive **ViT** AP on errors: **5% higher** than best classification ViT
- Best ResNet backbone AP is **higher than ViT-S** (ViT-S AP roughly ResNet AP minus 0.58)
- ISIL improves error AP for both contrastive losses and both backbones

---

## 3. STORM-PSR: Current PSR SOTA

**Paper**: "Learning to recognize correctly completed procedure steps in egocentric assembly videos through spatio-temporal modeling"
**Authors**: Tim J. Schoonbeek, Shao-Hsuan Hung, Dan Lehman, Hans Onvlee, Jacek Kustra, Peter H.N. de With, Fons van der Sommen
**Venue**: Computer Vision and Image Understanding (CVIU), Vol. 262, 104528, December 2025
**GitHub**: https://github.com/shaohsuanhung/STORM-PSR
**Note**: Schoonbeek & Hung are equal contribution

### Method
Dual-stream framework: (1) ASD stream for unobstructed views, (2) Spatio-temporal stream with weakly-supervised key-frame selection (KFS) + key-clip aware sampling (KCAS) + transformer temporal encoder. KFS pre-trains a spatial encoder using contrastive loss on step-completion frames. KCAS uses bimodal distribution to over-sample step completions and hard negatives.

### 3A. Main Results (Table 1 from paper)

**IndustReal**:
| Method | POS | F1 | tau (s) |
|--------|:-:|:-:|:-:|
| IndustReal baseline (B3 re-evaluated) | 0.797 | 0.891 | 21.0 |
| Spatio-temporal stream only | 0.497 | 0.506 | 14.2 |
| **STORM-PSR** | **0.812** | **0.901** | **15.5** |

**MECCANO** (newly annotated by authors):
| Method | POS | F1 | tau (s) |
|--------|:-:|:-:|:-:|
| IndustReal baseline (applied to MECCANO) | 0.354 | 0.545 | 99.8 |
| Spatio-temporal stream only | 0.206 | 0.247 | 120.3 |
| **STORM-PSR** | **0.377** | **0.497** | **88.6** |

### 3B. Key Improvements
- **tau reduction on IndustReal**: **26.1%** (22.4s -> 15.5s, or 21.0s baseline -> 15.5s)
- **tau reduction on MECCANO**: **11.2%**
- STORM-PSR achieves **SOTA POS and F1 on IndustReal**
- On MECCANO: POS improves +6%, but F1 decreases -9% (due to data sparsity: 1.1 steps/min vs 2.2 steps/min in IndustReal)
- Pipeline runs at **178 fps** on V100 GPU

### 3C. Ablation Study Highlights

Temporal encoder architecture (w/ KFS + KCAS, spatio-temporal stream only, IndustReal):
| Encoder | POS | F1 | tau (s) |
|---------|:-:|:-:|:-:|
| LSTM | 0.204 | 0.365 | 40.9 |
| TCN | 0.195 | 0.414 | 49.4 |
| Transformer (256-dim) | **0.497** | **0.506** | 14.2 |

STORM-PSR full (with KFS + KCAS) on IndustReal: POS **0.812**, F1 **0.901**, tau **15.5s**
Without KCAS: POS 0.766, F1 0.892, tau 30.0s
Without KFS: POS 0.467, F1 0.511, tau 62.6s

---

## 4. Other Related Work (Not on IndustReal Benchmark)

### ViMAT (Nardon et al., arXiv 2025)
"AI-driven visual monitoring of industrial assembly tasks" -- Uses LEGO scenario with digital twin + object detector trained on synthetic data + probabilistic reasoning (Viterbi). Different dataset, not IndustReal. No comparable numbers.

### Quality-integrated diagnostic (Springer, IJAMT 2024)
Multi-task spatial-temporal transfer learning for complex product assembly. Uses CNN-LSTM + MMD-MSE on array antenna assembly. Reports 97.6% accuracy for quality prediction, but not on IndustReal and not comparable.

---

## 5. Realistic Target Numbers

Based on the above SOTA, realistic targets for new work on IndustReal:

| Task | Metric | Current SOTA | Stretch Target | Notes |
|------|--------|-------------|----------------|-------|
| **PSR (all recordings)** | POS | 0.812 (STORM-PSR) | 0.85 | Small margin above SOTA |
| **PSR (all recordings)** | F1 | 0.901 (STORM-PSR) | 0.92 | Near ceiling |
| **PSR (all recordings)** | tau | 15.5s (STORM-PSR) | 10-12s | Significant room |
| **PSR (recordings w/ errors)** | POS | 0.731 (B3 baseline) | 0.78 | STORM-PSR doesn't report error split |
| **PSR (recordings w/ errors)** | F1 | 0.816 (B3 baseline) | 0.86 | STORM-PSR doesn't report error split |
| **ASD (annotated frames)** | mAP | 0.838 (YOLOv8-m) | 0.87 | Combined synth+real |
| **ASD (all frames)** | mAP | 0.641 (YOLOv8-m) | 0.72 | Major drop from all-frames eval |
| **ASD (error states)** | AP | 0.23 (YOLOv8-m) | 0.40 | Very low; big opportunity |
| **ASR clustering** | MAP@R(+) | ~0.69 over CE | SOTA unknown | SupCon+ISIL best; exact values not in text |
| **ASR classification** | F1@1 | ~0.12 over CE | SOTA unknown | ISIL paper only reports relative gains |
| **Error verification** | AP | ~ResNet > ViT by 0.58 | SOTA unknown | ISIL paper Fig 8; no table |
| **AR (action recog)** | Top-1 | 66.45% (MViTv2 ensemble) | 72% | Multi-modal ensemble |
| **AR (action recog)** | Top-5 | 88.43% (MViTv2 ensemble) | 92% | Multi-modal ensemble |

**Critical note on ISIL paper**: The IEEE RA-L 2024 paper reports results exclusively as figures (Fig 4, 5, 8) with relative percentage improvements in the text, not as a table of absolute numbers. Exact F1@1, MAP@R(+), and error AP values would need to be extracted from the figures or the published code's output logs.

---

## 6. GitHub Repositories

| Repo | URL | Purpose |
|------|-----|---------|
| IndustReal dataset | https://github.com/TimSchoonbeek/IndustReal | Main dataset, AR/ASD/PSR baselines |
| AssemblyStateRecognition | https://github.com/TimSchoonbeek/AssemblyStateRecognition | ISIL representation learning for ASR |
| STORM-PSR | https://github.com/shaohsuanhung/STORM-PSR | Current PSR SOTA |
| PSR annotations (MECCANO) | https://github.com/TimSchoonbeek/PSR-annotations | New MECCANO PSR labels |
| ASR project page | https://timschoonbeek.github.io/state_rec | ASR paper + data links |
| STORM-PSR project page | https://timschoonbeek.github.io/stormpsr | STORM-PSR paper + code |
| IndustReal project page | https://timschoonbeek.github.io/industreal | Dataset + paper |

---

## 7. Key Observations

1. **Single research group**: All IndustReal benchmark results come from the TU Eindhoven + ASML group. No external groups have published competing results as of August 2026.

2. **PSR is bottlenecked by ASD**: All PSR methods rely on assembly state detection as backbone. Improving ASD on error states (AP 0.23) would directly improve PSR on error-rich recordings.

3. **No published MTL approaches**: Despite the natural connection between AR, ASD, and PSR tasks, no multi-task learning approach has been published for IndustReal. This is an open research opportunity.

4. **Error handling is the weak spot**: Both the original baseline and STORM-PSR show significant performance drops on recordings with errors. The B3 baseline drops from POS 0.797/0.883 to POS 0.731/F1 0.816 on error recordings. STORM-PSR does not separately report error-split numbers but the paper discusses this limitation.

5. **Synthetic data is valuable**: The combined synthetic+real training scheme for ASD gives the best results (mAP 0.838), reinforcing the value of the 3D models published with the dataset.

6. **Temporal modeling pays off**: STORM-PSR's 26.1% tau reduction demonstrates that going beyond frame-level ASD to spatio-temporal modeling significantly reduces recognition delay -- the key bottleneck for real-time assistive systems.
