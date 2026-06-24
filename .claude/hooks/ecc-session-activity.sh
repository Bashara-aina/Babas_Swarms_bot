#!/usr/bin/env bash
# ECC Session Activity: Initializes session activity tracking
# Runs at SessionStart
set -euo pipefail

ACTIVITY_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/activity"
mkdir -p "$ACTIVITY_DIR"

SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)

cat > "$ACTIVITY_DIR/current.json" <<EOF
{
  "session_id": "$SESSION_ID",
  "started_at": "$TIMESTAMP",
  "profile": "${HOOK_PROFILE:-standard}",
  "tool_calls": 0,
  "edits": 0,
  "bash_commands": 0
}
EOF

exit 0
