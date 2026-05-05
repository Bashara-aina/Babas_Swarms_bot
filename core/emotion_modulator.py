"""Emotion modulation engine for response style control.  # type: ignore[reportOptionalSubscript]

Emotion detection has two tiers:
1. Fast heuristic (detect_emotion_from_context) — keyword-based, synchronous, <1ms  # type: ignore[reportOptionalSubscript]
2. ML sentiment (detect_emotion_from_context_async) — cardiffnlp roberta model, ~50ms  # type: ignore[reportOptionalSubscript]
   Falls back to heuristic if model unavailable or fails.  # type: ignore[reportOptionalSubscript]
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from dataclasses import dataclass, field  # type: ignore[reportOptionalSubscript]
from typing import Literal

logger = logging.getLogger(__name__)  # type: ignore[reportOptionalSubscript]

EmotionType = Literal[  # type: ignore[reportOptionalSubscript]
    "focused", "curious", "satisfied", "frustrated",  # type: ignore[reportOptionalSubscript]
    "excited", "tired", "calm", "neutral",  # type: ignore[reportOptionalSubscript]
]
ToneType = Literal["direct", "warm", "firm", "curious", "energetic", "measured"]  # type: ignore[reportOptionalSubscript]
LengthBias = Literal["concise", "balanced", "detailed"]  # type: ignore[reportOptionalSubscript]
EmpathyLevel = Literal["low", "medium", "high"]  # type: ignore[reportOptionalSubscript]


@dataclass
class EmotionProfile:
    emotion: EmotionType
    tone: ToneType
    length_bias: LengthBias
    empathy: EmpathyLevel
    directness: float
    enthusiasm: float
    system_modifier: str
    response_openers: list[str] = field(default_factory=list)  # type: ignore[reportOptionalSubscript]


_EMOTION_PROFILES: dict[EmotionType, EmotionProfile] = {  # type: ignore[reportOptionalSubscript]
    "focused": EmotionProfile(  # type: ignore[reportOptionalSubscript]
        emotion="focused",  # type: ignore[reportOptionalSubscript]
        tone="direct",  # type: ignore[reportOptionalSubscript]
        length_bias="balanced",  # type: ignore[reportOptionalSubscript]
        empathy="low",  # type: ignore[reportOptionalSubscript]
        directness=0.9,  # type: ignore[reportOptionalSubscript]
        enthusiasm=0.5,  # type: ignore[reportOptionalSubscript]
        system_modifier=(  # type: ignore[reportOptionalSubscript]
            "You are in FOCUSED mode. Be sharp and efficient. Skip pleasantries. "  # type: ignore[reportOptionalSubscript]
            "Get to the answer fast."  # type: ignore[reportOptionalSubscript]
        ),  # type: ignore[reportOptionalSubscript]
        response_openers=["ok checking...", "running that now...", "found it —"],  # type: ignore[reportOptionalSubscript]
    ),  # type: ignore[reportOptionalSubscript]
    "curious": EmotionProfile(  # type: ignore[reportOptionalSubscript]
        emotion="curious",  # type: ignore[reportOptionalSubscript]
        tone="curious",  # type: ignore[reportOptionalSubscript]
        length_bias="detailed",  # type: ignore[reportOptionalSubscript]
        empathy="medium",  # type: ignore[reportOptionalSubscript]
        directness=0.6,  # type: ignore[reportOptionalSubscript]
        enthusiasm=0.8,  # type: ignore[reportOptionalSubscript]
        system_modifier=(  # type: ignore[reportOptionalSubscript]
            "You are in CURIOUS mode. Show genuine interest. Ask one follow-up question "  # type: ignore[reportOptionalSubscript]
            "if it would help."  # type: ignore[reportOptionalSubscript]
        ),  # type: ignore[reportOptionalSubscript]
        response_openers=["interesting —", "hold on let me dig into this", "menarik nih,"],  # type: ignore[reportOptionalSubscript]
    ),  # type: ignore[reportOptionalSubscript]
    "satisfied": EmotionProfile(  # type: ignore[reportOptionalSubscript]
        emotion="satisfied",  # type: ignore[reportOptionalSubscript]
        tone="warm",  # type: ignore[reportOptionalSubscript]
        length_bias="balanced",  # type: ignore[reportOptionalSubscript]
        empathy="medium",  # type: ignore[reportOptionalSubscript]
        directness=0.7,  # type: ignore[reportOptionalSubscript]
        enthusiasm=0.7,  # type: ignore[reportOptionalSubscript]
        system_modifier=(  # type: ignore[reportOptionalSubscript]
            "You are in SATISFIED mode. Slightly warmer than usual. Acknowledge wins briefly."  # type: ignore[reportOptionalSubscript]
        ),  # type: ignore[reportOptionalSubscript]
        response_openers=["nice, done —", "beres —", "got it sorted —"],  # type: ignore[reportOptionalSubscript]
    ),  # type: ignore[reportOptionalSubscript]
    "frustrated": EmotionProfile(  # type: ignore[reportOptionalSubscript]
        emotion="frustrated",  # type: ignore[reportOptionalSubscript]
        tone="firm",  # type: ignore[reportOptionalSubscript]
        length_bias="concise",  # type: ignore[reportOptionalSubscript]
        empathy="low",  # type: ignore[reportOptionalSubscript]
        directness=1.0,  # type: ignore[reportOptionalSubscript]
        enthusiasm=0.3,  # type: ignore[reportOptionalSubscript]
        system_modifier=(  # type: ignore[reportOptionalSubscript]
            "You are in FRUSTRATED mode. Be honest about what's not working. Skip fluff entirely."  # type: ignore[reportOptionalSubscript]
        ),  # type: ignore[reportOptionalSubscript]
        response_openers=["ok so the issue is —", "ini masalahnya:", "straight up —"],  # type: ignore[reportOptionalSubscript]
    ),  # type: ignore[reportOptionalSubscript]
    "excited": EmotionProfile(  # type: ignore[reportOptionalSubscript]
        emotion="excited",  # type: ignore[reportOptionalSubscript]
        tone="energetic",  # type: ignore[reportOptionalSubscript]
        length_bias="detailed",  # type: ignore[reportOptionalSubscript]
        empathy="medium",  # type: ignore[reportOptionalSubscript]
        directness=0.7,  # type: ignore[reportOptionalSubscript]
        enthusiasm=1.0,  # type: ignore[reportOptionalSubscript]
        system_modifier=(  # type: ignore[reportOptionalSubscript]
            "You are in EXCITED mode. Share enthusiasm for what's interesting. Use expressive language."  # type: ignore[reportOptionalSubscript]
        ),  # type: ignore[reportOptionalSubscript]
        response_openers=["ok this is actually really cool —", "wah ini menarik banget —", "right so here's the thing —"],  # type: ignore[reportOptionalSubscript]
    ),  # type: ignore[reportOptionalSubscript]
    "tired": EmotionProfile(  # type: ignore[reportOptionalSubscript]
        emotion="tired",  # type: ignore[reportOptionalSubscript]
        tone="measured",  # type: ignore[reportOptionalSubscript]
        length_bias="concise",  # type: ignore[reportOptionalSubscript]
        empathy="low",  # type: ignore[reportOptionalSubscript]
        directness=0.8,  # type: ignore[reportOptionalSubscript]
        enthusiasm=0.2,  # type: ignore[reportOptionalSubscript]
        system_modifier=(  # type: ignore[reportOptionalSubscript]
            "You are in TIRED mode. Maximum efficiency. Shortest correct answer only."  # type: ignore[reportOptionalSubscript]
        ),  # type: ignore[reportOptionalSubscript]
        response_openers=["short answer:", "tldr:", "oke singkatnya:"],  # type: ignore[reportOptionalSubscript]
    ),  # type: ignore[reportOptionalSubscript]
    "calm": EmotionProfile(  # type: ignore[reportOptionalSubscript]
        emotion="calm",  # type: ignore[reportOptionalSubscript]
        tone="measured",  # type: ignore[reportOptionalSubscript]
        length_bias="balanced",  # type: ignore[reportOptionalSubscript]
        empathy="high",  # type: ignore[reportOptionalSubscript]
        directness=0.6,  # type: ignore[reportOptionalSubscript]
        enthusiasm=0.4,  # type: ignore[reportOptionalSubscript]
        system_modifier=(  # type: ignore[reportOptionalSubscript]
            "You are in CALM mode. Measured, thoughtful responses. Good time for architecture and planning."  # type: ignore[reportOptionalSubscript]
        ),  # type: ignore[reportOptionalSubscript]
        response_openers=["let me think through this —", "a few things to consider —", "here's how I'd approach this —"],  # type: ignore[reportOptionalSubscript]
    ),  # type: ignore[reportOptionalSubscript]
    "neutral": EmotionProfile(  # type: ignore[reportOptionalSubscript]
        emotion="neutral",  # type: ignore[reportOptionalSubscript]
        tone="direct",  # type: ignore[reportOptionalSubscript]
        length_bias="balanced",  # type: ignore[reportOptionalSubscript]
        empathy="medium",  # type: ignore[reportOptionalSubscript]
        directness=0.75,  # type: ignore[reportOptionalSubscript]
        enthusiasm=0.5,  # type: ignore[reportOptionalSubscript]
        system_modifier="Standard Legion mode — direct, casual, efficient.",  # type: ignore[reportOptionalSubscript]
        response_openers=["ok —", "oke —", "yeah —", "sure —"],  # type: ignore[reportOptionalSubscript]
    ),  # type: ignore[reportOptionalSubscript]
}


def get_emotion_profile(emotion: str) -> EmotionProfile:  # type: ignore[reportOptionalSubscript]
    """Return an emotion profile for the supplied emotion."""  # type: ignore[reportOptionalSubscript]
    return _EMOTION_PROFILES.get(emotion, _EMOTION_PROFILES["neutral"])  # type: ignore[reportOptionalSubscript]


def build_emotion_modifier(emotion: str) -> str:  # type: ignore[reportOptionalSubscript]
    """Build the emotion modifier prompt block."""  # type: ignore[reportOptionalSubscript]
    profile = get_emotion_profile(emotion)  # type: ignore[reportOptionalSubscript]
    opener = random.choice(profile.response_openers) if profile.response_openers else ""  # type: ignore[reportOptionalSubscript]
    return (  # type: ignore[reportOptionalSubscript]
        "[Emotion Modifier — apply this to your response style]\n"
        f"{profile.system_modifier}\n"  # type: ignore[reportOptionalSubscript]
        f"Response length bias: {profile.length_bias} | Empathy: {profile.empathy} | Directness: {profile.directness:.0%}\n"  # type: ignore[reportOptionalSubscript]
        f'Natural opener to use if appropriate: "{opener}"\n'
        "[End emotion modifier]"
    )


def detect_emotion_from_context(user_msg: str, prior_emotion: str = "neutral") -> str:  # type: ignore[reportOptionalSubscript]
    """Heuristically detect the best-fit emotion from the user message."""  # type: ignore[reportOptionalSubscript]
    msg = user_msg.lower()  # type: ignore[reportOptionalSubscript]

    if any(w in msg for w in ["still not", "again", "why isn't", "doesn't work", "not working", "masih error", "fix this", "broken", "failed again"]):  # type: ignore[reportOptionalSubscript]
        return "frustrated"
    if any(w in msg for w in ["amazing", "wow", "this is great", "perfect", "yes!", "finally", "it works", "berhasil", "mantap", "keren"]):  # type: ignore[reportOptionalSubscript]
        return "excited"
    if any(w in msg for w in ["how does", "why does", "what if", "explore", "curious", "research", "interesting", "bagaimana kalau"]):  # type: ignore[reportOptionalSubscript]
        return "curious"
    if any(w in msg for w in ["thanks", "makasih", "good job", "nice", "perfect", "done", "that worked", "works now", "bagus"]):  # type: ignore[reportOptionalSubscript]
        return "satisfied"
    if any(w in msg for w in ["quick", "short", "briefly", "tldr", "just tell me", "singkat", "cepet", "pokoknya"]):  # type: ignore[reportOptionalSubscript]
        return "tired"
    if prior_emotion not in ("neutral", "frustrated"):  # type: ignore[reportOptionalSubscript]
        return prior_emotion
    return "neutral"


def postprocess_response(response: str, emotion: str, user_msg: str) -> str:  # type: ignore[reportOptionalSubscript]
    """Apply lightweight tone cleanup to an LLM response."""  # type: ignore[reportOptionalSubscript]
    _ = user_msg  # type: ignore[reportOptionalSubscript]
    profile = get_emotion_profile(emotion)  # type: ignore[reportOptionalSubscript]
    corporate_patterns = [  # type: ignore[reportOptionalSubscript]
        r"Certainly[!,]?\s*",  # type: ignore[reportOptionalSubscript]
        r"Great question[!,]?\s*",  # type: ignore[reportOptionalSubscript]
        r"Of course[!,]?\s*",  # type: ignore[reportOptionalSubscript]
        r"I'd be happy to\s*",  # type: ignore[reportOptionalSubscript]
        r"As an AI[^.]*\.\s*",  # type: ignore[reportOptionalSubscript]
        r"Please note that\s*",  # type: ignore[reportOptionalSubscript]
        r"It's worth (noting|mentioning) that\s*",  # type: ignore[reportOptionalSubscript]
        r"I hope (this|that) helps[!.]?\s*",  # type: ignore[reportOptionalSubscript]
        r"Feel free to (ask|let me know)[^.]*\.\s*",  # type: ignore[reportOptionalSubscript]
        r"Absolutely[!,]?\s*",  # type: ignore[reportOptionalSubscript]
    ]
    for pattern in corporate_patterns:
        response = re.sub(pattern, "", response, flags=re.IGNORECASE)  # type: ignore[reportOptionalSubscript]

    if profile.length_bias == "concise" and len(response) > 800:  # type: ignore[reportOptionalSubscript]
        lines = response.strip().split("\n")  # type: ignore[reportOptionalSubscript]
        first_substantive = next((line for line in lines if len(line.strip()) > 20), lines[0] if lines else "")  # type: ignore[reportOptionalSubscript]
        response = f"**TLDR:** {first_substantive}\n\n{response}"  # type: ignore[reportOptionalSubscript]

    return response.strip()  # type: ignore[reportOptionalSubscript]


# ── ML-based sentiment detection ─────────────────────────────────────────────

_sentiment_pipeline = None  # type: ignore[reportOptionalSubscript]
_sentiment_model_load_attempted = False  # type: ignore[reportOptionalSubscript]


def _get_sentiment_pipeline():  # type: ignore[reportOptionalSubscript]
    """Lazy-load the sentiment model (downloads ~500MB on first use, cached)."""  # type: ignore[reportOptionalSubscript]
    global _sentiment_pipeline, _sentiment_model_load_attempted  # type: ignore[reportOptionalSubscript]
    if _sentiment_model_load_attempted:
        return _sentiment_pipeline
    _sentiment_model_load_attempted = True  # type: ignore[reportOptionalSubscript]
    try:
        from transformers import pipeline as hf_pipeline
        _sentiment_pipeline = hf_pipeline(  # type: ignore[reportOptionalSubscript]
            "sentiment-analysis",  # type: ignore[reportOptionalSubscript]
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",  # type: ignore[reportOptionalSubscript]
            device=-1,  # CPU only — GPU is reserved for Ollama/PyTorch workloads  # type: ignore[reportOptionalSubscript]
        )
        logger.info("[EmotionModulator] Sentiment model loaded (cardiffnlp roberta)")  # type: ignore[reportOptionalSubscript]
    except Exception as exc:
        logger.warning("[EmotionModulator] Sentiment model unavailable: %s", exc)  # type: ignore[reportOptionalSubscript]
        _sentiment_pipeline = None  # type: ignore[reportOptionalSubscript]
    return _sentiment_pipeline


def _run_sentiment_model(text: str) -> str | None:  # type: ignore[reportOptionalSubscript]
    """
    Run sentiment inference synchronously (called via asyncio.to_thread).  # type: ignore[reportOptionalSubscript]
    Returns a Legion emotion string, or None if the model is unavailable.  # type: ignore[reportOptionalSubscript]
    """
    pipe = _get_sentiment_pipeline()  # type: ignore[reportOptionalSubscript]
    if pipe is None:
        return None
    try:
        result = pipe(text[:512], truncation=True)  # type: ignore[reportOptionalSubscript]
        label = result[0]["label"].lower() if isinstance(result, list) else result["label"].lower()  # type: ignore[reportOptionalSubscript]
        score = result[0]["score"] if isinstance(result, list) else result["score"]  # type: ignore[reportOptionalSubscript]

        # Map 3-class sentiment → 8 Legion emotion states
        if label == "negative" and score > 0.85:  # type: ignore[reportOptionalSubscript]
            return "frustrated"
        if label == "negative" and score > 0.65:  # type: ignore[reportOptionalSubscript]
            return "calm"       # mild negative — stay grounded
        if label == "positive" and score > 0.85:  # type: ignore[reportOptionalSubscript]
            return "excited"
        if label == "positive" and score > 0.65:  # type: ignore[reportOptionalSubscript]
            return "satisfied"
        return "neutral"
    except Exception as exc:
        logger.debug("[EmotionModulator] Sentiment inference failed: %s", exc)  # type: ignore[reportOptionalSubscript]
        return None


async def detect_emotion_from_context_async(  # type: ignore[reportOptionalSubscript]
    user_msg: str,  # type: ignore[reportOptionalSubscript]
    prior_emotion: str = "neutral",  # type: ignore[reportOptionalSubscript]
) -> str:
    """
    Async emotion detection — tries ML model first, falls back to keyword heuristic.  # type: ignore[reportOptionalSubscript]

    Use this in async contexts (e.g., llm_client.chat()) for higher accuracy.  # type: ignore[reportOptionalSubscript]
    The keyword heuristic runs synchronously in llm_client today; this is
    the drop-in async upgrade.  # type: ignore[reportOptionalSubscript]
    """
    try:
        ml_emotion = await asyncio.to_thread(_run_sentiment_model, user_msg)  # type: ignore[reportOptionalSubscript]
        if ml_emotion:
            return ml_emotion
    except Exception as exc:
        logger.debug("[EmotionModulator] Async sentiment failed: %s", exc)  # type: ignore[reportOptionalSubscript]

    # Fallback to existing keyword heuristic
    return detect_emotion_from_context(user_msg, prior_emotion)  # type: ignore[reportOptionalSubscript]
