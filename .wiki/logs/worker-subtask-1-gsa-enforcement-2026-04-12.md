---
title: Worker Subtask 1 Gsa Enforcement 2026 04 12
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**File Modified:** `core/character_enforcer.py`'
wikilinks: []
confidence: medium
source: research
---
# Subtask 1: GSA Enforcement — COMPLETED

**Date:** 2026-04-12  
**Agent:** @worker  
**File Modified:** `core/character_enforcer.py`

## Changes Made

### 1. Added GSA Lists (after `_FALLBACK_FORBIDDEN`)
- `GSA_BANNED_OPENERS` — 9 opener patterns: "iya, ", "ya, ", "ok, ", "oke, ", "baik, ", "tentu, ", "pastinya, ", "benar, ", "tepat, "
- `GSA_BANNED_CLOSERS` — 5 closer patterns: "kalau ada pertanyaan", "jangan ragu untuk", "semoga membantu", "silakan hubungi", "apakah ada yang ingin"
- `GSA_BANNED_PHRASES` — 19 phrases covering generic motivasi, filler akademis, corporate speak, AI generic

### 2. Added `enforce_gsa_structure()` Function
- Strips banned openers (capitalizes result after removal)
- Strips banned closers (line-level filtering)
- Returns stripped text

### 3. Integrated into `enforce_character()`
- Step 2 now applies GSA banned phrases (after _FORBIDDEN_PATTERNS)
- Step 6 calls `enforce_gsa_structure()` after opener patterns
- Step numbers renumbered accordingly (5→7, etc.)

### 4. Built `_GSA_BANNED_PATTERNS` at module level (compiled regex)

## Verification

**Smoke test:**
```
python -c "from core.character_enforcer import enforce_character, enforce_gsa_structure; print('OK')"
→ OK
```

**GSA structure enforcement test:**
```
Input:  'iya, kamu pasti bisa\nsemoga membantu'
Output: 'Kamu pasti bisa'
```

**Full test suite:** 305 passed, 1 warning (unrelated requests warning)