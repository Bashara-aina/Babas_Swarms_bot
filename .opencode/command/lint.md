# /lint — Run Python and TypeScript Lint Checks
## Phase 3: Python Lint
ruff check . --fix --unsafe-fixes 2>&1
ruff format . 2>&1
mypy . --ignore-missing-imports --no-strict-optional --exclude ".venv|node_modules|ext/" 2>&1

## Phase 4: TypeScript (if applicable)
if [ -d "cekwajar.id" ]; then
  cd cekwajar.id && pnpm lint && pnpm tsc --noEmit && cd ..
fi

## Fail gate
echo "Lint complete."