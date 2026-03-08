"""
Agent Registry — dynamic loader for all 76 agents from departments.yaml.

Provides unified lookup, capability search, and semantic routing support.
Loaded once at startup via load_registry(); all lookups are cached.
"""

from __future__ import annotations

import logging
import os
import signal
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AgentDef:
    """Complete definition of a single agent."""

    name: str
    department: str
    description: str
    primary_model: str          # key in models.yaml → resolved to litellm model_id
    fallbacks: list[str]        # keys in models.yaml
    capabilities: list[str]     # keyword tags used for routing
    tools: list[str]
    complexity_tier: str        # lightweight / midweight / heavyweight
    prompt_template: str = ""   # path to Jinja2 .j2 file (auto-set)
    primary_model_id: str = ""  # resolved litellm model_id (set by load_registry)
    fallback_model_ids: list[str] = field(default_factory=list)  # resolved

    def __post_init__(self) -> None:
        if not self.prompt_template:
            self.prompt_template = (
                f"prompts/role/{self.department}/{self.name}.j2"
            )


# ---------------------------------------------------------------------------
# Global indexes (populated by load_registry)
# ---------------------------------------------------------------------------

AGENT_REGISTRY: dict[str, AgentDef] = {}
DEPARTMENT_INDEX: dict[str, list[str]] = {}
CAPABILITY_INDEX: dict[str, list[str]] = {}
CAPABILITY_EMBEDDINGS: dict[str, np.ndarray] = {}
MODEL_LOOKUP: dict[str, str] = {}  # yaml key → litellm model_id

_embedding_model = None  # sentence-transformers instance (lazy)


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

def load_registry(
    departments_path: str = "config/departments.yaml",
    models_path: str = "config/models.yaml",
) -> None:
    """Load all agents from YAML files and populate all indexes.

    Safe to call multiple times — clears and rebuilds everything.
    """
    global AGENT_REGISTRY, DEPARTMENT_INDEX, CAPABILITY_INDEX, MODEL_LOOKUP
    global CAPABILITY_EMBEDDINGS, _embedding_model

    AGENT_REGISTRY.clear()
    DEPARTMENT_INDEX.clear()
    CAPABILITY_INDEX.clear()
    CAPABILITY_EMBEDDINGS.clear()

    # ── Load model lookup table ─────────────────────────────────────────────
    models_file = Path(models_path)
    if not models_file.exists():
        logger.warning(f"models.yaml not found at {models_path}, using empty lookup")
    else:
        with models_file.open() as f:
            models_cfg = yaml.safe_load(f)
        MODEL_LOOKUP = {
            key: cfg["model_id"]
            for key, cfg in models_cfg.get("models", {}).items()
        }

    # ── Load department/agent definitions ───────────────────────────────────
    dept_file = Path(departments_path)
    if not dept_file.exists():
        logger.error(f"departments.yaml not found at {departments_path}")
        return

    with dept_file.open() as f:
        departments = yaml.safe_load(f)

    for dept_name, dept_cfg in departments.items():
        DEPARTMENT_INDEX[dept_name] = []
        agents_cfg = dept_cfg.get("agents", {})

        for agent_name, acfg in agents_cfg.items():
            primary_key = acfg.get("primary_model", "")
            fallback_keys: list[str] = acfg.get("fallbacks", [])

            agent = AgentDef(
                name=agent_name,
                department=dept_name,
                description=acfg.get("description", ""),
                primary_model=primary_key,
                fallbacks=fallback_keys,
                capabilities=acfg.get("capabilities", []),
                tools=acfg.get("tools", []),
                complexity_tier=acfg.get("complexity_tier", "midweight"),
                primary_model_id=MODEL_LOOKUP.get(primary_key, primary_key),
                fallback_model_ids=[
                    MODEL_LOOKUP.get(k, k) for k in fallback_keys
                ],
            )

            AGENT_REGISTRY[agent_name] = agent
            DEPARTMENT_INDEX[dept_name].append(agent_name)

            for cap in agent.capabilities:
                cap_lower = cap.lower()
                CAPABILITY_INDEX.setdefault(cap_lower, [])
                if agent_name not in CAPABILITY_INDEX[cap_lower]:
                    CAPABILITY_INDEX[cap_lower].append(agent_name)

    total = len(AGENT_REGISTRY)
    depts = len(DEPARTMENT_INDEX)
    logger.info(f"✓ Loaded {total} agents across {depts} departments")

    # ── Precompute semantic embeddings ──────────────────────────────────────
    _precompute_embeddings()


def _precompute_embeddings() -> None:
    """Encode all agents' description+capabilities with sentence-transformers."""
    global _embedding_model, CAPABILITY_EMBEDDINGS

    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        if _embedding_model is None:
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        for name, agent in AGENT_REGISTRY.items():
            text = agent.description + " " + " ".join(agent.capabilities)
            CAPABILITY_EMBEDDINGS[name] = _embedding_model.encode(
                text, normalize_embeddings=True
            )

        logger.info(
            f"✓ Precomputed embeddings for {len(CAPABILITY_EMBEDDINGS)} agents"
        )
    except ImportError:
        logger.warning(
            "sentence-transformers not installed — semantic routing (Layer 2) disabled"
        )
    except Exception as exc:
        logger.warning(f"Embedding precomputation failed: {exc}")


