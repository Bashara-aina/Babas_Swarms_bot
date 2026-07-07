# PaperPal — Academic Paper Search & Discovery

## Overview

PaperPal provides unified MCP-based access to three academic paper sources: arXiv, HuggingFace Papers, and Semantic Scholar. Originally developed at Mila Quebec AI Institute.

**Source:** https://github.com/mila-iqia/paperpal  
**License:** MIT  
**Upstream Author:** jerpint (Mila)

## Server

**Location:** `tools/mcpServers/paperpal_mcp/server.py`  
**MCP name:** `paperpal-mcp` (registered as `paperpal` in MCP config)

## Tool Reference

### search_arxiv_papers(query, max_results)
- **Source:** arXiv API (`export.arxiv.org`)
- **Max results:** 50
- **Returns:** title, authors, abstract, arXiv ID, URL, published date, category
- **Use when:** You need a broad search across all CS/ML papers

### fetch_paper_details_from_arxiv(arxiv_ids)
- **Primary:** `arxiv-txt.org` (rich format with BibTeX)
- **Fallback:** arXiv API
- **Returns:** title, authors, abstract, categories, BibTeX entry
- **Use when:** You have specific arXiv IDs from a search or citation list

### semantic_search_papers_on_huggingface(query, top_n)
- **Source:** HuggingFace Papers API
- **Returns:** title, summary, arXiv ID, upvotes, trending score
- **Use when:** You want community-signaled trending papers or semantic (not keyword) search

### search_semantic_scholar(query, limit)
- **Source:** Semantic Scholar API
- **Returns:** title, authors, abstract, TLDR, venue, year, citation count, arXiv ID
- **Use when:** You need citation-aware results, venue information, or paper ranking by impact

## Design Notes

- All tools use synchronous HTTP via stdlib (no external dependencies beyond stdlib).
- arXiv search uses the official arXiv API (`export.arxiv.org`) which is rate-limited but reliable.
- arxiv-txt.org is used for BibTeX extraction; falls back to arXiv API on failure.
- HuggingFace search uses semantic embeddings — queries can be natural language, not just keywords.
- Semantic Scholar includes `tldr` summaries and citation counts for impact assessment.

## Comparison with PaperDebugger

| Aspect | PaperPal | PaperDebugger |
|--------|----------|--------------|
| Primary purpose | Paper discovery/search | Paper review/critique |
| arXiv search | Yes (API + arxiv-txt) | Yes (API only) |
| HuggingFace Papers | Yes | No |
| Semantic Scholar | Yes | No |
| Paper review | No | Full review pipeline |
| Citation verification | No | BibTeX online check |
| Writing enhancement | No | Prose polish |

## Related

- `/paperdebugger` — paper review and critique
- `/paper` — academic writing pipeline (topic → PDF)
- `/paperops` — LaTeX DevOps (build, format, diff, archive)
