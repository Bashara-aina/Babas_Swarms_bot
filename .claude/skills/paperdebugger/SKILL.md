---
name: paperdebugger
description: "AI-powered LaTeX paper review and critique — reviewer-style analysis, citation verification, literature search, and writing enhancement. Use when the user wants a conference-level review of their draft, citation audit, paper search, or prose polishing. Complements the /paper (writing pipeline) and /paperops (build/format) skills."
trigger: /paperdebugger
---

# /paperdebugger

Review, critique, and improve LaTeX research papers using reviewer-style analysis. Powered by the PaperDebugger MCP server.

## Tools

All tools are available via the `paperdebugger-mcp` MCP server (`tools/mcpServers/paperdebugger_mcp/server.py`):

| Tool | What it does |
|------|-------------|
| `review_paper` | Full paper review against top-tier ML conference standards (NeurIPS/ICML/ICLR). Deterministic checks (structure, sections, TODOs) + style analysis. Returns issues with severity, category, and actionable suggestions. |
| `verify_citations` | Verify BibTeX entries against online sources (arXiv API). Flags unverifiable, missing, or potentially hallucinated citations. |
| `generate_citations` | Look up BibTeX entries by arXiv ID, DOI, URL, or paper title. |
| `enhance_academic_writing` | Polish LaTeX prose — remove filler, fix passive voice, improve rhythm. Preserves all `\cite{}` positions. |
| `search_relevant_papers` | Search academic literature (arXiv API) by topic, keywords, or concepts. |
| `deep_research` | Multi-step literature synthesis: search papers, compare to your draft, surface gaps and positioning insights. |
| `read_section_source` | Extract a specific section's LaTeX source by title, resolving `\input` directives. |
| `paper_score` | Score a paper on quality dimensions (structure, clarity, reproducibility, citations) with percentile ranking. |

## Workflows

### Full review workflow

1. `read_section_source` for each major section to understand content
2. `review_paper` on the main .tex file for structural analysis
3. `verify_citations` on the .bib file for citation integrity
4. Address blocker/major issues
5. `enhance_academic_writing` on critical paragraphs
6. Re-run `paper_score` to track improvement

### Citation audit

```
verify_citations with bib_path: papers/my-paper/ref.bib
```

### Literature positioning

```
deep_research with topic: "<your contribution>" and tex_path: papers/my-paper/main.tex
```

### Prose polish

```
enhance_academic_writing with text: "<paragraph>" and style: "concise"
```

## Integration with other skills

- `/paper` — academic writing pipeline (paper-from-zero → writer → backfill → refine). Use PaperDebugger for **review/QA** during and after the writing process.
- `/paperops` — LaTeX DevOps (build, format, diff, archive). Use for compilation after PaperDebugger review is complete.

## Non-negotiable rules (from PaperDebugger)

- **Never fabricate** citations, results, or significance claims — always verify.
- Issues are tagged as `blocker` (must fix), `major` (should fix), or `minor` (nice to fix).
- Reviewer-style critique means identifying what's missing, not rewriting content.
- The agent reads and suggests — it never modifies the paper directly without user approval.
