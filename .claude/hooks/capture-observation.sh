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
# Pre-filter with bash before Python — avoids subprocess on most tool calls
TOOL=$(echo "$INPUT" | grep -oP '"(?:toolName|tool_name|tool)"\s*:\s*"\K[^"]+' 2>/dev/null | head -1)

# Only capture write/edit/bash/task operations — skip everything else
case "$TOOL" in
  Write|Edit|MultiEdit|Bash|Task)
    echo "$INPUT" | python3 -c "
import sys, json, hashlib, os
from datetime import datetime, timezone

d = json.load(sys.stdin)
tool_name = d.get('toolName') or d.get('tool_name') or d.get('tool') or 'unknown'

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
    ;;
  *) exit 0 ;;
esac

exit 0
