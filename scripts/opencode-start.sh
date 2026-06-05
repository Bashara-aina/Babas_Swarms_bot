#!/bin/bash
# opencode-start.sh — ONE command to start a fully-memory-enabled OpenCode session.
#
# Usage:
#   ./scripts/opencode-start.sh                    # default query: recent session
#   ./scripts/opencode-start.sh "intent routing"   # custom recall query
#
# What this does:
#   1. Start session_watcher daemon (background, persists until stop_session_watcher.sh)
#   2. Query 6-layer memory system for prior context
#   3. Write recalled context to .session_state/recalled_context.md
#   4. Auto-inject context into OpenCode as first message via `opencode run -f ...`
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
bash "$REPO/scripts/start_session_watcher.sh" 2>/dev/null || true

# 2. Build recalled context via Python
CONTEXT_FILE="$SESSION_DIR/recalled_context.md"
echo ""
echo "Querying 6-layer memory: \"$QUERY\""

BUILD_ERR=$("$REPO/.venv/bin/python3" -c "
import sys
sys.path.insert(0, '$REPO')
from core.memory.memory_injector import build_memory_context
ctx = build_memory_context(query='$QUERY', user_id='bashara')
# Write to file
with open('$CONTEXT_FILE', 'w') as f:
    f.write(ctx)
print('memory recall done', file=sys.stderr)
" 2>&1)
echo "$BUILD_ERR" | grep -v "mem0 not available\|OpenViking\|RecursionError\|legacy memory" || true

# 3. Show what OpenCode will see
if [ -s "$CONTEXT_FILE" ]; then
    echo ""
    echo "━━━ RECALLED CONTEXT (auto-injecting into OpenCode) ━━━"
    head -20 "$CONTEXT_FILE"
    echo "...(truncated)"
    echo "━━━ END RECALL ━━━"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Launching OpenCode with memory context auto-injected..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 4. Auto-inject context into OpenCode via file attachment + --continue
#    The recalled_context.md becomes the first message's attachment
exec opencode run \
    -f "$CONTEXT_FILE" \
    --continue \
    --dir "$REPO" \
    --model minimax/MiniMax-M3 \
    "Continue where we left off. Review the attached recalled context — it is your prior memory."