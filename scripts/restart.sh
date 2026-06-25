#!/bin/bash
set -e  # stop on any error

echo "=== Stopping bot ==="
sudo systemctl stop swarm-bot 2>/dev/null || true
pkill -9 -f "python.*main.py" 2>/dev/null || true
sleep 1

echo "=== Pulling latest code ==="
cd ~/swarm-bot
git pull origin main || { echo "❌ git pull failed — aborting"; exit 1; }

echo "=== Installing dependencies ==="
# Activate venv if it exists
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

pip install -q -r requirements.txt

# Only reinstall Playwright if version changed
PLAYWRIGHT_VERSION=$(pip show playwright | grep Version | awk '{print $2}')
CACHED_VERSION=$(cat .playwright_version 2>/dev/null || echo "none")
if [ "$PLAYWRIGHT_VERSION" != "$CACHED_VERSION" ]; then
    echo "=== Installing Playwright Chromium (new version: $PLAYWRIGHT_VERSION) ==="
    playwright install chromium
    echo "$PLAYWRIGHT_VERSION" > .playwright_version
else
    echo "=== Playwright up to date ($PLAYWRIGHT_VERSION) — skipping ==="
fi

echo "=== Starting bot ==="
nohup python main.py > logs/bot.log 2>&1 &
echo "✅ Bot started (PID $!) — tail logs: tail -f ~/swarm-bot/logs/bot.log"
