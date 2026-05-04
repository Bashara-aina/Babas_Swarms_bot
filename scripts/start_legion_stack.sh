#!/usr/bin/env bash
# scripts/start_legion_stack.sh
# TMUX-based multi-pane Legion stack with MiroFish integration.
# Usage: ./scripts/start_legion_stack.sh [start|stop|restart|status]

set -e

SESSION="${LEGION_TMUX_SESSION:-legion}"
MIROFISH_SCRIPT="$(dirname "$0")/start_mirofish.sh"
LOG_DIR="${LOG_DIR:-/tmp/legion_logs}"
mkdir -p "$LOG_DIR"

start() {
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        echo "Legion TMUX session '$SESSION' already running"
        return 0
    fi

    echo "🚀 Starting Legion stack on TMUX session '$SESSION'..."

    # Window 0: Legion bot (main)
    tmux new-session -d -s "$SESSION" -n "legion"
    tmux send-keys -t "$SESSION:0" "cd /home/newadmin/swarm-bot && mkdir -p data && python core/watchdog.py > $LOG_DIR/watchdog.log 2>&1" Enter
    tmux send-keys -t "$SESSION:0" "echo '✅ Legion watchdog started'" Enter

    # Window 1: MiroFish backend
    tmux new-window -t "$SESSION" -n "mirofish"
    tmux send-keys -t "$SESSION:1" "cd /home/newadmin/swarm-bot && $MIROFISH_SCRIPT start" Enter

    # Window 2: N8N webhook (if configured)
    if command -v n8n &>/dev/null; then
        tmux new-window -t "$SESSION" -n "n8n"
        tmux send-keys -t "$SESSION:2" "cd /home/newadmin/swarm-bot && n8n start > $LOG_DIR/n8n.log 2>&1" Enter
    fi

    # Window 3: Hermes agent (if present)
    if [ -d "/home/newadmin/swarm-bot/ext/hermes-agent" ]; then
        tmux new-window -t "$SESSION" -n "hermes"
        tmux send-keys -t "$SESSION:3" "cd /home/newadmin/swarm-bot/ext/hermes-agent && python hermes.py > $LOG_DIR/hermes.log 2>&1" Enter
    fi

    echo "✅ Legion stack started in TMUX session '$SESSION'"
    echo "   Attach with: tmux attach -t $SESSION"
    echo "   MiroFish:  $MIROFISH_SCRIPT start|stop|status"
}

stop() {
    echo "Stopping Legion stack..."
    $MIROFISH_SCRIPT stop 2>/dev/null || true
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        tmux kill-session -t "$SESSION" 2>/dev/null && echo "✅ TMUX session killed" || echo "TMUX session not found"
    else
        echo "TMUX session '$SESSION' not running"
    fi
}

status() {
    $MIROFISH_SCRIPT status 2>/dev/null || echo "MiroFish: unknown"
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        echo "✅ TMUX session '$SESSION' running"
        tmux list-windows -t "$SESSION"
    else
        echo "❌ TMUX session '$SESSION' not running"
    fi
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 1; start ;;
    status)  status ;;
    *) echo "Usage: $0 {start|stop|restart|status}" ;;
esac
