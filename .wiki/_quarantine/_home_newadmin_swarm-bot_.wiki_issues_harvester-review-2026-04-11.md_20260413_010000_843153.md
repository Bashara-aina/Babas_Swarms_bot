---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/issues/harvester-review-2026-04-11.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.843189"
}
---

# Review: Legion Daily Intelligence Harvester
**Reviewer:** @reviewer  
**Date:** 2026-04-11  
**Files Reviewed:** 17 (11 core modules, 1 entry point, 1 test file, 2 wiki files, 2 config files)

---

## Summary: NEEDS FIXES BEFORE COMMIT

**CRITICAL issues found: 3**  
**MODERATE issues found: 5**  
**MINOR issues found: 4**

---

## ❌ CRITICAL ISSUES (Must fix before merge)

### 1. CRITICAL: Blocking I/O in Async Context
**File:** `core/daily_harvester/topic_budget.py`  
**Lines:** 23-31 (`_load_topic_weights`), 65 (`detect_active_topics`)

```python
def _load_topic_weights() -> dict[str, Any]:  # ← NOT async
    ...
    return json.loads(TOPIC_WEIGHTS_PATH.read_text(encoding="utf-8"))  # ← BLOCKING
```

`_load_topic_weights()` is a synchronous function using `Path.read_text()` (blocking I/O) inside an `async` function `detect_active_topics()`.

**Fix:** Either make `_load_topic_weights` async with `aiofiles`, or call `json.loads` on the result of an async file read.

---

### 2. CRITICAL: Syntax Error — Missing Closing Parenthesis
**File:** `core/daily_harvester/wiki_indexer.py`  
**Lines:** 48, 92, 149, 204

```python
title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), f.stem
# Missing closing ) here                                                       ^

title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), md_file.stem
# Missing closing ) here                                                       ^
```

These are generator expressions passed to `next()` that are missing the closing `)`. The code will fail with `SyntaxError` at import time or when these functions are called.

**Fix:** Add closing `)` to all four occurrences.

---

### 3. CRITICAL: Weight Formula Does Not Match ADR Specification
**File:** `core/daily_harvester/topic_budget.py`  
**Line:** 82

**ADR says (ADR-HARVESTER-001.md line 28):**
```
mention_count × 2 + commit_count × 3 + (days_since)^0.5
```

**Implementation:**
```python
score = base_weight + mention_count * 2 + commit_count * 3 + math.sqrt(days_since)
#        ^^^^^^^^^^^^ THIS IS NOT IN THE SPEC
```

The spec does NOT include `base_weight` as an additive term. The current implementation adds `base_weight` (which can be up to 18 per TOPIC_WEIGHTS.json) as an extra additive term, which will heavily skew scores. For example:
- Topic A: weight=18, mention=0, commit=0, days=1 → score = 18 + 0 + 0 + 1 = **19**
- Topic B: weight=5, mention=1, commit=0, days=1 → score = 5 + 2 + 0 + 1 = **8**

But per the ADR formula:
- Topic A: 0×2 + 0×3 + 1^0.5 = **1**
- Topic B: 1×2 + 0×3 + 1^0.5 = **3**

**Fix:** Remove `base_weight +` from the formula on line 82.

---

## ⚠️ MODERATE ISSUES (Should fix)

### 4. MODERATE: Timezone Inconsistency in `_days_since`
**File:** `core/daily_harvester/topic_budget.py`  
**Lines:** 34-41

```python
def _days_since(ts: str) -> float:
    then = datetime.fromisoformat(ts.replace("Z", "+00:00"))  # ← parses as UTC
    now = datetime.now(then.tzinfo) if then.tzinfo else datetime.now()  # ← uses LOCAL timezone
```

When `ts` is UTC (e.g., `"2026-04-11T00:00:00+00:00"`), `then.tzinfo` is set, so `now = datetime.now(then.tzinfo)` uses UTC. But `TOPIC_WEIGHTS.json` stores `"2026-04-10"` as WIB (UTC+7), which `datetime.fromisoformat` interprets as local time in whatever timezone Python runs in. This creates incorrect elapsed day calculations.

**Fix:** Use timezone-aware `datetime.now(timezone.utc)` consistently and convert all timestamps to UTC before comparison.

---

