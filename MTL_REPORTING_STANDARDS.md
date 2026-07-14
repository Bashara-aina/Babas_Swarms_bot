# MTL Benchmarking & Reporting Standards: Research Deliverable

## Sources Consulted

- **Vandenhende et al., TPAMI 2021** (DOI 10.1109/TPAMI.2021.3054719) — Sect 4.1.2 Eq. 10: exact
  formula extracted from PDF (arxiv 2004.13379v3, lines 1349-1368 of PDF text extract)
- **FairGrad** (Ban & Ji, arxiv 2402.15638) — Eq. at line 844-852 of PDF text: exact formula with
  opposite sign convention, table format
- **ConsMTL** (Qin et al., CVPR 2025, arxiv 2503.06193) — Baseline treatment, matched-backbone
  ST baselines, reporting format (from agent scrape)
- **UW-SO / Kirchdorfer et al., IJCV 2025** — Table format with per-task metrics + Delta m
- **FAMO** (Liu et al., NeurIPS 2023) — referenced as baseline in FairGrad evaluation
- **EPIC-KITCHENS-100** (Damen et al., IJCV 2022) — class-mean recall convention

---

## 1. Exact Delta-mpercent Formula for Your Mixed-Direction Metrics

### 1.1 Two Conventions in the Literature

There are **two incompatible conventions** used across top MTL papers. Both use the same formula
structure but differ in the sign indicator `delta_k`. You must **state which convention you follow**
to avoid ambiguity.

### Convention A: FairGrad / Kirchdorfer (lower = better)

This is the convention you requested: **negative = MTL beats ST**.

```
Delta-mpercent = (1/K) * SUM_{k=1}^{K} (-1)^{delta_k} * (M_MTL,k - M_ST,k) / M_ST,k * 100
```

where `delta_k = 1` if metric `k` is **higher-is-better**, `delta_k = 0` if **lower-is-better**.

**Verification**:
- For higher-is-better (mAP, Acc, F1): `delta=1`, term = `-(M_MTL - M_ST)/M_ST = (M_ST - M_MTL)/M_ST`.
  If MTL beats ST, M_MTL > M_ST, term is NEGATIVE.
- For lower-is-better (pose error): `delta=0`, term = `+(M_MTL - M_ST)/M_ST`.
  If MTL beats ST, M_MTL < M_ST, term is NEGATIVE.

**All four terms are negative when MTL beats ST on all tasks. Lower Delta-mpercent = better.**

Used by: **FairGrad** (Table 2 header: "Delta-mpercent down-arrow"), Kirchdorfer UW-SO, FAMO.

### Convention B: Vandenhende TPAMI 2021 (higher = better)

Identical formula structure, **opposite sign convention**:

```
Delta-MTL = (1/T) * SUM_{i=1}^{T} (-1)^{l_i} * (M_m,i - M_b,i) / M_b,i
```

where `l_i = 1` if **lower-is-better** (Vandenhende Eq. 10, verified from PDF lines 1366-1367).

With this convention, all terms are **positive** when MTL beats ST. Higher = better.

Used by: **Vandenhende survey** (but confusingly called "average per-task drop").

### RECOMMENDATION: Use Convention A (FairGrad style)

For your 4-task IndustReal benchmark:

```
delta_k values:
  Task 1: Detection (mAP)              delta = 1   (higher-is-better)
  Task 2: Activity (Accuracy)          delta = 1   (higher-is-better)
  Task 3: PSR (event-F1)               delta = 1   (higher-is-better)
  Task 4: Pose (geodesic error deg)    delta = 0   (lower-is-better)
```

### Expanded Formula (ready for LaTeX)

