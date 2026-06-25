# LEGION SYSTEM — Cognitive Operating System Reference
# ============================================================
# This file maps the Legion v11 cognitive architecture.
# It is READ-ONLY reference — not a behavioral prompt.
# The actual behavioral rules live in CLAUDE.md (Sections 0–0q).
#
# Read this when you need to understand:
# - How Legion reasons (4-phase loop)
# - Where information lives (5-tier memory pyramid)
# - When to use which agent (dispatch matrix)
# - How agents communicate (shared state files)
#
# LEGEND: ✅ = implemented and live | ⚠️ = partial | ❌ = missing

## ══════════════════════════════════════════════════════════
## PART 1: THE 4-PHASE REASONING LOOP
## Legion's cognitive architecture — how every task is processed
## ══════════════════════════════════════════════════════════

PHASE A — RETRIEVE (never skip)
  Before forming any opinion or plan:
  1. Read /tmp/legion_hermes_skills.txt — skills I've built before
  2. Read /tmp/legion_session_context.txt — mem0 memories about Bashara
  3. hermes_search_memory(query) via MCP — what do I already know?
  4. gitnexus_search_code(query) — what's already in the codebase?
  5. obsidian_read(relevant topic) — what's documented?
  Rules:
    • If PHASE A yields complete answer → skip to PHASE C
    • If PHASE A yields partial context → fill gaps in PHASE B
    • If PHASE A yields nothing → note it, proceed to PHASE B

PHASE B — PLAN (tasks > 2 steps only)
  Call sequentialthinking with:
    thought: "Task: [description]. Known context: [from PHASE A]. Steps needed:"
  Output: numbered step list with dependency arrows
  Rules:
    • Each step = what + which agent + which MCP + success criteria
    • Maximum 7 steps in one plan (break into sub-tasks if more)
    • Plan is LOCKED after Phase B — do not revise mid-execution

PHASE C — EXECUTE (agent-dispatched per step)
  Each step routes to the correct agent (see Part 3).
  Rules:
    • Execute steps sequentially unless explicitly parallelizable
    • After each step: verify output matches success criteria
    • If a step fails twice → STOP, report blocker, propose alternative

PHASE D — PERSIST (never skip at end of any complex task)
  1. hermes_write_skill() — save what was learned ✅ (hermes MCP live)
  2. obsidian_write(.wiki/...) — if architecture/wiki changed ✅
  3. git_commit() — if code changed ✅
  4. Write /tmp/legion_session_summary.txt ✅
  Rules:
    • PHASE D is not optional — it's how Legion gets smarter every session
    • If context too full → /compact first, then D

## ══════════════════════════════════════════════════════════
## PART 2: THE 5-TIER MEMORY PYRAMID
## Where every type of information lives and how to write/read it
## ══════════════════════════════════════════════════════════

TIER 1 — HOT MEMORY (/tmp/ files, session-scoped) ✅
  Purpose: Context available without tool calls
  Files:
    /tmp/legion_session_context.txt    → mem0 memories loaded at boot
    /tmp/legion_hermes_skills.txt      → hermes skills for this session
    /tmp/legion_temporal_context.txt   → gitnexus recent changes
    /tmp/legion_available_skills.txt → skill index
    /tmp/legion_plan.md                → current task plan (shared state)
    /tmp/legion_build_result.md       → @worker output (shared state)
    /tmp/legion_review.md             → @reviewer critique (shared state)
    /tmp/legion_verify.md             → @verifier test results (shared state)
    /tmp/legion_research.md           → @hermes-researcher findings
    /tmp/legion_session_summary.txt    → end-of-session summary
  Read: at session boot (automatic)
  Write: session start hook + end-of-session
  TTL: session only (cleared on reboot)

TIER 2 — WORKING MEMORY (core/working_memory.py, in-process) ✅
  Purpose: Current conversation turns + active task state
  Read/write: core/memory/memory_manager.py facade only
  Never access working_memory.py directly

TIER 3 — EPISODIC MEMORY (SQLite via aiosqlite, 30-day window) ✅
  Purpose: Recent conversations, what Bashara asked about
  Read/write: core/memory/memory_manager.py facade only
  Path: Legion's episodic store (~/.legionswarm/memory/)

