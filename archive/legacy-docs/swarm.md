# Swarm Agent Orchestration

This project uses hierarchical multi-agent orchestration. See [WORKFLOW.md](WORKFLOW.md) for the canonical agent definition and [CLAUDE.md](CLAUDE.md) for the full project context.

The swarm system coordinates:
- **planner**: Task decomposition (ruflo task_create + memory_search)
- **worker**: Implementation execution (browser + filesystem + bash)
- **reviewer**: Pre-merge quality gate
- **wikibot**: Documentation generation

For parallel execution of multiple agents, see [WORKFLOW.md](WORKFLOW.md) which defines the Symphony-compatible workflow.