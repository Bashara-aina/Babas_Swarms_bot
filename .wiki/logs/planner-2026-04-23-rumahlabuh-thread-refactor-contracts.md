---
title: Planner 2026 04 23 Rumahlabuh Thread Refactor Contracts
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# CONTRACT ARCHITECTURE — Rumahlabuh Thread System Refactor

> 25 contracts across 5 batches | Date: 2026-04-23
> Planner: @planner | Worker: @worker | Reviewer: @reviewer

---

## BATCH 1: Architecture + Data Layer (Contracts 1–5)
**Parallel**: Contracts 1, 2, 3, 4, 5 can run simultaneously

---

### CONTRACT #1: Create rumahlabuh_scheduler.py scheduler engine

WHAT:
Create a new scheduler engine at `tools/rumahlabuh_scheduler.py` that schedules daily thread generation across morning/afternoon/night windows, stores schedule state in the existing persistence DB, and supports reevaluation of previous threads based on engagement metrics.

FILES:
READ: tools/persistence.py (lines 32-47 schema, 126-148 scheduled tasks API)
WRITE: tools/rumahlabuh_scheduler.py (new file, ~300 lines)
RUN: python -c "from tools.rumahlabuh_scheduler import ThreadScheduler; print('ok')"

DONE_WHEN:
- tools/rumahlabuh_scheduler.py exists with ThreadScheduler class
- class has schedule_window(window_name, hour_range, count) → list[datetime] method
- class has record_engagement(signature, views, likes, comments) async method
- class has get_reevaluate_candidates(min_score=5.0, limit=5) async → list[dict]
- class has generate_batch(window_name, count) → list[tuple[result, datetime]]
- Uses persistence.Persistence for all storage (no new DB files)
- async methods with aiosqlite usage matching persistence.py patterns
- Morning window: 07:00-12:00 WIB, Afternoon: 12:00-19:00 WIB, Night: 19:00-22:00 WIB

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_scheduler import ThreadScheduler
import asyncio
async def test():
    s = ThreadScheduler()
    await s.init()
    morning = s.schedule_window('morning', (7, 12), count=3)
    print(f'morning posts: {len(morning)}')
    print(f'first post hour: {morning[0].hour}')
asyncio.run(test())
" → output: "morning posts: 3" and "first post hour: 7"

BLOCKER_IF:
- tools/persistence.py cannot be imported (missing aiosqlite)
- ThreadScheduler crashes on init (DB connection failure)

---

### CONTRACT #2: Add thread analytics tables to persistence.py

WHAT:
Add four new async functions to persistence.py for thread-specific analytics: store_thread_metrics, get_thread_analytics, update_thread_fyp_score, and list_recent_threads.

FILES:
READ: tools/persistence.py (lines 1-30 init, 677-708 __all__)
WRITE: tools/persistence.py (new functions + Persistence class methods + __all__ update)
RUN: python -c "from tools.persistence import store_thread_metrics, get_thread_analytics, update_thread_fyp_score, list_recent_threads; print('ok')"

DONE_WHEN:
- Added `thread_analytics` table: id, signature, posted_at, views, likes, comments, fyp_score, engagement_rate, technique, used_in_batch
- Added `thread_survey_responses` table: id, signature, question_key, response, created_at
- store_thread_metrics(sig, posted_at, views, likes, comments, technique, batch) async function exists
- get_thread_analytics(sig) → dict exists
- update_thread_fyp_score(sig, score) async function exists
- list_recent_threads(limit=10) → list[dict] exists
- survey_submit(sig, question_key, response) async function exists
- survey_get_responses(sig) → list[dict] exists
- Persistence class has all 6 new methods
- __all__ list includes all 6 new functions

PROOF_FORMAT:
python -c "
import asyncio
from tools.persistence import Persistence
async def test():
    p = Persistence()
    await p.init()
    await p.store_thread_metrics('sig_test_123', 1700000000.0, 500, 45, 12, 'edukasi', 'morning_1')
    result = await p.get_thread_analytics('sig_test_123')
    print('got analytics:', result is not None)
    await p.survey_submit('sig_test_123', 'q_fyp', 'yes')
    resp = await p.survey_get_responses('sig_test_123')
    print('survey responses:', len(resp))
asyncio.run(test())
"

BLOCKER_IF:
- asyncio runtime not available
- DB schema conflict (table already exists with different columns)

---

### CONTRACT #3: Create rumahlabuh_price_validator.py for rumahlabuh.com price scraping

WHAT:
Create a price validation module at `tools/rumahlabuh_price_validator.py` that validates price data by first browsing rumahlabuh.com (selecting room, ordering, filling check-in/check-out) before showing real prices.

FILES:
READ: tools/persistence.py (browser usage patterns - none exist, use firecrawl tools)
WRITE: tools/rumahlabuh_price_validator.py (new file, ~200 lines)
RUN: python -c "from tools.rumahlabuh_price_validator import PriceValidator, PriceValidationError; print('ok')"

