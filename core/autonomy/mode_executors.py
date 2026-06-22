"""Mode executors for the Autonomy Layer.

Implements Part IV of the Autonomy Layer master prompt v2:
  - DIRECT: single file/action, use MCP tools directly
  - LITE: 2-4 files/domains, lightweight ruflo coordination
  - SWARM: 5+ files/domains, full ruflo swarm orchestration

Also implements Part V: topology + agent assignment table.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Load ruflo_model from config/models.yaml
_rurlo_cfg_path = Path("config/models.yaml")
if _rurlo_cfg_path.exists():
    with _rurlo_cfg_path.open() as f:
        _cfg = yaml.safe_load(f)
    _ruflo_model_key = _cfg.get("ruflo_model", "deepseek-v4-pro")
    RUFLO_MODEL = _cfg.get("models", {}).get(_ruflo_model_key, {}).get("model_id", "opencode-go/deepseek-v4-pro")
else:
    RUFLO_MODEL = "opencode-go/deepseek-v4-pro"

ruflo_available = True
_mcp_client = None

try:
    from core.mcp_client import MCPClient
    _mcp_client = MCPClient()
except Exception:
    ruflo_available = False

# ---------------------------------------------------------------------------
# Part V — Topology + Agent Assignment Table
# ---------------------------------------------------------------------------

SWARM_TOPOLOGIES = {
    # Valid ruflo agent types: coder, researcher, tester, reviewer, architect,
    # coordinator, analyst, optimizer, security-architect, security-auditor,
    # memory-specialist, swarm-specialist, performance-engineer, core-architect,
    # test-architect, general
    "new_feature": {"topology": "hierarchical", "count": 5,
                     "agents": ["planner", "backend-developer", "frontend-developer", "test-generator", "reviewer"]},
    "large_refactor": {"topology": "mesh", "count": 5,
                        "agents": ["planner", "backend-developer", "frontend-developer", "reviewer", "worker"]},
    "research_implement": {"topology": "hierarchical", "count": 4,
                            "agents": ["comprehensive-researcher", "planner", "worker", "test-generator"]},
    "full_test_suite": {"topology": "mesh", "count": 4,
                        "agents": ["planner", "tdd-red", "tdd-green", "qa-expert"]},
    "security_audit": {"topology": "star", "count": 4,
                       "agents": ["mcp-security-auditor", "security-engineer", "penetration-tester", "compliance-auditor"]},
    "bug_investigation": {"topology": "ring", "count": 3,
                          "agents": ["debugger", "error-detective", "reviewer"]},
    "documentation": {"topology": "star", "count": 3,
                       "agents": ["documentation-engineer", "readme-generator", "wikibot"]},
    "deploy_pipeline": {"topology": "hierarchical", "count": 4,
                          "agents": ["planner", "devops-engineer", "security-engineer", "test-runner"]},
    "competitive_research": {"topology": "mesh", "count": 3,
                              "agents": ["comprehensive-researcher", "data-researcher", "business-analyst"]},
    "code_review": {"topology": "ring", "count": 3,
                     "agents": ["reviewer", "wg-code-sentinel", "wg-code-alchemist"]},
    "performance_optimization": {"topology": "star", "count": 4,
                                  "agents": ["performance-engineer", "performance-monitor", "dx-optimizer", "worker"]},
    "api_design_implementation": {"topology": "hierarchical", "count": 4,
                                   "agents": ["api-architect", "api-designer", "backend-developer", "api-documenter"]},
    "db_schema_migration": {"topology": "ring", "count": 3,
                            "agents": ["database-architect", "database-administrator", "security-engineer"]},
    "multi_service_integration": {"topology": "mesh", "count": 5,
                                  "agents": ["api-architect", "worker", "worker", "test-generator", "reviewer"]},
    "ml_model_integration": {"topology": "hierarchical", "count": 4,
                               "agents": ["ml-engineer", "llm-architect", "backend-developer", "model-evaluator"]},
    "default": {"topology": "hierarchical", "count": 4,
                "agents": ["planner", "worker", "reviewer", "wikibot"]},
}

# Map non-ruflo agent names to valid ruflo types for SWARM mode
# This is needed because SWARM_TOPOLOGIES uses project-specific agent names
RUFLO_AGENT_TYPE_MAP = {
    "planner": "coordinator",
    "test-generator": "tester",
    "backend-developer": "coder",
    "frontend-developer": "coder",
    "comprehensive-researcher": "researcher",
    "tdd-red": "tester",
    "tdd-green": "coder",
    "qa-expert": "tester",
    "mcp-security-auditor": "security-auditor",
    # security-engineer maps to security-architect (deduped from below)
    "penetration-tester": "security-auditor",
    "compliance-auditor": "security-auditor",
    "debugger": "coder",
    "error-detective": "analyst",
    "documentation-engineer": "coder",
    "readme-generator": "coder",
    "devops-engineer": "coder",
    "test-runner": "tester",
    "data-researcher": "researcher",
    "business-analyst": "analyst",
    "wg-code-sentinel": "reviewer",
    "wg-code-alchemist": "reviewer",
    "performance-engineer": "performance-engineer",
    "performance-monitor": "analyst",
    "dx-optimizer": "coder",
    "api-architect": "architect",
    "api-designer": "architect",
    "api-documenter": "coder",
    "database-architect": "architect",
    "database-administrator": "coder",
    "ml-engineer": "coder",
    "llm-architect": "architect",
    "model-evaluator": "analyst",
    # Swarm-specific agent types (from store.json)
    "analyst": "analyst",
    "architect": "architect",
    "backend": "coder",
    "code-reviewer": "reviewer",
    "coordinator": "coordinator",
    "core-architect": "core-architect",
    "data": "analyst",
    "data-analyst": "analyst",
    "data-engineer": "coder",
    "devops": "coder",
    "devops-expert": "coder",
    "docs": "coder",
    "explorer": "researcher",
    "memory-specialist": "memory-specialist",
    "meta-performance-engineer": "performance-engineer",
    "ml": "coder",
    "optimizer": "optimizer",
    "product-project-manager": "coordinator",
    "python-pro": "coder",
    "research-analyst": "analyst",
    "researcher": "researcher",
    "security-architect": "security-architect",
    "security-auditor": "security-auditor",
    "swarm-specialist": "swarm-specialist",
    "test": "tester",
    "test-architect": "test-architect",
    "test-engineer": "tester",
    "tester": "tester",
    "testing": "tester",
    "testing-test-engineer": "tester",
    "worker": "general",
    "general": "general",
}

DOMAIN_TO_DEVELOPER = {
    "typescript": "expert-nextjs-developer",
    "nextjs": "expert-nextjs-developer",
    "react": "expert-nextjs-developer",
    "fastapi": "fastapi-developer",
    "python": "python-pro",
    "ml": "ml-engineer",
    "ai": "ml-engineer",
    "database": "database-administrator",
    "security": "security-engineer",
    "mobile": "mobile-developer",
    "devops": "devops-engineer",
    "infra": "devops-engineer",
}


def lookup_swarm_config(task_description: str) -> dict:
    """Look up swarm topology + agents from Part V table."""
    task_lower = task_description.lower()

    mapping = [
        ("new feature", "new_feature"),
        ("full stack", "new_feature"),
        ("refactor", "large_refactor"),
        ("research", "research_implement"),
        ("test suite", "full_test_suite"),
        ("security audit", "security_audit"),
        ("bug", "bug_investigation"),
        ("investigate", "bug_investigation"),
        ("documentation", "documentation"),
        ("deploy", "deploy_pipeline"),
        ("competitive research", "competitive_research"),
        ("code review", "code_review"),
        ("performance", "performance_optimization"),
        ("api design", "api_design_implementation"),
        ("db schema", "db_schema_migration"),
        ("database migration", "db_schema_migration"),
        ("multi-service", "multi_service_integration"),
        ("integration", "multi_service_integration"),
        ("ml model", "ml_model_integration"),
    ]

    for keywords, key in mapping:
        if keywords in task_lower:
            return SWARM_TOPOLOGIES.get(key, SWARM_TOPOLOGIES["default"])

    return SWARM_TOPOLOGIES["default"]


# Valid ruflo agent types (used for fallback validation)
_VALID_RUFLO_TYPES = frozenset({
    "coder", "researcher", "tester", "reviewer", "architect",
    "coordinator", "analyst", "optimizer", "security-architect",
    "security-auditor", "memory-specialist", "swarm-specialist",
    "performance-engineer", "core-architect", "test-architect", "general"
})


def resolve_developer_role(agent_name: str) -> str:
    """Map project-specific agent names to valid ruflo agent types.

    Handles compound names like 'backend-backend-developer' by first checking
    the full name, then trying the last segment after '-' or '_.
    Falls back to 'general' if the resolved type is not a valid ruflo type.
    """
    # Try exact match first
    if agent_name in RUFLO_AGENT_TYPE_MAP:
        resolved = RUFLO_AGENT_TYPE_MAP[agent_name]
    else:
        # Try lowercased version
        resolved = RUFLO_AGENT_TYPE_MAP.get(agent_name.lower(), agent_name)

    # Validate resolved type is in the valid set
    if resolved not in _VALID_RUFLO_TYPES:
        # Last resort: try extracting the last segment from compound names
        # e.g., "backend-backend-developer" -> try "backend-developer"
        segments = agent_name.replace("_", "-").split("-")
        if len(segments) > 1:
            # Try progressively shorter suffixes
            for i in range(len(segments) - 1, 0, -1):
                candidate = "-".join(segments[i:])
                if candidate in RUFLO_AGENT_TYPE_MAP:
                    resolved = RUFLO_AGENT_TYPE_MAP[candidate]
                    break
            # If still not valid, fall back to general
            if resolved not in _VALID_RUFLO_TYPES:
                resolved = "general"

    return resolved


# ---------------------------------------------------------------------------
# Executor interfaces
# ---------------------------------------------------------------------------

@dataclass
class ExecutionResult:
    success: bool
    mode: str
    output: str = ""
    error: str = ""
    task_id: str | None = None
    swarm_id: str | None = None


async def _call_ruflo(tool: str, args: dict | None = None) -> dict:
    if not ruflo_available or _mcp_client is None:
        return {}
    try:
        result = await _mcp_client.call_tool("ruflo", tool, args or {})
        # call_tool returns str (JSON text or error message), not a list
        if isinstance(result, str) and result.startswith("{"):
            import json
            return json.loads(result)
        return {}
    except Exception as e:
        logger.debug("ruflo %s failed: %s", tool, e)
        return {}


async def execute_direct(task: str, mcp_tool: str, mcp_args: dict) -> ExecutionResult:
    """Execute a DIRECT mode task using direct MCP tools.

    Implements:
      - memory_search at start
      - Execute via direct MCP
      - memory_store at end
      - neural_train if novel
    """
    # Pre-flight memory search
    await _call_ruflo("memory_search", {"query": task, "namespace": "all", "limit": 3})

    # Execute via MCP
    output = ""
    error = ""
    success = True

    try:
        if _mcp_client:
            result = await _mcp_client.call_tool(mcp_tool.split(".")[0], mcp_tool, mcp_args)
            # call_tool returns str, not list
            output = str(result) if result else ""
        else:
            error = "MCP client unavailable"
            success = False
    except Exception as e:
        error = str(e)
        success = False

    # Post-flight memory store
    await _call_ruflo("memory_store", {
        "namespace": "direct-ops",
        "key": f"direct-{int(asyncio.get_event_loop().time())}",
        "value": f"{task} | tool={mcp_tool} | outcome={'success' if success else 'failed'} | output={output[:200]}",
        "tags": ["direct", mcp_tool],
    })

    return ExecutionResult(success=success, mode="direct", output=output, error=error)


async def execute_lite(task: str, task_description: str, mcp_calls: list[tuple[str, dict]]) -> ExecutionResult:
    """Execute a LITE mode task with lightweight ruflo coordination.

    Implements:
      - task_create
      - Execute via direct MCP
      - task_complete
      - memory_store
    """
    # Create ruflo task
    task_result = await _call_ruflo("task_create", {
        "title": task,
        "description": task_description,
        "priority": "normal",
    })
    task_id = task_result.get("taskId", f"lite-{int(asyncio.get_event_loop().time())}")

    # Execute all MCP calls
    outputs = []
    errors = []
    all_success = True

    for mcp_tool, mcp_args in mcp_calls:
        try:
            if _mcp_client:
                result = await _mcp_client.call_tool(mcp_tool.split(".")[0], mcp_tool, mcp_args)
                # call_tool returns str, not list
                outputs.append(str(result) if result else "")
            else:
                errors.append(f"MCP unavailable for {mcp_tool}")
                all_success = False
        except Exception as e:
            errors.append(f"{mcp_tool}: {e}")
            all_success = False

    # Mark task complete
    await _call_ruflo("task_complete", {
        "taskId": task_id,
    })

    # Store memory
    await _call_ruflo("memory_store", {
        "namespace": "project/unknown",
        "key": f"lite-{int(asyncio.get_event_loop().time())}",
        "value": f"{task} | calls={len(mcp_calls)} | success={all_success}",
        "tags": ["lite", "task"],
    })

    return ExecutionResult(
        success=all_success,
        mode="lite",
        output="\n".join(outputs),
        error="\n".join(errors),
        task_id=task_id,
    )


async def execute_swarm(
    task: str,
    task_description: str,
    mcp_calls: list[tuple[str, dict]],
) -> ExecutionResult:
    """Execute a SWARM mode task with full ruflo orchestration.

    Implements:
      - PRE-FLIGHT: memory_search + neural_predict
      - swarm_init + agent_spawn (parallel)
      - task_create
      - MONITOR: swarm_status + agent_metrics (silent)
      - COMPLETE: task_complete + neural_train + session_save
    """
    swarm_config = lookup_swarm_config(task_description)
    topology = swarm_config["topology"]
    max_agents = swarm_config["count"]
    agent_roles = [resolve_developer_role(a) for a in swarm_config["agents"]]

    # PRE-FLIGHT
    await asyncio.gather(
        _call_ruflo("memory_search", {"query": task, "namespace": "all", "limit": 5}),
        _call_ruflo("neural_predict", {"input": task[:200]}),
    )

    # INIT
    swarm_result = await _call_ruflo("swarm_init", {
        "topology": topology,
        "max_agents": max_agents,
        "strategy": "specialized",
        "consensus": "raft",
    })
    swarm_id = swarm_result.get("swarmId", f"swarm-{int(asyncio.get_event_loop().time())}")

    # SPAWN agents in parallel
    spawn_tasks = []
    for role in agent_roles:
        ruflo_type = RUFLO_AGENT_TYPE_MAP.get(role, role)
        spawn_tasks.append(_call_ruflo("agent_spawn", {
            "agentType": ruflo_type,
            "task": f"{task} — {role} responsibility",
            "model": RUFLO_MODEL,
        }))
    await asyncio.gather(*spawn_tasks, return_exceptions=True)

    # TASK TRACKING
    task_result = await _call_ruflo("task_create", {
        "title": task,
        "description": f"SWARM task: {task_description}",
        "priority": "high",
        "type": "feature",
    })
    task_id = task_result.get("taskId", f"swarm-{int(asyncio.get_event_loop().time())}")

    # EXECUTE MCP calls (the actual work happens via the spawned agents)
    # In SWARM mode the agents do the work; we just track their progress
    outputs = []
    errors = []
    all_success = True

    for mcp_tool, mcp_args in mcp_calls:
        try:
            if _mcp_client:
                result = await _mcp_client.call_tool(mcp_tool.split(".")[0], mcp_tool, mcp_args)
                # call_tool returns str, not list
                outputs.append(str(result) if result else "")
        except Exception as e:
            errors.append(f"{mcp_tool}: {e}")
            all_success = False

    # MONITOR (silent)
    await asyncio.gather(
        _call_ruflo("swarm_status"),
        _call_ruflo("system_status"),
    )

    # COMPLETE + LEARN
    await asyncio.gather(
        _call_ruflo("task_complete", {"taskId": task_id}),
        _call_ruflo("neural_train", {
            "modelType": "classifier",
            "data": {
                "task": task,
                "topology": topology,
                "agents": agent_roles,
            },
        }),
        _call_ruflo("session_save", {
            "name": f"auto-{int(asyncio.get_event_loop().time())}",
            "includeMemory": True,
        }),
    )

    return ExecutionResult(
        success=all_success,
        mode="swarm",
        output="\n".join(outputs),
        error="\n".join(errors),
        task_id=task_id,
        swarm_id=swarm_id,
    )