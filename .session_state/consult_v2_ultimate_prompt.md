# ULTIMATE CONSULTATION V2 — 20 MD FILES → DEEP RESEARCH → ADVERSAIRAL DEBATE → FINAL SYNTHESIS

## ABSOLUTE FINAL CONSULTATION FOR INDUSTREAL AAIML 2027

### CONTEXT
20 deep-analysis MD files are in `consult_v2/agent_outputs/`. Each covers a critical aspect of our MTL project targeting AAIML 2027. NOW each must be:
1. **RESEARCHED** — use ALL tools to verify every claim, find counter-evidence, discover new papers
2. **DEBATED** — adversarial agents challenge every recommendation
3. **SYNTHESIZED** — final verified recommendations ranked by impact

**There is NO other input. Only these 20 files. Do not load V1 docs.**

---

### INPUT: ONLY THESE 20 FILES

ALL input is in this single directory:
`analyses/consult_claude_science/consult_v2/agent_outputs/`

Load ALL 20 files:
1. `agent01_data_audit.md`
2. `agent02_val_analysis.md`
3. `agent03_detection_data.md`
4. `agent04_activity_psr_data.md`
5. `agent05_pose_temporal.md`
6. `agent06_backbone_capacity.md`
7. `agent07_neck_design.md`
8. `agent08_task_heads.md`
9. `agent09_training_pipeline.md`
10. `agent10_efficiency.md`
11. `agent11_detection_mtl_lit.md`
12. `agent12_activity_mtl_lit.md`
13. `agent13_psr_temporal_lit.md`
14. `agent14_pose_regression_lit.md`
15. `agent15_training_stability_lit.md`
16. `agent16_paper_strategy.md`
17. `agent17_competitor_landscape.md`
18. `agent18_final_roadmap.md`
19. `agent19_risk_contingency.md`
20. `agent20_synthesis.md`

**NO OTHER FILES FROM V1 ARE NEEDED.** The 20 agent_outputs contain all context.

---

## THREE-PHASE RESEARCH + DEBATE ARCHITECTURE

### PHASE 1 — DEEP RESEARCH (10 specialized research agents)

Each agent:
1. Reads its assigned MD file(s)
2. Uses ALL tools to verify, expand, challenge every claim:
   - `paper-search` MCP: arXiv, PubMed, bioRxiv, Semantic Scholar — PRIMARY literature source
   - `academic-search` MCP: Google Scholar — coverage intersection
   - `Exa`: cross-field search (robotics, autonomous driving, surgical, egocentric)
   - `crawl4ai`: open-access PDF extraction for methodology verification
   - `Jina Reader`: PDF-to-markdown for detail extraction
   - `sequential-thinking`: structured reasoning
3. For each claimed paper: verifies arXiv ID, title, venue, year, metrics
4. For each claimed metric: finds the exact table/figure in the original paper
5. For each recommendation: searches for counter-evidence

**Agent R1 — Data Research** (covers agent01-05)
- Verifies every data statistic against the actual dataset files
- For each: is the class distribution correct? Are the statistics reproducible?
- Use: `python3` to recompute statistics from raw data
- Output: `R1_DATA_VERIFIED.md`

**Agent R2 — Architecture Research** (covers agent06-10)
- Verifies every architecture claim against published papers
- For backbone MViTv2-S: find exact published FLOPs/params/accuracy
- For TSBN: find the original paper, verify +2-4 AP claim
- For each architecture recommendation: verify with paper-search MCP
- Output: `R2_ARCHITECTURE_VERIFIED.md`

**Agent R3 — Literature Research** (covers agent11-15)
- For every cited paper in all 5 literature files:
  1. Fetch via `paper-search` MCP or direct arXiv API
  2. Verify: title, year, venue, authors match
  3. Verify: claimed metrics match the actual paper
  4. Flag any hallucinated or inaccurate claims
  5. Search for NEWER papers (2025-2026) that supersede cited works
- Use: `paper-search` MCP (all 20+ sources), `academic-search`, Exa, `crawl4ai`, Jina Reader
- Output: `R3_LITERATURE_VERIFIED.md`

**Agent R4 — Strategy Research** (covers agent16-20)
- Verifies AAIML-specific claims: venue requirements, submission deadlines, paper length
- Searches for AAIML 2027 accepted papers (CFP, topics, reviewers)
- Finds published AAIML papers on similar topics for benchmarking
- Verifies competitor landscape claims
- Output: `R4_STRATEGY_VERIFIED.md`

**Agent R5 — Reference Implementation Alignment** (NEW — critical)
- Compares every code change recommendation against the actual reference implementation
- For each: does the IndustReal reference code (`datasets/industreal_github/`) support this approach?
- Specifically check:
  - PSR: does the author's PSR baseline match our approach? Do they achieve non-zero F1?
  - AR: does the author's action recognition setup match our activity head?
  - ASD: does the author's assembly state detection match our detection head?
- Use: Read `industreal_github/PSR/psr_baseline.py`, `AR/industreal.py`, `ASD/train.py`
- Output: `R5_REFERENCE_ALIGNMENT.md`

---

### PHASE 2 — ADVERSARIAL DEBATE (10 specialized debaters)

Each debater challenges the findings from Phase 1. They search SPECIFICALLY for counter-evidence.

