# Todo

- [ ] Run baseline: ResNet-50 single-task (pose only) — record PCK@0.5
- [ ] Run baseline: ResNet-50 single-task (activity only) — record top-1 accuracy
- [ ] Implement FiLM conditioning layer for multi-task joint training
- [ ] Run multi-task with naive equal weighting — compare vs single-task
- [ ] Implement Kendall uncertainty weighting and run comparison
- [ ] Ablation: FiLM ON vs OFF, uncertainty ON vs OFF (2x2 grid)
- [ ] Implement Mamba backbone variant and run same multi-task experiment
- [ ] Write results table for paper: PCK + Accuracy across all variants
- [ ] Generate qualitative figures: pose overlays on IKEA assembly frames
- [ ] Write methodology section (LaTeX): multi-task formulation + FiLM + Kendall