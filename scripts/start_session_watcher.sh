#!/bin/bash
# Start the session_watcher background daemon.
# Run ONCE at the start of an OpenCode session.
# Idempotent: fails gracefully if already running.

set -e

SESSION_DIR="$(pwd)/.session_state"
PID_FILE="$SESSION_DIR/watcher.pid"
LOG_FILE="$SESSION_DIR/watcher.log"

mkdir -p "$SESSION_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "session_watcher already running (PID $OLD_PID)"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

# Remove any stale stop signal
rm -f "$SESSION_DIR/STOP_WATCHER" 2>/dev/null || true

# Start the watcher
echo "Starting session_watcher..."
nohup python3 -c "
import logging, sys
logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(message)s', stream=open('$LOG_FILE', 'a'))
sys.path.insert(0, '$(pwd)')
from core.memory.session_watcher import run
run()
" >> "$LOG_FILE" 2>&1 &

WATCHER_PID=$!
echo $WATCHER_PID > "$PID_FILE"
echo "session_watcher started (PID $WATCHER_PID)"