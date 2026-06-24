#!/usr/bin/env bash
# PreToolUse hook: enhanced security denylist replacing block-dangerous-git.sh
set -euo pipefail

HOOK_PROFILE="${HOOK_PROFILE:-standard}"

# Get the command being run
INPUT=$(cat 2>/dev/null || echo "{}")
CMD=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tool_input = d.get('toolInput') or d.get('tool_input') or {}
    print(tool_input.get('command') or tool_input.get('Command') or tool_input.get('bash_command') or '')
except:
    print('')
" 2>/dev/null || echo "")

# Security denylist patterns
DANGEROUS_PATTERNS=(
  'git push --force'
  'git push -f'
  'git reset --hard'
  'git checkout \.'
  'git checkout --'
  'git restore \.'
  'git clean -f'
  'git clean -fd'
  'git branch -D'
  'rm -rf /'
  'rm -rf ~'
  'rm -rf \*'
  'mkfs\..*'
  'dd if='
  '> /dev/'
)

# File access patterns
FILE_PATTERNS=(
  'cat \.env'
  'source \.env'
  'cat \.env\.'
  'cat ~/\.ssh/'
  'cat /etc/shadow'
  'cat /etc/passwd'
)

# Check dangerous patterns
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qE "$pattern" 2>/dev/null; then
    echo "[SECURITY] Blocked dangerous command: '$pattern'"
    exit 1
  fi
done

# Check file access patterns (in strict/standard mode)
if [ "$HOOK_PROFILE" != "minimal" ]; then
  for pattern in "${FILE_PATTERNS[@]}"; do
    if echo "$CMD" | grep -qE "$pattern" 2>/dev/null; then
      echo "[SECURITY] Blocked sensitive file access: '$pattern'. Use Read tool instead."
      exit 1
    fi
  done
fi

exit 0
