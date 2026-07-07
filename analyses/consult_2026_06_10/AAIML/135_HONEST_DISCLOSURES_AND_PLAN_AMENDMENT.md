# Honest Disclosures and Plan Amendments

**Source:** Opus §5 (132_OPUS_ANSWERS.md) — 8 honest disclosures enumeration and §4 master plan amendments.

---

## Section 1: The 8 Honest Disclosures (§5.4 of Paper)

The following disclosures must appear verbatim in §5.4 (Limitations and Open Problems) of the paper. Each disclosure identifies a known limitation that the current experiments do not resolve.

### D1. D4 Backbone Swap

The D4 model reported in §4 uses a WideResNet backbone. We have trained a ViT-based variant on the same data but it fails to match WideResNet pose accuracy. This limits claims of architecture generality. [Placeholder: insert F1 result confirming or refuting ViT parity once the TCN+ViT transition experiment in §P2.6 completes.]

### D2. POS Structurally Inflated

The pseudo-observed-space (POS) reconstruction metrics are structurally inflated because the projection head \(g_{\phi}\) is a learned mapping trained to invert the forward model. POS accuracy does not measure whether the learnt latent \(z_t\)'s internal geometry matches true neural geometry. [Placeholder: insert null-POS result from the linear probe control once completed — specifically, report the \(R^2\) of a linear decoder from \(z_t\) to held-out position neurons. If \(R^2\) is near chance, POS is entirely an artifact of \(g_{\phi}\).]

### D3. Activity Rate 0.028 vs Majority Prior

The inferred population activity rate (\(\hat{\alpha} = 0.028\)) is an order of magnitude lower than the majority prior in the experimental literature (0.2–0.4 for rodent hippocampus). Two explanations remain open: (a) the true firing rate in this recording is genuinely sparse, or (b) the PSR prior \(p(\alpha)\) and the variational bound together bias toward low \(\alpha\) to explain variance with fewer active units. We have not disambiguated these.

### D4. Multi-Task Detection at 36% of Ceiling

The multi-task detection rate (jointly decoding position, head direction, and speed from a single latent \(z_t\)) reaches 0.36 of the single-task ceiling. This means the latent does not jointly encode all three variables at the quality of dedicated decoders. Whether this reflects a capacity limit of the 64-dimensional latent or a training dynamic issue (e.g., the multi-task head collapses for the weaker modalities) is unknown.

### D5. PSR Head Gradient Starvation

Analysis of gradient norms during training shows that the PSR reconstruction head receives gradients that are 10–100x smaller than the behaviour decoding heads throughout training. This gradient starvation means the PSR loss may not be effectively minimised, and the learnt latents may be dominated by behaviour-relevant information at the expense of neural dynamics.

### D6. Per-Component Thresholds Tuned on Validation Set

The sparsity threshold \(\lambda\) for each of the 64 latent components was chosen by scanning values on the validation set and picking the value that maximises POS \(R^2\) on held-out validation data. This constitutes leakage of validation information into the model architecture. [Placeholder: insert corrected performance under LOO-CV threshold selection once the leave-one-recording-out threshold stability experiment (§P2 alternative, Week 1 inverted sequence) completes.]

### D7. Up-Vector MAE Unstable

The up-vector (z-axis) mean absolute error shows high variance across recordings, with some recordings exceeding \(15^\circ\) even when head azimuth is below \(5^\circ\). [Placeholder: insert per-recording breakdown once the number-of-recordings-resolved analysis in Week 2 completes. This table should report MAE for each of the \(N\) recordings individually, not just the aggregate.]

### D8. Position Units Unverified

The model assigns 18 of 64 latent dimensions as "position units" (tuned to spatial position via the PSR prior). However, we have not verified whether these 18 units correspond to actual place cells in the recording — i.e., whether their inferred place fields match the spatial tuning of simultaneously recorded pyramidal neurons. This claim therefore rests on an algorithmic definition of place-cell-likeness, not on ground-truth electrophysiology.

---

## Section 2: Master Plan Amendments

Based on Opus §4 analysis, the master plan (130_MASTER_PLAN.md) is amended as follows.

### 2.1 Inverted Week 1 Sequence

Cheap, decisive experiments now precede expensive training runs. The original Week 1 opened with TCN+ViT training (expensive, high risk of null result). The amended sequence begins with:

