#!/bin/bash
# opencode-start.sh — ONE command to start a fully-memory-enabled OpenCode session.
#
# Usage:
#   ./scripts/opencode-start.sh                    # default query: recent session
#   ./scripts/opencode-start.sh "intent routing"   # custom recall query
#
# What this does:
#   1. Start session_watcher daemon (background, persists until stop_session_watcher.sh)
#   2. Query 4-layer memory system for prior context
#   3. Write recalled context to .session_state/recalled_context.md
#   4. Echo the context so you can paste it as your first message to OpenCode
#
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

QUERY="${1:-recent session work}"
SESSION_DIR="$REPO/.session_state"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Starting infinite memory session..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Start session_watcher (idempotent — safe to run multiple times)
bash "$REPO/scripts/start_session_watcher.sh"

# 2. Build recalled context via Python
echo ""
echo "Querying 4-layer memory: \"$QUERY\""
CONTEXT_FILE="$SESSION_DIR/recalled_context.md"

python3 -c "
import sys
sys.path.insert(0, '$REPO')
from core.memory.memory_injector import build_memory_context
ctx = build_memory_context(query='$QUERY', user_id='bashara')
print(ctx)
" > "$CONTEXT_FILE" 2>/dev/null || {
    echo "(memory recall skipped — run /memory manually if needed)"
}

# 3. Show what OpenCode will see
if [ -s "$CONTEXT_FILE" ]; then
    echo ""
    echo "━━━ RECALLED CONTEXT (paste this as your first message) ━━━"
    cat "$CONTEXT_FILE"
    echo "━━━ END RECALL ━━━"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Ready. session_watcher running in background."
echo "To stop + final save: bash scripts/stop_session_watcher.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"