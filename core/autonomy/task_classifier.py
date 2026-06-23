"""Task classifier for the Autonomy Layer.

Implements Part III of the Autonomy Layer master prompt v2:
  - Classify every incoming message into DIRECT / LITE / SWARM mode
  - Decision is based on: file count, domain count, phase count
  - Also checks neural memory for confident predictions
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum
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
_ruflo_client = None

try:
    from core.mcp_client import MCPClient
    _ruflo_client = MCPClient()
except Exception:
    ruflo_available = False


class ExecutionMode(Enum):
    DIRECT = "direct"
    LITE = "lite"
    SWARM = "swarm"


@dataclass
class Classification:
    mode: ExecutionMode
    file_count: int
    domain_count: int
    phase_count: int
    neural_confidence: float = 0.0
    reason: str = ""


async def _call_ruflo(tool: str, args: dict | None = None) -> dict:
    if not ruflo_available or _ruflo_client is None:
        return {}
    try:
        result = await _ruflo_client.call_tool("ruflo", tool, args or {})
        # call_tool returns str (JSON text or error message), not a list
        if isinstance(result, str) and result.startswith("{"):
            import json
            return json.loads(result)
        return {}
    except Exception:
        return {}


def count_files(text: str) -> int:
    """Estimate file count from user message."""
    patterns = [
        r'\b(?:handlers?|core/|agents?/|tools?|config/|tests?|lib/)[^\s]+?\.(?:py|js|ts|jsx|tsx|md|yaml|json|toml)\b',
        r'(?:file|files|module|script)[:\s]+([^\n]+)',
        r'`[^`]+`',
    ]
    matches = set()
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            if m.group(0).strip():
                matches.add(m.group(0).strip())
    return max(len(matches), 1)


def count_domains(text: str) -> int:
    """Count distinct domain categories mentioned."""
    domain_keywords = {
        "telegram": ["telegram", "bot", "aiogram", "message", "chat"],
        "auth": ["auth", "login", "password", "session", "jwt", "token"],
        "database": ["db", "database", "sql", "postgres", "sqlite", "mongodb"],
        "api": ["api", "endpoint", "rest", "graphql", "http"],
        "frontend": ["frontend", "ui", "react", "vue", "html", "css", "template"],
        "ml": ["ml", "ai", "model", "training", "inference", "tensor", "torch"],
        "devops": ["docker", "kubernetes", "deploy", "ci/cd", "github actions"],
        "security": ["security", "auth", "encryption", "pii", "secret"],
        "wiki": ["wiki", "obsidian", "knowledge", "documentation"],
    }
    text_lower = text.lower()
    found = set()
    for domain, keywords in domain_keywords.items():
        if any(kw in text_lower for kw in keywords):
            found.add(domain)
    return max(len(found), 1)


def count_phases(text: str) -> int:
    """Detect number of execution phases implied."""
    phase_indicators = {
        "research": ["research", "investigate", "find information", "look up", "search for", "crawl", "scrape"],
        "plan": ["plan", "design", "architect", "approach", "strategy"],
        "implement": ["implement", "write code", "create", "add", "build", "modify", "edit", "change", "refactor"],
        "test": ["test", "pytest", "unittest", "QA", "verify", "check"],
        "review": ["review", "audit", "check", "validate", "inspect"],
        "deploy": ["deploy", "ship", "release", "push to prod", "publish"],
    }
    text_lower = text.lower()
    phases_found = set()
    for phase, indicators in phase_indicators.items():
        if any(ind in text_lower for ind in indicators):
            phases_found.add(phase)
    return max(len(phases_found), 1)


def _classify_from_counts(file_count: int, domain_count: int, phase_count: int) -> ExecutionMode:
    if file_count >= 5 or domain_count >= 3 or phase_count >= 3:
        return ExecutionMode.SWARM
    if file_count >= 2 or domain_count >= 2 or phase_count >= 2:
        return ExecutionMode.LITE
    return ExecutionMode.DIRECT


async def classify_task(user_message: str) -> Classification:
    """Classify a user task into DIRECT / LITE / SWARM mode.

    Runs neural prediction + memory search in parallel with count analysis.
    Takes < 100ms total.
    """
    file_count = count_files(user_message)
    domain_count = count_domains(user_message)
    phase_count = count_phases(user_message)

    # Check neural memory for confident prediction (run in parallel)
    neural_task = _call_ruflo("neural_predict", {
        "input": user_message[:200],
    })
    memory_task = _call_ruflo("memory_search", {
        "query": user_message,
        "namespace": "all",
        "limit": 3,
    })

    neural_data, memory_data = await asyncio.gather(neural_task, memory_task)

    # Extract confidence from neural prediction
    neural_confidence = 0.0
    if neural_data and "predictions" in neural_data:
        preds = neural_data["predictions"]
        if preds and isinstance(preds, list):
            neural_confidence = max(p.get("confidence", 0) for p in preds)

    # Memory hit detection
    has_memory_hit = bool(memory_data and memory_data.get("count", 0) > 0)

    # Override from neural if high confidence
    mode = _classify_from_counts(file_count, domain_count, phase_count)
    if neural_confidence > 0.75 and has_memory_hit:
        if neural_confidence >= 0.9:
            mode = ExecutionMode.SWARM
        elif neural_confidence >= 0.8 and mode == ExecutionMode.DIRECT:
            mode = ExecutionMode.LITE

    reason = (
        f"files={file_count}, domains={domain_count}, phases={phase_count}, "
        f"neural_conf={neural_confidence:.2f}, memory_hit={has_memory_hit}"
    )

    logger.debug("Task classification: %s — %s", mode.value, reason)

    return Classification(
        mode=mode,
        file_count=file_count,
        domain_count=domain_count,
        phase_count=phase_count,
        neural_confidence=neural_confidence,
        reason=reason,
    )
