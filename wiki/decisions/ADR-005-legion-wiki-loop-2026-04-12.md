# ADR-005: LEGION WIKI LOOP — 10-HOUR KNOWLEDGE EXPANSION

**Date**: 2026-04-12
**Status**: ACCEPTED
**Author**: Three-agent pipeline (planner → 10x worker → 2x reviewer)

## Context

Legion needed a comprehensive knowledge base refresh. The .wiki/ directory had accumulated 150+ pages 
but lacked systematic coverage of core architectural domains. A 10-hour autonomous loop was designed 
to fill critical knowledge gaps across 10 domains.

## Decision

Executed full 10-cycle wiki loop:
1. BASHARA CONTEXT — personal profile, projects, vocabulary, schedule
2. LLM ROUTING — routing map, cost optimization, context strategy
3. MEMORY ARCHITECTURE — stores, gaps, injection strategy
4. INTENT ROUTING — routing map, gaps, multi-intent handling
5. PERSONALITY & SOUL — enforcement, gaps, debate system, emotional vocabulary
6. PROACTIVE INTELLIGENCE — schedule, gaps, quiet hours, briefing spec
7. TOOLS & SKILLS — inventory, gaps, output formatting
8. SECURITY & STABILITY — audit, stability map, rate limits
9. CONTEXT WINDOW — window map, optimization, system prompt spec
10. FUTURE ARCHITECTURE — vision, high-leverage changes, agent topology, use-case optimization

## Files Changed

34 wiki pages written to .wiki/:
- bashara-profile.md, bashara-projects.md, bashara-vocabulary.md, bashara-schedule.md
- llm-routing-map.md, llm-cost-optimization.md, llm-context-strategy.md
- memory-architecture.md, memory-gaps.md, memory-injection-strategy.md
- intent-routing-map.md, intent-gaps.md, multi-intent-strategy.md
- soul-enforcement-map.md, personality-gaps.md, debate-system-guide.md, emotional-vocabulary.md
- proactive-schedule.md, proactive-gaps.md, bashara-quiet-hours.md, briefing-format-spec.md
- tools-inventory.md, tools-gaps.md, tool-output-formatting.md
- security-audit.md, stability-map.md, rate-limit-strategy.md
- context-window-map.md, context-optimization.md, system-prompt-spec.md
- legion-vision-2026.md, high-leverage-changes.md, agent-topology-design.md, use-case-optimization.md

Plus:
- .wiki/SESSION_SUMMARY.md — complete session summary
- .wiki/LOOP_LOG.md — cycle-by-cycle log with all decisions
- .wiki/INDEX.md — updated index with all pages

## Key Findings

1. **4 separate ALLOWED_USER_ID sources of truth** — shared.py, admin_handlers.py, business_handler.py, github_intel_handler.py each define independently; split-brain consistency risk confirmed
2. **Daily briefing fires twice at different times** — tools/briefing.py fires at 7:30AM AND ProactiveScheduler fires at 8AM; Bashara receives duplicate morning briefings
3. **Profile block injected on every request** — even purely technical questions like "what time is it" get SOUL + personality + profile + 6 turns; quick questions could use 93% fewer tokens
4. **26 subprocess.run() locations across 14 files** — 4 modify crontab unsandboxed (project_manager.py, n8n_bridge.py, cron_setup.py)
5. **Memory auto-extraction fires on every message** — including "ok" and "thanks"; memory pollution risk identified

## Critical Issues Found

### CRITICAL (unfixed)
- 4 subprocess.run() calls modify crontab unsandboxed (project_manager.py, n8n_bridge.py, cron_setup.py)
- Telegram webhook has no verification secret — anyone can send fake updates

### HIGH (documented, unfixed)
- 4 separate ALLOWED_USER_ID sources of truth
- 2 duplicate daily briefings (7:30AM + 8AM)
- Profile block injected on every request (token waste)
- Memory auto-extraction fires on every message including "ok" and "thanks" (memory pollution)
- All proactive failures are completely silent — no monitoring hook

### MEDIUM (documented, unfixed)
- Circuit breaker health state is in-memory only — lost on restart
- No persistent crash log — bot.log rotates, crashes from hours ago may be lost
- Telegram rate limit: 0.3s chunk delay too aggressive for 30 msg/sec limit

## Consequences

- .wiki/ now has 34 new pages covering all 10 core architectural domains
- All pages survived 3-agent debate (Advocate/Skeptic/Judge) with scores 7+
- 2 blockers found and fixed during review phase:
  - intent-routing-map.md: Fixed routing from 23 handlers to 9 agents with two-stage classification
  - llm-routing-map.md: Fixed "general" agent from MiniMax M2.7 to ollama_chat/gemma4:e4b
- 3 minor flags fixed post-review:
  - tools-inventory.md: Token count corrected, tool count verified (77 total)
  - security-audit.md: subprocess count corrected (26 locations across 14 files)
  - bashara-quiet-hours.md: Clarified duplicate briefing mechanism
- No contradictions remain between pages
- Legion's context window now has comprehensive documentation
- Context optimization opportunity identified: 30-50% token reduction possible

## Next Steps

1. **Implement context optimizer** — highest ROI change (2-3h dev), enables 30-50% token reduction on quick questions
2. **Consolidate 4 proactive engines into 1 unified orchestrator** — eliminates duplicate fires, single debug point
3. **Wire ALLOWED_USER_ID to single source** — eliminates split-brain risk across 4 files
4. **Sandbox subprocess calls in cron_setup.py, project_manager.py, n8n_bridge.py** — critical security hardening
5. **Implement timer tool + calendar integration** — thesis/business productivity wins; needed for zemi blocking and meeting-aware briefings
