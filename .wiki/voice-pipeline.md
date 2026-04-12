---
title: voice-pipeline
domain: voice-media
impact_score: 9
last_updated: 2026-04-12
injects_into: handlers
tokens_estimated: 620
---

# Voice Pipeline

## ONE-LINE SUMMARY
Voice note transcription pipeline — 3-tier Whisper backend (GPU→API→CPU), language detection, temp file cleanup, optional TTS reply.

## FACTS
- **Three-tier transcription backend** (priority order):
  1. `faster-whisper` with GPU (`base` model, CUDA float16) — handlers/voice.py
  2. Groq Whisper API (`whisper-large-v3`, 30s timeout) — if `GROQ_API_KEY` set
  3. OpenAI Whisper API (`whisper-1`, hardcoded `language="id"`) — if `OPENAI_API_KEY` set
  4. Local `openai-whisper` (`base` model, CPU fallback) — last resort
- **File formats handled**: OGG (voice notes via `F.voice`), MP3/WAV/M4A (audio uploads via `F.audio`)
- **Temp storage**: `tempfile.NamedTemporaryFile(delete=False)` — files unlinked explicitly in `finally` block
- **Corrupted audio handling**: Empty transcription result → user message "Could not transcribe audio — please try again"
- **Language**: Hardcoded `language="id"` for OpenAI Whisper; Groq and faster-whisper use auto-detection
- **Long audio**: Groq API has 30s timeout; no explicit chunking for long files — entire file sent at once
- **Optional TTS reply**: After transcription, LLM generates response; `text_to_speech()` attempts Kokoro→edge-tts fallback

## LEGION BEHAVIOR RULES
1. Always download voice to temp file before transcription — never pipe directly
2. Delete temp file in `finally` block — always, even on exception
3. Log transcription result (first 80 chars) at INFO level for debugging
4. If transcription returns empty/whitespace → tell user "Could not transcribe audio"
5. Voice reply mode is toggleable via `/voice_on` / `/voice_off` — stored in KV store
6. When voice reply is OFF, transcribed text goes to same chat pipeline as text messages
7. When voice reply is ON, LLM response is sent as both text AND voice (via `answer_voice`)
8. Audio transcription (F.audio) uses identical pipeline to voice notes

## EXAMPLES
Bashara: sends 15-second voice note in Indonesian → transcribed via faster-whisper GPU → LLM responds → TTS reply
Bashara: uploads MP3 file → same pipeline, different temp suffix (.mp3)
Bashara: `/voice_off` → voice notes are transcribed but only text reply is sent
Bashara: sends corrupted/encrypted audio → empty transcription → user sees error message

## ANTI-PATTERNS
1. No language auto-detection for OpenAI Whisper — hardcoded `"id"` causes poor quality for non-Indonesian audio
2. No timeout handling for faster-whisper — GPU transcription of very long audio can hang
3. Groq API has 30s timeout but no retry logic — if timeout is hit, entire transcription fails
4. No file size limit for audio uploads — very large files could cause memory issues
5. TTS failure is silently swallowed (`logger.debug`) — user never knows TTS failed

## GAPS
- No streaming/chunked transcription for audio >10 minutes
- No speaker diarization (who said what)
- No punctuation model post-processing
- Voice transcript search (`/vcsearch`) is stub-only — not implemented
- No voice activity detection (VAD) preprocessing
- No file size limit for audio uploads — very large files could cause memory issues
- `language="id"` hardcoded for OpenAI Whisper — should use auto-detection

## DEBATE RECORD
Advocate: 9 | Skeptic: 6 | Judge: WRITE 9
Skeptic concerns: hardcoded Indonesian language, no GPU timeout, no Groq retry, no audio size limit. All valid but do not affect page accuracy — page documents codebase as-written.
