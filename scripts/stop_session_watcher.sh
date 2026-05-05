#!/bin/bash
# Stop the session_watcher daemon.
# Triggers graceful shutdown via STOP_SIGNAL file.
# The watcher saves a final checkpoint then exits.

SESSION_DIR="$(pwd)/.session_state"
STOP_FILE="$SESSION_DIR/STOP_WATCHER"
PID_FILE="$SESSION_DIR/watcher.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "session_watcher not running (no PID file)"
    exit 0
fi

PID=$(cat "$PID_FILE" 2>/dev/null || true)

# Touch the stop signal file
touch "$STOP_FILE"
echo "Stop signal sent (PID $PID)"

# Wait up to 10s for graceful shutdown
if [ -n "$PID" ]; then
    for i in $(seq 1 10); do
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "session_watcher stopped"
            rm -f "$PID_FILE"
            exit 0
        fi
        sleep 1
    done
    echo "Warning: process still running after 10s, killing"
    kill -9 "$PID" 2>/dev/null || true
fi

rm -f "$PID_FILE"
echo "session_watcher stopped"