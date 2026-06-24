#!/usr/bin/env bash
# ECC Format Typecheck: Batch format check on Stop/end of session
# Only active in strict profile
set -euo pipefail

if [ "${HOOK_PROFILE:-standard}" != "strict" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# Run ruff format check (don't modify, just report)
echo "[ECC Format] Checking Python formatting..."
python3 -m ruff format --check . 2>/dev/null || {
  echo "  Some files need formatting. Run: ruff format ."
}

echo "[ECC Format] Check complete."
exit 0
