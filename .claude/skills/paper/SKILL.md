---
name: paper
description: "AI-assisted academic paper writing pipeline — from topic to compiled PDF. Covers literature search, innovation framing, issues-driven writing with verified citations, experiment scaffold, results backfill, and prose refinement. Routes between review papers (IEEEtran) and empirical papers (with experiment matrices)."
trigger: /paper
---

# /paper

Write ML/AI academic papers with a gated, issues-driven workflow. From topic to compiled PDF with verified BibTeX citations.

## Pipeline stages

```
paper-from-zero  ─►  arxiv-paper-writer or empirical-paper-writer  ─►  results-backfill  ─►  latex-rhythm-refiner
     │                       │                                              │                      │
     └─ topic framing       └─ issues-driven writing                      └─ fill real results   └─ prose polish
     └─ literature search   └─ citation verification                       └─ resolve placeholders
     └─ contribution map    └─ LaTeX compilation
     └─ route decision
```

## Quick start

### Full pipeline (topic → PDF)

```
/paper from topic: <your topic>
```

### Direct review paper

```
/paper review: <topic>
```

### Direct empirical paper

```
/paper empirical: <topic>
```

### With dataset and cloud budget

```
/paper empirical: <topic>
  Datasets: <Dataset A>, <Dataset B>
  Compute: single A100 80GB, max 8 hours
  Need local smoke test first, then full cloud run
```

### Prose polish only

```
/paper refine: paper/main.tex
```

### Backfill results only

```
/paper backfill: papers/my-paper/
```

## Sub-skill reference

Full original skill files in `.claude/skills/paper/sub-skills/`. Python scripts in `tools/latex-paper-skills/scripts/`.

| Sub-skill | When to invoke |
|-----------|---------------|
| `paper-from-zero` | Topic is known, structure and contribution are not pinned down. Literature search + innovation framing + route to writer. |
| `arxiv-paper-writer` | Review/survey paper. Gated IEEEtran workflow with issues CSV, per-issue writing loop, citation verification, QA. |
| `empirical-paper-writer` | Experimental paper. Extends review with experiment matrices, result status tracking, evidence-claim mapping. |
| `results-backfill` | Back-fill real experiment results into existing draft. Resolve placeholders, upgrade hypotheses, generate figures. |
| `latex-rhythm-refiner` | Prose polisher. Vary sentence/paragraph rhythm, remove filler, preserve all `\cite{}` positions. |

## Non-negotiable rules

- **No prose before approval** — `main.tex` stays skeleton until the plan is approved and the issues CSV exists.
- **Issues CSV is the contract** — update status per issue; only mark DONE when acceptance criteria are met.
- **Citations must be verified** — every citation is checked against an online source before entering `ref.bib`.
- **Never fabricate** citations, results, or significance claims.
- **Collaboration hooks**: Gemini for breadth (literature expansion, alternative framings), Claude for depth (stress-testing, evidence audit).

## Directory structure (created per project)

```
papers/<project-name>/
├── main.tex                # Root document (skeleton until plan-approved)
├── ref.bib                 # Verified BibTeX entries
├── paper.config.yaml       # Venue, style, author config
├── plan/                   # Plans, contracts, routing decisions
├── issues/                 # Issues CSV (the work contract)
├── notes/                  # Literature notes, innovation logs
├── experiments/            # Experiment code, configs, results
├── results/                # Result CSVs, tables, figures
└── Makefile                # LaTeX build targets
```

## Related

- **paperops** `/paperops` — LaTeX DevOps template (Makefile, build, diff, archive). Use for actual LaTeX compilation once the paper is drafted.
- Reference docs: `.claude/reference/paper-skills/`
- Showcase projects: `papers/showcase/`