# ---------------------------------------------------------------------------
# Hot-reload
# ---------------------------------------------------------------------------

def reload_from_yaml() -> None:
    """Reload all agents from YAML without restarting the bot."""
    logger.info("Reloading agent registry from YAML…")
    get_agent.cache_clear()
    load_registry()
    logger.info("✓ Registry reloaded")


def _sighup_handler(signum: int, frame: object) -> None:  # noqa: ARG001
    reload_from_yaml()


signal.signal(signal.SIGHUP, _sighup_handler)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=512)
def get_agent(name: str) -> Optional[AgentDef]:
    """Return agent by name (cached). Returns None if not found."""
    return AGENT_REGISTRY.get(name)


def agents_by_department(dept: str) -> list[AgentDef]:
    """Return all AgentDef objects in a department."""
    return [AGENT_REGISTRY[n] for n in DEPARTMENT_INDEX.get(dept, [])]


def get_department_default(dept: str) -> Optional[AgentDef]:
    """Return the declared default agent for a department."""
    dept_file = Path("config/departments.yaml")
    if not dept_file.exists():
        agents = agents_by_department(dept)
        return agents[0] if agents else None

    with dept_file.open() as f:
        depts = yaml.safe_load(f)

    default_name: Optional[str] = depts.get(dept, {}).get("default_agent")
    if default_name:
        return get_agent(default_name)

    agents = agents_by_department(dept)
    return agents[0] if agents else None


def list_all_departments() -> list[str]:
    """Return sorted list of all department names."""
    return sorted(DEPARTMENT_INDEX.keys())


def get_agent_count() -> dict[str, int]:
    """Return {dept_name: agent_count} dict."""
    return {dept: len(names) for dept, names in DEPARTMENT_INDEX.items()}


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------

def search_by_capability(keywords: list[str]) -> list[tuple[str, int]]:
    """Keyword-based capability search (Layer 1).

    Returns list of (agent_name, score) sorted by score descending.
    Exact capability match scores 2; substring match scores 1.
    """
    scores: dict[str, int] = {}

    for kw in keywords:
        kw_lower = kw.lower().strip()
        # Exact match
        if kw_lower in CAPABILITY_INDEX:
            for aname in CAPABILITY_INDEX[kw_lower]:
                scores[aname] = scores.get(aname, 0) + 2
        # Substring match — skip caps shorter than 3 chars to avoid false positives
        for cap, anames in CAPABILITY_INDEX.items():
            if len(cap) < 3 or len(kw_lower) < 3:
                continue
            if kw_lower != cap and (kw_lower in cap or cap in kw_lower):
                for aname in anames:
                    scores[aname] = scores.get(aname, 0) + 1

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def semantic_search(
    query: str, top_k: int = 3
) -> list[tuple[str, float]]:
    """Embedding-based semantic search (Layer 2).

    Returns list of (agent_name, cosine_similarity) sorted descending.
    Returns empty list if embeddings unavailable.
    """
    if not _embedding_model or not CAPABILITY_EMBEDDINGS:
        return []

    try:
        qvec = _embedding_model.encode(query, normalize_embeddings=True)
        sims: list[tuple[str, float]] = [
            (name, float(np.dot(qvec, evec)))
            for name, evec in CAPABILITY_EMBEDDINGS.items()
        ]
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:top_k]
    except Exception as exc:
        logger.error(f"Semantic search error: {exc}")
        return []


# ---------------------------------------------------------------------------
# Compatibility shims — keep existing main.py call-sites working
# ---------------------------------------------------------------------------

# In-memory thread storage (mirrors old agents.ACTIVE_THREADS)
import time as _time
from datetime import datetime as _datetime

ACTIVE_THREADS: dict[str, list[dict]] = {}

# Legacy model mappings for backwards compat (/agent coding, /agent debug, etc.)
_LEGACY_AGENT_MODELS: dict[str, str] = {
    "vision":    "ollama_chat/gemma3:12b",
    "coding":    "cerebras/qwen3-235b-a22b",       # 14,400 req/day, fast, reliable
    "debug":     "zai/glm-4",
    "math":      "zai/glm-4",
    "architect": "cerebras/qwen3-235b-a22b",
    "mentor":    "gemini/gemini-2.0-flash",
    "analyst":   "groq/moonshotai/kimi-k2-instruct",
}
_LEGACY_FALLBACK_MODELS: dict[str, str] = {
    "coding":    "openrouter/qwen/qwen3-coder:free",  # fallback when cerebras unavailable
    "debug":     "cerebras/qwen3-235b-a22b",
    "math":      "cerebras/qwen3-235b-a22b",
    "architect": "openrouter/openai/gpt-oss-120b:free",
    "mentor":    "gemini/gemma-3-27b-it",
    "analyst":   "openrouter/openai/gpt-oss-120b:free",
}


