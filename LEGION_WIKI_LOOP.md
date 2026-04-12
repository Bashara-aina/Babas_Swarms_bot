# LEGION WIKI LOOP — 10-HOUR SUBAGENT KNOWLEDGE EXPANSION
# Paste this into OpenCode to start a fully autonomous 10-hour loop.
# Output: .wiki/ filled with 100x-performance-impact knowledge pages.
# Last updated: 2026-04-12

---

## ► HOW TO START

Paste this into OpenCode:
```
Read LEGION_WIKI_LOOP.md fully. Then read LEGION_MASTER.md, CLAUDE.md, and SOUL.md.
Then execute the ORCHESTRATOR LOOP defined in this file.
Do not ask for permission at each step. Run all 10 subagents autonomously.
Log every decision to .wiki/LOOP_LOG.md as you go.
```

---

# ──────────────────────────────────────────────────
# PART 0 — GROUND RULES FOR THIS SESSION
# ──────────────────────────────────────────────────

1. The goal is ONE thing: fill .wiki/ with knowledge that makes Legion 100x better.
   Not mildly better. Not "useful context". 100x. If a piece of knowledge doesn't
   make Legion measurably faster, smarter, more accurate, or more aware of Bashara's
   life — it does NOT get written to .wiki/.

2. Every candidate knowledge page must survive a 3-agent DEBATE before being written.
   Agents: Advocate (FOR) vs Skeptic (AGAINST) vs Judge (FINAL VERDICT).
   Judge must score impact 1-10. Only scores 7+ get written.
   This is mandatory. No exceptions. No fast-tracking.

3. .wiki/ is NOT a dump for documentation. It is Legion's second brain.
   Everything written there gets injected into Legion's context window on every boot.
   Bloat = slower inference = dumber Legion. Write less, write dense.

4. Each .wiki page must follow the WIKI PAGE FORMAT defined in Part 2.
   No freeform notes. No raw dumps. Structured, scannable, LLM-optimized.

5. The orchestrator runs 10 subagent cycles. Each cycle = 1 domain.
   Each cycle takes ~1 hour. Total: 10 hours.
   The orchestrator loops automatically. If one cycle finishes early, start next.

6. At the end of each cycle, update .wiki/LOOP_LOG.md with:
   - Cycle number and domain
   - Pages written (with impact score)
   - Pages REJECTED (with reason)
   - Time taken

7. At session end, update .wiki/INDEX.md with all live pages.

---

# ──────────────────────────────────────────────────
# PART 1 — THE 10 SUBAGENT DOMAINS
# ──────────────────────────────────────────────────

Each subagent owns one domain. It researches the codebase, extracts knowledge,
creates candidate pages, runs the debate, then writes approved pages to .wiki/.

---

## SUBAGENT 1 — BASHARA CONTEXT AGENT
Domain: Everything about Bashara that Legion must know to be useful.
Target files to read: SOUL.md, CLAUDE.md, MASTER_PROMPT.md, LEGION_MASTER.md

Research questions:
- What are Bashara's active projects? What are the current blockers on each?
- What is Bashara's daily schedule pattern? (When does he code? When does he sleep?)
- What communication style does Bashara prefer? (Short? Long? With code? Without?)
- What are Bashara's recurring frustrations that Legion should anticipate?
- What vocabulary and shortcuts does Bashara use? ("pusing", "nanti", "cek", "gw", etc.)
- What decisions has Bashara made that Legion should never reverse?
- What are the emotional triggers Legion must handle delicately?

Target .wiki pages to produce:
- .wiki/bashara-profile.md — who Bashara is, how to serve him
- .wiki/bashara-projects.md — all active projects, status, blockers
- .wiki/bashara-vocabulary.md — Indonesian shorthand + intent mapping
- .wiki/bashara-schedule.md — time patterns, peak hours, sleep windows

---

## SUBAGENT 2 — LLM ROUTING AGENT
Domain: How Legion routes LLM calls and how to make routing 100x smarter.
Target files: llm_client/, swarms_bot/routing/, config/, .env.example