### 5. MODERATE: `utcnow()` Deprecated in Python 3.12+
**Files:** Multiple
- `wiki_storage.py` lines 132, 209, 230, 243, 256
- `harvest_pipeline.py` lines 64, 141, 176, 208
- `wiki_indexer.py` lines 52, 187, 220
- `topic_budget.py` line 112
- `morning_report.py` line 94 (comment)

`datetime.utcnow()` is deprecated in Python 3.12+. Use `datetime.now(timezone.utc)` instead.

---

### 6. MODERATE: Missing Stdlib Import in `swarm_debate.py`
**File:** `core/daily_harvester/swarm_debate.py`  
**Lines:** 46, 83, 126, 195

```python
import json as _json  # ← imported INSIDE the try block, after the await chat() call
```

`import json as _json` is used inside the `try` block after the `await chat()` call, but `json` is a stdlib module that should be at the top of the file. The inline import works but violates the project's own import order rule (stdlib → third-party → local).

**Fix:** Move `import json` to the top of the file with other stdlib imports.

---

### 7. MODERATE: Contradiction Resolver Uses Undocumented 1.5x Citation Threshold
**File:** `core/daily_harvester/source_strategy.py`  
**Lines:** 114-117

```python
if new_citations > existing_citations * 1.5:  # ← Where does 1.5 come from?
    return ("SUPERSEDE", f"More citations ({new_citations} vs {existing_citations})")
if existing_citations > new_citations * 1.5:
    return ("EXISTING_WINS", f"Higher citations ({existing_citations})")
```

The ADR specifies "higher citations win" but doesn't mention a 1.5× threshold. This means a new entry with 10 citations vs an existing 9 citations (10% difference) would NOT trigger the citation rule under the current implementation, but the ADR intent seems to suggest it should.

**Fix:** Either document the 1.5× threshold in a code comment, or adjust to a more aggressive threshold like 1.2× if the intent is to catch most citation differences.

---

### 8. MODERATE: Morning Report Uses Markdown Without Telegram Parse Mode
**File:** `core/daily_harvester/morning_report.py`  
**Lines:** 40, 44, 72, 77, 81, 85, 94

The report uses `*bold*` markdown syntax:
```python
sections.append("🌅 *Legion Daily Intel*")  # ← Telegram won't render this as bold
```

If Telegram bot doesn't use `parse_mode=MarkdownV2` or `parse_mode=HTML`, these asterisks will be shown literally.

**Fix:** Either use HTML tags (`<b>text</b>`) or document that Telegram must be configured with `parse_mode=MarkdownV2`.

---

## ✅ PASSED CHECKS

### Correctness
- [x] TypedDicts have all required fields (`CandidateInfo`, `SwarmVerdict`, `WikiEntry`, etc.)
- [x] Type hints present on all public functions
- [x] Topic allocation normalizes to 100 total slots (tested)
- [x] Naming conventions follow `[PREFIX]-[NNN]-[slug]-[DATE].md` (tested)
- [x] Slot bounds enforced: min 3, max 35 (tested)
- [x] `surprise_discoveries` correctly reserved at 5 slots

### Security
- [x] No hardcoded API keys or secrets
- [x] No unsanitized user input in subprocess calls (cron_setup.py uses safe string construction)
- [x] No file path traversal risks (REPO_ROOT derived from `Path(__file__).resolve()`)
- [x] Cron command injection mitigated via `re.escape` for prefix pattern in `_next_seq`; repo_root is safe Path object

### Style
- [x] f-strings only throughout (no `.format()` or `%` formatting)
- [x] Docstrings on all public classes and methods
- [x] Import order mostly correct (stdlib → third-party → local)
- [x] No commented-out dead code

### API Integration
- [x] Uses `llm_client.chat()` instead of calling litellm directly
- [x] Uses `httpx.AsyncClient` for async HTTP
- [x] Uses `aiofiles` for async file I/O

### Swarm Debate Logic
- [x] All 4 agents have distinct system prompts (Prosecutor, Defender, FactChecker, Judge)
- [x] Debate order correct: Prosecutor → Defender → FactChecker → Judge
- [x] Verdict types match spec: ACCEPT, ACCEPT_WITH_CAVEAT, SUPERSEDE, REJECT, NEEDS_MORE_RESEARCH
- [x] Contradiction resolver priority: gov wins → newer date → higher citations → ADD_BOTH

