# /home/newadmin/swarm-bot/multimodal_processor.py
"""Unified processor for voice messages, documents, and images.

Providers:
- Voice → faster-whisper (GPU, CUDA) → Groq Whisper API → openai-whisper (CPU fallback)
- PDF   → PyPDF2
- DOCX  → python-docx
- TTS   → kokoro-onnx (local, high-quality) → edge-tts (cloud fallback)
- Image → Ollama Gemma3:12b vision (local)
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import tempfile
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

VISION_MODEL = "llava:13b"
OLLAMA_BASE = "http://localhost:11434"
TTS_VOICE = "en-US-AriaNeural"   # Change to "ja-JP-NanamiNeural" for Japanese
MAX_CONTEXT_CHARS = 8_000        # Max chars stored from a document into thread context


# ── Voice Transcription ────────────────────────────────────────────────────────

def _transcribe_sync(audio_bytes: bytes, extension: str = ".ogg") -> str:
    """Transcribe audio. Priority: faster-whisper (GPU) → openai-whisper (CPU).

    Args:
        audio_bytes: Raw audio file bytes.
        extension: File extension to save temp file as (e.g. '.ogg', '.mp3').

    Returns:
        Transcribed text string.
    """
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        # ── Tier 1: faster-whisper with GPU ──────────────────────────────────
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cuda", compute_type="float16")
            segments, _ = model.transcribe(tmp_path)
            text = " ".join(seg.text for seg in segments).strip()
            logger.info("Transcribed %d chars via faster-whisper (GPU)", len(text))
            return text
        except Exception as fw_err:
            logger.debug("faster-whisper failed (%s), trying CPU mode", fw_err)
            try:
                from faster_whisper import WhisperModel
                model = WhisperModel("base", device="cpu", compute_type="int8")
                segments, _ = model.transcribe(tmp_path)
                text = " ".join(seg.text for seg in segments).strip()
                logger.info("Transcribed %d chars via faster-whisper (CPU)", len(text))
                return text
            except Exception as fw_cpu_err:
                logger.debug("faster-whisper CPU also failed (%s), falling back to openai-whisper", fw_cpu_err)

        # ── Tier 2: openai-whisper (original fallback) ───────────────────────
        try:
            import whisper  # type: ignore[reportMissingImports]
            model_ow = whisper.load_model("base")
            result = model_ow.transcribe(tmp_path)
            text = str(result["text"]).strip()
            logger.info("Transcribed %d chars via openai-whisper", len(text))
            return text
        except ImportError:
            raise RuntimeError(
                "No Whisper backend available. Install faster-whisper or openai-whisper."
            )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def transcribe_voice(audio_bytes: bytes, extension: str = ".ogg") -> str:
    """Async: transcribe a voice message to text.

    Args:
        audio_bytes: Raw audio bytes (Telegram sends OGG/Opus).
        extension: Audio format extension.

    Returns:
        Transcribed text string.
    """
    return await asyncio.to_thread(_transcribe_sync, audio_bytes, extension)


# ── Text-to-Speech ─────────────────────────────────────────────────────────────

_KOKORO_VOICE = "af_sarah"   # High-quality English voice; change for other languages
_KOKORO_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "kokoro-v0_19.onnx"
_KOKORO_VOICES_PATH = Path(__file__).parent.parent.parent / "models" / "voices.bin"


def _tts_kokoro_sync(text: str) -> bytes:
    """Synthesise speech with kokoro-onnx (sync). Returns WAV bytes."""
    import wave

    import numpy as np
    from kokoro_onnx import Kokoro

    kokoro = Kokoro(str(_KOKORO_MODEL_PATH), str(_KOKORO_VOICES_PATH))
    samples, sample_rate = kokoro.create(text, _KOKORO_VOICE)

    # Encode raw float32 samples → WAV bytes
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


async def text_to_speech(text: str, voice: str = TTS_VOICE) -> bytes:
    """Convert text to audio bytes.

    Priority:
    1. kokoro-onnx  — local high-quality ONNX TTS (returns WAV)
    2. edge-tts     — Microsoft cloud neural TTS (returns MP3, fallback)

    Args:
        text: Text to synthesize.
        voice: Edge-TTS voice name used only for the fallback path.

    Returns:
        Audio bytes (WAV from kokoro, MP3 from edge-tts).
    """
    # ── Tier 1: kokoro-onnx ───────────────────────────────────────────────────
    if _KOKORO_MODEL_PATH.exists() and _KOKORO_VOICES_PATH.exists():
        try:
            audio_bytes = await asyncio.to_thread(_tts_kokoro_sync, text)
            logger.info("TTS: kokoro-onnx generated %d bytes for %d chars", len(audio_bytes), len(text))
            return audio_bytes
        except Exception as ko_err:
            logger.debug("kokoro-onnx TTS failed (%s), falling back to edge-tts", ko_err)
    else:
        logger.debug("kokoro-onnx model files not found, using edge-tts")

    # ── Tier 2: edge-tts ─────────────────────────────────────────────────────
    try:
        import edge_tts
    except ImportError:
        raise RuntimeError("edge-tts not installed — run: pip install edge-tts")

    communicate = edge_tts.Communicate(text, voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])  # type: ignore[reportTypedDictNotRequiredAccess]
    audio_bytes = buf.getvalue()
    logger.info("TTS: edge-tts generated %d bytes for %d chars", len(audio_bytes), len(text))
    return audio_bytes


# ── PDF Processing ─────────────────────────────────────────────────────────────

def _extract_pdf_sync(pdf_bytes: bytes) -> str:
    """Extract text from a PDF (sync).

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        Extracted text, capped at MAX_CONTEXT_CHARS.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore[reportMissingImports]
        except ImportError:
            raise RuntimeError("pypdf not installed — run: pip install pypdf")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages: list[str] = []

    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            pages.append(f"--- Page {i + 1} ---\n{text.strip()}")
        except Exception as exc:
            logger.warning("Failed to extract page %d: %s", i + 1, exc)

    full_text = "\n\n".join(pages)

    if len(full_text) > MAX_CONTEXT_CHARS:
        logger.info("PDF text truncated from %d to %d chars", len(full_text), MAX_CONTEXT_CHARS)
        full_text = full_text[:MAX_CONTEXT_CHARS] + f"\n\n[... truncated at {MAX_CONTEXT_CHARS} chars]"

    logger.info("Extracted %d chars from PDF (%d pages)", len(full_text), len(reader.pages))
    return full_text


