# Agent 1: Detection + Activity Recognition Multi-Task Learning Strategies

## Executive Summary

The core challenge: when adding activity/action classification heads to a detector backbone, detection mAP often degrades due to **negative transfer** and **conflicting gradients**. The shared backbone receives competing optimization signals from localization/regression losses (detection) and cross-entropy losses (classification), causing the shared representation to collapse into a suboptimal compromise for all tasks.

This report surveys SOTA methods across four axes:
1. Joint detection + action recognition architectures
2. Techniques to prevent detection collapse in MTL
3. Benchmark SOTA numbers
4. Papers with joint detection + action recognition training

---

## 1. Joint Detection + Action Recognition Architectures (HADR)

### 1.1 YOWO (You Only Watch Once) -- 2019
- **Venue**: arXiv:1911.06644
- **Author**: Kopuklu et al.
- **Architecture**: Single-stage, two-branch network. 2D-CNN extracts spatial features from keyframe; 3D-CNN extracts spatiotemporal features from clip. Predicts bounding boxes + action probabilities directly in one evaluation.
- **Metrics**:
  | Dataset | Metric | Score |
  |---------|--------|-------|
  | JHMDB-21 | frame-mAP @ 0.5 | ~75% (approx +3% over prior SOTA) |
  | UCF101-24 | frame-mAP @ 0.5 | 80.4% (approx +12% over prior SOTA) |
  | AVA v2.2 | mAP | 17.9% |
- **Speed**: 34 FPS (16-frame), 62 FPS (8-frame)
- **GitHub**: https://github.com/wei-tim/YOWO
- **Key insight**: Two-stream architecture naturally separates spatial detection and temporal action recognition, mitigating task interference.

### 1.2 YOWOv2 -- 2023
- **Venue**: arXiv:2302.06848
- **Architecture**: Enhanced YOWO with anchor-free detection, Feature Pyramid Networks, improved channel attention. Three model sizes (Nano/Tiny/Medium/Large).
- **Metrics**:
  | Model | Dataset | Clip | GFLOPs | Params | F-mAP | V-mAP |
  |-------|---------|------|--------|--------|-------|-------|
  | YOWOv2-Nano | UCF101-24 | 16 | 1.3 | 3.5M | 78.8% | 48.0% |
  | YOWOv2-Tiny | UCF101-24 | 16 | 2.9 | 10.9M | 80.5% | 51.3% |
  | YOWOv2-Medium | UCF101-24 | 16 | 12.0 | 52.0M | 83.1% | 50.7% |
  | YOWOv2-Large | UCF101-24 | 16 | 53.6 | 109.7M | 85.2% | 52.0% |
  | YOWOv2-Large | UCF101-24 | 32 | 91.9 | 109.7M | 87.0% | 52.8% |
  | YOWOv2-Large | AVA v2.2 | 16 | 53.6 | 109.7M | 20.2% mAP | -- |
- **GitHub**: https://github.com/yjh0410/YOWOv2
- **Key insight**: Showed that efficiency and accuracy can co-exist in joint detection+action architectures.

### 1.3 YOWOv3 -- 2024
- **Venue**: arXiv:2408.02623
- **Architecture**: Improved Two-Stream Network. Supports anchor-free detection, General Distribution Prediction (GFocal), TAL and SimOTA label assignment.
- **Metrics**:
  | Model | UCF101-24 mAP | AVA v2.2 mAP | GFLOPs | Params |
  |-------|--------------|-------------|--------|--------|
  | YOWOv3-T | 82.76% | 15.06% | 2.8 | 10.1M |
  | YOWOv3-M | 86.55% | 18.29% | 10.8 | 44.3M |
  | YOWOv3-L | 88.33% | 20.31% | 39.8 | 59.8M |
- **Key improvement**: 54.5% of YOWOv2's parameters while achieving higher mAP on UCF101-24.

### 1.4 YOLO-Act: Unified Spatiotemporal Detection -- 2025
- **Venue**: Sensors 2025, Vol 25, 3013; also in PMC (PMC12115296)
- **Architecture**: Extends YOLOv8 for video action detection. Integrates keyframe extraction (beginning, middle, end), YOLOv8-based action tracking, and class fusion.
- **Metrics**:
  | Metric | YOLO-Act | LART | I3D | SlowFast R101 |
  |--------|----------|------|-----|---------------|
  | AVA mAP | 73.28% | 45.10% | 21.90% | 23.80% |
  | GFLOPs | 114.41 | -- | -- | 138 |
