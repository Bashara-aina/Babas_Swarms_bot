---
title: ADR — Daily Harvester Web Search Integration
type: decision
status: active
tags: [legion, daily-harvester, duckduckgo, arxiv, search]
created: 2026-04-13
updated: 2026-04-13
summary: search_sources() in source_strategy.py was a stub returning []. Implemented real search via DuckDuckGo (primary) + arXiv API (fallback) with domain-based source type classification.
wikilinks:
  - [[architecture/daily-harvester]]
  - [[entities/litellm]]
confidence: high
source: loop-1-implementation
project: legion
---

## Decision

Replaced the stub `search_sources()` function in `core/daily_harvester/source_strategy.py` with a real implementation:

1. **Primary: DuckDuckGo** — `duckduckgo_search` library (already in requirements.txt), wrapped in `asyncio.to_thread()` to avoid blocking the event loop. Returns up to 10 results with title, URL, snippet, and domain-inferred trust score.

2. **Fallback: arXiv API** — `http://export.arxiv.org/api/query` with `follow_redirects=True`. Parses Atom feed with regex (no extra dependencies). Only used if DuckDuckGo returns 0 results.

3. **Source type classification** — `_classify_domain()` maps URL domains to SourceType: arxiv.org→ACADEMIC, github.com→INDUSTRY, wikipedia.org→COMMUNITY, twitter.com/x.com→SOCIAL, .gov/.go.jp/.ac.jp→GOV.

4. **Deduplication** — `seen_urls` set prevents duplicate URLs across both sources.

5. **Feature flag** — `FEATURE_WEB_SEARCH_ENABLED = True` (was False).

## Context

The `HarvestPipeline._parallel_harvest()` called `search_sources()` which always returned `[]` due to `FEATURE_WEB_SEARCH_ENABLED = False` and a TODO comment about Tavily/Firecrawl integration. The daily harvester was running but producing zero candidates every cycle.

`duckduckgo_search>=4.0.0` was already in requirements.txt (probed in `main.py:_probe_duckduckgo()`), and `httpx` was available for the arXiv API call. No new dependencies were needed.

## Consequences

- Harvest pipeline now produces real candidate entries from web search
- arXiv fallback ensures academic content is available even if DuckDuckGo is blocked (e.g., in certain regions)
- DuckDuckGo results may include low-quality sources (e.g., Chinese Q&A sites for generic ML queries) — the trust scoring system handles this by assigning them lower trust scores
- `FEATURE_WEB_SEARCH_ENABLED = True` means the daily harvester will make outbound HTTP requests at 04:00 WIB

## Files Changed

- `core/daily_harvester/source_strategy.py:search_sources` — full reimplementation with DuckDuckGo + arXiv
- `core/daily_harvester/source_strategy.py:_classify_domain` — new function for domain→SourceType mapping
- `core/daily_harvester/source_strategy.py:FEATURE_WEB_SEARCH_ENABLED` — changed to True
- `core/daily_harvester/harvest_pipeline.py:_parallel_harvest` docstring — updated (TODO removed)
- `core/daily_harvester/harvest_pipeline.py:_send_telegram_report` docstring — clarified Telegram delivery is via scheduler callback

## Notes

- The `duckduckgo_search` package emits `RuntimeWarning: This package has been renamed to 'ddgs'`. Consider migrating to `ddgs` in a future loop.
- DuckDuckGo may return 0 results from certain regions (e.g., Japan via some ISPs) due to Cloudflare blocking — the arXiv fallback handles this.
- The `test_daily_harvester.py` suite runs the pipeline with mocked search, so no live network calls occur during testing.
