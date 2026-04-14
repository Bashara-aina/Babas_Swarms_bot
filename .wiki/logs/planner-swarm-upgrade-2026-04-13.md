---
title: Planner Swarm Upgrade 2026 04 13
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
summary: '- Existing /swarm command at .opencode/command/swarm.md (207 lines, v2.0
  already but needs reinforcement)'
wikilinks: []
confidence: medium
source: research
---
## Plan: SWARM-Master v2.0 Upgrade — Anti-Hallucination Enforcement
Date: 2026-04-13
Type: FILE_OPERATION
Context gathered:
- Existing /swarm command at .opencode/command/swarm.md (207 lines, v2.0 already but needs reinforcement)
- 8 agents identified in .opencode/agents/: planner.md, worker.md, reviewer.md, verifier.md
- 4 agents in .opencode/agent/: research-agent.md, deployment-engineer.md, diff-analyzer.md, focused-implementer.md, paper-wiki-writer.md
- WikiBot at .opencode/agents/wikibot.md
- Target agents: @Planner, @Worker, @Reviewer, @Diff-Analyzer, @Build, @Wikibot, @Research-Agent, @Deployment-Engineer

Risk assessment:
- Overwriting existing agent prompts could break active workflows if new prompts are incompatible
- Missing Build agent prompt - need to check if it exists or create new
- Verifier agent not in original 8 list but exists in codebase

Approach:
- Batch 1 (contracts 1-5): Write swarm.md + upgrade 4 core agents (planner, worker, reviewer, wikibot)
- Batch 2 (contracts 6-10): Upgrade 4 additional agents (diff-analyzer, research-agent, deployment-engineer, focused-implementer)
- Batch 3 (contract 11): Write upgrade log
- Use anti-hallucination enforcement section in each agent prompt
- Verify all writes with grep commands
