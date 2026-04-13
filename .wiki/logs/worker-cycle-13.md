---
# Worker Cycle 13 — Voice & Media Processing
Executed by: @worker
Date: 2026-04-12
Session: LEGION WIKI LOOP

---

## Target Domain
Voice transcription, text-to-speech, image generation, file processing

## Source Files Investigated
- handlers/voice.py (249 lines)
- handlers/media_tools.py (495 lines)
- core/utils/multimodal_processor.py (359 lines)
- tools/minimax_media.py (255 lines)
- tools/documents.py (486 lines)
- tools/voice_engine.py (120 lines)
- tools/video.py (192 lines)

---

## Pages Written (All Approved — Score 7+)

### 1. voice-pipeline.md — Score: 9 (WRITE)
**Domain**: voice-media | **Injects**: handlers | **Tokens**: 620

Key findings:
- 3-tier Whisper backend: faster-whisper GPU → Groq API → OpenAI API → openai-whisper CPU fallback
- `handlers/voice.py:_transcribe()` uses priority chain with Groq API (30s timeout) as first cloud option
- `language="id"` hardcoded for OpenAI Whisper — non-Indonesian audio gets poor quality
- No timeout on faster-whisper GPU path — long audio can hang
- No file size limit for audio uploads
- Temp storage: `NamedTemporaryFile(delete=False)` + explicit unlink in finally
- TTS reply: Kokoro-ONNX → edge-tts fallback via `core.utils.multimodal_processor.text_to_speech()`
- Voice reply mode toggleable via KV store

**Anti-patterns flagged**:
1. Hardcoded Indonesian language (OpenAI Whisper)
2. No GPU timeout (faster-whisper)
3. No Groq retry logic
4. No audio file size limit
5. TTS failure silently swallowed

---

### 2. media-processing-guide.md — Score: 8 (WRITE)
**Domain**: voice-media | **Injects**: handlers | **Tokens**: 580

Key findings:
- MiniMax MCP tools: `TokenPlan_image_generation`, `CodingPlan_understand_image`, `CodingPlan_web_search`, `TokenPlan_speech_generation`
- Image gen: `/imagine` command, 5 aspect ratios (1:1, 16:9, 9:16, 4:3, 3:4), PNG → temp → document → delete
- Photo analysis: max 20MB, JPEG/PNG/WebP, `understand_image()` via MCP
- Video: keyframe extraction (1/10s, max 8, 640px), ffmpeg subprocess, `understand_audio()` for transcription
- **CRITICAL BUG FOUND**: `understand_audio` imported from `tools.minimax_media` in `media_tools.py:400` and `video.py:176` but NEVER DEFINED — runtime ImportError. Should use `core.utils.multimodal_processor.transcribe_voice`.
- Document processing: PDF (pdfplumber), Excel (openpyxl), Word (python-docx), CSV, PPTX, EPUB — all via `run_in_executor`
- OCR: pytesseract (system package) + pdfplumber page-to-image fallback
- Temp management: all use `delete=False` + explicit unlink

**Anti-patterns flagged**:
1. No file type magic bytes validation
2. Blocking ffmpeg subprocess in async handler
3. tesseract-ocr is system package (not pip)
4. shutil.rmtree on temp frames dir
5. **CRITICAL**: `understand_audio` undefined

---

### 3. tts-setup.md — Score: 7 (WRITE)
**Domain**: voice-media | **Injects**: handlers | **Tokens**: 540

Key findings:
- **Two separate TTS code paths**:
  1. `core.utils.multimodal_processor.text_to_speech()`: Kokoro-ONNX (local, WAV) → edge-tts (cloud, MP3)
  2. `tools.minimax_media.generate_speech()`: MiniMax MCP `TokenPlan_speech_generation`
