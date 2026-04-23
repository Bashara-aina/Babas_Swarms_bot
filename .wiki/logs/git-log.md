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
