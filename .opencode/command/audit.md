---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <module-or-path>
description: "Run tests. Without args: pytest tests/. With path: pytest tests/<path>."
---

# /audit — Cross-system audit

Compare two files or modules side by side for structural parity.

## Arguments
- `module-or-path`: File or module path to audit (required)

## Usage
```
/audit handlers/my_handler.py
/audit core/memory/
/audit tools/browser_tool.py agents/browser_agent.py
```

## What it checks
- Function/class presence in both
- Import structure parity
- Interface consistency
- Missing methods

## Swarm-Bot Audit Patterns
```
/audit tools/browser_tool.py tools/browser_agent.py
/audit core/memory/memory_manager.py core/legion_memory_facade.py
```

## Output
Returns a structured diff: matching symbols, missing from A, missing from B.
