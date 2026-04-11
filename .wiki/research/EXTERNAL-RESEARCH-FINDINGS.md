# Legion Wiki — External Research Findings
Generated: April 11, 2026
Source: Perplexity deep research

---

## 📊 IKEA ASM Dataset — Thesis Benchmark Baselines

**Source**: WACV 2021 paper + GitHub (IkeaASM/IKEA_ASM_Dataset)
**Dataset**: 3 million frames, multi-view, multi-modal (RGB + depth + pose + atomic actions)
**Tasks**: Action recognition, pose estimation, instance segmentation, part tracking

### Official Baseline Results (Action Recognition)
- **Evaluation metrics**: Frame-wise Accuracy (FA) + Macro-Recall (due to class imbalance)
- **P3D**: Best performing baseline
- **I3D on IKEA ASM**: FA = 57.57% (vs 68.4% on Kinetics, 63.64% on Drive&Act)
  → Dataset is significantly harder than standard benchmarks
- **Key insight**: Multi-task model (pose + action jointly) outperforms single-task approaches

### Legion implication
If WorkerNet exceeds I3D/P3D FA score, that IS publishable.
Dataset is deliberately hard — I3D drops 10% points vs Kinetics.

---

## 🤖 MiniMax M2.7 — Benchmark Evaluation

**Released**: March 18, 2026

### Key Benchmarks vs Competition
| Metric | GPT-4o | MiniMax M2.7 |
|---|---|---|
| GPQA (reasoning) | 54.3% | 87.4% |
| Intelligence index | 17.3 | 49.6 |
| Context window | 128K | 200K |
| Input price/1M | $2.50 | $0.30 |
| Output price/1M | $10.00 | $1.20 |

### Legion implication
MiniMax M2.7 is 8.3x cheaper than GPT-4o and 33% better on GPQA reasoning.
Slower TTFT (1.6s vs 0.45s) — use streaming in Telegram to hide latency.
**Best for**: Long reasoning tasks, thesis research, code generation.

---

## 💰 Indonesian PPh 21 + BPJS — 2026 Updated Rules

### PPh 21 Tax Brackets
| Taxable Income | Tax Rate |
|---|---|
| Up to IDR 60 million | 5% |
| IDR 60M – IDR 250M | 15% |
| IDR 250M – IDR 500M | 25% |
| IDR 500M – IDR 5B | 30% |

### BPJS 2026 Updates (March 2026)
- **BPJS JP ceiling**: Increased 5.11% to IDR 11,086,300 (effective March 1, 2026)
- **BPJS Healthcare**: Minimum IDR 286,494/month (5% of DKI Jakarta minimum wage)
- **DKI Jakarta 2026 minimum wage**: IDR 5,729,876/month

---

## 🎥 Top Computer Vision Conferences 2026

| Conference | Date | Notes |
|---|---|---|
| CVPR 2026 | June 3–7, Denver | Deadline likely passed |
| ECCV 2026 | Sept 8–13, Malmö | Realistic next target |
| WACV 2026 | April 23–27, Rio | Already happened |
| ICCV 2027 | TBD | Skip |

### Practical advice
If thesis writing finishes July 2026, target ECCV 2026 workshop or WACV 2027 main track.

---

## 🏘️ Surakarta / Pajang Boarding House Market

- Near-university kos in Surakarta showing full occupancy listings
- Pajang area is more residential than campus-facing
- 40% → 80% occupancy gap is likely a **visibility problem**
- Consider: Google Business Profile optimization, kos aggregators (Mamikos, Kos-Kosan, Infokos)

---

*Generated: April 11, 2026 — Bashara personal data + Perplexity research*
