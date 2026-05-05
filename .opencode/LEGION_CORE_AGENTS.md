# LEGION CORE AGENTS — Complete Specification

> These are the only agents actively used by the swarm routing system.
> All have proper `## Role`, `## Trigger`, `## Tools`, and `## Output` sections.
> AutoGen marketplace agents in `.opencode/agents/*/` are reference-only (not invoked).

## Agent Index

| Agent | File | Department | Active? |
|-------|------|------------|----------|
| planner | `.opencode/agents/planner.md` | Core | YES |
| worker | `.opencode/agents/worker.md` | Core | YES |
| reviewer | `.opencode/agents/reviewer.md` | Core | YES |
| wikibot | `.opencode/agents/wikibot.md` | Core | YES |
| hermes-agent | `.opencode/agents/hermes-agent.md` | Memory | YES |
| hermes-coder | `.opencode/agents/hermes-coder.md` | Memory | YES |
| hermes-researcher | `.opencode/agents/hermes-researcher.md` | Memory | YES |
| collaborator | `.opencode/agent/collaborator.md` | Orchestration | YES |
| explorer | `.opencode/agent/explorer.md` | Orchestration | YES |
| memory | `.opencode/agent/memory.md` | Memory | YES |
| focused-implementer | `.opencode/agents/focused-implementer.md` | Execution | YES |
| diff-analyzer | `.opencode/agents/diff-analyzer.md` | Execution | YES |
| verifier | `.opencode/agents/verifier.md` | Quality | YES |
| deployment-engineer | `.opencode/agents/deployment-engineer.md` | DevOps | YES |
| paper-wiki-writer | `.opencode/agents/paper-wiki-writer.md` | Research | YES |

---

## How to Use This File

The routing system in `core/agent_registry.py` maps task types to agents.
When creating a new agent, add it here AND to the registry.
Each agent below has: Role, Trigger (when to invoke), Tools, Output format.

---

## LEGION AGENT TRIGGER MAP

### By Task Type

| Task Type | Agent(s) | Pattern |
|-----------|-----------|---------|
| Complex multi-phase task | planner → worker → reviewer → verifier → wikibot | STANDARD |
| Research → implementation | hermes-researcher + planner → worker → reviewer → hermes-agent | RESEARCH+IMPL |
| Clear-scope bug | diff-analyzer → focused-implementer → verifier | BUG_FIX |
| Architecture change | planner(ext) → explorer → worker → reviewer → verifier | ARCH_CHANGE |
| Deploy/Ops | deployment-engineer → verifier → hermes-agent | DEPLOY |
| Academic paper to wiki | hermes-researcher → paper-wiki-writer | RESEARCH |
| Multi-agent coordination | collaborator | COLLABORATION |
| Codebase exploration | explorer | EXPLORATION |
| Git diff analysis | diff-analyzer | ANALYSIS |
| Independent verification | verifier | VERIFICATION |
| Session/task memory | hermes-agent | MEMORY |
| Long research task | hermes-researcher | RESEARCH |
| Write to wiki | wikibot | DOCUMENTATION |

### By Intent Keywords

| Keyword(s) | Agent |
|------------|-------|
| plan, decompose, break down, contract | planner |
| implement, write code, create file, fix | worker |
| review, approve, check quality, critique | reviewer |
| verify, test, prove, validate | verifier |
| deploy, ship, release, pipeline | deployment-engineer |
| research, investigate, find information | hermes-researcher |
| remember, recall, memory, persist | hermes-agent |
| wiki, document, write article, note | wikibot |
| explore, understand codebase, map | explorer |
| compare, diff, changes | diff-analyzer |
| focused, single issue, bug fix | focused-implementer |
| collaborate, coordinate agents | collaborator |
| academic, paper, research synthesis | paper-wiki-writer |