- **Key finding**: +28.18 mAP gain over LART, +51.38% relative over I3D, +49.48% over SlowFast.
- **Note**: Single unified pipeline -- no separate detection and classification stages. The detection and recognition are inherently unified in one forward pass. This is the closest to a "joint detection + action recognition" system.

### 1.5 JoVALE: Joint Actor-centric Visual, Audio, Language Encoder -- 2024
- **Venue**: arXiv:2412.13708
- **Architecture**: Transformer-based, multi-modal (audio + visual + scene-descriptive language from BLIP). Actor-centric Multi-modal Fusion Network (AMFN) aggregates features per actor.
- **Metrics**:
  | Dataset | Backbone | mAP |
  |---------|----------|-----|
  | AVA v2.2 | 3D-CNN | 38.2% (+1.9 over TubeR) |
  | AVA v2.2 | ViT | 40.1% (+2.4 over EVAD) |
  | UCF101-24 | SF-101 | 84.9% |
  | JHMDB51-21 | SF-101 | 91.0% |
- **Key finding**: Adding audio and scene description modalities boosts mAP from 32.7% (visual+scene) to 34.0% (all three) on AVA.

### 1.6 ACAR-Net: Actor-Context-Actor Relation Network -- CVPR 2021
- **Venue**: CVPR 2021
- **Author**: Pan et al.
- **Key achievement**: 1st place AVA-Kinetics Crossover Challenge 2020
- **Architecture**: Models actor-context-actor relations for spatiotemporal action localization.
- **GitHub**: https://github.com/Siyu-C/ACAR-Net

### 1.7 MOGO: Mamba Only Glances Once -- 2025
- **Venue**: OpenReview
- **Architecture**: Pure Mamba-based encoder-decoder for video action detection. No Transformer components. Key innovations: EQ-Mamba, QVI-Mamba decoder.
- **Metrics**:
  | Dataset | mAP | GFLOPs | Params | Latency |
  |---------|-----|--------|--------|---------|
  | JHMDB-21 | 76.7% | 102-104 | ~82M | 3.9 ms/img |
- **Speed**: 256 img/s throughput (vs 240 for EVAD ViT-B, 176 for WOO)
- **GitHub**: https://github.com/YunqingLiu-ML/MOGO
- **Key finding**: Mamba architecture is viable for action detection, offering competitive accuracy with significantly lower compute.

### 1.8 SiA: Scaling Open-Vocabulary Action Detection -- 2025
- **Venue**: arXiv:2504.03096
- **Architecture**: Encoder-only multimodal model. Uses [DET] token regression on ViCLIP video encoder. Weakly supervised pretraining on 700+ action classes.
- **GitHub**: https://siatheindochinese.github.io/sia_act_page/
- **Key finding**: Open-vocabulary action detection benefits from seeing many classes during training (700+ vs typical 18).

---

## 2. Techniques to Prevent Detection Collapse When Adding Classification Heads

### 2.1 Domain Expansion: Preventing Latent Representation Collapse -- 2026
- **Venue**: arXiv:2601.20069
- **Author**: Chi-Yao Huang, Khoa Vo, Aayush Verma, Duo Lu, Yezhou Yang (ASU)
- **Core method**: Assigns each task to a **mutually orthogonal subspace** in the latent space via orthogonal pooling. Proactive (structural) rather than reactive (gradient-level).
- **Key result**: Outperforms Nash-MTL, FAMO, IMTL on all benchmarks (ShapeNet, MPIIGaze, Rotated MNIST).
- **Key insight**: Gradient manipulation methods are "reactive" -- they fix conflicts after they occur. Domain Expansion prevents conflicts structurally by design.
- **GitHub**: Not yet available (preprint January 2026).

### 2.2 MAESTRO: Task-Relevant Optimization via Adaptive Feature Enhancement -- 2025
- **Venue**: arXiv:2509.17462
- **Architecture**: Three components: Class-wise Prototype Generator (CPG), Task-Specific Feature Generator (TSFG) with enhancement + suppression, Scene Prototype Aggregator (SPA).
- **Metrics** (nuScenes):
  | Task | Improvement |
  |------|-------------|
  | 3D Object Detection | +1.2% mAP |
  | BEV Map Segmentation | +3.8% mIoU |
  | 3D Occupancy Prediction | +1.3% mIoU |
- **Key method**: Feature Suppression module "masks out" irrelevant regions for each task, preventing interference.

