"""Voice Pipeline for Nihongo Mode.
STT: OpenAI Whisper (transcription of Bashara's voice notes)
TTS: VoiceVox (Japanese neural TTS) → fallback: gTTS
Completely isolated from any future Legion voice system.
"""

import io
import logging
import os
import tempfile

logger = logging.getLogger("nihongo.voice")

VOICEVOX_SPEAKERS = {
    "zundamon": 3,
    "metan": 2,
    "tsumugi": 8,
    "ritsu": 9,
}
DEFAULT_SPEAKER = "metan"
VOICEVOX_HOST = os.getenv("VOICEVOX_HOST", "http://localhost:50021")


async def transcribe_voice_note(audio_bytes: bytes, language: str = "ja", use_api: bool = True) -> str:
    if use_api:
        return await _transcribe_whisper_api(audio_bytes, language)
    else:
        return await _transcribe_whisper_local(audio_bytes, language)


async def _transcribe_whisper_api(audio_bytes: bytes, language: str) -> str:
    try:
        import openai

        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, language=language, response_format="text"
            )

        os.unlink(tmp_path)
        return transcript.strip()

    except Exception as e:
        logger.error(f"Whisper API error: {e}")
        return "[Transcription failed]"


async def _transcribe_whisper_local(audio_bytes: bytes, language: str) -> str:
    try:
        import importlib.util

        _NUMPY_AVAILABLE = importlib.util.find_spec("numpy") is not None
        _SOUNDFILE_AVAILABLE = importlib.util.find_spec("soundfile") is not None
        import whisper

        model = whisper.load_model("base")
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        result = model.transcribe(tmp_path, language=language)
        os.unlink(tmp_path)
        return result["text"].strip()

    except ImportError:
        logger.error("whisper not installed. Run: pip install openai-whisper")
        return "[Local Whisper not available]"
    except Exception as e:
        logger.error(f"Local Whisper error: {e}")
        return "[Transcription failed]"


async def text_to_speech_japanese(
    text: str, speaker: str = DEFAULT_SPEAKER, slow_speech: bool = True, use_voicevox: bool = True
) -> bytes | None:
    from skills.nihongo.furigana import extract_japanese_only

    jp_text = extract_japanese_only(text)
    if not jp_text.strip():
        return None

    if use_voicevox:
        audio = await _tts_voicevox(jp_text, speaker, slow_speech)
        if audio:
            return audio
        logger.warning("VoiceVox unavailable, falling back to gTTS")

    return await _tts_gtts_fallback(jp_text, slow_speech)


async def _tts_voicevox(text: str, speaker: str, slow: bool) -> bytes | None:
    try:
        import httpx

        speaker_id = VOICEVOX_SPEAKERS.get(speaker, 2)

        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{VOICEVOX_HOST}/audio_query", params={"text": text, "speaker": speaker_id})
            r.raise_for_status()
            query = r.json()

            if slow:
                query["speedScale"] = 0.75
                query["pauseLength"] = 1.5
                query["pauseLengthScale"] = 1.5

            r2 = await client.post(
                f"{VOICEVOX_HOST}/synthesis",
                params={"speaker": speaker_id},
                json=query,
                headers={"Content-Type": "application/json"},
            )
            r2.raise_for_status()
            return r2.content

    except Exception as e:
        logger.warning(f"VoiceVox error: {e}")
        return None


async def _tts_gtts_fallback(text: str, slow: bool) -> bytes | None:
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="ja", slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        logger.error(f"gTTS error: {e}")
        return None
