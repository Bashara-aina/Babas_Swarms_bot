---
title: Harvest System
type: timeline
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- legion
created: '2026-04-14'
updated: '2026-04-14'
summary: The harvest system continuously collects intelligence candidates (papers,
  GitHub repos, web articles) relevant to Bashara's projects. The **feedback loop**
  closes the gap between what Bashara consi...
wikilinks: []
confidence: medium
source: research
---

# Legion Harvest System — Feedback Loop Architecture

## Overview

The harvest system continuously collects intelligence candidates (papers, GitHub repos, web articles) relevant to Bashara's projects. The **feedback loop** closes the gap between what Bashara considers high-quality and what the scorer automatically ranks — turning passive collection into active, personalized learning.

```
[Daily Harvester] → candidates → [Telegram /harvest_review]
                                           ↓
                         Bashara: Accept / Reject + reason tag
                                           ↓
                          [harvest-log.md] ← wiki/legion/harvester/
                                           ↓
                        [load_harvest_feedback] ← scorer reads log
                                           ↓
                          [Scorer bias vector updated]
                                           ↓
                        [Next harvest cycle — adjusted scores]
```

## Core Components

| Component | Location | Role |
|-----------|----------|------|
| `HarvestPipeline` | `core/daily_harvester/harvest_pipeline.py` | Orchestrates full pipeline; calls `load_harvest_feedback()` at 04:05 JST |
| `Scorer` | `core/daily_harvester/scorer.py` | Feedback-aware relevance scorer with bias vector |
| `load_harvest_feedback()` | `core/daily_harvester/scorer.py` | Reads `harvest-log.md`, extracts patterns, returns bias deltas |
| `apply_loaded_feedback()` | `core/daily_harvester/scorer.py` | Applies deltas to the persistent bias vector |
| `harvest-review` handler | `handlers/harvest_review.py` | Telegram UI: accept/reject/skip + reason tagging |
| `harvest-log.md` | `wiki/legion/harvester/harvest-log.md` | Persistent YAML+JSON log of all review sessions |

## Scorer Bias System

### Default Bias Vector (`DEFAULT_BIAS`)

```python
{
    "topic_drift":      -0.15,   # Candidate drifted from the search topic
    "low_quality":      -0.20,   # Poor content quality
    "duplicate":       -0.10,   # Already captured in wiki
    "not_relevant":     -0.25,   # Not useful for any active project
    "outdated":         -0.10,   # Outdated information
    "unreliable_source": -0.20,  # Low-trust domain
    "accepted":          +0.05,  # Net positive signal
}
```

Bias is stored in `data/harvest/score_bias.json` and persists across sessions.

### How Bias Is Applied

When scoring a candidate:

```python
adjusted_score = base_score + topic_bias[key]
# Clamped to [0.0, 1.0]
# High-trust domains (arxiv.org, github.com, wikipedia.org) get +0.05 bonus
```

### Reason Codes

| Reason Code | Meaning | Bias Shift |
|-------------|---------|------------|
| `topic_drift` | Title/topics changed significantly from search intent | −0.15 |
| `low_quality` | Content is thin, shallow, or poorly written | −0.20 |
| `duplicate` | Already exists in wiki under a different URL | −0.10 |
| `not_relevant` | Useful in general but not for any active project | −0.25 |
| `outdated` | Information is stale or superseded | −0.10 |
| `unreliable_source` | Suspicious domain, predatory publisher, or low citation count | −0.20 |
| `accepted` (no reason) | Candidate meets quality bar | +0.05 net |

Each rejection shifts the relevant topic/tag bias by −0.05 (capped at −0.50).
Each acceptance shifts the `accepted` bucket by +0.02 (capped at +0.30).

## How to Run /harvest_review

1. Wait for a daily harvest cycle to complete (or run `HarvestPipeline.run_full_pipeline()` manually).
2. Pending candidates appear in `data/harvest/pending_candidates.jsonl`.
3. Send `/harvest_review` to the bot.
4. Telegram shows top 5 candidates as cards with:
   - **✅ Accept** — marks candidate accepted, updates scorer positively
   - **❌ Reject** — opens reason picker (6 reason tags)
   - **⏭ Skip** — skip without feedback
5. Selecting a reason (e.g., `topic_drift`) marks rejected + tags the reason.
6. Feedback is written to `harvest-log.md` immediately and to `pending_candidates.jsonl` as `reviewed: true`.

## How to Interpret /harvest_stats

Send `/harvest_stats` to get a 30-day quality report:

```
📊 Harvest Stats (last 30 days)
Total reviewed: 47 | ✅ 31 | ❌ 16 | Accept rate: 66%

By source:
  arxiv: 20 reviewed, 80% accept
  github: 15 reviewed, 53% accept
  web: 12 reviewed, 50% accept

Top rejection reasons:
  topic_drift: 7
  low_quality: 5
  not_relevant: 3

Current scorer bias:
  ▲ topic_drift: -0.22
  ▼ low_quality: -0.15
  ▲ accepted: +0.08
```

**Interpretation guide:**
- Acceptance rate by source tells you which channels are most reliable — arXiv papers are usually high-quality, web sources vary.
- Top rejection reasons reveal systematic issues — if `topic_drift` is high, the search queries may be too broad.
- Active bias values show how the scorer has adapted — large negative values for a tag mean similar candidates will be scored lower automatically.

## Data Files

| File | Location | Purpose |
|------|----------|---------|
| `pending_candidates.jsonl` | `data/harvest/` | Unreviewed candidates awaiting Telegram review |
| `score_bias.json` | `data/harvest/` | Current scorer bias vector (auto-updated) |
| `scores_history.jsonl` | `data/harvest/` | Historical scorer update log |
| `harvest-log.md` | `wiki/legion/harvester/` | YAML+JSON log of all Telegram review sessions |

## Loading Harvest Feedback Manually

```python
from pathlib import Path
from core.daily_harvester.scorer import Scorer

scorer = Scorer()
deltas = await scorer.load_harvest_feedback(
    log_path=Path("wiki/legion/harvester/harvest-log.md"),
    lookback_days=30,
)
print(f"Bias deltas: {deltas}")

await scorer.apply_loaded_feedback(deltas)
print(f"New bias: {scorer.get_bias()}")
```

## Current Status (2026-04-13)

- ✅ `load_harvest_feedback()` implemented in `scorer.py`
- ✅ `apply_loaded_feedback()` implemented in `scorer.py`
- ✅ Feedback wired into `HarvestPipeline` at Step 1b (before parallel harvest)
- ✅ `/harvest_stats` command added to `handlers/harvest_review.py`
- ✅ `harvest_stats` BotCommand registered in `main.py`
- ✅ `/biz` command uses correct rumahlabuh table names (`rooms`, `bookings`, `branches`)
- ⚠️ `harvest-log.md` will be created on first Telegram review session
- ⚠️ `pending_candidates.jsonl` will be populated by next `HarvestPipeline.run_full_pipeline()` run

## Related Articles

- [[core/daily_harvester/scorer]] — scorer implementation
- [[core/daily_harvester/harvest-pipeline]] — pipeline orchestration
- [[core/intent-classifier]] — how messages are routed to handlers
- [[handlers/harvest-review]] — Telegram review UI implementation
