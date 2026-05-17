"""Boot sequence for the Ruflo Autonomy Layer.

Implements Part II of the Autonomy Layer master prompt v2:
  - BOOT STEP 1: Health check (system_status + doctor)
  - BOOT STEP 2: Restore last session context
  - BOOT STEP 3: Load neural patterns
  - BOOT STEP 4: Dispatch background workers
  - BOOT STEP 5: Register hooks
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Load ruflo_model from config/models.yaml
_ruflo_cfg_path = Path("config/models.yaml")
if _ruflo_cfg_path.exists():
    with _ruflo_cfg_path.open() as f:
        _cfg = yaml.safe_load(f)
    _ruflo_model_key = _cfg.get("ruflo_model", "minimax-m2-7")
    _ruflo_model_id = _cfg.get("models", {}).get(_ruflo_model_key, {}).get("model_id", "minimax-coding-plan/MiniMax-M2.7")
    RUFLO_MODEL = _cfg.get("models", {}).get(_ruflo_model_key, {}).get("model_id", "minimax-coding-plan/MiniMax-M2.7")
else:
    RUFLO_MODEL = "minimax-coding-plan/MiniMax-M2.7"

ruflo_available = True
_ruflo_client = None

try:
    from core.mcp_client import MCPClient
    _ruflo_client = MCPClient()
    ruflo_available = True
except Exception as e:
    logger.warning("MCP client unavailable, ruflo will run in degraded mode: %s", e)
    ruflo_available = False


@dataclass
class BootResult:
    healthy: bool = False
    session_restored: bool = False
    patterns_loaded: bool = False
    workers_dispatched: int = 0
    hooks_registered: int = 0
    error_message: str | None = None


async def _call_ruflo(tool: str, args: dict | None = None) -> dict:
    """Call a ruflo tool via MCP client. Returns {} on failure."""
    if not ruflo_available or _ruflo_client is None:
        return {}
    try:
        result = await _ruflo_client.call_tool("ruflo", tool, args or {})
        # call_tool returns str (JSON text or error message), not a list
        if isinstance(result, str) and result.startswith("{"):
            import json
            try:
                return json.loads(result)
            except Exception:
                return {}
        return {}
    except Exception as e:
        logger.debug("ruflo call %s failed: %s", tool, e)
        return {}


async def run_boot_sequence() -> BootResult:
    """Execute the full boot sequence. Returns result summary.

    All steps run silently. On failure only, one line is printed.
    Total target: < 7 seconds.
    """
    result = BootResult()
    start = asyncio.get_event_loop().time()

    # STEP 1: Health check (parallel)
    status_task = asyncio.create_task(_call_ruflo("system_status"))
    doctor_task = asyncio.create_task(_call_ruflo("doctor", {"deep": False}))

    status_data, doctor_data = await asyncio.gather(status_task, doctor_task)

    if status_data and doctor_data:
        all_passed = doctor_data.get("all_passed", False)
        if not all_passed:
            checks = doctor_data.get("checks", [])
            failed = [c["name"] for c in checks if c.get("status") != "pass"]
            logger.warning("Ruflo health checks failed: %s", failed)
    else:
        pass

    result.healthy = bool(status_data)

    if not result.healthy:
        result.error_message = "⚠ Ruflo offline — run: python3 -m mcp_servers.ruflo_mcp_server"
        logger.warning(result.error_message)
        return result

    # STEP 2: Restore context
    restore_data = await _call_ruflo("session_restore", {"name": "latest"})
    result.session_restored = restore_data.get("success", False)

    # STEP 3: Load neural patterns
    patterns_data = await _call_ruflo("neural_patterns", {"action": "list"})
    result.patterns_loaded = "patterns" in str(patterns_data)

    # STEP 4: Dispatch background workers (fire-and-forget)
    workers = [
        ("audit", "session_start"),
        ("memory_consolidate", "session_end"),
        ("testgaps", "after_implementation"),
        ("optimize", "every_5_tasks"),
    ]
    for worker_name, trigger in workers:
        disp = await _call_ruflo("worker/dispatch", {
            "trigger": worker_name,
            "context": trigger,
        })
        if disp.get("success"):
            result.workers_dispatched += 1

    # STEP 5: Initialize hooks in project (idempotent — creates .claude/settings.json and .claude/hooks/)
    init_result = await _call_ruflo("hooks_init", {
        "path": "/home/newadmin/swarm-bot",
        "template": "standard",
    })
    if init_result.get("success") or "settingsJson" in str(init_result):
        result.hooks_registered = init_result.get("hooks", {}).get("configured", 9)

    elapsed = asyncio.get_event_loop().time() - start
    logger.info(
        "Ruflo boot complete: healthy=%s, workers=%d, hooks=%d, elapsed=%.1fs",
        result.healthy,
        result.workers_dispatched,
        result.hooks_registered,
        elapsed,
    )

    return result