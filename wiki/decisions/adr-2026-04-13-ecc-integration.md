---
title: adr-2026-04-13-ecc-integration
type: decision
status: active
tags: [architecture, integration, ecc, agents]
created: 2026-04-13
updated: 2026-04-13
summary: Integrated Everything Claude Code (ECC) as ext/everything-claude-code/ — 13 specialized agents, 6 high-value skills, hooks reference, and language rules.
wikilinks:
  - [[ext/everything-claude-code]]
  - [[concepts/multi-agent-orchestration]]
confidence: high
source: implementation
---

# ADR-2026-04-13: Everything Claude Code Integration

**Date**: 2026-04-13
**Status**: Accepted
**Decider**: Bashara + Legion

## Context

The swarm-bot had 84 domain/task-focused agents via `config/departments.yaml`. The
[Everything Claude Code](https://github.com/affaan-m/everything-claude-code) project
(140K+ stars, 47 specialized coding agents, 181 skills, 17 hooks) offered premium
agents not present in the existing roster — specifically: `code-reviewer`,
`security-reviewer`, `tdd-guide`, `build-error-resolver`, `refactor-cleaner`,
`e2e-runner`, `loop-operator`, `performance-optimizer`, `harness-optimizer`,
`architect`, `silent-failure-hunter`, `type-design-analyzer`.

The integration goal: selectively import the most valuable ECC components without
replacing or duplicating the existing 84-agent system.

## Decision

We integrated ECC as a standalone extension package at `ext/everything-claude-code/`
with a Python facade at `ext/everything_claude_code/__init__.py`.

### What Was Imported

| Component | Count | Location |
|-----------|-------|----------|
| Agents | 13 | `ext/everything-claude-code/agents/` |
| Skills | 6 dirs | `ext/everything-claude-code/skills/` |
| Hooks reference | 17 hooks | `ext/everything-claude-code/hooks/` |
| Language rules | 3 dirs | `ext/everything-claude-code/rules/` |

### What Was NOT Imported

- Language-specific reviewers (already covered by swarm-bot's 84-agent roster)
- GAN-related agents (outside project scope)
- Domain-specific agents (healthcare, flutter, etc.)
- Node.js hook scripts (not applicable to Python/aiogram bot)

### Integration Module

`ext/everything_claude_code/__init__.py` provides:
- `ECC_AGENTS` dict — 13 agent definitions with model, temperature, tools, domain
- `ECC_SKILLS` dict — 6 skill definitions with paths
- `load_agent_prompt(key)` — loads raw markdown prompt for an agent
- `load_skill_content(key)` — loads raw SKILL.md content
- `get_ecc_agent(key)` — get agent definition by key
- `list_ecc_agents()` / `list_ecc_skills()` — listing helpers
- `verify_installation()` — smoke test for all paths

### Agent Assignment

All 13 ECC agents use `minimax/MiniMax-M2-7` via OpenRouter with temperature
settings appropriate to their function:
- `temperature=0.0` — security-reviewer, build-error-resolver, loop-operator,
  harness-optimizer, silent-failure-hunter (deterministic, no creativity)
- `temperature=0.1` — planner, architect, tdd-guide, refactor-cleaner,
  e2e-runner, performance-optimizer, type-design-analyzer (structured creativity)
- `code-reviewer` uses `temperature=0.0` (strict, no false positives)

## Consequences

### What Is Now Easier
- Running ECC-style `code-reviewer` on any code change in swarm-bot
- TDD workflow enforcement via `tdd-guide` agent
- Security review via `security-reviewer` before commits
- Autonomous loop monitoring via `loop-operator`
- Performance profiling via `performance-optimizer`

### What Is Now Harder
- Two agent sources to maintain (departments.yaml + ECC)
- Potential routing ambiguity if ECC agent keywords overlap with existing routing

### Alternatives Considered

**Option A — Copy prompts into departments.yaml**: Rejected. Would duplicate
ECC's markdown prompts in YAML, losing formatting and making updates harder.

**Option B — Fork ECC agents into agents.py**: Rejected. Would diverge from ECC
upstream and make updates impossible.

**Option C — ECC as ext/ package (chosen)**: Clean separation, ECC can be
updated independently, swarm-bot references ECC as a data layer.

## Implementation

```
ext/
├── everything-claude-code/     ← ECC data (markdown agents, skills, hooks)
│   ├── agents/                  ← 13 .md agent prompts
│   ├── skills/                  ← 6 skill directories with SKILL.md
│   ├── hooks/                   ← hooks.json + reference docs
│   └── rules/                   ← common/, python/, typescript/ rules
└── everything_claude_code/      ← Python facade package
    └── __init__.py              ← ECC_AGENTS, load_agent_prompt(), etc.
```

## Next Steps

- Wire ECC agents into `config/routing_keywords.yaml` for `/run` command routing
- Add `ECC_AGENTS` to `core/agent_registry.py` as secondary lookup
- Implement Python equivalents of key ECC hooks (pre-commit lint, secrets detection)
- Add ECC agent prompts to `system_prompt_builder.py` when `code-reviewer` or
  `security-reviewer` is invoked

## See Also

[[ext/everything_claude_code/__init__]] — Integration module
[[concepts/multi-agent-orchestration]] — How agents coordinate
[[wiki/projects/legion-bot]] — Legion bot project