async def extract_pdf(pdf_bytes: bytes) -> str:
    """Async: extract text from a PDF document.

    Args:
        pdf_bytes: Raw PDF bytes.

    Returns:
        Extracted text string.
    """
    return await asyncio.to_thread(_extract_pdf_sync, pdf_bytes)


# ── DOCX Processing ────────────────────────────────────────────────────────────

def _extract_docx_sync(docx_bytes: bytes) -> str:
    """Extract text from a DOCX file (sync).

    Args:
        docx_bytes: Raw DOCX bytes.

    Returns:
        Extracted text, capped at MAX_CONTEXT_CHARS.
    """
    try:
        import docx
    except ImportError:
        raise RuntimeError("python-docx not installed — run: pip install python-docx")

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f.write(docx_bytes)
        tmp_path = f.name

    try:
        doc = docx.Document(tmp_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)

        if len(full_text) > MAX_CONTEXT_CHARS:
            full_text = full_text[:MAX_CONTEXT_CHARS] + "\n\n[... truncated]"

        logger.info("Extracted %d chars from DOCX", len(full_text))
        return full_text
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def extract_docx(docx_bytes: bytes) -> str:
    """Async: extract text from a DOCX document.

    Args:
        docx_bytes: Raw DOCX bytes.

    Returns:
        Extracted text string.
    """
    return await asyncio.to_thread(_extract_docx_sync, docx_bytes)


# ── Image Analysis ─────────────────────────────────────────────────────────────

def _analyze_image_sync(image_bytes: bytes, question: str = "Describe this image in detail.") -> str:
    """Analyze an image using Ollama Gemma3 vision (sync).

    Args:
        image_bytes: Raw image bytes (PNG, JPEG, etc.).
        question: What to ask about the image.

    Returns:
        Vision model's response string.
    """
    b64 = base64.b64encode(image_bytes).decode()

    payload = {
        "model": VISION_MODEL,
        "prompt": question,
        "images": [b64],
        "stream": False,
    }

    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        answer: str = resp.json().get("response", "No response from vision model")
        logger.info("Image analysis: %d chars", len(answer))
        return answer
    except requests.RequestException as exc:
        logger.exception("Image analysis failed: %s", exc)
        return f"Vision model error: {exc}"


async def analyze_image(image_bytes: bytes, question: str = "Describe this image in detail.") -> str:
    """Async: analyze an image with the vision model.

    Args:
        image_bytes: Raw image bytes.
        question: Question to ask about the image.

    Returns:
        Vision model answer.
    """
    return await asyncio.to_thread(_analyze_image_sync, image_bytes, question)


# ── Dispatcher ─────────────────────────────────────────────────────────────────

SUPPORTED_DOCUMENT_TYPES = {
    "application/pdf": extract_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": extract_docx,
    "text/plain": None,   # Handled inline
}


async def process_document(
    file_bytes: bytes,
    mime_type: str,
    filename: str = "",
) -> tuple[str, str]:
    """Dispatch document processing by MIME type.

    Args:
        file_bytes: Raw file bytes.
        mime_type: MIME type string from Telegram.
        filename: Original filename (for context).

    Returns:
        Tuple of (extracted_text, summary_label).
    """
    if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
        text = await extract_pdf(file_bytes)
        return text, "PDF"

    if mime_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ) or filename.lower().endswith(".docx"):
        text = await extract_docx(file_bytes)
        return text, "DOCX"

    if mime_type.startswith("text/") or filename.lower().endswith(".txt"):
        text = file_bytes.decode("utf-8", errors="replace")
        if len(text) > MAX_CONTEXT_CHARS:
            text = text[:MAX_CONTEXT_CHARS] + "\n[truncated]"
        return text, "TXT"

    return "", f"Unsupported file type: {mime_type}"
