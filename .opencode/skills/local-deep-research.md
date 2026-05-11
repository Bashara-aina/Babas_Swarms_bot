# Local Deep Research Skill

Use local-deep-research for comprehensive, AI-powered research with iterative analysis, proper citations, and access to academic databases.

## When to Use This Skill

- Research tasks requiring multi-source verification
- Academic research (arXiv, PubMed, Semantic Scholar)
- Comprehensive analysis with citations
- Factual research on complex topics
- Document analysis (RAG on private documents)

## Tools Available

### Research (LLM-powered, 1-30 min)

| Tool | Time | Use Case |
|------|------|----------|
| `quick_research` | 1-5 min | Quick facts, summaries |
| `detailed_research` | 5-15 min | Thorough investigation |
| `generate_report` | 10-30 min | Full report with citations |
| `analyze_documents` | 30s-2 min | Search private documents |

### Search (Direct, 5-30s)

| Tool | Time | Use Case |
|------|------|----------|
| `search` | 5-30s | Raw results, no LLM |

### Discovery

| Tool | Use Case |
|------|----------|
| `list_search_engines` | See available engines |
| `list_strategies` | See research strategies |
| `get_configuration` | Current LLM/search config |

## Quick Usage Examples

### Quick Research
```
Research: "What is the current state of quantum computing in 2026?"
Engine: duckduckgo
Strategy: rapid
```

### Detailed Academic Research
```
Research: "Recent advances in transformer architecture"
Engine: arxiv
Strategy: comprehensive
Iterations: 5
```

### Generate Full Report
```
Generate Report: "Climate change impact on agriculture"
Searches per section: 3
```

### Search Private Documents
```
Analyze Documents: "performance optimization techniques"
Collection: coding-patterns
Max results: 20
```

## Search Engines

| Engine | Best For | API Key? |
|--------|----------|----------|
| arxiv | CS, physics, math papers | No |
| pubmed | Medical, life sciences | No |
| semantic_scholar | Academic with citations | No |
| wikipedia | General knowledge | No |
| searxng | Meta-search | No |
| brave | Web search | No |
| duckduckgo | General web | No |
| google | Web search | Yes |

## Research Strategies

- **source-based** — Default iterative exploration
- **rapid** — Quick focused (1-2 iterations)
- **iterative** — Deep research (5-10 iterations)
- **comprehensive** — Most thorough
- **academic** — Paper-focused
- **factual** — Verification-focused

## Configuration

The MCP server respects environment variables:
- `LDR_LLM_PROVIDER` — LLM provider (openai, anthropic, ollama, etc.)
- `LDR_LLM_MODEL` — Model name
- `LDR_LLM_API_KEY` — API key
- `LDR_DATA_DIR` — Data directory for library

For Ollama local models:
```bash
export LDR_LLM_PROVIDER=ollama
export LDR_LLM_MODEL=qwen3.6-27b
export OLLAMA_HOST=http://localhost:11434
```