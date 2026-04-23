## CONTRACT ARCHITECTURE — Rumahlabuh Thread System Refactor

All contracts use this format:
- WHAT: one imperative sentence
- FILES: READ (existing), WRITE (new/modified), RUN (bash commands)
- DONE_WHEN: measurable criteria
- PROOF_FORMAT: exact command to verify
- BLOCKER_IF: stop conditions

---

## BATCH 1: Architecture + Data Layer (Contracts 1–5)

### CONTRACT #1: Create rumahlabuh_scheduler.py scheduler engine

WHAT:
Create a new scheduler engine at `tools/rumahlabuh_scheduler.py` that schedules daily thread generation across morning/afternoon/night windows, stores schedule state in the existing persistence DB, and supports reevaluation of previous threads based on engagement metrics.

FILES:
READ: tools/persistence.py (lines 32-47), tools/persistence.py (lines 126-148)
WRITE: tools/rumahlabuh_scheduler.py (new file, ~300 lines)
RUN: python -c "from tools.rumahlabuh_scheduler import ThreadScheduler; print('ok')"

DONE_WHEN:
- tools/rumahlabuh_scheduler.py exists with ThreadScheduler class
- class has schedule_window() method accepting hour range and count
- class has record_engagement() accepting signature + metrics (views, likes, comments)
- class has get_reevaluate_candidates() returning threads above performance threshold
- class has generate_batch() producing N thread signatures for a window
- uses persistence.Persistence for all storage (no new DB files)
- async methods with proper aiosqlite usage matching persistence.py patterns

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_scheduler import ThreadScheduler
import asyncio
async def test():
    s = ThreadScheduler()
    await s.init()
    w = s.schedule_window('morning', (7, 12), count=3)
    print(f'windows: {w}')
    print('ok')
asyncio.run(test())
" → output contains "windows:"

BLOCKER_IF:
- persistence.py init_db() schema not accessible for extension
- scheduled_tasks table doesn't support thread-specific fields

---

### CONTRACT #2: Add thread analytics tables to persistence.py

WHAT:
Add four new async functions to persistence.py for thread-specific analytics: store_thread_metrics, get_thread_analytics, update_thread_fyp_score, and list_recent_threads.

FILES:
READ: tools/persistence.py (lines 1-30, 677-708)
WRITE: tools/persistence.py (add new functions before line 677, extend Persistence class)
RUN: python -c "from tools.persistence import store_thread_metrics, get_thread_analytics, update_thread_fyp_score, list_recent_threads; print('ok')"

DONE_WHEN:
- Added `thread_analytics` table with columns: id, signature, posted_at, views, likes, comments, fyp_score, engagement_rate, technique, used_in_batch
- Added `thread_survey_responses` table with columns: id, signature, question_key, response, created_at
- store_thread_metrics(sig, posted_at, views, likes, comments, technique, batch) async function exists
- get_thread_analytics(sig) -> dict exists
- update_thread_fyp_score(sig, score) async function exists
- list_recent_threads(limit) -> list[dict] exists
- survey_submit(sig, question_key, response) async function exists
- survey_get_responses(sig) -> list[dict] exists
- Persistence class has all 6 new methods
- __all__ list includes all 6 new functions
- Tests pass: pytest tests/test_persistence.py -x -q (if exists) or manual verification

PROOF_FORMAT:
python -c "
import asyncio
from tools.persistence import Persistence
async def test():
    p = Persistence()
    await p.init()
    await p.store_thread_metrics('test_sig_abc123', 1700000000.0, 1500, 89, 23, 'edukasi', 'morning_batch_1')
    result = await p.get_thread_analytics('test_sig_abc123')
    print(f'analytics: {result}')
    await p.survey_submit('test_sig_abc123', 'q1', 'yes')
    resp = await p.survey_get_responses('test_sig_abc123')
    print(f'survey responses: {resp}')
asyncio.run(test())
" → output contains "analytics:" and "survey responses:"

BLOCKER_IF:
- asyncio runtime not available
- DB schema conflict with existing tables

---

### CONTRACT #3: Create rumahlabuh_price_validator.py for rumahlabuh.com price scraping

WHAT:
Create a price validation module at `tools/rumahlabuh_price_validator.py` that validates price data by first browsing rumahlabuh.com (selecting room, ordering, filling check-in/check-out) before showing real prices.

FILES:
READ: .claude/scripts/rumahlabuh-facts.md (all lines)
WRITE: tools/rumahlabuh_price_validator.py (new file, ~200 lines)
RUN: python -c "from tools.rumahlabuh_price_validator import PriceValidator, format_price_reply; print('ok')"

DONE_WHEN:
- PriceValidator class with async scrape_property(url) method
- PriceValidator class with async select_room_and_order(room_type) method  
- PriceValidator class with async fill_check_io(date_range) method
- PriceValidator class with get_validated_price() returning price breakdown
- format_price_reply(price_data) function returning Indonesian-format price string
- Uses firecrawl_firecrawl_browser_create + firecrawl_browser_execute for browser automation
- Falls back to webfetch if browser fails
- PriceValidator raises PriceValidationError with specific message if validation chain fails
- All facts must come from rumahlabuh.com or Google Maps (not hardcoded)
- Class has get_fact_for_content(fact_key) -> str method that uses FactsExtractor pattern

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_price_validator import PriceValidator, PriceValidationError
print('PriceValidator imported successfully')
print('PriceValidationError:', PriceValidationError)
" → output shows both imported without error

