# /skill — Write Memory Skill Note (Phase 9)
# Usage: /skill <slug>
## Phase 9: Memory & Skill Capture
SLUG="${1:-skill-$(date +%Y-%m-%d)}"
cat > .opencode/memory/$(date +%Y-%m-%d)-${SLUG}.md << 'EOF'
---
date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
session_type: implementation
tools_used: []
outcome: one sentence summary
---

## What Was Done
-

## Key Decisions
-

## Patterns to Reuse
-

## Files Changed
-

## Do NOT Repeat
-
EOF
echo "Created .opencode/memory/$(date +%Y-%m-%d)-${SLUG}.md"