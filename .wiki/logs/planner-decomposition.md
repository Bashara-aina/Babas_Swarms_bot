# Legion Daily Intelligence Harvester — Planner Decomposition
> Generated: 2026-04-11
> Task: Implement "Legion Daily Intelligence Harvester" autonomous knowledge evolution system

---

## CONTEXT SUMMARY

**Project**: SwarmBot (Python Telegram bot, aiogram 3.4+, litellm 1.57+)
**Key files**: `llm_client.py` → `llm_client/__init__.py` (async `chat()` with litellm acompletion)
**Existing patterns**: `skills/web_search.py` (WebSearch class with async search), `core/proactive/scheduler.py` (APScheduler-based)
**Wiki structure**: `.wiki/` with `logs/`, `decisions/`, `agents/`, `research/` directories
**Required env vars**: Use `os.getenv()`, never hardcode

---

## SUBTASK LIST (Ordered for Sequential Execution)

### Phase 1: Core Data Structures & Type Definitions

| # | File(s) | What It Accomplishes | Dependencies |
|---|---------|---------------------|--------------|
| 1 | `core/daily_harvester/types.py` | Create TypedDicts: `CandidateInfo`, `SwarmVerdict`, `TopicBudget`, `SourceInfo`, `WikiEntry`. Define enums: `VerdictDecision`, `SourceType`, `TrustTier`. | None |
| 2 | `.wiki/knowledge/TOPIC_WEIGHTS.json` | Initial JSON state for topic weights: base topics (cekwajar_labor_law:5, cekwajar_market:4, cekwajar_engineering:4, popw_ml_research:4, babas_bot_ai:3, rumahlabuh_property:3, indonesia_economy:3, ai_tools_llm:3, personal_life:3, surprise_discoveries:5) with decay tracking fields | 1 |
| 3 | `.wiki/knowledge/cekwajar/`, `.wiki/knowledge/popw/`, `.wiki/knowledge/ai-tools/`, `.wiki/knowledge/personal/`, `.wiki/knowledge/general/` | Create 5 topic directory structure with placeholder INDEX.md files | 2 |
| 4 | `core/daily_harvester/wiki_storage.py` | WikiStorage class: read/write wiki entries, `INDEX.md` management, `TOPIC_WEIGHTS.json` read/write, naming convention `[TOPIC-PREFIX]-[NNN]-[short-slug]-[YYYY-MM-DD].md`, `REJECTED_LOG.md`, `CONFLICT_LOG.md`, `HARVEST_LOG.md` | 1, 2, 3 |

### Phase 2: Topic Budget System

| # | File(s) | What It Accomplishes | Dependencies |
|---|---------|---------------------|--------------|
| 5 | `core/daily_harvester/topic_budget.py` | `detect_active_topics()`: reads Telegram history (7 days), git log (3 days), current wiki INDEX.md, TOPIC_WEIGHTS.json. Implements weight formula: `base_weight = mention_count × 2 + commit_count × 3 + (days_since_last_update)^0.5`. Allocates 100 slots dynamically. Respects minimums for base topics. Exception: cekwajar, popw, babas_bot_ai never decay below minimum. | 1, 2, 4 |
| 6 | `core/daily_harvester/topic_evolution.py` | `TopicEvolution` class: new topic detection (3 mentions in 3 days → create directory, 5 slots for 3 days trial). Decay logic: 14 days no mention → weight halved, 30 days → minimum (3 slots), 60 days → hibernate. `apply_decay()` and `promote_new_topic()` methods. | 5 |

### Phase 3: Swarm Debate System

