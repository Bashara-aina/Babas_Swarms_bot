"""ProactiveSensei — Integration with Legion's Proactive Engine.

Provides proactive nudges, daily summaries, and mastery gap analysis.
Integrates with Legion's proactive engine without breaking isolation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from skills.nihongo.srs_engine import SRSEngine, SRSCard
from skills.nihongo.mastery_gate import MasteryGate, BloomLevel


class ProactiveSensei:
    """Proactive Sensei for Nihongo Mode.

    Checks conditions for proactive nudges based on:
    - Time since last session
    - Cards due in SRS engine
    - Failed words needing reintroduction

    This class can be called by Legion's proactive engine.
    """

    # Topics for suggested learning
    SUGGESTED_TOPICS = [
        "greetings",
        "numbers",
        "directions",
        "self-introduction",
        "shopping",
        "food",
        "transportation",
        "university",
        "keigo",
        "hiragana",
        "katakana",
    ]

    def __init__(self) -> None:
        self.srs_engine = SRSEngine()
        self.mastery_gate = MasteryGate()
        # Last proactive check timestamps: user_id -> datetime
        self._last_check: dict[int, datetime] = {}

    def should_proactively_nudge(self, user_id: int) -> bool:
        """Check if user should receive a proactive nudge.

        Conditions:
        - No session in >48 hours (warm-up needed)
        - SRS cards are due
        - Failed words need reintroduction

        Args:
            user_id: The user's ID

        Returns:
            True if nudge should be sent
        """
        from skills.nihongo.mode_manager import NihongoModeManager

        session = NihongoModeManager.get_session(user_id)

        # Check if user has been inactive
        if session.last_active:
            hours_since_active = (datetime.now() - session.last_active).total_seconds() / 3600
            if hours_since_active > 48:
                return True

        # Check if user has SRS cards due
        due_cards = self.srs_engine.get_due_cards(user_id)
        if len(due_cards) >= 3:
            return True

        # Check if user has failed items
        failed_items = self.srs_engine.get_failed_items(user_id)
        if len(failed_items) >= 5:
            return True

        return False

    def generate_proactive_message(self, user_id: int) -> str:
        """Generate a gentle nudge message for the user.

        Args:
            user_id: The user's ID

        Returns:
            Nudge message string
        """
        due_cards = self.srs_engine.get_due_cards(user_id)
        failed_items = self.srs_engine.get_failed_items(user_id)
        mastery_pct = self.srs_engine.get_mastery_percentage(user_id)

        messages = []

        if due_cards:
            messages.append(f"📅 Ada {len(due_cards)} kartu yang perlu diulang nih!")

        if failed_items:
            messages.append(f"💪 Kata-kata yang perlu perhatian lebih: {', '.join(failed_items[:3])}")

        if mastery_pct < 30:
            messages.append("🎯 Baru mulai belajar — keep going Bas!")
        elif mastery_pct < 60:
            messages.append("📈 Progress bagus! Ayo lanjutkan perjalananmu.")
        else:
            messages.append("🏆 mastery naik! Kamu sudah hebat, Bas!")

        base_message = "،最近日本語で何を勉強したいですか？ ".join(messages)

        return f"⛩ <b>Hanako Sensei reminder:</b>\n\n{base_message}\n\nCoba ketik /nihonko untuk lanjut belajar!"

    def get_suggested_topic(self, user_id: int) -> str:
        """Get suggested topic based on mastery gaps.

        Args:
            user_id: The user's ID

        Returns:
            Topic name string
        """
        # Analyze mastery distribution to find gaps
        distribution = self.mastery_gate.get_mastery_distribution(user_id)

        # Find Bloom levels with low mastery
        weak_levels = [level for level, count in distribution.items() if count == 0 and level != BloomLevel.REMEMBER]

        if weak_levels:
            # Suggest topic based on weakest level
            weakest = min(weak_levels, key=lambda l: l.value)
            topic_map = {
                BloomLevel.REMEMBER: "hiragana",
                BloomLevel.UNDERSTAND: "greetings",
                BloomLevel.APPLY: "self-introduction",
                BloomLevel.ANALYZE: "directions",
                BloomLevel.EVALUATE: "keigo",
                BloomLevel.CREATE: "free",
            }
            return topic_map.get(weakest, "greetings")

        # Default to greeting if everything is equally weak
        return "greetings"

    def format_daily_summary(self, user_id: int) -> str:
        """Format end-of-day summary for user.

        Args:
            user_id: The user's ID

        Returns:
            Telegram-formatted summary string
        """
        mastery_pct = self.srs_engine.get_mastery_percentage(user_id)
        due_cards = self.srs_engine.get_due_cards(user_id)
        overdue_cards = self.srs_engine.get_overdue_cards(user_id)
        failed_items = self.srs_engine.get_failed_items(user_id)

        return (
            f"⛩ <b>Hanako Daily Summary</b>\n\n"
            f"📊 <b>Progress:</b>\n"
            f"- SRS Mastery: {mastery_pct:.1f}%\n"
            f"- Cards due: {len(due_cards)}\n"
            f"- Overdue: {len(overdue_cards)}\n"
            f"- Failed words: {len(failed_items)}\n\n"
            f"🎯 <b>Tips:</b>\n"
            f"{'Ayo diulang dulu kartu yang overdue!' if overdue_cards else 'Hari ini bagus! Lanjut besok ya!'}\n\n"
            f"AUTO_DI: Jangan lupa belajar日本語 setiap hari! "
            f'"/nihonko" untuk mulai!'
        )

    def check_and_trigger_proactive(self) -> list[tuple[int, str]]:
        """Check all conditions and return any triggered nudges.

        This can be called periodically by Legion's proactive engine.

        Returns:
            List of (user_id, message) tuples for users who need nudges
        """
        from skills.nihongo.mode_manager import NihongoModeManager

        triggers = []

        # Check all active sessions
        for user_id, session in NihongoModeManager._sessions.items():
            if session.active and self.should_proactively_nudge(user_id):
                message = self.generate_proactive_message(user_id)
                triggers.append((user_id, message))

        return triggers

    def get_user_learning_stats(self, user_id: int) -> dict:
        """Get comprehensive learning stats for a user."""
        from skills.nihongo.mode_manager import NihongoModeManager

        session = NihongoModeManager.get_session(user_id)

        return {
            "srs_mastery_percentage": self.srs_engine.get_mastery_percentage(user_id),
            "cards_due": len(self.srs_engine.get_due_cards(user_id)),
            "cards_overdue": len(self.srs_engine.get_overdue_cards(user_id)),
            "failed_items": len(self.srs_engine.get_failed_items(user_id)),
            "mastered_items": len(self.srs_engine.get_mastered_items(user_id)),
            "mastery_distribution": self.mastery_gate.get_mastery_distribution(user_id),
            "suggested_topic": self.get_suggested_topic(user_id),
            "last_active": session.last_active.isoformat() if session.last_active else None,
            "exchange_count": session.exchange_count,
        }
