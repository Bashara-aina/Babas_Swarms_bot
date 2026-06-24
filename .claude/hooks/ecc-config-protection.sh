#!/usr/bin/env bash
# ECC Config Protection: Blocks edits to linter/formatter configs
# Forces code fixes rather than weakening lint rules
set -euo pipefail

INPUT=$(cat 2>/dev/null || echo "{}")
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tool_input = d.get('toolInput') or d.get('tool_input') or {}
    print(tool_input.get('file_path') or tool_input.get('filePath') or '')
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Protected config files — editing these weakens code quality enforcement
PROTECTED_PATTERNS=(
  'pyproject.toml'
  '.flake8'
  'setup.cfg'
  'ruff.toml'
  '.ruff.toml'
  '.pylintrc'
  '.pre-commit-config.yaml'
  '.eslintrc'
  '.eslintrc.json'
  '.eslintrc.js'
  '.prettierrc'
  '.prettierrc.json'
  'tsconfig.json'
  'tsconfig.base.json'
  '.stylelintrc'
  '.stylelintrc.json'
)

for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if basename "$FILE_PATH" 2>/dev/null | grep -qFx "$pattern" 2>/dev/null; then
    echo "[ECC Config Protection] BLOCKED: Editing $pattern weakens code quality enforcement." >&2
    echo "  Fix the code to pass lint, don't weaken the rules." >&2
    echo "  If you MUST change this config, set ECC_BYPASS_CONFIG_PROTECTION=1" >&2
    if [ "${ECC_BYPASS_CONFIG_PROTECTION:-0}" != "1" ]; then
      exit 1
    fi
  fi
done

exit 0
