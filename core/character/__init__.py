"""Legion character subsystem."""
from core.character.disagreement_protocol import (
    get_disagreement_prompt,
    should_trigger_debate,
    build_debate_pre_prompt,
)

__all__ = [
    "get_disagreement_prompt",
    "should_trigger_debate",
    "build_debate_pre_prompt",
]
