---
title: legion-daily-harvester
type: architecture
status: active
tags: [architecture, autonomous, research, daily-harvester]
created: 2026-04-13
updated: 2026-04-13
summary: The daily harvester is Legion's autonomous research system — a set of 11 modules that run on a cron schedule to keep Legion's knowledge current through topic scoring, multi-source harvesting, wiki synthesis, and morning reports.
wikilinks:
  - [[architecture/legion-module-map]]
  - [[./concepts/multi-agent-orchestration]]
  - [[./concepts/reasoning-loop]]
confidence: high
source: implementation
---

# Legion Daily Harvester

## TL;DR

Legion's daily harvester (`core/daily_harvester/`) is an autonomous research pipeline that runs on a cron schedule. It selects topics based on relevance scoring, harvests content from configured sources, synthesizes wiki articles, and produces a morning briefing for Bashara. All LLM calls are budget-guarded.

## Directory Structure

```
core/daily_harvester/
├── swarm_debate.py        # Daily debate on selected topics (LLM calls, budget-guarded)
├── harvest_pipeline.py    # Multi-source content gathering orchestration
├── morning_report.py      # Formatted morning digest for Bashara
├── scheduler.py           # Cron scheduling logic
├── scorer.py              # Topic relevance scoring
├── source_strategy.py    # Source selection per topic
├── topic_budget.py       # Daily topic allocation (how many topics per day)
├── topic_evolution.py    # Tracks topic depth over successive runs
├── types.py              # Typed data classes (Topic, Source, Report)
├── wiki_indexer.py       # Wiki content indexing for relevance matching
└── wiki_storage.py       # Wiki write-back after synthesis

Entry point: daily_harvester.py (root) imports core/daily_harvester/
```

## Topic Selection Flow

1. **scorer.py** evaluates pending topics against:
   - Recent conversation history (recency)
   - Bashara's project interests (from `data/user_profile.json`)
   - Existing wiki coverage (wiki_indexer.py)
   - Topic evolution state (topic_evolution.py)

2. **topic_budget.py** limits daily topic count to prevent resource exhaustion

3. **source_strategy.py** selects appropriate sources per topic:
   - Academic → arXiv, Google Scholar
   - Market → news APIs, financial sites
   - Technical → GitHub, Hacker News, Stack Overflow
   - Indonesian regulatory → official government portals

## Harvest Pipeline

```
harvest_pipeline.py
├── source_strategy.select(topic) → list of Source
├── For each source:
│   ├── fetch content (web scraping / API calls)
│   └── extract structured data
├── Consolidate deduplicated content
└── Pass to synthesis stage
```

## Wiki Synthesis

After content harvest:

1. **wiki_storage.py** checks existing wiki coverage
2. If gap detected → triggers swarm debate for synthesis
3. New/updated articles written to `wiki/` with proper frontmatter
4. Dataview indexes updated
5. `compile_state.json` refreshed

## Morning Report

**morning_report.py** formats the digest for Telegram delivery:

- Top 3 researched topics with summaries
- Wiki changes overnight
- Pending items for Bashara's review
- Budget status (daily spend vs. limit)

Delivered via `tools/briefing.py` at configured time (default: 07:30 JST).

## Budget Guard

`swarm_debate.py` LLM calls are wrapped with `@budget_guard`:

```python
@budget_guard(task_type="daily_harvester")
async def run_debate(topic: str) -> DebateResult:
    ...
```

Guard checks `BudgetManager.can_spend("daily_harvester")` before any LLM call. If budget is exhausted, the harvester skips synthesis and logs a warning.

## Cron Schedule

Configured in `core/daily_harvester/scheduler.py`:
- Morning harvest: 06:00 JST
- Evening synthesis: 22:00 JST
- Topic evolution check: every 6 hours

Can be triggered manually via `/run harvest <topic>`.

## Related Pages

- [[architecture/legion-module-map]] — Module context
- [[./concepts/reasoning-loop]] — How Legion plans and refines
- [[architecture/legion-orchestrator-system]] — How orchestration layers connect
