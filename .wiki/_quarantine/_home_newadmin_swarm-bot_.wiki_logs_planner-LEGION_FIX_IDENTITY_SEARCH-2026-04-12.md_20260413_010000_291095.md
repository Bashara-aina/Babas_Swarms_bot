---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/planner-LEGION_FIX_IDENTITY_SEARCH-2026-04-12.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.291115"
}
---

# PLANNER LOG: LEGION_FIX_IDENTITY_SEARCH
## Date: 2026-04-12
## Task: Execute full three-agent pipeline for fixing identity search issues

---

## FILES READ

1. `/home/newadmin/swarm-bot/LEGION_FIX_IDENTITY_SEARCH.md` - 757 lines
   - Contains 3 fix plans for wiki injection, Chinese character stripping, and web search gate

2. `/home/newadmin/swarm-bot/SOUL.md` - 83 lines
   - Already has LANGUAGE RULES (line 63) and SEARCH BEFORE ADMITTING IGNORANCE (line 71)

3. `/home/newadmin/swarm-bot/LEGION_MASTER.md` - 617 lines
   - Context on Legion architecture and current implementation status

4. `/home/newadmin/swarm-bot/core/system_prompt_builder.py` - 376 lines
   - Already has wiki_loader wired in (lines 91-100)

---

## THREE FIX PLANS IDENTIFIED

### FIX 1: .wiki NOT INJECTED — Legion amnesia about Bashara
- **Root Cause**: .wiki/ exists but never loaded/injected into system prompt
- **Solution**:
  - 1A: Create `core/wiki_loader.py` with `load_wiki_context()` and `get_bashara_identity_context()`
  - 1B: Wire into `core/system_prompt_builder.py`
  - 1C: Create `.wiki/profiles/bashara-aina.md`
  - 1D: Verification tests

### FIX 2: CHINESE CHARACTERS — language contamination
- **Root Cause**: Model leaks Chinese when low-confidence, no language enforcement
- **Solution**:
  - 2A: Add `enforce_language()` to `core/character_enforcer.py` with CJK detection
  - 2B: Add LANGUAGE RULES to SOUL.md
  - 2C: Wire `enforce_language()` into `enforce_character()`
  - 2D: Check for Chinese-leaking models
  - 2E: Verification tests

### FIX 3: NO WEB SEARCH — must search before saying "tidak tahu"
- **Root Cause**: No "I don't know → search first" logic
- **Solution**:
  - 3A: Create `core/self_awareness_gate.py`
  - 3B: Wire into response pipeline (llm_client/__init__.py)
  - 3C: Add SEARCH rule to SOUL.md
  - 3D: Verify/create `tools/web_search.py`
  - 3E: Verification tests

---

## EXISTING IMPLEMENTATION STATUS CHECK

| Component | File | Status |
|-----------|------|--------|
| wiki_loader | `core/wiki_loader.py` | ✅ EXISTS (117 lines) |
| character_enforcer (CJK) | `core/character_enforcer.py` | ✅ EXISTS (572 lines, lines 24-91) |
| self_awareness_gate | `core/self_awareness_gate.py` | ✅ EXISTS (97 lines) |
| web_search | `tools/web_search.py` | ✅ EXISTS (38 lines) |
| wiki wired | `system_prompt_builder.py` | ✅ WIRED (lines 91-100) |
| SOUL.md rules | `SOUL.md` | ✅ COMPLETE (lines 63-83) |
| self_awareness wired | `llm_client/__init__.py` | ✅ WIRED (lines 1257-1264) |

**All three fixes already implemented and verified.**

---

## VERIFICATION RESULTS

### FIX 1: Wiki Loader
```
Wiki length: 17354 chars ✅
Identity context: "Bashara Aina" and "cekwajar" present ✅
System prompt: 27863 chars, contains Bashara identity and wiki ✅
```

### FIX 2: Character Enforcer
```
has_non_allowed_script('好奇') → True ✅
has_non_allowed_script('halo') → False ✅
enforce_language('kamu好奇吗') → 'kamupenasaran?' ✅
enforce_character('test好奇response') → 'Testpenasaranresponse' ✅
```

### FIX 3: Self-Awareness Gate
```
should_search_instead('Gak punya info...Bashara Aina', 'cari info bashara') → True ✅
should_search_instead('Ini kode perlu diperbaiki', 'ada bug') → False ✅
build_search_query_from_message('cari info bashara aina') → 'bashara aina adalah siapa profil' ✅
```

### FINAL INTEGRATION TEST
```
Wiki: 17354 chars, mentions Bashara ✅
Language: '好奇' stripped, replaced with 'penasaran' ✅
Search gate: triggers for Bashara query ✅
Profile: .wiki/profiles/bashara-aina.md exists ✅
```

### PYTEST
```
305 tests passed, 1 warning in 26.05s ✅
```

---

## CONCLUSION

All three fix plans have been verified as COMPLETE:
1. **FIX 1**: .wiki injected via wiki_loader.py → system_prompt_builder.py
2. **FIX 2**: Chinese characters stripped via enforce_language() in character_enforcer.py
3. **FIX 3**: Self-awareness gate intercepts "I don't know" and triggers web search

The implementation was already done in prior sessions. This planner session verified all components are working correctly.

---

## NEXT STEPS

1. Report completion to user
2. No additional ADR needed (ADR-001-LEGION_FIX_IDENTITY_SEARCH.md already exists)
3. The original query "Bisa cari info bashara aina tuh siapa ga" should now work correctly
