"""Nihongo Mode — Isolated Japanese Teacher Plugin for Legion."""

from skills.nihongo.mode_manager import NihongoModeManager, NihongoSession, NihongoSubMode
from skills.nihongo.sensei_prompt import build_sensei_system_prompt, SenseiPromptBuilder
from skills.nihongo.sensei_soul import SenseiSoul
from skills.nihongo.srs_engine import SRSEngine, SRSCard
from skills.nihongo.mastery_gate import MasteryGate, BloomLevel, MasteryRecord
from skills.nihongo.immersion_world import ImmersionWorld, Location, Scenario
from skills.nihongo.cultural_intel import CulturalIntel, CulturalNote, ImportanceLevel
from skills.nihongo.proactive_sensei import ProactiveSensei
from skills.nihongo.shadow_engine import ShadowEngine, ShadowExercise, PhonemeRecord

__all__ = [
    # Mode manager
    "NihongoModeManager",
    "NihongoSubMode",
    "NihongoSession",
    # Prompt builder
    "build_sensei_system_prompt",
    "SenseiPromptBuilder",
    # Soul
    "SenseiSoul",
    # SRS
    "SRSEngine",
    "SRSCard",
    # Mastery
    "MasteryGate",
    "BloomLevel",
    "MasteryRecord",
    # Immersion
    "ImmersionWorld",
    "Location",
    "Scenario",
    # Culture
    "CulturalIntel",
    "CulturalNote",
    "ImportanceLevel",
    # Proactive
    "ProactiveSensei",
    # Shadow
    "ShadowEngine",
    "ShadowExercise",
    "PhonemeRecord",
]