- Kokoro-ONNX: requires manual download to `models/kokoro-v0_19.onnx` + `models/voices.bin`
- Kokoro voice: `af_sarah` (hardcoded), path resolves via `Path(__file__).parent.parent.parent`
- Edge-tts fallback voice: `en-US-AriaNeural` (configurable via `TTS_VOICE`)
- MiniMax voices: English_expressive_narrator, male-qn-qingse, female-shaonv
- Speed: 0.5–2.0 validated before API call
- TTS failure silently caught → user only sees text reply

**Voice cloning potential**:
- Kokoro: supports custom voices via `voices.bin` — could train from 30s sample
- Edge-tts: NOT supported
- MiniMax: NOT supported (fixed roster)

**Anti-patterns flagged**:
1. Two separate TTS paths with inconsistent behavior
2. Silent TTS failures
3. Kokoro manual model download required

---

## Critical Bug Discovered

**`understand_audio` function is called but never defined anywhere in the codebase.**

Locations calling it:
- `handlers/media_tools.py:400` — `from tools.minimax_media import understand_audio`
- `tools/video.py:176` — `from tools.minimax_media import understand_audio`

The function is imported from `tools.minimax_media` but does not exist in that module. Actual audio transcription exists in:
- `core.utils.multimodal_processor.transcribe_voice()` — async, uses faster-whisper
- `tools.voice_engine.transcribe_voice()` — async, uses faster-whisper with prewarmed model

**Impact**: Video analysis handler (`handle_video`) will raise `ImportError` or `AttributeError` at runtime when attempting to transcribe audio. The video keyframe extraction and image analysis will still work, but audio transcript will silently fail.

**Fix required**: Either implement `understand_audio()` in `tools/minimax_media.py` (delegating to `core.utils.multimodal_processor.transcribe_voice`), or change the import in both files to use the correct function.

---

## 3-Agent Debate Summary

| Page | Advocate | Skeptic | Judge | Decision |
|------|----------|---------|-------|----------|
| voice-pipeline | 9 | 6 | WRITE 9 | Approved |
| media-processing-guide | 8 | 6 | WRITE 8 | Approved |
| tts-setup | 7 | 6 | WRITE 7 | Approved |

All 3 pages approved — 0 rejected.

---

## Research Questions Answered

1. **What voice transcription pipeline exists?**
   - `handlers/voice.py` uses: OpenAI Whisper → Groq API (whisper-large-v3) → openai-whisper CPU
   - `core/utils/multimodal_processor.py` uses: faster-whisper GPU → faster-whisper CPU → openai-whisper
   - Two separate pipelines with different priorities

2. **What TTS options exist?**
   - Kokoro-ONNX (local, WAV, `af_sarah` voice, requires manual model download)
   - Edge-tts (cloud, MP3, many voices)
   - MiniMax MCP TTS (API quota, 3 voices, MP3)

3. **How does image generation work?**
   - MiniMax `TokenPlan_image_generation` via MCP server
   - `/imagine` command with aspect ratio support
   - PNG saved to temp file, sent as document

4. **What file types are supported for processing?**
   - Direct handlers: OGG, MP3/WAV/M4A (audio), JPEG/PNG/WebP (photo), MP4 (video)
   - Document pipeline (tools/documents.py): PDF, DOCX, XLSX, CSV, PPTX, EPUB, TXT, images (via OCR)

5. **How are voice notes transcribed?**
   - `handlers/voice.py:_transcribe()` — no language auto-detection for OpenAI path (hardcoded "id")
   - Groq and faster-whisper use auto-detection

6. **What timeout exists for long audio?**
   - Groq API: 30s timeout (httpx.AsyncClient)
   - No timeout on faster-whisper GPU path
   - No chunking for long files

7. **How is temp storage managed?**
   - All handlers use `tempfile.NamedTemporaryFile(delete=False)` + explicit `os.unlink()` in finally
   - No cleanup on abrupt termination

8. **What happens with corrupted media files?**
   - Generic try/except → user sees "Error: {exc[:200]}"
   - Empty transcription → "Could not transcribe audio"

---

*Cycle 13 complete — 3 pages written, 1 critical bug discovered, 0 rejected*
