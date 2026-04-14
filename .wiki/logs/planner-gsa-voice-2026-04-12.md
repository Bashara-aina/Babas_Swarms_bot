---
title: Planner Gsa Voice 2026 04 12
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
summary: Implement GSA Voice — a communication style synthesis of three Indonesian
  figures (Gita Wirjawan, Sandiaga Uno, Anwar Ibrahim) into Legion's core personality
  system.
wikilinks: []
confidence: medium
source: research
---
# Planner Log — GSA Voice Implementation
Date: 2026-04-12

## Task Overview
Implement GSA Voice — a communication style synthesis of three Indonesian figures (Gita Wirjawan, Sandiaga Uno, Anwar Ibrahim) into Legion's core personality system.

## Task Decomposition

### Subtask 1: Update core/character_enforcer.py — add GSA enforcement
- **File(s)**: `core/character_enforcer.py`
- **Changes**:
  - Add `GSA_BANNED_OPENERS` list (iya, ya, ok, oke, baik, tentu, pastinya, benar, tepat)
  - Add `GSA_BANNED_CLOSERS` list (kalau ada pertanyaan, jangan ragu, semoga membantu, silakan hubungi, apakah ada yang ingin)
  - Add `enforce_gsa_structure()` function that strips banned openers/closers and returns cleaned text
- **Depends on**: None — standalone module update

### Subtask 2: Create core/gsa_voice.py — message context classification
- **File(s)**: `core/gsa_voice.py` (NEW FILE)
- **Changes**:
  - Create `MessageContext` enum (TECHNICAL, EMOTIONAL, ANALYTICAL, REVIEW, CASUAL, STRATEGIC)
  - Define `GSA_CONTEXT_KEYWORDS` dict mapping contexts to keyword lists
  - Define `GSA_SYSTEM_INJECTION` template string with GSA voice rules
  - Implement `get_gsa_injection(context)` function returning formatted injection
  - Implement `classify_message_context(text)` function for keyword-based classification
- **Depends on**: None — greenfield module

### Subtask 3: Wire gsa_voice.py into system_prompt_builder.py
- **File(s)**: `core/system_prompt_builder.py`
- **Changes**:
  - Import `classify_message_context` and `get_gsa_injection` from `core.gsa_voice`
  - In `build_full_system_prompt()`: after SOUL context (line 78-85), classify user message and inject GSA template
  - Insert GSA injection between SOUL context and core personality layers
- **Depends on**: Subtask 2 (gsa_voice.py must exist before import)

### Subtask 4: Update SOUL.md — add VOICE section
- **File(s)**: `SOUL.md`
- **Changes**:
  - Append new `## VOICE` section describing GSA synthesis (Gita depth, Sandi solutions, Anwar structure)
  - Include 5 Indonesian "Kunci" rules
- **Depends on**: None — standalone documentation update

### Subtask 5: Create .wiki/gsa-voice-spec.md — full specification document
- **File(s)**: `.wiki/gsa-voice-spec.md` (NEW FILE)
- **Changes**:
  - Create full spec with frontmatter (title, domain, impact_score, last_updated, injects_into, tokens_estimated)
  - Document one-liner summary, FACTS section, LEGION BEHAVIOR RULES (7 rules)
  - Add example with/without GSA voice, anti-patterns, debate record
- **Depends on**: None — greenfield wiki doc

### Subtask 6: Smoke tests — verify GSA voice integration
- **File(s)**: None (run existing test code)
- **Changes**: Run pytest-style smoke tests:
  - Test `enforce_character()` strips "semangat" 
  - Test `enforce_gsa_structure()` strips banned openers
  - Test `classify_message_context()` classifies EMOTIONAL, TECHNICAL, ANALYTICAL, CASUAL correctly
  - Test `build_full_system_prompt()` includes "GSA Voice" in output
- **Depends on**: Subtasks 1, 2, 3 complete

## Execution Order
1. **Subtask 1** — Update `core/character_enforcer.py` (standalone, no dependencies)
2. **Subtask 2** — Create `core/gsa_voice.py` (greenfield, no dependencies)
3. **Subtask 3** — Wire into `system_prompt_builder.py` (depends on Subtask 2)
4. **Subtask 4** — Update `SOUL.md` (standalone, can run in parallel with Subtasks 1-3)
5. **Subtask 5** — Create `.wiki/gsa-voice-spec.md` (standalone, can run in parallel with Subtasks 1-3)
6. **Subtask 6** — Run smoke tests (depends on Subtasks 1, 2, 3)

## Notes
- **Architecture concern**: `system_prompt_builder.py` has TWO prompt builders: `build_full_system_prompt()` (module-level) and `SystemPromptBuilder.build()`. The plan specifies wiring into `build_full_system_prompt()` only (line 56-167). The `SystemPromptBuilder.build()` (line 192-312) is a separate class-based path used by `llm_client.chat()`. GSA injection should be reviewed for both paths after initial implementation.
- **Token budget**: GSA injection is ~400 tokens estimated (from wiki spec). This is significant — ensure it doesn't push model over context limits for long conversations.
- **Dependency note**: Subtasks 4 and 5 are documentation-only and can run in parallel with code tasks.
- **ADR**: Will be written to `.wiki/decisions/adr-002-gsa-voice-implementation.md`
