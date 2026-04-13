---
title: gpt-researcher
type: entity
status: active
tags: [research, agent, web, autonomous]
created: 2026-04-13
updated: 2026-04-13
summary: GPT Researcher is an autonomous research agent that performs multi-source web research and synthesizes findings into reports.
wikilinks: [[multi-agent-orchestration]], [[reasoning-loop]]
confidence: medium
source: research
---

# GPT Researcher

## TL;DR
GPT Researcher is an autonomous multi-agent research system that plans, executes, and synthesizes web research across multiple sources.

## How It Works

1. **Planning agent**: Creates research outline
2. **Execution agents**: Search different sources in parallel
3. **Synthesis**: Combines findings into coherent report

## Legion Integration

Used via `/research <topic>` command:
- Triggers research agent pipeline
- Returns structured findings
- Context injected into LLM for response

## Alternatives Considered

| Tool | Pros | Cons |
|------|------|------|
| GPT Researcher | Full autonomy | Slow |
| Perplexity API | Fast | Cost |
| Direct Crawl4AI | Free | Manual |

## Related Pages

- [[multi-agent-orchestration]] — Related orchestration
- [[reasoning-loop]] — Research reasoning
