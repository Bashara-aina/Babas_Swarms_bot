# Ruflo — Claude Code Configuration

## Hard Rules
- Do what's asked; no extra files, docs, or tests in root
- Read before edit; never commit secrets/.env
- Keep files under 500 lines; validate input at boundaries
- **All agents: OpenCode Go via oc-cc-proxy only — no direct Anthropic/MiniMax API calls.**
- **NEVER use CronCreate or CronDelete — the user does not want scheduled tasks.**

## Swarm
- YES: 3+ files, new features, cross-module refactors, API, security, perf
- NO: single-file edits, 1-2 line fixes, docs, config, questions
- Topology: hierarchical-mesh (anti-drift), max 15 agents, HNSW + Neural enabled

## Build & Test
- After changes: `make check` (ruff lint + pytest) — Python project, no npm build needed

## GitNexus (required)
- **Before edit**: `gitnexus_impact({target, direction: "upstream"})` — warn on HIGH/CRITICAL
- **Before commit**: `gitnexus_detect_changes()` — verify scope
- **Rename**: `gitnexus_rename({dry_run: true})` only, never find-and-replace
- **Verify**: all modified symbols had impact run, d=1 dependents updated

## On-Demand Reference
- Model routing: `.claude/reference/model-routing.md`
- GitNexus: `.claude/reference/gitnexus-reference.md`
- Setup: `.claude/reference/setup.md`
- UI/UX: `.claude/reference/taste-router.md` + `ui-ux-excellence.md` (BOTH before UI work)
- Agent skills: `docs/agents/issue-tracker.md`, `triage-labels.md`, `domain.md`
- Full agent list: `.claude/agents/` (update count via `ls`)
- SearXNG: local metasearch MCP server at `tools/mcpServers/searxng_mcp/server.py`. Tools: `web_search` (metasearch), `search_and_crawl` (search + crawl4ai deep crawl). Service: `http://127.0.0.1:8888` (systemd: `searxng.service`). Config: `config/searxng/settings.yml`
- Crawl4AI: AI web crawler MCP server at `tools/mcpServers/crawl4ai_mcp/server.py`. Tools: `crawl4ai_crawl` (single URL → markdown), `crawl4ai_search` (batch crawl), `crawl4ai_facts` (fact verification). Installed: v0.9.0
- PaperOps: `tools/paperops-template/` — academic LaTeX DevOps template. Skill: `/paperops`. Reference: `.claude/reference/paperops.md`. Bootstrap: `scripts/paperops-bootstrap.sh`.
- Paper writing: `/paper` — AI-assisted academic writing pipeline (topic→PDF). Sub-skills at `.claude/skills/paper/sub-skills/`. Python scripts at `tools/latex-paper-skills/scripts/`. Reference: `.claude/reference/paper-skills/`. Showcase: `papers/showcase/`.
- PaperDebugger: `/paperdebugger` — LaTeX paper review and critique. MCP server at `tools/mcpServers/paperdebugger_mcp/server.py`. Skills at `.claude/skills/paperdebugger/`.
- PaperPal: `/paperpal` — academic paper search (arXiv, HuggingFace Papers, Semantic Scholar). MCP server at `tools/mcpServers/paperpal_mcp/server.py`. Skills at `.claude/skills/paperpal/`.
- ARIS: `/aris` — autonomous ML research pipeline. 79 sub-skills at `.claude/skills/aris/sub-skills/`. AGENT_GUIDE at `.claude/reference/aris/AGENT_GUIDE.md`. Tools at `tools/aris/`.
- GenAI Proofreader: `/genai-proofreader` — multi-persona LaTeX proofreading (Domain Expert + Language Expert). Source at `tools/genai-latex-proofreader/`. Prompts at `.claude/reference/genai-proofreader/`.
- ScholarCopilot: `/scholarcopilot` — citation-aware academic writing assistant (COLM 2025). Source at `tools/scholarcopilot/`. Reference: `.claude/reference/scholarcopilot.md`.
- Textidote: `/textidote` — LaTeX spelling, grammar and style linter (LanguageTool). MCP server at `tools/mcpServers/textidote_mcp/`. JAR at `tools/textidote/textidote.jar`.
- Scrapling: `/scrapling` — adaptive web scraping (HTTP/stealth/dynamic fetch, CSS/XPath parser, batch extraction). MCP tools: `scrapling_fetch`, `scrapling_stealth`, `scrapling_dynamic`, `scrapling_extract`, `scrapling_parse`, `scrapling_extract_multi`. Reference: `.claude/reference/scrapling.md`. Upstream: https://github.com/d4vinci/Scrapling (BSD-3-Clause, 67.9k stars).
- Jina Reader: `/jina-reader` — convert URLs to LLM-friendly markdown, web search via `s.jina.ai`. MCP tools: `jina_read`, `jina_search`, `jina_read_json`, `jina_batch`. Reference: `.claude/reference/jina-reader.md`. Upstream: https://github.com/jina-ai/reader (Apache-2.0).