DONE_WHEN:
- PriceValidator class with async scrape_property(url) method using firecrawl browser
- PriceValidator class with async select_room_and_order(room_type) method
- PriceValidator class with async fill_check_io(check_in, check_out) method
- PriceValidator class with get_validated_price() returning dict with breakdown
- format_price_reply(price_data) → str function for Indonesian formatting
- Uses firecrawl_firecrawl_browser_create + firecrawl_browser_execute for automation
- Falls back to firecrawl_firecrawl_scrape if browser fails
- Raises PriceValidationError if validation chain incomplete
- All facts sourced from rumahlabuh.com or Google Maps (not hardcoded)
- PriceValidator has get_fact_for_content(key) method using FactsExtractor pattern

PROOF_FORMAT:
python -c "from tools.rumahlabuh_price_validator import PriceValidator, PriceValidationError; print('imported ok')"

BLOCKER_IF:
- firecrawl browser tools not available (check firecrawl_firecrawl_browser_list first)

---

### CONTRACT #4: Refactor FactsExtractor with structured dataclass and config-driven path

WHAT:
Refactor FactsExtractor in `tools/rumahlabuh_thread_generator.py` to use a config-driven facts path and store all extracted facts in a typed ThreadFacts dataclass.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 109-137), tools/rumahlabuh_threads_v5.json (line 3 source_facts)
WRITE: tools/rumahlabuh_thread_generator.py (modify FactsExtractor class)
RUN: python -c "from tools.rumahlabuh_thread_generator import FactsExtractor, load_facts; fe = FactsExtractor(load_facts()); print('price_min:', fe.get_price_min()); print('city:', fe.get_city())"

DONE_WHEN:
- FactsExtractor uses @dataclass ThreadFacts with fields: price_min, price_max, city, area, facilities, room_types, parking_capacity, contact_wa, website, is_pet_friendly, has_joglo, has_dapur
- facts_path read from rumahlabuh_threads_v5.json source_facts field
- FactsExtractor(facts_text, facts_path=None) signature
- FactsExtractor.get_fact(key) → str generic lookup method
- FactsExtractor.all_facts() → dict full fact dict
- FactsExtractor lazy-reloads when file mtime changes
- FactsExtractor.get_room_price(room_name) → dict with daily/weekly/biweekly/monthly/deposit
- FactsExtractor.get_property(name) → dict (labuh_biru or labuh_banyu)

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import FactsExtractor, load_facts
fe = FactsExtractor(load_facts())
print('city:', fe.get_city())
print('facilities:', len(fe.all_facts()['facilities']))
print('price_min:', fe.get_price_min())
print('all_facts keys:', list(fe.all_facts().keys()))
"

BLOCKER_IF:
- Facts text format changed (breakage in parsing)
- Config file source_facts path invalid

---

### CONTRACT #5: Create rumahlabuh_facts.json structured facts data file

WHAT:
Create a new structured JSON data file at `tools/rumahlabuh_facts.json` containing all verified property facts in machine-readable format.

FILES:
READ: .claude/scripts/rumahlabuh-facts.md (all 118 lines)
WRITE: tools/rumahlabuh_facts.json (new file)
RUN: python -c "import json; d=json.load(open('tools/rumahlabuh_facts.json')); print('keys:', list(d.keys()))"

DONE_WHEN:
- tools/rumahlabuh_facts.json exists and is valid JSON
- Top-level keys: "labuh_biru", "labuh_banyu", "shared_facts"
- labuh_biru contains: address, room_types (list with name/daily/weekly/biweekly/monthly/deposit), facilities, parking_capacity, is_pet_friendly, has_joglo
- labuh_banyu contains: address, room_types, facilities, parking_capacity, is_pet_friendly, has_dapur
- shared_facts contains: distance_ums, wifi_speed, contact_wa, website, booking_url, monthly_price_min, monthly_price_max
- Facts match rumahlabuh-facts.md exactly (no fabrication)
- rumahlabuh_threads_v5.json source_facts updated to point to rumahlabuh_facts.json

PROOF_FORMAT:
python -c "
import json
d = json.load(open('tools/rumahlabuh_facts.json'))
print('labuh_biru rooms:', len(d['labuh_biru']['room_types']))
print('labuh_banyu rooms:', len(d['labuh_banyu']['room_types']))
print('price_min:', d['shared_facts']['monthly_price_min'])
print('facilities labuh_biru:', d['labuh_biru']['facilities'][:3])
print('all keys:', list(d.keys()))
"

BLOCKER_IF:
- JSON data differs from rumahlabuh-facts.md (fabrication check fails)
- Invalid JSON syntax

---

## BATCH 2: Core Refactor — Generator + Validator (Contracts 6–10)
**Dependencies**: BATCH 1 contracts 1, 2, 4, 5 must complete first
**Parallel**: Contracts 6, 7, 8 can run simultaneously (same file, different methods)
**Sequential after**: Contracts 9, 10 depend on BATCH 1 contracts 1, 2

---

