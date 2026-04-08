from __future__ import annotations

from core.skill_registry import load_skills, skills_prompt_block


def test_load_skills_returns_list() -> None:
    skills = load_skills()
    assert isinstance(skills, list)


def test_skills_prompt_block() -> None:
    b = skills_prompt_block()
    assert isinstance(b, str)
