#!/bin/bash
# start_with_watchdog.sh
# Start Legion with the watchdog for zero-downtime self-upgrade.
# Use this instead of `python main.py`

set -e

echo "👁️  Starting Legion with watchdog..."
echo "Bot will auto-restart on upgrade or crash."
echo "Telegram connection gap during restart: <3 seconds"
echo ""
echo "To stop: Ctrl+C or kill $(cat data/.watchdog.pid 2>/dev/null || echo 'the process')"
echo ""

# Store watchdog PID
mkdir -p data
python core/watchdog.py &
WATCHDOG_PID=$!
echo $WATCHDOG_PID > data/.watchdog.pid
echo "✅ Watchdog started (pid=$WATCHDOG_PID)"

# Wait for watchdog
wait $WATCHDOG_PID
