#!/usr/bin/env python3
"""
DelegateOrchestrator — Hierarchical 3-tier delegation: coordinator → specialist → worker.
Coordinator analyzes task, breaks into subtasks, assigns to specialists.
Each specialist owns a domain (code, web, file, research), spawns workers.
Workers execute specific micro-tasks.
"""
import asyncio
import json
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Level Enums ─────────────────────────────────────────────────────────────

class HierarchyLevel(Enum):
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    WORKER = "worker"

# ── Agent State ───────────────────────────────────────────────────────────────

@dataclass
class AgentState:
    agent_id: str
    name: str
    level: HierarchyLevel
    domain: str  # code, web, file, research
    status: str = "idle"  # idle, running, completed, failed
    parent_id: str = ""
    children: list[str] = field(default_factory=list)
    result: Any = None
    error: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0

# ── Hierarchy Registry ───────────────────────────────────────────────────────

_hierarchy_lock = threading.Lock()
_hierarchy: dict[str, AgentState] = {}

def _get_agent(agent_id: str) -> AgentState | None:
    return _hierarchy.get(agent_id)

def _register_agent(agent: AgentState) -> str:
    with _hierarchy_lock:
        _hierarchy[agent.agent_id] = agent
    return agent.agent_id

def _update_agent(agent_id: str, **kwargs) -> bool:
    with _hierarchy_lock:
        if agent_id in _hierarchy:
            agent = _hierarchy[agent_id]
            for k, v in kwargs.items():
                if hasattr(agent, k):
                    setattr(agent, k, v)
            return True
    return False

def _all_agents() -> list[AgentState]:
    with _hierarchy_lock:
        return list(_hierarchy.values())

def spawn_coordinator(goal: str, coordinator_id: str = "") -> str:
    """Spawn a coordinator agent at the top level."""
    cid = coordinator_id or f"coordinator-{uuid.uuid4().hex[:8]}"
    agent = AgentState(
        agent_id=cid,
        name=cid,
        level=HierarchyLevel.COORDINATOR,
        domain="coordinator",
        status="running",
    )
    _register_agent(agent)
    return cid

def spawn_specialist(coordinator_id: str, domain: str, specialists_count: int = 1) -> list[str]:
    """Spawn specialist agents under a coordinator."""
    specialist_ids = []
    for i in range(specialists_count):
        sid = f"specialist-{domain}-{uuid.uuid4().hex[:8]}"
        agent = AgentState(
            agent_id=sid,
            name=sid,
            level=HierarchyLevel.SPECIALIST,
            domain=domain,
            status="running",
            parent_id=coordinator_id,
        )
        _register_agent(agent)
        specialist_ids.append(sid)
        with _hierarchy_lock:
            if coordinator_id in _hierarchy:
                _hierarchy[coordinator_id].children.append(sid)
    return specialist_ids

def spawn_worker(specialist_id: str, domain: str, workers_count: int = 1) -> list[str]:
    """Spawn worker agents under a specialist."""
    worker_ids = []
    for i in range(workers_count):
        wid = f"worker-{domain}-{uuid.uuid4().hex[:8]}"
        agent = AgentState(
            agent_id=wid,
            name=wid,
            level=HierarchyLevel.WORKER,
            domain=domain,
            status="running",
            parent_id=specialist_id,
        )
        _register_agent(agent)
        worker_ids.append(wid)
        with _hierarchy_lock:
            if specialist_id in _hierarchy:
                _hierarchy[specialist_id].children.append(wid)
    return worker_ids

# ── Goal Decomposition ────────────────────────────────────────────────────────

def _decompose_goal(goal: str) -> list[dict[str, Any]]:
    """Break a goal into subtasks based on keywords."""
    # Simple keyword-based decomposition
    subtasks = []
    goal_lower = goal.lower()

    if any(w in goal_lower for w in ["search", "research", "find", "look up"]):
        subtasks.append({"domain": "web", "action": "search", "description": f"Web search: {goal}"})
    if any(w in goal_lower for w in ["code", "implement", "build", "create function", "write"]):
        subtasks.append({"domain": "code", "action": "write", "description": f"Code implementation: {goal}"})
    if any(w in goal_lower for w in ["file", "read", "write", "edit", "modify"]):
        subtasks.append({"domain": "file", "action": "edit", "description": f"File operation: {goal}"})
    if any(w in goal_lower for w in ["analyze", "audit", "review", "evaluate", "check"]):
        subtasks.append({"domain": "research", "action": "analyze", "description": f"Analysis: {goal}"})
    if any(w in goal_lower for w in ["test", "run", "execute", "benchmark"]):
        subtasks.append({"domain": "code", "action": "test", "description": f"Testing: {goal}"})

    # Fallback: single general task
    if not subtasks:
        subtasks.append({"domain": "general", "action": "execute", "description": goal})

    return subtasks[:5]  # Max 5 subtasks

# ── Hierarchical Execution ────────────────────────────────────────────────────

MAX_WORKERS_PER_SPECIALIST = 5
MAX_SPECIALISTS = 5
BUDGET_TIMEOUT_PER_WORKER = 60  # seconds

@dataclass
class HierarchyResult:
    coordinator_id: str
    status: str
    total_time: float
    specialists: list[dict[str, Any]]
    errors: list[str]