### CONTRACT #6: Add deterministic seed/reproducibility to BlueprintGenerator

WHAT:
Add optional seed parameter to BlueprintGenerator.generate() for deterministic, reproducible thread output.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 271-309)
WRITE: tools/rumahlabuh_thread_generator.py (modify generate method and result dict)
RUN: python -c "from tools.rumahlabuh_thread_generator import generate_fresh_thread; r1=generate_fresh_thread(seed=42); r2=generate_fresh_thread(seed=42); print('same seed same sig:', r1['signature']==r2['signature'])"

DONE_WHEN:
- BlueprintGenerator.generate(today, seed=None) accepts seed parameter
- When seed is None: uses existing f"{today.isoformat()}:{attempt}" behavior
- When seed is int: uses random.Random(seed) for all random choices
- Result dict includes "seed": int | None field
- Same seed + same today → identical thread (signature exact match)
- generate_fresh_thread(save_history=True, seed=None) signature updated
- CLI --seed argument added to __main__ block

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import generate_fresh_thread
r1 = generate_fresh_thread(seed=999)
r2 = generate_fresh_thread(seed=999)
r3 = generate_fresh_thread(seed=888)
print('seed 999 sig:', r1['signature'][:12])
print('identical same seed:', r1['signature'] == r2['signature'])
print('different different seed:', r1['signature'] != r3['signature'])
print('seed in result:', r1.get('seed'))
"

BLOCKER_IF:
- Same seed produces different signatures between runs

---

### CONTRACT #7: Add graceful fallback to pool exhaustion in BlueprintGenerator

WHAT:
Add graceful fallback logic in BlueprintGenerator so pool exhaustion uses hardcoded defaults instead of crashing.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 206-238)
WRITE: tools/rumahlabuh_thread_generator.py (modify _build_context, _safe_choice usage)
RUN: python tools/rumahlabuh_thread_generator.py 2>&1 | head -10

DONE_WHEN:
- _safe_choice(rng, [], fallback) returns fallback (already correct)
- All pool lookups have explicit fallbacks
- Empty pools produce hardcoded defaults (not crash)
- Generator records "pool_exhausted" in result metadata when fallback used
- result["metadata"]["fallback_used"] contains list of which pools used fallbacks
- ThreadValidator passes output with fallbacks (no new errors introduced)

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import BlueprintGenerator, load_config, load_facts
cfg = load_config()
gen = BlueprintGenerator(cfg, load_facts())
# Force empty pools test
cfg['generator']['blueprint_file'] = 'nonexistent.json'
# This should still work with graceful fallbacks
" 2>&1 | grep -i error || echo "Graceful handling works"

BLOCKER_IF:
- Empty pool causes KeyError/IndexError instead of fallback

---

### CONTRACT #8: Add configurable weight overrides to BlueprintGenerator

WHAT:
Add support for runtime technique weight configuration in BlueprintGenerator.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 247-269)
WRITE: tools/rumahlabuh_thread_generator.py (modify _select_technique and load_config)
RUN: python -c "from tools.rumahlabuh_thread_generator import BlueprintGenerator, load_config, load_facts; cfg=load_config(); cfg['generator']['technique_weights']={'edukasi':10,'showcase_soft':0}; gen=BlueprintGenerator(cfg,load_facts()); r=[gen.generate()['technique'] for _ in range(20)]; print('edukasi:',r.count('edukasi')); print('showcase_soft:',r.count('showcase_soft'))"

DONE_WHEN:
- load_config() reads technique_weights from generator section if present
- _select_technique respects technique_weights when non-empty dict
- Weight 0 excludes technique from random selection entirely
- Only _select_technique affected (not blueprint weights file)
- Validation passes with overridden weights

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import BlueprintGenerator, load_config, load_facts
cfg = load_config()
cfg['generator']['technique_weights'] = {'edukasi': 100, 'relatable_story': 0, 'hot_take': 0, 'fake_controversy': 0, 'showcase_soft': 0}
gen = BlueprintGenerator(cfg, load_facts())
results = [gen.generate()['technique'] for _ in range(10)]
print('All edukasi?', all(t == 'edukasi' for t in results))
print('showcase_soft count:', results.count('showcase_soft'))
"

BLOCKER_IF:
- Weight 0 still allows technique selection

---

### CONTRACT #9: Connect BlueprintGenerator to analytics system

