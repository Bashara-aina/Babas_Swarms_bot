---
name: aris
description: "ARIS (Auto-Research-In-Sleep) — autonomous ML research framework with cross-model review, adversarial audit, experiment automation, and paper writing. Use for end-to-end research pipelines, idea discovery, literature review, paper writing with multi-model review, experiment planning, patent writing, rebuttals, and more. Complements /paper (writing pipeline), /paperdebugger (review), and /paperpal (search)."
trigger: /aris
---

# /aris

ARIS ⚔️ is an autonomous ML research harness: composable skills that orchestrate the research lifecycle through cross-model adversarial collaboration. Source: https://github.com/wanshuiyin/auto-claude-code-research-in-sleep (MIT, 12.7k stars).

## Quick Start

```
/aris pipeline "topic" — effort: balanced, assurance: conference-ready
/aris ideas "challenging problem in <domain>" — effort: beast
/aris write "paper on <topic>" — venue: ICLR
/aris review "paper/main.tex" — reviewer: manual
/aris experiment "method description" — gpu: local
/aris rebuttal "reviewer comments"
```

## Skill Catalog (79 skills)

All skills are installed as sub-skills at `.claude/skills/aris/sub-skills/`. The `AGENT_GUIDE.md` at `.claude/reference/aris/AGENT_GUIDE.md` is the canonical routing index with full parameter specs for every skill.

### Main Research Pipeline

| Skill | File | What it does |
|-------|------|-------------|
| `research-pipeline` | `sub-skills/research-pipeline.md` | End-to-end W1→W3 pipeline: discover → lit review → idea → paper |
| `research-lit` | `sub-skills/research-lit.md` | Deep literature review with multi-source search |
| `idea-discovery` | `sub-skills/idea-discovery.md` | Structured research idea generation with gap analysis |
| `idea-creator` | `sub-skills/idea-creator.md` | Focused idea creation from seed concepts |
| `novelty-check` | `sub-skills/novelty-check.md` | Verify idea novelty against existing literature |

### Paper Writing & Refinement

| Skill | File | What it does |
|-------|------|-------------|
| `paper-plan` | `sub-skills/paper-plan.md` | Paper outline and story construction |
| `paper-write` | `sub-skills/paper-write.md` | Full paper draft from plan |
| `research-refine` | `sub-skills/research-refine.md` | Iterative paper refinement |
| `auto-paper-improvement-loop` | `sub-skills/auto-paper-improvement-loop.md` | Autonomous improvement with review loop |
| `citation-audit` | `sub-skills/citation-audit.md` | Deep citation verification and formatting |
| `claims-drafting` | `sub-skills/claims-drafting.md` | Evidence-to-claim conversion |

### Cross-Model Review

| Skill | File | What it does |
|-------|------|-------------|
| `auto-review-loop` | `sub-skills/auto-review-loop.md` | Cross-model adversarial review (executor + reviewer) |
| `research-review` | `sub-skills/research-review.md` | Full research output review |
| `experiment-audit` | `sub-skills/experiment-audit.md` | Experiment design and result audit |

### Experiments

| Skill | File | What it does |
|-------|------|-------------|
| `experiment-plan` | `sub-skills/experiment-plan.md` | Experiment design with compute budget |
| `analyze-results` | `sub-skills/analyze-results.md` | Result analysis and visualization |
| `ablation-planner` | `sub-skills/ablation-planner.md` | Ablation study planning |
| `result-to-claim` | `sub-skills/result-to-claim.md` | Experimental results → paper claims |

### Presentation & Communication

| Skill | File | What it does |
|-------|------|-------------|
| `paper-slides` | `sub-skills/paper-slides.md` | Conference presentation slides |
| `paper-poster` | `sub-skills/paper-poster.md` | Research poster generation |
| `paper-talk` | `sub-skills/paper-talk.md` | Talk script/storyboarding |
| `paper-figure` | `sub-skills/paper-figure.md` | Figure design and specification |
| `rebuttal` | `sub-skills/rebuttal.md` | Reviewer rebuttal letter |
| `grant-proposal` | `sub-skills/grant-proposal.md` | Research grant writing |

### Specialized