BLOCKER_IF:
- firecrawl browser tools not available in environment
- rumahlabuh.com not accessible

---

### CONTRACT #4: Extend FactsExtractor with structured data and config-driven facts path

WHAT:
Refactor FactsExtractor in `tools/rumahlabuh_thread_generator.py` to use a config-driven facts path and structured data accessors, storing all extracted facts in a typed dataclass.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 109-137)
WRITE: tools/rumahlabuh_thread_generator.py (modify FactsExtractor class)
RUN: python -c "from tools.rumahlabuh_thread_generator import FactsExtractor, load_facts; fe = FactsExtractor(load_facts()); print(fe.get_price_min()); print(fe.get_city())"

DONE_WHEN:
- FactsExtractor.__init__ accepts (facts_text: str, facts_path: Path | None = None)
- FactsExtractor stores all extracted facts in @dataclass ThreadFacts with fields: price_min, price_max, city, area, facilities, room_types, parking_capacity, contact_wa, contact_website, is_pet_friendly, has_joglo, has_dapur
- All 6 data-reading methods use ThreadFacts dataclass fields (not regex on raw text)
- facts_path is read from rumahlabuh_threads_v5.json config: source_facts field
- FactsExtractor.get_fact(key: str) -> str method for generic lookup
- FactsExtractor.all_facts() -> dict returns full fact dict
- FactsExtractor refreshes from file when file modified time changes (lazy reload)

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import FactsExtractor, load_facts, load_config
cfg = load_config()
facts = load_facts()
fe = FactsExtractor(facts)
print('price_min:', fe.get_price_min())
print('city:', fe.get_city())
print('facilities count:', len(fe.all_facts()['facilities']))
" → output shows price_min, city, and facilities count

BLOCKER_IF:
- rumahlabuh_threads_v5.json source_facts field not accessible
- Facts text format changed

---

### CONTRACT #5: Create rumahlabuh_facts.json structured facts data file

WHAT:
Create a new structured JSON data file at `tools/rumahlabuh_facts.json` containing all verified property facts in machine-readable format, replacing the markdown facts file for programatic access.

FILES:
READ: .claude/scripts/rumahlabuh-facts.md (all lines)
WRITE: tools/rumahlabuh_facts.json (new file)
RUN: cat tools/rumahlabuh_facts.json | python -c "import json,sys; d=json.load(sys.stdin); print('keys:', list(d.keys()))"

DONE_WHEN:
- tools/rumahlabuh_facts.json exists and is valid JSON
- File contains "labuh_biru" and "labuh_banyu" top-level keys
- labuh_biru has: address, room_types (list with name/daily/weekly/biweekly/monthly/deposit fields), facilities (list), parking_capacity, is_pet_friendly, has_joglo
- labuh_banyu has: address, room_types, facilities, parking_capacity, is_pet_friendly, has_dapur
- File contains "shared_facts": distance_ums, wifi_speed, contact_wa, website, booking_url
- Facts match rumahlabuh-facts.md exactly (no fabrication)
- Update rumahlabuh_threads_v5.json source_facts to point to rumahlabuh_facts.json

PROOF_FORMAT:
cat tools/rumahlabuh_facts.json | python -c "
import json, sys
d = json.load(sys.stdin)
print('labuh_biru rooms:', len(d['labuh_biru']['room_types']))
print('labuh_banyu rooms:', len(d['labuh_banyu']['room_types']))
print('shared_facts keys:', list(d['shared_facts'].keys()))
print('price_min:', d['shared_facts']['monthly_price_min'])
"

BLOCKER_IF:
- JSON data does not match rumahlabuh-facts.md exactly

---

## BATCH 2: Core Refactor — Generator + Validator + History (Contracts 6–10)

### CONTRACT #6: Add deterministic seed/reproducibility to BlueprintGenerator

WHAT:
Add optional seed parameter to BlueprintGenerator.generate() for deterministic, reproducible thread output, and store seed in result dict.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 271-309)
WRITE: tools/rumahlabuh_thread_generator.py (modify generate method signature and result dict)
RUN: python -c "from tools.rumahlabuh_thread_generator import generate_fresh_thread, BlueprintGenerator; r1 = generate_fresh_thread(seed=None); r2 = generate_fresh_thread(seed=None); r3 = generate_fresh_thread(seed=42); r4 = generate_fresh_thread(seed=42); print('same None:', r1['signature'] == r2['signature']); print('same 42:', r3['signature'] == r4['signature']); print('diff seeds:', r1['signature'] != r3['signature'])"

DONE_WHEN:
- BlueprintGenerator.generate(today: date | None = None, seed: int | None = None) accepts seed parameter
- When seed is None: uses random.Random(f"{today.isoformat()}:{attempt}") behavior (existing)
- When seed is provided: uses random.Random(seed) for all random choices within generate()
- Result dict includes "seed": int | None field
- Same seed + same today produces identical thread (signature match)
- generate_fresh_thread(save_history=True, seed=None) signature updated with seed param
- CLI in __main__ block respects --seed argument if provided

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import generate_fresh_thread
r1 = generate_fresh_thread(seed=12345)
r2 = generate_fresh_thread(seed=12345)
r3 = generate_fresh_thread(seed=67890)
print('seed 12345 signature:', r1['signature'][:12])
print('seed 67890 signature:', r3['signature'][:12])
print('identical with same seed:', r1['signature'] == r2['signature'])
print('different with different seed:', r1['signature'] != r3['signature'])
"

