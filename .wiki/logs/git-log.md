---
title: Git Log
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

## Commit: 1824110
- Date: Tue Apr 21 10:16:08 PM JST 2026
- Message: feat(legiona): LEGIONA ULTIMATE INTELLIGENCE AUDIT v2.0 — M2.7 maximized
---
## Commit: 2d03f08
- Date: Tue Apr 21 10:31:46 PM JST 2026
- Message: fix(claude.md): compress to 27KB while preserving all essential sections

Compression achieved:
- 43,677 → 27,548 bytes (16,129 byte reduction)
- Preserved: Safety Rules, Anti-Hallucination, Agent System, M2.7 Self-Evolution, Uncertainty Output

Refs: swarm-2026-04-21-legiona-ultimate-audit-v2
---
## Commit: 7caf6f6
- Date: Tue Apr 21 10:32:37 PM JST 2026
- Message: docs: add swarm audit v2 log

Pipelines executed:
- explorer (3x): pre-flight, diff-analyzer (2x)
- worker (4x): 10 contracts + 1 correction
- reviewer (3x): final approval on 3rd attempt

Ref: swarm-2026-04-21-legiona-ultimate-audit-v2
---
## Commit: 4ae4b45
- Date: Tue Apr 21 11:36:01 PM JST 2026
- Message: feat: Legiona self-evolution + omega audit — 8-pillar anti-hallucination, M2.7 optimization, wiki hygiene

- Security: Removed monkey-patching in main.py, wildcard git permissions fixed
- Anti-hallucination: Expanded from 5 to 8 pillars (Pillars 6-8 added)
- CLAUDE.md: +5KB with sections 0n-0r (reasoning_split, 8-pillar, self-evolution, regression gating)
- Copilot: Enhanced to 400 lines with LEGIONA v3 / M2.7 / 8-pillar guidance
- Memory: global_memory.md v3.0, rules.md v3.0 with timestamps
- Wiki hygiene: ORPHAN_TRIAGE.md created, compile_state.json updated
- 10 new documentation artifacts created (OMEGA_BASELINE, OMEGA_UPGRADE_REPORT, etc.)
- All verified by @Diff-Analyzer: 28/28 checks passed
---
## Commit: f06744e
- Date: Wed Apr 22 03:29:22 PM JST 2026
- Message: feat: add intent classification, task planning, and cognitive context injection to /do command

- Replaced fragile exec_keywords detection with classify_intent()
- Added _plan_task() + _is_complex_task() for strategic planning
- Complex tasks now use computer_use_loop (vision-action-verify)
- agent_loop now injects soul, GSA, memory, narrative context
- Multi-strategy self-healing: sanitized retry → re-parsed → computer_use_loop fallback
- Hard cap at _MAX_ATTEMPTS=5 to prevent infinite loops
- Backward compatible: simple tasks still go directly to _run_agent_loop
---
## Commit: 7aff6c9
- Date: Wed Apr 22 04:19:46 PM JST 2026
- Message: feat: command compaction, /do optimization, OMEGA audit v4.0 — full legiona self-evolution

Command compaction:
- /task_done → /mneme_done (session_handler.py vs pm.py conflict resolved)
- 17 thin-wrapper system commands auto-routed via intent classification
- /workernet_papers, /orchestrate_legacy deprecated with redirects
- /audit_summary → /audit, /loop_start → /loop

/do optimization:
- Intent classification replaces fragile exec_keywords
- Complex tasks route to computer_use_loop (vision-action-verify)
- Cognitive context injected into agent_loop (soul, GSA, memory, narrative)
- Multi-strategy self-healing: sanitized retry → re-parse → computer_use_loop fallback
- _MAX_ATTEMPTS=5 hard cap