Research questions:
- Which model is used for which task type right now? (map every route)
- Which routes use the wrong model (too expensive, too slow, too dumb)?
- What is the current cost per day in USD? What should it be?
- Which tasks benefit from chain-of-thought? Which don't?
- What temperature settings are correct for code vs creative vs emotional tasks?
- What models are available on OpenRouter that could replace current ones cheaper?
- How does fallback routing work? What fails silently?
- What is the optimal context window per task type?

Target .wiki pages:
- .wiki/llm-routing-map.md — every route, model, why, cost, alternatives
- .wiki/llm-cost-optimization.md — specific swap recommendations with savings math
- .wiki/llm-context-strategy.md — what to inject per task type, token budget guide

---

## SUBAGENT 3 — MEMORY ARCHITECTURE AGENT
Domain: How Legion stores, retrieves, and uses memory.
Target files: core/memory/, handlers/memory_commands.py, brain.py

Research questions:
- What memory backends are active? (SQLite? Redis? In-memory dict?)
- What types of memories are stored? (episodic? semantic? procedural?)
- What is the retrieval strategy? (keyword? vector? hybrid?)
- What gets forgotten and shouldn't? What never gets deleted and should?
- How long does a memory lookup take? What's the bottleneck?
- What would a 10x better memory system look like in this codebase?
- Are there memory conflicts (different stores with different answers)?
- What is the format of stored memories? Is it LLM-optimized?

Target .wiki pages:
- .wiki/memory-architecture.md — full map of stores, types, retrieval
- .wiki/memory-gaps.md — what gets lost, what should be fixed
- .wiki/memory-injection-strategy.md — which memories to inject per task type

---

## SUBAGENT 4 — INTENT ROUTING AGENT
Domain: How Legion understands what Bashara wants from a message.
Target files: core/intent_router.py, router.py, task_orchestrator.py

Research questions:
- How does intent classification work right now? (keyword? LLM? regex?)
- What are the most common misroutes? (what gets sent to wrong handler?)
- What intent types are missing entirely?
- What is the latency of intent classification? (should be <50ms)
- What happens when confidence is low? Does Legion ask, guess, or fail silently?
- How are multi-intent messages handled? ("cek seo rumahlabuh dan restart nginx")
- What would a 10x better intent system look like?

Target .wiki pages:
- .wiki/intent-routing-map.md — all intents, handlers, confidence thresholds
- .wiki/intent-gaps.md — missing intents and how to add them
- .wiki/multi-intent-strategy.md — how to handle compound requests

---

## SUBAGENT 5 — PERSONALITY & SOUL AGENT
Domain: How Legion's character is enforced and where it breaks down.
Target files: SOUL.md, core/character_enforcer.py, core/soul_engine.py,
             core/debate_engine.py, core/system_prompt_builder.py

Research questions:
- What banned phrases are enforced? What banned patterns are MISSING?
- Where in the codebase does Legion sound like a generic AI? (grep for it)
- What is the debate_engine trigger condition? Is it too aggressive? Too passive?
- How is SOUL.md injected? Is it always section 0? Verify.
- What emotional states can Legion express? What is missing?
- What makes Legion sound robotic right now? Give specific examples from the code.
- What would make Legion 10x more like a real coworker?

Target .wiki pages:
- .wiki/soul-enforcement-map.md — every enforcement point, what it blocks
- .wiki/personality-gaps.md — where Legion sounds like ChatGPT, how to fix
- .wiki/debate-system-guide.md — when to debate, when not to, tone calibration
- .wiki/emotional-vocabulary.md — Indonesian emotional expressions Legion should know

---

## SUBAGENT 6 — PROACTIVE INTELLIGENCE AGENT
Domain: How Legion initiates without being asked.
Target files: core/proactive/, daily_harvester.py, core/heartbeat/ (if exists)

Research questions:
- What proactive behaviors exist? List every scheduled job.
- What proactive behavior is broken or too noisy? (checkin spam = verified issue)
- What should Legion proactively do but currently doesn't?
- What is the morning briefing format? Is it actually useful?
- What context should Legion have to know when NOT to message? (e.g., 3am JST)
- What external triggers should drive proactive behavior? (GitHub, Supabase, weather)
- What would 10x better proactive intelligence look like for Bashara's life?

Target .wiki pages:
- .wiki/proactive-schedule.md — every job, trigger, frequency, purpose
- .wiki/proactive-gaps.md — what's missing, what should be added
- .wiki/bashara-quiet-hours.md — when Legion should not message
- .wiki/briefing-format-spec.md — optimal morning briefing structure

