# AUDIT 11 — Subtask 1: Fix bridges/__init__.py

**Date:** 2026-04-12
**Status:** ✅ COMPLETE

## Problem
`bridges/__init__.py` had wrong imports:
- `run_screenpipe_query` — function doesn't exist (actual export is `ScreenpipeBridge` class)
- `meet_join_url`, `build_room_token`, `livekit_status_message` — missing from livekit_bridge
- `GitHubIntelEngine`, `TrendingRepo`, `RepoEvaluation` — missing from github_bridge

## Changes Made

### `__all__`
- Removed `run_screenpipe_query`, added `ScreenpipeBridge`
- Added `GitHubIntelEngine`, `TrendingRepo`, `RepoEvaluation`
- Added `meet_join_url`, `build_room_token`, `livekit_status_message`

### Screenpipe import block
```python
# Before (wrong)
from bridges.screenpipe_bridge import run_screenpipe_query

# After (correct)
from bridges.screenpipe_bridge import ScreenpipeBridge
```

### LiveKit import block (new)
```python
try:
    from bridges.livekit_bridge import meet_join_url, build_room_token, livekit_status_message
except ...
```

### GitHub import block
- Added `GitHubIntelEngine`, `TrendingRepo`, `RepoEvaluation` to both the try import and the except fallback

## Verification
```bash
python -c "import bridges; from bridges import WhatsAppBridge, ScreenpipeBridge, GitHubBridge, VoiceVoxBridge; print('bridges OK')"
# Output: bridges OK
```
