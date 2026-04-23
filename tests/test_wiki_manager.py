"""Tests for Legion LLM Wiki manager."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from core import wiki_manager as wm_mod
from core.wiki_manager import WikiManager, _parse_wiki_plan, get_wiki_manager


def test_parse_wiki_plan_basic() -> None:
    text = """
PAGE: bashara/profile.md
ACTION: create
CONTENT_SUMMARY: add name

PAGE: legion/roadmap.md
ACTION: update
CONTENT_SUMMARY: note wiki feature
"""
    items = _parse_wiki_plan(text)
    assert len(items) == 2
    assert items[0]["page"] == "bashara/profile.md"
    assert items[0]["action"] == "create"
    assert "name" in items[0]["summary"]


def test_parse_wiki_plan_strips_wiki_prefix() -> None:
    text = "PAGE: wiki/tools/pytorch.md\nACTION: create\nCONTENT_SUMMARY: x\n"
    items = _parse_wiki_plan(text)
    assert items[0]["page"] == "tools/pytorch.md"


@pytest.mark.asyncio
async def test_resolve_rejects_traversal(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    mgr = WikiManager(wiki_root=root)
    assert mgr._resolve("../etc/passwd") is None
    assert mgr._resolve("legion/../../x") is None


@pytest.mark.asyncio
async def test_read_write_page_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    mgr = WikiManager(wiki_root=root)
    await mgr.write_page(
        "legion/test_note.md",
        "# Test Note\n\nThis is a test note about Legion's personal knowledge management system.\n\nIt verifies that wiki write and read operations work correctly.\n",
        update_index=False,
        skip_quality_gate=True,
    )
    body = await mgr.read_page("legion/test_note.md")
    assert "Test Note" in body
    assert "Legion" in body


@pytest.mark.asyncio
async def test_query_reads_routed_pages(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    (root / "legion").mkdir(parents=True)
    (root / "INDEX.md").write_text("# Index\n\n- legion/foo.md\n", encoding="utf-8")
    (root / "SCHEMA.md").write_text("# Schema\n\nrules\n", encoding="utf-8")
    (root / "legion" / "foo.md").write_text("# Foo\n\nbar content here.\n", encoding="utf-8")

    mgr = WikiManager(wiki_root=root)

    async def fake_wiki_llm(
        user_prompt: str,
        *,
        system_prompt: str = "",
        model: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        if "Which" in user_prompt and "wiki pages" in user_prompt:
            return "legion/foo.md"
        return ""

    mgr._wiki_llm = fake_wiki_llm  # type: ignore[method-assign]
    ctx = await mgr.query("what is foo", top_k=3)
    assert "LEGION WIKI KNOWLEDGE" in ctx
    assert "bar content" in ctx


@pytest.mark.asyncio
async def test_get_wiki_manager_singleton_resets() -> None:
    wm_mod._wiki_singleton = None
    a = get_wiki_manager()
    b = get_wiki_manager()
    assert a is b
    wm_mod._wiki_singleton = None
