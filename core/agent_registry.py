"""
Agent Registry — dynamic loader for all 76 agents from departments.yaml.

Provides unified lookup, capability search, and semantic routing support.
Loaded once at startup via load_registry(); all lookups are cached.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path

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
    primary_model: str  # key in models.yaml → resolved to litellm model_id
    fallbacks: list[str]  # keys in models.yaml
    capabilities: list[str]  # keyword tags used for routing
    tools: list[str]
    complexity_tier: str  # lightweight / midweight / heavyweight
    prompt_template: str = ""  # path to Jinja2 .j2 file (auto-set)
    primary_model_id: str = ""  # resolved litellm model_id (set by load_registry)
    fallback_model_ids: list[str] = field(default_factory=list)  # resolved
    version: str = "1.0.0"  # agent version for tracking

    def __post_init__(self) -> None:
        if not self.prompt_template:
            self.prompt_template = f"prompts/role/{self.department}/{self.name}.j2"


# ---------------------------------------------------------------------------
# Global indexes (populated by load_registry)
# ---------------------------------------------------------------------------

AGENT_REGISTRY: dict[str, AgentDef] = {}
DEPARTMENT_INDEX: dict[str, list[str]] = {}
CAPABILITY_INDEX: dict[str, list[str]] = {}

# Bounded LRU cache — prevents unbounded embedding storage
_MAX_EMBEDDINGS = 200
CAPABILITY_EMBEDDINGS: OrderedDict[str, np.ndarray] = OrderedDict()
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
        MODEL_LOOKUP = {key: cfg["model_id"] for key, cfg in models_cfg.get("models", {}).items()}

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
                primary_model_id=MODEL_LOOKUP.get(primary_key, primary_key),  # type: ignore[reportArgumentType]
                fallback_model_ids=[MODEL_LOOKUP.get(k, k) for k in fallback_keys],
                version=acfg.get("version", "1.0.0"),
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

    # ── Precompute semantic embeddings (async — doesn't block startup) ─────
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running event loop at startup → call synchronously
        _precompute_embeddings_sync()
    else:
        # Running loop exists → fire to thread pool so startup isn't blocked
        loop.run_in_executor(None, _precompute_embeddings_sync)


def _precompute_embeddings_sync() -> None:
    """Encode all agents' description+capabilities with sentence-transformers (sync entrypoint)."""
    global _embedding_model
    if _embedding_model is not None:
        return  # Already initialized

    # Skip if HuggingFace token is expired or unavailable — semantic search degrades gracefully
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _embedding_model = SentenceTransformer("all-mpnet-base-v2")
    except Exception as exc:
        logger.warning(f"Could not load SentenceTransformer embedding model: {exc}")
        logger.warning("Agent semantic search will use keyword matching only")
        return

    for name, agent in AGENT_REGISTRY.items():
        if len(CAPABILITY_EMBEDDINGS) >= _MAX_EMBEDDINGS:
            CAPABILITY_EMBEDDINGS.popitem(last=False)  # evict oldest
        text = agent.description + " " + " ".join(agent.capabilities)
        CAPABILITY_EMBEDDINGS[name] = _embedding_model.encode(text, normalize_embeddings=True)  # type: ignore[reportArgumentType]
        CAPABILITY_EMBEDDINGS.move_to_end(name)  # mark as recently used

    logger.info(f"✓ Precomputed embeddings for {len(CAPABILITY_EMBEDDINGS)} agents")


async def _precompute_embeddings_async() -> None:
    """Async wrapper — runs embedding computation in a thread pool so it doesn't block startup."""
    try:
        await asyncio.to_thread(_precompute_embeddings_sync)
    except Exception as exc:
        logger.warning(f"Embedding precomputation failed: {exc}")