**Debater D1:** Challenge Data Research
- "Are the data statistics actually correct? Recompute with different methods."
- "Is the class distribution truly the bottleneck, or is it the model?"
- "Would different data splits produce different conclusions?"

**Debater D2:** Challenge Architecture Research
- "Is MViTv2-S really insufficient, or is our training suboptimal?"
- "Would TSBN actually work, or is it overfitted to specific benchmarks?"
- "Is the efficiency analysis correct? Profile with different batch sizes."

**Debater D3:** Challenge Literature Research
- "Are all cited papers REAL? Verify every arXiv ID manually."
- "Do the claimed numbers match the actual paper tables?"
- "Are there NEWER papers (2026) that contradict these findings?"
- Use: `paper-search` MCP + direct arXiv API for verification

**Debater D4:** Challenge Strategy Research
- "Is the AAIML paper narrative actually novel enough?"
- "Are there published papers at AAIML 2025-2026 that already cover this ground?"
- "Is the competitor landscape accurate? Search for missing competitors."

**Debater D5:** Challenge Reference Alignment
- "Does the author's code actually do what we think it does?"
- "Are we misinterpreting the reference implementation?"
- "Would the author recommend a different approach?"

**Debater D6 — Data:** Challenge every data finding from agents 01-05
- For each claim about class imbalance: find counter-examples where similar imbalance was handled differently
- For each claim about annotation quality: find published methods that work WITH noisy annotations

**Debater D7 — Architecture:** Challenge every architecture recommendation from agents 06-10
- For backbone swap recommendation: find papers where a SMALLER backbone outperformed larger
- For TSBN/neck change: find papers where shared BN was BETTER than task-specific
- For each: "Is the expected improvement justified by the evidence?"

**Debater D8 — Literature:** Challenge every literature finding from agents 11-15
- For each method recommended: find failure cases, limitations, unreproducible results
- For each gap claimed: find papers that actually DO address this gap
- "Is the literature search comprehensive or cherry-picked?"

**Debater D9 — Strategy:** Challenge every strategy recommendation from agents 16-20
- "Is the paper positioning defensible?" Search for prior art that could invalidate our novelty claim
- "Is the roadmap realistic?" Challenge the time/cost estimates

**Debater D10 — Synthesis:** Challenge EVERYTHING
- Cross-check: do recommendations from different agents contradict each other?
- Check: are there recommendations that work against each other? (e.g., training recipe change that breaks architecture change)
- Produce: contradiction map

---

### PHASE 3 — FINAL SYNTHESIS (5 synthesizers)

**Synthesizer S1:** Verified Findings
- Compile ALL verified findings from Phase 1 + challenged findings from Phase 2
- For each: evidence strength (HIGH/MEDIUM/LOW), verification sources, challenge outcome
- Flag: which findings survived debate, which were refuted, which need more evidence
- Output: `FINAL_VERIFIED_FINDINGS.md`

**Synthesizer S2:** Ranked Recommendations
- From all surviving findings: rank by IMPACT_ON_AAIML_ACCEPTANCE / IMPLEMENTATION_COST
- For each: summary, evidence, implementation steps, compute cost, risk level
- Top 10: must implement for AAIML submission
- Next 10: implement if time/compute permits
- Rejected: with evidence
- Output: `FINAL_RANKED_RECOMMENDATIONS.md`

**Synthesizer S3:** Complete Implementation Plan
- Day-by-day plan from now until AAIML submission
- Each day: what to implement, which GPU to use, expected duration
- Decision gates: at what points do we pivot based on results?
- For each gate: what specific metric determines the decision?
- Output: `FINAL_IMPLEMENTATION_PLAN.md`

**Synthesizer S4:** AAIML Paper Framework
- Paper title, abstract, contribution statements
- Method section outline (with citations)
- Experiment section outline (with ablation design)
- Expected results table (with target numbers)
- Output: `FINAL_PAPER_FRAMEWORK.md`

**Synthesizer S5:** Claude Science Query Pack
- 20 targeted queries for the final Claude Science session
- Each query: full context (our setup, current baseline, goal), specific question, expected answer format
- Organized by: data, architecture, training, literature, strategy
- Output: `FINAL_CLAUDE_SCIENCE_QUERIES.md`

---

### OUTPUT DIRECTORY
All outputs to: `analyses/consult_claude_science/consult_v2/` 
Phase 1+2+3 outputs all go here with descriptive names.

### VERIFICATION PROTOCOL (REQUIRED)
1. Every paper claim: verify via `paper-search` MCP or direct arXiv fetch — tag with confidence
2. Every metric: find the exact table/figure in the original paper — cite page/table number
3. Every data statistic: recompute with `python3` on actual files
4. Every code claim: verify against actual reference implementation files
5. Every debate challenge: must cite specific evidence (paper, table, line number)

### TOOLS
- `paper-search` MCP — arXiv, PubMed, bioRxiv, Semantic Scholar, 20+ sources
- `academic-search` MCP — Google Scholar
- `Exa` — cross-field discovery
- `crawl4ai` — open-access PDF extraction
- `Jina Reader` — PDF-to-markdown
- `Bash` + `python3` — data analysis, code verification
- `Read` — code and file inspection
- `sequential-thinking` — structured reasoning
- `Task` — sub-agent spawning for parallel work
- `hermes` — sub-agent for specialized research