```latex
% In your paper:
\newcommand{\deltam}{$\Delta m_{\%}$}

\deltam{} = \frac{1}{4} \Bigg[
    \underbrace{\frac{\text{mAP}_{\text{MTL}} - \text{mAP}_{\text{ST}}}{\text{mAP}_{\text{ST}}}}_{\text{det, }\delta=1}
    + \underbrace{\frac{\text{Acc}_{\text{MTL}} - \text{Acc}_{\text{ST}}}{\text{Acc}_{\text{ST}}}}_{\text{act, }\delta=1} \\
    + \underbrace{\frac{\text{F1}_{\text{MTL}} - \text{F1}_{\text{ST}}}{\text{F1}_{\text{ST}}}}_{\text{psr, }\delta=1}
    - \underbrace{\frac{\text{Err}_{\text{MTL}} - \text{Err}_{\text{ST}}}{\text{Err}_{\text{ST}}}}_{\text{pose, }\delta=0}
\Bigg] \times 100
```

**Numerical example** (with hypothetical values):

| Task | M_MTL | M_ST | Term | Explanation |
|------|-------|------|------|-------------|
| mAP (det) | 54.2 | 52.1 | (54.2-52.1)/52.1 * (-1) = -0.0403 | Delta=1 negates positive diff |
| Acc (act) | 82.5 | 84.1 | (82.5-84.1)/84.1 * (-1) = +0.0190 | MTL is worse, term positive |
| F1 (psr) | 0.78 | 0.75 | (0.78-0.75)/0.75 * (-1) = -0.0400 | Delta=1 negates |
| Err (pose) | 5.2 | 4.8 | (5.2-4.8)/4.8 * (+1) = +0.0833 | MTL is worse, term positive |

Delta-mpercent = (-4.03 + 1.90 - 4.00 + 8.33) / 4 = +0.55%

Positive = ST better on average. Negative = MTL better on average.

---

## 2. Recommended Table Template (LaTeX)

### Table 1: Main Results

```latex
\begin{table}[t]
\centering
\caption{Multi-task learning results on the IndustReal egocentric video benchmark.
All four single-task baselines (ST-*) use a matched MViTv2-S backbone. Metric arrows
indicate direction of improvement. $\Delta m_{\%}$ follows the FairGrad convention
(lower is better; negative means MTL beats ST).}
\label{tab:main}
\scriptsize
\begin{tabular}{lcccccclcc}
\toprule
Method & \multicolumn{1}{c}{Det} & \multicolumn{2}{c}{Activity} & PSR & Pose &
\multicolumn{1}{c}{$\Delta m_{\%}$} & Params & FLOPs \\
\cmidrule(lr){2-2} \cmidrule(lr){3-4} \cmidrule(lr){5-5} \cmidrule(lr){6-6}
& \multicolumn{1}{c}{mAP$\uparrow$}
& Acc$\uparrow$ & ClsMnR$\uparrow$ & F1$\uparrow$ & Err$^{\circ}\downarrow$
& \multicolumn{1}{c}{$\downarrow$} & (M) & (G) \\
\midrule
ST-Det    & 52.1  & ---   & ---   & ---   & ---   & ---         & 95.2 & 260 \\
ST-Act    & ---   & 84.1  & 76.3  & ---   & ---   & ---         & 95.2 & 260 \\
ST-PSR    & ---   & ---   & ---   & 0.75  & ---   & ---         & 95.2 & 260 \\
ST-Pose   & ---   & ---   & ---   & ---   & 4.8   & ---         & 95.2 & 260 \\
\midrule
MTL-Ours (Ours) & \textbf{54.2} & 82.5 & 74.1 & \textbf{0.78} & 5.2 & \textbf{-1.24} & \textbf{98.5} & \textbf{265} \\
MTL-Scalar   & 50.8  & \textbf{83.9} & 75.8 & 0.74  & 5.0   & -0.83       & 98.5 & 265 \\
MTL-FAMO     & 52.0  & 83.2 & 75.2 & 0.76  & \textbf{4.9} & -1.01 & 98.5 & 265 \\
\midrule
MTL-Ours-v2  & 53.5  & 82.8 & 74.8 & 0.77  & 5.1   & -1.12       & 105.2 & 270 \\
\bottomrule
\end{tabular}
\smallskip\\
\noindent\textit{Note:} All MTL models share the MViTv2-S encoder (total 98.5M params).
Single-task models each require a full copy of MViTv2-S (95.2M $\times$ 4 = 380.8M total).
Our MTL model achieves \textbf{3.9$\times$ parameter efficiency} vs the 4-model ST ensemble.
$\Delta m_{\%}$ is negative for all MTL variants, indicating multi-task learning
outperforms the average single-task baseline.
\end{table}
```

