#!/usr/bin/env bash
# Legion MiroFish Server Launcher
# Usage: ./scripts/start_mirofish.sh [start|stop|restart|status]

MIROFISH_DIR="$(dirname "$0")/../tools/mirofish/backend"
VENV="$MIROFISH_DIR/.venv-mirofish"
PID_FILE="/tmp/mirofish.pid"
LOG_FILE="/tmp/mirofish.log"
PORT=5001

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        echo "MiroFish already running (PID $(cat $PID_FILE))"
        return 0
    fi
    echo "Starting MiroFish on port $PORT..."
    source "$VENV/bin/activate"
    cd "$MIROFISH_DIR"
    FLASK_PORT=$PORT nohup python run.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 4
    if kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        echo "✅ MiroFish started (PID $(cat $PID_FILE))"
    else
        echo "❌ MiroFish failed to start — check $LOG_FILE"
        cat "$LOG_FILE" | tail -20
        exit 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null && echo "Stopped MiroFish (PID $PID)"
        rm -f "$PID_FILE"
    else
        echo "MiroFish not running"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        echo "✅ MiroFish running (PID $(cat $PID_FILE))"
        curl -s http://localhost:$PORT/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "(health endpoint not available)"
    else
        echo "❌ MiroFish not running"
    fi
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 1; start ;;
    status)  status ;;
    *) echo "Usage: $0 {start|stop|restart|status}" ;;
esac