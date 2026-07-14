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
    # PostToolUse sends toolName, not tool — check all variants
    name = d.get('toolName') or d.get('tool_name') or d.get('tool') or ''
    print(name)
except:
    print('')
" 2>/dev/null || echo "")

# Only capture write/edit/bash/task operations
if echo "$TOOL" | grep -qE '^(Write|Edit|MultiEdit|Bash|Task)$' 2>/dev/null; then
  echo "$INPUT" | python3 -c "
import sys, json, hashlib, os
from datetime import datetime, timezone

d = json.load(sys.stdin)
tool_name = d.get('toolName') or d.get('tool_name') or d.get('tool') or 'unknown'

# Only store summary, not full content (saves disk space)
tool_input = d.get('toolInput') or d.get('tool_input') or d.get('args') or {}
result = d.get('result') or d.get('output') or ''
tool_summary = str(tool_input).split('.')[-1][:80] if isinstance(tool_input, dict) else str(tool_input)[:80]
result_summary = (str(result)[:200] + '...') if len(str(result)) > 200 else str(result)

entry = {
    'tool': tool_name,
    'command': tool_input.get('command') or tool_input.get('file_path') or tool_summary,
    'result_preview': result_summary,
    'session': os.environ.get('CLAUDE_SESSION_ID', 'unknown'),
    'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
}
entry_id = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()[:12]
with open(os.path.join('$OBS_DIR', entry_id + '.json'), 'w') as f:
    json.dump(entry, f, indent=2)
" 2>/dev/null || true
fi

exit 0
