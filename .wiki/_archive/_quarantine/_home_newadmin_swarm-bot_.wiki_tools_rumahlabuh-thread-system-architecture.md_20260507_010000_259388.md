---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/tools/rumahlabuh-thread-system-architecture.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-07T01:00:00.259410"
}
---

---
title: Rumahlabuh Thread System Architecture
type: architecture
status: active
tags: [rumahlabuh, threads, scheduler, analytics]
created: 2026-04-23
updated: 2026-04-23
summary: Time-windowed content scheduler for rumahlabuh Threads posts with 3 morning/4 afternoon/2 night slots, analytics tracking, and FYP survey analysis.
wikilinks:
  - [[rumahlabuh-facts.json]]
  - [[rumahlabuh-thread-blueprints]]
confidence: high
source: implementation
---

## Overview

The rumahlabuh thread system is a time-windowed content scheduling platform for Indonesian Twitter/X threads about kost (boarding house) reviews. It generates, schedules, and tracks engagement metrics for 6-post threads published across three daily publishing windows.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                              │
│              scripts/threads_mode.py                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │  status  │ │   on/off │ │  toggle  │ │ scheduler│               │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │
│                                              │                       │
│                         ┌────────────────────┼────────────────────┐  │
│                         │ scheduler status   │                     │  │
│                         │ scheduler generate │                     │  │
│                         │ scheduler run      │                     │  │
│                         │ scheduler windows  │                     │  │
│                         └────────────────────┴────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Scheduler Core                               │
│                   tools/rumahlabuh_scheduler.py                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │ Scheduler      │  │ SeededThread   │  │ AnalyticsStore │        │
│  │ (time windows) │  │ Generator      │  │ (engagement)   │        │
│  └────────────────┘  └────────────────┘  └────────────────┘        │
│  ┌────────────────┐  ┌────────────────┐                           │
│  │ ThreadReevaluator│  │ SurveyAnalyzer │                           │
│  └────────────────┘  └────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌──────────────────┐  ┌───────────────────────┐
│Persistence   │  │ Thread Blueprints│  │ Analytics JSON        │
│(rumahlabuh   │  │ (rumahlabuh_     │  │ (rumahlabuh_analytics │
│scheduler_    │  │ thread_blueprints│  │ .json)                │
│history.json)  │  │ .json)           │  │                       │
└───────────────┘  └──────────────────┘  └───────────────────────┘
```

---

## Data Flow

### 1. Scheduling Flow

```
User runs: python scripts/threads_mode.py scheduler generate --date 2026-04-24
    │
    ▼
threads_mode.py (main) parses --date argument
    │
    ▼
_scheduler_generate(date_iso) calls Scheduler.schedule_window(date_iso)
    │
    ▼
Scheduler.schedule_window():
  1. Parse date_iso → day_date
  2. For each WindowConfig (morning/afternoon/night):
     - Compute slot hours within window
     - Assign post_number (1-6 cycling)
     - Generate thread_seed via SHA1(date_iso:window:post_idx)
  3. Create PostSlot dataclass for each slot
  4. Record pseudo-signatures in AnalyticsStore
  5. Save schedule to SCHEDULER_HISTORY JSON
  6. Return list of slot dicts
    │
    ▼
Output: 9 slots across 3 windows printed to console
```

### 2. Generation Flow

```
User runs: python scripts/threads_mode.py scheduler run --date 2026-04-24
    │
    ▼
_scheduler_run(date_iso) calls:
  1. Scheduler.schedule_window(date_iso) — get slots
  2. For each slot: Scheduler.generate_thread_for_slot(slot)
    │
    ▼
Scheduler.generate_thread_for_slot():
  1. Extract date_iso and thread_seed from slot
  2. SeededThreadGenerator.generate_with_seed(date_iso, seed_suffix)
    │
    ▼
SeededThreadGenerator.generate_with_seed():
  1. SHA1(date_iso:seed_suffix) → seed_int
  2. random.Random(seed_int) — deterministic RNG
  3. Choose technique + pronouns from blueprints
  4. For each post 1-6: pick from technique template pool
  5. SHA1(thread content) → signature
  6. Return {thread, technique, pronouns, signature, date, seed_used}
    │
    ▼
AnalyticsStore.record_generated() called for each thread
  │
  ▼
Output: 9 threads with techniques/pronouns printed
```

### 3. Analytics Tracking Flow

```
Post goes live on Twitter/X → User completes survey
    │
    ▼
Scheduler.run_survey(sig, views, likes, replies, saves, notes)
    │
    ▼