TIER 4 — SEMANTIC MEMORY (mem0ai vector store, permanent) ✅
  Purpose: Semantic search over all past knowledge
  Read: hermes_search_memory(query) via hermes MCP
  Write: hermes_write_skill(title, content, tags) via hermes MCP
  Note: mem0ai package installed, imports as `from mem0 import Memory`
  Covers: everything Legion has learned, all skills, all research

TIER 5 — STRUCTURAL MEMORY (.wiki/ Obsidian vault, permanent) ✅
  Purpose: Synthesized knowledge articles, architecture maps, decisions
  Read: obsidian MCP (read, search)
  Write: obsidian MCP (create_note, update_note) — NEVER filesystem
  Rules:
    Structure:
      .wiki/architecture/   → module maps, system diagrams
      .wiki/concepts/       → technical concepts
      .wiki/decisions/      → ADRs (architecture decision records)
      .wiki/entities/       → tools, libraries, external services
      .wiki/bugs/           → fixed P1+ bugs with root cause + fix
      .wiki/research/       → synthesized research from papers/web
      .wiki/health/         → MCP status, service health reports
      .wiki/projects/       → project-level documentation
      .wiki/bashara/        → personal context, preferences, project state

## ══════════════════════════════════════════════════════════
## PART 3: AGENT DISPATCH MATRIX
## When to use which agent and with which MCPs
## ══════════════════════════════════════════════════════════

TIER 1 — CORE 4 (participate in EVERY complex task >3 steps) ✅

  @planner (.opencode/agents/planner.md)
    ROLE: Owns the spec. Breaks task into steps. Sets success criteria.
    NEVER writes code. NEVER edits files. Only plans.
    CALLS: sequential-thinking, hermes_search_memory, gitnexus_context
    TRIGGERS: Any task with >2 steps OR any architectural decision

  @worker (.opencode/agents/worker.md)
    ROLE: Implements against the locked spec from @planner.
    NEVER invents scope beyond the spec. NEVER does architecture.
    CALLS: filesystem, git, gitnexus_search_code
    TRIGGERS: After @planner produces locked spec

  @reviewer (.opencode/agents/reviewer.md)
    ROLE: Adversarial quality gate. Must find flaws BEFORE they ship.
    Outputs: P0 (blocker), P1 (must fix), P2 (should fix), P3 (nice to have)
    CALLS: gitnexus_get_impact, git_diff, filesystem_read
    TRIGGERS: After @worker produces output, before committing

  @verifier (.opencode/agents/verifier.md)
    ROLE: Runs tests. Verifies claims. Pastes proof output.
    CALLS: bash runner (via ruflo), pytest, filesystem
    TRIGGERS: After @reviewer approves, before closing task

TIER 2 — MEMORY & KNOWLEDGE LAYER ✅

  @hermes-agent (.opencode/agents/hermes-agent.md)
    ROLE: Persistent memory, messaging, skill storage, cross-session knowledge
    CALLS: hermes MCP (all 10 tools)
    TRIGGERS:
      - Any "remember/save/note" request
      - Any "do you remember/have we done" query
      - After every task with 5+ tool calls (auto write_skill)
      - After every bug fixed (auto write_skill with "fix:" prefix)
      - At session start (search_memory for context)
      - At session end (write_skill for session summary)

  @hermes-researcher (.opencode/agents/hermes-researcher.md)
    ROLE: Deep research using hermes memory + web MCPs
    CALLS: hermes, exa, crawl4ai
    TRIGGERS:
      - Indonesian law/regulation (PDP, PPh21, NJOP, UMR)
      - Market data (salary benchmarks, real estate prices)
      - Academic papers (ML architectures, pose estimation, Mamba, ViT)
      - Competitive analysis (SaaS, real estate platforms)

  @wikibot (.opencode/agents/wikibot.md)
    ROLE: Obsidian wiki maintainer. Writes structured knowledge articles.
    CALLS: obsidian MCP (write, read, search)
    TRIGGERS:
      - Any new Python module added to architecture
      - Any architectural decision made
      - Any new tool/dependency introduced
      - After research completes (write to .wiki/research/)
      - After a P1+ bug is fixed (write to .wiki/bugs/)

  @paper-wiki-writer (.opencode/agents/paper-wiki-writer.md)
    ROLE: Academic paper → wiki synthesis for ML research
    CALLS: exa, crawl4ai, obsidian, hermes

