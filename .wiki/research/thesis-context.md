# Thesis — WorkerNet / POPW Protocol
Generated: April 11, 2026
Source: BASHARA-MASTER-PROFILE

---

## Overview
- **Project name**: WorkerNet (also called POPW protocol)
- **Type**: Multi-task deep learning for industrial assembly action recognition
- **Institution**: Shibaura Institute of Technology (SIT), Tokyo
- **Advisor**: Prof. Masaomi Kimura
- **Thesis deadline**: July 2026
- **Zemi**: Thursday 1–3PM JST

---

## Technical Details

### Model Architecture
- **Backbone**: ResNet-50
- **Neck**: FPN (Feature Pyramid Network)
- **Conditioning**: FiLM (Feature-wise Linear Modulation)
- **Multi-task weighting**: Kendall homoscedastic uncertainty (automatic task weighting)

### Task Description
Assembly action recognition using POPW protocol:
- Multi-task learning: pose estimation + activity recognition
- Industrial assembly setting (IKEA ASM dataset baseline)
- Input: RGB + depth video frames
- Output: per-frame action labels + pose keypoints

### Dataset
- **Primary**: IKEA ASM dataset (WACV 2021)
- **Train**: 7,743 images | **Test**: 3,596 images
- **Note**: Test split bug fixed Feb 2026 (was class-0 only)
- **Baseline**: I3D on IKEA ASM = 57.57% FA (vs 68.4% on Kinetics)
- **Target**: Exceed I3D/P3D FA score — that IS publishable

---

## Progress
- Proposal complete
- Architecture locked: ResNet-50 + FPN + FiLM + 3 heads
- Implementation: pipeline working, training in progress
- Thesis writing: not yet started
- Target conference: ECCV 2026 workshop or WACV 2027

---

## Advisor Feedback (3 Key Points)
1. Find a hard problem that affects society — stay in domain
2. Understand the real foundations of the architecture you use
3. Build a model better than existing ones in efficiency OR performance

---

## Bashara's Thesis Context
- MEXT visa expires ~September 2027
- Wedding plan with Hanifah (Bandung) pending ADB scholarship decision → September 2026
- Thesis must be defended before visa expiry
- AI spend budget constrained — use MiniMax M2.7 as primary
