#!/usr/bin/env bash
set -euo pipefail
DIR="/home/newadmin/swarm-bot"
exec "$DIR/scripts/agent-browser-safe.sh" --config "$DIR/agent-browser.json" "$@"