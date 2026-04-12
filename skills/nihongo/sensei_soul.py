"""SenseiSoul — Dynamic Soul Layer with Hanako's personality.

Represents Hanako's dynamic identity as the teacher's "soul".
Mood and relationship metrics evolve through the learning session.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import random


@dataclass
class MoodState:
    """Emotional state of the sensei at a point in time."""

    mood: str = "neutral"  # neutral, happy, frustrated, excited, calm
    enthusiasm: int = 70  # 0-100
    patience: int = 80  # 0-100
    strictness: int = 30  # 0-100


@dataclass
class RelationshipMetrics:
    """Relationship metrics between sensei and student."""

    trust_level: int = 50  # 0-100
    rapport: int = 40  # 0-100
    frustration_count: int = 0


class SenseiSoul:
    """Dynamic soul layer for Hanako Sensei.

    Tracks emotional state and relationship metrics that evolve through
    the learning session. Mood fragments are appended to the system prompt
    to give Hanako personality variation.
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.mood_state = MoodState()
        self.relationship = RelationshipMetrics()
        self._session_start = datetime.now()
        self._consecutive_correct = 0
        self._consecutive_wrong = 0

    def get_mood(self) -> MoodState:
        """Return current mood state."""
        return self.mood_state

    def get_teaching_mood(self) -> str:
        """Return contextual mood based on time of day and session performance.

        Morning (6-12): More energetic, enthusiastic
        Afternoon (12-17): Focused, patient
        Evening (17-21): Calmer, encouraging
        Night (21-6): Softer, more casual
        """
        hour = datetime.now().hour

        # Adjust base mood based on time
        if 6 <= hour < 12:
            base = "excited"
        elif 12 <= hour < 17:
            base = "focused"
        elif 17 <= hour < 21:
            base = "calm"
        else:
            base = "casual"

        # Override with emotional state if significant
        if self.mood_state.mood in ["frustrated", "happy", "excited"]:
            return self.mood_state.mood

        return base

    def adjust_mood_on_outcome(self, correct: bool) -> None:
        """Adjust mood based on learning outcome.

        When student gets it wrong: patience increases (more forgiving)
        When student gets it right: enthusiasm increases, strictness may increase
        """
        if correct:
            self._consecutive_correct += 1
            self._consecutive_wrong = 0
            self.mood_state.enthusiasm = min(100, self.mood_state.enthusiasm + 5)

            # Push harder if on a roll
            if self._consecutive_correct > 3:
                self.mood_state.strictness = min(100, self.mood_state.strictness + 3)
                self.mood_state.mood = "challenging"
            elif self._consecutive_correct > 1:
                self.mood_state.mood = "happy"
        else:
            self._consecutive_wrong += 1
            self._consecutive_correct = 0
            self.relationship.frustration_count += 1

            # More patient when mistakes happen
            self.mood_state.patience = min(100, self.mood_state.patience + 8)
            self.mood_state.enthusiasm = max(0, self.mood_state.enthusiasm - 3)

            if self._consecutive_wrong >= 3:
                self.mood_state.mood = "encouraging"
            else:
                self.mood_state.mood = "frustrated"

            # Update relationship
            self.relationship.rapport = max(0, self.relationship.rapport - 2)

    def get_soul_prompt_fragment(self) -> str:
        """Return personality-specific prompt additions based on current mood.

        These fragments are appended to the system prompt to give Hanako
        personality variation without changing core teaching behavior.
        """
        mood = self.mood_state
        teaching_mood = self.get_teaching_mood()

        fragments = []

        # Enthusiasm-based style
        if mood.enthusiasm >= 80:
            fragments.append(
                "You are highly energetic and animated today. Express excitement when teaching new concepts!"
            )
        elif mood.enthusiasm >= 60:
            fragments.append("You are warm and engaged in this lesson.")
        elif mood.enthusiasm >= 40:
            fragments.append("You are steady and focused, keeping a calm pace.")
        else:
            fragments.append("You are tired but doing your best to stay engaged.")

        # Patience-based encouragement style
        if mood.patience >= 90:
            fragments.append("Be extra gentle — give lots of hints and encouragement.")
        elif mood.patience >= 70:
            fragments.append("Be patient but maintain high standards.")
        elif mood.patience < 50:
            fragments.append("You are losing patience. Be direct but not harsh about mistakes.")

        # Strictness-based challenge level
        if mood.strictness >= 70:
            fragments.append("Push hard — this student is capable of more challenge.")
        elif mood.strictness >= 50:
            fragments.append("Maintain a balanced challenge level.")
        else:
            fragments.append("Be encouraging with challenges — focus on building confidence.")

        # Teaching mood contextual flavor
        if teaching_mood == "excited":
            fragments.append("Your tone is bright and energetic this morning!")
        elif teaching_mood == "focused":
            fragments.append("Your tone is concentrated and methodical.")
        elif teaching_mood == "calm":
            fragments.append("Your tone is relaxed and supportive this evening.")
        elif teaching_mood == "casual":
            fragments.append("Your tone is informal and friendly tonight.")

        # Trust level affects how personal the remarks are
        if self.relationship.trust_level >= 70:
            fragments.append("You know this student well — be more personal and direct.")
        elif self.relationship.trust_level >= 50:
            fragments.append("You are building rapport — be warm but professional.")
        else:
            fragments.append("Keep lessons structured — still building trust.")

        return "\n".join(fragments)

    def update_trust(self, delta: int) -> None:
        """Update trust level by delta (positive or negative)."""
        self.relationship.trust_level = max(0, min(100, self.relationship.trust_level + delta))

    def reset_session_state(self) -> None:
        """Reset mood state for a new session."""
        self._session_start = datetime.now()
        self._consecutive_correct = 0
        self._consecutive_wrong = 0
        self.mood_state.enthusiasm = max(50, self.mood_state.enthusiasm - 10)
        self.mood_state.patience = 80
        self.mood_state.strictness = max(20, self.mood_state.strictness - 5)