## Superpowers SDLC Methodology
- Workflow: brainstorming -> writing-plans -> executing-plans (or subagent-driven-development) -> tdd -> requesting-code-review -> finishing-a-development-branch
- **Always check skills first** (listed in system reminders)
- **Subagent-driven-development**: for 2+ independent tasks, dispatch subagents with two-stage review. Templates at `.claude/skills/subagent-driven-development/`
- **Parallel dispatching**: for truly independent work, dispatch parallel agents per `dispatching-parallel-agents` skill
- Specs at `.superpowers/specs/`, plans at `.superpowers/plans/`, SDD ledger at `.superpowers/sdd/progress.md`
- Before editing: read first, check gitnexus_impact, ensure requirements are clear
- Active at session start via `superpowers_bootstrap` (auto-injected)

## Karpathy Principles (Plugin: andrej-karpathy-skills@karpathy-skills)
### Think Before Coding
State assumptions, surface tradeoffs, push back when warranted, stop when unclear.

### Simplicity First
No features beyond what's asked, no abstractions for single-use, match "would a senior engineer say this is overcomplicated?"

### Surgical Changes
Touch only what you must. Every changed line traces to your request. Remove only orphans your changes created.

### Goal-Driven Execution
Transform tasks into verifiable goals with success criteria. Loop until tests pass.

### Fable 5 — Autonomous Mode (Active: FABLE5_AUTONOMOUS=1)
- **Outcome-first**: Lead with result, not process. Write for a teammate who stepped away.
- **Act, don't ask**: Never "shall I", "want me to", "may I", "should I" — just do reversible work.
- **No plans, no promises**: If the last paragraph is a plan or next-step list, execute it now.
- **No hedging**: State findings plainly. No "I think", "it seems", "probably". When done, say so.
- **No narrating routing**: Do not explain tool choices or say "per my guidelines". Select and produce.
- **Context persistence**: Keep working through compaction. Do not re-derive or re-litigate.
- **Evidence check before system changes**: Verify cause before restart, delete, or config edit.
- **Readable over concise**: Complete sentences, plain language. Drop details the reader does not need.
- **File at `.claude/reference/fable5-behavior.md`** for full reference (load on demand)

## ECC Native Integration (affaan-m/ecc v2.1)
- **Continuous learning**: instincts auto-consolidate from observations at PreCompact
  - Commands: `/instinct-status`, `/evolve`, `/instinct-export`, `/instinct-import`, `/promote`, `/projects`
  - Storage: `.superpowers/homunculus/instincts/` (project) + `$XDG_DATA_HOME/ecc-homunculus/` (global)
- **Config protection**: edits to linter/formatter configs (pyproject.toml, ruff.toml, etc.) are blocked — fix code, not rules
- **Context monitor**: tracks tool call rate, warns on high frequency (strict profile)
- **Cost tracker**: records session metrics to `.superpowers/metrics/cost-log.jsonl`
- **Quality gate**: (strict profile) checks file sizes and lint after edits
- **Identity**: `.claude/identity.json` — project profile for tool selection
- **Reference patterns**: root-cause-tracing, defense-in-depth, condition-based-waiting, testing-anti-patterns, visual-companion in `.claude/reference/`
- **Profile**: set `HOOK_PROFILE=minimal|standard|strict` to control hook aggressiveness

## graphify
- For codebase Qs: `graphify query "<question>"` if `graphify-out/graph.json` exists
- After coding: `graphify update .` to keep graph current

