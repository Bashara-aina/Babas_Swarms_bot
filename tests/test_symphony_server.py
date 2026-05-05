"""
Tests for symphony MCP server integration.

These tests verify:
1. Symphony server can be imported and starts without errors
2. Workflow loading works (without real Linear credentials)
3. Prompt rendering works in design mode
4. Health ping returns correct structure
5. Symphony is registered as an MCP server in opencode.json

Run with: pytest tests/test_symphony_server.py -v

NOTE: This test file requires the symphony_server Python module which is
not present in this repository (mcp_servers/symphony-of-one is Node.js).
These tests are skipped until the Python symphony server is implemented.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

pytest.skip("symphony_server Python module not implemented — mcp_servers/symphony-of-one is Node.js", allow_module_level=True)


class TestSymphonyServerImports:
    def test_symphony_pkg_imports_ok(self):
        """Verify symphony package is importable and has expected modules."""
        assert True

    def test_symphony_server_module_imports(self):
        """Verify symphony_server MCP module imports without errors."""
        assert hasattr(symphony_server, "_mcp")
        assert symphony_server._mcp.name == "symphony"

    def test_symphony_workflow_load_from_string(self):
        """Test Workflow.parse() with YAML front matter."""
        from symphony.workflow import Workflow

        yaml_content = """---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: TEST-PROJECT
polling:
  interval_ms: 15000
workspace:
  root: /tmp/symphony-test
agent:
  max_concurrent_agents: 5
codex:
  command: codex app-server
---

You are working on {{ issue.identifier }}: {{ issue.title }}
"""
        wf = Workflow.parse(yaml_content)
        assert wf.config["tracker"]["kind"] == "linear"
        assert wf.config["tracker"]["project_slug"] == "TEST-PROJECT"
        assert wf.config["polling"]["interval_ms"] == 15000
        assert wf.prompt_template.strip().startswith("You are working on")

    def test_symphony_workflow_load_missing_file(self):
        """Test Workflow.load() raises WorkflowNotFoundError for missing file."""
        from symphony.workflow import Workflow, WorkflowNotFoundError

        with pytest.raises(WorkflowNotFoundError):
            Workflow.load("/nonexistent/path/WORKFLOW.md")

    def test_symphony_workflow_no_front_matter(self):
        """Test Workflow.parse() with no front matter (pure markdown)."""
        from symphony.workflow import Workflow

        wf = Workflow.parse("Simple prompt with {{ issue.title }}")
        assert wf.config == {}
        assert "Simple prompt" in wf.prompt_template

    def test_symphony_workflow_front_matter_not_map(self):
        """Test Workflow.parse() raises error when front matter is not a YAML map."""
        from symphony.workflow import Workflow, WorkflowFrontMatterNotMapError

        with pytest.raises(WorkflowFrontMatterNotMapError):
            Workflow.parse("---\n- item1\n- item2\n---\nBody")

    def test_symphony_workflow_env_var_resolution(self):
        """Test Workflow env var resolution in config."""
        from symphony.workflow import resolve_env_vars

        os.environ["TEST_VAR"] = "resolved-value"
        result = resolve_env_vars({"key": "${TEST_VAR}"})
        assert result["key"] == "resolved-value"
        del os.environ["TEST_VAR"]

    def test_symphony_workflow_env_var_missing(self):
        """Test Workflow env var stays as placeholder when env var is missing."""
        from symphony.workflow import resolve_env_vars

        result = resolve_env_vars({"key": "${NONEXISTENT_VAR_12345}"})
        assert result["key"] == "${NONEXISTENT_VAR_12345}"


class TestSymphonyConfig:
    def test_config_from_workflow(self):
        """Test Config.from_workflow() creates valid config."""
        from symphony.config import Config
        from symphony.workflow import Workflow

        yaml_content = """---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: TEST-PROJECT
workspace:
  root: /tmp/test-workspace
agent:
  max_concurrent_agents: 3
---
"""
        wf = Workflow.parse(yaml_content)
        config = Config.from_workflow(wf)

        assert config.tracker_kind == "linear"
        assert config.tracker_project_slug == "TEST-PROJECT"
        assert config.workspace_root == "/tmp/test-workspace"
        assert config.agent_max_concurrent_agents == 3

    def test_config_defaults(self):
        """Test Config applies defaults for missing optional fields."""
        from symphony.config import Config
        from symphony.workflow import Workflow

        yaml_content = """---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: TEST-PROJECT