TIER 3 — CODE SPECIALISTS ✅

  @focused-implementer — single-file implementation, bug fix with clear scope
  @diff-analyzer — large PR review, understanding what changed
  @deployment-engineer — systemd, Docker, nginx, environment setup
  @hermes-coder — Python/AI system coding with hermes memory context
  @research-agent — general research not requiring Hermes memory depth
  @explorer — unknown codebase, new repo discovery, first-time audit

TIER 4 — DOMAIN SPECIALISTS ✅
  agents/legiona/   → Legion bot core (aiogram, llm_client, soul_engine)
  agents/frontend/  → cekwajar.id (Next.js, React, Supabase)
  agents/backend/   → API routes, server actions, edge functions
  agents/ml/        → Research code (PyTorch, pose estimation, Mamba)
  agents/db/        → Supabase schema, aiosqlite, migrations

## ══════════════════════════════════════════════════════════
## PART 4: SWARM PATTERNS
## Named agent sequences for specific task types
## ══════════════════════════════════════════════════════════

PATTERN 1 — STANDARD FEATURE (most common) ✅
  @planner → @worker → @reviewer → @verifier → @wikibot
  Total: 5 agents, sequential

PATTERN 2 — RESEARCH + IMPLEMENT ⚠️
  @hermes-researcher (parallel with) @planner
  → @worker → @reviewer → @hermes-agent (persist) → @wikibot

PATTERN 3 — BUG FIX ✅
  @diff-analyzer → @focused-implementer → @verifier → @hermes-agent
  Total: 4 agents, sequential
  Skip @planner for bug fixes with clear scope

PATTERN 4 — ARCHITECTURE CHANGE ⚠️
  @planner (extended, uses sequential-thinking) →
  @explorer (audit blast radius) →
  @worker → @reviewer → @verifier → @wikibot + @hermes-agent

PATTERN 5 — RESEARCH ONLY ✅
  @hermes-researcher → @hermes-agent → @paper-wiki-writer (if academic)

PATTERN 6 — DEPLOY / OPS ✅
  @deployment-engineer → @verifier → @hermes-agent

## ══════════════════════════════════════════════════════════
## PART 5: INTER-AGENT COMMUNICATION PROTOCOL
## Shared state files — each agent writes its output here
## ══════════════════════════════════════════════════════════

Shared /tmp/ state files (legion_plan.md ecosystem):
  /tmp/legion_plan.md          ← @planner writes spec here
  /tmp/legion_build_result.md  ← @worker writes output here
  /tmp/legion_review.md        ← @reviewer writes critique here
  /tmp/legion_verify.md        ← @verifier writes test results here
  /tmp/legion_research.md      ← @hermes-researcher writes findings here
  /tmp/legion_session_summary.txt ← end-of-session summary

ROLE DISCIPLINE (never violate):
  • @planner writing code → STOP, hand off to @worker
  • @worker inventing architecture → STOP, return to @planner
  • @reviewer approving with no critique found → INVALID (must find P1+)
  • @verifier marking pass without running tests → INVALID

## ══════════════════════════════════════════════════════════
## PART 6: HERMES SKILL FORMAT
## How to write skills for permanent memory
## ══════════════════════════════════════════════════════════

Every hermes_write_skill must follow this structure:

  title: "[verb] [subject]" — e.g., "fix: litellm rate limit fallback"
  content: |
    ## Problem
    [what was happening]
    ## Root Cause
    [why it was happening]
    ## Solution
    [exact code/command/approach]
    ## Prevention
    [what to check next time]
  tags: [relevant, searchable, lowercase]

SKILL WRITE TRIGGERS (automatic — no manual request needed):
  • Any task with 5+ tool calls → write_skill on completion
  • Any bug requiring >2 attempts to fix → write_skill with "fix:" prefix
  • Any research task → write_skill with "research:" prefix
  • Any architecture decision → write_skill with "arch:" prefix
  • Session end → write_skill with "session:" prefix

## ══════════════════════════════════════════════════════════
## PART 7: SELF-EVOLUTION WIRING
## How Legion learns from failures automatically
## ══════════════════════════════════════════════════════════

AFTER EVERY BUG FIX:
  from core.self_evolution import get_self_evolution_engine
  engine = get_self_evolution_engine("/home/newadmin/swarm-bot")
  await engine.record_failure(
    task="[what was being built]",
    approach="[what was tried]",
    failure_mode="[how it failed]",
    root_cause="[why it failed]",
    fix="[what worked]",
    prevention="[check X next time]"
  )

