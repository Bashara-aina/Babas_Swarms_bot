"""test_private_tag_stripping.py — <private> tags stripped in every write path."""
import pytest
from core.memory.observation_store import get_observation_store, _strip_private


def test_strip_private_removes_xml_block():
    assert _strip_private("hello <private>secret</private> world") == "hello  world"


def test_strip_private_removes_inline_block():
    assert _strip_private("foo [private]hidden[/private] bar") == "foo  bar"


def test_strip_private_case_insensitive():
    assert _strip_private("X<PRIVATE>SECRET</PRIVATE>Y") == "XY"


@pytest.mark.asyncio
async def test_add_observation_strips_private_from_every_string_field():
    store = get_observation_store()
    obs_id = await store.add_observation(
        session_id="privacy-test",
        content="public content",
        title="public <private>hidden</private> title",
        subtitle="<private>hidden sub</private> visible",
        narrative="narrative with <private>nope</private> in it",
        facts="facts <private>X</private>",
        concepts="concepts <private>Y</private>",
    )
    assert obs_id > 0
    import aiosqlite
    async with aiosqlite.connect(str(store._db_path())) as db:  # type: ignore[attr-defined]
        cur = await db.execute(
            "SELECT title, subtitle, narrative, facts, concepts FROM observations WHERE id = ?",
            (obs_id,),
        )
        row = await cur.fetchone()
    assert row is not None
    title, subtitle, narrative, facts, concepts = row
    assert "hidden" not in title
    assert "hidden sub" not in subtitle
    assert "nope" not in narrative
    assert "X" not in facts
    assert "Y" not in concepts