WHAT:
Connect BlueprintGenerator.mark_used() to the new analytics store (fire-and-forget) and add analytics context to generate result.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 309-315), tools/persistence.py (from CONTRACT #2)
WRITE: tools/rumahlabuh_thread_generator.py (modify mark_used and generate result dict)
RUN: python -c "from tools.rumahlabuh_thread_generator import generate_fresh_thread; r=generate_fresh_thread(); print('success:',r.get('success')); print('signature:',bool(r.get('signature')))"

DONE_WHEN:
- mark_used(result) calls store_thread_metrics() async in fire-and-forget
- All analytics calls wrapped in try/except (do not block generation)
- Result dict includes "batch" field (None when not scheduled, string when scheduled)
- Result dict includes "analytics_pending" bool field
- generate_fresh_thread() returns complete result even if analytics fails
- No new required arguments to generate_fresh_thread() (backward compatible)

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import generate_fresh_thread
import asyncio
async def test():
    r = generate_fresh_thread()
    print('success:', r.get('success'))
    print('batch field:', r.get('batch'))
    print('analytics_pending:', r.get('analytics_pending'))
asyncio.run(test())
"

BLOCKER_IF:
- Analytics call makes generation slower
- Generation fails when DB unavailable

---

### CONTRACT #10: Add survey methods to persistence (extend CONTRACT #2)

WHAT:
Add complete survey system methods to persistence.py for FYP determination from user responses.

FILES:
READ: tools/persistence.py (from CONTRACT #2)
WRITE: tools/persistence.py (extend with survey methods from CONTRACT #2 requirements)
RUN: python -c "from tools.persistence import survey_submit, survey_get_responses, survey_stats, survey_get_fyp_worthy; print('ok')"

DONE_WHEN:
- survey_submit(signature, question_key, response) stores response
- survey_get_responses(signature) → list[dict]
- survey_stats(since_hours=24) → dict with response_count, fyp_yes, fyp_no
- survey_get_fyp_worthy(signature) → bool (True if majority "yes" to q_fyp_worthy)
- Survey questions: q_fyp_worthy, q_engagement_level, q_improve_point
- All survey methods are async
- Persistence class has survey methods
- __all__ updated

PROOF_FORMAT:
python -c "
import asyncio
from tools.persistence import survey_submit, survey_get_responses, survey_stats, survey_get_fyp_worthy
async def test():
    sig = 'survey_test_sig_999'
    await survey_submit(sig, 'q_fyp_worthy', 'yes')
    await survey_submit(sig, 'q_fyp_worthy', 'yes')
    await survey_submit(sig, 'q_fyp_worthy', 'no')
    fyp = await survey_get_fyp_worthy(sig)
    stats = await survey_stats()
    print(f'fyp worthy (2/3 yes): {fyp}')
    print(f'stats: {stats}')
asyncio.run(test())
"

BLOCKER_IF:
- Survey DB writes conflict with thread_analytics table

---

## BATCH 3: Scheduler System + CLI + Telegram (Contracts 11–15)
**Dependencies**: BATCH 1 (contracts 1, 2), BATCH 2 (contracts 6, 7, 8, 9)

---

### CONTRACT #11: Implement schedule_window in rumahlabuh_scheduler.py

WHAT:
Implement schedule_window method in ThreadScheduler that returns optimal posting datetimes for morning (3), afternoon (4), night (2) windows in WIB timezone.

FILES:
READ: tools/rumahlabuh_scheduler.py (from CONTRACT #1)
WRITE: tools/rumahlabuh_scheduler.py (implement schedule_window and generate_batch)
RUN: python -c "from tools.rumahlabuh_scheduler import ThreadScheduler; import asyncio; s=asyncio.run(ThreadScheduler().init()); m=s.schedule_window('morning',(7,12),count=3); print(f'count:{len(m)}, first:{m[0].hour}h')"

DONE_WHEN:
- schedule_window returns list of datetime objects spaced within window
- morning (07:00-12:00): 3 posts, spaced ~100-120 minutes apart
- afternoon (12:00-19:00): 4 posts, spaced ~90-105 minutes apart
- night (19:00-22:00): 2 posts, spaced ~90 minutes apart
- All times in Asia/Jakarta timezone (UTC+7, WIB)
- generate_batch(window, count) returns list of (thread_result, datetime) tuples

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_scheduler import ThreadScheduler
import asyncio
async def test():
    s = ThreadScheduler()
    await s.init()
    m = s.schedule_window('morning', (7, 12), count=3)
    a = s.schedule_window('afternoon', (12, 19), count=4)
    n = s.schedule_window('night', (19, 22), count=2)
    print(f'morning {len(m)}: [(t.hour,t.minute) for t in m]')
    print(f'afternoon {len(a)}: [(t.hour,t.minute) for t in a]')
    print(f'night {len(n)}: [(t.hour,t.minute) for t in n]')
asyncio.run(test())
"

BLOCKER_IF:
- Posts not evenly spaced within window
- Timezone not WIB (UTC+7)

---

### CONTRACT #12: Implement reevaluate_previous_threads in scheduler

WHAT:
Implement reevaluate_previous_threads in ThreadScheduler that retrieves past threads from history, ranks them by underperformance, and returns candidates for re-generation.

FILES:
READ: tools/rumahlabuh_scheduler.py (from CONTRACTS 1, 11)
WRITE: tools/rumahlabuh_scheduler.py (implement reevaluate_previous_threads and generate_improved_version)
RUN: python -c "from tools.rumahlabuh_scheduler import ThreadScheduler; import asyncio; r=asyncio.run(ThreadScheduler().reevaluate_previous_threads()); print(type(r), len(r))"

DONE_WHEN:
- reevaluate_previous_threads(min_age_days=7, top_n=5) → list[dict]
- Ranking: score = engagement_rate*0.4 + fyp_score*0.3 + (likes/max(views,1))*0.3
- Underperforming: score < 5.0 OR fyp_score < 3.0
- Each candidate dict: signature, technique, engagement_rate, fyp_score, views, likes, comments, posted_at, reevaluate_reason
- generate_improved_version(signature) → new thread result using same technique
- generate_improved_version produces different signature from original
- Empty history returns [] (not error)

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_scheduler import ThreadScheduler
import asyncio
async def test():
    s = ThreadScheduler()
    await s.init()
    c = await s.reevaluate_previous_threads(min_age_days=7, top_n=5)
    print(f'returned type: {type(c).__name__}')
    print(f'count: {len(c)}')
asyncio.run(test())
"

BLOCKER_IF:
- Empty history causes crash instead of returning []

---

### CONTRACT #13: Add --scheduler CLI subcommand to scripts/threads_mode.py

WHAT:
Add scheduler subcommand to the threads_mode.py CLI for managing daily thread schedules and generating batches.

FILES:
READ: scripts/threads_mode.py (all 65 lines)
WRITE: scripts/threads_mode.py (add scheduler subcommand group)
RUN: python scripts/threads_mode.py scheduler --help

DONE_WHEN:
- CLI accepts: scheduler status, scheduler generate [morning|afternoon|night|all], scheduler list, scheduler pause, scheduler resume
- scheduler status: shows next post time, posts remaining today, active windows
- scheduler generate morning: produces 3 threads, afternoon: 4, night: 2, all: 9
- scheduler generate output: shows each thread signature and technique
- scheduler list: shows last 10 threads with signature/technique/date
- scheduler pause/resume: toggles scheduler state in persistence
- Exit codes: 0 success, 1 error, 2 invalid argument
- All subcommands work without Telegram (pure CLI mode)

PROOF_FORMAT:
python scripts/threads_mode.py scheduler --help 2>&1 | head -20
echo "---status---"
python scripts/threads_mode.py scheduler status 2>&1 | head -10

BLOCKER_IF:
- --help missing subcommands
- Wrong exit code on invalid subcommand

---

### CONTRACT #14: Extend handlers/threads_mode.py with scheduler Telegram commands

WHAT:
Add Telegram /threads_scheduler command handlers in handlers/threads_mode.py for schedule status and batch generation.

FILES:
READ: handlers/threads_mode.py (all 210 lines)
WRITE: handlers/threads_mode.py (add new handlers)
RUN: python -c "from handlers.threads_mode import router; print([h.handler.__name__ for h in router.message_handlers])"

DONE_WHEN:
- @router.message(Command("threads_scheduler")) handler added
- /threads_scheduler status → formatted message with next post, posts today, window info
- /threads_scheduler generate morning/afternoon/night/all → generates and sends threads
- /threads_scheduler list → last 5 threads with inline preview (1/6 truncated)
- /threads_scheduler pause → pauses scheduler, confirms with message
- /threads_scheduler resume → resumes scheduler, confirms with message
- Generated threads sent as separate messages per post (1/6, 2/6, ...)
- build_threads_campaign_task() used for enrichment (existing logic preserved)
- is_allowed() check applied to all new commands

PROOF_FORMAT:
python -c "
from handlers.threads_mode import router
handlers = [h.handler.__name__ for h in router.message_handlers]
print('thread_scheduler in handlers:', 'cmd_threads_mode' in handlers or 'threads_mode' in str(handlers))
print('handler count:', len(handlers))
"

BLOCKER_IF:
- New handlers break existing /threads_mode command
- is_allowed check missing

---

### CONTRACT #15: Write integration test for scheduler + generator + persistence

WHAT:
Write integration test at `tests/test_rumahlabuh_scheduler.py` covering full scheduler loop: generate batch → store metrics → reevaluate → generate improved.

FILES:
READ: tools/rumahlabuh_thread_generator.py, tools/rumahlabuh_scheduler.py, tools/persistence.py
WRITE: tests/test_rumahlabuh_scheduler.py (new file, ~150 lines)
RUN: pytest tests/test_rumahlabuh_scheduler.py -x -v --asyncio-mode=auto 2>&1 | tail -25

DONE_WHEN:
- tests/test_rumahlabuh_scheduler.py exists
- TestThreadScheduler class with async tests
- test_generate_batch_morning produces 3 valid threads (pass ThreadValidator)
- test_generate_batch_all produces 9 threads total
- test_scheduler_stores_and_retrieves_metrics
- test_reevaluate_returns_list_or_empty
- test_improved_version_differs_from_original
- test_history_dedup_prevents_same_batch_duplicates
- Uses test DB (temp file or in-memory), cleanup after each test

PROOF_FORMAT:
pytest tests/test_rumahlabuh_scheduler.py -x -v --asyncio-mode=auto 2>&1 | tail -25

BLOCKER_IF:
- Tests use production legion.db
- Fixture setup failures

---

## BATCH 4: Regression Tests (Contracts 16–20)
**Dependencies**: BATCH 2 (contracts 6, 7, 8) must complete first
**Parallel**: All 5 test files can run simultaneously (independent)

---

### CONTRACT #16: Write test_rule_enforcement for ThreadValidator

WHAT:
Write regression test at `tests/test_rumahlabuh_thread_validator.py` covering all 20+ validation rules.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 317-450), tools/rumahlabuh_threads_v5.json (lines 47-166)
WRITE: tests/test_rumahlabuh_thread_validator.py (new file, ~200 lines)
RUN: pytest tests/test_rumahlabuh_thread_validator.py -x -v --asyncio-mode=auto 2>&1 | tail -30

DONE_WHEN:
- tests/test_rumahlabuh_thread_validator.py exists
- TestRuleEnforcement class with parameterized tests:
  - test_no_em_dash: "—" in post → error
  - test_no_caps_for_drama: "KOST" (3+ caps) → error (WiFi/AC/UMS/UNS allowed)
  - test_brand_only_in_post6: brand in post 5 → error
  - test_brand_max_1_per_thread: 2 mentions → error
  - test_pronoun_no_mixing: gue + aku in same thread → error
  - test_pronoun_no_kami: "kami" → error
  - test_no_unsourced_percentage: "75%" without allowed source → error
  - test_forbidden_opening: post starts "Hai yang lagi nyari kost" → error
  - test_no_blocked_english: "experience" in post → error
  - test_engagement_question_post5: post 5 no "?" → error
  - test_engagement_question_post6: post 6 no "?" → error
  - test_questions_post5_post6_different: same first question → error
  - test_no_non_latin_script: CJK char in post → error
  - test_max_hashtags_per_post: 4 hashtags → error
  - test_max_numbered_items_per_post: 5 numbered items → error
  - test_max_emoji_per_post: 3 emoji → error
  - test_structure_exact_6_posts: 5 posts → error
  - test_post_numbering_prefix: post doesn't start with "1/6" → error
  - test_no_duplicate_posts: identical post 1 and 2 → error
  - test_no_menakut_takuti: tone phrase "Jangan ulangi kesalahan mereka" → error
  - test_no_ai_formula: "Berikut adalah" → error
- Uses ThreadValidator directly, no network, no DB

PROOF_FORMAT:
pytest tests/test_rumahlabuh_thread_validator.py -x -v --asyncio-mode=auto 2>&1 | tail -30

BLOCKER_IF:
- Any test false negative (passes when should fail)
- Test relies on real-time date instead of mock

---

### CONTRACT #17: Write test_duplicate_prevention for HistoryStore

WHAT:
Write regression test at `tests/test_rumahlabuh_duplicate_prevention.py` verifying duplicate prevention within deduplication window.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 139-181)
WRITE: tests/test_rumahlabuh_duplicate_prevention.py (new file, ~100 lines)
RUN: pytest tests/test_rumahlabuh_duplicate_prevention.py -x -v --asyncio-mode=auto 2>&1 | tail -20

DONE_WHEN:
- tests/test_rumahlabuh_duplicate_prevention.py exists
- test_same_signature_blocked_within_window: same sig within 60 days → True from was_signature_used_recently
- test_different_signature_allowed: different sigs → all False
- test_signature_expires_after_window: 61 days → False (uses mock date)
- test_500_item_limit: after 500 items, oldest pruned (only 500 in memory)
- test_last_techniques_returns_recent: returns techniques from last 7 days
- test_empty_history_returns_no_recent: empty → []
- Uses temp JSON file, cleanup after each test

PROOF_FORMAT:
pytest tests/test_rumahlabuh_duplicate_prevention.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Tests modify production history.json
- Window expiry test takes too long (use mock date)

---

### CONTRACT #18: Write test_rotation_behavior for BlueprintGenerator

WHAT:
Write regression test at `tests/test_rumahlabuh_rotation.py` verifying technique rotation, 7-day avoidance, and seed reproducibility.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 247-269)
WRITE: tests/test_rumahlabuh_rotation.py (new file, ~100 lines)
RUN: pytest tests/test_rumahlabuh_rotation.py -x -v --asyncio-mode=auto 2>&1 | tail -20

DONE_WHEN:
- tests/test_rumahlabuh_rotation.py exists
- test_rotation_avoids_recent_technique: last 7 days excluded when rotation enabled
- test_rotation_wraps_around: after all techniques used, wraps to start
- test_weighted_selection_distributes: in 20 runs with equal weights, no technique > 60%
- test_rotation_disabled_uses_weights: rotation disabled → weighted selection
- test_seed_same_produces_same: seed=42 twice → same technique
- test_seed_different_produces_different: seed=42 vs 43 → different technique
- test_deterministic_date_same_output: same date on different days → same technique
- Uses BlueprintGenerator with temp history

PROOF_FORMAT:
pytest tests/test_rumahlabuh_rotation.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Tests use real date instead of mock date parameter
- Seed test non-deterministic (fails on re-run)

---

### CONTRACT #19: Write test_question_difference_checks

WHAT:
Write regression test at `tests/test_rumahlabuh_questions.py` verifying Q5/Q6 question difference requirement.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 55-58, 290-293, 417-424)
WRITE: tests/test_rumahlabuh_questions.py (new file, ~80 lines)
RUN: pytest tests/test_rumahlabuh_questions.py -x -v --asyncio-mode=auto 2>&1 | tail -20

