# CLAUDE SCIENCE V2 — FINAL CONSULTATION
## 20-Agent Deep Research Swarm → 20 MD Files for Claude Science

### CONTEXT
This is our FINAL consultation for the IndustReal MTL dataset targeting AAIML 2027.
V1 (previous consultation) produced 10 discovery agents + 5 debaters + 5 synthesizers.
V1 found: no published MTL beats ST on all tasks when detection is included — this is our white space.
Now V2 must go DEEPER: data quality, remaining gaps, architecture limits, and everything needed to win.

---

### LOAD THESE FIRST (Consultation V1 outputs)

All paths relative to:
`analyses/consult_claude_science/agent_outputs/`

1. **FINAL_CONSULTATION_REPORT.md** — V1 executive summary and recommendations
2. **IMPLEMENTATION_PLAN.md** — 30 ranked items (Tier 1-4) from V1
3. **VERIFIED_CITATIONS.md** — ~100 papers with verified citations, arXiv IDs, code URLs
4. **agent01-10_*.md** — All 10 Phase 1 discovery reports
5. **agent11-15_debate_*.md** — All 5 Phase 2 adversarial debate reports

### ALSO LOAD THESE (V1 Context Docs)
`analyses/consult_claude_science/`:
- `208_OVERVIEW_CONSULTATION_PACKAGE.md` — Project overview
- `212_PER_HEAD_GAP_ANALYSIS.md` — Per-task MTL/ST/SOTA numbers
- `215_50_DEEP_QUESTIONS.md` — Original 50 questions
- `216_AAIML_WINNING_PAPER_STRATEGY.md` — Venue strategy
- `217_LOSS_FUNCTION_DEEP_DIVE.md` — Per-task losses
- `218_DATA_AND_AUGMENTATION_STRATEGY.md` — Dataset