## Cognee (L7 Knowledge Graph Memory)
- **Cognee** provides knowledge-graph-backed memory (L7) layered on top of L1-L6
- MCP server at `.claude-flow/mcp/cognee-mcp-server.py` — tools: `cognee_remember`, `cognee_recall`, `cognee_status`, `cognee_sync`, `cognee_forget`
- Bridge at `.claude/helpers/cognee-bridge.mjs` — auto-syncs memory at session boundaries
- Uses oc-cc-proxy (`deepseek-v4-flash`), LanceDB vector store in `data/cognee/`
- First call initializes DBs; subsequent calls are faster

## PaperOps (Academic LaTeX DevOps)
- Template at `tools/paperops-template/` — Makefile-driven LaTeX with bib formatting, diff reports, archive generation
- **Bootstrap**: `scripts/paperops-bootstrap.sh <target-dir>` (copies template + runs `make config`)
- **Commands**: `make` (build), `make draft` (draft mode), `make bib-fmt` (format bib), `make main-diff-<COMMIT>.pdf` (diff), `make archive`/`make archive-safe` (archives), `make clean`
- **Overleaf support**: generates `nourl` bib/tex variants automatically
- **Skill**: `/paperops` for interactive use
- **Reference**: `.claude/reference/paperops.md`

## Paper Writing (AI-Assisted Academic Pipeline)
- Skill: `/paper` — topic-to-PDF pipeline with literature search, innovation framing, issues-driven writing, results backfill, prose refinement
- Pipeline: `paper-from-zero` (route) → `arxiv-paper-writer` or `empirical-paper-writer` → `results-backfill` → `latex-rhythm-refiner`
- **Non-negotiable**: No prose before plan approval. Issues CSV is the work contract. Citations must be verified against online sources. Never fabricate.
- Python scripts in `tools/latex-paper-skills/scripts/` — citation audit, LaTeX compilation, issue workflow, arXiv BibTeX registry, source ranking
- Templates: `tools/latex-paper-skills/assets/template/` (IEEEtran class, main.tex, ref.bib)
- Sub-skill references: `.claude/skills/paper/sub-skills/` (8 original SKILL.md files)
- Reference docs: `.claude/reference/paper-skills/` (writing style, bibtex guide, citation workflow, experiment design, etc.)
- Showcase projects: `papers/showcase/` (PEFT survey, RT inflow forecast — built with GPT-5.2)

## PaperDebugger (Academic Paper Review & Critique)
- Skill: `/paperdebugger` — LaTeX paper review against conference standards (NeurIPS/ICML/ICLR). MCP server at `tools/mcpServers/paperdebugger_mcp/server.py`
- **Tools**: `review_paper` (structural + style review), `verify_citations` (BibTeX online check), `enhance_academic_writing` (prose polish, preserves `\cite`), `search_relevant_papers` (arXiv API), `deep_research` (literature synthesis), `read_section_source` (section-by-section), `paper_score` (quality scoring with percentile), `generate_citations` (BibTeX lookup)
- **Workflow**: review → verify citations → enhance writing → re-score
- **Rules**: Never fabricate citations. Blocker/major/minor severity. Read-only — never modify without approval.

## PaperPal (Academic Paper Search & Discovery)
- Skill: `/paperpal` — search papers across arXiv, HuggingFace Papers, Semantic Scholar. MCP server at `tools/mcpServers/paperpal_mcp/server.py`
- **Tools**: `search_arxiv_papers` (arXiv API search), `fetch_paper_details_from_arxiv` (BibTeX + details), `semantic_search_papers_on_huggingface` (trending/community ML papers), `search_semantic_scholar` (citation-aware search with TLDR)
- **Upstream**: MIT License, by jerpint @ Mila Quebec AI Institute
- **Integration**: Use for literature search before `/paper` writing pipeline, and to supplement citations during `/paperdebugger` review

