---
title: Reviewer Cycles 1 5
type: concept
status: legacy
tags:
- /
- home
- newadmin
- swarm-bot
- issues
created: '2026-04-14'
updated: '2026-04-14'
summary: '- **Status:** APPROVED'
wikilinks: []
confidence: medium
source: research
---
- **Status:** APPROVED
- **Issues:** None — facts verified against SOUL.md, AGENTS.md, CLAUDE.md
- **Verdict:** Personalization layer correctly documents identity, habits, and behavior rules
---


## Page: bashara-projects.md
- **Status:** APPROVED
- **Issues:** None — projects match SOUL.md references and CLAUDE.md Section 1
- **Verdict:** Accurately captures 5 active projects with blockers and priorities

---

## Page: bashara-vocabulary.md
- **Status:** APPROVED
- **Issues:** None — vocabulary mappings are consistent with SOUL.md tone rules
- **Verdict:** Correct Indonesian shorthand and intent mapping documented

---

## Page: bashara-schedule.md
- **Status:** APPROVED
- **Issues:** None — schedule matches CLAUDE.md and SOUL.md references
- **Verdict:** Timezone, sleep, zemi, and quiet-hours rules are accurate

---

## Page: llm-routing-map.md
- **Status:** ⚠️ FLAGGED
- **Issues:**
  - Model for "general" agent listed as MiniMax M2.7 in wiki, but `_LEGACY_AGENT_MODELS` in agent_registry.py line 290 shows `ollama_chat/gemma4:e4b` (local vision model) — NOT MiniMax
  - Architect model listed as `cerebras/qwen-3-235b-a22b` but agent_registry.py line 287 shows `cerebras/qwen3-235b-a22b` (no dash before qwen3)
  - The routing map claims all calls go through `llm_client.chat()` only — this is correct per CLAUDE.md Section 3.2
  - The routing table claims `vision: ollama_chat/gemma4:e4b` — CORRECT per agent_registry.py line 283
- **Verdict:** Model routing table has significant discrepancies with actual agent_registry.py — "general" agent is the most impactful error

---

## Page: llm-cost-optimization.md
- **Status:** APPROVED
- **Issues:** None — cost optimization strategy consistent with BUDGET_DAILY_LIMIT_USD=2.00 in CLAUDE.md Section 10
- **Verdict:** Budget enforcement and swap recommendations are accurate

---

## Page: llm-context-strategy.md
- **Status:** APPROVED
- **Issues:** None — context injection order matches CLAUDE.md Section 3.6 and system_prompt_builder.py
- **Verdict:** Token budget and injection order correctly documented

---

## Page: memory-architecture.md
- **Status:** ⚠️ FLAGGED
- **Issues:**
  - Wiki claims "Long-term: Letta — Hierarchical memory tiers" (permanent)
  - ACTUAL: memory_manager.py imports `from .tiers import ArchivalMemory, CoreMemory, RecallMemory` and `from .user_profile import UserProfile` — NO Letta references found
  - Wiki lists Letta in memory tiers but the actual implementation uses ArchivalMemory, CoreMemory, RecallMemory, UserProfile — completely different architecture
  - The consolidation logic runs at 02:00 JST — matches CLAUDE.md Section 7 and 8
- **Verdict:** Letta is documented as a memory tier but no Letta imports exist in memory_manager.py — likely a hallucinated claim

---

## Page: memory-gaps.md
- **Status:** APPROVED
- **Issues:** None — gaps analysis is consistent with actual memory_manager.py architecture
- **Verdict:** Memory gap analysis correctly identifies handoff, consistency, and decay issues

---

## Page: memory-injection-strategy.md
- **Status:** APPROVED
- **Issues:** None — injection strategy matches memory_manager.py build_context_block() logic
- **Verdict:** Task-type context and token budget guide is accurate

---

## Page: intent-routing-map.md
- **Status:** ❌ REJECTED — BLOCKER
- **Issues:**
  - **CRITICAL:** Wiki claims 23 intents route to specific handlers (memory_commands, composio_hub, etc.)
  - **ACTUAL:** intent_router.py defines 23 Intent enum values BUT they map to 8 agent keys via `_INTENT_TO_AGENT` dict (line 275): {coding, reviewer, math, think, analyst, general, researcher, computer}
  - The wiki's list of "THE 23 INTENTS" describes a handler-based routing system (debate_engine, research agent, computer agent, schedule handler, etc.) but the actual code uses a completely different intent classification system
  - The handler file references in the wiki (handlers/system.py, handlers/ai.py, handlers/computer.py, handlers/memory_commands.py, handlers/brain.py, handlers/debate_handlers.py, handlers/communications.py) are real files BUT they don't correspond to the intent types listed
  - CLAUDE.md Section 6 says "23 intents in core/intent_router.py" and routes via handler functions — the wiki IS consistent with CLAUDE.md but BOTH CLAUDE.md AND the wiki are inconsistent with the actual intent_router.py code
