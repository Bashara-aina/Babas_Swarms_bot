#!/usr/bin/env bash
# Block dangerous git commands from running via Claude Code.
set -euo pipefail

CMD="${CLAUDE_TOOL_COMMAND:-$*}"

# Patterns that are always dangerous
DANGEROUS_PATTERNS=(
  'git push --force'
  'git push -f'
  'git reset --hard'
  'git checkout .'
  'git clean -f'
  'git branch -D'
  'git rebase --abort'
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qF "$pattern"; then
    echo "[BLOCKED] Dangerous git command detected: $pattern"
    echo "If you really want to run this, use the git tool directly."
    exit 1
  fi
done

exit 0