1. **P2.6 transition-F1** (one forward pass on frozen checkpoint — hours, not days)
2. **Null-POS linear probe** (train a linear layer on frozen latents — hours)
3. **LOO-CV threshold stability** (re-scan thresholds leaving one recording out — overnight)
4. **Gradient norm audit** (log gradient magnitudes during one training restart — one training run)
5. **Per-recording up-vector breakdown** (separate evaluation by recording — hours)

Only after these decisive cheap experiments return do we proceed to TCN+ViT and fixed-weight training.

### 2.2 Head Repair Before Fixed-Weight Training

The original plan scheduled PSR head gradient starvation fix concurrently with fixed-weight training. These must be sequential: first repair the head (increase PSR head learning rate, add gradient clipping, or reweight the loss), verify that PSR gradients are no longer starved, then begin fixed-weight training with the repaired head.

### 2.3 Linear Probe Before TCN+ViT

The null-POS linear probe (§D2) must complete and be analysed before TCN+ViT training begins. The linear probe result gates the interpretation of all subsequent experiments: if POS is entirely an artifact of \(g_{\phi}\), then TCN+ViT improvements to the backbone may not translate to better neural latents.

### 2.4 D4 Threshold Re-Tune Before Disclosure

The D4 (WideResNet) per-component thresholds must be re-tuned under LOO-CV before the disclosure (§D6) is written. The current validation-tuned thresholds likely overestimate performance. Re-tuning may change the reported POS \(R^2\) and activity rate \(\alpha\).

### 2.5 P2.6 Transition-F1 Elevated to Week 1

P2.6 (transition-F1 evaluation) was originally in Week 2. It is now the very first experiment in Week 1 because:

- It requires only a frozen checkpoint and a forward pass.
- The result gates the entire ViT line of inquiry.
- A low transition-F1 on the WideResNet checkpoint would indicate that the transition prior itself is misspecified, independently of backbone choice.

### 2.6 Results-Freeze Protocol End of Week 4

All reported numbers in the paper must be frozen at the end of Week 4. No additional results may be added after this date. Any experiment that does not complete by Week 4 end is reported as "ongoing work" in §5.4 or omitted. This prevents an indefinite extension loop and forces a clean boundary between completed results and future work.

---

## Section 3: Success Metrics Corrections

The success metrics in §3 of the master plan are corrected to reflect Opus's analysis and the honest disclosures.

### 3.1 "Head Pose Up ≤15° by Week 2" → Up-Vector Recording-Resolved

**Old metric:** "Head pose up-vector MAE ≤15° by Week 2."
**Corrected metric:** "Up-vector MAE resolved per-recording: report number of recordings where MAE ≤15° and number where MAE >15°. A bar plot showing per-recording MAE with recording-level error bars must be produced by Week 2. The aggregate ≤15° milestone is removed — the paper will disclose per-recording instability (§D7)."

### 3.2 "Activity ≥0.10 by Week 4-5" → Gate on Linear Probe

**Old metric:** "Inferred activity rate \(\alpha \geq 0.10\) by Week 4-5."
**Corrected metric:** "Activity rate improvement is gated on the linear probe result (§D2). If the linear probe shows that POS is structurally inflated, then \(\alpha\) is not a trustworthy metric and no target is set. If the linear probe shows genuine structure in \(z_t\), then the \(\alpha \geq 0.10\) target is pursued via LOO-CV threshold re-tuning (§2.4) and PSR head repair (§2.2), with a revised deadline of Week 5."

### 3.3 All Reported Numbers Traceable to Freeze Checkpoint

**New metric (added):** "Every numerical claim in the paper must be traceable to a specific freeze checkpoint (commit hash + config hash). A results provenance table must be maintained listing: (a) the claim, (b) the section, (c) the checkpoint identifier, (d) the evaluation script path, and (e) the random seed. This table must be complete before the results-freeze protocol applies at end of Week 4."

### 3.4 Transition-F1 Target

**New metric (added):** "Transition-F1 (P2.6) target: \(F_1 \geq 0.75\) on held-out recording. If this target is not met by the WideResNet checkpoint, the transition prior §3.3 claim is downgraded to a limitation and disclosed in §5.4 alongside D1–D8."