BLOCKER_IF:
- Same seed produces different output between runs (RNG state leakage)

---

### CONTRACT #7: Add graceful fallback to pool exhaustion in BlueprintGenerator

WHAT:
Add graceful fallback logic in BlueprintGenerator._build_context() so that when a pool is empty or exhausted, it falls back to a sensible default rather than failing.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 206-238)
WRITE: tools/rumahlabuh_thread_generator.py (modify _build_context and _safe_choice usage)
RUN: python tools/rumahlabuh_thread_generator.py 2>&1 | head -5

DONE_WHEN:
- _safe_choice(rng, [], fallback) returns fallback (unchanged behavior)
- All pool lookups in _build_context use fallback values
- Pool exhaustion does not cause KeyError or IndexError
- When all pools are empty, generator still produces valid output from hardcoded fallbacks
- Generator records "pool_exhausted" in result metadata when fallback used
- ThreadValidator still passes when fallback used (no new validation errors)
- Documentation comment added explaining fallback behavior

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import BlueprintGenerator, load_config, load_facts
cfg = load_config()
# Test with minimal pools (empty them artificially)
cfg_test = cfg.copy()
cfg_test['generator']['blueprint_file'] = 'nonexistent_blueprint.json'
try:
    gen = BlueprintGenerator(cfg_test, load_facts())
except Exception as e:
    print(f'Expected error with bad path: {type(e).__name__}')

# Test graceful handling
from pathlib import Path
gen = BlueprintGenerator(cfg, load_facts())
result = gen.generate()
print('success:', result.get('success'))
print('technique:', result.get('technique'))
" → shows graceful handling

BLOCKER_IF:
- Empty pool causes IndexError or KeyError instead of fallback

---

### CONTRACT #8: Add configurable weight overrides to BlueprintGenerator

WHAT:
Add support for runtime weight configuration in BlueprintGenerator so technique weights can be overridden via config without editing blueprints JSON.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 247-269)
WRITE: tools/rumahlabuh_thread_generator.py (modify _select_technique and load_config defaults)
RUN: python -c "from tools.rumahlabuh_thread_generator import BlueprintGenerator, load_config, load_facts; cfg = load_config(); cfg['generator']['technique_weights'] = {'edukasi': 10, 'showcase_soft': 0}; gen = BlueprintGenerator(cfg, load_facts()); result = [gen.generate()['technique'] for _ in range(20)]; print('edukasi count:', result.count('edukasi')); print('showcase_soft count:', result.count('showcase_soft'))"

DONE_WHEN:
- load_config() reads technique_weights from generator section if present
- BlueprintGenerator._select_technique respects weight overrides when present
- Weight override must be dict[str, int] mapping technique name -> weight
- Weight of 0 excludes technique from random selection
- Weight override only affects _select_technique when weights dict is non-empty
- Original blueprint weights unchanged (read-only override)
- Validation passes when using overridden weights

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import BlueprintGenerator, load_config, load_facts
cfg = load_config()
# Force only edukasi
cfg['generator']['technique_weights'] = {'edukasi': 100, 'relatable_story': 0, 'hot_take': 0, 'fake_controversy': 0, 'showcase_soft': 0}
gen = BlueprintGenerator(cfg, load_facts())
results = [gen.generate()['technique'] for _ in range(10)]
print('All edukasi?', all(t == 'edukasi' for t in results))
print('Results:', results)
"

BLOCKER_IF:
- Weight 0 still selects the technique in rotation

---

### CONTRACT #9: Add thread analytics integration to BlueprintGenerator and ThreadValidator

WHAT:
Connect BlueprintGenerator and ThreadValidator to the new analytics system, recording generated threads with metrics placeholders and validating against FYP scoring rules.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 271-315, 317-450)
WRITE: tools/rumahlabuh_thread_generator.py (modify mark_used and add analytics hooks)
RUN: python -c "from tools.rumahlabuh_thread_generator import generate_fresh_thread; r = generate_fresh_thread(); print('signature:', r['signature'][:12]); print('success:', r['success'])"

DONE_WHEN:
- BlueprintGenerator.mark_used(result) calls store_thread_metrics() from persistence
- Recorded metrics include: signature, technique, batch_name, posted_at=0 (placeholder until posted)
- ThreadValidator.validate() accepts optional context: dict with fyp_history for validation context
- ThreadValidator flags threads with signature in fyp_history with score > 7 as "high_performer" in metadata
- generate_fresh_thread() returns result with "batch" field when scheduled batch is active
- generate_fresh_thread() returns result with "analytics_pending" bool field
- No analytics calls block generation (fire-and-forget with try/except)

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_thread_generator import generate_fresh_thread
import asyncio
async def test():
    r = generate_fresh_thread()
    print('success:', r['success'])
    print('signature present:', bool(r.get('signature')))