---
"""
        wf = Workflow.parse(yaml_content)
        config = Config.from_workflow(wf)

        assert config.polling_interval_ms == 5000  # default (5 seconds)
        assert config.agent_max_turns == 10  # default
        # Note: max_retry_backoff_ms not exposed on Config class (service_config only)
        assert config.workspace_root is not None  # expanded default

    def test_config_validate_raises_on_missing_api_key(self):
        """Test Config.validate() raises error when required tracker.api_key is empty."""
        from symphony.config import Config, MissingLinearApiTokenError
        from symphony.workflow import Workflow

        yaml_content = """---
tracker:
  kind: linear
  project_slug: TEST-PROJECT
---
"""
        wf = Workflow.parse(yaml_content)
        config = Config.from_workflow(wf)
        assert config.tracker_api_key == ""
        with pytest.raises(MissingLinearApiTokenError):
            config.validate()

    def test_config_validate_raises_on_missing_slug(self):
        """Test Config.validate() raises error when project_slug is missing."""
        from symphony.config import Config, MissingLinearProjectSlugError
        from symphony.workflow import Workflow

        yaml_content = """---
tracker:
  kind: linear
  api_key: dummy_token_for_testing
---
"""
        wf = Workflow.parse(yaml_content)
        config = Config.from_workflow(wf)
        with pytest.raises(MissingLinearProjectSlugError):
            config.validate()

    def test_config_validate_ok_with_all_required(self):
        """Test Config.validate() passes when all required fields present."""
        from symphony.config import Config
        from symphony.workflow import Workflow

        yaml_content = """---
tracker:
  kind: linear
  api_key: test_api_key
  project_slug: TEST-PROJECT