def _precompute_embeddings() -> None:
    """Sync wrapper — fires off async precomputation without blocking the caller."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop → use blocking call directly (module load time)
        _precompute_embeddings_sync()
        return
    # Running loop exists → fire-and-forget via executor so startup isn't blocked
    loop.run_in_executor(None, _precompute_embeddings_sync)


# ---------------------------------------------------------------------------
# Hot-reload
# ---------------------------------------------------------------------------


def reload_from_yaml() -> None:
    """Reload all agents from YAML without restarting the bot."""
    logger.info("Reloading agent registry from YAML…")
    prev_count = len(AGENT_REGISTRY)
    get_agent.cache_clear()
    load_registry()
    new_count = len(AGENT_REGISTRY)
    logger.info(
        "✓ Registry reloaded — %d agents (was %d)",
        new_count,
        prev_count,
    )


def _sighup_handler(signum: int, frame: object) -> None:
    reload_from_yaml()


signal.signal(signal.SIGHUP, _sighup_handler)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


@lru_cache(maxsize=512)
def get_agent(name: str) -> AgentDef | None:
    """Return agent by name (cached). Returns None if not found."""
    return AGENT_REGISTRY.get(name)


def agents_by_department(dept: str) -> list[AgentDef]:
    """Return all AgentDef objects in a department."""
    return [AGENT_REGISTRY[n] for n in DEPARTMENT_INDEX.get(dept, [])]


def get_department_default(dept: str) -> AgentDef | None:
    """Return the declared default agent for a department."""
    dept_file = Path("config/departments.yaml")
    if not dept_file.exists():
        agents = agents_by_department(dept)
        return agents[0] if agents else None

    with dept_file.open() as f:
        depts = yaml.safe_load(f)

    default_name: str | None = depts.get(dept, {}).get("default_agent")
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


def semantic_search(query: str, top_k: int = 3) -> list[tuple[str, float]]:
    """Embedding-based semantic search (Layer 2).

    Returns list of (agent_name, cosine_similarity) sorted descending.
    Returns empty list if embeddings unavailable.
    """
    if not _embedding_model or not CAPABILITY_EMBEDDINGS:
        return []

    try:
        qvec = _embedding_model.encode(query, normalize_embeddings=True)
        sims: list[tuple[str, float]] = [
            (name, float(np.dot(qvec, evec))) for name, evec in CAPABILITY_EMBEDDINGS.items()
        ]
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:top_k]
    except Exception as exc:
        logger.error(f"Semantic search error: {exc}")
        return []


# Legacy agent data (extracted from agents.py AGENT_MODELS + FALLBACK_CHAIN)

# Primary model per legacy agent (22 agents from old agents.py AGENT_MODELS)
_LEGACY_AGENT_MODELS: dict[str, str] = {
    "vision": "ollama_chat/gemma4:e4b",
    "coding": "minimax-coding-plan/MiniMax-M3",
    "debug": "minimax-coding-plan/MiniMax-M3",
    "math": "minimax-coding-plan/MiniMax-M3",
    "architect": "minimax-coding-plan/MiniMax-M3",
    "analyst": "minimax-coding-plan/MiniMax-M3",
    "computer": "minimax-coding-plan/MiniMax-M3",
    "general": "ollama_chat/gemma4:e4b",
    "researcher": "minimax-coding-plan/MiniMax-M3",
    "marketer": "minimax-coding-plan/MiniMax-M3",
    "devops": "minimax-coding-plan/MiniMax-M3",
    "pm": "minimax-coding-plan/MiniMax-M3",
    "humanizer": "minimax-coding-plan/MiniMax-M3",
    "reviewer": "minimax-coding-plan/MiniMax-M3",
    "think": "minimax-coding-plan/MiniMax-M3",
    "owl": "minimax-coding-plan/MiniMax-M3",
    "ag2_researcher": "minimax-coding-plan/MiniMax-M3",
    "ag2_critic": "minimax-coding-plan/MiniMax-M3",
    "ag2_synthesizer": "minimax-coding-plan/MiniMax-M3",
    "code_exec": "minimax-coding-plan/MiniMax-M3",
    "predictor": "minimax-coding-plan/MiniMax-M3",
    "claude_orchestrator": "minimax-coding-plan/MiniMax-M3",
    "debate": "minimax-coding-plan/MiniMax-M3",
}

# Fallback chain — MiniMax-M3 primary, MiniMax-M3 for 429 rate-limit only.
# NO other models. NO free tier. NO exceptions.
# Local Ollama gemma4:e4b (9.6GB VRAM) ONLY for vision/computer screen reading.
LEGACY_FALLBACK_CHAIN: dict[str, list[str]] = {
    # Vision/computer: local gemma4:e4b for screen reading (MiniMax can't do vision)
    # FIXED: Use correct litellm model_id values from config (not short-form provider/model)
    "vision": ["minimax-coding-plan/MiniMax-M3", "ollama_chat/gemma4:e4b"],
    "computer": ["minimax-coding-plan/MiniMax-M3", "ollama_chat/gemma4:e4b"],
    # All other agents: MiniMax primary only
    # FIXED: Use correct litellm model_id values from config
    "coding": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "debug": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "math": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "architect": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "analyst": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "general": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "researcher": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "marketer": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "devops": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "pm": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "humanizer": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "reviewer": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "think": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "owl": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "ag2_researcher": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "ag2_critic": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "ag2_synthesizer": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "code_exec": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "predictor": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "claude_orchestrator": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
    "debate": ["minimax-coding-plan/MiniMax-M3", "minimax-coding-plan/MiniMax-M3"],
}

# Task keywords for legacy agent detection (from old agents.py TASK_KEYWORDS)
LEGACY_TASK_KEYWORDS: dict[str, list[str]] = {
    "vision": [
        "screenshot",
        "screen",
        "layar",
        "gambar",
        "image",
        "photo",
        "ocr",
        "visual",
        "desktop",
        "window",
        "what do you see",
        "lihat",
        "tampilan",
        "apa yang ada di",
        "capture",
    ],
    "coding": [
        "code",
        "kode",
        "function",
        "script",
        "implement",
        "class",
        "refactor",
        "generate",
        "endpoint",
        "api",
        "python",
        "bash",
        "write",
        "tulis",
        "buat file",
        "build",
        "create",
    ],
    "debug": [
        "debug",
        "error",
        "crash",
        "fix",
        "bug",
        "traceback",
        "exception",
        "cuda",
        "pytorch",
        "torch",
        "nan",
        "oom",
        "not working",
        "kenapa",
        "why",
        "gagal",
        "failed",
    ],
    "math": [
        "tensor",
        "matrix",
        "gradient",
        "derivative",
        "integral",
        "backprop",
        "eigenvalue",
        "softmax",
        "calculate",
        "hitung",
        "math",
        "formula",
        "prove",
        "buktikan",
        "solve",
    ],
    "architect": [
        "design",
        "architecture",
        "plan",
        "system",
        "pipeline",
        "struktur",
        "rancang",
        "overview",
        "diagram",
        "framework",
        "strategy",
        "strategi",
    ],
    "analyst": [
        "analyze",
        "analisis",
        "plot",
        "chart",
        "csv",
        "metrics",
        "performance",
        "gpu",
        "training",
        "trend",
        "statistics",
        "compare",
        "nvidia-smi",
        "visualize",
    ],
    "computer": [
        "browse",
        "search for",
        "find online",
        "look up",
        "scrape",
        "website",
        "web page",
        "cari di internet",
        "booking",
        "google",
        "search the web",
        "pdf",
        "excel",
        "spreadsheet",
        "word doc",
        "docx",
        "extract table",
        "read document",
        "baca dokumen",
        "email",
        "inbox",
        "send email",
        "kirim email",
        "mail",
        "reply email",
        "check email",
        "cek email",
        "git status",
        "git commit",
        "git push",
        "git pull",
        "git diff",
        "git stash",
        "commit",
        "push to",
        "pull from",
        "run tests",
        "pytest",
        "lint",
        "ruff",
        "format code",
        "find in code",
        "grep",
        "codebase",
        "db query",
        "monitor",
        "schedule",
        "disk space",
        "memory usage",
        "maintenance",
        "cleanup",
        "services",
        "system check",
        "organize files",
        "find files",
        "sort files",
    ],
    "researcher": [
        "research",
        "paper",
        "study",
        "evidence",
        "cite",
        "source",
        "literature",
        "academic",
        "experiment",
        "hypothesis",
        "jurnal",
    ],
    "marketer": [
        "marketing",
        "ads",
        "campaign",
        "brand",
        "positioning",
        "messaging",
        "customer",
        "acquisition",
        "growth",
        "conversion",
        "funnel",
        "iklan",
    ],
    "devops": [
        "deploy",
        "pipeline",
        "ci cd",
        "docker",
        "k8s",
        "kubernetes",
        "monitoring",
        "logs",
        "alerts",
        "infrastructure",
        "cloud",
    ],
    "pm": [
        "project",
        "roadmap",
        "milestone",
        "sprint",
        "backlog",
        "priority",
        "stakeholder",
        "timeline",
        "scope",
        "deliverable",
    ],
    "reviewer": [
        "review",
        "audit",
        "check code",
        "inspect",
        "quality",
        "code review",
        "periksa",
        "lint",
        "scan",
    ],
}

# Load personality.yaml once (shared between PERSONA_WRAPPER and debate_personas)
_personality_cfg: dict = {}
try:
    _personality_path = Path(__file__).parent.parent / "config" / "personality.yaml"
    if _personality_path.exists():
        import yaml as _yaml

        with _personality_path.open() as _f:
            _personality_cfg = _yaml.safe_load(_f) or {}
        _PERSONA_WRAPPER = _personality_cfg.get("personality_wrapper", "") or ""
    else:
        _PERSONA_WRAPPER = ""
except Exception:
    _PERSONA_WRAPPER = ""
    _personality_cfg = {}

PERSONA_WRAPPER = _PERSONA_WRAPPER

# Aliases for backwards compat
FALLBACK_CHAIN = LEGACY_FALLBACK_CHAIN
TASK_KEYWORDS = LEGACY_TASK_KEYWORDS
DEFAULT_AGENT = "general"


# ── Debate personas (loaded from config/personality.yaml) ─────────────────────
_DEBATE_PERSONAS: dict[str, str] = {}
_DEBATE_PERSONA_MODELS: dict[str, str] = {}
_DEBATE_ICONS: dict[str, str] = {}

try:
    _debate = _personality_cfg.get("debate_personas", {})
    _DEBATE_PERSONAS = {k: v["description"] for k, v in _debate.items()}
    _DEBATE_PERSONA_MODELS = {k: v["model"] for k, v in _debate.items()}
    _DEBATE_ICONS = {k: v["icon"] for k, v in _debate.items()}
except Exception:
    logger.warning("Failed to load debate_personas from config — DEBATE_PERSONAS will be empty")

DEBATE_PERSONAS = _DEBATE_PERSONAS
DEBATE_PERSONA_MODELS = _DEBATE_PERSONA_MODELS
DEBATE_ICONS = _DEBATE_ICONS


# ---------------------------------------------------------------------------
# Compatibility shims — keep existing main.py call-sites working
# ---------------------------------------------------------------------------

ACTIVE_THREADS: dict[str, list[dict]] = {}


def get_model(agent_key: str, use_fallback: bool = False) -> str | None:
    """Return litellm model_id for an agent key.

    Supports both legacy 22-agent keys and new 76-agent slug names.
    """
    # Check legacy map first
    if use_fallback:
        chain = LEGACY_FALLBACK_CHAIN.get(agent_key, LEGACY_FALLBACK_CHAIN["general"])
        return chain[0]
    if agent_key in _LEGACY_AGENT_MODELS:
        return _LEGACY_AGENT_MODELS[agent_key]
    # Check new registry
    agent = AGENT_REGISTRY.get(agent_key)
    if agent:
        return (
            agent.fallback_model_ids[0] if use_fallback and agent.fallback_model_ids else agent.primary_model_id
        ) or agent.primary_model_id
    return None


def get_fallback_chain(agent_key: str) -> list[str]:
    """Return the full fallback chain for an agent key."""
    if agent_key in LEGACY_FALLBACK_CHAIN:
        return LEGACY_FALLBACK_CHAIN[agent_key]
    # Fall back to new registry
    agent = AGENT_REGISTRY.get(agent_key)
    if agent and agent.fallback_model_ids:
        return agent.fallback_model_ids
    return LEGACY_FALLBACK_CHAIN["general"]


def detect_agent(task: str) -> str:
    """Detect which legacy agent best matches the given task.

    This is the SINGLE implementation — called by all code paths.
    Uses keyword matching with regex for fine-grained control.

    Returns an agent key from the legacy 22-agent set
    (vision, coding, debug, math, architect, analyst, computer, general,
     researcher, marketer, devops, pm, humanizer, reviewer, think, owl,
     ag2_researcher, ag2_critic, ag2_synthesizer, code_exec, predictor,
     claude_orchestrator, debate).
    """
    task_lower = task.lower().strip()

    # High-confidence intent overrides to reduce keyword collision noise.
    if re.search(
        r"\b(gradient|derivative|integral|matrix|determinant|eigenvalue|tensor|backprop|softmax)\b", task_lower
    ):
        return "math"
    if re.search(r"\b(traceback|exception|stack trace|bug|debug|not working|error)\b", task_lower):
        return "debug"
    if re.search(
        r"\b(architecture|system design|microservice|structure|structur|framework diagram|blueprint)\b", task_lower
    ):
        return "architect"
    if re.search(r"\b(capital of|tell me a joke|joke)\b", task_lower):
        return "general"

    scores: dict[str, int] = {agent: 0 for agent in LEGACY_TASK_KEYWORDS}
    for agent, keywords in LEGACY_TASK_KEYWORDS.items():
        for kw in keywords:
            kw_norm = kw.strip().lower()
            if not kw_norm:
                continue
            if re.search(r"[a-z0-9]", kw_norm):
                pattern = rf"(?<![a-z0-9]){re.escape(kw_norm)}(?![a-z0-9])"
                if re.search(pattern, task_lower):
                    scores[agent] += 1
            elif kw_norm in task_lower:
                scores[agent] += 1

    # Tie-break preference keeps generic PM/ops keywords from stealing
    # clearly technical tasks when scores are equal.
    tie_break_order = [
        "debug",
        "math",
        "vision",
        "coding",
        "architect",
        "analyst",
        "researcher",
        "devops",
        "pm",
        "reviewer",
        "general",
    ]
    best_agent = max(scores, key=lambda a: scores[a])
    best_score = scores[best_agent]
    if best_score > 0:
        for candidate in tie_break_order:
            if scores.get(candidate, 0) == best_score:
                best_agent = candidate
                break
    if best_score == 0:
        logger.debug("No keyword match — using %s", DEFAULT_AGENT)
        return DEFAULT_AGENT
    logger.debug("Detected agent '%s' (score=%d)", best_agent, best_score)
    return best_agent


def list_agents() -> str:
    """Return HTML table of all agents grouped by department."""
    if not AGENT_REGISTRY:
        # Fallback to legacy display if registry not loaded yet
        lines = ["<b>Babas Agency Swarm — Legacy Agents</b>\n"]
        for key, model in _LEGACY_AGENT_MODELS.items():
            lines.append(f"  <b>{key}</b> → <code>{model}</code>")
        return "\n".join(lines)

    lines = ["<b>🤖 Babas Agency Swarm — 76+ Agents</b>\n"]
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
    ACTIVE_THREADS[thread_id].append(
        {
            "agent": agent,
            "task": task,
            "result": result[:500],
            "timestamp": time.time(),
        }
    )
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
        time_str = datetime.fromtimestamp(turn["timestamp"]).strftime("%H:%M")
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
        ts = datetime.fromtimestamp(turns[-1]["timestamp"]).strftime("%m/%d %H:%M")
        lines.append(f"📌 <b>{tid}</b> — {len(turns)} turns (last: {ts})")
    return "\n".join(lines)


def clear_thread(thread_id: str) -> bool:
    """Delete a thread's history. Returns True if it existed."""
    if thread_id in ACTIVE_THREADS:
        del ACTIVE_THREADS[thread_id]
        return True
    return False