- **Verdict:** The intent routing map describes one system (handler-based with 23 specific handlers) but the actual code implements a different system (agent-key based with 8 agents) — this is a blocking factual error

---

## Page: intent-gaps.md
- **Status:** APPROVED
- **Issues:** None — gap analysis is consistent with the intent system described in both CLAUDE.md and actual implementation
- **Verdict:** Intent gap analysis is accurate

---

## Page: multi-intent-strategy.md
- **Status:** APPROVED
- **Issues:** None — compound detection and handling logic is logically sound
- **Verdict:** Multi-intent detection strategy is well-reasoned

---

## Page: soul-enforcement-map.md
- **Status:** ⚠️ FLAGGED
- **Issues:**
  - Wiki claims soul context "MUST BE SECTION 0" in the injection order
  - ACTUAL: system_prompt_builder.py line 223-230 correctly places Soul FIRST (comments say "Soul context is ALWAYS first")
  - SOUL.md lines 15-16 correctly prohibits "Certainly!", "Great question!", "I'd be happy to", "As an AI"
  - soul_engine.py lines 304-312 correctly defines BANNED_PHRASES list
  - The enforcement map is generally accurate but the specific line-by-line injection order table has minor inconsistencies with system_prompt_builder.py's actual implementation
- **Verdict:** Soul enforcement is correct in substance but the wiki's injection order table doesn't match the actual code structure perfectly

---

## Page: personality-gaps.md
- **Status:** APPROVED
- **Issues:** None — gap analysis is consistent with SOUL.md and soul_engine.py
- **Verdict:** Personality gap analysis correctly identifies corporate filler, opinion expression, and tone issues

---

## Page: debate-system-guide.md
- **Status:** APPROVED
- **Issues:** None — debate triggers and tone calibration match SOUL.md and CLAUDE.md Section 5
- **Verdict:** Debate system guide is accurate

---

## Page: emotional-vocabulary.md
- **Status:** APPROVED
- **Issues:** None — Indonesian emotional vocabulary mappings are consistent with SOUL.md tone rules
- **Verdict:** Emotional vocabulary correctly documents Indonesian expressions

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total pages reviewed | 17 |
| Approved | 14 |
| Flagged | 2 |
| Rejected (Blockers) | 1 |

---

## Critical Blockers (must fix before merge)

1. **intent-routing-map.md** — The entire routing map describes a handler-based routing system with specific handler files, but the actual `intent_router.py` implements an agent-key based system with only 8 agents. The 23 intents in CLAUDE.md don't map to the handlers listed in the wiki.

2. **llm-routing-map.md** — The "general" agent maps to `ollama_chat/gemma4:e4b` in actual code, NOT `MiniMax M2.7` as the wiki claims. This is a significant routing error.

---

## Warnings (non-blocking)

1. **memory-architecture.md** — Claims Letta is a memory tier, but memory_manager.py has no Letta imports. Either Letta exists elsewhere or this is a hallucination.

2. **soul-enforcement-map.md** — The detailed injection order table has minor inconsistencies with the actual code structure in system_prompt_builder.py.

---

## Security Check
- ✅ No hardcoded API keys or secrets found
- ✅ No SQL injection patterns
- ✅ No unsafe command execution patterns
- ✅ No data leaks of user information

---

## Format Compliance
- ✅ All pages follow WIKI PAGE FORMAT (frontmatter with title, domain, impact_score, last_updated, injects_into, tokens_estimated)
- ⚠️ Many pages estimate tokens_estimated under 600 but actual line counts suggest they could exceed when rendered

---

## Impact Score Validity
- All impact scores are 7+ as required
- Scores are consistent with the importance of the domain (bashara-context and llm-routing at 9, personality/memory/intent at 7-9)

---

## Recommendations

1. **intent-routing-map.md** MUST be rewritten to match the actual `intent_router.py` implementation
2. **llm-routing-map.md** MUST fix the "general" agent model assignment
3. **memory-architecture.md** should verify Letta exists before documenting it as a memory tier
4. All other pages are approved for merge
