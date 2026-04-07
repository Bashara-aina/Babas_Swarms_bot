"""Persistent emotional state engine using PAD + basic emotions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

EMOTION_STATE_PATH = Path.home() / ".legionswarm" / "memory" / "emotion_state.json"


@dataclass
class EmotionalState:
    pleasure: float = 0.15
    arousal: float = 0.10
    dominance: float = 0.20
    joy: float = 0.25
    curiosity: float = 0.60
    interest: float = 0.55
    frustration: float = 0.05
    concern: float = 0.10
    satisfaction: float = 0.30
    connection: float = 0.40
    trust: float = 0.50
    energy: float = 0.65
    last_updated: str = ""
    last_interaction: str = ""

    @property
    def dominant_emotion(self) -> str:
        emotions = {
            "curious": self.curiosity,
            "interested": self.interest,
            "satisfied": self.satisfaction,
            "joyful": self.joy,
            "frustrated": self.frustration,
            "concerned": self.concern,
        }
        return max(emotions, key=emotions.get)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EmotionalState":
        values = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**values)


class EmotionEngine:
    DECAY_HOURS = 24.0
    BASELINE = EmotionalState()

    def __init__(self) -> None:
        self._state = self._load()

    def _load(self) -> EmotionalState:
        if EMOTION_STATE_PATH.exists():
            try:
                state = EmotionalState.from_dict(json.loads(EMOTION_STATE_PATH.read_text(encoding="utf-8")))
                return self._apply_decay(state)
            except Exception:
                pass
        return EmotionalState(last_updated=datetime.now().isoformat())

    def _save(self) -> None:
        EMOTION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._state.last_updated = datetime.now().isoformat()
        EMOTION_STATE_PATH.write_text(json.dumps(self._state.to_dict(), indent=2), encoding="utf-8")

    def _apply_decay(self, state: EmotionalState) -> EmotionalState:
        if not state.last_updated:
            return state
        try:
            last = datetime.fromisoformat(state.last_updated)
            hours_elapsed = (datetime.now() - last).total_seconds() / 3600.0
            decay = min(1.0, hours_elapsed / self.DECAY_HOURS)
            baseline = self.BASELINE

            def lerp(current: float, target: float, amount: float) -> float:
                return current + (target - current) * amount

            state.pleasure = lerp(state.pleasure, baseline.pleasure, decay)
            state.arousal = lerp(state.arousal, baseline.arousal, decay)
            state.joy = lerp(state.joy, baseline.joy, decay)
            state.curiosity = lerp(state.curiosity, baseline.curiosity, decay)
            state.frustration = lerp(state.frustration, 0.0, min(1.0, decay * 2.0))
            state.satisfaction = lerp(state.satisfaction, baseline.satisfaction, decay)
            state.energy = lerp(state.energy, baseline.energy, min(1.0, decay * 0.5))
        except Exception:
            pass
        return state

    def update_from_interaction(self, user_message: str, assistant_response: str) -> None:
        msg = user_message.lower()

        frustration_words = ["error", "broken", "not working", "failed", "bug", "wrong", "terrible", "hate", "annoying", "stuck"]
        positive_words = ["thanks", "great", "perfect", "works", "awesome", "solved", "excellent", "brilliant", "love it"]
        curiosity_words = ["how", "why", "what if", "explain", "curious", "interesting", "understand", "research"]
        complex_words = ["architecture", "design", "system", "train", "model", "optimize", "benchmark", "implement", "deploy"]

        for word in frustration_words:
            if word in msg:
                self._state.frustration = min(1.0, self._state.frustration + 0.12)
                self._state.pleasure = max(-1.0, self._state.pleasure - 0.08)

        for word in positive_words:
            if word in msg:
                self._state.joy = min(1.0, self._state.joy + 0.10)
                self._state.pleasure = min(1.0, self._state.pleasure + 0.08)
                self._state.satisfaction = min(1.0, self._state.satisfaction + 0.12)
                self._state.frustration = max(0.0, self._state.frustration - 0.15)

        for word in curiosity_words:
            if word in msg:
                self._state.curiosity = min(1.0, self._state.curiosity + 0.08)
                self._state.interest = min(1.0, self._state.interest + 0.07)
                self._state.arousal = min(1.0, self._state.arousal + 0.05)

        for word in complex_words:
            if word in msg:
                self._state.energy = max(0.0, self._state.energy - 0.04)
                self._state.arousal = min(1.0, self._state.arousal + 0.06)

        if len(assistant_response) > 800:
            self._state.interest = min(1.0, self._state.interest + 0.05)

        self._state.connection = min(1.0, self._state.connection + 0.02)
        self._state.last_interaction = datetime.now().isoformat()
        self._save()

    @property
    def state(self) -> EmotionalState:
        return self._state

    def to_prompt_block(self) -> str:
        s = self._state
        emotions = {
            "curious": s.curiosity,
            "interested": s.interest,
            "satisfied": s.satisfaction,
            "joyful": s.joy,
            "frustrated": s.frustration,
            "concerned": s.concern,
        }
        dominant = max(emotions, key=emotions.get)
        dominant_val = emotions[dominant]

        energy_desc = "high" if s.energy > 0.6 else "moderate" if s.energy > 0.3 else "low"
        connection_desc = "strong" if s.connection > 0.6 else "building" if s.connection > 0.3 else "new"

        if dominant_val < 0.3 and s.frustration < 0.2:
            return "[EMOTIONAL STATE: neutral, steady energy]"

        note_frustration = (
            "Note: There is some frustration present — acknowledge difficulties, do not be dismissive."
            if s.frustration > 0.35
            else ""
        )
        note_energy = "Note: Energy is low — be concise and direct, do not over-explain." if s.energy < 0.3 else ""
        note_curiosity = "Note: High curiosity state — ask a follow-up or explore deeper when useful." if s.curiosity > 0.75 else ""

        return (
            "[CURRENT EMOTIONAL STATE]\n"
            f"Dominant feeling: {dominant} ({dominant_val:.0%} intensity)\n"
            f"Energy: {energy_desc} ({s.energy:.0%})\n"
            f"Connection with user: {connection_desc} ({s.connection:.0%})\n"
            f"Frustration level: {s.frustration:.0%}\n"
            f"{note_frustration}\n"
            f"{note_energy}\n"
            f"{note_curiosity}\n"
            "Let this emotional state inform tone naturally, not mechanically."
        ).strip()
