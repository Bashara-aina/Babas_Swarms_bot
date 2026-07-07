---
name: paperpal
description: "Search and discover academic papers across arXiv, HuggingFace Papers, and Semantic Scholar. Use when the user wants to find papers by topic, get paper details by arXiv ID, discover trending ML papers, or search with citation data. Complements /paperdebugger (review) and /paper (writing pipeline)."
trigger: /paperpal
---

# /paperpal

Search and discover academic papers across three sources. MCP server at `tools/mcpServers/paperpal_mcp/server.py`.

## Tools

All tools available via the `paperpal-mcp` MCP server:

| Tool | Source | What it does |
|------|--------|-------------|
| `search_arxiv_papers` | arXiv API | Search papers by query. Returns titles, authors, abstracts, arXiv IDs. |
| `fetch_paper_details_from_arxiv` | arxiv-txt.org + arXiv API fallback | Get full details + BibTeX for specific arXiv papers by ID. |
| `semantic_search_papers_on_huggingface` | HuggingFace Papers | Semantic search over HF papers. Includes upvote/trending scores. |
| `search_semantic_scholar` | Semantic Scholar | Search with citation counts, venue info, TLDR summaries, external IDs. |

## Workflows

### Literature search for a topic
1. `search_arxiv_papers` for broad coverage
2. `search_semantic_scholar` for citation-aware results
3. `semantic_search_papers_on_huggingface` for trending/community-signaled papers
4. `fetch_paper_details_from_arxiv` on promising IDs for BibTeX

### After reading a paper, find related work
1. Search Semantic Scholar for citing and cited papers
2. Cross-reference on arXiv for full text

### Collect BibTeX for a reading list
`fetch_paper_details_from_arxiv` returns BibTeX from arxiv-txt.org

## Integration with other paper skills

- **Before writing** (`/paper from-zero`): use paperpal for literature search to build the evidence matrix and literature notes.
- **During review** (`/paperdebugger review_paper`): use paperpal to verify and supplement citations.
- **After writing** (`/paperdebugger verify_citations`): use paperpal's search tools to double-check hard-to-find references.

## Upstream

Original project: https://github.com/mila-iqia/paperpal (MIT, by jerpint @ Mila Quebec AI Institute)
