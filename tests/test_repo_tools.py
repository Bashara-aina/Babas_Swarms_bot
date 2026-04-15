"""Tests for the new REPO tools: plandex_agent, crawl4ai_tool, nanobrowser_agent, swe_agent_bridge, sandbox_executor, swarm_handoff."""

import pytest


class TestPlandexAgent:
    """REPO #1: Plandex agent wrapper."""

    def test_plandex_extract_plan_id(self):
        from tools.plandex_agent import PlandexAgent

        lines = [
            "Planning: Fix the auth bug",
            "Created plan-abc123xyz on branch main",
            "Steps: 4 files, 2 dirs",
        ]
        plan_id = PlandexAgent.extract_plan_id(lines)
        assert plan_id == "abc123xyz"

    def test_plandex_extract_plan_id_none(self):
        from tools.plandex_agent import PlandexAgent

        lines = ["No plan created", "Error: something went wrong"]
        assert PlandexAgent.extract_plan_id(lines) is None


class TestSandboxExecutor:
    """REPO #3: E2B sandbox executor."""

    def test_sandbox_executor_init(self):
        from tools.sandbox_executor import SandboxExecutor

        exec = SandboxExecutor(api_key="test-key")
        assert exec.api_key == "test-key"
        # LEGION_SANDBOX_ENABLED defaults to false (no .env in test)
        assert exec._enabled is False

    def test_sandbox_executor_local_fallback(self):
        from tools.sandbox_executor import SandboxExecutor

        exec = SandboxExecutor()
        # Without E2B_API_KEY, should use local fallback
        assert exec._enabled is False or exec.api_key is None


class TestCrawl4aiTool:
    """REPO #7: Crawl4AI tool."""

    def test_crawl4ai_init(self):
        from tools.crawl4ai_tool import Crawl4AITool

        tool = Crawl4AITool()
        assert tool._crawler is None

    def test_crawl4ai_singleton(self):
        from tools.crawl4ai_tool import get_crawl4ai

        a = get_crawl4ai()
        b = get_crawl4ai()
        assert a is b


class TestSwarmHandoff:
    """REPO #10: Swarm handoff."""

    def test_handoff_request(self):
        from tools.swarm_handoff import HandoffTarget, SwarmHandoff

        h = SwarmHandoff()
        result = h.request_handoff(
            from_agent="general",
            to_target=HandoffTarget.CODING,
            context={"original_task": "write tests"},
            reason="coding intent detected",
        )
        assert result.target == HandoffTarget.CODING
        assert result.context["source_agent"] == "general"
        assert result.context["original_task"] == "write tests"

    def test_handoff_pending(self):
        from tools.swarm_handoff import HandoffTarget, SwarmHandoff

        h = SwarmHandoff()
        h.request_handoff(
            from_agent="general",
            to_target=HandoffTarget.BROWSER,
            context={"task": "browse github"},
            reason="browser intent",
        )
        pending = h.get_pending_handoff()
        assert pending is not None
        assert pending.target == HandoffTarget.BROWSER

    def test_handoff_history(self):
        from tools.swarm_handoff import HandoffTarget, SwarmHandoff

        h = SwarmHandoff()
        h.request_handoff(
            "a", HandoffTarget.CODING, {}, "reason1"
        )
        h.request_handoff(
            "b", HandoffTarget.RESEARCH, {}, "reason2"
        )
        history = h.get_handoff_history()
        assert len(history) == 2


class TestSWEBridge:
    """REPO #5: SWE-agent bridge."""

    def test_parse_github_issue_valid(self):
        from tools.swe_agent_bridge import parse_github_issue

        owner, repo, num = parse_github_issue(
            "https://github.com/princeton-nlp/SWE-agent/issues/123"
        )
        assert owner == "princeton-nlp"
        assert repo == "SWE-agent"
        assert num == 123

    def test_parse_github_issue_invalid(self):
        from tools.swe_agent_bridge import parse_github_issue

        with pytest.raises(ValueError, match="Invalid GitHub issue URL"):
            parse_github_issue("https://notgithub.com/owner/repo/issues/1")
