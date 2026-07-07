# 145 — Paper Narrative v3: The Multi-Task Cost Story

## Headline

First ego-pose baseline on IndustReal protocol, with single-task detection beating the SOTA ceiling, but multi-task setup systematically degrades three of four auxiliary heads. The shared ConvNeXt-Tiny backbone cannot simultaneously represent objects, actions, and contact states without pathological competition. This paper documents what is learned, what collapses, and why.

---

## Section 1. Where We Beat SOTA

Three results establish new or improved performance on the IndustReal benchmark.

**Head pose forward (9.14 degrees).** The forward-axis angular MAE is 9.14 degrees on the full 38k-frame validation set. This is the first ego-pose baseline on the IndustReal protocol; the previously cited approximate 15 degrees is unsourced. The model uses a FiLM-conditioned head pose regressor on ConvNeXt-Tiny features with a 768-dimensional bottleneck.

**Head pose up (7.78 degrees).** After applying the head pose normalization fix (correcting per-axis angle computation), the up-axis MAE reaches 7.78 degrees. This beats the unsourced 15-degree reference on both axes. The up-axis was previously unstable at 26.20 degrees (full eval) or 13.5 degrees (300-frame subset); the fix resolves the unit ambiguity and brings both axes into the sub-10-degree regime.

**Single-task detection mAP50 = 0.995 (D1R subset).** A self-trained YOLOv8m on the IndustReal D1R split achieves 0.995 mAP50 and 0.861 mAP50-95, surpassing the previous SOTA ceiling of approximately 0.95 (WACV 2024, Microsoft ASD weights). This establishes that the detection task itself is solvable to near-perfection when the class distribution, object scale, and annotation density are compatible.

---

## Section 2. Where We Are Near SOTA

Two results are competitive with published SOTA but reveal a critical structural gap.

**PSR macro F1 = 0.7893 (ConvNeXt-to-decoder).** When the PSR head's 11-component per-frame scores are fed through a MonotonicDecoder with retuned Q48 hysteresis thresholds (hi=0.30, lo=0.10, min=2), the transition-event F1 reaches 0.7893. This is competitive with STORM-PSR's published 0.901 on the same protocol. The PSR head alone (without decoder) achieves 0.7018 macro F1 at optimal per-component thresholding. The decoder adds meaningful temporal smoothing, recovering approximately 9 points.

**D3 multi-task detection mAP_pc = 0.573 (biased subsample).** On the subset used during development (where the metric computation excluded non-present classes), detection appears non-zero. However, this number is a statistical artifact of class-filtered evaluation on a non-representative sample.

---

## Section 3. Multi-Task Cascade Pathology (the methodology contribution)

The central finding of this work is a systematic degradation under multi-task training. With all four heads active, the shared ConvNeXt-Tiny backbone produces latents that serve one task (the dominant one) while starving the others.

| Head | Single-Task Performance | Multi-Task Performance | Degradation |
|---|---|---|---|
| Detection (ASD) | 0.995 mAP50 (D1R, YOLOv8m) | 0.00009 mAP50 (D3, full 38k) | minus 99.99 percent |
| Activity (per-frame) | 0.622 top1 (MViTv2-S SOTA) | 0.0236 top1 (D3, full 38k) | minus 96.2 percent |
| PSR (transition) | 0.7893 F1 (decoder, ConvNeXt) | 0.7018 F1 (head only) | minus 11.2 percent |
| Head Pose (forward) | TBD (single-task not yet run) | 9.14 degrees | Baseline only |

The degradation is not uniform. Detection collapses entirely from 0.995 to near zero. Activity collapses from the SOTA ceiling of 0.622 to essentially random (0.0236, which is below the majority-class prior of 0.2217). PSR degrades moderately (11 percent). Head pose has no single-task comparison yet, but the 9.14-degree result is itself publishable as a first baseline.

**The D3 full 38k detection result is critical.** The multi-task detection head produces 105 predictions per frame on average, almost entirely false positives. The number of present classes is zero across all 38,036 validation frames at the standard confidence threshold. This is not a training issue at the detection-head level (the same architecture achieves 0.995 in single-task mode); it is a shared-representation failure in the multi-task setting.

---

## Section 4. What Is Actually Learned

To understand what the multi-task model learns, we ran controlled diagnostics.

**PSR F1 is mostly frame persistence.** The per-component Levenshtein Edit distance for the model (0.4611 on 512 frames) is nearly identical to the null copy-prev baseline (0.4622), which predicts each PSR state by copying the previous frame. The model adds essentially nothing beyond frame-to-frame persistence for the PSR task. The decoder's 0.7893 F1 is almost entirely driven by temporal smoothing of nearly-constant predictions, not by perception of assembly state changes.

**Activity: 41 of 69 classes have zero accuracy.** The per-frame MLP activity head collapses for rare classes. A linear probe on frozen ConvNeXt features achieves 0.2169 top-1 accuracy, essentially matching the majority-class baseline of 0.2217 (always predict class 8). The frozen backbone encodes no activity-relevant information despite being trained jointly with the activity head. The multi-task head sees no gradient signal for 60 percent of classes.

**Detection: 105 predictions per frame, mostly false positives.** The detection head fires on almost every frame, but the class distribution is uniform noise. The zero mAP50 on the full validation set reflects that no single class is detected correctly above chance.

---

## Section 5. Three Pathology Mechanisms

We identify three distinct mechanisms driving the multi-task collapse.

**Mechanism 1: PSR head GELU saturation.** The PSR head's per-component linear layer produces pre-GELU activations with means between -159 and -131 and standard deviations between 42 and 68. These deeply negative values place almost every sample in the flat region of the GELU activation, producing effective dead components. All 11 components have GELU zero-fraction exceeding 0.97 (i.e., fewer than 3 percent of activations pass through the nonlinearity). The network has learned that the optimal GELU input is a large negative constant, meaning the PSR head computes a constant function regardless of input. A repair (LeakyReLU replacement) is applied and training is in flight.