OMEGA AUDIT v4.0:
- Anti-hallucination: 5→8 pillars (P6-8 added)
- CLAUDE.md: +5KB with reasoning_split, 8-pillar, self-evolution, regression gating
- .claude/settings.json: ANTHROPIC_REASONING_SPLIT=true
- Copilot instructions: 209→400 lines
- Memory: global_memory.md v3.0, rules.md v3.0
- Monkey-patching removed from main.py
- 11 new OMEGA documentation artifacts created
- Wiki hygiene: ORPHAN_TRIAGE.md, compile_state.json updated
- 300+ orphaned wiki files quarantined
---
## Commit: 3b6b832
- Date: Wed Apr 22 09:49:23 PM JST 2026
- Message: audit: MCP cross-editor config parity findings

- Git: duplicate MCP servers (mseep vs modelcontextprotocol official)
- Exa: remote vs local architecture mismatch
- Obsidian: config/mcp_config.json references wrong disabled package
- Firecrawl: CONSISTENT across all configs
- Filesystem/GitNexus: CONSISTENT across all configs

Audit complete per swarm pipeline
---
## Commit: 3966a7c
- Date: Wed Apr 22 10:59:51 PM JST 2026
- Message: fix: remove dead output dict assignments in handlers/pm.py and handlers/research.py

Remove unused output = {...} dict assignments in exception/success handlers across 9 locations in pm.py and research.py. These were dead code since the error/success state was already communicated via message edits/answers.

Fixes remaining F841 (local variable assigned but never used) lint errors.
---
## Commit: 8b0ffca
- Date: Wed Apr 22 11:11:52 PM JST 2026
- Message: fix: resolve all CI-blocking lint and import errors

- Quote minimax/MiniMax-Text-01 model IDs in DEBATE_PERSONA_MODELS (SyntaxError)
- Remove ContextTypes import from handlers/ai.py (aiogram has no ContextTypes)
- Add asyncio import to handlers/media_tools.py (F821)
- Add html import to handlers/memory_commands.py (F821)
- Remove stray urlrequest block from _ruflo_restart_monitor in main.py
- Remove unnecessary f-strings and unused variables in handlers/gstack.py
- Strip trailing whitespace in core/utils/error_formatter.py, feedback_animator.py, loading_manager.py (W293)

Fixes: SyntaxError in agents/__init__.py, ImportError for ContextTypes in handlers/ai.py, and all F821/F541/W293 lint errors.
---
## Commit: cafa735
- Date: Wed Apr 22 11:21:21 PM JST 2026
- Message: fix: remove threads_mode from handlers/__init__.py to resolve circular import

threads_mode module is untracked and not in the repo, causing
ImportError: cannot import name 'threads_mode' from partially initialized module 'handlers'
during pytest collection and wiring verification.
---
## Commit: 35f811c
- Date: Wed Apr 22 11:47:50 PM JST 2026
- Message: fix: resolve 5 duplicate command pairs — /screen /type /key /loop_start /audit_summary /task_done

- Remove /screen /type /key from legiona_tools.py (router order meant computer.py
  versions were shadowed — /screen only returned file path, not photo)
- computer.py now correctly handles /screen (photo + inline keyboard), /type, /key
- Remove /loop_start redirect from ecc_compat.py (canonical /loop in ai.py)
- Remove /audit_summary redirect from enterprise.py (canonical /audit in sessions.py)
- Remove /task_done redirect from pm.py (canonical /mneme_done in session_handler.py)
- All redirects already told users to use the canonical command
---
## Commit: 8351e3d
- Date: Wed Apr 22 11:49:00 PM JST 2026
- Message: chore: prune wiki quarantine revivals and stale research files

