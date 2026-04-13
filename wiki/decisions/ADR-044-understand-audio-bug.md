---
title: Adr 044 Understand Audio Bug
type: decision
status: stub
tags: [decisions, general]
created: 2026-04-13
updated: 2026-04-13
summary: Stub — needs enrichment. Auto-added frontmatter during QC restructure.
wikilinks: []
confidence: low
source: migration
project: general
---

# ADR-044: BUG — understand_audio Not Implemented in minimax_media.py

## Status
Documented: 2026-04-12

## Context

ADR-043 planned `tools/minimax_media.py` with 4 function wrappers:
- `understand_image(prompt, image_source)`
- `web_search(query)`
- `generate_image(prompt, aspect_ratio)`
- `generate_speech(text, voice_id, speed)`

**Bug found in review (cycle 13):** The file also imports `understand_audio` but this function is **never defined** in `minimax_media.py`.

**Call sites:**
- `handlers/media_tools.py:400` — imports `understand_audio` from `tools.minimax_media`
- `tools/video.py:176` — calls `tools.minimax_media.understand_audio(actual_path)`

The call in `video.py` is for transcribing audio extracted from videos (used in `_transcribe_video_audio()`).

---

## Decision

**DO NOT MODIFY PRODUCTION CODE.** This is a wiki loop session — production fixes require separate implementation task.

This ADR documents the bug for future remediation.

---

## Bug Analysis

### Missing Implementation

`tools/minimax_media.py` does not define `understand_audio`. The file only contains the 4 functions planned in ADR-043.

### Call Chain

```
tools/video.py:_transcribe_video_audio()
  → calls tools.minimax_media.understand_audio(actual_path)
  → function not defined → ImportError/AttributeError at runtime
```

### Workaround in Place

`tools/video.py` catches transcription failures silently and returns `""`:
```python
try:
    transcript = await tools.minimax_media.understand_audio(actual_path)
except Exception:
    return ""  # Silent failure, user sees metadata without transcript
```

So video transcription silently fails when `understand_audio` is called, but the error is caught and empty string returned — user sees video metadata but no transcript.

### Correct Fix Options

**Option A** (preferred): Implement `understand_audio` in `minimax_media.py` delegating to `core.utils.multimodal_processor.transcribe_voice()`

**Option B**: Change call sites to import from `core.utils.multimodal_processor` directly

---

## Files Affected

| File | Issue |
|------|-------|
| `tools/minimax_media.py` | Missing `understand_audio` definition |
| `tools/video.py:176` | Calls undefined function (caught by try/except) |
| `handlers/media_tools.py:400` | Imports undefined function |

---

## Consequences

- Video transcription via `minimax_media.understand_audio()` silently fails
- User receives video metadata but no transcript
- Error is caught by try/except in `video.py` — no crash
- `handlers/media_tools.py` imports the function but it's unclear if it's ever called

---

## Recommended Fix

Implement `understand_audio` in `tools/minimax_media.py`:

```python
async def understand_audio(audio_path: str) -> str:
    """Transcribe audio file using MiniMax multimodal processor."""
    try:
        from core.utils.multimodal_processor import transcribe_voice
        return await transcribe_voice(audio_path)
    except Exception as e:
        logger.warning("understand_audio failed: %s", e)
        return ""
```

Then update call sites to use this wrapper instead of calling `transcribe_voice` directly.

---

## Reviewer Notes

- Bug was caught during cycle 13 review
- Silent failure pattern means no user-facing error, just missing transcript
- `transcribe_voice` in `core.utils.multimodal_processor` already exists and works
- Fix is straightforward delegation pattern
