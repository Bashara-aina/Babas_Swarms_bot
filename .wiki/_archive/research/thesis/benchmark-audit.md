# POPW / WorkerNet — Thesis Benchmark Audit
Generated: April 11, 2026
Source: BASHARA-MASTER-PROFILE + Perplexity research

---

## Thesis: POPW Protocol — Multi-task Deep Learning for IKEA Assembly Action Recognition

### Architecture
- **Backbone**: ResNet-50
- **Neck**: Feature Pyramid Network (FPN)
- **Conditioning**: FiLM (Feature-wise Linear Modulation)
- **Tasks**: Multi-task — pose estimation + assembly action recognition
- **Loss**: Kendall homoscedastic uncertainty weighting
- **Dataset**: IKEA assembly dataset (7,743 train / 3,596 test images)
- **Protocol**: POPW (assembly action recognition research protocol)

### Key Design Decisions (locked)
- Activity head always receives `[B, 2304]` = GAP(C5_mod) + GAP(P4)
- γ uses `1 + tanh ∈ (0, 2)`, β is linear and unbounded
- Residual MLP: 2304 → 512 → 256 → 512 + skip
- C5 routes directly to FiLM (bypasses FPN)
- P3 feeds only pose head; P3–P7 feed detection head

---

## Known Bugs Fixed
1. **Geometric loss using GT keypoints** (Jan 2026) — was using ground-truth instead of predictions
2. **IKEA dataset class-0 collapse** (Feb 2026) — all 3,596 test images had no valid annotations, fixed by rebuilding test split
3. **Soft-argmax boundary bias** — adjusted grid coordinates near borders
4. **Anchor ordering** — ratios-outer/scales-inner to match RetinaNet convention
5. **log_var_pose initialization** — corrected from 0.0 to -1.0
6. **self.samples not being populated** — fixed data flow

---

## Benchmark Baselines — IKEA ASM Dataset

### Dataset Characteristics
- **Source**: WACV 2021 paper + GitHub (IkeaASM/IKEA_ASM_Dataset)
- **Size**: 3 million frames, multi-view, multi-modal (RGB + depth + pose + atomic actions)
- **Tasks**: Action recognition, pose estimation, instance segmentation, part tracking
- **Difficulty**: Significantly harder than standard benchmarks

### Official Baseline Results (Action Recognition)
| Model | Frame-wise Accuracy (FA) | Notes |
|---|---|---|
| I3D | 57.57% | vs 68.4% on Kinetics, 63.64% on Drive&Act |
| P3D | Best performing | Outperforms all other baselines |
| C3D | Lower than P3D | Tested as control |
| ResNet (single-frame) | Lower | Control baseline |

**Key insight**: I3D drops ~10% points on IKEA ASM vs Kinetics — dataset is deliberately harder.

### Multi-task Insight
- Multi-task model (pose + action jointly) outperforms single-task approaches
- Multi-view + pose fusion gives additional improvement
- Depth fusion is inconsistent

---

## Comparable Datasets Audited (17 papers)
The 17-paper audit found:
- Majority contained fabricated or misattributed metrics
- Ego-Exo4D and HA-ViD identified as strongest comparable datasets
- Both have triple annotation: activity + object + 2D keypoints

### Ego-Exo4D (Meta FAIR)
- **Size**: 1,286 hours, 740 participants, 13 cities
- **Coverage**: Egocentric + exocentric synchronized capture
- **Best baseline (keystep recognition)**: View-Invariant Encoder = 41.53% accuracy
- **Potential framing**: WorkerNet as assembly-specialized counterpart

### HA-ViD
- Human assembly video dataset benchmark
- Less widely documented than Ego-Exo4D
- Bashara should verify: `python -c "from datasets import load_dataset; d = load_dataset('assembly-action/HA-VID')"`

---

## Current Status (April 2026)
- Exact epoch/mAP/loss: Bashara updates Legion via chat when running experiments
- Thesis writing deadline: Target ~July 2026
- Target: CVPR-quality conference submission
- Advisor: Prof. Masaomi Kimura

### Advisor's 3 Key Feedback Points
1. Find a hard problem that affects society — stay in domain
2. Understand the real foundations of the architecture you use
3. Build a model better than existing ones in efficiency OR performance

---

## Conference Targets
| Conference | Date | Notes |
|---|---|---|
| CVPR 2026 | June 3–7, Denver | Deadline likely already passed |
| ECCV 2026 | Sept 8–13, Malmö | Realistic next target — deadline ~March/April 2026 |
| WACV 2026 | April 23–27, Rio | Already happened |
| WACV 2027 | TBD | Next WACV main track |

**Practical advice**: If thesis writing finishes July 2026, target ECCV 2026 workshop or WACV 2027 main track.

---

## What "Done" Looks Like for POPW
- Exceed I3D FA baseline (57.57%) and ideally P3D
- Multi-task head working correctly (pose + action jointly)
- FiLM conditioning properly routing C5 features
- Thesis submitted ~July 2026

---

## Related Wiki Files
- `.wiki/profiles/BASHARA-MASTER-PROFILE.md` — thesis overview
- `.wiki/research/EXTERNAL-RESEARCH-FINDINGS.md` — dataset benchmarks