DONE_WHEN:
- tests/test_rumahlabuh_questions.py exists
- test_post5_has_question: post 5 no "?" → fails validation
- test_post6_has_question: post 6 no "?" → fails validation
- test_post5_post6_question_text_different: same first question text → fails
- test_question_text_extraction: "Apa yang lo pikirin?" → "apa yang lo pikirin"
- test_different_phrasing_passes: "Apa?" vs "Menurut?" → passes
- test_same_phrasing_fails: identical phrasing in both → fails
- test_question_marks_in_middle: only first "?" counts for extraction
- Uses ThreadValidator directly

PROOF_FORMAT:
pytest tests/test_rumahlabuh_questions.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Test false negative (passes when questions same)
- Test false positive (fails when questions different)

---

### CONTRACT #20: Write test_brand_placement_enforcement

WHAT:
Write regression test at `tests/test_rumahlabuh_brand_placement.py` verifying brand placement rules.

FILES:
READ: tools/rumahlabuh_threads_v5.json (lines 47-53), tools/rumahlabuh_thread_generator.py (lines 342-354)
WRITE: tests/test_rumahlabuh_brand_placement.py (new file, ~80 lines)
RUN: pytest tests/test_rumahlabuh_brand_placement.py -x -v --asyncio-mode=auto 2>&1 | tail -20