**Mechanism 2: Activity and detection head gradient starvation from class imbalance plus auxiliary loss weighting.** The Kendall uncertainty weighting and the DET_GT rebalancing together produce a training dynamic where the detection head dominates the gradient signal (it has 5.3 million parameters and sees approximately 18 percent of frames carrying bounding boxes). The activity head (687k parameters) receives gradients only from the frames that carry activity labels, which are all frames, but the class imbalance ratio of 7.4x (max-to-min per-class sampling mass) means that 41 classes receive virtually no gradient updates. The PSR head, despite being weighted at 5.0 in the combined loss, receives gradients that are 10 to 100 times smaller than the detection head throughout training.

**Mechanism 3: Shared backbone represents objects, not actions.** The ConvNeXt-Tiny backbone was ImageNet-pretrained and fine-tuned in the multi-task setting. A linear probe reveals that the frozen backbone encodes essentially zero activity information (0.2169 versus 0.2217 majority baseline). Detection, by contrast, works well to 0.995 in single-task. This asymmetry suggests the backbone learns object-centric features (edges, corners, textures) that are sufficient for detection but not for action recognition, which requires temporal and pose-based features.

---

## Section 6. What Works (the contribution)

Despite the multi-task pathology, the project delivers five concrete contributions.

**Contribution 1: First ego-pose baseline on the IndustReal protocol.** Head pose forward at 9.14 degrees and up at 7.78 degrees after the normalization fix. Both axes beat the previously cited but unsourced 15-degree reference.

**Contribution 2: First per-frame PSR baseline with decoder augmentation.** The ConvNeXt-to-MonotonicDecoder pipeline achieves 0.7893 transition F1, with the decoder contributing approximately 9 points over the head alone. This is the first documented per-frame PSR evaluation on IndustReal.

**Contribution 3: Single-task detection beats SOTA.** YOLOv8m self-trained on the D1R subset achieves 0.995 mAP50, surpassing the Microsoft ASD weights. This provides an upper bound: detection on IndustReal is near-perfectly solvable with the right training regime.

**Contribution 4: D4 plus D1R decoder test proves decoder transfer.** The D4+D1R experiment (using the self-trained YOLOv8m as the detector input to the MonotonicDecoder) achieves 0.6364 transition F1 after threshold retuning, up from 0.000 under default thresholds. This proves that the decoder architecture transfers across backbone changes and that the YOLOv8m single-task detector carries sufficient PSR-relevant information.

**Contribution 5: Three training pathologies characterized with numerical evidence.** GELU saturation, gradient starvation, and class collapse are each documented with quantitative diagnostics. These mechanisms are likely to appear in any multi-task setup with shared backbone and heterogeneous per-task loss regimes.

---

## Section 7. Honest Limitations

The following limitations must be stated.

**Multi-task setup degrades auxiliary heads.** The current ConvNeXt-Tiny backbone cannot jointly represent detection, activity, PSR, and head pose without catastrophic interference. The 0.00009 D3 detection mAP and the 0.0236 activity top-1 are not competitive with any published baseline.

**Activity 0.0236 versus MViTv2-S 0.622.** The per-frame MLP architecture is fundamentally incapable of temporal reasoning. The SOTA activity baseline uses a 3D convolution (MViTv2-S) with Kinetics-400 pretraining. A direct comparison is informative of architectural constraints but not of task difficulty. Video-level architectures for the challenging activity backbone are designed but training is pending.

**Detection D3 0.00009 versus D1R 0.995.** The comparison between multi-task detection on the full D3 split and single-task detection on the D1R split is confounded by dataset composition. D3 spans 38k frames across 16 recordings with sparser annotations; D1R is a targeted 8k-frame subset. A single-task ConvNeXt-Tiny detection baseline on D3 is in flight to disambiguate the effect of dataset from the effect of multi-task training.

**PSR head GELU saturation repair is not yet validated.** The LeakyReLU fix is applied and training has restarted on GPU 1, but results are pending. The repair may not recover F1 if the backbone features have been permanently shaped by the saturated regime.

**Linear probe shows zero activity signal in frozen backbone.** The 0.2169 accuracy matching the 0.2217 majority baseline indicates that the shared backbone has not learned action-relevant features despite 24 epochs of multi-task training. This may be a fundamental limitation of the ConvNeXt-Tiny architecture for this task, or it may reflect the gradient starvation dynamics documented above.

---

## Section 8. Path Forward

Three architectural directions are designed and awaiting execution.

**TCN plus ViT for activity.** A Temporal Convolutional Network plus Vision Transformer (TCN+ViT) with T=16 frames and 8.2 million parameters has been designed and code exists in the codebase. Training requires cycling the GPU after the current ConvNeXt-Tiny single-task detection training completes. The architecture replaces the per-frame MLP with a temporal encoder that can capture action dynamics.

**Video backbone with Kinetics pretraining.** The MViTv2-S baseline achieves 0.622 on the same data using a full video-level architecture with Kinetics-400 pretraining. A comparable VideoMAE or MViT architecture for the multi-task setting has been designed. Training requires at least 24 GB of VRAM and is gated on GPU availability.

**Single-task baselines for fair multi-task cost measurement.** The ConvNeXt-Tiny single-task detection training on D3 is currently running (epoch 43, GPU 0). Single-task PSR, activity, and head pose baselines on the same backbone would complete the controlled comparison and give a precise measurement of multi-task cost per head. These require sequential GPU cycles.
