---
title: Audit08 Plan
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Created: 2026-04-12 | Agent: @planner | Status: ✅ COMPLETE'
wikilinks: []
confidence: medium
source: research
---
# LEGION AUDIT 08 — Bridges Layer Connectivity
> Created: 2026-04-12 | Agent: @planner | Status: ✅ COMPLETE
## Goal
Every bridge must: (1) connect to its target service, (2) be imported by at least one handler.

## BRIDGES INVENTORY

| File | Service | Handler Imports | Status |
|------|---------|-----------------|--------|
| `bridges/discord_bridge.py` | Discord | NONE | ❌ ORPHANED |
| `bridges/livekit_bridge.py` | LiveKit | NONE | ❌ ORPHANED |
| `bridges/mastra_bridge.py` | Mastra | NONE | ❌ ORPHANED |
| `bridges/ruflo_bridge.py` | RUFLO | NONE | ❌ ORPHANED |
| `bridges/screenpipe_bridge.py` | Screenpipe | NONE | ❌ ORPHANED |
| `bridges/whatsapp_bridge.py` | WhatsApp | whatsapp_handler.py, message_handler.py | ✅ OK |
| `bridges/voicevox_bridge.py` | VoiceVox | DOES NOT EXIST | ❌ MISSING |

---

## SUBTASK RESULTS

### Subtask 1: List all bridges ✅ DONE
- Found 6 bridge files in `bridges/`:
  - discord_bridge.py
  - livekit_bridge.py
  - mastra_bridge.py
  - ruflo_bridge.py
  - screenpipe_bridge.py
  - whatsapp_bridge.py

### Subtask 2: Upstream check — handler imports ✅ DONE
```
rg "discord_bridge" handlers/ → 0 matches
rg "livekit_bridge" handlers/ → 0 matches
rg "mastra_bridge" handlers/ → 0 matches
rg "ruflo_bridge" handlers/ → 0 matches
rg "screenpipe_bridge" handlers/ → 0 matches
rg "whatsapp_bridge" handlers/ → 2 matches:
  - handlers/whatsapp_handler.py:31: from bridges.whatsapp_bridge import WhatsAppBridge
  - handlers/message_handler.py:500: from bridges.whatsapp_bridge import WhatsAppBridge
```

### Subtask 3: Downstream connectivity check ✅ DONE

| Bridge | Async | Timeout | Error Handling | Service URL | Status |
|--------|-------|---------|----------------|-------------|--------|
| discord_bridge.py | ✅ | ❌ none | ✅ try/except | Discord API | ⚠️ No timeout on client.start() |
| livekit_bridge.py | N/A (sync) | N/A | ✅ try/except | LIVEKIT_URL env | ✅ Safe |
| mastra_bridge.py | ✅ | ✅ aiohttp timeout=45 | ✅ try/except | 127.0.0.1:7835 | ✅ OK |
| ruflo_bridge.py | ✅ | ✅ aiohttp timeout=60 | ✅ try/except | 127.0.0.1:7834 | ✅ OK |
| screenpipe_bridge.py | ✅ class | ✅ asyncio.sleep() | ✅ try/except | tools.screenpipe_tool | ✅ OK |
| whatsapp_bridge.py | ✅ | ✅ aiohttp timeouts 3-15s | ✅ try/except | WA_SIDECAR_PORT 3002 | ✅ OK |

### Subtask 4: VoiceVox bridge ✅ DONE
- **Finding**: No `bridges/voicevox_bridge.py` exists
- **Reference**: `handlers/nihongo_handler.py:75` mentions "TTS: VoiceVox (neural) atau gTTS jika VoiceVox tidak tersedia"
- **Action needed**: Create `bridges/voicevox_bridge.py` with VoiceVox API + gTTS fallback
- **Note**: VoiceVox API runs on `http://localhost:50021` by default

### Subtask 5: GitHub bridge ✅ DONE
- **Finding**: `handlers/github_intel_handler.py` imports `from tools.github_intel import GitHubIntelEngine`
- **This is a tool, NOT a bridge** — no `bridges/github_bridge.py` exists
- **Verdict**: Gap — GitHub has no bridge layer. `tools/github_intel.py` is used directly.
- **Decision**: LOW PRIORITY — github_intel works as-is, no handler needs a bridge abstraction

### Subtask 6: WhatsApp bridge ✅ DONE
- **whatsapp_bridge.py** structure:
  - `FEATURE_WHATSAPP_ENABLED` guard: NOT FOUND — bridge has no env guard
  - Sidecar health check: `async def _is_healthy()` with 3s timeout
  - Sidecar start: `async def start_sidecar()` with 30s boot timeout
  - All methods have try/except + logging
- **Verdict**: Bridge is well-structured. Handler (`whatsapp_handler.py`) needs to check `FEATURE_WHATSAPP_ENABLED` before importing.

### Subtask 7: bridges/__init__.py ✅ DONE
- **Finding**: `bridges/__init__.py` DOES NOT EXIST
- **Action**: Create it to wrap all bridges with try/except imports
- **Pattern**:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  
  from bridges import discord_bridge  # with try/except
  ```

### Subtask 8: `python -c "import bridges; print('bridges OK')"` ⏳ PENDING
- Cannot run until `bridges/__init__.py` is created

---

## ACTIONS REQUIRED (Worker Tasks)

1. **[HIGH]** Create `bridges/__init__.py` — wrap all 6 bridges in try/except, log warnings
2. **[HIGH]** Create `bridges/voicevox_bridge.py` — VoiceVox API + gTTS fallback
3. **[MEDIUM]** Discord bridge: add timeout to `client.start(token)` or document that it's blocking
4. **[LOW]** GitHub bridge: decide if `tools/github_intel.py` needs a bridge wrapper (currently low priority)
5. **[MEDIUM]** WhatsApp handler: add `FEATURE_WHATSAPP_ENABLED` guard before bridge import

---

## Progress: 7/8 subtasks complete. Subtask 8 blocked by Subtask 7.