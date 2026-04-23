---
name: daily-harvester
description: "Skill for the Daily_harvester area of swarm-bot. 66 symbols across 12 files."
---

# Daily_harvester

66 symbols | 12 files | Cohesion: 81%

## When to Use

- Working with code in `core/`
- Understanding how write_entry, update_index, append_harvest_log work
- Modifying daily_harvester-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `core/daily_harvester/wiki_storage.py` | _topic_dir, write_entry, update_index, append_harvest_log, write_pending_candidates (+8) |
| `core/daily_harvester/harvest_pipeline.py` | _write_to_wiki, _get_scorer, _context_read, _generate_report, _send_telegram_report (+4) |
| `core/daily_harvester/scorer.py` | load_bias, save_bias, apply_bias, update_from_feedback, apply_loaded_feedback (+4) |
| `core/daily_harvester/source_strategy.py` | get_trust_score, get_trust_tier, _ddg_search, _classify_domain, _source_rank (+3) |
| `core/daily_harvester/swarm_debate.py` | run_judge, run_debate, run_debate_batch, _budget_guard_check, run_prosecutor (+2) |
| `core/daily_harvester/topic_budget.py` | _load_topic_weights, _recent_commit_subjects, _days_since, _get_git_commit_count, detect_active_topics (+1) |
| `tests/test_daily_harvester.py` | test_report_length, test_pipeline_ordering, test_trust_scores, test_swarm_verdict |
| `core/daily_harvester/scheduler.py` | _wib_now, start, _run_loop, _run_harvest |
| `core/daily_harvester/wiki_indexer.py` | build_index, search_by_topic |
| `core/daily_harvester/__init__.py` | detect, run |

## Entry Points

Start here when exploring this area:

- **`write_entry`** (Function) — `core/daily_harvester/wiki_storage.py:135`
- **`update_index`** (Function) — `core/daily_harvester/wiki_storage.py:198`
- **`append_harvest_log`** (Function) — `core/daily_harvester/wiki_storage.py:242`
- **`write_pending_candidates`** (Function) — `core/daily_harvester/wiki_storage.py:333`
- **`read_pending_candidates`** (Function) — `core/daily_harvester/wiki_storage.py:342`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `write_entry` | Function | `core/daily_harvester/wiki_storage.py` | 135 |
| `update_index` | Function | `core/daily_harvester/wiki_storage.py` | 198 |
| `append_harvest_log` | Function | `core/daily_harvester/wiki_storage.py` | 242 |
| `write_pending_candidates` | Function | `core/daily_harvester/wiki_storage.py` | 333 |
| `read_pending_candidates` | Function | `core/daily_harvester/wiki_storage.py` | 342 |
| `mark_candidate_reviewed` | Function | `core/daily_harvester/wiki_storage.py` | 367 |
| `build_index` | Function | `core/daily_harvester/wiki_indexer.py` | 27 |
| `search_by_topic` | Function | `core/daily_harvester/wiki_indexer.py` | 72 |
| `test_report_length` | Function | `tests/test_daily_harvester.py` | 186 |
| `test_pipeline_ordering` | Function | `tests/test_daily_harvester.py` | 234 |
| `generate` | Function | `core/daily_harvester/morning_report.py` | 25 |
| `run_full_pipeline` | Function | `core/daily_harvester/harvest_pipeline.py` | 226 |
| `test_trust_scores` | Function | `tests/test_daily_harvester.py` | 93 |
| `get_trust_score` | Function | `core/daily_harvester/source_strategy.py` | 47 |
| `get_trust_tier` | Function | `core/daily_harvester/source_strategy.py` | 52 |
| `resolve` | Function | `core/daily_harvester/source_strategy.py` | 203 |
| `detect_active_topics` | Function | `core/daily_harvester/topic_budget.py` | 96 |
| `normalize_budget` | Function | `core/daily_harvester/topic_budget.py` | 160 |
| `detect` | Function | `core/daily_harvester/__init__.py` | 90 |
| `load_bias` | Function | `core/daily_harvester/scorer.py` | 54 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Handlers | 1 calls |
| Tests | 1 calls |

## How to Explore

1. `gitnexus_context({name: "write_entry"})` — see callers and callees
2. `gitnexus_query({query: "daily_harvester"})` — find related execution flows
3. Read key files listed above for implementation details
