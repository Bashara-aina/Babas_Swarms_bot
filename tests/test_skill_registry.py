from __future__ import annotations

from core.skill_registry import load_skills, skills_prompt_block, skills_prompt_block_for_query


def test_load_skills_returns_list() -> None:
    skills = load_skills()
    assert isinstance(skills, list)


def test_skills_prompt_block() -> None:
    b = skills_prompt_block()
    assert isinstance(b, str)


def test_skills_prompt_ranks_email_query() -> None:
    b = skills_prompt_block_for_query("check my inbox and draft a reply to the guest")
    assert "email_management" in b
    assert "AUTONOMOUS ROUTES" in b
