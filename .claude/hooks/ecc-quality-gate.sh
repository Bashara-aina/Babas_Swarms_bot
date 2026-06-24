#!/usr/bin/env bash
# ECC Quality Gate: Async quality checks after edits
# Runs in background — does not block the edit
set -euo pipefail

# Only run in strict mode (it's async so it doesn't block the edit)
if [ "${HOOK_PROFILE:-standard}" != "strict" ]; then
  exit 0
fi

QUALITY_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/quality-gate"
mkdir -p "$QUALITY_DIR"
TIMESTAMP=$(date +%s)

# Run quality checks in background — don't block the edit
{
  cd "${CLAUDE_PROJECT_DIR:-.}"

  # Check file size of recently modified files
  echo "=== File Size Check ===" >> "$QUALITY_DIR/check-$TIMESTAMP.log"
  find . -name "*.py" -newer "$QUALITY_DIR/.last-check" -type f 2>/dev/null | while read -r f; do
    lines=$(wc -l < "$f" 2>/dev/null || echo 0)
    if [ "$lines" -gt 500 ] 2>/dev/null; then
      echo "  OVER 500 lines: $f ($lines lines)" >> "$QUALITY_DIR/check-$TIMESTAMP.log"
    fi
  done

  # Quick lint on changed files (timeout after 10s)
  timeout 10 python3 -m ruff check --statistics . 2>/dev/null >> "$QUALITY_DIR/check-$TIMESTAMP.log" || true

  echo "[ECC Quality Gate] Check complete — see $QUALITY_DIR/check-$TIMESTAMP.log" >&2
} &

touch "$QUALITY_DIR/.last-check"
exit 0