asyncio.run(test())
"

BLOCKER_IF:
- Analytics calls make generation slower (must be async fire-and-forget)
- Generation fails when analytics DB is unavailable

---

### CONTRACT #10: Add thread survey methods to persistence

WHAT:
Add survey system methods to persistence.py for collecting and analyzing FYP-worthy post determinations from user responses.

FILES:
READ: tools/persistence.py (lines 403-449)
WRITE: tools/persistence.py (add survey methods)
RUN: python -c "from tools.persistence import survey_submit, survey_get_responses, survey_stats; print('ok')"

DONE_WHEN:
- survey_submit(signature, question_key, response) stores response linked to thread signature
- survey_get_responses(signature) -> list[dict] returns all responses for a thread
- survey_stats(since_hours=24) -> dict returns aggregate stats (response_count, fyp_determinations)
- survey_get_fyp_worthy(signature) -> bool returns True if majority responses say "yes" to FYP question
- Survey questions stored: q_fyp_worthy (yes/no), q_engagement_level (low/medium/high), q_improve_point (free text)
- All survey methods are async
- Persistence class has survey methods added
- __all__ updated

PROOF_FORMAT:
python -c "
import asyncio
from tools.persistence import survey_submit, survey_get_responses, survey_stats
async def test():
    sig = 'test_survey_sig_999'
    await survey_submit(sig, 'q_fyp_worthy', 'yes')
    await survey_submit(sig, 'q_fyp_worthy', 'no')
    await survey_submit(sig, 'q_fyp_worthy', 'yes')
    resp = await survey_get_responses(sig)
    stats = await survey_stats()
    print(f'responses for sig: {len(resp)}')
    print(f'stats: {stats}')
asyncio.run(test())
"

BLOCKER_IF:
- Survey storage conflicts with existing schema

---

## BATCH 3: Scheduler System + CLI + Telegram (Contracts 11–15)

### CONTRACT #11: Build thread schedule builder in rumahlabuh_scheduler.py

WHAT:
Implement the schedule_window method in ThreadScheduler that returns optimal posting times for morning (3 posts), afternoon (4 posts), and night (2 posts) windows based on WIB timezone.

