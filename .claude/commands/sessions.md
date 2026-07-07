---
description: List all saved sessions from ~/.claude/session-data/ with dates and context for easy picking.
---

# Sessions Command

Shows all available session resume files so you can pick which one to load.

## Process

### Step 1: List session files

```bash
ls -lt ~/.claude/session-data/*-session.tmp 2>/dev/null
```

If none found, check the project's auto-session system:

```bash
cat /home/newadmin/swarm-bot/.claude-flow/metrics/last-session.json 2>/dev/null
```

### Step 2: Show a picker

```bash
SESSION_DIR="$HOME/.claude/session-data"
if [ -d "$SESSION_DIR" ] && [ "$(find "$SESSION_DIR" -name '*-session.tmp' | head -1)" ]; then
  echo "Available sessions:"
  idx=1
  for f in "$SESSION_DIR"/*-session.tmp; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    first=$(head -1 "$f")
    echo "  [$idx] $name — $first"
    idx=$((idx + 1))
  done
  echo ""
  echo "To load: /resume-session ~/.claude/session-data/<filename>"
else
  echo "No session files found. Sessions auto-save at start/end. Run a session first."
fi
```

### Step 3: Prompt

After listing, ask: "Which session would you like to resume? Run /resume-session <filename>"

## Notes

- Sessions auto-save at session start and end by session.js
- Native /resume is a Claude Code built-in for crash recovery (looks at PIDs, not saved sessions)
- Use /resume-session for our saved session system
- Use /save-session to manually save the current session