### Morning Report
- [x] Capped at 3000 characters (tested)
- [x] Capped at 5 topics (MAX_TOPICS = 5)
- [x] Generates topic budget visualization with bar chart

### Cron
- [x] Correct UTC time (21:00 UTC = 04:00 WIB+1)
- [x] Uses `%` escaping in date format (`\%Y\%m\%d`)
- [x] Cron label for idempotent install/remove

---

## 🔍 MINOR ISSUES (Nice to have)

### 9. MINOR: `_slugify` Can Produce Duplicate Slugs
**File:** `core/daily_harvester/wiki_storage.py`  
**Line:** 60-64

```python
def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", title)
    slug = re.sub(r"\s+", "-", slug)
    return slug[:40].lower().rstrip("-")
```

Two entries with titles "UMP 2026 Jakarta" and "UMP-2026 Jakarta" will produce the same slug: "ump-2026-jakarta". Combined with `_next_seq`, this is not a correctness bug (sequence numbers differ), but the slug portion becomes redundant.

### 10. MINOR: `TopicEvolution` Methods Are Static But Could Be Instance Methods
**File:** `core/daily_harvester/topic_evolution.py`  
**Lines:** 17, 39, 68

All methods are `@staticmethod`. This is fine but unusual for a class that maintains state. Consider whether these should read from/write to TOPIC_WEIGHTS.json directly (they don't currently).

### 11. MINOR: `HARVEST_LOG` Not Created If Missing
**File:** `core/daily_harvester/wiki_storage.py`  
**Lines:** 254-258

`append_harvest_log` opens `self.harvest_log` with mode `"a"` but doesn't ensure the parent directory exists. If `WIKI_ROOT.parent` doesn't exist, this will fail.

**Fix:** Ensure `self.wiki_root.parent` directory exists before appending, or use `dir_path.mkdir(parents=True, exist_ok=True)` somewhere.

### 12. MINOR: `test_pipeline_ordering` Makes Real LLM Calls
**File:** `tests/test_daily_harvester.py`  
**Line:** 240

`test_pipeline_ordering` calls `pipeline.run_full_pipeline()` which in turn calls `run_debate_batch`, which makes real LLM calls. This test is not isolated and could be flaky or expensive.

**Fix:** Mock the `swarm_debate` module or add a `--real-llm` flag to opt-in.

---

## 📋 EXACT FIXES REQUIRED

| # | File | Line(s) | Fix |
|---|------|---------|-----|
| 1 | `topic_budget.py` | 23-31 | Make `_load_topic_weights` async with `aiofiles` |
| 1 | `topic_budget.py` | 65 | `await _load_topic_weights()` |
| 2 | `wiki_indexer.py` | 48 | Add `)` after `f.stem` |
| 2 | `wiki_indexer.py` | 92 | Add `)` after `f.stem` |
| 2 | `wiki_indexer.py` | 149 | Add `)` after `md_file.stem` |
| 2 | `wiki_indexer.py` | 204 | Add `)` after `md_file.stem` |
| 3 | `topic_budget.py` | 82 | Change to `score = mention_count * 2 + commit_count * 3 + math.sqrt(days_since)` |
| 4 | `topic_budget.py` | 34-41 | Use timezone-aware datetime throughout |
| 5 | Multiple | Multiple | Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` |
| 6 | `swarm_debate.py` | 4-7 | Add `import json` at top of file |
| 7 | `source_strategy.py` | 114-117 | Add comment explaining 1.5× threshold, or adjust threshold |
| 8 | `morning_report.py` | All | Use HTML `<b>` tags or document parse_mode requirement |
| 11 | `wiki_storage.py` | 254-258 | Ensure parent directory exists before `aiofiles.open` |

---

## VERDICT

**READY FOR COMMIT** — NO  
**NEEDS FIXES BEFORE COMMIT** — YES

The 3 CRITICAL issues (blocking I/O, syntax errors, wrong weight formula) must be fixed before this code can run at all. The MODERATE issues should also be addressed before merge as they represent correctness issues (timezone handling) or will cause unexpected behavior (markdown in Telegram).

All 3 CRITICAL issues are in `topic_budget.py` and `wiki_indexer.py` — fixing these two files unblocks the entire module.
