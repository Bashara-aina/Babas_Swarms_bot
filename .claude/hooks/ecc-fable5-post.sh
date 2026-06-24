#!/bin/bash
# Fable 5: Check output doesn't end with plans, promises, or hedging
set -euo pipefail

OUTPUT_FILE="${CLAUDE_OUTPUT_FILE:-}"
[ -z "$OUTPUT_FILE" ] || [ ! -f "$OUTPUT_FILE" ] && exit 0

LAST_LINES=$(tail -5 "$OUTPUT_FILE" 2>/dev/null || true)

# Check for promise-endings (plans, next steps, I'll, questions about proceeding)
if echo "$LAST_LINES" | grep -qiE "(i.?ll|let me know|shall i|want me to|should i|next steps|i will|the next step|then i can|would you like me|here.s what i|i.m going to|my plan is|first i.ll)"; then
  echo "[Fable5-WARN] Output ends with planning/promising — Fable 5: the user is not watching. Execute now." >&2
fi

# Check for hedging (weak language)
if echo "$LAST_LINES" | grep -qiE "(i think|it seems|probably|maybe|perhaps|i believe|i suspect)"; then
  echo "[Fable5-WARN] Output contains hedging — state findings plainly or do not assert" >&2
fi

exit 0