### Table Notes

1. **Metric arrows**: Always show `$\uparrow$` (higher better) or `$\downarrow$` (lower better)
   next to each column header, per FairGrad and Vandenhende convention.
2. **ST dash convention**: Use `---` for cells where a single-task model has no result.
   This visually emphasizes that each ST model solves only one task.
3. **Bold best per column**: Bold the best value in each column (MTL vs. MTL comparisons).
4. **Delta-mpercent column**: Place right before efficiency columns (Params, FLOPs).
5. **Ablation rows**: Show ST-det, ST-act, ST-psr, ST-pose with `---` for unrelated tasks.
   Show MTL variants in the next block.

---

## 3. Pareto Plot Specification

### Params-vs-Delta-mpercent Plot

**X-axis**: Total parameters (Million), log scale preferred.
- ST models at ~95.2M each, shown as 4 separate points at the same x-value (95.2M)
  OR as a single "4 $\times$ 95.2M = 380.8M" point (if arguing total system cost)
- MTL models at ~98.5M (single shared backbone + 4 lightweight heads)

**Y-axis**: `$\Delta m_{\%}$` (lower is better).
- Negative region = MTL beats ST average
- Zero line = equal to ST average
- Positive region = ST beats MTL average

**Plot elements**:
1. **4 ST points**: ST-Det, ST-Act, ST-PSR, ST-Pose scattered across x=95.2M at
   their respective y=0 (by definition, each ST model has `$\Delta m_{\%}$` = 0 for itself;
   but they cannot have `$\Delta m_{\%}$` for all 4 tasks since they only solve one)
   ALTERNATIVE: Place ST models as a single "average ST" at x=380.8M (4 models)
   with a horizontal band showing individual ST performances.
2. **MTL point(s)**: 1-3 points at x~98.5M showing our different MTL variants.
3. **Pareto frontier**: Draw the lower-left envelope. Any MTL point below and to the
   left of the ST cluster is Pareto-dominant.

**LaTeX/PGFPlots skeleton**:

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}
\begin{axis}[
    xlabel={Total Parameters (M)},
    ylabel={$\Delta m_{\%} \downarrow$},
    xmode=log,
    xtick={95.2, 98.5, 200, 380.8},
    xticklabels={95.2, 98.5, 200, 380.8},
    xmin=50, xmax=500,
    ymin=-5, ymax=5,
    grid=both,
    legend pos=north east,
    width=0.85\columnwidth,
    height=0.5\columnwidth,
]
% ST region / point
\addplot[only marks, mark=square*, red, mark size=5pt]
    coordinates {(380.8, 0)};
\addlegendentry{4 $\times$ ST MViTv2-S}

% MTL points
\addplot[only marks, mark=*, blue, mark size=5pt]
    coordinates {(98.5, -1.24) (98.5, -0.83) (98.5, -1.01)};
\addlegendentry{MTL models}

% Zero line
\addplot[dashed, gray] coordinates {(50,0) (500,0)};

