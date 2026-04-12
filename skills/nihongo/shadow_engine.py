"""ShadowEngine — Shadow Speaking for Pronunciation Practice.

Provides shadow speaking exercises with phoneme-level feedback.
Tracks pronunciation improvement over time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class ShadowExercise:
    """A shadow speaking exercise with transcription data.

    Attributes:
        japanese_text: The Japanese text to shadow
        romaji: Romaji transcription
        audio_url: Optional URL to audio reference
        difficulty: Difficulty level (N5, N4, etc.)
        scenario: Context scenario for this exercise
    """

    japanese_text: str
    romaji: str
    audio_url: Optional[str] = None
    difficulty: str = "N5"
    scenario: str = "general"


@dataclass
class PhonemeRecord:
    """Tracks accuracy for a specific phoneme."""

    phoneme: str
    attempts: int = 0
    correct_count: int = 0
    accuracy: float = 0.0


class ShadowEngine:
    """Shadow Speaking Engine for Nihongo Mode.

    Provides shadow speaking exercises with phoneme-level feedback
    and pronunciation tracking. Narita-specific scripts include
    airport announcements and campus PA.
    """

    # Common N5 shadow exercises
    BASE_EXERCISES = [
        ShadowExercise(
            japanese_text="ありがとうございます",
            romaji="arigatou gozaimasu",
            difficulty="N5",
            scenario="general",
        ),
        ShadowExercise(
            japanese_text="すみません、教えてください",
            romaji="sumimasen, oshiete kudasai",
            difficulty="N5",
            scenario="asking_help",
        ),
        ShadowExercise(
            japanese_text="はい、わかりました",
            romaji="hai, wakamarimashita",
            difficulty="N5",
            scenario="acknowledgment",
        ),
        ShadowExercise(
            japanese_text="お名前はなんですか",
            romaji="onamae wa nan desu ka",
            difficulty="N5",
            scenario="introduction",
        ),
        ShadowExercise(
            japanese_text="どこですか",
            romaji="doko desu ka",
            difficulty="N5",
            scenario="location",
        ),
        ShadowExercise(
            japanese_text="いくらですか",
            romaji="ikura desu ka",
            difficulty="N5",
            scenario="shopping",
        ),
    ]

    # Narita-specific shadow scripts
    NARITA_SCRIPTS = [
        ShadowExercise(
            japanese_text="成田空港へようこそ",
            romaji="narita kuukou e youkoso",
            difficulty="N5",
            scenario="narita_airport",
        ),
        ShadowExercise(
            japanese_text="この電車は、成田空港駅行きです",
            romaji="kono densha wa, narita kuukou eki yuki desu",
            difficulty="N5",
            scenario="train_announcement",
        ),
        ShadowExercise(
            japanese_text="出口は前の扉です",
            romaji="deguchi wa mae no tobira desu",
            difficulty="N5",
            scenario="train_announcement",
        ),
        ShadowExercise(
            japanese_text="京成線はお,第32番線ホームです",
            romaji="keisei-sen wa, dai 32 ban sen hoomu desu",
            difficulty="N5",
            scenario="keio_line",
        ),
        ShadowExercise(
            japanese_text="次は、成田空港駅です",
            romaji="tsugi wa, narita kuukou eki desu",
            difficulty="N5",
            scenario="train_announcement",
        ),
        ShadowExercise(
            japanese_text="学研究室の山田先生、いらっしゃいますか",
            romaji="kenkyuushitsu no Yamada-sensei, irasshaimasu ka",
            difficulty="N5",
            scenario="campus",
        ),
        ShadowExercise(
            japanese_text="飛行機の時間は9時です",
            romaji="hikouki no jikan wa, ku-ji desu",
            difficulty="N5",
            scenario="narita_airport",
        ),
    ]

    # Problematic phonemes for Indonesian speakers
    PROBLEMATIC_PHONEMES = {
        "ら": {"description": "r vs l distinction", "common_mistake": "la"},
        "る": {"description": "ru vs lu", "common_mistake": "ru often pronounced as 'lu'"},
        "ふ": {"description": "f sound not in Indonesian", "common_mistake": "hu instead of fu"},
        "じ": {"description": "ji vs zi", "common_mistake": "Indonesian 'j' is different"},
        "ち": {"description": "chi vs ti", "common_mistake": "t before i should be chi"},
        "つ": {"description": "tsu not in Indonesian", "common_mistake": "tu instead of tsu"},
        "しゃ": {"description": "sha consonant cluster", "common_mistake": "sia"},
        "しょ": {"description": "sho consonant cluster", "common_mistake": "sio"},
        "じゃ": {"description": "ja vs dya", "common_mistake": "jia"},
    }

    def __init__(self) -> None:
        # User phoneme tracking: user_id -> {phoneme -> PhonemeRecord}
        self._phoneme_progress: dict[int, dict[str, PhonemeRecord]] = {}
        # User shadow history: user_id -> list of attempt dicts
        self._shadow_history: dict[int, list[dict]] = {}

    def get_exercise_for_level(self, user_id: int, level: str) -> ShadowExercise:
        """Get a shadow exercise appropriate for the user's level.

        Args:
            user_id: The user's ID
            level: JLPT level (N5, N4, N3)

        Returns:
            ShadowExercise appropriate for level
        """
        exercises = [e for e in self.BASE_EXERCISES if e.difficulty == level]
        if not exercises:
            exercises = self.BASE_EXERCISES

        # Weight by weak phonemes
        weaknesses = self.get_phoneme_weaknesses(user_id)

        # Prefer exercises containing weak phonemes
        weighted = []
        for ex in exercises:
            weight = sum(1 for phoneme in weaknesses if phoneme in ex.romaji)
            weighted.extend([ex] * (weight + 1))

        return random.choice(weighted if weighted else exercises)

    def compare_shadow_attempt(self, user_id: int, original: str, attempt_transcription: str) -> dict:
        """Compare user's shadow attempt to original.

        Args:
            user_id: The user's ID
            original: The original Japanese text
            attempt_transcription: User's transcription attempt

        Returns:
            Dict with similarity_score, problem_phonemes, and feedback
        """
        original_clean = original.replace(" ", "").lower()
        attempt_clean = attempt_transcription.replace(" ", "").lower()

        # Simple similarity: character overlap
        if original_clean == attempt_clean:
            similarity = 100.0
        else:
            # Character-by-character comparison
            matches = sum(1 for o, a in zip(original_clean, attempt_clean) if o == a)
            similarity = (matches / max(len(original_clean), len(attempt_clean))) * 100

        # Find problem phonemes based on common mistakes
        problem_phonemes = []
        for phoneme, info in self.PROBLEMATIC_PHONEMES.items():
            if phoneme in original_clean:
                # Check if user might have mispronounced
                if info["common_mistake"].split()[0] in attempt_clean:
                    problem_phonemes.append(phoneme)

        # Generate feedback
        if similarity >= 90:
            feedback = "✅ Sempurna! Artikulasimu sangat dekat dengan asli."
        elif similarity >= 70:
            feedback = "👍 Bagus! Coba perhatikan lebih detail pelafalan."
        else:
            feedback = "💪 Terus berlatih! Jangan menyerah."

        result = {
            "similarity_score": similarity,
            "problem_phonemes": problem_phonemes,
            "feedback": feedback,
        }

        # Record attempt
        if user_id not in self._shadow_history:
            self._shadow_history[user_id] = []
        self._shadow_history[user_id].append(result)

        return result

    def get_narita_shadow_scripts(self) -> list[ShadowExercise]:
        """Get Narita-specific shadowing scripts.

        Returns:
            List of ShadowExercise for Narita/airport context
        """
        return self.NARITA_SCRIPTS.copy()

    def track_shadow_progress(self, user_id: int, phoneme: str, accuracy: float) -> PhonemeRecord:
        """Track shadow practice progress for a phoneme.

        Args:
            user_id: The user's ID
            phoneme: The Japanese phoneme/character
            accuracy: Accuracy score 0.0-100.0

        Returns:
            Updated PhonemeRecord
        """
        if user_id not in self._phoneme_progress:
            self._phoneme_progress[user_id] = {}

        if phoneme not in self._phoneme_progress[user_id]:
            self._phoneme_progress[user_id][phoneme] = PhonemeRecord(phoneme=phoneme)

        record = self._phoneme_progress[user_id][phoneme]
        record.attempts += 1
        if accuracy >= 70:
            record.correct_count += 1
        record.accuracy = (record.correct_count / record.attempts) * 100.0

        return record

    def get_phoneme_weaknesses(self, user_id: int) -> list[str]:
        """Get phonemes that user has difficulty with.

        Args:
            user_id: The user's ID

        Returns:
            List of problematic phoneme strings
        """
        if user_id not in self._phoneme_progress:
            return []

        weaknesses = [
            record.phoneme
            for record in self._phoneme_progress[user_id].values()
            if record.accuracy < 70 and record.attempts >= 3
        ]
        return weaknesses

    def get_phoneme_strengths(self, user_id: int) -> list[str]:
        """Get phonemes user is strong at."""
        if user_id not in self._phoneme_progress:
            return []

        return [
            record.phoneme
            for record in self._phoneme_progress[user_id].values()
            if record.accuracy >= 80 and record.attempts >= 3
        ]

    def get_shadow_stats(self, user_id: int) -> dict:
        """Get overall shadow practice statistics."""
        if user_id not in self._phoneme_progress:
            return {
                "total_phonemes_practiced": 0,
                "strong_phonemes": 0,
                "weak_phonemes": 0,
                "total_exercises": 0,
            }

        records = list(self._phoneme_progress[user_id].values())
        return {
            "total_phonemes_practiced": len(records),
            "strong_phonemes": sum(1 for r in records if r.accuracy >= 80),
            "weak_phonemes": sum(1 for r in records if r.accuracy < 70),
            "total_exercises": len(self._shadow_history.get(user_id, [])),
        }
