#!/bin/bash
# MCP Server Bootstrap - filters startup messages from MCP servers
# This wrapper swallows any non-JSON output from the server until JSON-RPC begins
#
# Usage:
#   mcp_bootstrap.sh @scope/package arg1 arg2   (npx package)
#   mcp_bootstrap.sh command arg1 arg2           (direct command like ruflo mcp start)
#
# Environment variables are passed through to the MCP server.

FIFO=$(mktemp -u)
mkfifo "$FIFO"

# Filter stdout - skip non-JSON lines until JSON-RPC begins
# Keep reading until we hit a line that's valid JSON (starts with '{')
# then pass everything through (including the first JSON line)
{
    while IFS= read -r line; do
        if [[ "$line" =~ ^\{.* ]]; then
            # Found JSON start - echo it and switch to cat mode
            echo "$line"
            break
        fi
        # Skip non-JSON lines (startup messages)
    done
    # Now pass through everything as-is (remaining JSON + future output)
    cat
} < "$FIFO" &
PIPER=$!

# Determine if first arg is an npx package (starts with @)
if [[ "$1" == @* ]]; then
    # npx-based server - pass env vars through
    npx -y "$@" > "$FIFO" 2>/dev/null
else
    # Direct command (e.g., ruflo mcp start) - pass env vars through
    "$@" > "$FIFO" 2>/dev/null
fi

# Cleanup
kill $PIPER 2>/dev/null
rm -f "$FIFO"
