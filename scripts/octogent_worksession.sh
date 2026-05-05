#!/usr/bin/env bash
# Legion Daily Work Session Launcher
# Run this at the start of each coding session.
# Opens Octogent UI + creates tmux windows pre-loaded with context.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="legion"
PORT="${OCTOGENT_PORT:-8788}"

echo "🚀 Starting Legion Work Session..."

# 1. Start Octogent dashboard
"$REPO_ROOT/scripts/start_octogent.sh" start

# 2. Create tmux session if not exists
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux new-session -d -s "$SESSION" -n "orchestrator" -c "$REPO_ROOT"
    echo "✅ Created tmux session: $SESSION"
else
    echo "⚠️  tmux session '$SESSION' already exists — attaching..."
fi

# 3. Create named windows for each active tentacle
# Each window pre-loads the tentacle CONTEXT.md before OpenCode starts

create_tentacle_window() {
    local name="$1"
    local tentacle_id="$2"
    local workdir="$3"

    tmux new-window -t "$SESSION" -n "$name" -c "$workdir" 2>/dev/null || true
    # Show context before starting OpenCode
    tmux send-keys -t "$SESSION:$name" \
        "echo '=== $name tentacle context ===' && cat '$REPO_ROOT/.octogent/tentacles/$tentacle_id/CONTEXT.md' | head -30 && echo '' && echo 'Starting OpenCode...' && sleep 2 && opencode" \
        Enter
}

create_tentacle_window "legion-core" "legion-core" "$REPO_ROOT"
create_tentacle_window "mirofish"    "mirofish"    "$REPO_ROOT"
create_tentacle_window "cekwajar"    "cekwajar"    "$HOME/cekwajar"       # adjust path
create_tentacle_window "rumahlabuh"  "rumahlabuh"  "$HOME/rumahlabuh"     # adjust path
create_tentacle_window "research"    "research"    "$HOME/research"       # adjust path

# 4. Window for monitoring
tmux new-window -t "$SESSION" -n "monitor" -c "$REPO_ROOT"
tmux send-keys -t "$SESSION:monitor" \
    "watch -n 10 'echo === Git Status === && git log --oneline -5 && echo && echo === MiroFish === && curl -s http://localhost:8001/health 2>/dev/null || echo offline && echo === Octogent === && curl -s http://localhost:$PORT/api/health 2>/dev/null || echo offline'" \
    Enter

# 5. Focus orchestrator window
tmux select-window -t "$SESSION:orchestrator"

echo ""
echo "═══════════════════════════════════════"
echo "✅ Legion Work Session Ready"
echo "   Octogent UI: http://localhost:$PORT"
echo "   tmux: Ctrl+B + window-name to switch"
echo "   Windows: orchestrator | legion-core | mirofish | cekwajar | rumahlabuh | research | monitor"
echo "═══════════════════════════════════════"

# 6. Attach to tmux
tmux attach-session -t "$SESSION"