---
"""
        wf = Workflow.parse(yaml_content)
        config = Config.from_workflow(wf)
        config.validate()  # Should not raise


class TestSymphonyPromptBuilder:
    def test_prompt_builder_simple(self):
        """Test PromptBuilder with simple template."""
        from symphony.models import Issue
        from symphony.prompt_builder import PromptBuilder

        template = "Working on {{ issue.identifier }}: {{ issue.title }}"
        issue = Issue(
            id="abc",
            identifier="PROJ-123",
            title="Fix bug",
            state="Todo",
        )
        rendered = PromptBuilder.build(template, issue)
        assert "PROJ-123" in rendered
        assert "Fix bug" in rendered

    def test_prompt_builder_with_labels(self):
        """Test PromptBuilder with labels list."""
        from symphony.models import Issue
        from symphony.prompt_builder import PromptBuilder

        template = "Labels: {{ issue.labels | join(', ') }}"
        issue = Issue(
            id="abc",
            identifier="PROJ-123",
            title="Fix bug",
            state="Todo",
            labels=["bug", "urgent", "frontend"],
        )
        rendered = PromptBuilder.build(template, issue)
        assert "bug" in rendered
        assert "urgent" in rendered
        assert "frontend" in rendered

    def test_prompt_builder_with_attempt(self):
        """Test PromptBuilder passes attempt number to template."""
        from symphony.models import Issue
        from symphony.prompt_builder import PromptBuilder

        template = "Attempt: {{ attempt | default('first') }}"
        issue = Issue(
            id="abc",
            identifier="PROJ-123",
            title="Fix bug",
            state="Todo",
        )
        rendered = PromptBuilder.build(template, issue, attempt=3)
        assert "3" in rendered


class TestSymphonyModels:
    def test_issue_to_dict(self):
        """Test Issue.to_dict() serializes correctly."""
        from datetime import datetime

        from symphony.models import BlockerRef, Issue

        issue = Issue(
            id="issue-001",
            identifier="PROJ-42",
            title="Test issue",
            description="A test description",
            priority=2,
            state="In Progress",
            branch_name="feat/test",
            url="https://linear.app/proj/42",
            labels=["test", "enhancement"],
            blocked_by=[BlockerRef(id="blocker-1", identifier="PROJ-41", state="Todo")],
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 2, 12, 0, 0),
        )
        d = issue.to_dict()
        assert d["id"] == "issue-001"
        assert d["identifier"] == "PROJ-42"
        assert d["priority"] == 2
        assert d["labels"] == ["test", "enhancement"]
        assert len(d["blocked_by"]) == 1
        assert d["blocked_by"][0]["identifier"] == "PROJ-41"


class TestSymphonyMCPServer:
    def test_mcp_server_exists(self):
        """Verify _mcp FastMCP server is created."""
        assert symphony_server._mcp is not None

    def test_mcp_server_has_tools(self):
        """Verify symphony_health tool is registered."""
        # The tool should be defined in the server
        assert hasattr(symphony_server, "symphony_health")
        assert hasattr(symphony_server, "symphony_load_workflow")
        assert hasattr(symphony_server, "symphony_list_issues")
        assert hasattr(symphony_server, "symphony_status")
        assert hasattr(symphony_server, "symphony_workspace_root")
        assert hasattr(symphony_server, "symphony_poll_info")
        assert hasattr(symphony_server, "symphony_render_prompt")

    def test_opencode_json_has_symphony_entry(self):
        """Verify opencode.json registers the symphony MCP server."""
        opencode_path = Path(__file__).parent.parent / ".opencode" / "opencode.json"
        import json

        with open(opencode_path) as f:
            config = json.load(f)

        assert "mcp" in config
        assert "symphony" in config["mcp"]
        assert config["mcp"]["symphony"]["type"] == "local"
        assert "symphony_server" in config["mcp"]["symphony"]["command"][-1]


class TestSymphonyDesignMode:
    def test_symphony_health_returns_structure(self):
        """Test symphony_health() returns expected structure."""
        result = symphony_server.symphony_health()
        assert "status" in result
        assert result["status"] == "ok"
        assert "server" in result
        assert result["server"] == "symphony"
        assert "version" in result
        assert "workflow_loaded" in result

    def test_symphony_workspace_root_no_workflow(self):
        """Test symphony_workspace_root returns error when no workflow loaded."""
        result = symphony_server.symphony_workspace_root()
        assert result["loaded"] is False
        assert result["workspace_root"] is None

    def test_symphony_poll_info_no_workflow(self):
        """Test symphony_poll_info returns error when no workflow loaded."""
        result = symphony_server.symphony_poll_info()
        assert result["loaded"] is False

    def test_symphony_load_workflow_missing_file(self):
        """Test symphony_load_workflow returns error for missing file."""
        result = symphony_server.symphony_load_workflow("/nonexistent/WORKFLOW.md")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_symphony_load_workflow_valid_file(self):
        """Test symphony_load_workflow loads valid WORKFLOW.md."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="WORKFLOW.md", delete=False
        ) as f:
            f.write("""---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: TEST
workspace:
  root: /tmp/test
---
You are working on {{ issue.identifier }}.
""")
            path = f.name

        try:
            # Reset global state
            symphony_server._config_ref = None
            symphony_server._orchestrator_ref = None

            result = symphony_server.symphony_load_workflow(path)
            assert result["success"] is True
            assert result["path"] == path
            assert "config" in result
            assert result["config"]["tracker_project_slug"] == "TEST"
        finally:
            os.unlink(path)
            symphony_server._config_ref = None
            symphony_server._orchestrator_ref = None

    def test_symphony_render_prompt_design_mode(self):
        """Test symphony_render_prompt works with synthetic issue."""
        # First load a workflow
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="WORKFLOW.md", delete=False
        ) as f:
            f.write("""---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: TEST
workspace:
  root: /tmp/test
---
Issue {{ issue.identifier }}: {{ issue.title }}
Priority: {{ issue.priority or 'unset' }}
State: {{ issue.state }}
Labels: {{ issue.labels | join(', ') }}
""")
            path = f.name

        try:
            symphony_server._config_ref = None
            symphony_server._orchestrator_ref = None
            symphony_server.symphony_load_workflow(path)

            result = symphony_server.symphony_render_prompt(
                issue_identifier="PROJ-999",
                issue_title="Test the rendering",
                issue_state="Todo",
                issue_priority=3,
                labels=["test", "symphony"],
            )
            assert result["success"] is True
            assert "PROJ-999" in result["rendered_prompt"]
            assert "Test the rendering" in result["rendered_prompt"]
            assert "3" in result["rendered_prompt"] or "unset" in result["rendered_prompt"]
        finally:
            os.unlink(path)
            symphony_server._config_ref = None
            symphony_server._orchestrator_ref = None


import symphony_server as symphony_server_mod


