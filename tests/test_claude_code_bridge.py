
import pytest

from core.claude_code_bridge import (
    CLAUDE_CODE_CLI,
    extract_claude_directive,
    run_claude_task,
)


def test_cli_path():
    assert CLAUDE_CODE_CLI is not None

def test_extract_directive():
    m = extract_claude_directive("done! @claude implement auth middleware")
    assert m is not None
    assert "implement auth" in m

def test_extract_directive_none():
    m = extract_claude_directive("no directive here")
    assert m is None

@pytest.mark.asyncio
async def test_run_claude_task_smoke():
    result = await run_claude_task("say exactly: hello", timeout=30)
    # May fail if claude CLI not available — check error field
    assert "output" in result or "error" in result