DONE_WHEN:
- tests/test_rumahlabuh_brand_placement.py exists
- test_brand_allowed_in_post6: brand in post 6 → passes
- test_brand_forbidden_in_post5: brand in post 5 → fails
- test_brand_forbidden_in_post1: brand in post 1 → fails
- test_brand_max_1_per_thread: 2 mentions → fails
- test_brand_max_1_per_post: 2 mentions in post 1 → fails
- test_brand_name_exact: "rumahlabuh.com" passes, "rumahlabuh" fails
- test_no_other_brand_names: "rumah123.com" → fails
- Uses ThreadValidator directly, no DB

PROOF_FORMAT:
pytest tests/test_rumahlabuh_brand_placement.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Brand in post 5 not caught
- Max per thread not enforced

---

## BATCH 5: Integration + Polish + Documentation (Contracts 21–25)
**Dependencies**: All BATCH 1-4 contracts must complete first

---

### CONTRACT #21: Write end-to-end test for full generate → validate → store pipeline

WHAT:
Write end-to-end integration test at `tests/test_rumahlabuh_e2e.py` covering complete pipeline.

FILES:
READ: tools/rumahlabuh_thread_generator.py, tools/rumahlabuh_scheduler.py, tools/persistence.py
WRITE: tests/test_rumahlabuh_e2e.py (new file, ~100 lines)
RUN: pytest tests/test_rumahlabuh_e2e.py -x -v --asyncio-mode=auto 2>&1 | tail -25