AFTER 5+ FAILURES IN FAILURES.md:
  count = await engine.build_eval_set_from_failures()
  # Builds regression tests automatically

AFTER ANY ARCHITECTURE DECISION:
  await engine.record_decision(
    title="[decision name]",
    context="[why this decision was needed]",
    decision="[what was decided]",
    rationale="[why this option]",
    alternatives=["[option A]", "[option B]"],
    consequences={"good": "...", "risk": "..."}
  )

## ══════════════════════════════════════════════════════════
## PART 8: CONTEXT HEALTH MONITORING
## The "noticedly dumber after compaction" prevention system
## ══════════════════════════════════════════════════════════

Health levels (from core/context_health.py):
  🟢 HEALTHY (0–40%):   normal operation
  🟡 CAUTION (40–60%):   pre-compaction checkpoint required
  🔴 CRITICAL (60–80%):  finish current task, then /compact
  💀 OVERFLOW (80%+):    MANDATORY /compact before ANY new work

Pre-compaction ritual (mandatory before 60%):
  python3 .claude/scripts/wiki_health.py  # if it exists
  Writes: .claude/.checkpoint_index.json + .claude/memory_bootstrap.md

Post-compaction reload order:
  1. Read .claude/memory_bootstrap.md
  2. Read SOUL.md (identity reload)
  3. Read CLAUDE.md Section 0 (safety rules)
  4. Read /tmp/legion_precompact_checkpoint.md
  5. hermes_search_memory("recent checkpoint current task")
  6. git log --oneline -10 && git status

## ══════════════════════════════════════════════════════════
## PART 9: PROJECT CONTEXT SWITCHING
## Legion works on 3 projects. Switch protocol here.
## ══════════════════════════════════════════════════════════

PROJECT REGISTRY:
  swarm-bot  → /home/newadmin/swarm-bot
    Legion bot, aiogram, Python, RTX 3060
    Primary agents: legiona/, hermes-agent, deployment-engineer
    Key MCPs: hermes, gitnexus, ruflo, filesystem, obsidian

  cekwajar   → /home/newadmin/cekwajar.id
    Next.js 15 + React 19 + TypeScript + Supabase
    Primary agents: frontend/, backend/, db/, typescript/
    Key MCPs: gitnexus, filesystem, git, exa (Indonesian law)
    Model: MiniMax M3 for all LLM, Supabase for data

  popw       → /home/newadmin/swarm-bot/project/popw
    Research project, academic writing, LaTeX
    Primary agents: paper-wiki-writer, research-agent, hermes-researcher
    Key MCPs: exa, crawl4ai, obsidian, latex

PROJECT SWITCH PROTOCOL:
  1. Write current project session summary to hermes + /tmp/
  2. hermes_search_memory("[new project] recent state decisions")
  3. gitnexus_search_code("recent changes") in new project directory
  4. Load relevant domain agents for new project
  5. Announce to Bashara: "Switching to [project]. Last I knew: [2-sentence state]."

## ══════════════════════════════════════════════════════════
## PART 10: EMERGENCY PROCEDURES
## When things break — recovery protocols
## ══════════════════════════════════════════════════════════

HERMES DOWN:
  → Continue session. Use /tmp/legion_hermes_skills.txt as cache.
  → Note: cannot write new skills this session.
  → At session end: write skills to /tmp/legion_pending_skills.jsonl

LITELLM PROXY DOWN (port 4000 unreachable):
  → CRITICAL BLOCKER. Report immediately.
  → Command: sudo systemctl restart litellm
  → Check: curl http://localhost:4000/health
  → Do NOT fall back to direct cloud APIs.

GITNEXUS FAILING:
  → Fall back to filesystem_read + grep for code exploration.
  → Note: impact analysis unavailable. Be extra conservative with changes.

CONTEXT OVERFLOW (>80% full):
  → /compact IMMEDIATELY.
  → Do not write another line of code.
  → Run pre-compaction checkpoint first (write to /tmp/).

