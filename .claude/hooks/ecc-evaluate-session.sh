#!/usr/bin/env bash
# ECC Evaluate Session: Pattern extraction for continuous learning
# Runs during PreCompact to consolidate session patterns into instincts
set -euo pipefail

if [ "${HOOK_PROFILE:-standard}" = "minimal" ]; then
  exit 0
fi

EVAL_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/homunculus/evaluations"
mkdir -p "$EVAL_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Check for instinct CLI and run consolidation if available
INSTINCT_CLI="${CLAUDE_PROJECT_DIR:-.}/.claude/helpers/instinct-cli.cjs"
if [ -f "$INSTINCT_CLI" ]; then
  node "$INSTINCT_CLI" consolidate 2>/dev/null || true
fi

# Record evaluation timestamp
echo "{\"timestamp\": \"$TIMESTAMP\", \"profile\": \"${HOOK_PROFILE:-standard}\"}" > "$EVAL_DIR/latest.json"

exit 0
