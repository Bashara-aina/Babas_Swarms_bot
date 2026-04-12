---
title: media-processing-guide
domain: voice-media
impact_score: 8
last_updated: 2026-04-12
injects_into: handlers
tokens_estimated: 580
---

# Media Processing Guide

## ONE-LINE SUMMARY
All media processing pipelines — MiniMax MCP (image gen, TTS, web search), video keyframe extraction, document formats (PDF/Excel/Word/CSV/EPUB/PPTX), and temp file management.

## FACTS
- **Image Generation**: MiniMax `TokenPlan_image_generation` via MCP → `/imagine` command
  - Aspect ratios: 1:1, 16:9, 9:16, 4:3, 3:4
  - Result: PNG saved to temp file, sent as document, temp file deleted after sending
  - If MCP unavailable: clear error message returned to user
- **Image Analysis**: MiniMax `CodingPlan_understand_image` via MCP → sent photo
  - Supported formats: JPEG, PNG, WebP
  - Max photo size: 20 MB (checked before download)
  - Returns text description from vision model
- **Web Search**: MiniMax `CodingPlan_web_search` via MCP → `/search` command
  - Returns formatted results string
  - Timeout: 120s via MCP client
- **TTS/Speech**: MiniMax `TokenPlan_speech_generation` via MCP → `/speak` command
  - Voices: English_expressive_narrator, male-qn-qingse, female-shaonv
  - Speed: 0.5–2.0 (default 1.0)
  - Returns MP3 saved to temp file, sent as voice message
- **Video Analysis**: `/videowatch` handler
  - Downloads video (max 100 MB)
  - Extracts keyframes: 1 frame per 10 seconds, max 8 frames, 640px width
  - Transcribes audio via `understand_audio()` → faster-whisper
  - Analyzes up to 4 keyframes via `understand_image()`
  - Response: keyframe descriptions + audio transcript
- **Temp file management**: All handlers use `tempfile.NamedTemporaryFile(delete=False)` + explicit `os.unlink()` in `finally`
- **Corrupted media handling**: Generic try/except on all operations → user sees "Error: {exc[:200]}"
- **No file type magic bytes validation** — relies on Telegram's MIME type + extension

## DOCUMENT PROCESSING (tools/documents.py)
- **PDF**: `pdfplumber` → text extraction, table extraction, OCR fallback (pytesseract)
- **Excel**: `openpyxl` → markdown table output, max 100 rows default
- **Word**: `python-docx` → paragraph text extraction, max 8000 chars
- **CSV**: built-in `csv` module → markdown table, max 200 rows
- **PPTX**: `python-pptx` → slide text extraction, max 50 slides
- **EPUB**: `ebooklib` + BeautifulSoup → metadata + HTML item text extraction
- **OCR (image)**: `pytesseract` with lang parameter (default "eng")
- **OCR (PDF)**: `pdfplumber` page-to-image → tesseract on each page
- All document functions are async wrappers around sync implementations (via `run_in_executor`)
- Truncation: 8000 chars default for text-heavy formats
- Page range syntax: "all", "1-5", "3", "1,3,5" (0-indexed internally)

## LEGION BEHAVIOR RULES
1. Temp files must always be deleted in `finally` block — never rely on `delete=True`
2. Photo size check happens before download — prevents memory exhaustion
3. Video size limit: 100 MB — hard limit from Telegram API
4. Image generation always cleans up temp PNG after sending
5. Document processing runs in thread executor — never blocks event loop
6. All MiniMax MCP calls have 120s timeout — if MCP unavailable, return clear error
7. Chunked output for long results (>4000 chars) via `send_chunked()`
8. Corrupted media: catch all exceptions → return "Error: {msg[:200]}" to user

## EXAMPLES
Bashara: `/imagine a sunset over mountains 16:9` → MiniMax image gen → PNG sent as document
Bashara: sends photo with caption "what's in this?" → MiniMax vision → description
Bashara: `/search latest AI news` → MiniMax web search → formatted results
Bashara: `/speak Hello, how are you?` → MiniMax TTS → MP3 as voice message
Bashara: sends video → keyframes extracted + transcribed → description + transcript
Bashara: sends DOCX file → python-docx → text extracted → sent as message
Bashara: sends scanned PDF → pdfplumber fails → OCR fallback → pytesseract

## ANTI-PATTERNS
1. No file type validation beyond extension — malicious files could be uploaded
2. Video keyframe extraction uses blocking `subprocess` (ffmpeg) not async
3. OCR requires `tesseract-ocr` system package — not pip-installable
4. Temp frame directory (`video_frames_*`) uses `shutil.rmtree()` — could fail on permission errors
5. **CRITICAL BUG**: `understand_audio` is imported from `tools.minimax_media` in `media_tools.py:400` and `video.py:176` but is NEVER defined — runtime ImportError. Should use `core.utils.multimodal_processor.transcribe_voice` instead.
6. No cleanup on Ctrl+C / abrupt termination — temp files accumulate in /tmp

## GAPS
- `understand_audio` function missing from `tools/minimax_media.py` — called but undefined
- MiniMax MCP `understand_audio` is referenced but doesn't exist — actual audio transcription available via `core.utils.multimodal_processor.transcribe_voice`

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Skeptic concerns: understand_audio undefined is a CRITICAL runtime bug — page accurately documents this gap in ANTI-PATTERNS. Page correctly identifies the discrepancy between referenced and implemented functions.