FILES:
READ: tools/rumahlabuh_scheduler.py (from CONTRACT #1)
WRITE: tools/rumahlabuh_scheduler.py (implement schedule_window method)
RUN: python -c "from tools.rumahlabuh_scheduler import ThreadScheduler; import asyncio; s = asyncio.run(ThreadScheduler().init()); print(s)"

DONE_WHEN:
- ThreadScheduler.schedule_window(window_name: str, hour_range: tuple[int, int], count: int) -> list[datetime]
- morning window returns 3 datetime objects between 07:00-12:00 WIB
- afternoon window returns 4 datetime objects between 12:00-19:00 WIB
- night window returns 2 datetime objects between 19:00-22:00 WIB
- Times are spaced relatively evenly within the window
- Times are in Asia/Jakarta timezone (WIB, UTC+7)
- schedule_window called by generate_batch to get actual posting timestamps
- generate_batch(window, count) returns list of (thread_result, scheduled_time) tuples

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_scheduler import ThreadScheduler
import asyncio
async def test():
    s = ThreadScheduler()
    await s.init()
    morning = s.schedule_window('morning', (7, 12), count=3)
    afternoon = s.schedule_window('afternoon', (12, 19), count=4)
    night = s.schedule_window('night', (19, 22), count=2)
    print(f'morning ({len(morning)} posts):', [(t.hour, t.minute) for t in morning])
    print(f'afternoon ({len(afternoon)} posts):', [(t.hour, t.minute) for t in afternoon])
    print(f'night ({len(night)} posts):', [(t.hour, t.minute) for t in night])
asyncio.run(test())
"

BLOCKER_IF:
- Posts not spaced within window
- Timezone not WIB

---

### CONTRACT #12: Add reevaluate_previous_threads method to scheduler

WHAT:
Implement reevaluate_previous_threads in ThreadScheduler that retrieves past generated threads from history, fetches their analytics metrics, and returns ranked candidates for re-generation based on underperformance.

FILES:
READ: tools/rumahlabuh_scheduler.py (from CONTRACT #1)
WRITE: tools/rumahlabuh_scheduler.py (implement reevaluate_previous_threads)
RUN: python -c "from tools.rumahlabuh_scheduler import ThreadScheduler; print('ok')"

DONE_WHEN:
- reevaluate_previous_threads(min_age_days=7, top_n=5) -> list[dict] returns underperforming threads
- Method fetches from thread_analytics using persisted history
- Ranking score = engagement_rate * 0.4 + fyp_score * 0.3 + (likes / max(views,1)) * 0.3
- Underperforming = threads with score below 5.0 OR fyp_score below 3.0
- Each candidate dict contains: signature, technique, engagement_rate, fyp_score, views, likes, comments, posted_at
- Method updates rank reason in thread_analytics.reevaluate_reason field
- generate_improved_version(signature) returns new thread using same technique but different pool selections

PROOF_FORMAT:
python -c "
from tools.rumahlabuh_scheduler import ThreadScheduler
import asyncio
async def test():
    s = ThreadScheduler()
    await s.init()
    candidates = await s.reevaluate_previous_threads(min_age_days=7, top_n=5)
    print(f'candidates returned: {len(candidates)}')
    print(f'type: {type(candidates)}')
asyncio.run(test())
"

BLOCKER_IF:
- Scheduler crashes on empty history (should return empty list, not error)

---

### CONTRACT #13: Add --scheduler CLI subcommand to scripts/threads_mode.py

WHAT:
Add scheduler subcommand to the threads_mode.py CLI for managing daily thread schedules, viewing next posting times, and manually triggering batch generation.

FILES:
READ: scripts/threads_mode.py (all lines)
WRITE: scripts/threads_mode.py (add scheduler subcommand)
RUN: python scripts/threads_mode.py scheduler --help

DONE_WHEN:
- CLI now accepts: scheduler status, scheduler generate [morning|afternoon|night|all], scheduler list, scheduler pause, scheduler resume
- scheduler status shows: next scheduled post, posts remaining today, active batches
- scheduler generate morning produces 3 threads for morning window
- scheduler generate all produces 9 threads (3+4+2) 
- scheduler list shows last 10 generated threads with signature and technique
- Output format: each thread shows "1/6: {first_50_chars}..." truncation
- All subcommands work without Telegram (pure CLI)
- Exit codes: 0 success, 1 error, 2 invalid argument

PROOF_FORMAT:
python scripts/threads_mode.py scheduler status 2>&1 | head -10
python scripts/threads_mode.py scheduler --help 2>&1 | head -15

BLOCKER_IF:
- CLI crashes when persistence not initialized
- Missing subcommands return wrong exit code

---

### CONTRACT #14: Extend handlers/threads_mode.py with scheduler commands

WHAT:
Add Telegram command handlers in handlers/threads_mode.py for /threads_scheduler status and /threads_scheduler generate subcommands.

FILES:
READ: handlers/threads_mode.py (all lines)
WRITE: handlers/threads_mode.py (add new command handlers)
RUN: python -c "from handlers.threads_mode import router; print('handlers imported ok')"

DONE_WHEN:
- @router.message(Command("threads_scheduler")) handler added
- /threads_scheduler status → sends formatted schedule status (next post time, posts today, window)
- /threads_scheduler generate morning/afternoon/night/all → generates and sends threads to user
- /threads_scheduler list → sends last 5 generated threads with inline preview
- /threads_scheduler pause → pauses scheduler
- /threads_scheduler resume → resumes scheduler
- Generated threads sent as individual messages per post (1/6, 2/6, ...)
- Uses build_threads_campaign_task() for enrichment (existing logic preserved)
- is_allowed() check applied to all commands

PROOF_FORMAT:
python -c "from handlers.threads_mode import router; print('router handlers:', [h.handler.__name__ for h in router.message_handlers])"

BLOCKER_IF:
- New handlers break existing /threads_mode command
- is_allowed check not applied

---

### CONTRACT #15: Write integration test for scheduler + generator + persistence

WHAT:
Write an integration test at `tests/test_rumahlabuh_scheduler.py` that tests the full scheduler loop: generate batch → store metrics → reevaluate → generate improved version.

FILES:
READ: tools/rumahlabuh_thread_generator.py, tools/rumahlabuh_scheduler.py, tools/persistence.py
WRITE: tests/test_rumahlabuh_scheduler.py (new file, ~150 lines)
RUN: pytest tests/test_rumahlabuh_scheduler.py -x -v --asyncio-mode=auto

DONE_WHEN:
- tests/test_rumahlabuh_scheduler.py exists
- Test class: TestThreadScheduler
- test_generate_batch_morning produces 3 threads, all valid (pass ThreadValidator)
- test_generate_batch_all produces 9 threads total
- test_scheduler_stores_metrics after generation, metrics are stored in DB
- test_reevaluate_returns_candidates finds underperforming threads
- test_improved_version_differs produces different signature for same technique
- test_history_dedup prevents duplicate signatures in same batch
- All tests use in-memory or temp DB (not production DB)
- Tests clean up after themselves (delete test records)

PROOF_FORMAT:
pytest tests/test_rumahlabuh_scheduler.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Tests use production legion.db instead of test DB
- Tests fail with fixture errors

---

## BATCH 4: Regression Tests (Contracts 16–20)

### CONTRACT #16: Write test_rule_enforcement for ThreadValidator

WHAT:
Write regression test at `tests/test_rumahlabuh_thread_validator.py` covering all 20+ validation rules from rumahlabuh_threads_v5.json.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 317-450), tools/rumahlabuh_threads_v5.json (lines 47-166)
WRITE: tests/test_rumahlabuh_thread_validator.py (new file, ~200 lines)
RUN: pytest tests/test_rumahlabuh_thread_validator.py -x -v --asyncio-mode=auto

DONE_WHEN:
- tests/test_rumahlabuh_thread_validator.py exists
- TestRuleEnforcement class with parameterized tests for each rule:
  - test_no_em_dash: posts with "—" return error
  - test_no_caps_for_drama: posts with "KOST" (3+ letters all caps) return error (allowed: WiFi, AC, CCTV, UMS, UNS)
  - test_brand_only_in_post6: brand in post 5 returns error
  - test_brand_max_1_per_thread: brand appears twice returns error
  - test_pronoun_no_mixing: mixed gue/aku returns error
  - test_pronoun_no_kami: "kami" in post returns error
  - test_no_unsourced_percentage: "75%" without allowed source returns error
  - test_forbidden_opening: post starting "Hai yang lagi nyari kost" returns error
  - test_no_blocked_english: "experience" in post returns error
  - test_engagement_question_post5: post 5 without "?" returns error
  - test_engagement_question_post6: post 6 without "?" returns error
  - test_questions_post5_post6_different: same question text in posts 5+6 returns error
  - test_no_non_latin_script: post with CJK/Hiragana character returns error
  - test_max_hashtags_per_post: 4 hashtags in post returns error
  - test_max_numbered_items_per_post: 5 numbered items in post returns error
  - test_max_emoji_per_post: 3 emoji in post returns error
  - test_structure_exact_6_posts: 5 posts returns error
  - test_post_numbering_prefix: post not starting with "1/6" returns error
  - test_no_duplicate_posts: identical post 1 and post 2 returns error
  - test_no_menakut_takuti: tone phrase "Jangan ulangi kesalahan mereka" returns error
  - test_no_ai_formula: blocked AI formula "Berikut adalah" returns error
- Each test has descriptive docstring
- Tests use ThreadValidator directly (no network, no DB)

PROOF_FORMAT:
pytest tests/test_rumahlabuh_thread_validator.py -x -v --asyncio-mode=auto 2>&1 | tail -30

BLOCKER_IF:
- Any test passes when it should fail (false negative)
- Any test fails when rule not violated (false positive)

---

### CONTRACT #17: Write test_duplicate_prevention for HistoryStore

WHAT:
Write regression test at `tests/test_rumahlabuh_duplicate_prevention.py` verifying that HistoryStore prevents duplicate thread signatures within the configured deduplication window.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 139-181)
WRITE: tests/test_rumahlabuh_duplicate_prevention.py (new file, ~100 lines)
RUN: pytest tests/test_rumahlabuh_duplicate_prevention.py -x -v --asyncio-mode=auto

