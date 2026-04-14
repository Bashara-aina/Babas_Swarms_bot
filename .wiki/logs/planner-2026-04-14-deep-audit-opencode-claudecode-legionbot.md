## Plan: Deep Audit — OpenCode, Claude Code, LegionBot
Date: 2026-04-14
Type: RESEARCH

## Context Gathered

### OpenCode (`/home/newadmin/.opencode/`)
- Minimal Node.js project with package.json, node_modules
- No agents/ directory visible — likely installed via npm globally
- Need to audit how it's wired into swarm-bot via bridges/

### Claude Code (`/home/newadmin/.claude/`)
- CLAUDE.md exists (1878 bytes) — needs verification vs implementation
- settings.json, session data, .credentials.json (sensitive)
- projects/, plugins/, tasks/ directories

### swarm-bot (`/home/newadmin/swarm-bot/`)
- AGENTS.md claims: 76+ specialized agents, 45+ handlers, 9 departments
- CLAUDE.md exists (28KB) — extensive documentation
- Wiki at .wiki/ with 129 articles per INDEX.md
- Multiple subsystems: handlers/, core/, tools/, agents/, config/, bridges/, swarms_bot/
- LLM client: llm_client.py + llm_client/ package
- Budget guard: BudgetManager vs litellm call sites

## Risk Assessment

1. **OpenCode integration** — may not be fully wired; if OpenCode is used as external CLI, task dispatch may be lossy or blocking
2. **Intent routing accuracy** — AGENTS.md claims 45+ handlers but actual count unknown
3. **Agent count accuracy** — claims 76+ agents but actual registry count unknown  
4. **BudgetManager coverage** — litellm calls that bypass budget tracking could cause cost overruns
5. **Async compliance** — blocking I/O could still exist in handlers/core
6. **Wiki health** — frontmatter, YAML validity, orphaned wikilinks post-fixes
7. **Memory architecture** — facade vs mem0 vs memory_manager confusion

## Approach

Decompose into 6 contracts:
1. OpenCode architecture audit (integration points, agent defs, configs)
2. Claude Code audit (CLAUDE.md claim verification)
3. swarm-bot codebase health (handlers, core, agents, tools, config counts)
4. Budget guard coverage (litellm call sites vs BudgetManager)
5. Wiki health (frontmatter, YAML, orphans)
6. Async compliance + memory architecture

Each contract produces findings for one major subsystem.