### 2.3 Recon: Reducing Conflicting Gradients from the Root -- 2023
- **Venue**: arXiv:2302.11289
- **Author**: Guangyuan Shi et al.
- **Core method**: Instead of modifying gradients, **identifies layers with high conflict scores** and turns them into **task-specific layers**. Only a small subset of layers need to be task-specific.
- **Key finding**: "Gradient surgery" (PCGrad, etc.) cannot effectively reduce the occurrence of conflicting gradients. Structural separation of conflicting layers works better.
- **Key finding**: Search for conflict layers once, then reuse across different methods and datasets.

### 2.4 Neural Collapse in Multi-Task Learning -- 2025
- **Venue**: OpenReview (2025)
- **Core theory**: Defines SSMTC-NC (Single-Source Multi-Task Classification NC) and MSMTC-NC (Multi-Source MTC NC).
- **Key finding**: In SSMTC, task-specific classifiers converge to **mutually orthogonal ETFs**. Shared features converge to scaled sum of task-specific classifiers.
- **Implication**: Task correlation **reconfigures the geometry** of task-specific classifiers and promotes feature alignment. Orthogonal classifier geometry naturally prevents interference.

### 2.5 Dual-Head Knowledge Distillation (DHKD) -- 2024
- **Venue**: HuggingFace Papers / arXiv:2411.08937
- **Author**: Penghui Yang et al.
- **Core method**: When two loss functions (CE + BinaryKL) conflict, they cause **classification head collapse** (prevents convergence to simplex ETF). Solution: **split the linear classifier into two heads**, one for each loss.
- **Key insight**: Gradients of two losses contradict each other **only at the classifier head**, not at the backbone. Dual heads preserve beneficial backbone gradients from both losses.
- **GitHub**: https://github.com/penghui-yang/DHKD

### 2.6 Generalist YOLO -- WACV 2025
- **Venue**: WACV 2025, pp. 6217-6227
- **Author**: Chang, Wang, Wang, Chou, Liao
- **Core method**: 
  - **Unified encoder** with 4 feature types (pixel semantic, multi-level instance semantic, instance spatial, interaction relation)
  - **Relaxed optimizer**: Masks gradient channels between vision tasks and language tasks, preventing gradient conflict
  - **Primary-Secondary co-attention** for image captioning
  - **Semantically consistent asymmetric training**: Different augmentation pipelines per task type
- **Metrics** (COCO):
  | Task | Score |
  |------|-------|
  | Detection (AP box) | 52.4% (e2e) / 52.8% (NMS) |
  | Instance Segmentation (AP mask) | 43.0% (e2e) / 43.1% (NMS) |
  | Semantic Segmentation (mIoU 164k) | 44.7% |
  | Panoptic Segmentation (PQ) | 44.2% |
  | Image Captioning (CIDEr) | 122.1 |
- **Speed**: 135x faster than existing generalist models (GiT-H), 4% of parameters.
- **GitHub**: https://github.com/WongKinYiu/GeneralistYOLO

### 2.7 CerberusDet: Unified Multi-Task Object Detection -- 2024
- **Venue**: arXiv:2407.12632
- **Architecture**: YOLO-based multi-headed model. Shared backbone, optional shared neck, task-specific heads.
- **Key method**: Uses **Representation Similarity Analysis (RSA)** to determine which neck modules should be shared vs task-specific.
- **Key finding**: With proper grouping, achieves SOTA data-specific results with 36% less inference time.
- **GitHub**: https://github.com/ai-forever/CerberusDet

### 2.8 TOOD: Task-aligned One-stage Object Detection -- 2021
- **Venue**: arXiv:2108.07755
- **Core problem**: Spatial misalignment between classification and localization predictions in one-stage detectors.
- **Method**: Task-aligned Head (T-Head) + Task Alignment Learning (TAL) -- aligns classification scores with localization quality.
- **Metrics**: MS-COCO 51.1 AP (single-model, single-scale), surpassing ATSS (47.7), GFL (48.2), PAA (49.0).

### 2.9 TSCODE: Task-Specific Context Decoupling -- 2023
- **Venue**: arXiv:2303.01047
- **Core problem**: Classification needs semantic context, localization needs boundary-aware features. Same input features cause imperfect balance.
- **Method**: Generates spatially-coarse but semantically-strong features for classification, high-resolution edge-preserving features for localization.
- **Result**: +1.0 AP across multiple detectors.

