---
# PLANNER — Cycles 1-5 Wiki Knowledge Expansion
> Session: 2026-04-12
> Target: Fill .wiki/ with 100x-performance-impact knowledge pages
> Debate threshold: Judge score >= 7 to write
> Last updated: 2026-04-12

---

## OVERVIEW

This plan decomposes the first 5 of 10 wiki knowledge expansion cycles.
Each cycle researches a domain, drafts candidate pages, runs 3-agent debate, and writes approved pages.

**Orchestration:** Launch 5 workers in parallel (cycles 1-5), each running:
1. Read all target files for their domain
2. Answer research questions
3. Draft candidate wiki pages
4. Run 3-agent debate (Advocate/Skeptic/Judge)
5. Write approved pages (score 7+) to .wiki/
6. Log decisions to .wiki/LOOP_LOG.md

---

## CYCLE 1: BASHARA CONTEXT AGENT
**Domain:** Everything about Bashara that Legion must know to be useful.

### Target Files to Read
- `/home/newadmin/swarm-bot/SOUL.md`
- `/home/newadmin/swarm-bot/CLAUDE.md`
- `/home/newadmin/swarm-bot/MASTER_PROMPT.md`
- `/home/newadmin/swarm-bot/LEGION_MASTER.md`
- `/home/newadmin/swarm-bot/.wiki/profiles/BASHARA-MASTER-PROFILE.md` (if exists)
- `/home/newadmin/swarm-bot/.wiki/MASTER-INTELLIGENCE.md`

### Research Questions
1. What are Bashara's active projects? What are the current blockers on each?
2. What is Bashara's daily schedule pattern? (When does he code? When does he sleep?)
3. What communication style does Bashara prefer? (Short? Long? With code? Without?)
4. What are Bashara's recurring frustrations that Legion should anticipate?
5. What vocabulary and shortcuts does Bashara use? ("pusing", "nanti", "cek", "gw", etc.)
6. What decisions has Bashara made that Legion should never reverse?
7. What are the emotional triggers Legion must handle delicately?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/bashara-profile.md` | Who Bashara is, how to serve him | High — personalization |
| `.wiki/bashara-projects.md` | All active projects, status, blockers | High — context accuracy |
| `.wiki/bashara-vocabulary.md` | Indonesian shorthand + intent mapping | Medium — routing accuracy |
| `.wiki/bashara-schedule.md` | Time patterns, peak hours, sleep windows | High — proactive intelligence |

### Security Issues / Critical Gaps
- No critical security issues in this domain
- Gap: No structured vocabulary doc exists — Indonesian intent mapping is implicit

---

## CYCLE 2: LLM ROUTING AGENT
**Domain:** How Legion routes LLM calls and how to make routing 100x smarter.

### Target Files to Read
- `/home/newadmin/swarm-bot/llm_client.py`
- `/home/newadmin/swarm-bot/llm_client/__init__.py` (63KB — main LLM routing logic)
- `/home/newadmin/swarm-bot/swarms_bot/routing/` (entire directory)
- `/home/newadmin/swarm-bot/config/models.yaml`
- `/home/newadmin/swarm-bot/config/routing_keywords.yaml`
- `/home/newadmin/swarm-bot/.env.example`

### Research Questions
1. Which model is used for which task type right now? (map every route)
2. Which routes use the wrong model (too expensive, too slow, too dumb)?
3. What is the current cost per day in USD? What should it be?
4. Which tasks benefit from chain-of-thought? Which don't?
5. What temperature settings are correct for code vs creative vs emotional tasks?
6. What models are available on OpenRouter that could replace current ones cheaper?
7. How does fallback routing work? What fails silently?
8. What is the optimal context window per task type?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/llm-routing-map.md` | Every route, model, why, cost, alternatives | High — cost savings |
| `.wiki/llm-cost-optimization.md` | Specific swap recommendations with savings math | High — $40/mo budget |
| `.wiki/llm-context-strategy.md` | What to inject per task type, token budget guide | Medium — context optimization |

### Security Issues / Critical Gaps
- No API keys hardcoded (verified from .env.example pattern)
- Gap: No cost tracking per route exists currently
- Gap: Fallback behavior not well documented

---