DONE_WHEN:
- tests/test_rumahlabuh_duplicate_prevention.py exists
- test_same_signature_blocked_within_window: same signature appended twice within 60 days → second append returns False from was_signature_used_recently
- test_different_signature_allowed: different signatures all pass
- test_signature_expires_after_window: after 61 days same signature allowed
- test_500_item_limit: after 500 items, oldest items pruned (only 500 in memory)
- test_append_updates_items_count: append increases items count
- test_last_techniques_returns_recent: last_techniques returns techniques used within window
- test_empty_history_returns_no_recent: empty history returns empty list from last_techniques
- Uses temp JSON file for HistoryStore (not production history)
- Cleanup after each test

PROOF_FORMAT:
pytest tests/test_rumahlabuh_duplicate_prevention.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Tests modify production history file
- Window expiry test takes too long (use mock date)

---

### CONTRACT #18: Write test_rotation_behavior for BlueprintGenerator technique rotation

WHAT:
Write regression test at `tests/test_rumahlabuh_rotation.py` verifying technique rotation behavior, including 7-day avoidance, weighted selection, and seed reproducibility.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 247-269)
WRITE: tests/test_rumahlabuh_rotation.py (new file, ~100 lines)
RUN: pytest tests/test_rumahlabuh_rotation.py -x -v --asyncio-mode=auto

DONE_WHEN:
- tests/test_rumahlabuh_rotation.py exists
- test_rotation_avoids_recent: when rotation enabled, last 7 days of techniques excluded
- test_rotation_wraps_around: after all techniques exhausted, rotation wraps to beginning
- test_weighted_selection_distributes: with equal weights, distribution is reasonably spread (no single technique > 60% in 20 runs)
- test_rotation_disabled_uses_weights: when rotation disabled, weighted random selection used
- test_seed_same_produces_same: seed=42 run twice produces identical technique
- test_seed_different_produces_different: seed=42 vs seed=43 produces different techniques
- test_deterministic_date_produces_same: same date run on different days produces same technique (when seed=None)
- Tests use BlueprintGenerator directly with temp history

PROOF_FORMAT:
pytest tests/test_rumahlabuh_rotation.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Rotation test relies on actual real-time date (use mock date)
- Seed test produces non-deterministic output

---

### CONTRACT #19: Write test_question_difference_checks for Q5/Q6 constraint

WHAT:
Write regression test at `tests/test_rumahlabuh_questions.py` verifying that posts 5 and 6 must have different question content and all required engagement questions are present.

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 55-58, 290-293, 417-424)
WRITE: tests/test_rumahlabuh_questions.py (new file, ~80 lines)
RUN: pytest tests/test_rumahlabuh_questions.py -x -v --asyncio-mode=auto

DONE_WHEN:
- tests/test_rumahlabuh_questions.py exists
- test_post5_has_question: thread where post 5 has no "?" fails validation
- test_post6_has_question: thread where post 6 has no "?" fails validation  
- test_post5_post6_question_text_different: same first-question text in posts 5 and 6 fails validation
- test_question_text_extraction: "Apa yang lo pikirin?" → extracts "apa yang lo pikirin"
- test_different_phrasing_passes: "Apa yang lo pikirin?" vs "Menurut lo?" passes (different first question text)
- test_same_phrasing_fails: same phrasing in both posts fails
- test_question_marks_in_middle_count: "Apakah ini - apakah itu?" → extracts "apakah ini" (first ? only)
- Tests use ThreadValidator directly