### 2.10 UniHead: Unifying Multi-Perception for Detection Heads -- 2023
- **Venue**: arXiv:2309.13242
- **Core method**: Three perceptions unified: deformation perception (deformable conv), global perception (Dual-axial Aggregation Transformer), cross-task perception (Cross-task Interaction Transformer with cross-attention).
- **Metrics**: +2.7 AP (RetinaNet), +2.9 AP (FreeAnchor), +2.1 AP (GFL) on COCO.

### 2.11 Single-Input Multi-Output Model Merging -- 2025
- **Venue**: arXiv:2504.11268
- **Author**: Giraldo, Dimitriadis, Wang, Frossard (EPFL)
- **Key finding**: When merging task-specific encoders in SIMO setting, **representation misalignment** between merged encoder and task-specific heads causes severe degradation (-27.5% to -83.3%).
- **Solution**: Head re-alignment (fine-tune heads) + Representation re-alignment (LoRA).
- **Metrics** (NYUv2): Recovered from -27.5% to -5.4% performance loss vs MTL joint training.

### 2.12 DisTaC: Distillation for Task Vector Conditioning -- 2025
- **Venue**: arXiv:2508.01148
- **Key finding**: Two failure modes cause model merging to fail: (1) disparities in task vector norms, (2) low source-model confidence.
- **Method**: Knowledge distillation on unlabeled data to pre-condition task vectors before merging.
- **Metrics** (RoBERTa-large): Norm mismatch recovery: 58.1 -> 80.5; Low confidence recovery: 73.9 -> 82.3.

---

## 3. Benchmark SOTA Numbers

### 3.1 AVA v2.2 (Spatiotemporal Action Detection, val set)
| Method | Backbone | mAP | Year |
|--------|----------|-----|------|
| JoVALE | ViT (multi-modal) | 40.1% | 2024 |
| EVAD | ViT-B | 32.3% | 2024 |
| STMixer | CSN-152 | 31.7% | 2024 |
| BMVIT | ViT-B | 31.4% | 2024 |
| TubeR | CSN-152 | 29.7% | 2022 |
| SE-STAD | SF-R101 | 29.3% | 2024 |
| WOO | SF-R101 | 28.3% | 2024 |
| YOWOv2-L | ResNext-101 | 20.2% | 2023 |
| YOWOv3-L | -- | 20.31% | 2024 |
| YOWO | ResNext-101 | 17.9% | 2019 |
| **YOLO-Act** | YOLOv8-based | **73.28%** | 2025 |

*Note: YOLO-Act's 73.28% appears to use a different evaluation protocol -- likely full-frame action detection rather than person-centric tube detection. The standard AVA protocol evaluates on detected person boxes, making numbers not directly comparable to YOLO-Act.*

### 3.2 UCF101-24 (Spatiotemporal Action Detection, split 1)
| Method | Backbone | f-mAP @ 0.5 | v-mAP @ 0.2 | Year |
|--------|----------|-------------|-------------|------|
| YOWOv3-L | -- | 88.33% | -- | 2024 |
| YOWOv2-L (32 clip) | ResNext-101 | 87.0% | 52.8% | 2023 |
| YOWOv2-L (16 clip) | ResNext-101 | 85.2% | 52.0% | 2023 |
| JoVALE | SF-101 | 84.9% | -- | 2024 |
| YOWOv3-M | -- | 86.55% | -- | 2024 |
| YOWOv3-T | -- | 82.76% | -- | 2024 |
| YOWOv2-N | ShuffleNetv2 | 78.8% | 48.0% | 2023 |
| YOWO | ResNext-101 | 80.4% | 48.8% | 2019 |

### 3.3 JHMDB-21 (Spatiotemporal Action Detection)
| Method | Backbone | mAP @ 0.5 | Year |
|--------|----------|------------|------|
| JoVALE | SF-101 | 91.0% | 2024 |
| MOGO | Mamba-based | 76.7% | 2025 |

### 3.4 Temporal Action Detection (THUMOS14, ActivityNet)
| Method | Backbone | THUMOS14 avg mAP | ActivityNet-1.3 mAP | Multi-THUMOS mAP | Charades mAP | Year |
|--------|----------|-------------------|---------------------|-------------------|--------------|------|
| Effi-TAD | VideoMAE-B | 72.4% | 38.99% | 44.3% | 28.9% | 2026 |
| Effi-TAD | VideoMAE-L | 74.0% | -- | -- | -- | 2026 |