def execute_hierarchy(coordinator_id: str, goal: str, max_specialists: int = 5,
                       max_workers_per_specialist: int = 5, max_time_per_worker: int = 60) -> HierarchyResult:
    """
    Execute 3-tier hierarchical delegation.
    Returns hierarchical result with status per level.
    """
    start_time = time.time()
    subtasks = _decompose_goal(goal)
    specialists_count = min(len(subtasks), max_specialists)
    subtasks = subtasks[:specialists_count]

    # Coordinator spawns specialists
    specialist_ids = spawn_specialist(coordinator_id, "general", specialists_count)

    # Each specialist spawns workers
    all_worker_ids = []
    for i, (sid, subtask) in enumerate(zip(specialist_ids, subtasks)):
        workers_needed = min(max_workers_per_specialist, 1)
        worker_ids = spawn_worker(sid, subtask["domain"], workers_needed)
        all_worker_ids.extend(worker_ids)
        _update_agent(sid, result=subtask)

    # Wait for all workers (simulated with timer threads)
    # In real implementation, these would be async subprocesses
    def _simulate_worker(wid: str, task: dict[str, Any]) -> dict[str, Any]:
        _update_agent(wid, status="completed", completed_at=time.time(), result={"domain": task["domain"], "description": task["description"]})
        return {"worker_id": wid, "status": "completed"}

    # Simulated completion
    for (sid, subtask), worker_ids in zip(zip(specialist_ids, subtasks), [all_worker_ids]):
        for wid in worker_ids:
            _simulate_worker(wid, subtask)
        _update_agent(sid, status="completed", completed_at=time.time())

    _update_agent(coordinator_id, status="completed", completed_at=time.time())

    # Gather results
    specialists_data = []
    errors = []
    for sid in specialist_ids:
        agent = _get_agent(sid)
        if agent:
            specialists_data.append({
                "specialist_id": sid,
                "domain": agent.domain,
                "status": agent.status,
                "result": agent.result,
                "workers": [c for c in agent.children],
            })
        if agent and agent.error:
            errors.append(agent.error)

    total_time = time.time() - start_time

    return HierarchyResult(
        coordinator_id=coordinator_id,
        status="completed",
        total_time=round(total_time, 2),
        specialists=specialists_data,
        errors=errors,
    )

def hierarchical_status(coordinator_id: str) -> dict[str, Any]:
    """Return hierarchical status report."""
    coord = _get_agent(coordinator_id)
    if not coord:
        return {"error": f"coordinator {coordinator_id} not found"}

    specialists = [a for a in _all_agents() if a.parent_id == coordinator_id and a.level == HierarchyLevel.SPECIALIST]
    all_workers = [a for a in _all_agents() if a.level == HierarchyLevel.WORKER and any(a.parent_id == s.agent_id for s in specialists)]

    return {
        "coordinator": {
            "id": coordinator_id,
            "status": coord.status,
            "started_at": coord.started_at,
        },
        "specialists": {
            "total": len(specialists),
            "active": len([s for s in specialists if s.status == "running"]),
            "completed": len([s for s in specialists if s.status == "completed"]),
        },
        "workers": {
            "total": len(all_workers),
            "active": len([w for w in all_workers if w.status == "running"]),
            "completed": len([w for w in all_workers if w.status == "completed"]),
        },
    }

def hierarchical_result_merge(coordinator_id: str) -> dict[str, Any]:
    """Aggregate all levels into single result."""
    coord = _get_agent(coordinator_id)
    if not coord:
        return {"error": "coordinator not found"}

    specialists = [a for a in _all_agents() if a.parent_id == coordinator_id and a.level == HierarchyLevel.SPECIALIST]

    merged = {
        "coordinator_id": coordinator_id,
        "total_result": {"domains": {}, "workers": 0},
    }

    for s in specialists:
        domain = s.domain or "general"
        if domain not in merged["total_result"]["domains"]:
            merged["total_result"]["domains"][domain] = []
        merged["total_result"]["domains"][domain].append({
            "specialist_id": s.agent_id,
            "result": s.result,
            "workers": [w for w in _all_agents() if w.parent_id == s.agent_id and w.level == HierarchyLevel.WORKER]
        })
        merged["total_result"]["workers"] += len(s.children)

    return merged

def handle_delegate_orchestrator(args: dict[str, Any]) -> str:
    """Handler for orchestrator operations."""
    action = args.get("action", "execute")
    if action == "spawn":
        cid = spawn_coordinator(args.get("goal", ""), args.get("coordinator_id", ""))
        result = {"coordinator_id": cid, "status": "spawned"}
    elif action == "execute":
        cid = spawn_coordinator(args.get("goal", ""))
        exec_result = execute_hierarchy(
            cid,
            args.get("goal", ""),
            args.get("max_specialists", MAX_SPECIALISTS),
            args.get("max_workers_per_specialist", MAX_WORKERS_PER_SPECIALIST),
            args.get("max_time_per_worker", BUDGET_TIMEOUT_PER_WORKER),
        )
        result = {
            "coordinator_id": exec_result.coordinator_id,
            "status": exec_result.status,
            "total_time": exec_result.total_time,
            "specialists": exec_result.specialists,
            "errors": exec_result.errors,
        }
    elif action == "status":
        result = hierarchical_status(args.get("coordinator_id", ""))
    elif action == "merge":
        result = hierarchical_result_merge(args.get("coordinator_id", ""))
    else:
        result = {"error": f"unknown action: {action}"}
    return json.dumps(result, indent=2)

DELEGATE_ORCHESTRATOR_SCHEMA = {
    "name": "delegate_orchestrator",
    "description": "3-tier hierarchical delegation: coordinator → specialist → worker.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["spawn", "execute", "status", "merge"]},
            "goal": {"type": "string"},
            "coordinator_id": {"type": "string"},
            "max_specialists": {"type": "integer", "default": 5},
            "max_workers_per_specialist": {"type": "integer", "default": 5},
            "max_time_per_worker": {"type": "integer", "default": 60},
        },
    },
}