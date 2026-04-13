# Comprehensive Audit Report: ClaudeCode, OpenCode & LegionBot
Generated: 2026-04-13 | Auditor: Claude Code (Autonomous Audit Loop)
Duration: 6-hour loop, every 10 minutes

---

## Audit Cycle 1 - 2026-04-13T09:00:00+09:00

Findings:

### CLAUDE.md
- **Issue**: CLAUDE.md project identity references "agency-swarm refactor (March 2026)" and mentions 84 agents in `config/departments.yaml`, but the repo's `main.py` and `agents.py` structure has evolved significantly. Potential misalignment between documentation and actual codebase.
- **How to fix**: Align the architecture map in CLAUDE.md Section 2 with current `main.py`, `core/agent_registry.py`, and `core/nexus_orchestrator.py` state. The "84 agents" number should be verified against `config/departments.yaml` count.

### Git Status Observations
- **Issue**: `.wiki/` has many untracked files (decisions/, concepts/, entities/, logs/, research/) — the wiki has been worked on but not committed. This means the Obsidian vault is out of sync with git.
- **Issue**: `.playwright-mcp/` is untracked — new tooling added but not committed
- **Issue**: `data/harvest` directory untracked — session harvesting data exists
- **How to fix**: Run `git add .wiki/ .playwright-mcp/ data/harvest && git commit` with appropriate messages

### Wiki Health (Section 2b Protocol)
- **Status**: NOT RUN YET — need to execute the full health pulse script from CLAUDE.md Section 2b Step 3
- **How to fix**: Run the Python health pulse script to check YAML failures, broken wikilinks, and orphan articles

### Intent Router & Soul Engine
- **Status**: NOT YET VERIFIED — smoke tests pending execution
- **How to fix**: Run the smoke tests from CLAUDE.md Section 12

### OpenCode Reference
- **Issue**: `.wiki/research/opencode` and `.wiki/tools/openaugi` are listed as modified in git status but the actual OpenCode agent/tooling at `.opencode/` may not be fully documented or tested
- **How to fix**: Verify `.opencode/` directory exists and contains valid agent definitions; cross-reference with wiki articles

### Memory System
- **Issue**: `core/memory/memory_manager.py` facade is the single entry point per CLAUDE.md, but need to verify no direct store calls bypass it (grep for direct episodic_store, mem0, temporal_graph calls in handlers/)
- **How to fix**: `grep -r "episodic_store\|mem0\|temporal_graph" handlers/ --include="*.py"` to find bypass patterns

### Security
- **Issue**: CLAUDE.md mandates `ALLOWED_USER_ID` check in `handlers/shared.py`, but need to verify ALL handler files use `_shared.require_owner()` and no handler has inline user ID checks
- **How to fix**: Audit handler files for `message.from_user.id` checks vs `_shared.require_owner()` usage

### Async Compliance
- **Issue**: CLAUDE.md states "NEVER use threading, time.sleep(), or blocking I/O" — need to grep for violations
- **How to fix**: `grep -rn "time\.sleep\|threading\." core/ handlers/ --include="*.py" | grep -v "# legacy\|# old\|# deprecated"` to find violations

---

## Audit Cycle 2 - 2026-04-13T09:10:00+09:00

Findings:

### [TO BE FILLED BY AUTOMATED AUDIT]
