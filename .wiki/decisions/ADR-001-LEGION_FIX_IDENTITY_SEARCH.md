---
title: Adr 001 Legion Fix Identity Search
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Bashara asked: "Bisa cari info bashara aina tuh siapa ga?"'
wikilinks: []
confidence: medium
source: research
---
Bashara asked: "Bisa cari info bashara aina tuh siapa ga?"  
Legion responded with three separate failures:

1. **Amnesia**: Said "no idea who Bashara Aina is" — `.wiki/` content never injected into system prompt
2. **Language contamination**: "好奇" (Chinese "curious") leaked into Indonesian response  
3. **No self-search**: Said "tidak tahu" instead of automatically searching the web
---


## Decision

Implement three sequential fixes, each with verification tests.

---

## FIX 1: Wiki Not Injected

### Subtask 1A → @worker
**File**: `core/wiki_loader.py` (create)  
**Action**: Create module with `load_wiki_context()` and `get_bashara_identity_context()`  
**Verify**: `python -c "from core.wiki_loader import load_wiki_context, get_bashara_identity_context; assert len(load_wiki_context()) > 100; print('OK')"`

### Subtask 1B → @worker  
**File**: `core/system_prompt_builder.py` (modify)  
**Action**: Wire `load_wiki_context()` and `get_bashara_identity_context()` into `build_full_system_prompt()` — inject BEFORE task context at line ~190  
**Verify**: `python -c "from core.system_prompt_builder import build_full_system_prompt; p = build_full_system_prompt(''); assert 'Bashara Aina' in p; print('OK')"`

### Subtask 1C → @worker
**File**: `.wiki/profiles/bashara-aina.md` (create)  
**Action**: Create with full identity from BASHARA-MASTER-PROFILE.md plus fix-specific rules  
**Verify**: `ls .wiki/profiles/bashara-aina.md`

### Subtask 1D → @worker
**Action**: Run Fix 1 verification tests  
**Verify**: All tests pass

---

## FIX 2: Chinese Language Contamination

### Subtask 2A → @worker
**File**: `core/character_enforcer.py` (modify)  
**Action**: Add `has_non_allowed_script()`, `strip_non_allowed_script()`, `enforce_language()` functions with CJK/Arabic detection  
**Verify**: `python -c "from core.character_enforcer import enforce_language; r = enforce_language('kamu好奇吗'); assert '好奇' not in r and 'penasaran' in r; print('OK')"`

### Subtask 2B → @worker
**File**: `SOUL.md` (modify)  
**Action**: Add LANGUAGE RULES section with explicit Chinese character prohibition  
**Verify**: `grep -A5 'LANGUAGE RULES' SOUL.md`

### Subtask 2C → @worker
**File**: `core/character_enforcer.py` (modify)  
**Action**: Wire `enforce_language()` into response pipeline — add to `enforce_character()` function  
**Verify**: `python -c "from core.character_enforcer import enforce_character; r = enforce_character('test好奇response'); assert '好奇' not in r; print('OK')"`

### Subtask 2D → @worker
**Action**: Check config for Chinese-leaking models (deepseek/qwen/yi)  
**Verify**: `grep -rn "deepseek\|qwen\|yi-\|glm" config/ .env*` — report findings

### Subtask 2E → @worker
**Action**: Run Fix 2 verification tests  
**Verify**: All tests pass

---

## FIX 3: No Web Search

### Subtask 3A → @worker
**File**: `core/self_awareness_gate.py` (create)  
**Action**: Create module with `should_search_instead()`, `get_search_trigger_message()`, `build_search_query_from_message()`  
**Verify**: `python -c "from core.self_awareness_gate import should_search_instead; assert should_search_instead('tidak tahu', 'siapa bashara'); print('OK')"`

### Subtask 3B → @worker
**File**: `core/self_awareness_gate.py` + response pipeline (modify)  
**Action**: Wire gate into response pipeline (likely in llm_client.py or task_orchestrator.py)  
**Verify**: `grep -n "should_search_instead\|self_awareness_gate" core/ llm_client.py`

### Subtask 3C → @worker
**File**: `SOUL.md` (modify)  
**Action**: Add SEARCH BEFORE ADMITTING IGNORANCE section  
**Verify**: `grep -A5 'SEARCH BEFORE ADMITTING' SOUL.md`

### Subtask 3D → @worker
**File**: `tools/search_tool.py` (verify/exist)  
**Action**: Check if `web_search()` exists and works; if not, create with DuckDuckGo fallback  
**Verify**: `python -c "import asyncio; from tools.search_tool import web_search; print(asyncio.run(web_search('test')))"`

### Subtask 3E → @worker
**Action**: Run Fix 3 verification tests  
**Verify**: All tests pass

---

## FINAL

### Integration Test → @reviewer
**Action**: Run full integration test verifying all three fixes  
**Verify**: All checks pass, then report to user

---

## Consequence

After this fix, repeating the query "Bisa cari info bashara aina tuh siapa ga" should produce:
1. Legion knows who Bashara is (from wiki injection)
2. No Chinese characters in response
3. Legion searches web automatically before admitting ignorance