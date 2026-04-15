## Execution Order
Serial (must run in sequence): [1, 2, 3, 4]
Parallel (can run simultaneously): none
Final gate (must run last): Contract #4 (output file must be >200 words)

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LaTeX file not found in workspace | H | M | Use existing wiki research instead |
| Prior research files missing or incomplete | M | H | Verify file existence before reading |
| GFLOPs reported at different resolutions | H | L | Note resolution context in output |
| Methods not validated on assembly datasets | M | H | Focus on pose-aware activity methods |

---

### CONTRACT #1: Verify Prior Research Files Exist

WHAT:
  Verify existence of all 5 prior research files from 2026-04-15 POPW temporal modeling research and read key context for this ASM-focused task.

FILES:
  READ:  [.wiki/research/popw-better-alternatives-final.md, .wiki/research/popw-temporal-model-comparison-table.md, .wiki/research/popw-feature-bank-alternatives-attention.md, .wiki/research/popw-mamba-alternatives-linear-models.md, .wiki/research/popw-temporal-convolution-alternatives.md]
  WRITE: none
  RUN:   ls -la .wiki/research/popw-better-alternatives-final.md .wiki/research/popw-temporal-model-comparison-table.md .wiki/research/popw-feature-bank-alternatives-attention.md .wiki/research/popw-mamba-alternatives-linear-models.md .wiki/research/popw-temporal-convolution-alternatives.md

DONE_WHEN:
  - All 5 files exist at their exact paths
  - popw-better-alternatives-final.md contains >200 words with specific method recommendations
  - popw-temporal-model-comparison-table.md contains a markdown table with >8 rows
  - Each file has been read and key metrics extracted (params, GFLOPs, accuracy)

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/popw-better-alternatives-final.md .wiki/research/popw-temporal-model-comparison-table.md .wiki/research/popw-feature-bank-alternatives-attention.md .wiki/research/popw-mamba-alternatives-linear-models.md .wiki/research/popw-temporal-convolution-alternatives.md && wc -w .wiki/research/popw-*.md`
  CONTENT: `head -30 .wiki/research/popw-better-alternatives-final.md` — must show frontmatter with title and summary

BLOCKER_IF:
  - Any of the 5 prior research files do not exist
  - popw-better-alternatives-final.md has <200 words

DEPENDS_ON: none

---

### CONTRACT #2: Research ASM-Specific Methods Beyond POPW Research

WHAT:
  Research state-of-the-art assembly sequence modeling (ASM) methods not covered in POPW's prior temporal research, focusing on: (1) ASM-specific architectures, (2) methods evaluated on IKEA ASM, IndustReal, or Assembly101, (3) pose-aware temporal modeling for procedural activities.

FILES:
  READ:  [.wiki/research/005-ikea-asm-dataset-2021.md, .wiki/research/041-sener-assembly101-2022.md, .wiki/research/045-industreal-dataset-2024.md, .wiki/research/048-manufacturing-survey-2024.md]
  WRITE: .wiki/research/asm-alternatives-sota-research.md
  RUN:   none

DONE_WHEN:
  - File exists at .wiki/research/asm-alternatives-sota-research.md
  - File contains >400 words
  - File identifies at least 3 methods specifically for assembly/obstacle course/ procedural activity modeling
  - Each method has: paper citation, params (M), GFLOPs, accuracy on at least one ASM dataset (IKEA/IndustReal/Assembly101)
  - File contains explicit comparison showing why these methods are BETTER alternatives

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/asm-alternatives-sota-research.md && wc -w .wiki/research/asm-alternatives-sota-research.md`
  CONTENT: `head -50 .wiki/research/asm-alternatives-sota-research.md` — must show frontmatter and method names with numbers

BLOCKER_IF:
  - Cannot find any method with explicit evaluation on IKEA ASM, IndustReal, or Assembly101
  - Found methods only for generic action recognition (Kinetics, Charades) without assembly focus

DEPENDS_ON: [1]

---

### CONTRACT #3: Compile Dataset-Specific Accuracy Comparison

WHAT:
  Compile a structured comparison of temporal modeling alternatives specifically for assembly sequence modeling, with per-dataset accuracy metrics for IKEA ASM, IndustReal, and Assembly101. Include methods from prior research and ASM-specific methods from Contract 2.

FILES:
  READ:  [.wiki/research/popw-temporal-model-comparison-table.md, .wiki/research/asm-alternatives-sota-research.md, .wiki/research/005-ikea-asm-dataset-2021.md, .wiki/entities/assembly101.md]
  WRITE: .wiki/research/asm-alternatives-dataset-comparison.md
  RUN:   none

DONE_WHEN:
  - File exists at .wiki/research/asm-alternatives-dataset-comparison.md
  - File contains >300 words
  - File contains a markdown table with columns: Method, Year, Params (M), GFLOPs, IKEA ASM Acc, IndustReal Acc, Assembly101 Acc
  - At least 5 rows have partial or complete dataset-specific accuracy (not all "N/A")
  - File highlights which methods have been validated on small datasets (<500 videos)

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/asm-alternatives-dataset-comparison.md && wc -w .wiki/research/asm-alternatives-dataset-comparison.md`
  CONTENT: `grep -A 20 "^| Method" .wiki/research/asm-alternatives-dataset-comparison.md` — must show table with dataset columns

BLOCKER_IF:
  - Table has no accuracy values for any of the three datasets (all "N/A")
  - Fewer than 3 methods total found with any dataset evaluation

DEPENDS_ON: [2]

---

### CONTRACT #4: Write Final Structured ASM Alternatives Research Output

WHAT:
  Write a structured research output file to .wiki/research/asm-alternatives-final.md that synthesizes all prior research and Contracts 1-3, identifying BETTER alternatives to Feature Bank and MAMBA-3 for ASM evaluation. The output must compare accuracy, efficiency (Gflops), and parameters across IKEA, IndustReal, and Assembly101 datasets.

FILES:
  READ:  [.wiki/research/popw-better-alternatives-final.md, .wiki/research/asm-alternatives-sota-research.md, .wiki/research/asm-alternatives-dataset-comparison.md]
  WRITE: .wiki/research/asm-alternatives-final.md
  RUN:   none

DONE_WHEN:
  - File exists at .wiki/research/asm-alternatives-final.md
  - File contains >200 words
  - File explicitly names at least 2 BETTER alternatives with specific evidence
  - File includes a comparison table with: Method, Params (M), GFLOPs, IKEA ASM Acc, IndustReal Acc, Assembly101 Acc
  - File identifies the recommended alternative(s) for POPW's constraints (254 videos, RTX 3060)
  - File acknowledges POPW's constraints (small dataset, real-time inference)

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/asm-alternatives-final.md && wc -w .wiki/research/asm-alternatives-final.md`
  CONTENT: `grep -A 10 "BETTER alternatives\|Recommendation\|## " .wiki/research/asm-alternatives-final.md` — must show named alternatives with specific metrics

BLOCKER_IF:
  - Output file has <200 words
  - No method is identified as BETTER on both accuracy AND efficiency criteria
  - No dataset-specific accuracy values found for any method

DEPENDS_ON: [3]
