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
from typing import Any

logger = logging.getLogger(__name__)

RUFLO_MODEL = "minimax/MiniMax-M2.7"

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


def resolve_developer_role(agent_name: str) -> str:
    """Map generic developer roles to project-specific specialists."""
    agent_lower = agent_name.lower()
    for domain, developer in DOMAIN_TO_DEVELOPER.items():
        if domain in agent_lower:
            return developer
    return agent_name


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
        if isinstance(result, list) and len(result) > 0:
            import json
            return json.loads(result[0].text)
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
            if isinstance(result, list):
                output = "\n".join(r.text if hasattr(r, "text") else str(r) for r in result)
            else:
                output = str(result)
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
    task_id = task_result.get("task_id", f"lite-{int(asyncio.get_event_loop().time())}")

    # Execute all MCP calls
    outputs = []
    errors = []
    all_success = True

    for mcp_tool, mcp_args in mcp_calls:
        try:
            if _mcp_client:
                result = await _mcp_client.call_tool(mcp_tool.split(".")[0], mcp_tool, mcp_args)
                if isinstance(result, list):
                    outputs.append("\n".join(r.text if hasattr(r, "text") else str(r) for r in result))
                else:
                    outputs.append(str(result))
            else:
                errors.append(f"MCP unavailable for {mcp_tool}")
                all_success = False
        except Exception as e:
            errors.append(f"{mcp_tool}: {e}")
            all_success = False

    # Mark task complete
    await _call_ruflo("task_complete", {
        "task_id": task_id,
        "result": "success" if all_success else "partial",
    })

    # Store memory
    files_changed = [str(a.get("path", "")) for a in mcp_args if isinstance(a, dict)]
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
        _call_ruflo("neural_predict", {"context": task[:200], "pattern_type": "task"}),
    )

    # INIT
    swarm_result = await _call_ruflo("swarm_init", {
        "topology": topology,
        "max_agents": max_agents,
        "strategy": "specialized",
        "consensus": "raft",
    })
    swarm_id = swarm_result.get("swarm", {}).get("id", f"swarm-{int(asyncio.get_event_loop().time())}")

    # SPAWN agents in parallel
    spawn_tasks = []
    for role in agent_roles:
        spawn_tasks.append(_call_ruflo("agent_spawn", {
            "agent_type": role,
            "task": f"{task} — {role} responsibility",
            "model": RUFLO_MODEL,
        }))
    spawn_results = await asyncio.gather(*spawn_tasks, return_exceptions=True)

    # TASK TRACKING
    task_result = await _call_ruflo("task_create", {
        "title": task,
        "agent_id": swarm_id,
        "priority": "high",
    })
    task_id = task_result.get("task_id", f"swarm-{int(asyncio.get_event_loop().time())}")

    # EXECUTE MCP calls (the actual work happens via the spawned agents)
    # In SWARM mode the agents do the work; we just track their progress
    outputs = []
    errors = []
    all_success = True

    for mcp_tool, mcp_args in mcp_calls:
        try:
            if _mcp_client:
                result = await _mcp_client.call_tool(mcp_tool.split(".")[0], mcp_tool, mcp_args)
                if isinstance(result, list):
                    outputs.append("\n".join(r.text if hasattr(r, "text") else str(r) for r in result))
                else:
                    outputs.append(str(result))
        except Exception as e:
            errors.append(f"{mcp_tool}: {e}")
            all_success = False

    # MONITOR (silent)
    await asyncio.gather(
        _call_ruflo("swarm_status"),
        _call_ruflo("agent_metrics"),
    )

    # COMPLETE + LEARN
    await asyncio.gather(
        _call_ruflo("task_complete", {"task_id": task_id, "result": "success"}),
        _call_ruflo("neural_train", {
            "pattern_type": "task",
            "data": f"{task} | topology={topology} | agents={agent_roles}",
            "epochs": 10,
        }),
        _call_ruflo("session_save", {
            "name": f"auto-{int(asyncio.get_event_loop().time())}",
            "include_memory": True,
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