---

## SUBAGENT 7 — TOOLS & SKILLS AGENT
Domain: Every tool and skill Legion can execute.
Target files: tools/, skills/, handlers/, core/skills/ (if exists)

Research questions:
- Map every tool file to what it does and what command/intent triggers it.
- Which tools are broken, untested, or incomplete?
- Which tools are duplicated across different files?
- What tools does Bashara need most (based on project list) that don't exist?
- What is the error handling strategy per tool? What fails silently?
- How does tool output get formatted for Telegram? What gets cut off?
- What is the tool timeout strategy? Are all tools async?

Target .wiki pages:
- .wiki/tools-inventory.md — every tool, status (working/broken/untested), trigger
- .wiki/tools-gaps.md — tools needed that don't exist, priority order
- .wiki/tool-output-formatting.md — how to format tool output for Telegram properly

---

## SUBAGENT 8 — SECURITY & STABILITY AGENT
Domain: What can go wrong and how to prevent it.
Target files: core/shell/, handlers/shared.py, computer_agent/, main.py

Research questions:
- Where are raw subprocess calls that bypass sandbox? List every occurrence.
- Where is ALLOWED_USER_ID check missing? (any handler without it = security hole)
- What happens if the bot receives a message from an unknown user? Verify behavior.
- What is the crash recovery strategy? What happens on unhandled exception?
- What data is logged that shouldn't be? (tokens, user messages in plaintext logs)
- What happens if Telegram API rate limit is hit?
- What happens if OpenRouter is down? Is fallback working?
- What is the longest possible response time for any command? Is there a cap?

Target .wiki pages:
- .wiki/security-audit.md — every vulnerability found, severity, fix status
- .wiki/stability-map.md — crash scenarios, recovery behavior, gaps
- .wiki/rate-limit-strategy.md — Telegram + OpenRouter limits and handling

---

## SUBAGENT 9 — CONTEXT WINDOW AGENT
Domain: What gets injected into the LLM context and whether it's optimal.
Target files: core/system_prompt_builder.py, core/soul_engine.py,
             core/memory/context_builder.py (if exists), prompts/

Research questions:
- What is the full system prompt structure? (list every section in order)
- How many tokens does the system prompt use? (estimate)
- What is injected on every request vs only on certain task types?
- What useful context is NOT injected that should be?
- What is injected that wastes tokens without adding value?
- What is the conversation history injection strategy? (last N turns? sliding window?)
- How does memory get selected for injection? Is it relevant or just recent?
- What would a perfectly optimized context for each of Legion's 5 main task types look like?

Target .wiki pages:
- .wiki/context-window-map.md — every section, token count, purpose
- .wiki/context-optimization.md — what to cut, what to add, per task type
- .wiki/system-prompt-spec.md — canonical structure for every task type

---

## SUBAGENT 10 — FUTURE ARCHITECTURE AGENT
Domain: What Legion should become in the next 30 days.
Target files: LEGION_MASTER.md, LEGION_CLAWCODE_UPGRADE.md, IMPLEMENTATION_STATUS.md

Research questions:
- What are the 5 highest-leverage architectural changes Legion could make?
- What does 100x performance actually mean for each of Bashara's 5 use cases?
- What is the optimal agent topology for Legion's workload? (single-agent? swarm?)
- How should Legion handle tasks that take >30 seconds? (async job queue?)
- What would make Legion feel like a 10x engineer instead of a smart assistant?
- What are the 3 things that if removed would break Legion most? Protect those.
- What does Legion 2.0 look like architecturally? Write the vision.

Target .wiki pages:
- .wiki/legion-vision-2026.md — what Legion becomes, architecture, timeline
- .wiki/high-leverage-changes.md — top 5 changes ranked by impact per hour
- .wiki/agent-topology-design.md — optimal multi-agent structure for Legion's workload
- .wiki/use-case-optimization.md — 100x definition per Bashara use case

---

# ──────────────────────────────────────────────────
# PART 2 — DEBATE PROTOCOL (mandatory before every .wiki write)
# ──────────────────────────────────────────────────

