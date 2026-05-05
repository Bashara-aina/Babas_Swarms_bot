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
    "BloomLevel",
    # Culture
    "CulturalIntel",
    "CulturalNote",
    # Immersion
    "ImmersionWorld",
    "ImportanceLevel",
    "Location",
    # Mastery
    "MasteryGate",
    "MasteryRecord",
    # Mode manager
    "NihongoModeManager",
    "NihongoSession",
    "NihongoSubMode",
    "PhonemeRecord",
    # Proactive
    "ProactiveSensei",
    "SRSCard",
    # SRS
    "SRSEngine",
    "Scenario",
    "SenseiPromptBuilder",
    # Soul
    "SenseiSoul",
    # Shadow
    "ShadowEngine",
    "ShadowExercise",
    # Prompt builder
    "build_sensei_system_prompt",
]