| # | File(s) | What It Accomplishes | Dependencies |
|---|---------|---------------------|--------------|
| 7 | `core/daily_harvester/swarm_debate.py` | `SwarmDebate` class with 4 agents: PROSECUTOR (skeptical, finds reasons wrong), DEFENDER (advocates accuracy), FACT_CHECKER (verifies 2+ sources, checks contradictions), JUDGE (final decision: ACCEPT/ACCEPT_WITH_CAVEAT/SUPERSEDE/REJECT/NEEDS_MORE_RESEARCH). `run_debate()` method returns `SwarmVerdict`. Batch processing in `run_debate_batch()` for 10 candidates. Model assignments (cost-optimized): PROSECUTOR=minimax/M2.7, DEFENDER=minimax/M2.7, FACT_CHECKER=anthropic/claude-sonnet-4-20250514, JUDGE=minimax/M2.7. | 1 |
| 8 | `core/daily_harvester/source_strategy.py` | `SourceStrategy` class: trust scores by source type (Government .go.id: 10/10, Academic/arXiv: 9/10, Verified news: 7/10, Official company: 7/10, Reddit verified: 6/10, X/Twitter: 6/10, Blog known author: 7/10). `fetch_source()` with async HTTP. `ContradictionResolver` with rules: gov always wins, newer date wins for time-sensitive, higher citation wins for research, ADD_BOTH with conflict note if unclear. | 1 |

### Phase 4: Daily Job Pipeline & Harvester Orchestrator

| # | File(s) | What It Accomplishes | Dependencies |
|---|---------|---------------------|--------------|
| 9 | `core/daily_harvester/harvest_pipeline.py` | `HarvestPipeline` class orchestrating the daily job: 04:00 WIB context read → topic_budget dict; 04:15 WIB parallel harvest (one worker per topic × 2-3 sources); 04:45 WIB swarm debate in batches of 10; 05:00 WIB write to .wiki; 05:15 WIB generate morning report; 05:20 WIB done. `run_daily_harvest()` async method. Uses `apscheduler` for scheduling (compatible with existing scheduler.py pattern). Timezone: Asia/Jakarta (WIB = UTC+7). | 5, 6, 7, 8 |
| 10 | `core/daily_harvester/morning_report.py` | `MorningReport` class: generates max 3000 chars, max 5 topics, emoji anchors, topic budget visualization, conflicts found count, rejected count. `format_report()` returns Telegram HTML string. | 4, 9 |
| 11 | `core/daily_harvester/__init__.py` | Package init with exports: `DailyHarvester`, `HarvestPipeline`, `SwarmDebate`, `TopicBudgetEngine`, `WikiStorage`, `MorningReport`, all TypedDicts/enums | 1-10 |

### Phase 5: Main Entry Point

| # | File(s) | What It Accomplishes | Dependencies |
|---|---------|---------------------|--------------|
| 12 | `daily_harvester.py` (root) | Standalone CLI entry point: `python daily_harvester.py --run-now` for manual trigger, `--dry-run` for testing without LLM calls. Imports from `core.daily_harvester`. Shows harvester status. | 11 |
| 13 | `core/daily_harvester/cron_setup.py` | Cron job registration: generates crontab entry `0 21 * * *` (runs at 04:00 WIB = 21:00 UTC previous day) to call `python /home/newadmin/swarm-bot/daily_harvester.py --run-now`. `setup_cron()` function that appends to crontab, `remove_cron()` to cleanup. | 12 |

### Phase 6: Integration & Environment Spec

| # | File(s) | What It Accomplishes | Dependencies |
|---|---------|---------------------|--------------|
| 14 | `.env.example` addition | Document new env vars: `HARVESTER_ENABLED=1`, `HARVESTER_TELEGRAM_DAYS=7`, `HARVESTER_GIT_DAYS=3`, `HARVESTER_WIKI_MODEL=minimax/MiniMax-M2.7`, `HARVESTER_JUDGE_MODEL=minimax/MiniMax-M2.7`, `HARVESTER_FACTCHECK_MODEL=anthropic/claude-sonnet-4-20250514` | None |
| 15 | `core/daily_harvester/wiki_indexer.py` | `WikiIndexer` class: maintains `INDEX.md` for each topic directory. Updates on each new entry. Provides `search_by_topic()`, `search_by_tag()`, `get_recent()` methods. | 4 |
| 16 | `tests/test_daily_harvester.py` | pytest tests: test_topic_budget_weight_formula, test_swarm_verdict_struct, test_wiki_storage_naming, test_source_trust_scores, test_contradiction_resolver_gov_wins, test_morning_report_format_length, test_harvest_pipeline_stage_ordering. Use `pytest-asyncio`. | 1-15 |

