#!/usr/bin/env bash
# SessionStart hook: inject Superpowers SDLC methodology context
# Supports Claude Code (hookSpecificOutput.additionalContext),
# Cursor (additional_context), and Copilot CLI (additionalContext).
set -euo pipefail

INJECT_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/superpowers_bootstrap.md"
SKILL_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/skills/using-superpowers/SKILL.md"

# Always write bootstrap file as fallback
cat > "$INJECT_FILE" << 'INJECT'
---
name: superpowers_bootstrap
description: Superpowers SDLC methodology -- auto-injected at session start
mode: bootstrap
hidden: true
---

# SUPERPOWERS SDLC METHODOLOGY -- ACTIVE

## Workflow Priority
1. ALWAYS check available skills first (they are listed in system reminders)
2. Follow: brainstorming -> writing-plans -> executing-plans -> tdd -> requesting-code-review -> finishing-a-development-branch
3. When uncertain or requirements are ambiguous -> run brainstorming
4. When design is approved -> run writing-plans
5. When tasks are defined -> run executing-plans
6. Before asking for human review -> run requesting-code-review
7. When branch is complete -> run finishing-a-development-branch

## Data Locations
- Specs: .superpowers/specs/
- Plans: .superpowers/plans/
- Review artifacts: .claude/reviews/
- Observations: .superpowers/homunculus/observations/

## Red Flags (slow down when these appear)
- You haven't read the relevant files yet
- You're modifying more than 3 files without a plan
- Requirements are ambiguous
- There's no test for the code you're writing
- You haven't checked gitnexus_impact for changed symbols
INJECT

echo "[superpowers] Injected bootstrap context" >&2

# Attempt to inject SKILL.md content as additional context
# This works with Claude Code's hookSpecificOutput mechanism
if [ -f "$SKILL_FILE" ]; then
  # JSON-escape the SKILL.md content and output as structured context
  ESCAPED=$(python3 -c "
import json, sys
with open('$SKILL_FILE') as f:
    content = f.read()
# Output as Claude Code additionalContext
print(json.dumps({
    'additionalContext': {
        'file': '.claude/skills/using-superpowers/SKILL.md',
        'content': content,
        'description': 'Superpowers meta-skill: always check skills before acting'
    }
}))
" 2>/dev/null || true)

  if [ -n "$ESCAPED" ]; then
    # Write to stdout for Claude Code to pick up as hookSpecificOutput
    echo "$ESCAPED"
  fi
fi

exit 0
