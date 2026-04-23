"""Nihongo Mode — Isolated Japanese Teacher Plugin for Legion."""

from skills.nihongo.cultural_intel import CulturalIntel, CulturalNote, ImportanceLevel
from skills.nihongo.immersion_world import ImmersionWorld, Location, Scenario
from skills.nihongo.mastery_gate import BloomLevel, MasteryGate, MasteryRecord
from skills.nihongo.mode_manager import NihongoModeManager, NihongoSession, NihongoSubMode
from skills.nihongo.proactive_sensei import ProactiveSensei
from skills.nihongo.sensei_prompt import SenseiPromptBuilder, build_sensei_system_prompt
from skills.nihongo.sensei_soul import SenseiSoul
from skills.nihongo.shadow_engine import PhonemeRecord, ShadowEngine, ShadowExercise
from skills.nihongo.srs_engine import SRSCard, SRSEngine

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
