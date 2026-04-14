---
title: Adr 002 Gsa Voice Implementation
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
summary: Legion's current voice is defined by `core/character_enforcer.py` (forbidden
  phrases) and `SOUL.md` (identity). However, there is no structured communication
  *style* that governs how Legion respond...
wikilinks: []
confidence: medium
source: research
---
Legion's current voice is defined by `core/character_enforcer.py` (forbidden phrases) and `SOUL.md` (identity). However, there is no structured communication *style* that governs how Legion responds to different message types (emotional, technical, analytical).

Bashara wants Legion to adopt the **GSA Voice** — a synthesis of three Indonesian communication styles:
- **Gita Wirjawan**: depth, data, strategic pause, 3 key points, global framing
- **Sandiaga Uno**: concrete solutions, specific steps, positive realism, problem → opportunity framing
- **Anwar Ibrahim**: inductive logic, sharp metaphor, structured arguments (fact → analysis → value → action)

Without a structured implementation, the GSA voice remains aspirational and inconsistent.
---


## Decision

We will implement the GSA Voice in three layers:

### Layer 1: Output Enforcement (`core/character_enforcer.py`)
- Add `GSA_BANNED_OPENERS` — phrases that cannot start a response (iya, ya, ok, oke, baik, etc.)
- Add `GSA_BANNED_CLOSERS` — phrases that cannot end a response (offers to help more, "semangat", etc.)
- Add `enforce_gsa_structure()` function to strip these programmatically

### Layer 2: Input Classification + Template Injection (`core/gsa_voice.py`)
- New module with `MessageContext` enum (TECHNICAL, EMOTIONAL, ANALYTICAL, REVIEW, CASUAL, STRATEGIC)
- `classify_message_context()` — keyword-based classifier for incoming messages
- `get_gsa_injection()` — returns context-specific system prompt injection
- `GSA_SYSTEM_INJECTION` — the actual voice instructions (~400 tokens)

### Layer 3: Prompt Integration (`core/system_prompt_builder.py`)
- Wire `gsa_voice.py` into `build_full_system_prompt()`
- Inject GSA template AFTER SOUL context, BEFORE personality + role layers
- Classification uses the raw user message text

### Documentation Layer
- Update `SOUL.md` with `## VOICE` section (GSA synthesis description + 5 Indonesian Kunci rules)
- Create `.wiki/gsa-voice-spec.md` (full spec with behavior rules, examples, anti-patterns)

---

## Consequences

### Positive
- Legion's communication becomes consistent and characterful across all message types
- GSA voice is enforceable at the output layer (not just advisory)
- Classification enables context-sensitive response templates
- Documentation lives in `.wiki/` for future reference and auto-ingest

### Negative / Risks
- **Token overhead**: ~400 token injection per response adds up over long conversations
- **Classification accuracy**: Keyword-based classification is simple; may misclassify edge cases
- **Dual paths**: `SystemPromptBuilder.build()` (class-based) is separate from `build_full_system_prompt()` — GSA injection only wired into one initially
- **Gita pause enforcement**: The "pause before key insight" (empty line) is in the injection template but cannot be programmatically enforced — relies on LLM compliance

### Mitigation
- Monitor token usage after deployment; consider making GSA injection optional via env var
- After initial rollout, add classification accuracy metrics
- After Subtask 3, evaluate whether `SystemPromptBuilder.build()` also needs GSA injection
- The pause/diam behavior is a soft guideline — LLM should self-enforce via the injection text

---

## References

- Implementation plan: `LEGION_VOICE_UPGRADE.md` lines 346-575
- Affected files: `core/character_enforcer.py`, `core/system_prompt_builder.py`, `SOUL.md`
- New file: `core/gsa_voice.py`
- Wiki spec: `.wiki/gsa-voice-spec.md`
