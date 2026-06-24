#!/usr/bin/env bash
# ECC Cost Tracker: Records token/cost metrics at session boundaries
set -euo pipefail

METRICS_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/metrics"
mkdir -p "$METRICS_DIR"
TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)

LOG_FILE="$METRICS_DIR/cost-log.jsonl"

# Record a session end entry
echo "{\"timestamp\": \"$TIMESTAMP\", \"event\": \"$(echo "${1:-session_end}")\", \"profile\": \"${HOOK_PROFILE:-standard}\"}" >> "$LOG_FILE"

# Print session summary (last 10 entries)
TOTAL_SESSIONS=$(wc -l < "$LOG_FILE" 2>/dev/null || echo 0)
echo "[ECC Cost Tracker] Session recorded. Total sessions tracked: $TOTAL_SESSIONS" >&2

exit 0
