from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Skill:
    name: str
    description: str
    trigger_keywords: list[str]
    handler: Callable
    required_env_keys: list[str] = field(default_factory=list)
    category: str = "general"


class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def find_by_example(self, text: str) -> Skill | None:
        text_lower = text.lower()
        best: tuple[float, Skill | None] = (0.0, None)
        for skill in self._skills.values():
            score = sum(1 for kw in skill.trigger_keywords if kw.lower() in text_lower)
            if score > best[0]:
                best = (score, skill)
        return best[1]

    def list_all(self) -> list[Skill]:
        return list(self._skills.values())

    def describe_for_prompt(self) -> str:
        lines = ["Available skills:"]
        for s in self._skills.values():
            lines.append(f"  {s.name}: {s.description} [{', '.join(s.trigger_keywords)}]")
        return "\n".join(lines)


SKILL_REGISTRY = SkillRegistry()

def get_skill_registry() -> SkillRegistry:
    return SKILL_REGISTRY