For EVERY candidate wiki page, run this 3-agent debate before writing:

## ADVOCATE (argues FOR writing the page)
Prompt: You are the Advocate. Your job is to argue that this knowledge page
deserves to be in Legion's .wiki. Be specific about:
1. Which Legion capability does this knowledge directly improve?
2. How much faster/smarter/more aware will Legion be with this knowledge?
3. What would Legion do WRONG without this knowledge?
4. Give a concrete example of a Bashara message that Legion handles better
   WITH this page vs WITHOUT.
Be honest. Don't advocate for weak content. If you can't make a strong case, say so.

## SKEPTIC (argues AGAINST writing the page)
Prompt: You are the Skeptic. Your job is to argue that this knowledge page
should NOT be written. Challenge on:
1. Is this already covered somewhere in CLAUDE.md, SOUL.md, or LEGION_MASTER.md?
2. Will this add token bloat without proportional value?
3. Is this too implementation-specific — will it be outdated in 2 weeks?
4. Is the information speculative rather than factual?
5. Would this confuse Legion or contradict existing knowledge?
Be ruthless. Protect the wiki from noise.

## JUDGE (gives final verdict)
Prompt: You are the Judge. You have heard the Advocate and the Skeptic.
Score this knowledge page 1-10 on IMPACT TO LEGION PERFORMANCE.

Scoring rubric:
- 9-10: Fixes a critical Legion failure mode OR unlocks a major new capability
- 7-8: Meaningfully improves an existing capability Bashara uses daily
- 5-6: Nice to have, low urgency, borderline token cost
- 3-4: Already covered elsewhere, minimal new value
- 1-2: Speculative, outdated, or harmful

VERDICT FORMAT:
Score: [1-10]
Decision: [WRITE / REJECT]
Reason: [1 sentence]
Condition: [If WRITE — any required changes before writing. If REJECT — what would change the verdict.]

ONLY scores 7+ get written to .wiki/.

---

# ──────────────────────────────────────────────────
# PART 3 — WIKI PAGE FORMAT (every page must follow this exactly)
# ──────────────────────────────────────────────────

Every .wiki page must use this exact structure:

```markdown
---
title: [page title]
domain: [which subagent wrote this]
impact_score: [judge's score 1-10]
last_updated: [YYYY-MM-DD]
injects_into: [which task types benefit: all | code | emotional | research | media | system]
tokens_estimated: [rough token count of this page]
---

# [TITLE]

## ONE-LINE SUMMARY
[Single sentence. What does Legion do better because of this page?]

## FACTS
[Bullet list of concrete facts. No speculation. No "maybe". No padding.]
[Each fact must be actionable or directly informative for Legion.]
[Max 15 bullets.]

## LEGION BEHAVIOR RULES
[Numbered list of rules Legion must follow based on this knowledge.]
[Format: "When [X], Legion must [Y]."]
[Max 10 rules.]

## EXAMPLES
[2-3 concrete examples of Bashara message vs ideal Legion response, using this knowledge.]
[Format:]
[Bashara: "..."]
[Legion (with this page): "..."]
[Legion (without): "..."]

## ANTI-PATTERNS
[What would Legion do WRONG without this page? List 2-3 failure modes.]

## DEBATE RECORD
Advocate score: [1-10] | Skeptic score: [1-10] | Judge verdict: [WRITE/REJECT] [score]
Judge note: [1 sentence]
```

Page size limit: 600 tokens per page. Exceeded pages get split into part A / part B.
No page should be a prose essay. Dense, structured, LLM-scannable.

---

# ──────────────────────────────────────────────────
# PART 4 — THE ORCHESTRATOR LOOP (run this exactly)
# ──────────────────────────────────────────────────

For each cycle i = 1 to 10:

```
CYCLE i START

1. LOAD: Read the subagent i definition from PART 1 above.
   Read all target files listed under that subagent.
   Read .wiki/INDEX.md to check what already exists (avoid duplicates).

2. RESEARCH: Answer all research questions for subagent i.
   Write raw findings to .wiki/DRAFT_cycle{i}.md (temporary, will be deleted).
   Be thorough. Don't skip questions. If a file doesn't exist yet, note that.

3. CANDIDATE PAGES: From the research findings, identify the
   target pages listed under subagent i. For each candidate page:

   a. Draft the page content following Part 3 format.
   b. Run the 3-agent DEBATE (Part 2) on this candidate.
   c. If Judge score >= 7: write the page to .wiki/[filename].md
   d. If Judge score < 7: note the rejection in LOOP_LOG.md and skip.

4. LOG: Append to .wiki/LOOP_LOG.md:
   ## Cycle {i}: [DOMAIN NAME]
   Date: [timestamp]
   Pages written: [list with scores]
   Pages rejected: [list with reason]
   Key findings: [3 bullet points of most important discoveries]

5. INDEX: Update .wiki/INDEX.md with any new pages written.

6. CLEANUP: Delete .wiki/DRAFT_cycle{i}.md

7. CONTINUE to cycle i+1 without waiting.

CYCLE i END
```

After all 10 cycles:
```
FINAL PASS:
1. Read all pages in .wiki/
2. Find any contradictions between pages — resolve them.
3. Find any pages that overlap >50% — merge them.
4. Update .wiki/INDEX.md with final page list, impact scores, token counts.
5. Write .wiki/SESSION_SUMMARY.md:
   - Total pages written
   - Total pages rejected
   - Top 3 highest-impact pages written
   - Top 3 most surprising findings
   - Estimated Legion performance improvement
   - Recommended next loop domains (for next session)
```

---

# ──────────────────────────────────────────────────
# PART 5 — IMPACT CRITERIA (what 100x means per dimension)
# ──────────────────────────────────────────────────

Subagents must evaluate impact using these criteria.
Knowledge qualifies as "100x" if it enables at least ONE of:

| Dimension | What 100x looks like | What NOT to write |
|-----------|---------------------|--------------------|
| Speed | Legion answers in 1 step instead of 3 | Info that saves 1 word |
| Accuracy | Legion stops making a mistake it makes daily | Rarely-triggered edge cases |
| Personalization | Legion knows something about Bashara that prevents a generic reply | Generic AI behavior rules |
| Autonomy | Legion does something useful without being asked | One-off tasks |
| Cost | LLM cost drops without quality loss | Marginal optimizations |
| Safety | Prevents a crash, data loss, or security breach | Theoretical risks |
| Emotional | Legion responds like a real coworker, not an AI, in a situation Bashara faces daily | Rare emotional scenarios |

If the knowledge doesn't land in at least one cell with a clear example — reject it.

---

# ──────────────────────────────────────────────────
# PART 6 — BOOTSTRAP FILES (create these first, before any cycle)
# ──────────────────────────────────────────────────

Before starting cycle 1, create these two files:

### .wiki/INDEX.md (create empty, fill as pages are approved)
```markdown
# LEGION WIKI INDEX
Generated by: LEGION_WIKI_LOOP.md session 2026-04-12
Total pages: 0
Total tokens: 0

## Pages
| File | Domain | Impact | Injects Into | Tokens |
|------|--------|--------|--------------|--------|
```

### .wiki/LOOP_LOG.md (create empty, append each cycle)
```markdown
# LEGION WIKI LOOP LOG
Session: 2026-04-12
Target: 10 cycles × ~1hr = 10 hours
Debate threshold: Score >= 7 to write

---
```

---

# ──────────────────────────────────────────────────
# PART 7 — WHAT SUCCESS LOOKS LIKE
# ──────────────────────────────────────────────────

At end of 10 hours, .wiki/ should contain:

- 20-35 approved pages (some candidates will be rejected by debate — expected)
- 0 pages with impact score < 7
- An INDEX.md that is a genuine map of Legion's second brain
- A SESSION_SUMMARY.md that Bashara can read in 2 minutes
- A LOOP_LOG.md that shows the debate was actually run (not skipped)

After this session, Legion should be able to:
- Answer "explain your LLM routing strategy" accurately
- Answer "what do you know about my thesis deadline" accurately
- Handle "pusing nih" with emotional vocabulary specific to Bashara's context
- Route any Bashara message to the right handler with 95%+ confidence
- Know when NOT to respond proactively at any given hour

---

*This file does not get deleted. It is the template for future wiki loops.*
*Next loop: add 10 new domains. Same debate gate. Same format.*
*Run this every time Legion needs a knowledge base refresh.*