def get_model(agent_key: str, use_fallback: bool = False) -> Optional[str]:
    """Return litellm model_id for an agent key.

    Supports both legacy 7-agent keys and new 76-agent slug names.
    """
    # Check legacy map first
    registry = _LEGACY_FALLBACK_MODELS if use_fallback else _LEGACY_AGENT_MODELS
    if agent_key in registry:
        return registry[agent_key]
    # Check new registry
    agent = AGENT_REGISTRY.get(agent_key)
    if agent:
        return (
            agent.fallback_model_ids[0]
            if use_fallback and agent.fallback_model_ids
            else agent.primary_model_id
        ) or agent.primary_model_id
    return None


def detect_agent(task: str) -> str:
    """Legacy keyword detection — returns agent key string.

    Used by existing _execute_task(); bridges to new search_by_capability().
    """
    results = search_by_capability(task.lower().split())
    if results:
        return results[0][0]
    # Fallback to legacy keyword scan
    task_lower = task.lower()
    _LEGACY_KEYWORDS: dict[str, list[str]] = {
        "vision": ["screenshot", "image", "photo", "ui", "visual", "ocr", "screen"],
        "debug": ["debug", "traceback", "exception", "crash", "fix", "bug", "cuda", "nan", "oom"],
        "math": ["tensor", "matrix", "derivative", "gradient", "backprop", "calculate"],
        "architect": ["design", "architecture", "plan", "system", "strategy"],
        "mentor": ["explain", "teach", "what is", "how does", "eli5", "beginner"],
        "analyst": ["analyze", "plot", "csv", "dataframe", "statistics", "trend"],
        "coding": ["code", "function", "implement", "class", "endpoint", "api"],
    }
    scores = {a: sum(kw in task_lower for kw in kws) for a, kws in _LEGACY_KEYWORDS.items()}
    best = max(scores, key=lambda a: scores[a])
    return best if scores[best] > 0 else "senior_python_dev"


def list_agents() -> str:
    """Return HTML table of all agents grouped by department."""
    if not AGENT_REGISTRY:
        # Fallback to legacy display if registry not loaded yet
        lines = ["<b>Babas Agency Swarm — Agents</b>\n"]
        for key, model in _LEGACY_AGENT_MODELS.items():
            lines.append(f"  <b>{key}</b> → <code>{model}</code>")
        return "\n".join(lines)

    lines = ["<b>🤖 Babas Agency Swarm — 76 Agents</b>\n"]
    for dept, agent_names in DEPARTMENT_INDEX.items():
        dept_display = dept.replace("_", " ").title()
        lines.append(f"\n<b>{dept_display}</b> ({len(agent_names)} agents)")
        for name in agent_names[:5]:  # Show first 5 per dept to fit in 4000 chars
            agent = AGENT_REGISTRY[name]
            lines.append(f"  • <code>{name}</code> — {agent.description[:60]}")
        if len(agent_names) > 5:
            lines.append(f"  … +{len(agent_names) - 5} more (use /dept {dept})")
    lines.append(f"\n<b>Total: {len(AGENT_REGISTRY)} agents across {len(DEPARTMENT_INDEX)} departments</b>")
    return "\n".join(lines)


def add_to_thread(thread_id: str, agent: str, task: str, result: str) -> None:
    """Store a conversation turn in thread history."""
    ACTIVE_THREADS.setdefault(thread_id, [])
    ACTIVE_THREADS[thread_id].append({
        "agent": agent,
        "task": task,
        "result": result[:500],
        "timestamp": _time.time(),
    })
    if len(ACTIVE_THREADS[thread_id]) > 10:
        ACTIVE_THREADS[thread_id] = ACTIVE_THREADS[thread_id][-10:]


def get_thread_context(thread_id: str, last_n: int = 3) -> str:
    """Get recent conversation context from a thread."""
    turns = ACTIVE_THREADS.get(thread_id)
    if not turns:
        return ""
    recent = turns[-last_n:]
    lines = ["Previous conversation in this thread:\n"]
    for turn in recent:
        time_str = _datetime.fromtimestamp(turn["timestamp"]).strftime("%H:%M")
        lines.append(f"[{time_str}] {turn['agent'].upper()}: {turn['task'][:100]}…")
        lines.append(f"Response: {turn['result']}\n")
    return "\n".join(lines)


def list_threads_raw() -> list[str]:
    """Return list of active thread IDs."""
    return list(ACTIVE_THREADS.keys())


def list_threads() -> str:
    """List all active threads with turn counts."""
    if not ACTIVE_THREADS:
        return "<b>No active threads</b>\n\nUse <code>/thread &lt;name&gt;</code> to start one."
    lines = ["<b>Active Threads</b>\n"]
    for tid, turns in ACTIVE_THREADS.items():
        ts = _datetime.fromtimestamp(turns[-1]["timestamp"]).strftime("%m/%d %H:%M")
        lines.append(f"📌 <b>{tid}</b> — {len(turns)} turns (last: {ts})")
    return "\n".join(lines)


def clear_thread(thread_id: str) -> bool:
    """Delete a thread's history. Returns True if it existed."""
    if thread_id in ACTIVE_THREADS:
        del ACTIVE_THREADS[thread_id]
        return True
    return False