### Phase 7: Documentation & Review Preparation

| # | File(s) | What It Accomplishes | Dependencies |
|---|---------|---------------------|--------------|
| 17 | `.wiki/decisions/ADR-HARVESTER-001.md` | Architecture Decision Record: "Legion Daily Intelligence Harvester" — why, how it works, alternatives considered, consequences | 1-16 |
| 18 | `.wiki/logs/harvester-implementation-2026-04-11.md` | Implementation log: subtask completions, notes, blockers | 1-17 |

---

## WORKER PROMPT

```
Implement the "Legion Daily Intelligence Harvester" as described in `.wiki/logs/planner-decomposition.md`.

## Key Systems to Build

### 1. Topic Budget System (Adaptive Quota Engine)
- `detect_active_topics()` function that reads Telegram history (7 days), git log (3 days), current wiki INDEX.md, and TOPIC_WEIGHTS.json
- Allocates 100 slots dynamically across topics
- Base topics with minimum allocations: cekwajar_labor_law (5), cekwajar_market (4), cekwajar_engineering (4), popw_ml_research (4), babas_bot_ai (3), rumahlabuh_property (3), indonesia_economy (3), ai_tools_llm (3), personal_life (3), surprise_discoveries (5)
- Weight formula: base_weight = mention_count × 2 + commit_count × 3 + (days_since_last_update)^0.5

### 2. Swarm Debate System (4 agents)
- PROSECUTOR: Skeptical, finds reasons info might be wrong
- DEFENDER: Advocates for the information's accuracy
- FACT-CHECKER: Verifies against 2+ sources, checks contradictions
- JUDGE: Final decision (ACCEPT/ACCEPT_WITH_CAVEAT/SUPERSEDE/REJECT/NEEDS_MORE_RESEARCH)
- Swarm verdict includes: decision, reason, contradicts (wiki file ID), prosecutor_concerns, defender_rebuttals, fact_check_result

### 3. Wiki Storage Format
- Directory structure: .wiki/knowledge/{cekwajar,popw,ai-tools,personal,general}/
- Wiki page format with id, title, source, source_type, trust_score, dates, topic, tags, swarm_verdict, actionable_for
- Entry naming: [TOPIC-PREFIX]-[NNN]-[short-slug]-[YYYY-MM-DD].md
- Required files: INDEX.md, TOPIC_WEIGHTS.json, REJECTED_LOG.md, CONFLICT_LOG.md, HARVEST_LOG.md

### 4. Daily Job Pipeline
- 04:00 WIB: Context read → topic_budget dict
- 04:15 WIB: Parallel harvest (one worker per topic × 2-3 sources)
- 04:45 WIB: Swarm debate in batches of 10
- 05:00 WIB: Write to .wiki
- 05:15 WIB: Generate morning report
- 05:20 WIB: Done

### 5. Morning Report Format
- Max 3000 chars, max 5 topics
- Format with emoji anchors, topic budget visualization
- Includes conflicts found, rejected count

### 6. Source Strategy
- Government (.go.id): trust 10/10
- Academic journals/arXiv: trust 9/10
- Verified news: trust 7/10
- Official company: trust 7/10
- Reddit (verified): trust 6/10
- X/Twitter: trust 6/10
- Blog (known author): trust 7/10

### 7. Contradiction Resolution
- Official gov regulation always wins
- Newer date wins for time-sensitive data
- Higher citation count wins for research
- If unclear: ADD_BOTH with conflict note

### 8. Topic Evolution
- New topic: 3 mentions in 3 days → create directory, 5 slots for 3 days trial
- Topic decay: 14 days no mention → weight halved, 30 days → minimum (3 slots), 60 days → hibernate
- Exceptions: cekwajar, popw, babas_bot_ai never decay below minimum

## Code Standards
- Python: type hints on all functions, docstrings on public methods, Black formatting
- Async: All I/O operations use asyncio/await
- LLM calls go through llm_client.py `chat()` function — never call litellm directly
- Use os.getenv() for all env vars
- Format: f-strings only

## Existing Patterns to Follow
- `skills/web_search.py`: WebSearch class with async search, returns list[dict] with title/url/snippet
- `core/proactive/scheduler.py`: ProactiveScheduler with asyncio Task loop, apscheduler usage
- `llm_client/__init__.py`: `_call_model()` with litellm acompletion, retry logic

## Execute subtasks in order from `.wiki/logs/planner-decomposition.md`
```

