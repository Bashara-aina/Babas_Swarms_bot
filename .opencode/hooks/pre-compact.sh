#!/bin/bash
# pre-compact hook — runs before context compaction
# Extracts session state including verbatim last user prompt for next session

set -e

echo "[pre-compact] Saving checkpoint state with last prompt..."

# Extract the LAST user message from conversation (user prompt = source of truth)
LAST_PROMPT=""
if [ -f /tmp/legion_conversation.txt ]; then
    # Look for user message markers — Claude Code uses "user" at turn start
    # Get the last complete user message block
    LAST_PROMPT=$(awk '
        BEGIN { in_user = 0; last_line = "" }
        /^## User/ { in_user = 1; last_line = "" }
        in_user && /^## User/ && last_line != "" { in_user = 0 }
        in_user && /^[>*]/ { last_line = last_line " " $0 }
        in_user { last_line = last_line "\n" $0 }
        END { print last_line }
    ' /tmp/legion_conversation.txt 2>/dev/null | tail -c 2000)
fi

# If awk extraction failed, try python
if [ -z "$LAST_PROMPT" ] || [ ${#LAST_PROMPT} -lt 5 ]; then
    LAST_PROMPT=$(python3 -c "
import re, sys
try:
    content = open('/tmp/legion_conversation.txt').read()
    # Find user message blocks: lines starting with > or *
    matches = re.findall(r'(?:^|\n)(?:>|\*)(.*?)(?=\n\n|\Z)', content, re.DOTALL)
    if matches:
        # Return last non-empty user message
        for m in reversed(matches):
            m = m.strip()
            if len(m) > 10:
                print(m[:2000].replace('\n', ' '))
                break
except:
    pass
" 2>/dev/null || echo "")
fi

# Save hot session context
cp /tmp/legion_session_context.txt /tmp/legion_session_context.backup 2>/dev/null || true
cp /tmp/legion_hermes_skills.txt /tmp/legion_hermes_skills.backup 2>/dev/null || true

# Write last user prompt to a dedicated file (next session reads this first)
if [ -n "$LAST_PROMPT" ] && [ ${#LAST_PROMPT} -gt 5 ]; then
    echo "$LAST_PROMPT" > /tmp/legion_last_user_prompt.txt
    echo "[pre-compact] Last prompt captured: ${#LAST_PROMPT} chars"
else
    # Create marker so we know compaction fired but had no user prompt
    echo "NO_USER_PROMPT" > /tmp/legion_last_user_prompt.txt
    echo "[pre-compact] Warning: no user prompt found in conversation"
fi

# Write checkpoint metadata including last prompt
python3 -c "
import sys, json, os
from pathlib import Path

checkpoint = {
    'timestamp': __import__('datetime').datetime.now().isoformat(),
    'session_id': os.environ.get('SESSION_ID', 'unknown'),
    'conversation_exists': Path('/tmp/legion_conversation.txt').exists(),
    'context_size': Path('/tmp/legion_conversation.txt').stat().st_size if Path('/tmp/legion_conversation.txt').exists() else 0,
}

try:
    last_prompt_path = Path('/tmp/legion_last_user_prompt.txt')
    if last_prompt_path.exists():
        content = last_prompt_path.read_text()
        if content != 'NO_USER_PROMPT':
            checkpoint['last_user_prompt'] = content
        else:
            checkpoint['last_user_prompt'] = ''
except:
    checkpoint['last_user_prompt'] = ''

Path('/tmp/legion_compaction_checkpoint.json').write_text(json.dumps(checkpoint, indent=2))
print(f'Checkpoint metadata: {checkpoint[\"context_size\"]} chars')
" 2>/dev/null || true

echo "[pre-compact] Checkpoint complete"