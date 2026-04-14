---
title: Upgrade Log V7
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- changelogs
created: '2026-04-14'
updated: '2026-04-14'
summary: 'This commit completes the 10-repo upgrade roadmap:'
wikilinks: []
confidence: medium
source: research
---
# Legion v7 Upgrade Log

## Date: 2026-04-07

## What Was Implemented

This commit completes the 10-repo upgrade roadmap:

### Phase 3 — Letta Stateful Personality (`tools/letta_personality.py`)
- Persona state persisted to `~/.legion/persona_state.json`
- OCEAN traits, emotion (VAD model), trust/familiarity tracking
- `build_persona_system_block()` injects into every LLM call
- `enforce_persona()` strips forbidden phrases from responses
- `update_emotion()` shifts mood per interaction and persists

### Phase 5 — ElizaOS Character Card (`tools/elizaos_character.py` + `config/legion_character.json`)
- JSON character card drives all system prompts consistently
- Works across all LLMs (Groq, Gemini, Ollama) — same voice everywhere
- `build_character_system_prompt()` merges bio, lore, knowledge, style
- Character file editable without code changes

### Phase 6 — AgentOps Observability (`tools/agentops_client.py`)
- 2-line init, full session replay at agentops.ai
- Cost tracking, time-travel debugging, action recording
- Non-fatal if `AGENTOPS_API_KEY` not set

### Phase 7 — Kokoro TTS + faster-whisper (`tools/voice_engine.py` + `handlers/voice_handler.py`)
- Voice note in → faster-whisper transcribe → LLM → Kokoro TTS out
- Runs on RTX 3060 (CUDA float16) with CPU fallback
- Commands: `/voice_on`, `/voice_off`, `/voice_status`
- Sub-100ms latency target on local GPU

### Phase 9 — mneme Session Continuity (`tools/mneme_session.py` + `core/session/`)
- Three memory layers: working (active task) / episodic (history) / semantic (facts)
- Survives restarts — Legion knows what it was doing before shutdown
- Commands: `/task`, `/task_done`, `/sessions`, `/semantic_set`, `/semantic_get`
- `build_session_resume_block()` injected at startup

### Phase 10 — Emotion Modulator (`tools/emotion_modulator.py`)
- Strips all corporate filler phrases from every response
- Applies mood-driven word substitutions (excited/frustrated/content/melancholy)
- `modulate_with_persona()` reads live emotion state
- Must be called in `llm_client.py` as final post-processing step

### Mind-Bus Routing (`tools/mindbus_router.py`)
- Context-aware routing using Adaptive Context Compression (ACC)
- Compresses conversation history before routing decision
- LLM routing fallback reads full conversation state, not single message
- Integrates mem0 memory retrieval into routing

### Persona Handler (`handlers/persona_handler.py`)
- Commands: `/persona`, `/mood`, `/persona_reset`, `/persona_note`

### Session Handler (`handlers/session_handler.py`)
- Commands: `/task`, `/task_done`, `/sessions`, `/semantic_set`, `/semantic_get`

## Integration Steps Required

After pulling, add to `main.py` `on_startup()`:

```python
# AgentOps
try:
    from tools.agentops_client import init_agentops
    init_agentops()
except Exception as e:
    logger.warning("AgentOps init failed: %s", e)

# ElizaOS character
try:
    from tools.elizaos_character import ensure_character_file
    ensure_character_file()
except Exception as e:
    logger.warning("Character card init failed: %s", e)

# Voice engine prewarm
try:
    from tools.voice_engine import prewarm
    await prewarm()
except Exception as e:
    logger.warning("Voice prewarm failed: %s", e)

# Session resume
try:
    from core.session import on_startup_resume
    resume_block = await on_startup_resume()
    if resume_block:
        logger.info("Session resumed:\n%s", resume_block)
except Exception as e:
    logger.warning("Session resume failed: %s", e)
```

Add to `llm_client.py` `chat()` function:

```python
# Inject persona block
from tools.letta_personality import build_persona_system_block
system_prompt = build_persona_system_block() + "\n\n" + system_prompt

# After response, modulate
from tools.emotion_modulator import modulate_with_persona
result = modulate_with_persona(result)

# Track emotion shift
from tools.letta_personality import update_emotion
update_emotion(valence_delta=0.02, arousal_delta=-0.01)
```

Add to `handlers/__init__.py`:
```python
from handlers.voice_handler import router as voice_router
from handlers.persona_handler import router as persona_router
from handlers.session_handler import router as session_router
```

## New ENV Vars (add to .env.example)
```
AGENTOPS_API_KEY=          # Optional — agentops.ai session replay
KOKORO_VOICE=af_bella      # Kokoro TTS voice ID
KOKORO_SPEED=1.0           # TTS speed multiplier
WHISPER_MODEL=base         # faster-whisper model size
WHISPER_DEVICE=cuda        # cuda or cpu
ROUTING_MODEL=groq/llama-3.3-70b-versatile  # Model for MindBus routing
```

## New Dependencies
```
pip install kokoro soundfile faster-whisper agentops
```
