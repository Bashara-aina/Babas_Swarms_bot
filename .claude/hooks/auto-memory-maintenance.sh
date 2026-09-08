#!/usr/bin/env bash
# Session cache maintenance: runs at SessionEnd.
# Prunes stale Claude Code session JSONL caches (keep newest 10) to prevent
# unbounded disk growth.
#
# NOTE: The old L1/L4/L5 claude-flow memory layers (checkpoints, observations,
# auto-memory-store GraphRAG) were archived as non-POPW. This hook no longer
# touches those paths.
set -euo pipefail

# Prune old session JSONL caches (keep newest 10)
prune_session_cache() {
    local cache_dir="$HOME/.claude/projects/-home-newadmin-swarm-bot"
    [ -d "$cache_dir" ] || return 0
    local count=0
    while IFS= read -r f; do
        rm -f "$f" 2>/dev/null
        count=$((count + 1))
        echo "[auto-cleanup] Pruned stale cache: $(basename "$f")" >&2
    done < <(ls -1t "$cache_dir"/*.jsonl 2>/dev/null | tail -n +11)
    [ "$count" -gt 0 ] && echo "[auto-cleanup] Removed $count stale session cache files" >&2
}

prune_session_cache
exit 0
