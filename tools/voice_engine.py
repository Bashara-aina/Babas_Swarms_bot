"""
Kokoro TTS + faster-whisper STT voice pipeline — Phase 7.
Voice note in → transcribe → LLM → Kokoro TTS voice note out.
Runs fully on RTX 3060 (CUDA). Falls back gracefully if GPU unavailable.
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_bella")
KOKORO_SPEED = float(os.getenv("KOKORO_SPEED", "1.0"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")

_whisper_model = None
_kokoro_pipeline = None


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel(
                WHISPER_MODEL, device=WHISPER_DEVICE, compute_type="float16"
            )
            logger.info("faster-whisper loaded: %s on %s", WHISPER_MODEL, WHISPER_DEVICE)
        except Exception as e:
            logger.warning("faster-whisper load failed (%s), trying CPU", e)
            try:
                from faster_whisper import WhisperModel
                _whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            except Exception as e2:
                logger.warning("faster-whisper CPU also failed: %s", e2)
    return _whisper_model


def _load_kokoro():
    global _kokoro_pipeline
    if _kokoro_pipeline is None:
        try:
            from kokoro import KPipeline
            _kokoro_pipeline = KPipeline(lang_code="a")
            logger.info("Kokoro TTS pipeline loaded")
        except Exception as e:
            logger.warning("Kokoro TTS load failed: %s", e)
    return _kokoro_pipeline


async def transcribe_voice(audio_bytes: bytes, file_ext: str = "ogg") -> str:
    """Transcribe voice note bytes → text using faster-whisper."""
    model = _load_whisper()
    if model is None:
        return ""
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        segments, info = await asyncio.to_thread(
            model.transcribe, tmp_path, beam_size=5
        )
        text = " ".join(seg.text for seg in segments).strip()
        logger.info("Transcribed %.1fs audio → %d chars", info.duration, len(text))
        return text
    except Exception as e:
        logger.warning("transcribe_voice failed: %s", e)
        return ""
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


async def synthesize_speech(text: str, voice: str | None = None) -> bytes | None:
    """Synthesize text → WAV bytes using Kokoro TTS."""
    pipeline = _load_kokoro()
    if pipeline is None:
        return None
    try:
        import numpy as np
        import soundfile as sf

        chosen_voice = voice or KOKORO_VOICE

        def _synth():
            audio_chunks = []
            for _, _, audio in pipeline(
                text, voice=chosen_voice, speed=KOKORO_SPEED, split_pattern=r"\n+"
            ):
                audio_chunks.append(audio)
            return np.concatenate(audio_chunks) if audio_chunks else np.array([])

        audio_data = await asyncio.to_thread(_synth)
        if audio_data.size == 0:
            return None
        buf = io.BytesIO()
        sf.write(buf, audio_data, 24000, format="WAV")
        return buf.getvalue()
    except Exception as e:
        logger.warning("synthesize_speech failed: %s", e)
        return None


async def prewarm() -> None:
    """Pre-load both models at startup so first request is fast."""
    try:
        await asyncio.to_thread(_load_whisper)
        await asyncio.to_thread(_load_kokoro)
        logger.info("✅ Voice engine prewarmed (Kokoro TTS + faster-whisper)")
    except Exception as e:
        logger.warning("Voice prewarm failed (non-fatal): %s", e)
