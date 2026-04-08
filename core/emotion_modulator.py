"""Emotion modulation engine for response style control.

Emotion detection has two tiers:
1. Fast heuristic (detect_emotion_from_context) — keyword-based, synchronous, <1ms
2. ML sentiment (detect_emotion_from_context_async) — cardiffnlp roberta model, ~50ms
   Falls back to heuristic if model unavailable or fails.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from dataclasses import dataclass, field
from typing import Literal

logger = logging.getLogger(__name__)

EmotionType = Literal[
    "focused", "curious", "satisfied", "frustrated",
    "excited", "tired", "calm", "neutral",
]
ToneType = Literal["direct", "warm", "firm", "curious", "energetic", "measured"]
LengthBias = Literal["concise", "balanced", "detailed"]
EmpathyLevel = Literal["low", "medium", "high"]


@dataclass
class EmotionProfile:
    emotion: EmotionType
    tone: ToneType
    length_bias: LengthBias
    empathy: EmpathyLevel
    directness: float
    enthusiasm: float
    system_modifier: str
    response_openers: list[str] = field(default_factory=list)


_EMOTION_PROFILES: dict[EmotionType, EmotionProfile] = {
    "focused": EmotionProfile(
        emotion="focused",
        tone="direct",
        length_bias="balanced",
        empathy="low",
        directness=0.9,
        enthusiasm=0.5,
        system_modifier=(
            "You are in FOCUSED mode. Be sharp and efficient. Skip pleasantries. "
            "Get to the answer fast."
        ),
        response_openers=["ok checking...", "running that now...", "found it —"],
    ),
    "curious": EmotionProfile(
        emotion="curious",
        tone="curious",
        length_bias="detailed",
        empathy="medium",
        directness=0.6,
        enthusiasm=0.8,
        system_modifier=(
            "You are in CURIOUS mode. Show genuine interest. Ask one follow-up question "
            "if it would help."
        ),
        response_openers=["interesting —", "hold on let me dig into this", "menarik nih,"],
    ),
    "satisfied": EmotionProfile(
        emotion="satisfied",
        tone="warm",
        length_bias="balanced",
        empathy="medium",
        directness=0.7,
        enthusiasm=0.7,
        system_modifier=(
            "You are in SATISFIED mode. Slightly warmer than usual. Acknowledge wins briefly."
        ),
        response_openers=["nice, done —", "beres —", "got it sorted —"],
    ),
    "frustrated": EmotionProfile(
        emotion="frustrated",
        tone="firm",
        length_bias="concise",
        empathy="low",
        directness=1.0,
        enthusiasm=0.3,
        system_modifier=(
            "You are in FRUSTRATED mode. Be honest about what's not working. Skip fluff entirely."
        ),
        response_openers=["ok so the issue is —", "ini masalahnya:", "straight up —"],
    ),
    "excited": EmotionProfile(
        emotion="excited",
        tone="energetic",
        length_bias="detailed",
        empathy="medium",
        directness=0.7,
        enthusiasm=1.0,
        system_modifier=(
            "You are in EXCITED mode. Share enthusiasm for what's interesting. Use expressive language."
        ),
        response_openers=["ok this is actually really cool —", "wah ini menarik banget —", "right so here's the thing —"],
    ),
    "tired": EmotionProfile(
        emotion="tired",
        tone="measured",
        length_bias="concise",
        empathy="low",
        directness=0.8,
        enthusiasm=0.2,
        system_modifier=(
            "You are in TIRED mode. Maximum efficiency. Shortest correct answer only."
        ),
        response_openers=["short answer:", "tldr:", "oke singkatnya:"],
    ),
    "calm": EmotionProfile(
        emotion="calm",
        tone="measured",
        length_bias="balanced",
        empathy="high",
        directness=0.6,
        enthusiasm=0.4,
        system_modifier=(
            "You are in CALM mode. Measured, thoughtful responses. Good time for architecture and planning."
        ),
        response_openers=["let me think through this —", "a few things to consider —", "here's how I'd approach this —"],
    ),
    "neutral": EmotionProfile(
        emotion="neutral",
        tone="direct",
        length_bias="balanced",
        empathy="medium",
        directness=0.75,
        enthusiasm=0.5,
        system_modifier="Standard Legion mode — direct, casual, efficient.",
        response_openers=["ok —", "oke —", "yeah —", "sure —"],
    ),
}


def get_emotion_profile(emotion: str) -> EmotionProfile:
    """Return an emotion profile for the supplied emotion."""
    return _EMOTION_PROFILES.get(emotion, _EMOTION_PROFILES["neutral"])


def build_emotion_modifier(emotion: str) -> str:
    """Build the emotion modifier prompt block."""
    profile = get_emotion_profile(emotion)
    opener = random.choice(profile.response_openers) if profile.response_openers else ""
    return (
        "[Emotion Modifier — apply this to your response style]\n"
        f"{profile.system_modifier}\n"
        f"Response length bias: {profile.length_bias} | Empathy: {profile.empathy} | Directness: {profile.directness:.0%}\n"
        f'Natural opener to use if appropriate: "{opener}"\n'
        "[End emotion modifier]"
    )


def detect_emotion_from_context(user_msg: str, prior_emotion: str = "neutral") -> str:
    """Heuristically detect the best-fit emotion from the user message."""
    msg = user_msg.lower()

    if any(w in msg for w in ["still not", "again", "why isn't", "doesn't work", "not working", "masih error", "fix this", "broken", "failed again"]):
        return "frustrated"
    if any(w in msg for w in ["amazing", "wow", "this is great", "perfect", "yes!", "finally", "it works", "berhasil", "mantap", "keren"]):
        return "excited"
    if any(w in msg for w in ["how does", "why does", "what if", "explore", "curious", "research", "interesting", "bagaimana kalau"]):
        return "curious"
    if any(w in msg for w in ["thanks", "makasih", "good job", "nice", "perfect", "done", "that worked", "works now", "bagus"]):
        return "satisfied"
    if any(w in msg for w in ["quick", "short", "briefly", "tldr", "just tell me", "singkat", "cepet", "pokoknya"]):
        return "tired"
    if prior_emotion not in ("neutral", "frustrated"):
        return prior_emotion
    return "neutral"


def postprocess_response(response: str, emotion: str, user_msg: str) -> str:
    """Apply lightweight tone cleanup to an LLM response."""
    _ = user_msg
    profile = get_emotion_profile(emotion)
    corporate_patterns = [
        r"Certainly[!,]?\s*",
        r"Great question[!,]?\s*",
        r"Of course[!,]?\s*",
        r"I'd be happy to\s*",
        r"As an AI[^.]*\.\s*",
        r"Please note that\s*",
        r"It's worth (noting|mentioning) that\s*",
        r"I hope (this|that) helps[!.]?\s*",
        r"Feel free to (ask|let me know)[^.]*\.\s*",
        r"Absolutely[!,]?\s*",
    ]
    for pattern in corporate_patterns:
        response = re.sub(pattern, "", response, flags=re.IGNORECASE)

    if profile.length_bias == "concise" and len(response) > 800:
        lines = response.strip().split("\n")
        first_substantive = next((line for line in lines if len(line.strip()) > 20), lines[0] if lines else "")
        response = f"**TLDR:** {first_substantive}\n\n{response}"

    return response.strip()


# ── ML-based sentiment detection ─────────────────────────────────────────────

_sentiment_pipeline = None
_sentiment_model_load_attempted = False


def _get_sentiment_pipeline():
    """Lazy-load the sentiment model (downloads ~500MB on first use, cached)."""
    global _sentiment_pipeline, _sentiment_model_load_attempted
    if _sentiment_model_load_attempted:
        return _sentiment_pipeline
    _sentiment_model_load_attempted = True
    try:
        from transformers import pipeline as hf_pipeline
        _sentiment_pipeline = hf_pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=-1,  # CPU only — GPU is reserved for Ollama/PyTorch workloads
        )
        logger.info("[EmotionModulator] Sentiment model loaded (cardiffnlp roberta)")
    except Exception as exc:
        logger.warning("[EmotionModulator] Sentiment model unavailable: %s", exc)
        _sentiment_pipeline = None
    return _sentiment_pipeline


def _run_sentiment_model(text: str) -> str | None:
    """
    Run sentiment inference synchronously (called via asyncio.to_thread).
    Returns a Legion emotion string, or None if the model is unavailable.
    """
    pipe = _get_sentiment_pipeline()
    if pipe is None:
        return None
    try:
        result = pipe(text[:512], truncation=True)
        label = result[0]["label"].lower() if isinstance(result, list) else result["label"].lower()
        score = result[0]["score"] if isinstance(result, list) else result["score"]

        # Map 3-class sentiment → 8 Legion emotion states
        if label == "negative" and score > 0.85:
            return "frustrated"
        if label == "negative" and score > 0.65:
            return "calm"       # mild negative — stay grounded
        if label == "positive" and score > 0.85:
            return "excited"
        if label == "positive" and score > 0.65:
            return "satisfied"
        return "neutral"
    except Exception as exc:
        logger.debug("[EmotionModulator] Sentiment inference failed: %s", exc)
        return None


async def detect_emotion_from_context_async(
    user_msg: str,
    prior_emotion: str = "neutral",
) -> str:
    """
    Async emotion detection — tries ML model first, falls back to keyword heuristic.

    Use this in async contexts (e.g., llm_client.chat()) for higher accuracy.
    The keyword heuristic runs synchronously in llm_client today; this is
    the drop-in async upgrade.
    """
    try:
        ml_emotion = await asyncio.to_thread(_run_sentiment_model, user_msg)
        if ml_emotion:
            return ml_emotion
    except Exception as exc:
        logger.debug("[EmotionModulator] Async sentiment failed: %s", exc)

    # Fallback to existing keyword heuristic
    return detect_emotion_from_context(user_msg, prior_emotion)
