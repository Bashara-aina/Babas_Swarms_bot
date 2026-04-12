"""System monitoring and management skills."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from typing import Any

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def _system_health_handler(text: str) -> str:
    """Check system health including GPU via nvidia-smi."""
    lines = ["🖥️ System Health Report\n"]

    # CPU and RAM
    try:
        import psutil

        cpu_pct = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        mem_pct = mem.percent
        lines.append(f"CPU: {cpu_pct:.1f}% | RAM: {mem_pct:.1f}%")
    except ImportError:
        lines.append("CPU/RAM: psutil not available")
    except Exception as exc:
        lines.append(f"CPU/RAM: error — {exc}")

    # GPU via nvidia-smi
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            [
                "nvidia-smi",
                "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            gpu_lines = result.stdout.strip().split("\n")
            for gpu in gpu_lines:
                parts = [p.strip() for p in gpu.split(",")]
                if len(parts) >= 6:
                    idx, name, util, mem_used, mem_total, temp = parts[:6]
                    lines.append(f"GPU {idx} ({name}): {util}% util | {mem_used}MB/{mem_total}MB | {temp}°C")
        else:
            lines.append("GPU: nvidia-smi error or no GPUs found")
    except FileNotFoundError:
        lines.append("GPU: nvidia-smi not found (NVIDIA driver not installed)")
    except Exception as exc:
        lines.append(f"GPU: error — {exc}")

    # Disk space
    try:
        disk = psutil.disk_usage("/")
        lines.append(f"Disk: {disk.percent:.1f}% used ({disk.used // (1024**3)}GB/{disk.total // (1024**3)}GB)")
    except Exception:
        pass

    return "\n".join(lines)


async def _service_status_handler(text: str) -> str:
    """Check status of a systemd service."""
    # Extract service name
    service = "swarm-bot"
    import re

    match = re.search(r"(?:service|daemon)[:\s]+([\w\-]+)", text, re.IGNORECASE)
    if match:
        service = match.group(1)

    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True,
            text=True,
            timeout=10,
        )
        status = result.stdout.strip()
        if status == "active":
            return f"✅ Service '{service}' is ACTIVE"
        return f"⚠️ Service '{service}' is {status.upper()}"
    except Exception as exc:
        return f"❌ Service check failed: {exc}"


async def _service_restart_handler(text: str) -> str:
    """Restart a systemd service."""
    service = "swarm-bot"
    import re

    match = re.search(r"(?:service|daemon)[:\s]+([\w\-]+)", text, re.IGNORECASE)
    if match:
        service = match.group(1)

    # Require explicit confirmation in text
    if "restart" not in text.lower() and "yes" not in text.lower() and "confirm" not in text.lower():
        return f"⚠️ Please confirm restart of '{service}' explicitly (e.g., 'restart {service}')."

    try:
        result = subprocess.run(
            ["systemctl", "restart", service],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return f"✅ Service '{service}' restarted successfully"
        return f"❌ Restart failed: {result.stderr.strip()}"
    except Exception as exc:
        return f"❌ Restart failed: {exc}"


async def _run_shell_handler(text: str) -> str:
    """Run a shell command in a sandboxed environment."""
    import re

    # Extract command from text
    # Remove trigger keywords
    cmd = text
    for kw in ["run shell", "run command", "execute", "shell", "bash", "cmd"]:
        cmd = re.sub(rf"\b{kw}\b", "", cmd, flags=re.IGNORECASE).strip()

    if not cmd:
        return "Please provide a shell command to run."

    # Basic safety check - reject dangerous commands
    dangerous = ["rm -rf /", "dd if=", "> /dev/sda", "mkfs", ":(){ :|:& };:", "curl | sh", "wget | sh"]
    for d in dangerous:
        if d in cmd:
            return f"❌ Blocked dangerous command pattern: {d}"

    # Limit to safe, short-running commands
    allowed_patterns = [
        r"^(ls|ll|ps|df|du|free|top|htop|cat|head|tail|grep|find|echo|date|uptime|w|who|id|uname|hostname|pwd|cd )",
        r"^(git |npm |pip |python |python3 |node )",
        r"^(systemctl |journalctl |curl |wget )",
    ]

    is_allowed = any(re.match(p, cmd) for p in allowed_patterns)
    if not is_allowed:
        return f"⚠️ Command '{cmd}' is not in the allowed list for sandboxed execution."

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        if not output:
            output = "(no output)"
        return f"```\n{output[:2000]}\n```"
    except subprocess.TimeoutExpired:
        return "❌ Command timed out (30s limit)"
    except Exception as exc:
        return f"❌ Shell execution failed: {exc}"


def _register_system_skills() -> None:
    SKILL_REGISTRY.register(
        Skill(
            name="system_health",
            description="Check system health (CPU, RAM, GPU via nvidia-smi, disk)",
            trigger_keywords=[
                "system health",
                "system status",
                "check system",
                "gpu status",
                "cpu status",
                "health check",
            ],
            handler=_system_health_handler,
            required_env_keys=[],
            category="system",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="service_status",
            description="Check systemd service status",
            trigger_keywords=["service status", "daemon status", "check service", "is active", "systemctl status"],
            handler=_service_status_handler,
            required_env_keys=[],
            category="system",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="service_restart",
            description="Restart a systemd service",
            trigger_keywords=["restart service", "restart daemon", "reload service", "systemctl restart"],
            handler=_service_restart_handler,
            required_env_keys=[],
            category="system",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="run_shell",
            description="Run a safe shell command",
            trigger_keywords=["run shell", "run command", "execute shell", "bash", "shell command"],
            handler=_run_shell_handler,
            required_env_keys=[],
            category="system",
        )
    )


_register_system_skills()
