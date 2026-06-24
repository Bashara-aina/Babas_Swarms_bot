#!/usr/bin/env bash
# PreCompact hook: consolidate observations into instincts
set -euo pipefail

HOOK_PROFILE="${HOOK_PROFILE:-standard}"
if [ "$HOOK_PROFILE" = "minimal" ]; then
  exit 0
fi

HOMUNCULUS_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/homunculus"
mkdir -p "$HOMUNCULUS_DIR/observations" "$HOMUNCULUS_DIR/instincts"

# Run consolidation via instinct-cli if it exists
if [ -f "${CLAUDE_PROJECT_DIR:-.}/.claude/helpers/instinct-cli.cjs" ]; then
  exec node "${CLAUDE_PROJECT_DIR:-.}/.claude/helpers/instinct-cli.cjs" consolidate 2>/dev/null || true
fi

exit 0
