# ADR-002: YAML Agent Configs Not Fully Verified at Runtime

**Date**: 2026-04-12  
**Status**: Accepted  
**Deciders**: Worker agent (audit task)

## Context

The audit found that 107 agents are loaded from `config/departments.yaml` at startup via `load_registry()`. However:
- Prior knowledge suggested 76 agents never loaded — this was incorrect (107 are loaded)
- No runtime verification that each agent's implementation actually exists
- Dead configs could exist without causing startup failures

## Decision

Add a startup validation step that verifies:
1. Each YAML agent has a corresponding Python file/function
2. Required fields are present (name, model, keywords)
3. Log warnings for orphaned configs

## Consequences

**Positive**:
- Early detection of dead agent configs
- Better debugging when adding new agents

**Negative**:
- Startup time increase (minimal)

## References

- `core/agent_registry.py` — where `load_registry()` is implemented
- `config/departments.yaml` — source of agent configs
