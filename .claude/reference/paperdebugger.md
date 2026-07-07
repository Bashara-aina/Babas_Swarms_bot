# PaperDebugger — Academic Paper Review & Critique

## Overview

PaperDebugger is an AI-powered academic writing assistant focused on **review and critique** of LaTeX research papers. It provides reviewer-style analysis against top-tier ML conference standards, citation verification, literature search, and writing enhancement.

**Source:** https://github.com/PaperDebugger/paperdebugger  
**License:** AGPL v3.0  
**arXiv:** https://arxiv.org/abs/2512.02589  

## Integration in this project

This project hosts a local PaperDebugger MCP server that implements the XtraMCP tool interface from the PaperDebugger project. The Go backend and Chrome extension are not installed — only the MCP-level tools for paper review are included.

**MCP server:** `tools/mcpServers/paperdebugger_mcp/server.py`  
**Skill:** `/paperdebugger` at `.claude/skills/paperdebugger/SKILL.md`

## Tool Reference

### review_paper
Analyze a LaTeX paper against conference standards.
- **Pass A (deterministic):** Required sections, abstract quality, TODO/FIXME markers, figure references, citation count, code availability
- **Pass B (structural):** Section-level analysis
- **Returns:** Issues with severity (blocker/major/minor), category, and actionable suggestions

### verify_citations
Verify BibTeX entries against the arXiv API.
- Parses `.bib` file entries
- Checks each title against arXiv search
- Returns: verified/unverifiable/error per entry

### enhance_academic_writing
Rule-based prose polish that preserves all `\cite{}` positions.
- Reduces filler: "in order to" → "to", "due to the fact that" → "because", etc.
- Fixes sentence starts: "And" → "Moreover,", "But" → "However,"
- Passive → active: "it can be observed that" → "we observe that"
- Styles: concise, formal, clear, neurips

### search_relevant_papers
Search academic papers via the arXiv API.
- Sorts by relevance
- Returns title, authors, summary, published date, arXiv ID

### deep_research
Multi-step literature synthesis.
1. Searches for relevant papers on the topic
2. Compares against your draft (if `tex_path` provided)
3. Identifies key themes and suggests positioning

### read_section_source
Extract LaTeX section by title.
- Resolves `\input` and `\include` directives
- Returns section content with line numbers

### paper_score
Score paper on quality dimensions with percentile ranking.
- Dimensions: structure, clarity, reproducibility, citations
- Issue-weighted scoring: blocker (-20), major (-8), minor (-3)

## Comparison with PaperDebugger Upstream

| Feature | Upstream (XtraMCP) | Local MCP Server |
|---------|-------------------|------------------|
| Paper review | LLM-based sections (Pass B/C) | Structural/deterministic |
| Citation check | Full resolution | arXiv API lookup |
| Writing enhancement | XtraGPT models | Rule-based |
| Paper search | 800K local vector DB | arXiv API |
| Deep research | Multi-step with ranking | arXiv + synthesis |
| Custom endpoint | Go backend | Python stdio MCP |

The local implementation provides structural review, citation verification, and literature search without requiring the closed-source XtraMCP server or the Go backend.

## Original Project Architecture

The full PaperDebugger project includes:
- **Go backend** (Gin HTTP + gRPC) with MongoDB
- **Chrome extension** for Overleaf integration
- **XtraMCP** orchestration layer (closed-source at `4ndrelim/academic-paper-mcp-server`)
- **Custom MCP client** with streaming and tool registry (in `internal/services/toolkit/`)
- **LaTeX tooling** — section parser, file operations, string search
- **CI/CD** — GitHub Actions for extension and backend builds

## Related

- `/paper` skill — academic writing pipeline (paper-from-zero → writer → backfill → refine)
- `/paperops` skill — LaTeX DevOps (build, diff, archive)
- PaperOps template: `tools/paperops-template/`
