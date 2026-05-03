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
from core.character.svara_surya import (
    SvaraActivation,
    SvaraDomain,
    classify_svara_domain,
    get_svara_injection,
    get_svara_markers,
    should_activate,
)

__all__ = [
    "SvaraActivation",
    "SvaraDomain",
    "build_base_persona",
    "build_debate_pre_prompt",
    "build_mode_instructions",
    "classify_svara_domain",
    "get_disagreement_prompt",
    "get_svara_injection",
    "get_svara_markers",
    "load_character_config",
    "should_activate",
    "should_trigger_debate",
]
