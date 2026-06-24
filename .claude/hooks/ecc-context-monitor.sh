#!/usr/bin/env bash
# ECC Context Monitor: Warns on context exhaustion, high cost, scope creep
# Only active in strict profile
set -euo pipefail

if [ "${HOOK_PROFILE:-standard}" != "strict" ]; then
  exit 0
fi

CONTEXT_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/context-monitor"
mkdir -p "$CONTEXT_DIR"
TIMESTAMP=$(date +%s)

# Track tool call frequency per session
CALL_LOG="$CONTEXT_DIR/calls.log"
echo "$TIMESTAMP | ${CLAUDE_TOOL_NAME:-unknown}" >> "$CALL_LOG"

# Count calls in last N seconds
RECENT_CALLS=$(tail -50 "$CALL_LOG" 2>/dev/null | wc -l)

# Warn if unusually high call rate
if [ "$RECENT_CALLS" -gt 40 ] 2>/dev/null; then
  echo "[ECC Context Monitor] ⚠️  High tool call rate: $RECENT_CALLS in recent operations" >&2
  echo "  Consider compacting or simplifying the task." >&2
fi

# Track total tool calls in session
TOTAL_CALLS=$(wc -l < "$CALL_LOG" 2>/dev/null || echo 0)
if [ "$TOTAL_CALLS" -gt 0 ] && [ $((TOTAL_CALLS % 50)) -eq 0 ] 2>/dev/null; then
  echo "[ECC Context Monitor] Session stats: $TOTAL_CALLS total tool calls" >&2
fi

exit 0