| Skill | File | What it does |
|-------|------|-------------|
| `formula-derivation` | `sub-skills/formula-derivation.md` | Mathematical formula derivation |
| `proof-checker` | `sub-skills/proof-checker.md` | Theorem/proof correctness checking |
| `proof-writer` | `sub-skills/proof-writer.md` | Theorem/proof writing |
| `patent-pipeline` | `sub-skills/patent-pipeline.md` | End-to-end patent drafting |
| `invention-structuring` | `sub-skills/invention-structuring.md` | Patent invention disclosure |
| `mermaid-diagram` | `sub-skills/mermaid-diagram.md` | Mermaid diagram generation |
| `render-html` | `sub-skills/render-html.md` | HTML paper/blog rendering |
| `interview-cheatsheet` | `sub-skills/interview-cheatsheet.md` | ML interview preparation |

### Infrastructure

| Skill | File | What it does |
|-------|------|-------------|
| `run-experiment` | `sub-skills/run-experiment.md` | Execute experiment code |
| `monitor-experiment` | `sub-skills/monitor-experiment.md` | Experiment monitoring |
| `experiment-queue` | `sub-skills/experiment-queue.md` | Experiment batch queue |
| `serverless-modal` | `sub-skills/serverless-modal.md` | Modal serverless deployment |
| `vast-gpu` | `sub-skills/vast-gpu.md` | Vast.ai GPU provisioning |
| `overleaf-sync` | `sub-skills/overleaf-sync.md` | Overleaf project sync |
| `feishu-notify` | `sub-skills/feishu-notify.md` | Feishu/Lark notification |

### Search & Knowledge

| Skill | File | What it does |
|-------|------|-------------|
| `arxiv` | `sub-skills/arxiv.md` | arXiv paper search |
| `deepxiv` | `sub-skills/deepxiv.md` | Deep arXiv search with full-text |
| `semantic-scholar` | `sub-skills/semantic-scholar.md` | Semantic Scholar search |
| `openalex` | `sub-skills/openalex.md` | OpenAlex open scholarly search |
| `exa-search` | `sub-skills/exa-search.md` | Exa web search for research |
| `research-wiki` | `sub-skills/research-wiki.md` | Persistent research wiki |
| `comm-lit-review` | `sub-skills/comm-lit-review.md` | Community literature review |

## Common Parameters

All ARIS skills accept:

```
— effort: lite | balanced | max | beast        # depth/budget (default: balanced)
— assurance: draft | polished | conference-ready | submission  # audit strictness
— human checkpoint: true | false              # pause for approval
— AUTO_PROCEED: true | false                  # auto-continue at gates
— difficulty: medium | hard | nightmare       # reviewer adversarial level
— venue: ICLR | NeurIPS | ICML | CVPR | ...   # target venue
— gpu: local | remote | vast | modal           # GPU backend
— reviewer: codex | oracle-pro | manual        # reviewer routing
```

## Source of Truth

- **`AGENT_GUIDE.md`** at `.claude/reference/aris/AGENT_GUIDE.md` — canonical routing index
- **`SKILLS_CATALOG.md`** at `.claude/reference/aris/SKILLS_CATALOG.md` — full 79-skill catalog
- **Individual skill specs** at `.claude/skills/aris/sub-skills/<name>.md`
- **Shared references** at `.claude/reference/aris/*.md` (28 contracts: acceptance gates, assurance levels, citation discipline, effort contracts, venue checklists, etc.)
- **Python tools** at `tools/aris/` (12 scripts: arxiv/deepxiv/semantic-scholar fetchers, evidence check, provenance, threat scan, etc.)
- **Upstream repo**: https://github.com/wanshuiyin/auto-claude-code-research-in-sleep (v0.4.20)

## Integration with paper stack

ARIS fills the **end-to-end autonomous research pipeline** role. The full paper workflow:

| Phase | Tool | Role |
|-------|------|------|
| **Discover** | `/aris ideas` / `/aris pipeline` | Generate research ideas, gap analysis |
| **Search** | `/paperpal` | Literature search (arXiv, HF, S2) |
| **Plan** | `/aris paper-plan` | Outline and story construction |
| **Write** | `/aris paper-write` | Full paper draft with auto-review |
| **Review** | `/paperdebugger` | Structural review, citation verification |
| **Refine** | `/aris research-refine` | Iterative improvement |
| **Build** | `/paperops` | LaTeX compilation, diff, archive |
| **Present** | `/aris paper-slides` / `/aris rebuttal` | Slides, poster, rebuttal |
