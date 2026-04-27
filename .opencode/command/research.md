---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <topic>
description: "Research a topic. Web search, code analysis, documentation review. Returns comprehensive report."
---

# /research — Deep technical research

Conduct thorough research on a technical topic.

## Usage
```
/research best LLM fallback strategies 2024
/research aiogram 3.x middleware patterns
/research mem0ai vs llamaindex for agent memory
/research firecrawl vs crawl4ai for web scraping
```

## Research Workflow
```
1. Check existing wiki/docs for prior knowledge
2. Web search for latest information
3. Analyze code in codebase for existing patterns
4. Synthesize findings
5. Provide recommendations
```

## Web Research Tools
- firecrawl_search — primary web search
- firecrawl_scrape — extract from specific pages
- exa_web_search_exa — alternative search
- browser-use_browse_task — JS-rendered pages

## Output Format
```
## RESEARCH_QUESTION
<precise question>

## EXECUTIVE_SUMMARY
<2-3 sentence answer>

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