SurveyAnalyzer.analyze() computes fyp_likelihood
    │
    ▼
AnalyticsStore records:
  - update_engagement() → engagement_score
  - set_fyp_worthy() → marks fyp_candidates
  - record_survey() → stores survey_responses
    │
    ▼
ThreadReevaluator.reevaluate_previous_threads() scores all threads
  │
  ▼
Returns weak threads, top performers, average score
```

---

## Scheduler Windows

| Window | Label | Hours | Posts | Weight | Interval |
|--------|-------|-------|-------|--------|----------|
| Morning | Pagi | 06:00–10:00 | 3 | 1.0 | 1.3h |
| Afternoon | Siang | 12:00–17:00 | 4 | 1.2 | 1.25h |
| Night | Malam | 19:00–22:00 | 2 | 0.9 | 1.5h |

**Total: 9 posts/day**

### Post Distribution Algorithm

```python
for window in config.windows:
    window_duration = window.end_hour - window.start_hour
    step = window_duration / window.post_count

    for post_idx in range(window.post_count):
        hour = int(window.start_hour + post_idx * step)
        minute = int((window.start_hour + (post_idx + 0.5) * step - hour) * 60) % 60
```

### Slot Output for 2026-04-24

| Slot | Window | Time | Post |
|------|--------|------|------|
| 0 | Pagi | 06:40 | 1/6 |
| 1 | Pagi | 07:00 | 2/6 |
| 2 | Pagi | 08:19 | 3/6 |
| 3 | Siang | 12:37 | 4/6 |
| 4 | Siang | 13:52 | 5/6 |
| 5 | Siang | 14:07 | 6/6 |
| 6 | Siang | 15:22 | 1/6 |
| 7 | Malam | 19:45 | 2/6 |
| 8 | Malam | 20:15 | 3/6 |

---

## Analytics Schema

### Thread Record

```json
{
  "date_iso": "2026-04-24",
  "signature": "sha1_hex_of_thread_content",
  "technique": "relatable_story",
  "pronouns": "gue/lo",
  "engagement_score": 0.5234,
  "views": 1250,
  "likes": 45,
  "replies": 12,
  "quotes": 3,
  "bookmarks": 8,
  "fyp_worthy": true,
  "scheduled_at": 1745450000.0,
  "posted_at": 1745500000.0,
  "survey_completed": true,
  "survey_responses": {
    "fyp_likelihood": 0.75,
    "likes": 45,
    "replies": 12,
    "saves": 8
  }
}
```

### AnalyticsStore Top-Level

```json
{
  "threads": [/* ThreadRecord[] */],
  "daily_summaries": {
    "2026-04-24": {
      "total_posts": 9,
      "window_distribution": {"Pagi": 3, "Siang": 4, "Malam": 2}
    }
  },
  "fyp_candidates": ["sig1", "sig2", "sig3"],
  "last_reevaluate": "2026-04-23T10:00:00"
}
```

### Engagement Score Formula

```python
score = round(
    (likes * 1.0 + replies * 2.0 + quotes * 3.0 + bookmarks * 1.5) / views * 100, 4
)
```

### FYP Likelihood Thresholds

| Likes | FYP Likelihood |
|-------|----------------|
| >50 | 0.9 |
| >30 | 0.75 |
| >15 | 0.6 |
| ≥15 AND replies ≥3 | 0.4 |
| <15 | 0.15 |

---

## File Dependencies

```
tools/rumahlabuh_scheduler.py
├── tools/persistence.py (init_db, add_scheduled_task, get_active_tasks, record_task_execution)
├── tools/rumahlabuh_thread_blueprints.json (technique templates, post pools)
├── tools/rumahlabuh_facts.json (factual content for thread generation)
├── tools/rumahlabuh_scheduler_history.json (schedule history)
└── tools/rumahlabuh_analytics.json (engagement tracking)

scripts/threads_mode.py
└── tools/threads_mode_control.py (is_enabled, set_enabled, toggle, open_workspace)
```

---

## Scheduler Config Defaults

```python
@dataclass
class SchedulerConfig:
    windows: list[WindowConfig] = [
        WindowConfig(name="morning",   label="Pagi",   start_hour=6,  end_hour=10, post_count=3, weight=1.0),
        WindowConfig(name="afternoon", label="Siang",  start_hour=12, end_hour=17, post_count=4, weight=1.2),
        WindowConfig(name="night",     label="Malam",  start_hour=19, end_hour=22, post_count=2, weight=0.9),
    ]
    default_date: str = ""
    seed_date_format: str = "%Y-%m-%d"
