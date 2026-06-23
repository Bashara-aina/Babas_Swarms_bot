#!/usr/bin/env bash
# Memory sync hook — syncs Claude memory files to auto-memory-store index
set -euo pipefail
cd /home/newadmin/swarm-bot

MEMORY_SOURCE="${HOME}/.claude/projects/-home-newadmin-swarm-bot/memory"
AUTO_STORE=".claude-flow/data/auto-memory-store.json"

# Report source memory state
if [ -d "$MEMORY_SOURCE" ]; then
  file_count=$(find "$MEMORY_SOURCE" -name '*.md' | wc -l)
  echo "[MEMORY] Source: $file_count memory files"
else
  echo "[MEMORY] Source: not found at $MEMORY_SOURCE"
  file_count=0
fi

# Report store state
if [ -f "$AUTO_STORE" ]; then
  store_size=$(python3 -c "
import json
with open('$AUTO_STORE') as f:
    data = json.load(f)
if isinstance(data, dict):
    print(f\"{len(data.get('entries', data))} entries, {len(data.get('nodes', []))} nodes\" if 'entries' in data or 'nodes' in data else \"loaded\")
elif isinstance(data, list):
    print(f\"{len(data)} entries\")
else:
    print(\"unknown\")
" 2>/dev/null || echo "unknown")
  echo "[MEMORY] Store: $store_size"
else
  echo "[MEMORY] Store: no auto-memory-store.json"
fi

echo "[MEMORY] Sync complete"