DONE_WHEN:
- tests/test_rumahlabuh_e2e.py exists
- test_generate_valid_thread_passes_validation: generate_fresh_thread() → no errors
- test_generate_stores_metrics: save_history=True → metrics in DB
- test_generate_returns_complete_result: all required fields present
- test_multiple_generations_are_unique: 5 runs → 5 different signatures
- test_generate_with_seed_is_reproducible: same seed → same signature
- test_invalid_thread_rejected: artificially bad thread → validation errors
- Uses test DB/temp files, cleanup after

PROOF_FORMAT:
pytest tests/test_rumahlabuh_e2e.py -x -v --asyncio-mode=auto 2>&1 | tail -25

BLOCKER_IF:
- E2E test uses production DB or files
- Test isolation failures

---

### CONTRACT #22: Verify backward compatibility for existing CLI entry

WHAT:
Run existing CLI entry `python tools/rumahlabuh_thread_generator.py` and verify unchanged behavior.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 513-525)
WRITE: None (read-only verification)
RUN: python tools/rumahlabuh_thread_generator.py 2>&1 | head -20

DONE_WHEN:
- python tools/rumahlabuh_thread_generator.py runs without error
- Output shows "Generated thread:" and 6 posts labeled 1/6 through 6/6
- Output shows "Pronouns:", "Technique:", "Signature:"
- save_history=True is default (unchanged)
- No new required arguments added
- Output format unchanged

PROOF_FORMAT:
python tools/rumahlabuh_thread_generator.py 2>&1 | grep -E "(Generated thread|/6|Pronouns|Technique|Signature)"

BLOCKER_IF:
- CLI output format changed (breaking change)
- save_history default changed

---

