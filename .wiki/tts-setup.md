---
title: Tts Setup
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- tts-setup.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Two TTS backends — Kokoro-ONNX (local, high-quality) and edge-tts (cloud
  fallback) — with 3 MiniMax voices, speed control, and WAV/MP3 output formats.
wikilinks: []
confidence: medium
source: research
---

# TTS Setup

## ONE-LINE SUMMARY
Two TTS backends — Kokoro-ONNX (local, high-quality) and edge-tts (cloud fallback) — with 3 MiniMax voices, speed control, and WAV/MP3 output formats.

## FACTS
- **Primary TTS (handlers/voice.py)**: `core.utils.multimodal_processor.text_to_speech()`
  - Tier 1: Kokoro-ONNX local synthesis (WAV output)
  - Tier 2: Microsoft edge-tts (MP3 output, cloud fallback)
  - Kokoro voice: `af_sarah` (high-quality English female voice)
  - Kokoro model: `models/kokoro-v0_19.onnx` + `models/voices.bin`
  - Kokoro path resolution: `Path(__file__).parent.parent.parent / "models" / ...`
- **Secondary TTS (handlers/media_tools.py)**: `tools.minimax_media.generate_speech()`
  - MiniMax `TokenPlan_speech_generation` via MCP server
  - 3 voices: `English_expressive_narrator`, `male-qn-qingse`, `female-shaonv`
  - Speed: 0.5–2.0 (default 1.0)
  - Output: MP3 downloaded from URL or decoded from base64
- **Edge TTS fallback voice**: `en-US-AriaNeural` (configurable via `TTS_VOICE` constant)
- **Voice reply mode**: `/voice_on` enables TTS reply after LLM response; `/voice_off` disables
- **TTS failure handling**: Silently caught with `logger.debug` — user only sees text reply
- **Chunked responses**: LLM output chunked at 4000 chars before TTS — each chunk sent separately
- **No voice cloning** currently implemented
- **Kokoro-ONNX not installed** by default — requires manual model download to `models/` directory

## LEGION BEHAVIOR RULES
1. TTS is best-effort — if it fails, always fall back to text-only (never block on TTS)
2. Kokoro-ONNX takes priority — higher quality, no API cost, runs locally
3. Edge-tts used only when Kokoro files missing or Kokoro fails
4. MiniMax TTS requires `LEGION_MCP_MINIMAX_SERVER` env var configured
5. Voice reply mode state persisted in KV store (`voice_reply_enabled` key)
6. When voice mode is ON, both text AND voice reply are sent
7. TTS audio files cleaned up after sending — never left in temp directory
8. Speed parameter validated: must be 0.5–2.0, otherwise error returned

## EXAMPLES
Bashara: `/voice_on` → voice reply enabled → sends voice note → gets text + audio reply
Bashara: `/speak The meeting starts at 3 PM` → MiniMax TTS → MP3 voice message sent
Bashara: `/tts Hello world speed=0.8` → speed 0.8 applied → slower speech output
Bashara: sends voice note with TTS enabled but Kokoro not installed → edge-tts used → MP3 reply
Bashara: `/speak` with invalid voice_id → error returned before any API call

## TTS BACKEND COMPARISON

| Feature | Kokoro-ONNX | Edge-TTS | MiniMax MCP |
|---------|-------------|----------|-------------|
| Quality | High (neural) | High ( neural) | High |
| Latency | Low (local) | Medium (network) | Medium |
| Cost | Free (GPU) | Free (Microsoft) | API quota |
| Voices | 1 built-in | Many | 3 |
| Languages | English+ | Many | English+Mandarin |
| Output | WAV | MP3 | MP3 |
| Setup | Manual model dl | pip install | MCP server |

## VOICE CLONING POTENTIAL
- Kokoro-ONNX supports custom voice files via `voices.bin` — voice cloning possible with audio samples
- Edge-tts does NOT support voice cloning
- MiniMax TTS does NOT support voice cloning (fixed voice roster)
- Future: could train custom Kokoro voice from 30s sample → ~1hr training

## ANTI-PATTERNS
1. TTS failure silently ignored — user never knows their audio reply failed to generate
2. Kokoro model files not in repo — requires manual download from external source
3. MiniMax TTS and multimodal_processor TTS are separate code paths — inconsistent behavior
4. No rate limiting on TTS — user could spam `/speak` with 10-minute texts
5. No streaming TTS — entire text synthesized before sending

## DEBATE RECORD
Advocate: 7 | Skeptic: 6 | Judge: WRITE 7
Skeptic concerns: two separate TTS code paths (Kokoro vs MiniMax MCP), silent TTS failures, Kokoro manual setup. All valid — page accurately documents both paths and flags silent failures.