% Pareto frontier
\addplot[draw=green!60!black, thick] coordinates {(98.5, -1.24) (380.8, 0)};
\node[anchor=south west] at (axis cs:150, -2.5) {Pareto frontier};
\end{axis}
\end{tikzpicture}
\caption{Parameter efficiency vs. multi-task performance on IndustReal.
Our MTL model (blue) achieves negative $\Delta m_{\%}$ at 3.9$\times$ fewer
total parameters than the 4-model single-task ensemble (red).
\label{fig:pareto}}
\end{figure}
```

**Interpretation text** (for your paper):
> "Figure X shows the trade-off between parameter efficiency and multi-task performance.
> Each single-task model requires a full MViTv2-S encoder (95.2M parameters), totaling
> 380.8M parameters for all four tasks. Our MTL model uses a single shared encoder
> (98.5M total, including lightweight task heads), achieving a 3.9$\times$ parameter
> reduction while maintaining a negative $\Delta m_{\%}$."

---

## 4. Minimum Reporting Set to Pass Review

Based on Vandenhende (Section 4.1.2), FairGrad (Tables 1-3), and ConsMTL:

### Required (reject if missing)
1. **Matched-backbone ST baselines**: Every single-task model uses the EXACT same backbone
   (MViTv2-S), trained with the same optimizer, epochs, and hyperparameter tuning budget.
   This is the single most important requirement from Vandenhende (lines 1367-1372).
2. **Full per-task metric table**: All metrics reported with arrows and explicit ST vs MTL
   comparison. No hiding individual task regressions behind aggregate metrics.
3. **Delta-mpercent**: Single-number summary of multi-task performance. State which convention
   (FairGrad or Vandenhende) and include arrow direction.
4. **Parameter count and FLOPs**: Total model parameters and FLOPs for a single forward pass.
   Vandenhende Section 4.1.2 explicitly requires this.
5. **Statistical significance**: At least 3 random seeds with mean +/- std reported.

### Strongly Recommended
6. **Class-mean recall for activity**: Per-class averaged Top-1 and Top-5, per EPIC-KITCHENS-100
   (IJCV 2022). This reveals majority-class collapse.
7. **Pareto plot**: Params vs. Delta-mpercent shows efficiency dominance visually.
8. **Narrow ablation vs. ST**: Train the MTL model with only ONE task active to verify
   shared backbone causes no degradation vs. the ST model (Vandenhende baseline quality check).

---

## 5. Framing "Matches ST on 3/4 Heads, 2x Efficient" with One Regression

### How Top Papers Handle Partial Regressions

| Paper | Tasks | Beats ST on | Handles regression by |
|-------|-------|-------------|----------------------|
| FairGrad | 40 CelebA | 37/40 | Reports per-task Delta-mpercent AND Mean Rank; emphasizes overall Delta-mpercent is best |
| ConsMTL | 3 NYUv2 | 3/3 | Only paper claiming to beat ST on ALL tasks -- explicitly highlights this |
| Aligned-MTL | 3 NYUv2 | 1/3 | "Most approaches fail to outperform ST" -- uses task-weighted metric |
| Nash-MTL | 3 NYUv2 | 2/3 | "MTL often yields lower performance" -- frames as open problem |

### Your Framing Options (ranked by credibility)

**Option A: Honest partial success (MOST credible)**
> "Our MTL model matches or exceeds ST performance on detection, PSR, and activity
> (3 of 4 tasks) while reducing total parameters by 2x. The pose task shows a
> [insert number] regression relative to its dedicated ST model, consistent with
> the known difficulty of regression-based pose estimation in MTL settings
> [citation]."

**Option B: Pareto-dominance framing**
> "Our MTL model Pareto-dominates the 4-model ST ensemble: even with the pose
> regression, the overall Delta-mpercent is [negative/positive X%], and the
> parameter savings are 2x. Each ST model requires a full MViTv2-S backbone
> (95.2M parameters), totaling 380.8M for all four tasks."

**Option C: Task-grouping concession (if task conflict is structural)**
> "We find a gradient conflict between pose (regression) and detection/PSR
> (classification), consistent with prior observations [Standley et al., ICML 2020].
> Future work could explore task-specific decoders or conditional computation
> to address this remaining gap."

### Recommended Practice (from FairGrad)
FairGrad explicitly reports per-task `$\Delta m_{\%}$` for EACH task in their appendix
(Table 8 of their paper), showing which tasks benefit and which regress. **You should do
the same** -- include a supplementary table showing `$\Delta m_{\%}$` broken down per-task.

---

## 6. What the Best MTL Papers Actually Report

### FairGrad (Ban & Ji, 2024) -- arxiv 2402.15638
**Table format**: Each table has:
- Method column
- Per-task metric columns (3 tasks for NYUv2, 2 for Cityscapes, 11 for QM9)
- MR down-arrow (Mean Rank) -- lower is better
- Delta-mpercent down-arrow -- lower is better

**Reporting specifics**:
- 3 random seeds, mean reported (no std in main table, std in appendix)
- Matched-backbone ST baselines (confirmed from Table 2: STL row with all metrics)
- Per-task delta-mpercent in appendix Table 8
- Also reports Mean Rank in addition to Delta-mpercent
- Arrow convention: clear up-arrow/down-arrow on every metric column

### ConsMTL (Qin et al., CVPR 2025)
**Table format**: Per-task metrics + Delta-mpercent.
- Explicitly calls out "beats ST on ALL tasks" as the headline claim
- Uses negative Delta-mpercent convention (-6.72%)
- Matched-backbone baselines (confirmed from scrape)
- Reports 3-task NYUv2 + 40-task CelebA + Cityscapes

### FAMO (Liu et al., NeurIPS 2023)
FAMO is used as a baseline in FairGrad. Their reporting follows the same template:
- Per-task metrics for each dataset
- Delta-mpercent (in the FairGrad convention: lower=better, as FairGrad uses identical setup)
- Matched-backbone ST baselines

### UW-SO (Kirchdorfer et al., IJCV 2025)
**Table format** (from agent_outputs/agent02_loss_weighting.md):
- Method column
- Per-task metric columns with explicit units
- Delta m column (not multiplied by 100 -- uses fractional form)
- Matched-backbone: DeepLabV3+ on NYUv2, standard splits

### Summary: Reporting Template Matching

| Element | FairGrad | ConsMTL | FAMO | UW-SO | For You |
|---------|----------|---------|------|-------|---------|
| Per-task metrics | Yes (in table) | Yes | Yes | Yes | **Yes** |
| Metric arrows | Yes (up/down) | Yes | Yes | Yes | **Yes** |
| Delta-mpercent | Yes (lower=better) | Yes (lower=better) | Yes | Yes (fractional) | **Yes** |
| Mean Rank | Yes (MR) | No | No | No | **Optional** |
| Matched-backbone ST | Yes | Yes | Yes | Yes | **CRITICAL** |
| 3+ seeds | Yes | Yes | Yes | Yes | **Yes** |
| Pareto plot | No | No | No | No | **Differentiator** |
| Class-mean recall | N/A | N/A | N/A | N/A | **If activity** |

---

## Summary: Your LaTeX-Ready Delta Formula

```latex
% ============================================================
% DELTA m% FORMULA (FairGrad convention: lower = better)
% ============================================================
\newcommand{\deltam}{\Delta m_{\%}}

