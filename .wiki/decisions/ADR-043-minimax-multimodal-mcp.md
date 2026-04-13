---
## Decision

---
### Architecture

```
handlers/media_tools.py       ← NEW — command + photo handlers
tools/minimax_media.py        ← NEW — thin wrappers around MiniMax function tools
core/autonomous_router.py    ← MODIFY — add SKILL_PATTERNS entries for media intents
handlers/__init__.py         ← MODIFY — register media_tools.router
```

The MiniMax tools are invoked as **function calls** inside the LLM's tool-use loop. A new `MiniMaxMedia` class in `tools/minimax_media.py` will expose `understand_image`, `web_search`, `generate_image`, `generate_speech` — each calling the respective function tool.
---


## What to Create / Modify

### 1. `tools/minimax_media.py` (NEW)

Thin async wrappers around the 4 MiniMax function tools:

```python
# understand_image(prompt, image_source)  → str description
# web_search(query)                       → str results  
# generate_image(prompt, aspect_ratio)    → str image_path/URL
# generate_speech(text, voice_id, speed)  → str audio_path/URL
```

Each wrapper:
- Calls the function tool via the conversation's tool-use mechanism
- Returns a clean string result (not raw tool output)
- Logs errors and returns a user-friendly error string

### 2. `handlers/media_tools.py` (NEW)

Aiogram router with these handlers:

| Handler | Trigger | Action |
|---------|---------|--------|
| `cmd_imagine` | `/imagine <prompt>` | Generate image, send as photo |
| `cmd_search` | `/search <query>` | Web search, format results as text |
| `cmd_speak` | `/speak <text>` | Generate speech, send as voice |
| `handle_photo` | `F.photo` | Understand image, describe it |
| `cmd_mcp_status` | `/mcp_status` | Show MiniMax MCP tool status |

All handlers check `is_allowed(msg)` first.

### 3. `core/autonomous_router.py` (MODIFY)

Add to `SKILL_PATTERNS`:

```python
"image_understanding": {
    "keywords": ["what's in this", "analyze image", "describe photo", "what does this show", "see image"],
    "handler": "media_photo",
},
"image_generation": {
    "keywords": ["generate image", "create picture", "draw", "imagine", "make art", "generate a picture"],
    "handler": "media_imagine",
},
"web_search": {
    "keywords": ["search web", "google", "look up online", "find on internet"],
    "handler": "media_search",
},
"speech_generation": {
    "keywords": ["speak this", "read aloud", "text to speech", "voice this", "say it"],
    "handler": "media_speak",
},
```

### 4. `handlers/__init__.py` (MODIFY)

Add `media_tools` to `_ROUTER_ORDER`, **before** `ai.router` (since ai is the NL catch-all and must be last). Place it near `legion_extras` or `voice`:

```python
media_tools.router,   # /imagine /search /speak + F.photo
```

### 5. `handlers/message_handler.py` (MODIFY)

Add route branches in `handle_plain_message()` for `media_photo`, `media_imagine`, `media_search`, `media_speak` similar to existing skill handlers.

---

## Priority Order (Subtasks)

### Phase 1 — Core Infrastructure
1. **`tools/minimax_media.py`** — create the media tool wrappers (blocking for all other tasks)
2. **`handlers/media_tools.py`** — create the handler router with all 5 handlers
3. **`handlers/__init__.py`** — register `media_tools.router`
4. **Test Phase 1** — `pytest tests/ -x --asyncio-mode=auto -q`

### Phase 2 — Autonomous Routing
5. **`core/autonomous_router.py`** — add SKILL_PATTERNS entries for the 4 intents
6. **`handlers/message_handler.py`** — add route branches for media skill handlers
7. **Test Phase 2** — run full test suite

### Phase 3 — Polish
8. Update `llm_client.py` or relevant prompt to expose MiniMax media tools to the LLM (so the LLM can call them directly when users describe what they want in natural language)
9. Add keyword aliases (e.g., `/genimage`, `/tts`, `/voice_gen`)
10. Final test run

---

## Consequences

### Positive
- Bot can now see, search, draw, and speak — full multi-modal pipeline
- MiniMax tools invoked directly (no stdio overhead)
- Consistent handler pattern (same as all other handlers)
- Auto-routing via SKILL_PATTERNS means natural-language triggers work without commands

### Risks
- MiniMax API keys must be set in environment (no hardcoding)
- Image generation may produce large files — consider file size limits
- Web search results may need pagination or chunking for long outputs
- Photo handling downloads the image first before passing to MiniMax — temp file management needed

### Mitigations
- All wrappers return error strings (never raise to handler level)
- Temp files cleaned up in `finally` blocks
- File size check before downloading large photos
- Async throughout (no blocking calls)

---

## File Summary

| File | Action |
|------|--------|
| `tools/minimax_media.py` | **CREATE** — MiniMax tool wrappers |
| `handlers/media_tools.py` | **CREATE** — aiogram router with 5 handlers |
| `handlers/__init__.py` | **MODIFY** — add media_tools.router to _ROUTER_ORDER |
| `core/autonomous_router.py` | **MODIFY** — add 4 SKILL_PATTERNS entries |
| `handlers/message_handler.py` | **MODIFY** — add 4 media route branches |