### CONTRACT #23: Finalize CLI --scheduler subcommand and verify all subcommands

WHAT:
Finalize all scheduler CLI subcommands and verify complete help output.

FILES:
READ: scripts/threads_mode.py (from CONTRACT #13)
WRITE: scripts/threads_mode.py (finalize)
RUN: python scripts/threads_mode.py scheduler --help && python scripts/threads_mode.py scheduler status

DONE_WHEN:
- python scripts/threads_mode.py scheduler --help shows: status, generate, list, pause, resume
- scheduler status shows schedule info (or empty state)
- scheduler list shows recent threads (or empty message)
- All error cases return exit code 2
- Empty/invalid subcommand shows help

PROOF_FORMAT:
python scripts/threads_mode.py scheduler --help 2>&1
echo "---status---"
python scripts/threads_mode.py scheduler status 2>&1 | head -10

BLOCKER_IF:
- --help does not show all subcommands
- Invalid subcommand wrong exit code

---

### CONTRACT #24: Update wiki docs with new architecture

WHAT:
Create architecture document at `.wiki/tools/rumahlabuh-thread-system-architecture.md`.

FILES:
READ: .wiki/tools/threads-viral-secret-sauce.md (architecture reference)
WRITE: .wiki/tools/rumahlabuh-thread-system-architecture.md (new file, ~100 lines)
RUN: ls -la .wiki/tools/rumahlabuh-thread-system-architecture.md

DONE_WHEN:
- .wiki/tools/rumahlabuh-thread-system-architecture.md exists
- Contains module map: rumahlabuh_thread_generator.py, rumahlabuh_scheduler.py, rumahlabuh_price_validator.py, persistence.py (thread tables), viral_thread_playbook.py, threads_mode_control.py
- Describes data flow: scheduler → generator → validator → analytics → survey → price_validator
- Lists config files: rumahlabuh_threads_v5.json, rumahlabuh_thread_blueprints.json, rumahlabuh_facts.json, rumahlabuh_thread_history.json
- Describes posting schedule: morning(3), afternoon(4), night(2)
- Contains frontmatter: title, tags, created date
- Cross-links to existing guides

PROOF_FORMAT:
ls -la .wiki/tools/rumahlabuh-thread-system-architecture.md && head -25 .wiki/tools/rumahlabuh-thread-system-architecture.md

BLOCKER_IF:
- File not created
- Missing frontmatter

---

### CONTRACT #25: Run full test suite and produce summary report

WHAT:
Run complete test suite and produce summary report showing pass/fail counts.

FILES:
READ: All test files from CONTRACTS 15-21
WRITE: tests/rumahlabuh_test_summary.txt (temp output)
RUN: pytest tests/test_rumahlabuh_*.py -v --asyncio-mode=auto --tb=short 2>&1 | tee tests/rumahlabuh_test_summary.txt

DONE_WHEN:
- All tests pass: N passed, 0 failed, 0 errors
- Summary saved to tests/rumahlabuh_test_summary.txt
- Skipped tests documented with reason
- If failures: specific test name and assertion reported
- Final: "ALL TESTS PASSED" or specific failures listed

PROOF_FORMAT:
pytest tests/test_rumahlabuh_*.py --asyncio-mode=auto -q 2>&1 | tail -10
echo "===summary==="
cat tests/rumahlabuh_test_summary.txt | tail -10

BLOCKER_IF:
- Any test failures
- Test suite crashes without producing report

---

## Execution Order

### Serial (must run in sequence within batch):
- BATCH 1: All 5 contracts can run in parallel (independent files)
- BATCH 2: 6, 7, 8 in parallel; 9, 10 sequential after 1, 2 complete
- BATCH 3: 11, 12 sequential after 1 complete; 13, 14 sequential after 11, 12; 15 after 13, 14
- BATCH 4: All 5 tests in parallel (independent test files)
- BATCH 5: 21 after all BATCH 2-4 complete; 22 after 21; 23 after 22; 24 after 23; 25 final gate

### Parallel groups:
- BATCH 1: Contracts 1, 2, 3, 4, 5 → all parallel (different files)
- BATCH 2: Contracts 6, 7, 8 → parallel (same file, different methods)
- BATCH 4: Contracts 16, 17, 18, 19, 20 → all parallel (independent test files)

### Final gate:
- CONTRACT #25: Full test suite (must pass before task is complete)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Persistence DB schema conflicts | M | H | New tables with new names only |
| Price validator web scraping blocked | M | M | Falls back to webfetch |
| Thread generator seed non-determinism | L | H | Run CONTRACT #6 seed test first |
| Regression tests false negatives | M | H | Explicit assertions, not "no crash" |
| Scheduler time zone issues | M | M | Use zoneinfo, test WIB explicitly |
| Existing CLI broken | L | H | CONTRACT #22 is gate before generator changes |
| Analytics DB writes fail silently | M | L | All analytics fire-and-forget with try/except |
| Test DB isolation failure | M | M | Use temp files, cleanup, never production DB |