```

---

## Backward Compatibility

### CLI Legacy Support

The original `threads_mode.py` commands remain functional:

```bash
python scripts/threads_mode.py status    # → threads_mode=ON/OFF
python scripts/threads_mode.py on       # → turns ON
python scripts/threads_mode.py off      # → turns OFF
python scripts/threads_mode.py toggle   # → toggles state
```

These are handled by the top-level subparsers before the `scheduler` subcommand is processed. The `--no-open` flag continues to work to suppress browser opening.

### Persistence Backward Compatibility

The `Scheduler` class reads from `rumahlabuh_scheduler_history.json` and appends new entries. The JSON structure has not changed — `{"schedule_history": [...]}` remains the root key.

---

## Migration Notes

### v1.0 (2026-04-23) — Initial Architecture

**No prior version exists.** This document captures the initial system design.

### Future Schema Changes

If `rumahlabuh_analytics.json` schema changes:

1. **Add new fields with defaults** — existing threads must deserialize without errors
2. **Never remove fields** — mark deprecated with `_` prefix in code, keep in JSON
3. **Version bump** — add `schema_version: int` field to root analytics object
4. **Migration path** — document transform function from old → new schema

### Blueprints Schema Evolution

The `rumahlabuh_thread_blueprints.json` file structure:

```json
{
  "techniques": ["relatable_story", "showcase_soft", "fake_controversy", "edukasi"],
  "pools": {
    "relatable_story": {
      "1": ["Post 1 templates..."],
      "2": ["Post 2 templates..."]
    }
  },
  "pronouns": [["gue", "lo"], ["aku", "kamu"]]
}
```

If adding new technique fields, ensure `SeededThreadGenerator.generate_with_seed()` handles missing keys gracefully (fallback pool exists for sparse pools).

---

## Price Validator Architecture

```
tools/rumahlabuh_price_validator.py
├── firecrawl (browser automation) — primary
│   └── BrowserValidator.navigate_and_validate()
│       ├── _browser_goto() → navigate to rumahlabuh.com
│       ├── _browser_click_location() → select location
│       ├── _browser_select_room() → select room type
│       ├── _browser_fill_date() → fill check-in/check-out
│       ├── _browser_click_order() → click order button
│       └── _browser_extract_price() → extract from price display
│
└── HTTP fallback (rumahlabuh_http / aiohttp) — graceful degradation
    └── BrowserValidator._http_fallback_validate()
        ├── GET https://rumahlabuh.com (connectivity check)
        └── GET https://rumahlabuh.com/api/search (price lookup)
```

### Price Parser

Handles formats: `Rp 2.500.000`, `2.5 juta`, `2500000`, `2500.000`

```python
def _parse_price(self, price_text: str) -> Optional[float]:
    text = price_text.strip()
    text = text.replace("Rp", "").replace("rp", "").replace("IDR", "")
    text = text.replace("juta", "000000").replace("jt", "000000")
    text = text.replace(",", "").replace(" ", "")
    match = re.search(r"[\d.]+", text)
    return float(match.group()) if match else None
```

---

## Key Entry Points

| Entry Point | Purpose |
|-------------|---------|
| `scripts/threads_mode.py scheduler status` | Show analytics summary |
| `scripts/threads_mode.py scheduler generate --date YYYY-MM-DD` | Generate slots for a date |
| `scripts/threads_mode.py scheduler run --date YYYY-MM-DD` | Generate + log threads |
| `scripts/threads_mode.py scheduler windows --date YYYY-MM-DD` | Show window config + computed slots |
| `Scheduler.schedule_window(date_iso)` | Core scheduling algorithm |
| `SeededThreadGenerator.generate_with_seed(date_iso, seed_suffix)` | Deterministic thread gen |
| `AnalyticsStore.record_generated(date_iso, sig, technique, pronouns)` | Track new thread |
| `validate_room_price(room_type, location, check_in, check_out)` | Browser price validation |

---

## Dependencies

```
# Core
aiogram>=3.4          # Telegram bot
litellm>=1.57          # LLM routing
aiohttp               # HTTP client (fallback)
aiodns                # DNS resolver (fallback)

# Optional
firecrawl             # Browser automation (primary price validation)

# Data files
rumahlabuh_thread_blueprints.json
rumahlabuh_facts.json
rumahlabuh_analytics.json
rumahlabuh_scheduler_history.json
```

---

*End of document*