---

## REVIEW CHECKLIST

For each subtask, @reviewer must verify:

### Types & Data Structures (Subtasks 1-4)
- [ ] `CandidateInfo` TypedDict has all required fields: id, title, content, source, source_type, trust_score, topic, tags, discovered_at
- [ ] `SwarmVerdict` TypedDict has: decision (enum), reason, contradicts (list[str]), prosecutor_concerns, defender_rebuttals, fact_check_result, agent_model_used
- [ ] `TopicBudget` TypedDict has: topic, allocated_slots, weight, base_weight, last_updated
- [ ] Wiki entry naming follows `[TOPIC-PREFIX]-[NNN]-[short-slug]-[YYYY-MM-DD].md` pattern
- [ ] TOPIC_WEIGHTS.json has all 10 base topics with minimum allocations

### Topic Budget System (Subtasks 5-6)
- [ ] Weight formula implemented correctly: `mention_count × 2 + commit_count × 3 + (days_since_last_update)^0.5`
- [ ] 100 slots allocated dynamically with minimums respected
- [ ] Exception topics (cekwajar, popw, babas_bot_ai) never decay below minimum
- [ ] New topic creation: 3 mentions in 3 days triggers directory creation + 5 slots for 3 days trial

### Swarm Debate System (Subtask 7)
- [ ] PROSECUTOR prompt: skeptical, adversarial, looks for flaws
- [ ] DEFENDER prompt: advocates for information accuracy
- [ ] FACT_CHECKER prompt: verifies against multiple sources, checks contradictions
- [ ] JUDGE prompt: authoritative, returns one of 5 decisions
- [ ] Batch processing handles 10 candidates at a time
- [ ] Model cost optimization: FACT_CHECKER uses strongest model (claude), others use minimax

### Source Strategy (Subtask 8)
- [ ] Trust scores match spec (gov 10, academic 9, news 7, etc.)
- [ ] `fetch_source()` handles async HTTP with proper error handling
- [ ] ContradictionResolver implements all 4 rules correctly
- [ ] Gov source always wins in contradictions
- [ ] ADD_BOTH used when unclear

### Pipeline & Report (Subtasks 9-10)
- [ ] Pipeline runs in correct order: context → harvest → debate → wiki → report → done
- [ ] All timestamps in WIB (Asia/Jakarta = UTC+7)
- [ ] Morning report: max 3000 chars, max 5 topics
- [ ] Morning report includes: emoji anchors, topic budget visualization, conflicts/rejected counts

### Entry Point & Cron (Subtasks 12-13)
- [ ] CLI accepts `--run-now` flag for manual trigger
- [ ] CLI accepts `--dry-run` for testing without LLM calls
- [ ] Cron: `0 21 * * *` runs at 04:00 WIB
- [ ] `setup_cron()` and `remove_cron()` functions work correctly

### Integration & Tests (Subtasks 14-16)
- [ ] All new env vars documented in `.env.example`
- [ ] Tests cover: weight formula, verdict structure, naming convention, trust scores, contradiction rules, report format, pipeline ordering
- [ ] Tests use `pytest-asyncio` with `--asyncio-mode=auto`

### Documentation (Subtasks 17-18)
- [ ] ADR-001 explains architecture decision with alternatives considered
- [ ] Implementation log tracks all subtask completions
