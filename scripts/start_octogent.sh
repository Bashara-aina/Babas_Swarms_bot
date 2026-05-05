#!/usr/bin/env bash
# ═══════════════════════════════════════════
# Legion Elite Stack — Octogent Session Launcher
# Usage: ./scripts/start_octogent.sh [start|stop|status]
# ═══════════════════════════════════════════

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="/tmp/octogent_legion.pid"
LOG_FILE="/tmp/octogent_legion.log"
PORT="${OCTOGENT_PORT:-8788}"

start() {
    echo "🐙 Starting Octogent for Legion Elite Stack..."
    cd "$REPO_ROOT"

    # Check Octogent is installed
    if ! which octogent &>/dev/null; then
        echo "❌ octogent not found in PATH."
        echo "   Install it: cd ~/octogent && pnpm build && npm install -g ."
        exit 1
    fi

    # Check if already running
    if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        echo "⚠️  Octogent already running (PID $(cat $PID_FILE))"
        echo "   Open: http://localhost:$PORT"
        return 0
    fi

    # Start Octogent in background (it opens browser automatically)
    # Use OCTOGENT_NO_OPEN=1 to prevent auto-opening browser
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm use 22 &>/dev/null || true

    OCTOGENT_NO_OPEN="${OCTOGENT_NO_OPEN:-0}" \
    OCTOGENT_PORT="$PORT" \
    nohup octogent > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 3

    if kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        echo "✅ Octogent started (PID $(cat $PID_FILE))"
        echo "   Dashboard: http://localhost:$PORT"
        echo "   Logs:      tail -f $LOG_FILE"
        echo ""
        echo "📋 Your tentacles:"
        for t in legion-core mirofish cekwajar rumahlabuh research popw; do
            todos=$(grep -c "\- \[ \]" "$REPO_ROOT/.octogent/tentacles/$t/todo.md" 2>/dev/null || echo 0)
            echo "   • $t ($todos pending todos)"
        done
    else
        echo "❌ Octogent failed to start — check $LOG_FILE"
        tail -20 "$LOG_FILE"
        exit 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null && echo "⛔ Octogent stopped (PID $PID)"
        rm -f "$PID_FILE"
    else
        echo "Octogent not running"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ Octogent running (PID $(cat "$PID_FILE"))"
        echo "   Dashboard: http://localhost:$PORT"
        octogent tentacle list 2>/dev/null || true
    else
        echo "❌ Octogent not running"
    fi
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    status)  status ;;
    restart) stop; sleep 1; start ;;
    *) echo "Usage: $0 {start|stop|restart|status}" ;;
esac
