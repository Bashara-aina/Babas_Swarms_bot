#!/usr/bin/env bash
# Auto-prune completed tasks from Claude Code's task store.
# Runs at SessionEnd — removes only `completed` task JSONs, keeps pending/in_progress.
# Prevents task_reminder attachments from growing without bound.
set -euo pipefail

TASKS_DIR="${HOME}/.claude/tasks"
[ -d "$TASKS_DIR" ] || exit 0

pruned=0
for f in "$TASKS_DIR"/*/*.json; do
  [ -f "$f" ] || continue
  if python3 -c "
import json, sys
try:
    d = json.load(open('$f'))
    sys.exit(0 if d.get('status') == 'completed' else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
    rm -f "$f"
    pruned=$((pruned + 1))
  fi
done

# Remove now-empty session dirs
for d in "$TASKS_DIR"/*/; do
  [ -d "$d" ] || continue
  if [ -z "$(ls -A "$d" 2>/dev/null || true)" ]; then
    rmdir "$d" 2>/dev/null || true
  fi
done

[ "$pruned" -gt 0 ] && echo "[auto-prune-tasks] Pruned $pruned completed tasks" >&2
exit 0