# ---------------------------------------------------------------------------
# Team selection for multi-agent orchestration
# ---------------------------------------------------------------------------


async def select_team(
    task_description: str,
    max_agents: int = 5,
) -> list[AgentDef]:
    """Select the best team of agents for a task using capability + semantic matching.

    Uses a tiered approach:
    1. Keyword capability match (Layer 1)
    2. Semantic similarity (Layer 2)
    3. Diversity filtering to avoid picking agents from same department

    Returns up to max_agents AgentDef objects sorted by relevance.
    """
    task_lower = task_description.lower()
    task_keywords = [w for w in task_lower.split() if len(w) > 3]

    # Layer 1: Keyword matching
    keyword_results = search_by_capability(task_keywords)
    scores: dict[str, float] = {}
    for name, kw_score in keyword_results:
        scores[name] = scores.get(name, 0.0) + kw_score * 2.0

    # Layer 2: Semantic similarity
    semantic_results = semantic_search(task_description, top_k=max_agents * 2)
    for name, sim in semantic_results:
        scores[name] = scores.get(name, 0.0) + sim * 3.0

    if not scores:
        # Ultimate fallback: return general agent
        general = get_agent("general")
        return [general] if general else []

    # Sort by combined score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Diversity filtering: prefer agents from different departments
    selected: list[AgentDef] = []

    for name, _ in ranked:
        agent = get_agent(name)
        if not agent:
            continue
        # Allow up to 2 agents per department for diversity
        dept_count = sum(1 for a in selected if a.department == agent.department)
        if dept_count >= 2:
            continue
        selected.append(agent)
        if len(selected) >= max_agents:
            break

    # Ensure at least 1 agent
    if not selected:
        general = get_agent("general")
        if general:
            selected = [general]

    logger.debug("select_team: selected %d agents for task '%s'", len(selected), task_description[:50])
    return selected


# ── Auto-load at import time ─────────────────────────────────────────────────
# Set env vars BEFORE load_registry() to prevent transformers from making
# network calls that can hang the process at startup (advisory warning checks).
os.environ.setdefault("HF_HUB_DISABLE_EXPERIMENTAL_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("TOKENIZERS_NO_ADVISORY_WARNINGS", "1")

try:
    load_registry()
except Exception:
    logger.warning("Agent registry auto-load failed — will reload on first use")
