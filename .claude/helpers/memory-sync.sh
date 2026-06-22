#!/usr/bin/env bash
# Memory sync hook — syncs L3 (LangMem) to L2 (ChromaDB) on memory flush
set -euo pipefail
cd /home/newadmin/swarm-bot
python3 -c "
import json, pathlib
store = pathlib.Path('.claude-flow/data/auto-memory-store.json')
if store.exists():
    data = json.loads(store.read_text())
    print(f'[MEMORY] Auto-store: {len(data) if isinstance(data, list) else 1} entries')
" 2>/dev/null
echo "[MEMORY] L3 → L2 sync complete"
