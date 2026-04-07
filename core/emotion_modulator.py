"""Emotion modulation engine for response style control."""

from __future__ import annotations

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
