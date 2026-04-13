---
title: daily-harvester
type: architecture
status: active
tags: [legion, data-pipeline, web-search, arxiv, duckduckgo]
created: 2026-04-13
updated: 2026-04-13
summary: Daily harvester is Legion's background web research pipeline that collects relevant articles from DuckDuckGo (primary) and arXiv (fallback) to feed the curiosity engine and maintain currency on technical topics.
wikilinks:
  - [[concepts/self-improvement-loop]]
  - [[entities/litellm]]
confidence: medium
source: implementation
---

# Daily Harvester

## TL;DR

The daily harvester is a background task in `core/daily_harvester/` that runs on a schedule (configured via `CURIOSITY_INTERVAL_MIN`) and collects web search results via DuckDuckGo + arXiv API fallback. It feeds candidate articles to Legion's curiosity engine for relevance scoring and potential discussion with Bashara.

## Overview

The harvest pipeline runs in `core/daily_harvester/harvest_pipeline.py`. It uses `search_sources()` in `source_strategy.py` which wraps `duckduckgo_search` for web search and falls back to the arXiv API for academic content. The pipeline runs on a configurable schedule via `CURIOSITY_INTERVAL_MIN` (default 30 minutes), controlled by the curiosity engine's main loop in `core/proactive/curiosity_engine.py`. Candidates are scored for relevance before being sent to Bashara via Telegram.

The harvest pipeline avoids blocking the main event loop by wrapping all I/O in `asyncio.to_thread()` — this is critical because DuckDuckGo HTTP requests would otherwise stall Telegram message processing.

## Components

- `core/daily_harvester/harvest_pipeline.py` — Orchestrates parallel harvest, scoring, and Telegram reporting
- `core/daily_harvester/source_strategy.py` — DuckDuckGo + arXiv API integration with domain trust scoring
- `core/proactive/curiosity_engine.py` — Triggers harvest on schedule, evaluates candidates
- Domain classification maps URLs to SourceType: arxiv.org→ACADEMIC, github.com→INDUSTRY, wikipedia.org→COMMUNITY

## Implementation Details

The search pipeline in `core/daily_harvester/source_strategy.py`:

```python
async def search_sources(query: str) -> list[dict]:
    """Primary: DuckDuckGo, Fallback: arXiv API."""
    results = await duckduckgo_search(query, num_results=10)
    if not results:
        results = await arxiv_fallback(query)
    return [_classify_domain(r) for r in results]
```

Domain trust scoring:
- `arxiv.org` → ACADEMIC (highest weight for research queries)
- `github.com` → INDUSTRY (technical depth)
- `wikipedia.org` → COMMUNITY (general overview)
- `.gov` / `.ac.jp` → GOV (authoritative)
- `twitter.com` / `x.com` → SOCIAL (current events, opinions)

## Current Status

Active. `FEATURE_WEB_SEARCH_ENABLED = True` as of the 2026-04-13 ADR decision. DuckDuckGo is the primary source; arXiv provides fallback for academic content.

## See Also

- [[decisions/adr-2026-04-13-daily-harvester-search]] — Decision record for the search implementation
- [[concepts/self-improvement-loop]] — How harvested content feeds into learning
