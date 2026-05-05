#!/usr/bin/python3
"""
Claude Code Swarm Executor — Automatic multi-agent orchestration.

Usage:
    python3 swarm-executor.py "your task here"

What it does:
1. Analyzes task → selects top-k agents by capability matching
2. Spawns N concurrent Claude Code CLI processes, each running as a specialized agent
3. Collects results and synthesizes them

Environment:
    CLAUDE_CODE_PATH - path to claude CLI (default: which claude or ~/.local/bin/claude)
"""

import argparse
import asyncio
import itertools
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Capability engine (mirrors swarm-bot's AgentSelector)
# --------------------------------------------------------------------------- #

CAPABILITY_KEYWORDS = {
    "python": ["python", "django", "flask", "fastapi", "async", "pandas", "numpy", "pytest", "jwt", "auth", "authentication", "oauth"],
    "javascript": ["javascript", "js", "node", "nodejs", "react", "vue", "typescript", "ts", "npm"],
    "cuda": ["cuda", "gpu", "kernel", "nvidia", "cudnn", "tensor", "torch", "triton"],
    "debug": ["debug", "bug", "fix", "traceback", "error", "exception", "crash", "pdb"],
    "fastapi": ["fastapi", "api", "rest", "endpoint", "middleware", "pydantic", "uvicorn", "jwt", "auth"],
    "react": ["react", "frontend", "ui", "component", "hook", "tsx", "jsx", "nextjs"],
    "database": ["sql", "postgres", "postgresql", "mysql", "redis", "query", "table", "schema", "sqlite", "aiosqlite"],
    "security": ["security", "vulnerability", "pentest", "audit", "exploit", "injection", "xss", "csrf", "jwt", "auth"],
    "solidity": ["solidity", "smart-contract", "ethereum", "web3", "blockchain", "defi", "vyper"],
    "research": ["research", "paper", "arxiv", "academic", "study", "survey", "analysis", "review"],
    "design": ["design", "ui", "ux", "figma", "interface", "layout", "css", "tailwind"],
    "devops": ["devops", "ci", "cd", "docker", "kubernetes", "k8s", "deployment", "pipeline", "github-actions"],
    "data": ["data", "analytics", "ml", "machine-learning", "model", "training", "inference", "sklearn"],
}

COMPLEXITY_SIGNALS = [
    "implement", "build", "create", "design", "develop",
    "analyze", "audit", "review", "research",
    "multiple", "several", "various", "different",
    "backend", "frontend", "database", "api",
    "test", "debug", "fix", "patch",
    "full-stack", "end-to-end", "comprehensive",
]


def _tokenize(text: str) -> set[str]:
    text = text.lower()
    tokens = set(re.findall(r"[a-z][a-z0-9]{1,}", text))
    words = text.split()
    tokens |= {f"{a}_{b}" for a, b in itertools.pairwise(words)}
    return tokens


def _score_capability(task_tokens: set[str], cap_tokens: set[str]) -> float:
    overlap = len(task_tokens & cap_tokens)
    bonus = sum(0.5 for t in task_tokens if t in cap_tokens)
    return overlap * 3.0 + bonus


def select_capabilities(task: str, max_agents: int = 4) -> list[tuple[str, float]]:
    """Score all capabilities and return top-k sorted by score."""
    task_tokens = _tokenize(task)
    scores = []

    for cap_name, keywords in CAPABILITY_KEYWORDS.items():
        cap_tokens = _tokenize(" ".join(keywords))
        score = _score_capability(task_tokens, cap_tokens)
        if score > 0:
            scores.append((cap_name, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:max_agents]


def estimate_complexity(task: str) -> int:
    task_lower = task.lower()
    word_count = len(task.split())
    is_complex = any(s in task_lower for s in COMPLEXITY_SIGNALS)

    if word_count > 80 or (is_complex and word_count > 40):
        return 8
    elif word_count > 40 or is_complex:
        return 5
    else:
        return 3


# --------------------------------------------------------------------------- #
# Claude Code agent prompts
# --------------------------------------------------------------------------- #

AGENT_SYSTEM_PROMPTS = {
    "python": """You are a Python expert. You specialize in:
- Django, Flask, FastAPI, async/await
- pandas, numpy, pytest
- Clean Pythonic code with type hints
- Production-grade implementations

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "javascript": """You are a JavaScript/TypeScript expert. You specialize in:
- Node.js, React, Vue, Next.js
- TypeScript, ES6+ features
- npm, yarn, bundlers

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "cuda": """You are a CUDA/GPU optimization expert. You specialize in:
- CUDA kernel development, Triton
- GPU memory management, tensor ops
- PyTorch CUDA extensions

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "debug": """You are a debugging specialist. You specialize in:
- Traceback analysis, error diagnosis
- Memory leaks, race conditions
- pdb, pytest debugging

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "fastapi": """You are a FastAPI expert. You specialize in:
- REST API design, endpoints
- Pydantic validation, middleware
- Uvicorn, async handlers

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "react": """You are a React frontend expert. You specialize in:
- React components, hooks, context
- TypeScript, TSX/JSX
- Next.js, responsive design

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "database": """You are a database expert. You specialize in:
- SQL (PostgreSQL, MySQL, SQLite)
- Schema design, query optimization
- aiosqlite, async drivers

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "security": """You are a security expert. You specialize in:
- Vulnerability assessment, penetration testing
- XSS, SQL injection, CSRF
- Authentication, authorization

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "solidity": """You are a smart contract expert. You specialize in:
- Solidity, Vyper, Ethereum
- Smart contract security audits
- Web3.js, Ethers.js

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "research": """You are a research expert. You specialize in:
- Academic paper analysis, arxiv
- Technical surveys, literature review
- Synthesizing complex topics

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "design": """You are a UI/UX designer. You specialize in:
- Figma, interface design
- CSS, Tailwind, layout
- User experience optimization

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "devops": """You are a DevOps engineer. You specialize in:
- Docker, Kubernetes, CI/CD
- GitHub Actions, pipelines
- Deployment automation

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",

    "data": """You are a data/ML expert. You specialize in:
- Machine learning, model training
- sklearn, PyTorch
- Data pipelines, analytics

Your task: Execute the assigned work with precision. Return findings as:
FINDING: [what you discovered/built]
STATUS: done|blocked|needs_more""",
}


# --------------------------------------------------------------------------- #
# OpenCode CLI (programmatic execution)
# --------------------------------------------------------------------------- #

OPENCODE_CLI = "/home/newadmin/.opencode/bin/opencode"


def run_agent_task(
    capability: str,
    task: str,
    session_id: str,
    cli_path: str = OPENCODE_CLI,
    timeout: int = 180,
) -> dict[str, Any]:
    """Run a single agent task via OpenCode CLI."""
    started = time.perf_counter()

    system_prompt = AGENT_SYSTEM_PROMPTS.get(
        capability,
        f"You are a {capability} expert. Execute the task precisely."
    )

    # Build the full prompt for OpenCode
    full_prompt = f"""{system_prompt}

---

TASK: {task}

Execute your portion of this task. Be precise. Return your findings.
"""

    try:
        result = subprocess.run(
            [cli_path, "run", full_prompt],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        latency_ms = (time.perf_counter() - started) * 1000.0

        return {
            "capability": capability,
            "session_id": session_id,
            "output": result.stdout[:2000] if result.stdout else "(no output)",
            "stderr": result.stderr[:500] if result.stderr else "",
            "latency_ms": latency_ms,
            "success": result.returncode == 0 and bool(result.stdout),
            "return_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "capability": capability,
            "session_id": session_id,
            "output": f"(timeout after {timeout}s)",
            "stderr": "",
            "latency_ms": (time.perf_counter() - started) * 1000.0,
            "success": False,
            "return_code": -1,
        }
    except Exception as exc:
        return {
            "capability": capability,
            "session_id": session_id,
            "output": f"error: {exc}",
            "stderr": "",
            "latency_ms": (time.perf_counter() - started) * 1000.0,
            "success": False,
            "return_code": -1,
        }


# --------------------------------------------------------------------------- #
# Concurrent execution
# --------------------------------------------------------------------------- #

def run_swarm(task: str, max_agents: int = 4, timeout_per_agent: int = 180) -> dict[str, Any]:
    """Run swarm: select capabilities and execute agents concurrently."""
    started = time.perf_counter()
    session_id = uuid.uuid4().hex[:8]

    # Select capabilities
    capabilities = select_capabilities(task, max_agents=max_agents)
    complexity = estimate_complexity(task)

    if not capabilities:
        return {
            "error": "No matching capabilities found",
            "task": task,
            "selected_capabilities": [],
            "results": [],
        }

    print("\n## Swarm Execution Plan")
    print(f"**Task**: {task[:100]}{'...' if len(task) > 100 else ''}")
    print(f"**Selected Capabilities**: {', '.join(c for c, _ in capabilities)}")
    print(f"**Sub-agents to spawn**: ~{complexity}")
    print(f"**Session ID**: {session_id}")
    print(f"[CLI] Using: {OPENCODE_CLI}\n")

    # Run agents concurrently
    import concurrent.futures

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(capabilities)) as executor:
        futures = {
            executor.submit(
                run_agent_task,
                cap,
                task,
                session_id,
                OPENCODE_CLI,
                timeout_per_agent,
            ): cap
            for cap, _ in capabilities
        }

        for future in concurrent.futures.as_completed(futures):
            cap = futures[future]
            print(f"[{cap}] completed")
            results.append(future.result())

    # Synthesize results
    total_latency_ms = (time.perf_counter() - started) * 1000.0

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    synthesis = f"""# Swarm Execution Report

**Session**: {session_id}
**Task**: {task}
**Capabilities selected**: {len(capabilities)}
**Successful agents**: {len(successful)}/{len(results)}
**Total latency**: {total_latency_ms/1000:.1f}s

## Results by Agent
"""

    for r in results:
        status = "✓" if r["success"] else "✗"
        synthesis += f"""
### {status} [{r['capability']}] ({r['latency_ms']/1000:.1f}s)
```
{r['output'][:500]}
```
"""

    if failed:
        synthesis += "\n## Failed Agents\n"
        for r in failed:
            synthesis += f"- {r['capability']}: {r['output'][:200]}\n"

    return {
        "session_id": session_id,
        "task": task,
        "selected_capabilities": capabilities,
        "complexity": complexity,
        "results": results,
        "synthesis": synthesis,
        "total_latency_ms": total_latency_ms,
        "success_count": len(successful),
        "failure_count": len(failed),
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Swarm — Automatic multi-agent orchestration"
    )
    parser.add_argument("task", nargs="+", help="Task description")
    parser.add_argument(
        "--max-agents", "-k", type=int, default=4,
        help="Max agents to select (default: 4)"
    )
    parser.add_argument(
        "--timeout", "-t", type=int, default=180,
        help="Timeout per agent in seconds (default: 180)"
    )
    parser.add_argument(
        "--json", "-j", action="store_true",
        help="Output results as JSON"
    )
    args = parser.parse_args()

    task = " ".join(args.task)

    result = run_swarm(task, max_agents=args.max_agents, timeout_per_agent=args.timeout)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["synthesis"])

    return 0 if result["failure_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
