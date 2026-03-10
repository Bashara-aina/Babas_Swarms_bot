"""devops.py — DevOps automation for Legion.

Vulnerability scanning, dependency updates, GPU health,
training log watcher, VPS deployment.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


async def _run(cmd: str, timeout: int = 60) -> str:
    """Run a shell command."""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    out = stdout.decode("utf-8", errors="replace").strip()
    err = stderr.decode("utf-8", errors="replace").strip()
    return out if proc.returncode == 0 else f"exit {proc.returncode}\n{out}\n{err}".strip()


async def check_vulnerabilities(project_path: str = ".") -> str:
    """Run pip-audit or safety check on requirements.txt."""
    path = Path(project_path)
    req_file = path / "requirements.txt"

    if not req_file.exists():
        return f"No requirements.txt found in {project_path}"

    # Try pip-audit first
    result = await _run(f"pip-audit -r '{req_file}' 2>&1", timeout=120)
    if "command not found" in result.lower() or "No module" in result.lower():
        # Try safety
        result = await _run(f"safety check -r '{req_file}' 2>&1", timeout=120)
        if "command not found" in result.lower():
            return (
                "Neither pip-audit nor safety installed.\n"
                "Install: pip install pip-audit\n"
                "Or: pip install safety"
            )

    return result[:4000]


async def dependency_updates(project_path: str = ".") -> str:
    """Check for outdated pip packages."""
    result = await _run("pip list --outdated --format=columns 2>&1", timeout=60)
    if not result or "Package" not in result:
        return "All packages up to date."
    return f"<b>Outdated Packages</b>\n<pre>{result[:3500]}</pre>"


async def check_gpu_health() -> str:
    """Enhanced GPU status: temp, VRAM, utilization, processes, power."""
    result = await _run(
        "nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,"
        "memory.used,memory.total,power.draw,power.limit,fan.speed "
        "--format=csv,noheader,nounits 2>/dev/null",
        timeout=10,
    )

    if "No GPU" in result or "command not found" in result.lower():
        return "No NVIDIA GPU detected."

    lines = ["<b>GPU Health</b>\n"]
    for i, gpu_line in enumerate(result.strip().split("\n")):
        parts = [p.strip() for p in gpu_line.split(",")]
        if len(parts) >= 7:
            name, temp, util, mem_used, mem_total, power, power_limit = parts[:7]
            fan = parts[7] if len(parts) > 7 else "N/A"

            # Temperature warning
            temp_icon = "🟢" if int(temp) < 70 else "🟡" if int(temp) < 85 else "🔴"

            lines.append(f"  {temp_icon} <b>{name}</b>")
            lines.append(f"    Temp: {temp}C | Util: {util}%")
            lines.append(f"    VRAM: {mem_used}/{mem_total} MB")
            lines.append(f"    Power: {power}/{power_limit} W | Fan: {fan}%")

    # Running GPU processes
    procs = await _run(
        "nvidia-smi --query-compute-apps=pid,name,used_memory "
        "--format=csv,noheader,nounits 2>/dev/null",
        timeout=10,
    )
    if procs and "No running" not in procs:
        lines.append("\n<b>GPU Processes</b>")
        for proc_line in procs.strip().split("\n")[:5]:
            parts = [p.strip() for p in proc_line.split(",")]
            if len(parts) >= 3:
                lines.append(f"  PID {parts[0]}: {parts[1]} ({parts[2]} MB)")

    return "\n".join(lines)


async def watch_training_log(
    log_path: str,
    callback: Optional[Callable[[str], Coroutine]] = None,
    check_interval: int = 30,
    max_checks: int = 0,  # 0 = infinite
) -> str:
    """Tail a training log file, call callback on events.

    Events: loss spike, NaN, training complete, new best model.
    Returns the last alert message or "monitoring started".
    """
    path = Path(log_path)
    if not path.exists():
        return f"Log file not found: {log_path}"

    last_size = path.stat().st_size
    last_loss = None
    check_count = 0
    alerts = []

    while max_checks == 0 or check_count < max_checks:
        check_count += 1
        await asyncio.sleep(check_interval)

        if not path.exists():
            alert = f"Training log disappeared: {log_path}"
            if callback:
                await callback(alert)
            return alert

        current_size = path.stat().st_size
        if current_size <= last_size:
            continue

        # Read new content
        with open(path, "r", errors="replace") as f:
            f.seek(last_size)
            new_content = f.read()
        last_size = current_size

        # Check for events
        alert_msg = ""

        # NaN detection
        if "nan" in new_content.lower() or "inf" in new_content.lower():
            alert_msg = f"NaN/Inf detected in training!\n{new_content[-200:]}"

        # Loss spike
        loss_matches = re.findall(r"loss[:\s]*([0-9.]+)", new_content.lower())
        if loss_matches:
            current_loss = float(loss_matches[-1])
            if last_loss is not None and current_loss > last_loss * 2:
                alert_msg = f"Loss spike: {last_loss:.4f} -> {current_loss:.4f}"
            last_loss = current_loss

        # Training complete
        if "training complete" in new_content.lower() or "finished training" in new_content.lower():
            alert_msg = f"Training completed!\n{new_content[-300:]}"

        # New best model
        if "best model" in new_content.lower() or "new best" in new_content.lower():
            alert_msg = f"New best model saved!\n{new_content[-200:]}"

        if alert_msg:
            alerts.append(alert_msg)
            if callback:
                await callback(alert_msg)

    return f"Watch completed. {len(alerts)} alerts raised."


async def deploy_to_vps(
    project_path: str,
    host: str,
    user: str,
    service_name: str = "",
) -> str:
    """rsync project to VPS, restart systemd service."""
    path = Path(project_path)
    if not path.exists():
        return f"Project not found: {project_path}"

    results = []

    # rsync
    rsync_cmd = (
        f"rsync -avz --exclude='.venv' --exclude='__pycache__' "
        f"--exclude='.git' --exclude='node_modules' "
        f"'{project_path}/' {user}@{host}:~/{path.name}/"
    )
    result = await _run(rsync_cmd, timeout=120)
    results.append(f"rsync: {result[:200]}")

    # Restart service if specified
    if service_name:
        restart = await _run(
            f"ssh {user}@{host} 'sudo systemctl restart {service_name}'",
            timeout=30,
        )
        results.append(f"restart: {restart}")

        # Check status
        await asyncio.sleep(3)
        status = await _run(
            f"ssh {user}@{host} 'sudo systemctl is-active {service_name}'",
            timeout=10,
        )
        results.append(f"status: {status}")

    return "\n".join(results)
