---
title: "ADR-052: core Subpackages — Empty `__init__.py` Files Need Docstrings"
date: "2026-04-12"
decider: "@planner"
status: "Accepted"
---
# ADR-052: core Subpackages — Empty `__init__.py` Files Need Docstrings

**Date:** 2026-04-12
**Status:** Accepted
**Decider:** @planner

## Context

The following core subpackages have 0-byte `__init__.py` files:
- `core/orchestration/__init__.py` (has supervisor.py, swarm_patterns.py)
- `core/optimization/__init__.py` (has usage_tracker.py, feedback_learner.py)
- `core/utils/__init__.py` (has 10+ utility modules)
- `core/tools/__init__.py` (has computer_control.py, playwright_agent.py, vscode_bridge.py)
- `prompts/__init__.py` (empty, no callers found)

No callers use `from core import orchestration` pattern — all use direct imports (`from core.orchestration.supervisor import orchestrate`). However, empty `__init__.py` files are misleading and create confusing package structures.

## Decision

Add minimal docstring `__init__.py` to each empty package to clarify purpose:

**core/orchestration/__init__.py:**
```python
"""Orchestration subsystem — supervisor and swarm patterns."""
```

**core/optimization/__init__.py:**
```python
"""Optimization subsystem — usage tracking and feedback learning."""
```

**core/utils/__init__.py:**
```python
"""Utility functions — formatters, UI helpers, multimodal processing."""
```

**core/tools/__init__.py:**
```python
"""Tool agents — computer control, Playwright browser automation, VSCode bridge."""
```

**prompts/__init__.py:**
```python
"""Prompt templates and message builders."""
```

**swarms_bot/agents/__init__.py:**
```python
"""Specialized agent implementations for swarms_bot."""
```

## Consequences

- Package directories are clearly documented
- `dir(package)` will show module-level docstrings
- No functional change to imports
- Standard Python packaging convention followed

## Implementation

Assign to @worker — see AUDIT 11 subtask list.