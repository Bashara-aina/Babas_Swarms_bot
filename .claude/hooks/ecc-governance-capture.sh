#!/usr/bin/env bash
# ECC Governance Capture: Captures secrets, policy violations, approval requests
# Only active when ECC_GOVERNANCE_CAPTURE=1
set -euo pipefail

if [ "${ECC_GOVERNANCE_CAPTURE:-0}" != "1" ]; then
  exit 0
fi

INPUT=$(cat 2>/dev/null || echo "{}")
GOVERNANCE_DIR="${CLAUDE_PROJECT_DIR:-.}/.superpowers/governance"
mkdir -p "$GOVERNANCE_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('toolName', d.get('tool_name', 'unknown')))
except:
    print('unknown')
" 2>/dev/null || echo "unknown")

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tool_input = d.get('toolInput') or d.get('tool_input') or {}
    print(tool_input.get('file_path') or tool_input.get('filePath') or '')
except:
    print('')
" 2>/dev/null || echo "")

# Check for secrets in the input
echo "$INPUT" | python3 -c "
import sys, json, re
try:
    d = json.load(sys.stdin)
    raw = json.dumps(d)
    secret_patterns = [
        r'api[-_]?key[s]?[\"\'\\s]*[:=][\"\\']?[a-zA-Z0-9_]{16,}',
        r'token[\"\'\\s]*[:=][\"\\']?[a-zA-Z0-9_]{16,}',
        r'secret[\"\'\\s]*[:=][\"\\']?[a-zA-Z0-9_]{16,}',
        r'password[\"\'\\s]*[:=][\"\\']?[^\"\\'\\s]{4,}',
        r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
    ]
    for p in secret_patterns:
        if re.search(p, raw, re.IGNORECASE):
            print(f'SECRET PATTERN DETECTED: {p[:40]}')
            sys.exit(0)
    print('CLEAN')
" 2>/dev/null | grep -q "SECRET" && {
  echo "$TIMESTAMP | $TOOL_NAME | $FILE_PATH | POTENTIAL SECRET" >> "$GOVERNANCE_DIR/alerts.log"
  echo "[ECC Governance] ⚠️  Potential secret detected in $TOOL_NAME operation on $FILE_PATH" >&2
  echo "  See .superpowers/governance/alerts.log" >&2
}

exit 0