## CYCLE 3: MEMORY ARCHITECTURE AGENT
**Domain:** How Legion stores, retrieves, and uses memory.

### Target Files to Read
- `/home/newadmin/swarm-bot/core/memory/` (entire directory — 10 files)
- `/home/newadmin/swarm-bot/core/memory/memory_manager.py`
- `/home/newadmin/swarm-bot/core/memory/episodic_store.py`
- `/home/newadmin/swarm-bot/core/memory/temporal_graph.py`
- `/home/newadmin/swarm-bot/core/memory/tiers.py`
- `/home/newadmin/swarm-bot/core/memory/semantic_cache.py`
- `/home/newadmin/swarm-bot/core/memory/consolidator.py`
- `/home/newadmin/swarm-bot/core/memory/unified_context.py`
- `/home/newadmin/swarm-bot/core/memory/user_profile.py`
- `/home/newadmin/swarm-bot/handlers/memory_commands.py`
- `/home/newadmin/swarm-bot/handlers/brain.py`
- `/home/newadmin/swarm-bot/core/legion_memory_facade.py`

### Research Questions
1. What memory backends are active? (SQLite? Redis? In-memory dict?)
2. What types of memories are stored? (episodic? semantic? procedural?)
3. What is the retrieval strategy? (keyword? vector? hybrid?)
4. What gets forgotten and shouldn't? What never gets deleted and should?
5. How long does a memory lookup take? What's the bottleneck?
6. What would a 10x better memory system look like in this codebase?
7. Are there memory conflicts (different stores with different answers)?
8. What is the format of stored memories? Is it LLM-optimized?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/memory-architecture.md` | Full map of stores, types, retrieval | High — understanding |
| `.wiki/memory-gaps.md` | What gets lost, what should be fixed | High — quality |
| `.wiki/memory-injection-strategy.md` | Which memories to inject per task type | High — context relevance |

### Security Issues / Critical Gaps
- Gap: Multiple memory stores exist (mem0, chromadb, episodic, graphiti) — potential for conflicts
- Gap: No consistency validation between stores
- Critical: CLAUDE.md says "never write to stores directly" but need to verify this is enforced

---

## CYCLE 4: INTENT ROUTING AGENT
**Domain:** How Legion understands what Bashara wants from a message.

### Target Files to Read
- `/home/newadmin/swarm-bot/core/intent_router.py`
- `/home/newadmin/swarm-bot/core/intent_classifier.py`
- `/home/newadmin/swarm-bot/core/task_router.py`
- `/home/newadmin/swarm-bot/router.py`
- `/home/newadmin/swarm-bot/task_orchestrator.py`
- `/home/newadmin/swarm-bot/core/natural_command_parser.py`
- `/home/newadmin/swarm-bot/config/routing_keywords.yaml`

### Research Questions
1. How does intent classification work right now? (keyword? LLM? regex?)
2. What are the most common misroutes? (what gets sent to wrong handler?)
3. What intent types are missing entirely?
4. What is the latency of intent classification? (should be <50ms)
5. What happens when confidence is low? Does Legion ask, guess, or fail silently?
6. How are multi-intent messages handled? ("cek seo rumahlabuh dan restart nginx")
7. What would a 10x better intent system look like?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/intent-routing-map.md` | All intents, handlers, confidence thresholds | High — routing accuracy |
| `.wiki/intent-gaps.md` | Missing intents and how to add them | Medium — completeness |
| `.wiki/multi-intent-strategy.md` | How to handle compound requests | Medium — compound handling |

### Security Issues / Critical Gaps
- Gap: Multi-intent handling not well defined
- Gap: Low-confidence scenarios not handled consistently
- Security: Need to verify ALLOWED_USER_ID checks in intent routing

---

## CYCLE 5: PERSONALITY & SOUL AGENT
**Domain:** How Legion's character is enforced and where it breaks down.

### Target Files to Read
- `/home/newadmin/swarm-bot/SOUL.md`
- `/home/newadmin/swarm-bot/core/character_enforcer.py`
- `/home/newadmin/swarm-bot/core/soul_engine.py`
- `/home/newadmin/swarm-bot/core/debate_engine.py`
- `/home/newadmin/swarm-bot/core/system_prompt_builder.py`
- `/home/newadmin/swarm-bot/core/character_voice.py`
- `/home/newadmin/swarm-bot/core/emotion_modulator.py`
- `/home/newadmin/swarm-bot/core/personality/` (entire directory if exists)
- `/home/newadmin/swarm-bot/config/legion_character.json`
- `/home/newadmin/swarm-bot/config/personality.yaml`