## ARIS (Auto-Research-In-Sleep)
- Skill: `/aris` — autonomous ML research framework (12.7k stars, 79 skills). Upstream: https://github.com/wanshuiyin/auto-claude-code-research-in-sleep (MIT, v0.4.20)
- **Key skills**: `research-pipeline` (end-to-end), `idea-discovery`/`idea-creator` (ideas), `paper-write`/`paper-plan` (writing), `auto-review-loop`/`research-review` (review), `experiment-plan`/`analyze-results` (experiments), `rebuttal`/`paper-slides`/`paper-figure` (presentation), `citation-audit` (citations), `proof-checker`/`formula-derivation` (math), `patent-pipeline` (patents)
- **Parameters**: `— effort: lite|balanced|max|beast`, `— assurance: draft|polished|conference-ready|submission`, `— venue`, `— reviewer`, `— gpu`, `— difficulty`
- **Shared references**: 28 contracts at `.claude/reference/aris/` (assurance, effort, citation discipline, venue checklists, governance)
- **Python tools**: 12 scripts at `tools/aris/` (arxiv/deepxiv/semantic-scholar/openalex fetchers, evidence check, threat scan, provenance tracking)
- **Full skill catalog**: `.claude/skills/aris/sub-skills/` (79 .md files). Canonical routing: `.claude/reference/aris/AGENT_GUIDE.md`
- **Integration**: Complements `/paper` (writing) with autonomous research pipeline; `/paperdebugger` (review) with adversarial multi-model review; `/paperpal` (search) with deepxiv/openalex/exa sources; `/paperops` (build) with paper compilation/git operations

## GenAI Proofreader (Multi-Persona LaTeX Proofreading)
- Skill: `/genai-proofreader` — persona-based LaTeX proofreading (Domain Expert + Language Expert). Source: `tools/genai-latex-proofreader/` (MIT, by matiasdahl)
- **Two personas**: Domain Expert (correctness, clarity, motivation, completeness) and Language Expert (grammar, spelling, punctuation, consistency, flow)
- **Section-by-section**: Each section proofread independently with full-paper context. LaTeX-aware feedback with `\ref{}` and valid LaTeX output.
- **LaTeX Guard**: AI-generated feedback auto-compiled and auto-fixed if LaTeX errors are introduced
- **Prompts at**: `.claude/reference/genai-proofreader/` (domain_expert_prompts.py, language_expert_prompts.py, latex_guard.py, formatting.py)
- **Run**: `cd tools/genai-latex-proofreader && pip install -r requirements.txt && export ANTHROPIC_API_KEY=... && python3 -m genai_latex_proofreader.cli --input_latex_path paper.tex --output_report_filepath output/report.tex`
- **Integration**: Complements `/paperdebugger` (structural checklist review) with full-text persona-grounded critique. Use both before submission.

## ScholarCopilot (Citation-Aware Academic Writing)
- Skill: `/scholarcopilot` — unified LLM for citation-aware academic writing (COLM 2025, TIGER-Lab). Source: `tools/scholarcopilot/`
- **Architecture**: Dynamic citation token switching — model generates text until `<|cite_start|>` token, uses hidden state to retrieve papers from FAISS index, injects reference, resumes generation
- **Six special tokens**: `<|paper_start|>`, `<|paper_end|>`, `<|cite_start|>`, `<|cite_end|>`, `<|reference_start|>`, `<|reference_end|>` — trained on full arXiv papers
- **Two modes**: "Complete 3 sentences" and "Generate to the end"
- **Files**: `run_demo/scholar_copilot_model.py` (inference), `train/src/arxivllm.py` (model arch), `utils/process_arxiv_meta_data.py` (arXiv→corpus), `utils/build_hnsw_index.py` (FAISS index)
- **Model**: 7B LLM + LoRA, trained with contrastive + generation loss on 32 GPUs
- **Integration**: Use citation-aware pattern (pause → retrieve real papers via /paperpal → inject → resume)

## Textidote (LaTeX Linter)
- Skill: `/textidote` — automated LaTeX spelling, grammar and style checking via LanguageTool. Upstream: https://github.com/sylvainhalle/textidote (GPL-3.0, 1048 stars, by Sylvain Hallé)
- **MCP tools**: `lint_latex` (full lint: grammar + LaTeX-specific rules), `check_grammar` (plain text), `clean_latex` (strip markup)
- **JAR**: `tools/textidote/textidote.jar` (215 MB, requires Java 8+). Wrapper: `tools/textidote/textidote.sh`
- **Rule categories**: Capitalization (sh:0xx), Punctuation & citations (sh:c:0xx), Structure (sh:1xx), Spacing (sh:s:0xx), Formatting (sh:f:0xx), Labels (sh:r:0xx), LanguageTool grammar/spelling (LT:*)
- **Usage**: `/textidote lint: paper.tex — language: en` or direct CLI `textidote.sh --check en --output singleline paper.tex`
- **Integration**: Run as first automated pass (fast, rule-based) before `/paperdebugger` structural review and `/genai-proofreader` persona critique
