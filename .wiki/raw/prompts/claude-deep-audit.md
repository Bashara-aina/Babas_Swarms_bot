---
title: Claude Deep Audit
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- prompts
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Give Claude full repo access before running this.'
wikilinks: []
confidence: medium
source: research
---
# CLAUDE — DEEP HONEST AUDIT: IS LEGION TRULY CAPABLE OR JUST WIDE?
> Give Claude full repo access before running this.
> This is not a bug hunt. This is a depth audit.
> Goal: Identify the gap between what Legion CLAIMS to do and what it ACTUALLY does.

---

## CONTEXT FOR CLAUDE

You have full access to this repository: Babas_Swarms_bot.
This is a Telegram AI bot called **Legion**.

Before reading any code, read these files first in this order:
1. `SOUL.md` — Legion\'s identity and personality
2. `IMPLEMENTATION_STATUS.md` — what the developer thinks is done
3. `DEEP_AUDIT_2026-04-10.md` — previous audit findings
4. `WIRING_VERIFIED_2026-04-12.md` — what was verified recently
5. `main.py` — the entry point (full read)
6. `router.py` — the routing logic

Then explore freely: `handlers/`, `core/`, `skills/`, `agents/`,
`bridges/`, `task_orchestrator.py`, `llm_client/`, `wiki/`.

---

## THE CORE QUESTION

The developer\'s goal is not a Telegram chatbot that can do many things on the surface.
The goal is:

> **A bot that works EVERY intention, DEEPLY — not just acknowledged, but actually executed.**
> **Not just "jack of all trades" (wide), but also a specialist in each thing it claims to do.**

Examples of the difference:
- WIDE: User asks to search → Legion says "let me search that" → searches → returns 3 bullet points
- DEEP: User asks to search → Legion searches → synthesizes → reasons about the results → gives a nuanced answer with source quality assessment → proactively identifies follow-up information the user didn\'t know to ask for

- WIDE: User asks for code help → Legion returns code snippet
- DEEP: Legion reads the full context, identifies what the user ACTUALLY needs vs what they asked for, gives working code, explains the tradeoffs, catches the edge cases the user will hit in 3 hours

- WIDE: Swarm mode exists as a command
- DEEP: Swarm orchestration actually breaks down complex tasks, assigns sub-tasks to specialized agents, aggregates results intelligently, handles failures gracefully, and returns something no single LLM call could produce

---

## YOUR AUDIT MISSION

Audit Legion across 5 dimensions. For each, give:
- **Honest rating: 1–10** (1 = totally broken, 10 = genuinely world-class)
- **What exists** (real evidence from code)
- **What\'s missing** to go from current rating to 9/10
- **Specific file-level recommendations** (not vague "improve this" — name the file and the function)

---

### DIMENSION 1: INTELLIGENCE DEPTH
*Does Legion actually think, or does it just relay?*

Questions to investigate:
- When a user asks a complex question, how many "thinking steps" happen before the LLM call?
- Is there any chain-of-thought, self-critique, or reflection loop?
- Does Legion ever ask clarifying questions before answering?
- Does it ever say "wait, let me re-approach this" when its first answer is weak?
- Is context window used strategically or just filled linearly?
- Does Legion ever synthesize multiple sources (search + wiki + memory) intelligently, or just concatenate them?
- Is there any model routing logic? (easy questions → cheap model, hard questions → strong model)
- Does the LLM ever receive structured reasoning prompts, or always the same generic system prompt?

What to look for in code:
  `core/` — any reasoning or thinking modules?
  `llm_client/` — is there multi-step reasoning support?
  `handlers/` — do handlers add any intelligence before calling LLM?
  `task_orchestrator.py` — what is the actual orchestration logic?

---

### DIMENSION 2: MEMORY DEPTH
*Does Legion actually know the user, or just store text blobs?*

Questions to investigate:
- What is the memory schema? Key-value? Vector? Structured? Timestamped?
- When memory is read, is ALL memory dumped into context, or is relevant memory retrieved?
- Is there memory COMPRESSION? (old memories summarized, not deleted)
- Is there memory DECAY? (things said 6 months ago weighted less)
- Can Legion infer things about the user from patterns? Or only remember explicit statements?
- Is there cross-session continuity? Does Legion remember context from last week?
- Is there a memory SIZE limit? What happens when it\'s full?
- Does Legion update memory DURING conversation (streaming writes) or only at end?
- Can the user QUERY their own memory? (/what do you know about me)
- Is memory per-user correctly isolated? (check for global state bugs)

What to look for:
  `core/memory_engine.py` or equivalent — read completely
  Database schema: is it Postgres/SQLite/JSON/pickle?
  Check for vector embeddings (semantic search over memories)

---

### DIMENSION 3: SKILL DEPTH
*When a skill is triggered, does it actually work well?*

Pick the 3 most important skills in `skills/` directory.
For each skill, audit:
- What is it supposed to do? (read the code, not the name)
- Does it actually do that? (trace the execute() function end-to-end)
- What\'s the output quality? Would a user find this useful?
- Is error handling real or just a bare try/except pass?
- Is the skill parameterized (adapts to context) or static (same output every time)?
- Is the skill result POST-PROCESSED by LLM before returning to user, or raw data?
- Does the skill integrate with memory? (skill results remembered for future use)

