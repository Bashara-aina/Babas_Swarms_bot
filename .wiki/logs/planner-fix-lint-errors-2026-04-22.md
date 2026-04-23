## Plan: Fix All Remaining Lint Errors
Date: 2026-04-22
Type: BUG_FIX

## Context Gathered
- ruff check reveals 150+ lint errors across 9 files
- Most are fixable with `ruff --fix` (W293, F541, I001, E701, W292)
- F821 errors (undefined names) need manual fixes for missing imports
- E741 ambiguous variable also needs manual fix

## Error Summary
| File | Issues | Fix Approach |
|------|--------|--------------|
| core/utils/error_formatter.py | W293 (27), I001 (1) | ruff --fix + manual |
| core/utils/feedback_animator.py | W293 (20) | ruff --fix |
| core/utils/loading_manager.py | W293 (13), I001 (1), W291 (1) | ruff --fix + manual |
| handlers/gstack.py | F541 (47), F841 (2), E741 (1), I001 (1) | ruff --fix + manual |
| handlers/media_tools.py | F821 (asyncio), I001 (2), F541 (1) | manual import + ruff --fix |
| handlers/memory_commands.py | F821 (html_mod) | manual import |
| .claude/commands/status.py | E701 (2), W292 (1) | manual fixes |
| .claude/commands/swarm-executor.py | F541 (2) | ruff --fix |
| .claude/commands/swarm-run.py | I001 (1) | ruff --fix |

## Approach
1. Fix W293 whitespace (trailing spaces on blank lines) with ruff --fix
2. Fix F541 f-strings without placeholders with ruff --fix
3. Fix I001 import sorting with ruff --fix
4. Add missing `import asyncio` to handlers/media_tools.py
5. Add missing `import html as html_mod` to handlers/memory_commands.py  
6. Fix E701 multi-statement lines in .claude/commands/status.py
7. Fix W292 no newline at end of file in .claude/commands/status.py
8. Remove unused variables (F841) in handlers/gstack.py
9. Rename ambiguous variable `l` in handlers/gstack.py
10. Run full ruff check to verify