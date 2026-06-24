#!/usr/bin/env bash
# ECC MCP Health Check: Validates MCP server health before MCP tool calls
# Marks unhealthy servers so they can be avoided
set -euo pipefail

HEALTH_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/mcp-health"
mkdir -p "$HEALTH_DIR"

INPUT=$(cat 2>/dev/null || echo "{}")
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('toolName', d.get('tool_name', '')))
except:
    print('')
" 2>/dev/null || echo "")

# Extract MCP server name from tool name (format: mcp__server__tool)
SERVER_NAME=$(echo "$TOOL_NAME" | python3 -c "
import sys
parts = sys.stdin.read().strip().split('__')
if len(parts) >= 2:
    print(parts[1])
else:
    print('')
" 2>/dev/null || echo "")

if [ -z "$SERVER_NAME" ]; then
  exit 0
fi

# Check if this server is marked unhealthy
UNHEALTHY_FILE="$HEALTH_DIR/${SERVER_NAME}.unhealthy"
if [ -f "$UNHEALTHY_FILE" ]; then
  FAILED_AT=$(cat "$UNHEALTHY_FILE" 2>/dev/null || echo "unknown")
  echo "[ECC MCP Health] ⚠️  Server '$SERVER_NAME' marked unhealthy since $FAILED_AT" >&2
  echo "  MCP calls to this server may fail." >&2
  echo "  To reset: rm -f '$UNHEALTHY_FILE'" >&2
fi

exit 0