Delete 300+ orphaned wiki files: old quarantine revivals, stale session logs,
obsolete research artifacts, old .wiki/concepts/* and .wiki/issues/* files.
These were generated during audit cycles and are no longer relevant.
---
## Commit: 8d3e0ae1
- Date: Mon Apr 27 10:11:50 PM JST 2026
- Message: test
---
## Commit: c41ced95
- Date: Mon Apr 27 10:12:09 PM JST 2026
- Message: opencode skill files updated
---
## Commit: 83906757
- Date: Sat May  2 09:27:06 PM JST 2026
- Message: chore: sync AGENTS.md
---
## Commit: cc4222b5
- Date: Sat May  2 09:27:41 PM JST 2026
- Message: chore: sync main.py
---
## Commit: 56a57d02
- Date: Sat May  2 09:28:00 PM JST 2026
- Message: chore: sync CLAUDE.md
---
## Commit: e2bdf39c
- Date: Sat May  2 09:28:09 PM JST 2026
- Message: chore: sync requirements.txt
---
## Commit: 9034a470
- Date: Sat May  2 09:28:18 PM JST 2026
- Message: chore: sync core/
---
## Commit: 4a842026
- Date: Sat May  2 09:28:24 PM JST 2026
- Message: chore: sync handlers, tools, config
---
## Commit: f1d78514
- Date: Sat May  2 10:07:32 PM JST 2026
- Message: feat(browser): add browser-use + agent-browser routing layer (MiniMax-only)

- browser-use MCP server already present (browser_open, browser_click, etc.)
- Added browser_task_router.py with crawl4ai vs browser-use auto-routing
- Added /browse slash command (quick navigation alias)
- Added browser department agents (browser-automation, web-researcher)
- Added WORKFLOW.md for symphony orchestration
- Added .wiki/architecture/browser-stack.md documentation
- Updated .env with AI_GATEWAY_* vars for MiniMax-only enforcement
- Added browser-use.json config validation
- E2E verification: import, guard, MCP handshake, smoke test all PASS
- steel-browser skipped (Docker unavailable on this host)
- Agent-browser 0.26.0 already installed
---
## Commit: 63619461
- Date: Sat May  2 11:51:52 PM JST 2026
- Message: feat(browser): add browser-use runner, agent_browser_safe shell wrapper, and browser-use skill

- tools/browser_runner.py: run_browser_task() using browser-use Agent + MiniMax LLM
- scripts/agent_browser_safe.sh: MiniMax-only guard wrapper for agent-browser CLI
- .opencode/skills/browser-use.md: skill reference for browser-use library
---
## Commit: 4f3ff94f
- Date: Sun May  3 12:35:10 AM JST 2026
- Message: fix(agents): remove invalid tools array from browser agent frontmatter

The tools field was causing 'Expected object | undefined' validation error
in web-researcher.md. Removed tools field from both browser agents to match
planner.md pattern (no tools key = all tools allowed).
---
## Commit: 51ebcfa8
- Date: Sun May  3 08:21:03 AM JST 2026
- Message: fix(browser): lint fix — remove unused subprocess import, fix ambiguous variable name
---
## Commit: 1913e000
- Date: Sun May  3 08:25:51 AM JST 2026
- Message: feat(browser): add /browser slash command
---
## Commit: 37288041
- Date: Sun May  3 08:28:13 AM JST 2026
- Message: feat(browser): add browser-use safe wrapper with MiniMax guard
---
## Commit: e3e3383d
- Date: Sun May  3 08:28:19 AM JST 2026
- Message: feat(browser): add browser and browse slash commands, browser-use and agent-browser skills, browser automation agents
---
## Commit: a886fae1
- Date: Sun May  3 08:37:14 AM JST 2026
- Message: feat(browser): update browser runner with actual API key env, improve retry/temp settings
---
## Commit: 79d745fb
- Date: Sun May  3 08:37:44 AM JST 2026
- Message: feat(browser): add browser-use and agent-browser project configs, runner scripts
---
## Commit: d77eeb5e
- Date: Sun May  3 08:38:12 AM JST 2026
- Message: docs(browser): add browser-use discovery and install logs
---
## Commit: 8af5d8a2
- Date: Sun May  3 09:09:27 AM JST 2026
- Message: wiring(opencode): add Ultimate Internal Master Prompt v3 with all 15 phases

What changed:
- Created OPENCODE_ULTIMATE_MASTER.md (524-line reference doc covering all 15 phases)
- Created .opencode/scripts/health-check.sh (executable, Phase 10 health dashboard)
- Created 6 slash commands: health, lint, preflight, hermes-status, agents, skill
- Fixed compaction.md and title.md agent files (added Role/Behavior Rules/Output Contract)
- Updated watcher ignore list in opencode.json (.venv, flatpak, pdf, zip patterns)
- Updated .gitignore with binary blob patterns
- Appended @OPENCODE_ULTIMATE_MASTER.md reference to CLAUDE.md

Why:
- Phase 0: Pre-flight ensures clean environment at every session start
- Phase 7: Agent file quality standard prevents routing failures
- Phase 10: Health dashboard provides single-command stack verification
- Phase 15: Binary blobs (68MB+ flatpak/pdf/zip) removed from git tracking

Files affected: .opencode/, OPENCODE_ULTIMATE_MASTER.md, CLAUDE.md, .gitignore
---
## Commit: de687eb2
- Date: Sun May  3 09:26:19 AM JST 2026
- Message: refactor(opencode): add Phase 7 sections to all 15 flat agent files

What changed:
- Added ## Role, ## Behavior Rules, ## Tool Usage, ## Output Contract to all 15 flat agents
- Agents: hermes-agent, hermes-coder, hermes-researcher, planner, worker, reviewer, verifier, focused-implementer, diff-analyzer, wikibot, research-agent, deployment-engineer, paper-wiki-writer

Why:
- Phase 7 (Agent File Quality Standard) requires all 5 sections for routing integrity
- Consistent structure enables mechanical validation via health-check.sh
- Tool Usage and Output Contract sections provide explicit contract for agent behavior

Files affected: .opencode/agents/*.md (13 files, +622/-23)
---
## Commit: 8828598f
- Date: Sun May  3 09:43:13 AM JST 2026
- Message: feat(opencode): enhance plan/research/swarm slash commands with mandatory sequences

What changed:
- plan.md: Added mandatory sequential thinking + memory search before planning
- research.md: Added GraphRAG wiki query first, web search fallback, Exa integration
- swarm.md: Added boot sequence, ruflo orchestration tools, session persistence

Why:
- Phase 0 (pre-flight) and Phase 2 (routing) require these commands to follow structured sequences
- research.md now queries wiki graph before web search (avoid redundant research)
- swarm.md now properly initializes ruflo swarm with task tracking

Files affected: .opencode/command/plan.md, research.md, swarm.md (+185/-24)
---
## Commit: 5b0c19b5
- Date: Sun May  3 10:37:53 AM JST 2026
- Message: fix(agents): convert tools lists to maps in hermes-researcher and hermes-coder

hermes-researcher.md and hermes-coder.md had tools as YAML lists
but OpenCode requires tools as a map {tool_name: boolean}.
Fixed: web_search, web_extract, session_search, browser_navigate,
delegate_task, terminal, read_file, write_file, patch, search_files,
execute_code now all specified as tools: {name}: true.
---
## Commit: 43184f9e
- Date: Sun May  3 01:21:49 PM JST 2026
- Message: feat(docs): wire LEGION cognitive architecture into OpenCode agent system

Phase 16 appended to OPENCODE_ULTIMATE_MASTER.md — cognitive flow,
4-phase reasoning loop, 5-tier memory pyramid, agent dispatch matrix,
compaction protocol, session lifecycle, project switching manifest.

New docs:
- LEGION_MASTER_PROMPT.md (12 sections, boot through metacognition)
- LEGION_SYSTEM.md (companion reference doc)
- elite-stack-*.md (session lifecycle + initialization docs)
- ruflo-memory-routing.md, project-switching-manifest.md
- research/056-smote-chawla-2002.md, 091-cutmix-yun-2019.md

Wiki YAML fixes (6 files):
- tools/: threads-*.md — multiline sources: blocks → valid YAML nested format
- _archive/: popw-*.md — unclosed summary: quotes fixed
- detectron2/: 4 dead symlinks removed

New scripts:
- .claude/scripts/wiki_health.py (wiki linter)
- scripts/ingest_wiki_to_graphiti.py
- tests/test_wiki_auto_ingest.py

Scope: wiki health + new master prompt infrastructure only.
No agent behavior changes — gap was orchestration documentation.
---
## Commit: 76e1a72f
- Date: Sun May  3 03:05:39 PM JST 2026
- Message: feat(legion): implement cognitive orchestration infrastructure

New Python modules for OpenCode session lifecycle:
- core/legion_state.py: /tmp/ shared state bus (12 state files)
- core/legion_session.py: session lifecycle, context health, task classification
- core/legion_compaction.py: 9-section mandatory compaction format
- core/legion_skill_indexer.py: auto-generates /tmp/legion_available_skills.txt

Updated agent files with Phase 16 cognitive wiring:
- planner.md: 4-phase loop + 6 swarm dispatch patterns
- worker.md: Phase D mandatory persistence
- hermes-agent.md: 5-tier memory pyramid + write_skill protocol
- reviewer.md: P0-P3 severity findings format
- compaction.md: 9-section mandatory format
- CLAUDE.md: Python infrastructure + emergency procedures
---
## Commit: 4600cbf1
- Date: Sun May  3 03:14:30 PM JST 2026
- Message: feat(legion): implement cognitive boot + 5-tier memory pyramid + missing agents

New infrastructure:
- core/cognition_boot.py: OpenCode cognitive boot (STEP 1-4 identity/memory/health/task)
- core/TIER.py: 5-tier memory pyramid constants, write routing table, file paths
- .claude/memory_bootstrap.md: session-start memory cache template

4 missing agents created:
- .opencode/agent/explorer.md: codebase discovery + architecture audit
- .opencode/agent/lsp-reader.md: type-aware analysis via LSP
- .opencode/agent/collaborator.md: parallel workstream coordination
- .opencode/agent/memory.md: cross-session knowledge synthesis

CLAUDE.md Section 0 rewritten:
- Boot sequence (1-7 steps at session start)
- 5-tier memory pyramid table
- Cognition boot + TIER references

CLAUDE.md Section 15j-k added:
- 15j: Metacognition layer (self-check, ambiguity threshold, loop detection)
- 15k: Definition of a perfect session

SOUL.md: cognitive architecture awareness added to identity
---
## Commit: f028cb1d
- Date: Sun May  3 03:52:20 PM JST 2026
- Message: audit: system audit 2026-05-03 — 103/150 ⚠️ GOOD

P0: no hooks in opencode.json, 3785 ruff errors
P1: LiteLLM no_db, Supabase down, systemd inactive, 650 wiki stubs
P2: 3593 broken wikilinks, 80 pyright errors

Fixed:
- SOUL.md: added Projects known section
- docs/review/security/wiki/plan-ceo-review: added steps sections
- deploy/swarm-bot.service: systemd unit file created
- .wiki/health/audit-2026-05-03.md: full scorecard

Score: 103/150 ⚠️ GOOD
---
## Commit: 4ef0baa8
- Date: Sun May  3 04:23:43 PM JST 2026
- Message: fix: pyright errors, hermes skill integration, liteLLM config, hooks, wiki stubs

- handlers/shared.py: narrow msg.from_user None guard, fix int→str for user_id
- core/wiki_auto_ingest.py: replace undefined complete/get_model_for_task with chat()
- core/utils/streaming_response.py: guard interpreter.chat() None iterable
- core/self_evolution.py: add _write_hermes_skill() + integrate into record_failure/record_decision
- config/litellm_proxy_config.yaml: add store_model_results: false + no-cache + disable_constraints for no_db fix
- .opencode/opencode.json: add hooks section (session:start/end, task:complete)
---