OBSIDIAN NOT RESPONDING:
  → Write wiki articles to /tmp/wiki_pending/*.md
  → Sync to .wiki/ next session via filesystem_write.

BOT BROKEN (Legion not responding on Telegram):
  → systemctl status swarm-bot.service
  → journalctl -u swarm-bot.service -n 50 --no-pager
  → Check for import errors: python3 main.py 2>&1 | head -30
  → Smoke test: python3 -c "from core.soul_engine import build_soul_context; print('ok')"

## ══════════════════════════════════════════════════════════
## PART 11: MCP FALLBACK CHAINS
## What to do when each MCP fails
## ══════════════════════════════════════════════════════════

exa fails          → crawl4ai → browser-use
hermes fails       → read /tmp/legion_hermes_skills.txt → continue without memory
gitnexus fails     → filesystem_read (manual code exploration)
obsidian fails     → filesystem_write(.wiki/[path]) as fallback
ruflo fails        → use bash via filesystem commands
sequential-thinking fails → reason inline, document steps manually
crawl4ai fails    → browser-use → exa_web_search

NEVER:
  • Call exa AND crawl4ai on the same query (pick one)
  • Write to .wiki/ via filesystem MCP (always obsidian MCP)
  • Call hermes for code execution (hermes = knowledge only)
  • Use browser-use for static page extraction (use crawl4ai)
  • Call gitnexus AFTER modifying code (call it BEFORE)
  • Skip sequential-thinking for tasks > 2 steps
  • Write a skill to hermes without tags

## ══════════════════════════════════════════════════════════
## PART 12: ALIVE CHECKLIST
## The Legion system is fully operational when all items are ✅
## ══════════════════════════════════════════════════════════

CORE INFRASTRUCTURE:
  ✅ mem0ai installed (imports as `from mem0 import Memory`)
  ✅ core/memory/memory_manager.py — 4-tier facade
  ✅ core/context_health.py — health monitor with checkpoints
  ✅ core/self_evolution.py — failure recording + eval set builder
  ✅ SOUL.md — living identity file
  ✅ CLAUDE.md — 1387-line master engineering prompt
  ✅ .wiki/ — 136+ notes, fully structured

SESSION LIFECYCLE:
  ✅ /tmp/legion_session_context.txt — auto-loaded at boot
  ✅ /tmp/legion_hermes_skills.txt — skill index at boot
  ✅ /tmp/legion_temporal_context.txt — recent git changes
  ✅ /tmp/legion_available_skills.txt — hermes skill index
  ✅ /tmp/legion_session_summary.txt — end-of-session write
  ⚠️ /tmp/legion_plan.md — shared state (create template)
  ⚠️ /tmp/legion_build_result.md — shared state (create template)
  ⚠️ /tmp/legion_review.md — shared state (create template)
  ⚠️ /tmp/legion_verify.md — shared state (create template)

MCP SERVERS (12/12 live per preflight):
  ✅ gitnexus, obsidian, git, filesystem, exa, crawl4ai
  ✅ symphony, latex, ruflo, sequential-thinking, hermes, browser-use

AGENT FILES (15 agents defined):
  ✅ planner.md, worker.md, reviewer.md, verifier.md
  ✅ hermes-agent.md, hermes-coder.md, hermes-researcher.md
  ✅ wikibot.md, paper-wiki-writer.md
  ✅ focused-implementer.md, diff-analyzer.md, deployment-engineer.md
  ✅ research-agent.md, compaction.md

OPERATIONAL SCRIPTS:
  ⚠️ .claude/scripts/wiki_health.py — does NOT exist (create)
  ✅ .claude/scripts/update_compile_state.py — exists
  ✅ core/context_health.py — fully implemented

WIKI STRUCTURE:
  ✅ .wiki/decisions/ — 20+ ADRs
  ⚠️ .wiki/decisions/README.md — does NOT exist (create index)
  ✅ .wiki/health/ — exists
  ✅ .wiki/architecture/ — exists

COMPACTION:
  ✅ .opencode/agents/compaction.md — 9-section format defined
  ⚠️ Pre-compaction checkpoint ritual — partially defined in CLAUDE.md
  ✅ Post-compaction reload order — defined in CLAUDE.md

## ══════════════════════════════════════════════════════════
## LEGION SYSTEM STATUS: 85% OPERATIONAL
## Critical gaps remaining:
##   1. Shared /tmp/ state file templates (5 files)
##   2. .claude/scripts/wiki_health.py (create)
##   3. .wiki/decisions/README.md index (create)
##   4. Session bootstrap hook (wire into OpenCode pre-session)
## ══════════════════════════════════════════════════════════