### 3.5 IMPACT (Industrial Assembly Understanding)
- **Venue**: https://kratos-wen.github.io/IMPACT/
- **Scope**: Real angle grinder assembly/disassembly, 112 trials, 13 participants, 39.5 video hours
- **Modalities**: 5-view RGB-D, ego audio, eye tracking, cognitive metadata
- **Tasks**: Temporal understanding (TAS-S, TAS-BL/BR), Cross-view understanding (CV-TA, CV-SMR, CV-SMC), Forecasting
- **GitHub**: Official benchmark repository with protocols and evaluation code

### 3.6 Video Action Detection Efficiency Comparison
| Method | GFLOPs | Params | FPS/Latency | mAP (AVA/JHMDB) |
|--------|--------|--------|-------------|------------------|
| MOGO | 104 | 82M | 3.9 ms/img (256 img/s) | 76.7% (JHMDB) |
| EVAD ViT-B | 243 | -- | 240 img/s | 32.3% (AVA) |
| WOO | 252 | -- | 176 img/s | 28.3% (AVA) |
| TubeR | 120 | -- | 64 img/s | 29.7% (AVA) |
| YOWOv3-L | 39.8 | 59.8M | -- | 20.31% (AVA), 88.33% (UCF) |
| YOWO | 44 | 121M | 34 FPS | 17.9% (AVA) |
| Hiera | -- | 600M+ | -- | -- |
| VideoMAEv2 | -- | 1B | -- | -- |

---

## 4. Papers Showing Joint Detection + Action Recognition Training

### 4.1 Direct Joint Training of Detection + Classification on the Same Backbone

**YOWO / YOWOv2 / YOWOv3** (2019-2024)
- Two-stream architecture: 2D-CNN for spatial (detection) + 3D-CNN for temporal (action). Outputs are fused and fed to a shared detection head that predicts both bounding boxes and action labels.
- This is the most established paradigm for joint detection+action training.
- **Evidence of mAP improvement from joint training**: The 2D+3D fusion consistently outperforms single-stream approaches.

**YOLO-Act** (2025)
- Single unified YOLOv8 pipeline with keyframe extraction and temporal fusion.
- Detection and action classification happen in the same forward pass.
- **Evidence**: 73.28% mAP on AVA -- but note different evaluation protocol from standard AVA.

**Joint Action and Gesture Recognition via MTL** (Spathis et al., 2025)
- arXiv:2505.17867
- First paper to propose MTL framework handling **both actions and gestures** jointly.
- Uses 3D-ResNet backbone with different weight sharing methods (hard parameter sharing, soft parameter sharing, task-specific heads).
- **Key finding**: "Almost all MTL approaches outperform their single-task variants" -- providing direct evidence that joint training benefits both tasks when properly structured.

**Generalist YOLO** (WACV 2025)
- Trains object detection, instance segmentation, semantic segmentation, panoptic segmentation, and image captioning on a single backbone.
- The "relaxed optimizer" is key: masks gradient channels between vision and language tasks.
- **Evidence**: 52.4% AP detection + 44.7% mIoU segmentation + 122.1 CIDEr captioning all from one model -- without any single-task performance degradation.

### 4.2 Papers Specifically Addressing Detection Collapse in MTL

**CerberusDet** (2024)
- Shows that without careful parameter sharing, MTL can degrade detection. Uses RSA to determine optimal sharing.
- **Evidence**: 36% less inference time while maintaining SOTA per-task accuracy.

**SIMO Model Merging** (Giraldo et al., 2025)
- Directly measures performance degradation: -27.5% to -83.3% when naively merging encoders.
- Shows that head re-alignment recovers most of the loss.

**Dual-Head KD** (Yang et al., 2024)
- Formally proves that conflicting gradients at the classification head cause collapse (prevents simplex ETF convergence).
- Solution: separate heads for conflicting losses.

**TOOD** (Feng et al., 2021)
- Shows that classification and localization heads have spatial misalignment in one-stage detectors.
- Task-aligned head + task alignment learning fixes this.

### 4.3 Theoretical Frameworks

**Neural Collapse in MTL** (OpenReview 2025)
- Proves that in SSMTC setting, task-specific classifiers become **mutually orthogonal**.
- This provides theoretical justification for why decoupled/orthogonal task heads work.

**Domain Expansion** (Huang et al., 2026)
- Formalizes "latent representation collapse" as the core problem.
- Proves that orthogonal subspaces prevent collapse.