### Research Questions
1. What banned phrases are enforced? What banned patterns are MISSING?
2. Where in the codebase does Legion sound like a generic AI? (grep for it)
3. What is the debate_engine trigger condition? Is it too aggressive? Too passive?
4. How is SOUL.md injected? Is it always section 0? Verify.
5. What emotional states can Legion express? What is missing?
6. What makes Legion sound robotic right now? Give specific examples from the code.
7. What would make Legion 10x more like a real coworker?

### Candidate Wiki Pages to Produce
| Page | Description | Impact if Written |
|------|-------------|-------------------|
| `.wiki/soul-enforcement-map.md` | Every enforcement point, what it blocks | High — voice consistency |
| `.wiki/personality-gaps.md` | Where Legion sounds like ChatGPT, how to fix | High — authenticity |
| `.wiki/debate-system-guide.md` | When to debate, when not to, tone calibration | Medium — debate quality |
| `.wiki/emotional-vocabulary.md` | Indonesian emotional expressions Legion should know | Medium — emotional intelligence |

### Security Issues / Critical Gaps
- Critical: SOUL.md must be section 0 in system prompt — need to verify this
- Gap: No systematic grep for generic AI phrases across responses
- Gap: Debate engine trigger conditions not well documented

---

## WORKER LAUNCH SUMMARY

| Worker | Cycle | Domain | Files to Read | Pages to Produce |
|--------|-------|--------|---------------|-----------------|
| Worker-1 | 1 | Bashara Context | 6 files | 4 pages |
| Worker-2 | 2 | LLM Routing | 6 files | 3 pages |
| Worker-3 | 3 | Memory Architecture | 12 files | 3 pages |
| Worker-4 | 4 | Intent Routing | 7 files | 3 pages |
| Worker-5 | 5 | Personality & Soul | 10 files | 4 pages |

**Total candidate pages:** 17
**Expected approved (debate threshold 7+):** ~10-14 pages

---

## DEBATE PROTOCOL REMINDER

For each candidate page, run:
1. **ADVOCATE**: Argues FOR — capability improvement, speed/awareness gain, what Legion does wrong without it
2. **SKEPTIC**: Argues AGAINST — already covered, token bloat, implementation-specific, speculative
3. **JUDGE**: Scores 1-10, verdict WRITE/REJECT

**Scoring rubric:**
- 9-10: Critical Legion failure mode fixed OR major new capability unlocked
- 7-8: Meaningfully improves existing capability Bashara uses daily
- 5-6: Nice to have, borderline token cost
- 3-4: Already covered elsewhere, minimal new value
- 1-2: Speculative, outdated, or harmful

**Only scores 7+ get written to .wiki/**

---

## WIKI PAGE FORMAT (mandatory)

Every page must follow this exact structure:
```markdown
---
title: [page title]
domain: [which subagent wrote this]
impact_score: [judge's score 1-10]
last_updated: [YYYY-MM-DD]
injects_into: [which task types benefit]
tokens_estimated: [rough token count]
---

# [TITLE]

## ONE-LINE SUMMARY
[Single sentence. What does Legion do better because of this page?]

## FACTS
[Bullet list of concrete facts. Max 15 bullets.]

## LEGION BEHAVIOR RULES
[Numbered list of rules. Max 10 rules.]

## EXAMPLES
[2-3 concrete examples of Bashara message vs ideal Legion response]

## ANTI-PATTERNS
[2-3 failure modes without this page]

## DEBATE RECORD
Advocate: [score] | Skeptic: [score] | Judge: [verdict] [score]
Judge note: [1 sentence]
```

Page size limit: 600 tokens per page.

---

## LOGGING REQUIREMENTS

After each cycle, update `.wiki/LOOP_LOG.md` with:
- Cycle number and domain
- Pages written (with impact score)
- Pages rejected (with reason)
- Key findings (3 bullet points)
- Time taken

---

*Plan created: 2026-04-12 by @planner*
