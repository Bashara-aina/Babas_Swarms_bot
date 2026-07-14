#!/usr/bin/env bash
# Auto-memory maintenance: runs on PreCompact and SessionEnd
# Handles: L1 auto-prune, L4→L5 auto-consolidate, L4 rotate, wiki sync
set -euo pipefail

PROJECT="${CLAUDE_PROJECT_DIR:-.}"
L1_DIR="$PROJECT/.claude-flow/data/checkpoints"
L4_DIR="$PROJECT/.superpowers/homunculus/observations"
L5_FILE="$PROJECT/.claude-flow/data/auto-memory-store.json"
WIKI_DIR="$PROJECT/.wiki"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── L1: Auto-prune checkpoints — keep last 10 ──────────────────────
prune_l1() {
    local count
    count=$(ls "$L1_DIR"/cp-*.json 2>/dev/null | wc -l)
    if [ "$count" -gt 10 ]; then
        local excess=$((count - 10))
        ls -t "$L1_DIR"/cp-*.json 2>/dev/null | tail -n "$excess" | while read -r f; do
            rm "$f"
            echo "[auto-memory] Pruned L1 checkpoint: $(basename "$f")" >&2
        done
        echo "[auto-memory] L1: $count → 10 checkpoints" >&2
    fi
}

# ── L4: Rotate file observations — keep last 100 ───────────────────
prune_l4() {
    local count
    count=$(ls "$L4_DIR"/*.json 2>/dev/null | wc -l)
    if [ "$count" -gt 100 ]; then
        local excess=$((count - 100))
        ls -t "$L4_DIR"/*.json 2>/dev/null | tail -n "$excess" | while read -r f; do
            rm "$f"
        done
        echo "[auto-memory] L4: $count → 100 observations" >&2
    fi
}

# ── L4→L5: Consolidate recent observations into GraphRAG ───────────
consolidate_to_l5() {
    if [ ! -f "$L5_FILE" ]; then
        echo "[]" > "$L5_FILE"
    fi

    # Find observation files newer than last consolidation
    local marker="$PROJECT/.claude-flow/data/.last-obs-consolidation"
    local since="1970-01-01"
    [ -f "$marker" ] && since=$(cat "$marker")

    local new_obs=0
    for f in "$L4_DIR"/*.json; do
        [ -f "$f" ] || continue
        local ftime
        ftime=$(stat -c '%Y' "$f" 2>/dev/null || echo 0)
        local since_epoch
        since_epoch=$(date -d "$since" +%s 2>/dev/null || echo 0)
        [ "$ftime" -le "$since_epoch" ] && continue

        python3 -c "
import json, hashlib
with open('$f') as f:
    obs = json.load(f)

# Skip legacy observations without tool field
if not obs.get('tool') or obs['tool'] == '?':
    exit(0)

l5 = json.load(open('$L5_FILE'))

# Create summary from observation
content = obs.get('command', '') or obs.get('result_preview', '')
if not content:
    exit(0)

summary = f\"[{obs['tool']}] {content[:100]}\"
entry_id = hashlib.sha256(summary.encode()).hexdigest()[:16]

# Skip if already exists
if any(e.get('id') == entry_id for e in l5):
    exit(0)

entry = {
    'id': entry_id,
    'key': f'auto-obs-{entry_id[:8]}',
    'content': content,
    'summary': summary,
    'namespace': 'auto-memory',
    'type': 'observation',
    'metadata': {'source': 'observation', 'tool': obs['tool'], 'timestamp': '$TIMESTAMP'},
    'createdAt': int(__import__('time').time()),
    'accessCount': 0,
    'confidence': 0.5,
}
l5.append(entry)
with open('$L5_FILE', 'w') as f:
    json.dump(l5, f, indent=2)
print(f'[auto-memory] L4→L5: consolidated {summary[:50]}...')
" 2>&1 | grep -v '^$' | while read -r line; do echo "$line" >&2; done
        new_obs=$((new_obs + 1))
    done

    echo "$TIMESTAMP" > "$marker"
    echo "[auto-memory] L4→L5: processed $new_obs new observations" >&2
}

# ── L5: Auto-update accessCount feedback ──────────────────────────
update_l5_feedback() {
    # Reset confidence on entries never accessed for 30+ days
    python3 -c "
import json, time
with open('$L5_FILE') as f:
    l5 = json.load(f)
changed = 0
for e in l5:
    # Decay confidence for untouched entries
    if e.get('accessCount',0) == 0:
        age_days = (time.time() - (e.get('createdAt',0) or 0)) / 86400
        if age_days > 30 and e.get('confidence',0.5) > 0.2:
            e['confidence'] = max(0.1, e['confidence'] - 0.1)
            changed += 1
if changed:
    with open('$L5_FILE', 'w') as f:
        json.dump(l5, f, indent=2)
    print(f'[auto-memory] L5: decayed confidence on {changed} stale entries')
" 2>&1 | while read -r line; do echo "$line" >&2; done
}

# ── Run all maintenance ──────────────────────────────────────────
prune_l1
prune_l4
consolidate_to_l5
update_l5_feedback

exit 0
