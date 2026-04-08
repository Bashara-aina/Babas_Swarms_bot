"""Legion character subsystem."""
from core.character.disagreement_protocol import (
    build_debate_pre_prompt,
    get_disagreement_prompt,
    should_trigger_debate,
)
from core.character.persona import (
    build_base_persona,
    build_mode_instructions,
    load_character_config,
)

__all__ = [
    "build_base_persona",
    "build_debate_pre_prompt",
    "build_mode_instructions",
    "get_disagreement_prompt",
    "load_character_config",
    "should_trigger_debate",
]
