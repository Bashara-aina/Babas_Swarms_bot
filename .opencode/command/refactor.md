# /refactor — Safe Refactor

Refactor the component described below. Safety rules: do not break existing tests.

## Steps
1. Read the file to refactor: cat [file]
2. Run existing tests BEFORE: pytest tests/ -x -q 2>/dev/null | tail -5 → paste output
3. Identify refactor scope — write it here before touching anything
4. Execute refactor
5. After refactor: run same tests → must show same pass count
6. Check for remaining old references: grep -r "[old name]" . --include="*.py" | grep -v ".git"
   Must return empty for complete rename refactors
7. Update .wiki/architecture/legion-module-map.md if module structure changed

Verify: pytest tests/ -x -q | tail -5 → paste output (must match pre-refactor result)

Component to refactor: