"""Claude Code /swarm skill — Multi-agent orchestration via Agent tool."""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any

# Capability keywords for agent selection
CAPABILITY_TOKENS = {
    "python": ["python", "django", "flask", "fastapi", "async", "pandas", "numpy"],
    "javascript": ["javascript", "js", "node", "nodejs", "react", "vue", "typescript", "ts"],
    "cuda": ["cuda", "gpu", "kernel", "nvidia", "cudnn", "tensor"],
    "debug": ["debug", "bug", "fix", "traceback", "error", "exception", "crash"],
    "fastapi": ["fastapi", "api", "rest", "endpoint", "middleware", "pydantic"],
    "react": ["react", "frontend", "ui", "component", "hook", "tsx", "jsx"],
    "database": ["sql", "postgres", "postgresql", "mysql", "query", "table", "schema", "sqlite"],
    "security": ["security", "vulnerability", "pentest", "audit", "exploit", "injection", "xss"],
    "solidity": ["solidity", "smart-contract", "ethereum", "web3", "blockchain", "defi"],
    "research": ["research", "paper", "arxiv", "academic", "study", "survey", "analysis"],
    "design": ["design", "ui", "ux", "figma", "interface", "layout", "css"],
    "devops": ["devops", "ci", "cd", "docker", "kubernetes", "k8s", "deployment", "pipeline"],
    "data": ["data", "analytics", "ml", "machine-learning", "model", "training", "inference"],
}

COMPLEXITY_SIGNALS = [
    "implement", "build", "create", "design",
    "analyze", "audit", "review", "research",
    "multiple", "several", "various", "different",
    "backend", "frontend", "database", "api",
    "test", "debug", "fix", "patch",
    "full-stack", "end-to-end", "comprehensive",
]


def tokenize(text: str) -> set[str]:
    """Lowercase, extract alphanumeric tokens + bigrams."""
    text = text.lower()
    tokens = set(re.findall(r"[a-z][a-z0-9]{1,}", text))
    words = text.split()
    bigrams = {f"{a}_{b}" for a, b in zip(words, words[1:])}
    return tokens | bigrams


def score_capability(task_tokens: set[str], cap_tokens: set[str]) -> float:
    """Score a capability match."""
    overlap = len(task_tokens & cap_tokens)
    bonus = sum(0.5 for t in task_tokens if t in cap_tokens)
    return overlap * 3.0 + bonus


def select_capabilities(task: str) -> list[tuple[str, float]]:
    """Score all capabilities and return sorted list."""
    task_tokens = tokenize(task)
    scores: list[tuple[str, float]] = []

    for cap_name, cap_keywords in CAPABILITY_TOKENS.items():
        cap_tokens = tokenize(" ".join(cap_keywords))
        score = score_capability(task_tokens, cap_tokens)
        if score > 0:
            scores.append((cap_name, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def estimate_complexity(task: str) -> int:
    """Estimate sub-agent count based on task complexity."""
    task_lower = task.lower()
    word_count = len(task.split())

    is_complex = any(s in task_lower for s in COMPLEXITY_SIGNALS)

    if word_count > 80 or (is_complex and word_count > 40):
        return 8
    elif word_count > 40 or is_complex:
        return 5
    else:
        return 3


async def run_swarm(task: str, max_agents: int = 4) -> dict[str, Any]:
    """Run swarm orchestration on a task.

    Returns dict with:
    - selected_capabilities: list of (cap_name, score) tuples
    - sub_agent_count: estimated number of sub-agents
    - plan: what each agent should do
    """
    started = time.perf_counter()

    # Select capabilities
    capabilities = select_capabilities(task)[:max_agents]
    sub_agent_count = estimate_complexity(task)

    # Build execution plan
    tokenize(task)
    plan = {
        "task": task,
        "selected_capabilities": capabilities,
        "sub_agent_count": sub_agent_count,
        "execution_mode": "concurrent" if len(capabilities) > 1 else "sequential",
        "token_count": len(task.split()),
    }

    return {
        "plan": plan,
        "latency_ms": (time.perf_counter() - started) * 1000.0,
        "ready": True,
    }


def get_capability_description(cap_name: str) -> str:
    """Get description for a capability."""
    descriptions = {
        "python": "Python development (Django, Flask, FastAPI, async/await, data processing)",
        "javascript": "JavaScript/TypeScript (Node.js, React, Vue, frontend)",
        "cuda": "CUDA/GPU development (kernel optimization, NVIDIA, tensor ops)",
        "debug": "Debugging (traceback analysis, bug fixes, error resolution)",
        "fastapi": "FastAPI REST API development (endpoints, middleware, Pydantic)",
        "react": "React frontend development (components, hooks, TSX)",
        "database": "Database operations (SQL, PostgreSQL, queries, schema)",
        "security": "Security auditing (vulnerability assessment, penetration testing)",
        "solidity": "Smart contract development (Solidity, Ethereum, Web3)",
        "research": "Academic research (papers, arxiv, technical analysis)",
        "design": "UI/UX design (interface, layout, Figma)",
        "devops": "DevOps (CI/CD, Docker, Kubernetes, deployment)",
        "data": "Data/ML (analytics, machine learning, model training)",
    }
    return descriptions.get(cap_name, f"{cap_name} development")


# Export for skill registry
SKILL_METADATA = {
    "name": "swarm",
    "description": "Multi-agent swarm orchestration — auto-selects specialized agents and spawns sub-agents based on task complexity",
    "keywords": ["swarm", "multi-agent", "concurrent", "parallel", "orchestrate"],
}


async def execute(task: str) -> str:
    """Execute a swarm task. Returns formatted plan for Agent tool."""
    result = await run_swarm(task)

    lines = [
        "## Swarm Plan",
        f"**Task**: {result['plan']['task'][:100]}...",
        f"**Selected Capabilities** ({len(result['plan']['selected_capabilities'])}):",
    ]

    for cap, score in result['plan']['selected_capabilities']:
        desc = get_capability_description(cap)
        lines.append(f"  - {cap} (score: {score:.1f}) — {desc}")

    lines.extend([
        f"**Sub-agents to spawn**: ~{result['plan']['sub_agent_count']}",
        f"**Execution mode**: {result['plan']['execution_mode']}",
        "",
        "### Agent Assignments:",
    ])

    for i, (cap, _) in enumerate(result['plan']['selected_capabilities'], 1):
        lines.append(f"{i}. [{cap}] {get_capability_description(cap)}")

    return "\n".join(lines)