### LOAD THESE (Codebase to Analyze)
- `src/config.py` — Full config
- `src/models/mvit_mtl_model.py` — Full model
- `src/losses/` — All loss modules (check what's changed since V1)
- `scripts/train_mtl_mvit.py` — Training loop
- `src/data/industreal_dataset.py` — Dataset loader
- `src/data/det_augment.py` — Augmentations

---

## 20 AGENT ASSIGNMENTS

### PHASE 1 — DATA INTEGRITY (Agents 1-5)
Each agent uses: `paper-search` MCP, `crawl4ai`, Exa for methodology verification, `python3` + `bash` for local data analysis.

**Agent 1: Training Data Deep Audit**
- Analyze all 26K training frames: class distribution per task, temporal coherence, annotation quality
- Check: PSR positive rate <0.5%, activity 75-class power-law tail (16 classes with <10 samples)
- For each task: measure annotation noise, missing annotations, temporal consistency
- Use: `python3 -c "..."` to compute statistics from the actual dataset, `crawl4ai` to fetch annotation methodology papers
- Output: `agent01_data_audit.md` with exact numbers, histograms, problem statements
- Questions for Claude Science:
  1. Does annotation noise in PSR explain the constant-prediction failure?
  2. How many activity tail classes are beyond recovery even with LDAM/balanced softmax?
  3. Is there temporal annotation drift across the 16 recordings?
  4. What is the inter-annotator agreement for each task?

**Agent 2: Validation Data Scrutiny**
- Analyze all 38K validation frames
- Check: distribution shift vs training data, label leakage, temporal overlap between train/val splits
- For each task: val performance floor (what does a constant predictor score?)
- Output: `agent02_val_analysis.md` with val distribution, ceiling/floor analysis, split integrity
- Questions:
  1. Does the val set have distribution shift from training (different recordings, different lighting)?
  2. Is there any temporal leakage between the 10 train and 6 val recordings?
  3. What is the theoretical maximum performance given annotation quality?
  4. Are val metrics stable across recordings or dominated by easy/hard recordings?

**Agent 3: Detection Annotation Quality**
- Deep dive on 24-class detection: bounding box quality, small object distribution, occluded objects
- Check: min/max/avg box size per class, aspect ratio distribution, classes with <10 instances
- Compare against COCO, LVIS, other detection benchmarks
- Output: `agent03_detection_data.md`
- Questions:
  1. How many Instances per class? Are tail classes learnable at 224px?
  2. What is the smallest object size? Is 224px resolution fundamentally limiting detection?
  3. Are there annotation errors (missing boxes, wrong class, wrong size)?
  4. Would removing tail classes or merging them improve mAP meaningfully?

**Agent 4: Activity & PSR Annotation Analysis**
- Activity: per-class sample counts, confusion pairs, temporal consistency of labels
- PSR: transition frame accuracy, state duration distribution, annotation protocol
- Output: `agent04_activity_psr_data.md`
- Questions:
  1. Activity: which classes are commonly confused? Is the 75-class taxonomy too fine?
  2. Activity: are there class hierarchies that could improve learning?
  3. PSR: what is the ground-truth transition frame accuracy? +-1 frame? +-5 frames?
  4. PSR: would Gaussian-smeared targets (sigma=2) actually improve F1 given annotation noise?

**Agent 5: Pose & Temporal Consistency**
- Head pose: 6D annotation distribution, per-recording variability, temporal smoothness
- Temporal: frame-to-frame consistency across all tasks
- Output: `agent05_pose_temporal.md`
- Questions:
  1. Pose: is the 9 deg MAE ceiling due to annotation noise or model capacity?
  2. Pose: are extreme errors (>30 deg) annotation mistakes or genuine model failures?
  3. Temporal: does frame-to-frame label jitter limit performance?
  4. Would temporal smoothing of annotations improve all tasks?

---

### PHASE 2 — ARCHITECTURE LIMITS & OPPORTUNITIES (Agents 6-10)
These agents evaluate whether the current architecture can reach AAIML-winning performance.

**Agent 6: Backbone Capacity Analysis**
- Evaluate MViTv2-S (34.5M) vs alternatives: MViTv2-B, VideoMAE, TimeSformer, ConvNeXt
- Use: `paper-search` MCP for backbone comparison papers, `academic-search` for Google Scholar
- Compute: FLOPs, params, throughput at 224px × T=16 for each backbone
- Key question: is MViTv2-S fundamentally underpowered for 4 heterogeneous tasks?
- Output: `agent06_backbone_analysis.md`
- Questions:
  1. What backbone gives the best MTL vs ST tradeoff for 4 tasks including detection?
  2. Does a larger backbone (MViTv2-B, 54M) improve all tasks equally or widen the detection gap?
  3. Are there published MTL results with MViTv2 backbone on detection+classification+regression?
  4. What is the FLOPs budget for real-time inference? Does our current model meet it?

**Agent 7: BiFPN & Neck Architecture**
- Current LightweightFPN: is it sufficient for 4 tasks? Does detection need a stronger neck?
- Compare: BiFPN, NAS-FPN, PANet, task-specific necks
- Output: `agent07_neck_architecture.md`
- Questions:
  1. Does the current FPN limit detection at 224px + small objects?
  2. Would task-specific FPNs (separate necks per task) help without breaking parameter efficiency?
  3. What neck design gives the best MTL/ST retention for detection?
  4. Is there a neck architecture that explicitly handles multi-scale MTL features?

**Agent 8: Task Head Architecture**
- Current heads: DetectionHead, ActivityHead, PSRHead, PoseHead
- For each head: capacity (params, layers), architecture choice, comparison to published SOTA
- Output: `agent08_head_architecture.md`
- Questions:
  1. ActivityHead: 75-class classifier with conv_proj features — is this architecture too simple?
  2. PSRHead: can a temporally-aware head (TCN, Transformer) solve the F1=0 problem?
  3. PoseHead: 6D rotation head — is the current head limiting the 9 deg MAE?
  4. DetectionHead: is RetinaNet-style anchor-based head the best choice at 224px?

**Agent 9: Training Pipeline Optimization**
- Analyze the full training loop: LR schedule, optimizer, batch composition, gradient flow
- Check: PCGrad effectiveness, gradient conflict patterns, task interaction
- Use: existing gradient diagnostic scripts, `e8_gradient_diagnostic.py`
- Output: `agent09_training_pipeline.md`
- Questions:
  1. Is CosineAnnealingLR without warmup the right schedule for MTL? Compare to linear warmup + cosine.
  2. What batch composition strategy maximizes learning: pure random, balanced per task, curriculum?
  3. Is AdamW the right optimizer? Compare to SGD with nesterov for MTL.
  4. Does gradient conflict vary across training? When does PCGrad help most?

**Agent 10: Efficiency & Inference Optimization**
- Current: 11 FPS inference, 48.6M params. Can we improve both accuracy AND efficiency?
- Compare: pruning, quantization, knowledge distillation, efficient attention
- Output: `agent10_efficiency.md`
- Questions:
  1. Can we hit real-time (30 FPS) with accuracy improvements? What needs to change?
  2. Would knowledge distillation from a larger backbone help all tasks?
  3. Are there efficient attention mechanisms that reduce FLOPs without accuracy loss?
  4. What is the pareto frontier of accuracy vs FLOPs for MTL with our task set?

---

### PHASE 3 — LITERATURE DEEP DIVE (Agents 11-15)
These agents search for specific solutions to our remaining problems.

**Agent 11: Detection-Specific MTL Solutions**
- Search for papers that solve detection degradation in MTL specifically
- Use: `paper-search` MCP (all 20+ sources), `academic-search`, Exa cross-field
- Focus: methods that recover detection performance in multi-task models
- Output: `agent11_detection_mtl.md`
- Questions:
  1. What specific techniques recover detection mAP in MTL (beyond TSBN)? Rank by published improvement.
  2. Are there detection-specific MTL benchmarks with published results we should compare against?
  3. Does task-specific batch normalization fully close the gap or only partially?
  4. What is the SOTA MTL detection mAP at 224px? How far are we?

**Agent 12: Activity Classification in MTL**
- Search for long-tail activity recognition + MTL intersection
- Use: `paper-search` MCP, `crawl4ai` for PDF extraction, Jina Reader for markdown
- Output: `agent12_activity_mtl.md`
- Questions:
  1. What is the SOTA for 75-class egocentric activity recognition with long-tail distribution?
  2. Can decoupled training (Kang ICLR 2020) recover activity performance in MTL setting?
  3. Is the activity head gradient-starved by detection? How to measure and fix this?
  4. Would a 2-stage training (activity-first, then detection) produce better balance?

**Agent 13: PSR / Temporal State Detection**
- Search for papers on procedure step recognition, temporal action segmentation, state detection
- Key challenge: F1 near zero from constant prediction. Is this a loss problem or architecture problem?
- Output: `agent13_psr_temporal.md`
- Questions:
  1. What loss functions are proven for extreme class imbalance (<0.5% positive) in temporal detection?
  2. Is PSR a temporal modeling problem? Would a TCN/GRU/Temporal Transformer help?
  3. Are there published papers with successful PSR at similar positive rates?
  4. What is the correct evaluation metric for PSR when event-F1=0?

**Agent 14: Head Pose Regression in MTL**
- Search for 6D head pose estimation in multi-task settings, or MTL with regression tasks
- Output: `agent14_pose_regression.md`
- Questions:
  1. What is the SOTA 6D head pose from egocentric video? How does our head compare?
  2. Are there MTL-specific techniques for improving regression task performance?
  3. Does geodesic loss + Huberisation (V1 Item 10) have published evidence for pose?
  4. What data augmentation specifically improves head pose accuracy?

**Agent 15: Training Stability & Generalization**
- Search for MTL training stability, generalization theory, regularization for MTL
- Output: `agent15_training_stability.md`
- Questions:
  1. What regularization techniques are proven for MTL with 4+ heterogeneous tasks?
  2. Is there evidence that MTL models generalize worse than ST? How to measure?
  3. What is the theoretical sample complexity for MTL vs ST?
  4. Are there published MTL training tricks that consistently improve all tasks?

---

### PHASE 4 — AAIML STRATEGY & SYNTHESIS (Agents 16-20)

**Agent 16: Paper Positioning**
- Based on ALL V1+V2 findings: what is our strongest paper narrative?
- Use: `216_AAIML_WINNING_PAPER_STRATEGY.md`, V1 outputs, V2 findings
- Output: `agent16_paper_positioning.md`
- Questions:
  1. What is the strongest claim we can make with evidence from V1+V2?
  2. What claims must we qualify or avoid?
  3. What is our "killer result" that makes the paper stand out at AAIML?
  4. What baselines must we compare against, and what metrics must we report?

**Agent 17: Competitor Landscape**
- Search for papers that WILL be published at AAIML 2027 or similar venues
- Search for: MTL, efficient video understanding, egocentric vision, IndustReal-like datasets
- Output: `agent17_competitor_landscape.md`
- Questions:
  1. Who are our direct competitors? What datasets, backbones, tasks do they use?
  2. What is the expected SOTA at AAIML 2027 submission time?
  3. Are there concurrent submissions we should be aware of?
  4. What differentiates our work from expected competition?

**Agent 18: Final Implementation Roadmap**
- Based on ALL V1+V2 findings: produce the final implementation ranking
- Rank by: impact on AAIML acceptance probability / implementation effort
- Output: `agent18_final_roadmap.md`
- Questions:
  1. What is the minimum viable paper (MVP): smallest set of changes that produces a publishable result?
  2. What is the "bet the farm" set: all high-risk high-reward changes?
  3. What changes MUST be made regardless of results?
  4. What is the compute budget for each scenario?

**Agent 19: Risk & Contingency**
- For each proposed change: probability of success, compute cost, evidence strength
- Define decision gates: at what point do we pivot?
- Output: `agent19_risk_contingency.md`
- Questions:
  1. If our central hypothesis fails (MTL cannot beat ST with detection), what is our fallback paper?
  2. If activity remains below 15% top-1, do we drop it from the paper?
  3. If PSR F1 stays below 0.05, do we include it as a negative result?
  4. What is the minimum acceptable result for each task to publish?

**Agent 20: V2 Synthesis & Claude Science Query Pack**
- Compile ALL V2 findings into 20 targeted Claude Science queries
- Each query should be self-contained, with context, specific ask, and expected output format
- Output: `agent20_claude_science_queries.md` with 20 ready-to-paste queries
- Each query must include: our setup (MViTv2-S, 4 tasks, metrics), the specific question, what we already know (cite V1 findings), and what evidence we need

---

### OPERATING PROTOCOL

**Phase 1 (Agents 1-5):** Data integrity — run sequentially (each depends on previous)
- Each agent reads the actual dataset files to compute statistics
- Use `python3` + `bash` for data analysis, `numpy` for statistics, `matplotlib` for histograms
- Agents 1-5 must CHECK the data, not just describe it

**Phase 2 (Agents 6-10):** Architecture limits — run in parallel (independent)
- Each agent uses `paper-search` MCP for literature + `python3` for code analysis
- Agent 6 and 7 should compare FLOPs/params by running the actual model

**Phase 3 (Agents 11-15):** Literature deep dive — run in parallel
- Primary tool: `paper-search` MCP (20+ sources)
- Secondary: `academic-search` (Google Scholar), Exa (cross-field)
- Each agent must verify every claim via the MCP before reporting

**Phase 4 (Agents 16-20):** Synthesis — run sequentially
- Agent 16+17: parallel (independent)
- Agent 18: depends on 16+17
- Agent 19: depends on 18
- Agent 20: depends on all previous

### OUTPUT DIRECTORY
All files go to:
`analyses/consult_claude_science/consult_v2/agent_outputs/`

### VERIFICATION
- Every paper claim must be verified via `paper-search` MCP or direct arXiv fetch
- Explicitly state confidence: HIGH (verified via multiple sources), MEDIUM (single source), LOW (extrapolated)
- For each MD file: include summary at top, detailed analysis in body, specific Claude Science queries at bottom
