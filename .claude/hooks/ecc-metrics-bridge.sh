#!/usr/bin/env bash
# ECC Metrics Bridge: Feeds session metrics to statusline
set -euo pipefail

METRICS_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/metrics"
mkdir -p "$METRICS_DIR"

INPUT=$(cat 2>/dev/null || echo "{}")
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('toolName', d.get('tool_name', 'unknown')))
except:
    print('unknown')
" 2>/dev/null || echo "unknown")

# Increment tool counter
COUNTER_FILE="$METRICS_DIR/tool-count.json"
COUNT=$(python3 -c "
import json, os
try:
    with open('$COUNTER_FILE') as f:
        d = json.load(f)
except:
    d = {'total': 0, 'tools': {}}
d['total'] += 1
tool = '$TOOL_NAME'
d['tools'][tool] = d['tools'].get(tool, 0) + 1
with open('$COUNTER_FILE', 'w') as f:
    json.dump(d, f)
print(d['total'])
" 2>/dev/null || echo "0")

exit 0
