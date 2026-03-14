"""Legion Orchestrator package — exports all key classes."""
from swarms_bot.orchestrator.agent_base import Agent, AgentResponse, Task
from swarms_bot.orchestrator.chief_of_staff import ChiefOfStaff, TaskType
from swarms_bot.orchestrator.dag_planner import DAGNode, DAGPlanner, TaskDAG
from swarms_bot.orchestrator.dag_executor import DAGExecutor
from swarms_bot.orchestrator.agent_messaging import AgentMessage, AgentMessageBus, MessageType
from swarms_bot.orchestrator.shared_workspace import SharedWorkspace
from swarms_bot.orchestrator.nested_agents import SpawnableAgent, SpawnContext
from swarms_bot.orchestrator.human_in_loop import HumanApprovalGate
from swarms_bot.orchestrator.model_router import ModelRouter, TaskComplexity
from swarms_bot.orchestrator.registry import build_agent_registry

__all__ = [
    "Agent", "AgentResponse", "Task",
    "ChiefOfStaff", "TaskType",
    "DAGNode", "DAGPlanner", "TaskDAG",
    "DAGExecutor",
    "AgentMessage", "AgentMessageBus", "MessageType",
    "SharedWorkspace",
    "SpawnableAgent", "SpawnContext",
    "HumanApprovalGate",
    "ModelRouter", "TaskComplexity",
    "build_agent_registry",
]