**Merging Collapse** (Cao et al., 2026)
- arXiv:2603.09463
- Proves via rate-distortion theory that **representational incompatibility**, not parameter conflicts, drives merging collapse.
- This suggests architecture-level solutions (separate subspaces, decoupled heads) are more fundamental than gradient manipulation.

---

## 5. Gradient Modification Methods (Reactive Solutions)

These are widely cited but evidence shows they are less effective than structural solutions:

| Method | Year | Core Idea | Key Limitation |
|--------|------|-----------|----------------|
| PCGrad (Yu et al.) | 2020 | Project conflicting gradients onto normal plane of others | Recon (2023) showed this doesn't reduce conflict occurrence |
| CAGrad (Liu et al.) | 2021 | Find common gradient that is Pareto optimal | Computationally expensive |
| IMTL (Liu et al.) | 2021 | Closed-form gradient balance | Static, not adaptive to task dynamics |
| Nash-MTL (Navon et al.) | 2022 | Cooperative bargaining game for gradient combination | Domain Expansion outperforms it |
| FAMO (Liu et al.) | 2023 | Dynamic task weighting | Domain Expansion outperforms it |
| GradNorm (Chen et al.) | 2017 | Dynamic loss weighting to balance learning rates | Does not address gradient direction conflicts |
| MGDA (Sener & Koltun) | 2018 | Minimize worst-case loss (Pareto optimal) | Computationally heavy |

**Key conclusion from Recon (2023)**: "Gradient surgery cannot effectively reduce the occurrence of conflicting gradients." Structural solutions (task-specific layers, orthogonal subspaces, decoupled heads) are preferred.

---

## 6. Recommended Strategy for Preventing Detection mAP Degradation

Based on the surveyed literature, the following strategies are ranked by evidence strength:

### Tier 1 (Strong Evidence -- Structural Solutions)
1. **Decoupled task-specific heads** with shared backbone (YOLOv8/YOLOX-style, CerberusDet, DHKD)
2. **Orthogonal subspace assignment** for each task (Domain Expansion 2026)
3. **Task-specific feature enhancement + suppression** (MAESTRO 2025)
4. **Two-stream architecture** separating spatial (2D) and temporal (3D) processing (YOWO family)

### Tier 2 (Moderate Evidence -- Optimization Solutions)
5. **Relaxed optimizer** with gradient channel masking (Generalist YOLO)
6. **Task Alignment Learning** for spatial alignment of detection + classification (TOOD)
7. **Identify and isolate conflicting layers** (Recon 2023)

### Tier 3 (Weaker Evidence -- Loss Balancing)
8. Gradient surgery / gradient modulation (PCGrad, CAGrad, IMTL)
9. Uncertainty weighting / dynamic loss weighting (GradNorm, FAMO)

### Specific Recommendation for Detection + Activity Classification
- Use a **decoupled head architecture** (separate detection head with cls+reg branches, separate action classification head)
- Add a **gradient mask** or **relaxed optimizer** between detection and action tasks
- Consider **orthogonal projection** or **feature suppression** to prevent cross-task interference in the shared backbone
- Monitor **neural collapse metrics** (ETF convergence) for both heads to detect degradation early

---

## 7. Papers with GitHub Repositories

| Paper | GitHub | Year | Venue |
|-------|--------|------|-------|
| YOWO | https://github.com/wei-tim/YOWO | 2019 | arXiv |
| YOWOv2 | https://github.com/yjh0410/YOWOv2 | 2023 | arXiv |
| ACAR-Net | https://github.com/Siyu-C/ACAR-Net | 2021 | CVPR |
| Generalist YOLO | https://github.com/WongKinYiu/GeneralistYOLO | 2025 | WACV |
| CerberusDet | https://github.com/ai-forever/CerberusDet | 2024 | arXiv |
| DHKD | https://github.com/penghui-yang/DHKD | 2024 | arXiv |
| MOGO | https://github.com/YunqingLiu-ML/MOGO | 2025 | OpenReview |
| SiA (OVAD) | https://siatheindochinese.github.io/sia_act_page/ | 2025 | arXiv |
| Effi-TAD | https://github.com/guojiayi1209/Effi-TAD | 2026 | Springer PA&A |
| OpenMixer | https://github.com/Cogito2012/OpenMixer | 2025 | WACV |
| IMPACT Benchmark | https://kratos-wen.github.io/IMPACT/ | 2025 | -- |

---

*Report compiled: 2026-08-01. Searched via Exa across arXiv, PMC, OpenReview, theCVF, Springer, Nature, HuggingFace Papers, and GitHub.*