PROOF_FORMAT:
pytest tests/test_rumahlabuh_questions.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Test passes when questions are same (false negative)
- Test fails when questions are genuinely different (false positive)

---

### CONTRACT #20: Write test_brand_placement_enforcement

WHAT:
Write regression test at `tests/test_rumahlabuh_brand_placement.py` verifying brand placement rules: brand only in post 6, max 1 per thread, max 1 per post.

FILES:
READ: tools/rumahlabuh_threads_v5.json (lines 47-53), tools/rumahlabuh_thread_generator.py (lines 342-354)
WRITE: tests/test_rumahlabuh_brand_placement.py (new file, ~80 lines)
RUN: pytest tests/test_rumahlabuh_brand_placement.py -x -v --asyncio-mode=auto

DONE_WHEN:
- tests/test_rumahlabuh_brand_placement.py exists
- test_brand_allowed_in_post6: brand in post 6 passes
- test_brand_forbidden_in_post5: brand in post 5 fails validation
- test_brand_forbidden_in_post1: brand in post 1 fails validation
- test_brand_max_1_per_thread: 2 brand mentions in thread fails
- test_brand_max_1_per_post: 2 brand mentions in same post fails
- test_brand_name_exact_match: "rumahlabuh.com" passes, "rumahlabuh" (without .com) fails
- test_no_other_brand_names: "rumah123.com" (wrong) in post fails
- test_brand_in_cta_only: brand in CTA context (post 6) passes
- Uses ThreadValidator directly, no DB

PROOF_FORMAT:
pytest tests/test_rumahlabuh_brand_placement.py -x -v --asyncio-mode=auto 2>&1 | tail -20

BLOCKER_IF:
- Brand mentions in post 5 not caught
- Max per thread not enforced

---

## BATCH 5: Integration + Polish + Documentation (Contracts 21–25)

### CONTRACT #21: Write end-to-end test for full generate → validate → store pipeline

WHAT:
Write end-to-end integration test at `tests/test_rumahlabuh_e2e.py` covering the full pipeline: generate thread → validate → store metrics → retrieve analytics.

FILES:
READ: tools/rumahlabuh_thread_generator.py, tools/rumahlabuh_scheduler.py, tools/persistence.py
WRITE: tests/test_rumahlabuh_e2e.py (new file, ~100 lines)
RUN: pytest tests/test_rumahlabuh_e2e.py -x -v --asyncio-mode=auto

DONE_WHEN:
- tests/test_rumahlabuh_e2e.py exists
- test_generate_valid_thread_passes_validation: generate_fresh_thread() result passes validator with no errors
- test_generate_stores_metrics: after generation with save_history=True, metrics stored in DB
- test_generate_returns_complete_result: result dict has all required fields (success, thread, signature, technique, pronouns, date, seed)
- test_multiple_generations_are_unique: 5 generations produce 5 different signatures
- test_generate_with_seed_is_reproducible: same seed produces same signature on second call
- test_invalid_thread_rejected: artificially invalid thread fails validation
- All tests use test DB or temp files, cleanup after

PROOF_FORMAT:
pytest tests/test_rumahlabuh_e2e.py -x -v --asyncio-mode=auto 2>&1 | tail -25

BLOCKER_IF:
- E2E test creates files in production paths
- Test isolation failures (tests affect each other)

---

### CONTRACT #22: Verify backward compatibility for existing CLI entry

WHAT:
Run the existing CLI entry `python tools/rumahlabuh_thread_generator.py` and verify it still works exactly as before (unchanged behavior for save_history default).

FILES:
READ: tools/rumahlabuh_thread_generator.py (lines 513-525)
WRITE: None (read-only verification)
RUN: python tools/rumahlabuh_thread_generator.py 2>&1 | head -20

DONE_WHEN:
- python tools/rumahlabuh_thread_generator.py runs without error
- Output shows "Generated thread:" and 6 posts labeled 1/6 through 6/6
- Output shows "Pronouns:", "Technique:", "Signature:"
- --no-save flag works if added to CLI (or save_history=False behavior is preserved)
- generate_fresh_thread(save_history=True) is default behavior unchanged
- No new required arguments added to generate_fresh_thread()

PROOF_FORMAT:
python tools/rumahlabuh_thread_generator.py 2>&1 | grep -E "(Generated thread|Pronouns|Technique|Signature|/6)"

BLOCKER_IF:
- CLI output format changed (breaking)
- save_history default changed

---

### CONTRACT #23: Finalize CLI --scheduler subcommand and verify all subcommands

WHAT:
Finalize all scheduler CLI subcommands and verify complete help output matches CONTRACT #13 specification.