Also audit:
- Are ALL skills in `skills/` registered in the skill registry?
- Can skills call other skills? (skill composition)
- Is there a skill discovery mechanism? (user can ask "what can you do?" and get accurate list)

---

### DIMENSION 4: SWARM / AGENT DEPTH
*Is the multi-agent system real or theater?*

This is probably the most important dimension.
The swarm/orchestration is Legion\'s claimed superpower.

Read `task_orchestrator.py` completely and answer:
- How does it break down a complex task? Rule-based? LLM-based? Hardcoded?
- How many agent "roles" exist? What are they specialized in?
- Do agents communicate with each other, or do they just run in parallel isolation?
- Is there a supervisor/critic agent that reviews other agents\' outputs?
- When an agent fails, what happens? Retry? Fallback? Propagate error?
- What\'s the actual output format? Does it produce better results than a single LLM call?
- Can the swarm be extended with new specialized agents without changing core code?
- Is there a maximum depth/breadth control? (prevent infinite agent spawning)

Also check `agents/` directory:
- How many agent types exist? What are their specialties?
- Is there a `BaseAgent` with a consistent interface?
- Are agents stateful or stateless?

---

### DIMENSION 5: SELF-AWARENESS / META-CAPABILITIES
*Does Legion know itself? Can it improve itself?*

The most advanced dimension. Questions:
- Can Legion explain to a user EXACTLY what it can and cannot do?
- Does it know which features are "stub" vs "implemented"?
- Can it report on its own performance? ("my last 3 searches returned weak results")
- Is there any self-improvement loop? (daily harvest updates its knowledge)
- Does Legion know when it\'s uncertain? Does it say so?
- Can Legion refuse tasks it knows it can\'t do well, rather than giving a weak answer?
- Is there any feedback loop? (user rates answer → system learns)
- Can Legion spawn new wiki pages about topics it frequently encounters?

---

## WHAT TO DELIVER

After your full audit, deliver a structured report:

### 1. DIMENSION SCORECARD
| Dimension | Current Score | Target Score | Gap |
|-----------|--------------|--------------|-----|
| Intelligence Depth | X/10 | 9/10 | ... |
| Memory Depth | X/10 | 9/10 | ... |
| Skill Depth | X/10 | 9/10 | ... |
| Swarm/Agent Depth | X/10 | 9/10 | ... |
| Self-Awareness | X/10 | 9/10 | ... |

### 2. THE HONEST VERDICT
In plain language:
- What is Legion TODAY? (a sentence that truly captures its current state)
- What would Legion be if all gaps were fixed? (a sentence about the potential)
- What is the single biggest thing holding it back?

### 3. THE PRIORITY FIX LIST
Rank the top 10 things to fix/build, ordered by:
  (impact on user experience) × (feasibility in 1-2 days)

For each:
  Priority: [1-10]
  Title: [name]
  File: [exact file to change]
  Current state: [what it does now]
  Target state: [what it should do]
  Estimated effort: [hours]
  Why it matters: [user-facing impact]

### 4. THE DEPTH UPGRADE PLAN
For each of the 3 dimensions with the lowest scores:
Write a concrete implementation plan:
  - Exact files to create or modify
  - Exact functions to add
  - Exact data structures to change
  - Verification method

### 5. THE SPECIALITY GAPS
Legion claims to be good at many things. For each claimed specialty:
  - Is it actually specialized or just a generic LLM call with a different prompt?
  - What would make it GENUINELY specialized? (specific training data, domain tools, 
    structured reasoning chains, specialized memory)
  - Which claimed specialties should be DROPPED (not worth building deeply)?
  - Which should be made MUCH deeper?

---

## HARD RULES FOR YOUR AUDIT

1. **Be brutally honest.** A “3/10” is more useful than a polite “6/10”.
2. **Read the actual code.** Do not assume something works because a file exists.
   A 900-byte handler is almost certainly a stub. A feature mentioned in README
   might not exist in code at all.
3. **Name specific files.** “Improve the memory system” is useless.
   “core/memory_engine.py line 45: read_memory() dumps all memories without relevance
   filtering — replace with cosine similarity over memory embeddings” is useful.
4. **Distinguish stub from broken from missing.**
   - Stub = function exists, returns placeholder
   - Broken = function exists, has logic, but logic is wrong
   - Missing = feature doesn\'t exist at all, needs to be built from scratch
5. **Think about the end user.** For every gap, ask:
   "Would a real user notice this? Does it make the bot feel shallow?"
6. **Do NOT just list problems.** For every problem, give a solution direction.
7. **The goal is not perfection.** The goal is:
   A bot that deeply, reliably handles every intention it accepts.
   Better to do 10 things DEEPLY than 50 things shallowly.

---

## BONUS: ASK YOURSELF THIS AT THE END

If you were a power user who:
- Used Legion daily for 30 days
- Threw complex tasks at it
- Tested its memory across sessions
- Used swarm mode for a real research task
- Tried to use it as a genuine productivity tool

Would you keep using it? Or would you go back to ChatGPT?
Why?

That answer is the most important thing you can tell the developer.
