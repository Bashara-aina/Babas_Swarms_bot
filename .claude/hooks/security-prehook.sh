#!/usr/bin/env bash
# PreToolUse hook: enhanced security denylist replacing block-dangerous-git.sh
set -euo pipefail

HOOK_PROFILE="${HOOK_PROFILE:-standard}"

# Get the command being run (bash-only parsing, no Python subprocess)
INPUT=$(cat 2>/dev/null || echo "{}")
if [ -n "$INPUT" ] && [ "$INPUT" != "{}" ]; then
  # Extract command field from JSON using bash pattern matching
  # Matches: "command": "the actual command" or "Command": "..." or "bash_command": "..."
  CMD=$(echo "$INPUT" | grep -oP '"command"\s*:\s*"\K[^"]+' 2>/dev/null | head -1)
  [ -z "$CMD" ] && CMD=$(echo "$INPUT" | grep -oP '"Command"\s*:\s*"\K[^"]+' 2>/dev/null | head -1)
  [ -z "$CMD" ] && CMD=$(echo "$INPUT" | grep -oP '"bash_command"\s*:\s*"\K[^"]+' 2>/dev/null | head -1)
else
  CMD=""
fi

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
    echo "[SECURITY] Blocked dangerous command: '$pattern'" >&2
    exit 1
  fi
done

# Check file access patterns (in strict/standard mode)
if [ "$HOOK_PROFILE" != "minimal" ]; then
  for pattern in "${FILE_PATTERNS[@]}"; do
    if echo "$CMD" | grep -qE "$pattern" 2>/dev/null; then
      echo "[SECURITY] Blocked sensitive file access: '$pattern'. Use Read tool instead." >&2
      exit 1
    fi
  done
fi

# Silent on success — no stdout so success doesn't attach to the transcript.
exit 0
