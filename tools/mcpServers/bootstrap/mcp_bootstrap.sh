#!/bin/bash
# MCP Server Bootstrap - filters startup messages from MCP servers
# This wrapper swallows any non-JSON output from the server until JSON-RPC begins
#
# Usage:
#   mcp_bootstrap.sh @scope/package arg1 arg2   (npx package)
#   mcp_bootstrap.sh command arg1 arg2         (direct command like ruflo mcp start)

FIFO=$(mktemp -u)
mkfifo "$FIFO"

# Filter stdout - skip non-JSON lines until JSON-RPC begins
{
    while IFS= read -r line; do
        if [[ "$line" == \{* ]]; then
            echo "$line"
            break
        fi
        # Skip non-JSON lines (startup messages)
    done
    # Now pass through everything as-is
    cat
} < "$FIFO" &

PIPER=$!

# Determine if first arg is an npx package (starts with @)
if [[ "$1" == @* ]]; then
    # npx-based server
    npx -y "$@" > "$FIFO" 2>/dev/null
else
    # Direct command (e.g., ruflo mcp start)
    "$@" > "$FIFO" 2>/dev/null
fi

# Cleanup
kill $PIPER 2>/dev/null
rm -f "$FIFO"