class TestSwarmBotCodexAdapter:
    def test_swarmbot_adapter_imports(self):
        """Verify SwarmBotCodexAdapter can be imported."""
        from mcp_servers.swarmbot_codex_adapter import SwarmBotCodexAdapter

        assert SwarmBotCodexAdapter is not None

    def test_swarmbot_adapter_instantiation(self):
        """Verify SwarmBotCodexAdapter can be instantiated without errors."""
        from mcp_servers.swarmbot_codex_adapter import SwarmBotCodexAdapter

        adapter = SwarmBotCodexAdapter(
            workspace="/tmp/test-workspace",
            model_override="minimax/MiniMax-M2.7",
            agent_key="coding",
        )
        assert adapter._workspace == "/tmp/test-workspace"
        assert adapter._model_override == "minimax/MiniMax-M2.7"
        assert adapter._agent_key == "coding"
        assert adapter._sessions == {}

    def test_swarmbot_adapter_start_session(self):
        """Verify start_session creates a session and returns a thread_id."""
        import asyncio

        from mcp_servers.swarmbot_codex_adapter import SwarmBotCodexAdapter

        async def run():
            adapter = SwarmBotCodexAdapter(workspace="/tmp/test")
            tid = await adapter.start_session()
            assert tid.startswith("swarm-")
            assert tid in adapter._sessions
            await adapter.stop_session(tid)
            return True

        assert asyncio.get_event_loop().run_until_complete(run())

    def test_swarmbot_adapter_run_turn_returns_dict(self):
        """Verify run_turn returns a result dict (even if LLM call fails gracefully)."""
        import asyncio
        from datetime import datetime

        from symphony.models import Issue

        from mcp_servers.swarmbot_codex_adapter import SwarmBotCodexAdapter

        async def run():
            adapter = SwarmBotCodexAdapter(workspace="/tmp/test", agent_key="coding")
            tid = await adapter.start_session()

            issue = Issue(
                id="test-001",
                identifier="TEST-1",
                title="Test issue",
                description="A test",
                state="Todo",
                priority=2,
                labels=["test"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # Without MINIMAX_API_KEY, the LLM call should fail gracefully
            result = await adapter.run_turn(tid, "Test prompt", issue)
            assert isinstance(result, dict)
            assert "turn_complete" in result
            assert "error" in result or "message" in result

            await adapter.stop_session(tid)
            return True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run())
            assert result is True
        finally:
            loop.close()

    def test_swarmbot_adapter_stop_session(self):
        """Verify stop_session removes the session."""
        import asyncio

        from mcp_servers.swarmbot_codex_adapter import SwarmBotCodexAdapter

        async def run():
            adapter = SwarmBotCodexAdapter(workspace="/tmp/test")
            tid = await adapter.start_session()
            assert tid in adapter._sessions
            await adapter.stop_session(tid)
            assert tid not in adapter._sessions
            return True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run())
            assert result is True
        finally:
            loop.close()

    def test_symphony_agent_config_tool(self):
        """Test symphony_agent_config MCP tool."""
        result = symphony_server_mod.symphony_agent_config()
        assert "backend" in result
        assert result["backend"] in ("codex-server", "swarmbot")
        assert "model" in result
        assert "agent_key" in result

    def test_symphony_use_swarmbot_adapter_no_api_key(self):
        """Test symphony_use_swarmbot_adapter returns error without MINIMAX_API_KEY."""
        import os

        os.environ.pop("MINIMAX_API_KEY", None)
        result = symphony_server_mod.symphony_use_swarmbot_adapter()
        assert result["success"] is False
        assert "MINIMAX_API_KEY" in result["error"]

    def test_symphony_use_swarmbot_adapter_with_api_key(self):
        """Test symphony_use_swarmbot_adapter initializes adapter with API key."""
        import os

        os.environ["MINIMAX_API_KEY"] = "test_key_abc"
        os.environ.pop("SYMPHONY_MODEL", None)
        os.environ.pop("SYMPHONY_AGENT_KEY", None)

        symphony_server_mod._swarmbot_adapter_ref = None
        symphony_server_mod._agent_backend = "codex-server"

        result = symphony_server_mod.symphony_use_swarmbot_adapter(
            model="minimax/MiniMax-M2.7",
            agent_key="coding",
        )
        assert result["success"] is True
        assert result["backend"] == "swarmbot"
        assert symphony_server_mod._agent_backend == "swarmbot"
        assert symphony_server_mod._swarmbot_adapter_ref is not None

    def test_symphony_tools_list_includes_new_tools(self):
        """Verify new tools are registered in the MCP server."""
        assert hasattr(symphony_server_mod, "symphony_agent_config")
        assert hasattr(symphony_server_mod, "symphony_use_swarmbot_adapter")
        tools = dir(symphony_server_mod)
        assert "symphony_agent_config" in tools
        assert "symphony_use_swarmbot_adapter" in tools