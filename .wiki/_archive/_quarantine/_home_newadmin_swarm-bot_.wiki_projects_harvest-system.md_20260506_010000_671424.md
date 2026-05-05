---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/projects/harvest-system.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-06T01:00:00.671457"
}
---

---
title: harvest-system
type: project
status: active
tags: [legion, harvester, data-pipeline, feedback-loop, telegram]
created: 2026-04-13
updated: 2026-04-13
summary: Daily harvester with Telegram-powered feedback loop — candidates are scored, reviewed via one-tap /harvest-review, and bias is updated for better future candidates.
wikilinks:
  - [[concepts/self-improvement-loop]]
  - [[architecture/daily-harvester]]
  - [[entities/litellm]]
confidence: high
source: implementation
---

# Harvest System

## TL;DR

The harvest system collects web research candidates via DuckDuckGo + arXiv, presents them for one-tap Telegram review via `/harvest-review`, writes structured feedback to `wiki/legion/harvester/harvest-log.md`, and updates the scoring bias in `data/harvest/score_bias.json` so future candidates are more relevant.

## Overview

The harvest quality loop closes the gap between "harvester runs" and "learning what Bashara actually cares about." Without feedback, the harvester scores candidates purely on topical relevance. With feedback, it adjusts topic weights based on accept/reject patterns.

```
┌─────────────────────────────────────────────────────────────┐
│  04:00 WIB  Daily Harvester runs                           │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ DuckDuckGo│───▶│  Scoring +  │───▶│ pending_candidates│  │
│  │ + arXiv  │    │  Swarm Debate│    │ .jsonl           │  │
│  └──────────┘    └──────────────┘    └────────┬─────────┘  │
└───────────────────────────────────────────────┼─────────────┘
                                                │ Bashara opens
                                                ▼ /harvest-review
┌─────────────────────────────────────────────────────────────┐
│  Telegram UI: candidate cards with                         │
│  [Accept] [Reject] [Skip] + reason tag picker               │
│                                                │ Feedback    │
│                                                ▼ written    │
│  ┌──────────────────────┐   ┌──────────────────────────────┐│
│  │ harvest-log.md       │◀──│ score_bias.json updated     ││
│  │ (structured JSON)    │   │ (reason → bias shift)       ││
│  └──────────────────────┘   └──────────────────────────────┘│
│          │ next run reads bias ─────────────────────────────┘
└──────────────────────────────────────────────────────────────┘
```

## Components

| File | Purpose |
|------|---------|
| `core/daily_harvester/harvest_pipeline.py` | Orchestrates harvest → scoring → write pending |
| `core/daily_harvester/wiki_storage.py` | Reads/writes `harvest-log.md` + `pending_candidates.jsonl` |
| `core/daily_harvester/scorer.py` | Feedback-aware scoring + bias management |
| `handlers/harvest_review.py` | Telegram UI — `/harvest-review` command |
| `data/harvest/pending_candidates.jsonl` | Pending candidate queue (one JSON per line) |
| `data/harvest/score_bias.json` | Current scoring bias vector |
| `wiki/legion/harvester/harvest-log.md` | Structured session log (YAML frontmatter + JSON body) |

## Vault Path

All harvester wiki content lives in `wiki/legion/harvester/` — the **active vault** per CLAUDE.md section 2b. The deprecated `.wiki/` (split-brain) is no longer written by the harvester.

## Structured Log Format

Each harvest session produces a YAML-frontmatter block followed by a JSON body in `harvest-log.md`:

```json
{
  "date": "2026-04-13",
  "session_id": "a1b2c3d4",
  "candidates_reviewed": [
    {
      "candidate_id": "ai_tools_llm_http...",
      "source": "arxiv/cs.AI/2504.01999",
      "title": "Sparse Attention Patterns for Long Context",
      "url": "https://arxiv.org/abs/2504.01999",
      "score": 0.72,
      "decision": "rejected",
      "reason": "topic_drift",
      "reason_detail": "transformer efficiency, not relevant to Bashara's research",
      "tags": ["transformers", "efficiency"]
    }
  ],
  "metadata": {
    "candidates_found": 23,
    "candidates_reviewed": 2,
    "pending": 21,
    "review_mode": "telegram"
  }
}
```

## Reason Codes

| Code | When to use |
|------|-------------|
| `topic_drift` | Candidate is about a related but not directly relevant topic |
| `low_quality` | Source is shallow, clickbait, or unreliable |
| `duplicate` | Already covered by an existing accepted candidate |
| `not_relevant` | Wrong topic entirely for Bashara's current interests |
| `outdated` | Information is stale (>1 year old for tech topics) |
| `unreliable_source` | Blogspam, Chinese Q&A sites, no citations |
| `accepted` | High-quality, directly relevant, worth reading |

## Scoring Bias Vector

Bias is stored in `data/harvest/score_bias.json` and applied multiplicatively to topic scores on each run. Default values:

| Reason | Default bias | Effect per rejection |
|--------|-------------|---------------------|
| `topic_drift` | -0.15 | -0.05 per feedback |
| `low_quality` | -0.20 | -0.05 per feedback |
| `duplicate` | -0.10 | -0.05 per feedback |
| `not_relevant` | -0.25 | -0.05 per feedback |
| `outdated` | -0.10 | -0.05 per feedback |
| `unreliable_source` | -0.20 | -0.05 per feedback |
| `accepted` | +0.05 | +0.02 per feedback |

Bias is clamped to `[-0.50, +0.30]` per reason.

## Telegram Review UX

`/harvest-review` shows the top 5 pending candidates as compact cards:

```
🔍 Harvest Review — 12 pending
Showing top 5 (7 more)
One-tap feedback closes the loop → better candidates next time.

1. Sparse Attention Patterns for Long Context
🔗 https://arxiv.org/abs/2504.01999
📊 score=0.72 | topic=ai_tools_llm

[✅ Accept] [❌ Reject] [⏭ Skip]
[topic_drift] [low_quality] [not_relevant]
[duplicate] [outdated] [bad_source]
```

Each candidate card has:
- **Accept** — marks accepted, updates bias +0.02, writes to harvest-log
- **Reject** — marks rejected with `low_quality`, updates bias -0.05
- **Skip** — defers without feedback
- **Reason picker row** — precise rejection reason (more impactful than default `low_quality`)

## Current Status

Active. `/harvest_review` command registered. Structured log format deployed. Scoring bias updates on every review action.

## See Also

- [[architecture/daily-harvester]] — Pipeline architecture
- [[concepts/self-improvement-loop]] — How harvested content feeds into learning
- [[entities/litellm]] — LLM routing used in swarm debate scoring
