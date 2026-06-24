#!/usr/bin/env bash
# PostToolUse hook: capture tool use observations for continuous learning
set -euo pipefail

HOOK_PROFILE="${HOOK_PROFILE:-standard}"
if [ "$HOOK_PROFILE" = "minimal" ]; then
  exit 0
fi

OBS_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/homunculus/observations"
mkdir -p "$OBS_DIR"

INPUT=$(cat 2>/dev/null || echo "{}")
TOOL=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    d.get('tool','') or d.get('toolInput',{}).get('name','')
except:
    ''
" 2>/dev/null || echo "")

# Only capture write/edit/bash operations (not reads)
if echo "$TOOL" | grep -qE '^(Write|Edit|MultiEdit|Bash)$' 2>/dev/null; then
  echo "$INPUT" | python3 -c "
import sys, json, hashlib, os
d = json.load(sys.stdin)
entry = {
    'timestamp': open('/dev/stdin','r') and '',
    'tool': d.get('tool', ''),
    'tool_input': d.get('toolInput', d.get('args', {})),
    'result': d.get('result', d.get('output', '')),
    'session': os.environ.get('CLAUDE_SESSION_ID', 'unknown'),
}
entry['timestamp'] = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
entry_id = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()[:12]
with open(os.path.join('$OBS_DIR', entry_id + '.json'), 'w') as f:
    json.dump(entry, f, indent=2)
" 2>/dev/null || true
fi

exit 0