FILES:
READ: scripts/threads_mode.py (from CONTRACT #13)
WRITE: scripts/threads_mode.py (finalize subcommands)
RUN: python scripts/threads_mode.py scheduler --help && python scripts/threads_mode.py scheduler status

DONE_WHEN:
- python scripts/threads_mode.py scheduler --help shows all 5 subcommands: status, generate, list, pause, resume
- python scripts/threads_mode.py scheduler status shows schedule info (or empty state message)
- python scripts/threads_mode.py scheduler list shows recent threads or empty message
- All error cases return exit code 2 with descriptive error
- Empty/invalid subcommand shows help

PROOF_FORMAT:
python scripts/threads_mode.py scheduler --help 2>&1
echo "---"
python scripts/threads_mode.py scheduler status 2>&1

BLOCKER_IF:
- --help does not show all subcommands
- Invalid subcommand doesn't return exit code 2

---

### CONTRACT #24: Update wiki docs with new architecture

WHAT:
Update .wiki/tools/ directory with a new architecture document describing the refactored thread system: scheduler, analytics, survey, price validator, and generator modules.

FILES:
READ: .wiki/tools/threads-viral-secret-sauce.md (architecture reference)
WRITE: .wiki/tools/rumahlabuh-thread-system-architecture.md (new file, ~100 lines)
RUN: ls -la .wiki/tools/rumahlabuh-thread-system-architecture.md

DONE_WHEN:
- .wiki/tools/rumahlabuh-thread-system-architecture.md exists
- Document contains module map showing: rumahlabuh_thread_generator.py, rumahlabuh_scheduler.py, rumahlabuh_price_validator.py, persistence.py (thread tables), viral_thread_playbook.py, threads_mode_control.py
- Document describes data flow: scheduler → generator → validator → analytics → survey → price_validator
- Document lists all config files: rumahlabuh_threads_v5.json, rumahlabuh_thread_blueprints.json, rumahlabuh_facts.json, rumahlabuh_thread_history.json
- Document describes posting schedule: morning (3), afternoon (4), night (2) 
- Document contains frontmatter with title, tags, created date
- Document cross-links to existing guides: threads-viral-secret-sauce.md, threads-natural-language-guide.md

PROOF_FORMAT:
ls -la .wiki/tools/rumahlabuh-thread-system-architecture.md && head -20 .wiki/tools/rumahlabuh-thread-system-architecture.md

BLOCKER_IF:
- File not created (permission or path error)
- Missing frontmatter

---

### CONTRACT #25: Run full test suite and produce summary report

WHAT:
Run the complete test suite for all rumahlabuh thread system tests and produce a summary report showing pass/fail counts.

FILES:
READ: All generated test files from CONTRACTS 15-21
WRITE: tests/rumahlabuh_test_summary.txt (temp output)
RUN: pytest tests/test_rumahlabuh_*.py -v --asyncio-mode=auto --tb=short 2>&1 | tee tests/rumahlabuh_test_summary.txt

DONE_WHEN:
- All tests in test_rumahlabuh_*.py pass (0 failures, 0 errors)
- Summary shows: N passed, 0 failed, 0 errors
- Summary saved to tests/rumahlabuh_test_summary.txt
- Any skipped tests documented with reason
- If any tests fail, report specific test name and assertion
- Final report: "ALL TESTS PASSED" or specific failures listed

PROOF_FORMAT:
pytest tests/test_rumahlabuh_*.py --asyncio-mode=auto -q 2>&1 | tail -5
echo "---Summary---"
cat tests/rumahlabuh_test_summary.txt | tail -20

BLOCKER_IF:
- Any test failures (even 1)
- Test suite crashes without producing report

---

## Execution Order

Serial (must run in sequence):
- BATCH 1 (Contracts 1-5): Architecture/Data Layer first (all other contracts depend on these)
- BATCH 2 (Contracts 6-10): Core Refactor (depends on BATCH 1 contracts 1,2,4,5)
- BATCH 3 (Contracts 11-15): Scheduler + CLI (depends on BATCH 1 contracts 1,2 and BATCH 2 contracts 6,7,8,9)
- BATCH 4 (Contracts 16-20): Regression Tests (depends on BATCH 2 contracts 6,7,8 and BATCH 1 contract 4)
- BATCH 5 (Contracts 21-25): Integration + Docs (depends on all prior batches)

Parallel (can run simultaneously within batch):
- BATCH 1: Contracts 1, 2, 3, 4, 5 can run in parallel (independent files)
- BATCH 2: Contracts 6, 7, 8 can run in parallel (same file, different methods); 9, 10 depend on 1+2 so sequential to those
- BATCH 4: All 5 test files (16-20) are independent and can run in parallel

Final gate (must run last):
- CONTRACT #25: Full test suite (all 25 contracts must be complete)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Persistence DB schema conflicts | M | H | Add new tables with new names, don't modify existing tables |
| Price validator web scraping blocked | M | M | Falls back to webfetch, then to existing facts |
| Thread generator seed non-determinism | L | H | Run seed reproducibility test in CONTRACT #6 first |
| Regression tests false negatives | M | H | Each test has explicit assertions, not just "no crash" |
| Scheduler time zone issues | M | M | Use pendulum or zoneinfo, test WIB explicitly |
| Existing CLI broken by changes | L | H | CONTRACT #22 is gate before any contract that modifies generator |
| Analytics DB writes fail silently | M | L | All analytics are fire-and-forget with try/except |
| Test DB isolation failure | M | M | Use temp files and cleanup, never touch production DB |
