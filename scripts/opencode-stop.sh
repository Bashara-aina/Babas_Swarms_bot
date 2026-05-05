#!/bin/bash
# opencode-stop.sh — ONE command to stop session + deep save + show summary.
#
# Usage:
#   ./scripts/opencode-stop.sh
#
# What this does:
#   1. Signal session_watcher to stop gracefully (final checkpoint + save)
#   2. Wait for confirmation
#   3. Show session summary (files changed, decisions, checkpoints created)
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

SESSION_DIR="$REPO/.session_state"
CHECKPOINT_DIR="$SESSION_DIR/checkpoints"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Stopping session + final deep save..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Signal the watcher to stop
bash "$REPO/scripts/stop_session_watcher.sh"
WAIT_COUNT=0
while [ -f "$SESSION_DIR/watcher.pid" ] && [ $WAIT_COUNT -lt 15 ]; do
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

# Session summary
echo ""
echo "━━━ SESSION SUMMARY ━━━"

if [ -d "$CHECKPOINT_DIR" ]; then
    CP_COUNT=$(ls "$CHECKPOINT_DIR"/checkpoint_*.json 2>/dev/null | wc -l)
    echo "Checkpoints created: $CP_COUNT"
    if [ "$CP_COUNT" -gt 0 ]; then
        echo "Latest checkpoint:"
        ls -t "$CHECKPOINT_DIR"/checkpoint_*.json 2>/dev/null | head -1 | xargs cat 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"  Task: {d.get('current_task','?')}\")
print(f\"  Phase: {d.get('phase','?')}\")
if d.get('files_changed'):
    print(f\"  Files: {', '.join(d['files_changed'][-5:])}\")
if d.get('decisions'):
    print(f\"  Recent decisions: {len(d['decisions'])} logged\")
" 2>/dev/null || true
    fi
else
    echo "No checkpoints"
fi

# Show LLM event log if present
LLM_LOG="$SESSION_DIR/llm_events.log"
if [ -f "$LLM_LOG" ]; then
    LLM_COUNT=$(wc -l < "$LLM_LOG" 2>/dev/null || echo 0)
    echo "LLM calls logged: $LLM_COUNT"
fi

echo ""
echo "Memory saved to mem0 + langmem. Session is durable."
echo "Next session: bash scripts/opencode-start.sh"