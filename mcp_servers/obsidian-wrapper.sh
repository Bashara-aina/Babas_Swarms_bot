#!/bin/bash
# Obsidian MCP filter: node prints startup spam to stdout (dotenvx).
# We run node, pipe through sed to drop non-JSON lines, and exec the
# result so stdin/stdout connect directly to the MCP Python SDK.
# Usage: obsidian-wrapper.sh <node_bin> <script> [args...]
#   node_bin  = /home/newadmin/.local/node18/bin/node
#   script    = /home/newadmin/swarm-bot/mcp_servers/obsidian-patched/index.js
#   args      = remaining args after script

_node="$1"
_script="$2"
shift 2 || shift 1
exec $_node "$_script" "$@" 2>/dev/null | sed -u '/^{/!d'