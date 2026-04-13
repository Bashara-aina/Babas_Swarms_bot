---
## Summary

---
GSA Voice implementation is substantially correct with 305/305 tests passing. However, one code bug was found in `enforce_gsa_structure()` that must be fixed before merge.
---


## ✅ Passed

### Code Quality
- [x] All new code has proper type hints (`MessageContext` enum, `get_gsa_injection()`, `classify_message_context()`, `enforce_gsa_structure()`)
- [x] No hardcoded API keys, passwords, or secrets
- [x] Async functions properly declared (N/A — no new async functions added)
- [x] No use of `time.sleep()` or threading
- [x] No unused imports in `gsa_voice.py` (only `Enum` from `enum` module)
- [x] `system_prompt_builder.py` correctly imports from `core.gsa_voice`

### Security
- [x] No new API keys or secrets added
- [x] Input validation: `classify_message_context()` handles empty/None strings implicitly (returns ANALYTICAL by default)

### GSA Voice Integrity
- [x] Banned openers/closers lists match spec (LEGION_VOICE_UPGRADE.md lines 354-366)
- [x] `enforce_gsa_structure()` correctly strips banned openers and closers (except for leading whitespace edge case)
- [x] `MessageContext` enum has all 6 required values: TECHNICAL, EMOTIONAL, ANALYTICAL, REVIEW, CASUAL, STRATEGIC
- [x] GSA injection appears in system prompt AFTER SOUL context (confirmed at position 4457 in prompt)
- [x] `SystemPromptBuilder.build()` does NOT include GSA injection — this is the documented limitation per ADR-002 Risk #3

### Test Coverage
- [x] All 3 GSA smoke tests pass:
  - Banned phrases removed: PASS
  - Banned openers stripped: PASS
  - Context classification (4 tests): ALL PASS
  - GSA injection in prompt: PASS
- [x] Full pytest suite: **305 passed**, 0 failed

### Documentation
- [x] `.wiki/decisions/adr-002-gsa-voice-implementation.md` exists
- [x] `.wiki/logs/planner-gsa-voice-2026-04-12.md` exists
- [x] `.wiki/logs/worker-subtask-*-2026-04-12.md` logs exist (6 worker subtask logs)
- [x] `.wiki/gsa-voice-spec.md` created with correct frontmatter (title, domain, impact_score, last_updated, injects_into, tokens_estimated)

---

## ⚠️ Warnings

### 1. ADR notes known limitation (acceptable)
**File:** `system_prompt_builder.py` lines 244-335

The `SystemPromptBuilder.build()` method (class-based prompt builder) does NOT include GSA injection. The ADR-002 explicitly documents this as Risk #3 with mitigation: "After Subtask 3, evaluate whether SystemPromptBuilder.build() also needs GSA injection."

**Assessment:** This is a documented trade-off, not a bug. The functional `build_full_system_prompt()` (function-based) is the primary entry point and correctly includes GSA injection.

### 2. Name reference inconsistency (cosmetic)
**File:** `core/gsa_voice.py` line 78

The GSA_SYSTEM_INJECTION template says "Anwar Baswedan's" but the ADR-002 references "Anwar Ibrahim" (line 17). However, `.wiki/gsa-voice-spec.md` line 19 also uses "Anwar Baswedan's", so the implementation is internally consistent.

**Assessment:** The three figures are Gita Wirjawan, Sandiaga Uno, and Anwar Baswedan's. "Anwar Ibrahim" in the ADR appears to be an error. No fix needed for implementation.

---

## ❌ Blockers

### 1. `enforce_gsa_structure()` fails when input has leading whitespace before banned opener

**File:** `core/character_enforcer.py`
**Lines:** 124-135
**Severity:** HIGH — produces malformed output

**Bug Description:**
When input has leading whitespace before a banned opener (e.g., `"  iya, ada masalah"`), the function returns `", ada masalah"` instead of `"ada masalah"`.

**Root Cause (line 126-131):**
```python
def enforce_gsa_structure(text: str) -> str:
    lower = text.lower().strip()  # lower is stripped
    for opener in GSA_BANNED_OPENERS:
        if lower.startswith(opener):  # comparison is on stripped version
            text = text[len(opener):].lstrip()  # but slicing uses ORIGINAL text
            text = text[0].upper() + text[1:] if text else text
```

The problem: `lower` is stripped for comparison, but `text` is not. When `"  iya, ada masalah"` is processed:
1. `lower = "iya, ada masalah"` (stripped) → `lower.startswith("iya, ")` → True
2. `text = text[5:] = ", ada masalah"` (sliced from ORIGINAL with leading spaces)
3. `text.lstrip() = ", ada masalah"` (lstrip removes comma too since it's considered whitespace-adjacent)
4. `text[0].upper()` on comma → `","` (unchanged)

**Recommended Fix:**
```python
def enforce_gsa_structure(text: str) -> str:
    """Strip banned openers and closers from GSA-style responses."""
    # Strip leading whitespace first so opener detection is clean
    stripped_text = text.lstrip()
    lower = stripped_text.lower()
    
    # Kill banned openers
    for opener in GSA_BANNED_OPENERS:
        if lower.startswith(opener):
            result = stripped_text[len(opener):].lstrip()
            if result:
                result = result[0].upper() + result[1:]
            return result if result else text  # fall back to original if empty
    
    # Kill banned closers
    lines = text.split("\n")
    filtered = [l for l in lines if not any(c in l.lower() for c in GSA_BANNED_CLOSERS)]
    return "\n".join(filtered).strip()
```

Or simpler (preserving original logic but fixing whitespace):
```python
def enforce_gsa_structure(text: str) -> str:
    """Strip banned openers and closers from GSA-style responses."""
    stripped = text.lstrip()  # strip leading whitespace first
    lower = stripped.lower()
    
    for opener in GSA_BANNED_OPENERS:
        if lower.startswith(opener):
            result = stripped[len(opener):].lstrip()
            if result:
                result = result[0].upper() + result[1:]
            return result
    
    # Kill banned closers
    lines = text.split("\n")
    filtered = [l for l in lines if not any(c in l.lower() for c in GSA_BANNED_CLOSERS)]
    return "\n".join(filtered).strip()
```

**Test Case:**
```python
assert enforce_gsa_structure("  iya, ada masalah") == "Ada masalah"  # Currently returns ", ada masalah"
```

---

## Test Results

```
pytest tests/ -x --asyncio-mode=auto -q
======================= 305 passed, 1 warning in 20.63s ========================
```

### GSA Smoke Tests
```
Test 1 - Banned phrases: PASS
Test 1b - Banned openers: PASS
Test 2 - Context [pusing nih thesis stuck]: PASS (expected emotional, got emotional)
Test 2 - Context [ada bug di handler]: PASS (expected technical, got technical)
Test 2 - Context [gimana menurut lo pasar proper]: PASS (expected analytical, got analytical)
Test 2 - Context [lagi ngopi]: PASS (expected casual, got casual)
Test 3 - GSA in prompt: PASS, validate: PASS
```

---

## Verdict

**BLOCKER MUST BE FIXED BEFORE MERGE**

The leading whitespace bug in `enforce_gsa_structure()` produces corrupted output. All other aspects of the implementation are correct and match the specification.

**Required Action:** Fix `enforce_gsa_structure()` to properly handle leading whitespace before banned openers.
