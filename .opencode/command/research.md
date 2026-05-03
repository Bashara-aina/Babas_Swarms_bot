---
allowed-tools: Read,Bash,Grep,Glob,exa_web_search_exa,exa_web_fetch_exa,query_wiki_graph,gitnexus_query
argument-hint: <topic>
description: "Research a topic. Web search, code analysis, documentation review. Returns comprehensive report."
---

# /research — Deep technical research

Conduct thorough research on a technical topic.

## MANDATORY SEQUENCE (run in order)

### Step 0 — GraphRAG Wiki Query (ALWAYS run first)
Before ANY web search, query the knowledge graph:
```python
result = await query_wiki_graph(
    question="<research_topic>",
    mode="global",
    vault_path="/home/newadmin/swarm-bot/.wiki/"
)
```
If GraphRAG returns relevant content → use it, cite it, skip to synthesis.
Only call exa_web_search_exa if GraphRAG returns no useful result.

### Step 1 — Web Search (only if GraphRAG had no result)
```python
results = await exa_web_search_exa(
    num_results=10,
    query="<precise research question>"
)
```

### Step 2 — Content Fetch
For each promising result:
```python
content = await exa_web_fetch_exa(urls=[<urls>])
```

### Step 3 — Codebase Analysis
Check existing patterns:
```bash
gitnexus_query(query="<topic> related code")  # or grep
```

### Step 4 — Synthesis
Write comprehensive report.

## Research Workflow
```
0. query_wiki_graph(vault_path=.wiki/) → if relevant, use it
1. exa_web_search_exa → latest information
2. exa_web_fetch_exa → extract content from URLs
3. analyze code in codebase for existing patterns
4. synthesize findings
5. provide recommendations
```

## Web Research Tools
- `query_wiki_graph` — query GraphRAG knowledge graph (ALWAYS first)
- `gitnexus_query` — code intelligence (find existing implementations)
- `webfetch` — simple markdown extraction from URL
- `exa_web_search_exa` — search the web
- `exa_web_fetch_exa` — extract content from URLs
- `browse` — headless Chromium for JS-rendered pages

## Output Format
```
## RESEARCH_QUESTION
<precise question>

## EXECUTIVE_SUMMARY
<2-3 sentence answer>

## FROM_WIKI
<GraphRAG results if found>

## DETAILED_FINDINGS
<comprehensive analysis>

## SWARM_BOT_RELEVANCE
<how this applies to this codebase>

## RECOMMENDATIONS
<actionable next steps>

## SOURCES
- source1: URL or file
- source2: URL or file
```

## Swarm-Bot Research Priorities
- LLM provider capabilities and pricing
- Telegram Bot API updates
- Python async patterns
- Memory system best practices
- Security hardening

## Constraints
- Cite all sources
- Separate verified facts from opinions
- Include both positive and negative findings
- Wiki first → web only if wiki has no answer
