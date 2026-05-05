# Research — Academic Work & Computer Vision

Bashara's academic research at Shibaura Institute of Technology. Focused on
multi-task learning for assembly action recognition combining pose estimation
and activity classification on the IKEA ASM dataset.

## What this area owns
- Experiment scripts: training, evaluation, ablation studies
- Model implementations: ResNet-50 backbone, ViT, Mamba variants
- Dataset pipeline: IKEA ASM loader, augmentation, keypoint preprocessing
- Results tracking: wandb / local CSV logs
- Paper writing: LaTeX sections, figures, tables

## Research focus
- Multi-task learning: simultaneous pose estimation + activity classification
- Loss weighting: Kendall uncertainty weighting (homoscedastic)
- Feature conditioning: FiLM (Feature-wise Linear Modulation)
- Heatmap-based keypoint detection
- Backbone comparison: ResNet-50 vs ViT vs Mamba vs BiLSTM

## Key architecture decisions (already made)
- FiLM conditioning: activity features condition pose branch
- Uncertainty weighting: learned log-variance per task loss
- Evaluation: PCK for pose, top-1 accuracy for activity
- Dataset: IKEA ASM — 33 participants, 371 sequences, 17 keypoints

## Constraints
- PyTorch — not TensorFlow
- GPU: check available GPU memory before launching training (nvidia-smi)
- Never overwrite experiment checkpoints without versioning
- Paper is in English — LaTeX, IEEE format
- ADB scholarship application may reference this work — keep results reproducible

## Important files (adjust to actual locations)
- models/ — model architecture files
- data/ — dataset loading pipeline
- train.py — main training script
- eval.py — evaluation script
- configs/ — experiment configs (YAML)

<!-- octogent:suggested-skills:start -->
<!-- octogent:suggested-skills:end -->