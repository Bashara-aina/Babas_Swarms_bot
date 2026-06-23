#!/usr/bin/env bash
# memory-to-wiki-sync.sh — One-way file-level mirror from Claude memory files
# to Obsidian vault. Runs at session end and on cron.
#
# Source: ~/.claude/projects/-home-newadmin-swarm-bot/memory/*.md
# Target: .wiki/memories/ (with claude- prefix, frontmatter for Obsidian)

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/newadmin/swarm-bot}"
MEMORY_SOURCE="${HOME}/.claude/projects/-home-newadmin-swarm-bot/memory"
WIKI_TARGET="${PROJECT_DIR}/.wiki/memories"

mkdir -p "$WIKI_TARGET"

if [ ! -d "$MEMORY_SOURCE" ]; then
  echo "[memory-to-wiki] Source not found: $MEMORY_SOURCE (skipping)"
  exit 0
fi

count=0
ts=$(date --iso-8601=seconds)

for f in "$MEMORY_SOURCE"/*.md; do
  [ -f "$f" ] || continue
  basename=$(basename "$f")
  target="${WIKI_TARGET}/claude-${basename}"

  # Skip if target exists and source is not newer
  if [ -f "$target" ] && [ "$f" -ot "$target" ]; then
    continue
  fi

  content=$(cat "$f")

  # If the file doesn't already have frontmatter, add it
  if ! echo "$content" | head -1 | grep -q '^---$'; then
    cat > "$target" <<EOFM
---
date: $ts
type: memory-file
source: claude-memory
---

$content
EOFM
  else
    cp "$f" "$target"
  fi

  count=$((count + 1))
done

# Clean up orphaned targets whose source files were deleted
orphan_count=0
for target in "$WIKI_TARGET"/claude-*.md; do
  [ -f "$target" ] || continue
  source_file="$MEMORY_SOURCE/$(echo "$(basename "$target")" | sed 's/^claude-//')"
  if [ ! -f "$source_file" ]; then
    rm "$target"
    orphan_count=$((orphan_count + 1))
  fi
done

echo "[memory-to-wiki] Synced $count files, removed $orphan_count orphans to $WIKI_TARGET"
