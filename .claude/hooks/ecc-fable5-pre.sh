#!/bin/bash
# Fable 5: Block permission-asking patterns in tool calls
# The user is NOT watching in real time — asking blocks the work.
set -euo pipefail

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# Only check Bash commands
if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

# Check for permission-asking patterns — comprehensive blocklist
if echo "$TOOL_INPUT" | grep -qiE '(can i|should i|shall i|may i|want me to|do you want me to|permission to|would you like me to|need your permission|let me know if you want)'; then
  echo "[Fable5] Autonomous mode: the user is not watching in real time — proceed without asking" >&2
  exit 1
fi

exit 0