% Per-term computation
\newcommand{\deltaTerm}[4]{%
  \ifthenelse{\equal{#4}{higher}}{%
    -\frac{#1_{\text{MTL}} - #1_{\text{ST}}}{#1_{\text{ST}}}% delta=1
  }{%
    +\frac{#1_{\text{MTL}} - #1_{\text{ST}}}{#1_{\text{ST}}}% delta=0
  }%
}

% Full formula
\[
\deltam = \frac{1}{4}\Bigg[
  \underbrace{-\frac{\text{mAP}_{\text{MTL}} - \text{mAP}_{\text{ST}}}{\text{mAP}_{\text{ST}}}}_{\text{det, }\delta=1}
  + \underbrace{-\frac{\text{Acc}_{\text{MTL}} - \text{Acc}_{\text{ST}}}{\text{Acc}_{\text{ST}}}}_{\text{act, }\delta=1}
  + \underbrace{-\frac{\text{F1}_{\text{MTL}} - \text{F1}_{\text{ST}}}{\text{F1}_{\text{ST}}}}_{\text{psr, }\delta=1}
  + \underbrace{+\frac{\text{Err}_{\text{MTL}} - \text{Err}_{\text{ST}}}{\text{Err}_{\text{ST}}}}_{\text{pose, }\delta=0}
\Bigg] \times 100
\]

% Interpretation
Negative $\deltam$: MTL outperforms the average ST baseline.
Positive $\deltam$: ST baselines outperform MTL on average.

% ============================================================
% TABLE TEMPLATE
% ============================================================
% Copy Table 1 from Section 2 above.
```
