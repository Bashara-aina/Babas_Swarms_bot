# POPW Protocol — Project Intelligence

## Domain
Multi-task learning for assembly action recognition on the IKEA ASM dataset.
Tasks: (1) pose estimation via heatmap regression, (2) activity classification.
Backbone: ResNet-50. Conditioning: FiLM (Feature-wise Linear Modulation).
Loss weighting: Kendall homoscedastic uncertainty (learned log-variance σ per task).

## Verified Benchmarks (ground truth — never fabricate these)

### IKEA ASM baselines (Ben-Shabat WACV 2021, arXiv:2007.00394)
- Pose PCK@10px = 64.3, PCK@0.2 = 88.0
- Activity Top-1: I3D combined = 63.09, I3D combined+pose = 64.15
- Temporal loc I3D mAP@0.5 = 20.00

### PC3D (Aganian IJCNN 2023, arXiv:2306.05844)
- Activity Top-1 PC3D (all views, most relevant obj.) = 80.2%

### PTMA (Xie IEEE TMM 2025, arXiv:2508.17025)
- PTMA mcAP: 86.99% (cs), 86.72% (cv), 84.47% (csv)
- PTMA params=12.9M, GFLOPs=1.96, FPS=291

## Codebase Map (code/industreal_improved/)
- model.py         — full multi-task model: ResNet50 backbone + FiLM + heatmap head + classifier head
- train.py         — training loop, Kendall uncertainty weighting, mixed precision, gradient clipping
- losses.py        — KendallLoss, heatmap JointsMSELoss, classification CrossEntropy
- evaluate.py      — PCK metric, Top-1/Top-5 accuracy, mAP for detection
- industreal_dataset.py — IKEA ASM data loader, augmentations, multi-view handling
- config.py        — all hyperparameters (do not hardcode values, always reference config)
- calibrate_anchors.py  — anchor calibration for detection head
- cross_validate.py     — leave-one-subject-out CV protocol
- run_multi_seed.py     — multi-seed averaging for statistical significance
- pretrain_mae.py       — masked autoencoder pretraining
- pretrain_synthetic.py — synthetic data pretraining

## Architecture Details
- Heatmap resolution: see config.HEATMAP_SIZE (do not assume 64×64)
- Number of keypoints: see config.NUM_JOINTS (IKEA ASM hand joints)
- FiLM conditioning: activity label → MLP → (γ, β) applied after each ResNet block
- Kendall loss: L_total = (1/2σ_pose²)·L_pose + (1/2σ_act²)·L_act + log(σ_pose·σ_act)

## Known Issues (from VALIDATION_BUG_REPORT.md)
- evaluate.py had PCK normalization bug — use evaluate.py (current), NOT evaluate.py.bak
- evaluate_patched.py is a transitional version, do not use for final benchmarks
- Validation loss during training can diverge from eval script results due to augmentation mismatch

## Evaluation Protocol
- PCK threshold: @10px and @0.2 (normalized by torso/head size)
- Activity metric: Top-1 accuracy, mcAP for multi-class AP
- Always run run_multi_seed.py (3+ seeds) before reporting final numbers
- Cross-validation: leave-one-subject-out per cross_validate.py

## File Naming Conventions
- Checkpoints: runs/{experiment_name}/checkpoint_epoch_{N}.pth
- Best model: runs/{experiment_name}/best_model.pth
- Logs: runs/{experiment_name}/train_log.json

## Reference Libraries (in .wiki/popw-references/)
- mmpose/ — pose estimation standard (compare heatmap outputs here)
- detectron2/ — detection backbone reference (multi-camera detection)
- mmaction2/ — action recognition standard (compare accuracy here)
- performer-pytorch/ — attention-based FiLM alternative
- pointnet2/ — depth channel processing reference

## What NOT to Do
- Never report single-seed results as final
- Never use evaluate.py.bak for PCK computation
- Never hardcode dataset paths — use config.DATA_ROOT
- Never add batch norm after FiLM layers (architectural constraint)
- Do not mix the v1/v2/v3 hand joint visualizations; use hand_joint_visualizations_final/