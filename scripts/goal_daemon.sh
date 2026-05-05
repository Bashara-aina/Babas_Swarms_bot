#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# /goal daemon — run a goal from CLI without Telegram
# Usage: ./scripts/goal_daemon.sh "Build the search page" [--cost-limit 3.00]
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

GOAL="${1:-}"
COST_LIMIT="${2:-5.00}"
LOG_FILE="$REPO_ROOT/.goal/logs/daemon_$(date +%Y%m%d_%H%M%S).log"

if [ -z "$GOAL" ]; then
    echo "Usage: $0 \"your goal description\" [cost_limit_dollars]"
    echo ""
    echo "Examples:"
    echo "  $0 \"Build the Rumahlabuh search/filter page\""
    echo "  $0 \"Add PPh 21 TER calculator to Cekwajar\" 3.00"
    echo ""
    echo "The agent will run autonomously and log to: $LOG_FILE"
    exit 1
fi

# Clean cost limit arg if passed with flag
if [[ "$COST_LIMIT" == "--cost-limit" ]]; then
    COST_LIMIT="${2:-5.00}"
fi

mkdir -p "$REPO_ROOT/.goal/logs"

echo "🎯 Starting goal: $GOAL"
echo "💰 Cost limit: \$$COST_LIMIT"
echo "📋 Logging to: $LOG_FILE"
echo ""
echo "Press Ctrl+C to stop (current task will finish first)"
echo "═══════════════════════════════════════════════════════════"

# Export for mini-swe-agent
export MSWEA_GLOBAL_COST_LIMIT="$COST_LIMIT"
export MSWEA_COST_TRACKING="ignore_errors"

# Run goal runner (streams output to both console and log)
python3 -u "$REPO_ROOT/tools/goal_runner.py" "$GOAL" 2>&1 | tee "$LOG_FILE"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Goal execution complete. Check .goal/ for reports."