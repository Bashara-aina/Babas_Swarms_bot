### CONTRACT #1: Research Attention-Based Temporal Feature Retrieval Alternatives

WHAT:
  Research attention-based feature retrieval methods (2019-2025) as alternatives to POPW's deque-based Feature Bank, focusing on Longformer, BigBird, Longchat, and memory-augmented networks.

FILES:
  READ: [.wiki/research/018-pose-aware-feature-bank.md, .wiki/research/016-bigru-temporal-action-recognition.md]
  WRITE: .wiki/research/popw-feature-bank-alternatives-attention.md
  RUN: none

DONE_WHEN:
  - File exists at .wiki/research/popw-feature-bank-alternatives-attention.md
  - File contains >500 words with specific paper citations
  - File contains a comparison table with: method name, venue/year, attention mechanism type, memory complexity, params (M), GFLOPs (if reported), accuracy metric
  - File contains specific numbers from at least 4 papers (2019-2025)

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/popw-feature-bank-alternatives-attention.md && wc -w .wiki/research/popw-feature-bank-alternatives-attention.md`
  CONTENT: `head -50 .wiki/research/popw-feature-bank-alternatives-attention.md` — must show frontmatter + table with numeric values

BLOCKER_IF:
  - Cannot find any papers with explicit memory complexity O(T) or better for temporal retrieval
  - Papers found only on skeleton data, not vision features

DEPENDS_ON: none
---
### CONTRACT #2: Research Linear-Time Sequence Model Alternatives to Mamba

WHAT:
  Research linear-time sequence models (2019-2025) as alternatives to Mamba SSM for temporal modeling, covering: RetNet, HyperConnections, Linear Transformers, LSTM/GRU variants, and RWKV.

FILES:
  READ: [.wiki/research/mamba-selective-ssm.md, .wiki/research/mamba-pose-activity-survey.md]
  WRITE: .wiki/research/popw-mamba-alternatives-linear-models.md
  RUN: none

DONE_WHEN:
  - File exists at .wiki/research/popw-mamba-alternatives-linear-models.md
  - File contains >600 words with specific paper citations (arXiv IDs or DOIs)
  - File contains comparison table with: method, complexity (O notation), params (M), GFLOPs (at T=8), throughput relative to Transformer
  - At least 5 methods compared with numeric values
  - Each method has accuracy on a known benchmark (Kinetics-400, NTU RGB+D, or similar)

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/popw-mamba-alternatives-linear-models.md && wc -w .wiki/research/popw-mamba-alternatives-linear-models.md`
  CONTENT: `head -60 .wiki/research/popw-mamba-alternatives-linear-models.md` — must show frontmatter + table with numeric params/GFLOPs

BLOCKER_IF:
  - Cannot find papers with explicit complexity O(T) or O(N) (not O(T²))
  - Papers found lack GFLOPs or parameter counts

DEPENDS_ON: none
---
### CONTRACT #3: Research Efficient Temporal Convolutional Alternatives

WHAT:
  Research temporal convolution alternatives (2019-2025) to both Feature Bank and Mamba, covering: TSM (Temporal Shift Module), P3D (Pseudo-3D), R(2+1)D, X3D, MoViNet, and SlowFast — with specific focus on efficiency metrics.

FILES:
  READ: [.wiki/research/014-video-swin-transformer-liu-2022.md, .wiki/research/006-p3d-resnet-qiu-2017.md]
  WRITE: .wiki/research/popw-temporal-convolution-alternatives.md
  RUN: none

DONE_WHEN:
  - File exists at .wiki/research/popw-temporal-convolution-alternatives.md
  - File contains >500 words
  - Comparison table with: method, params (M), GFLOPs, K400 accuracy (top-1), inference speed (fps or ms)
  - At least 4 methods with complete numeric entries
  - File explicitly compares these to POPW's current BiGRU (2.44M params) and Mamba (0.15M params)

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/popw-temporal-convolution-alternatives.md && wc -w .wiki/research/popw-temporal-convolution-alternatives.md`
  CONTENT: `grep -A 20 "| Method" .wiki/research/popw-temporal-convolution-alternatives.md` — must show table with numbers

BLOCKER_IF:
  - Cannot find GFLOPs for at least 3 methods
  - Papers only on skeleton-based action recognition, not video/vision features

DEPENDS_ON: none
---
### CONTRACT #4: Compile Comprehensive Accuracy Comparison Table

WHAT:
  Compile a comprehensive comparison table of ALL temporal modeling alternatives for pose-aware activity recognition, including: BiGRU, Mamba, Feature Bank, TSM, Video Swin, SlowFast, RetNet, Linear Transformer — with accuracy on pose/activity benchmarks, parameter counts, and GFLOPs.

FILES:
  READ: [.wiki/research/popw-feature-bank-alternatives-attention.md, .wiki/research/popw-mamba-alternatives-linear-models.md, .wiki/research/popw-temporal-convolution-alternatives.md]
  WRITE: .wiki/research/popw-temporal-model-comparison-table.md
  RUN: none

DONE_WHEN:
  - File exists at .wiki/research/popw-temporal-model-comparison-table.md
  - File contains a markdown table with at least 8 methods (rows)
  - Columns include: Method, Year, Complexity, Params (M), GFLOPs, K400 Top-1, Pose Activity Accuracy (if available), Memory Complexity
  - At least 6 rows have complete numeric data (no "N/A")
  - File identifies top 3 methods by efficiency (params + GFLOPs) and top 3 by accuracy

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/popw-temporal-model-comparison-table.md`
  CONTENT: `grep -A 15 "^| Method" .wiki/research/popw-temporal-model-comparison-table.md` — must show table with 8+ rows and numeric values

BLOCKER_IF:
  - Fewer than 6 methods have complete numeric entries in the table
  - Table missing complexity column entirely

DEPENDS_ON: [1, 2, 3]
---
### CONTRACT #5: Synthesize BETTER Alternatives Recommendation

WHAT:
  Synthesize research from contracts 1-4 to produce a final recommendation report identifying BETTER alternatives to POPW's Feature Bank and Mamba-3, with specific evidence-based reasoning and implementation feasibility for POPW's 254-video IKEA assembly dataset.

FILES:
  READ: [.wiki/research/popw-temporal-model-comparison-table.md, .wiki/projects/popw-multi-task-ikea.md]
  WRITE: .wiki/research/popw-better-alternatives-final.md
  RUN: none

DONE_WHEN:
  - File exists at .wiki/research/popw-better-alternatives-final.md
  - File contains >600 words
  - File explicitly names 2 "BETTER" alternatives with specific evidence:
    1. One alternative to Feature Bank (better memory efficiency or retrieval accuracy)
    2. One alternative to Mamba (better accuracy or efficiency for POPW's scale)
  - Each recommendation includes: method name, paper citation, specific numbers (params, GFLOPs, accuracy), and reasoning why it is BETTER than current POPW approach
  - File contains a "Recommendation Summary" section with clear verdict
  - File acknowledges POPW's constraints (RTX 3060 12GB, 254 videos, T=8 window)

PROOF_FORMAT:
  FILE_OP: `ls -la .wiki/research/popw-better-alternatives-final.md && wc -w .wiki/research/popw-better-alternatives-final.md`
  CONTENT: `grep -A 5 "Recommendation Summary" .wiki/research/popw-better-alternatives-final.md` — must show final verdict with method names and numbers

BLOCKER_IF:
  - Cannot identify any method that is objectively BETTER on both efficiency AND accuracy
  - Found methods only validated on datasets with 10K+ videos (not suitable for POPW's 254 videos)

DEPENDS_ON: [4]
