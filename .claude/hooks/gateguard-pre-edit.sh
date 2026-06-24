#!/usr/bin/env bash
# GateGuard: Pre-edit verification for first-touch files
# On first edit to a file, warns agent to verify understanding
set -euo pipefail

HOOK_PROFILE="${HOOK_PROFILE:-standard}"
if [ "$HOOK_PROFILE" = "minimal" ]; then
  exit 0
fi

INPUT=$(cat 2>/dev/null || echo "{}")
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tool_input = d.get('toolInput') or d.get('tool_input') or {}
    print(tool_input.get('file_path') or tool_input.get('filePath') or '')
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Resolve to absolute path
RESOLVED_PATH="$FILE_PATH"
if [[ "$FILE_PATH" != /* ]]; then
  RESOLVED_PATH="${CLAUDE_PROJECT_DIR:-.}/$FILE_PATH"
fi

# Skip non-existent files (new file creation)
if [ ! -f "$RESOLVED_PATH" ]; then
  exit 0
fi

# Track first-touch via sentinel file
SENTINEL_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/.gateguard"
mkdir -p "$SENTINEL_DIR"
FILE_HASH=$(echo "$RESOLVED_PATH" | md5sum 2>/dev/null | cut -c1-16 || echo "$RESOLVED_PATH" | md5 2>/dev/null || echo "$RESOLVED_PATH")
SENTINEL_FILE="$SENTINEL_DIR/$FILE_HASH"

if [ ! -f "$SENTINEL_FILE" ]; then
  touch "$SENTINEL_FILE"
  echo "[GateGuard] FIRST EDIT: $FILE_PATH — ensure you have read this file and understand its contents before editing." >&2
fi

exit 0
