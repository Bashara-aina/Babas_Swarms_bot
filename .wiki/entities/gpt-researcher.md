---
title: GPT Researcher
type: entity
status: active
tags: [research, agent, web, autonomous]
created: 2026-04-13
updated: 2026-04-13
summary: GPT Researcher is an autonomous multi-agent research system used by Legion for deep research tasks. It plans, executes parallel web searches, and synthesizes findings into structured reports. Accessed via the three-agent pipeline or /research command.
wikilinks:
  - [[./concepts/multi-agent-orchestration]]
  - [[./concepts/reasoning-loop]]
  - [[./concepts/llm-cost-routing]]
confidence: medium
source: research
project: legion
---

# GPT Researcher

## TL;DR
GPT Researcher is an autonomous multi-agent research system that plans, executes parallel web searches, and synthesizes findings into structured reports. Used by Legion for deep research tasks via `/research <topic>` or the three-agent pipeline. Not actively deployed — `browser_agent.py` (Playwright-based) is the primary research tool.

## How It Works

1. **Planning agent**: Analyzes topic, creates research outline with key questions
2. **Execution agents**: Launch parallel searches across different sources (web, arXiv, news)
3. **Synthesis agent**: Combines findings into coherent structured report with citations

## Legion Integration

```
[/research Indonesia wage laws]
  → intent_router: research intent detected
  → three-agent pipeline: analyst → researcher → synthesizer
  → Returns structured report with sources
```

Primary research tool: `browser_agent.py` (Playwright) which is more reliable for web navigation.

## Key Properties
- Autonomy level: High (self-directs search strategy)
- Average task duration: 60-180 seconds
- Parallel agents: Up to 5 concurrent search agents
- Cost: Uses `groq/moonshotai/kimi-k2-instruct` (free tier)

## Alternatives Considered

| Tool | Autonomy | Speed | Cost | Status in Legion |
|------|----------|-------|------|-----------------|
| GPT Researcher | High | Slow (2-5min) | Medium | Evaluated, not primary |
| Browser Agent (Playwright) | Medium | Fast | Low | **Primary research tool** |
| Perplexity API | Low | Fast | Pay-per-use | Fallback |
| Direct Crawl4AI | Low | Medium | Free | Used for arXiv |

## Failure Modes
- Web search blocked: Falls back to Crawl4AI for academic sources
- Task timeout: Cut off at 180s, partial results returned
- Synthesis fails: Returns raw search results with error note

## See Also
[[./concepts/multi-agent-orchestration]] — How research fits into the three-agent pipeline
[[./concepts/reasoning-loop]] — Research reasoning pattern
[[./concepts/llm-cost-routing]] — Model selection for research tasks
