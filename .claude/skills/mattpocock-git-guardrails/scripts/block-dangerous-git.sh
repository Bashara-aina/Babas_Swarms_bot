#!/bin/bash
# Git Guardrails - Block Dangerous Git Commands
# Intercepts and blocks destructive git operations

set -euo pipefail

# Read the command from stdin (JSON format: {"tool_input": {"command": "..."}})
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")

# If no command found in JSON, try raw input
if [ -z "$command" ]; then
  command="$input"
fi

# Commands to block (case-insensitive matching)
blocked_patterns=(
  "^git push"
  "^git reset --hard"
  "^git clean -f"
  "^git clean -fd"
  "^git branch -D"
  "^git checkout \."
  "^git restore \."
  "^git stash drop"
)

# Check each pattern
for pattern in "${blocked_patterns[@]}"; do
  if echo "$command" | grep -iqE "$pattern"; then
    echo "⚠️  BLOCKED: $command" >&2
    echo "" >&2
    echo "This git command is blocked by guardrails." >&2
    echo "Reason: $pattern - potentially destructive operation" >&2
    echo "" >&2
    echo "If you need to run this command, run it directly in your terminal." >&2
    echo "Guardrails only intercepts commands from Claude." >&2
    exit 2
  fi
done

# Not blocked - pass through (no output, exit 0)
exit 0