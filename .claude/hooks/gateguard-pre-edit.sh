#!/usr/bin/env bash
# GateGuard: Pre-edit verification for first-touch files
# On first edit to a file, warns agent to verify understanding
set -euo pipefail

HOOK_PROFILE="${HOOK_PROFILE:-standard}"
if [ "$HOOK_PROFILE" = "minimal" ]; then
  exit 0
fi

INPUT=$(cat 2>/dev/null || echo "{}")
if [ -n "$INPUT" ] && [ "$INPUT" != "{}" ]; then
  FILE_PATH=$(echo "$INPUT" | grep -oP '"(?:file_path|filePath)"\s*:\s*"\K[^"]+' 2>/dev/null | head -1)
else
  FILE_PATH=""
fi

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
