"""system_maintenance.py — System health checks and maintenance for Legion.

Disk, memory, GPU, services, cleanup, updates, and driver status.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def _shell(cmd: str, timeout: int = 30) -> str:
    from computer_agent import run_shell
    return await run_shell(cmd, timeout=timeout)


async def check_disk_space(threshold: int = 80) -> str:
    """Check disk usage. Alert if any partition exceeds threshold %."""
    output = await _shell("df -h --output=source,pcent,avail,target 2>/dev/null || df -h")
    lines = output.strip().split("\n")
    alerts = []
    for line in lines[1:]:  # skip header
        parts = line.split()
        if len(parts) >= 2:
            pct_str = parts[1].replace("%", "")
            try:
                pct = int(pct_str)
                if pct >= threshold:
                    alerts.append(f"  ⚠️ {line.strip()}")
            except ValueError:
                pass

    result = f"💾 Disk Usage (threshold: {threshold}%):\n\n"
    if alerts:
        result += "ALERTS:\n" + "\n".join(alerts) + "\n\n"
    result += output
    return result


async def check_memory_usage() -> str:
    """Check RAM and swap usage."""
    mem = await _shell("free -h 2>/dev/null || vm_stat")
    result = "🧠 Memory Usage:\n\n" + mem

    # Check for high memory usage
    mem_detailed = await _shell("free -m 2>/dev/null")
    if mem_detailed and "Mem:" in mem_detailed:
        parts = mem_detailed.split("\n")
        for line in parts:
            if line.startswith("Mem:"):
                fields = line.split()
                if len(fields) >= 3:
                    try:
                        total = int(fields[1])
                        used = int(fields[2])
                        pct = (used / total) * 100 if total > 0 else 0
                        if pct > 85:
                            result += f"\n⚠️ High memory usage: {pct:.0f}%"
                        else:
                            result += f"\n✅ Memory usage: {pct:.0f}%"
                    except (ValueError, ZeroDivisionError):
                        pass
    return result


async def check_gpu_health() -> str:
    """Check GPU status, temperature, memory, and utilization."""
    # Try nvidia-smi first
    nvidia = await _shell("nvidia-smi 2>/dev/null")
    if nvidia and "NVIDIA" in nvidia:
        result = "🎮 GPU Health:\n\n" + nvidia

        # Parse for warnings
        if "ERR!" in nvidia or "N/A" in nvidia:
            result += "\n⚠️ GPU reporting errors or unavailable data"

        # Check temperature
        temp_output = await _shell(
            "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null"
        )
        if temp_output.strip():
            try:
                temp = int(temp_output.strip().split("\n")[0])
                if temp > 85:
                    result += f"\n🔥 GPU temperature: {temp}°C — CRITICAL"
                elif temp > 75:
                    result += f"\n⚠️ GPU temperature: {temp}°C — warm"
                else:
                    result += f"\n✅ GPU temperature: {temp}°C"
            except ValueError:
                pass

        return result

    # Fallback for non-NVIDIA systems
    return "No NVIDIA GPU detected. Run `lspci | grep VGA` to check for other GPUs."


async def check_services(services: str = "") -> str:
    """Check systemd service status.

    services: comma-separated list of service names (e.g. "swarm-bot,nginx,ollama")
    """
    if not services:
        services = "swarm-bot,ollama"

    service_list = [s.strip() for s in services.split(",") if s.strip()]
    lines = ["🔧 Service Status:\n"]

    for svc in service_list:
        status = await _shell(f"systemctl is-active {svc} 2>/dev/null")
        status = status.strip()

        if status == "active":
            icon = "🟢"
        elif status == "inactive":
            icon = "🔴"
        elif status == "failed":
            icon = "❌"
        else:
            icon = "⚪"

        # Get brief description
        desc = await _shell(
            f"systemctl show {svc} --property=Description --value 2>/dev/null"
        )
        desc = desc.strip()[:60] if desc.strip() else svc

        lines.append(f"  {icon} <b>{svc}</b>: {status}")
        if desc and desc != svc:
            lines.append(f"    {desc}")

    return "\n".join(lines)


async def system_cleanup(dry_run: bool = True) -> str:
    """Clean temp files, old logs, pip cache, apt cache.

    dry_run=True shows what would be cleaned without deleting.
    """
    lines = [f"🧹 System Cleanup ({'DRY RUN' if dry_run else 'EXECUTING'}):\n"]

    # 1. Temp files
    tmp_size = await _shell("du -sh /tmp 2>/dev/null | cut -f1")
    lines.append(f"  /tmp: {tmp_size.strip()}")

    # 2. Old logs
    log_size = await _shell(
        "find /var/log -name '*.gz' -o -name '*.old' 2>/dev/null | xargs du -sh 2>/dev/null | tail -1"
    )
    if log_size.strip():
        lines.append(f"  Old logs: {log_size.strip()}")

    # 3. Pip cache
    pip_cache = await _shell("pip cache info 2>/dev/null | head -3")
    if pip_cache.strip():
        lines.append(f"  Pip cache: {pip_cache.strip()}")

    # 4. Apt cache
    apt_size = await _shell("du -sh /var/cache/apt/archives 2>/dev/null | cut -f1")
    if apt_size.strip():
        lines.append(f"  Apt cache: {apt_size.strip()}")

    # 5. Journal logs
    journal_size = await _shell("journalctl --disk-usage 2>/dev/null")
    if journal_size.strip():
        lines.append(f"  Journal: {journal_size.strip()}")

    if not dry_run:
        lines.append("\nCleaning...")
        # Clean old temp files (>7 days)
        await _shell("find /tmp -type f -atime +7 -delete 2>/dev/null")
        # Clean pip cache
        await _shell("pip cache purge 2>/dev/null")
        # Clean apt cache
        await _shell("sudo apt-get clean 2>/dev/null")
        # Vacuum journal logs (keep last 3 days)
        await _shell("sudo journalctl --vacuum-time=3d 2>/dev/null")
        lines.append("✅ Cleanup complete")
    else:
        lines.append("\nRun with dry_run=False to execute cleanup.")

    return "\n".join(lines)


async def check_updates() -> str:
    """Check for available system and pip updates."""
    lines = ["📦 Available Updates:\n"]

    # APT updates
    apt_updates = await _shell(
        "apt list --upgradable 2>/dev/null | grep -c upgradable || echo 0"
    )
    count = apt_updates.strip()
    lines.append(f"  System (apt): {count} packages upgradable")

    # Pip updates
    pip_updates = await _shell(
        "pip list --outdated --format=columns 2>/dev/null | tail -n +3 | head -10"
    )
    if pip_updates.strip():
        pip_count = len(pip_updates.strip().split("\n"))
        lines.append(f"  Python (pip): {pip_count} packages outdated")
        lines.append(f"\n  Top outdated pip packages:\n{pip_updates}")
    else:
        lines.append("  Python (pip): all up to date ✅")

    return "\n".join(lines)


async def driver_status() -> str:
    """Check GPU driver version, CUDA status, and Ollama status."""
    lines = ["🔧 Driver & Runtime Status:\n"]

    # NVIDIA driver
    driver = await _shell("nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null")
    if driver.strip():
        lines.append(f"  NVIDIA driver: {driver.strip()}")
    else:
        lines.append("  NVIDIA driver: not found")

    # CUDA version
    cuda = await _shell("nvcc --version 2>/dev/null | tail -1")
    if cuda.strip():
        lines.append(f"  CUDA: {cuda.strip()}")
    else:
        cuda_alt = await _shell("cat /usr/local/cuda/version.txt 2>/dev/null")
        lines.append(f"  CUDA: {cuda_alt.strip() if cuda_alt.strip() else 'not found'}")

    # PyTorch CUDA
    torch_cuda = await _shell(
        "python3 -c 'import torch; print(f\"PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}\")'  2>/dev/null"
    )
    if torch_cuda.strip():
        lines.append(f"  {torch_cuda.strip()}")

    # Ollama status
    ollama = await _shell("ollama list 2>/dev/null | head -10")
    if ollama.strip():
        model_count = len(ollama.strip().split("\n")) - 1  # minus header
        lines.append(f"\n  Ollama models: {model_count} installed")
        lines.append(f"  {ollama}")
    else:
        lines.append("  Ollama: not running or not installed")

    return "\n".join(lines)


async def full_maintenance_check() -> str:
    """Run all health checks and return a combined report."""
    lines = ["<b>🏥 Full System Health Report</b>\n"]

    # Run all checks
    disk = await check_disk_space()
    memory = await check_memory_usage()
    gpu = await check_gpu_health()
    services = await check_services()
    drivers = await driver_status()
    updates = await check_updates()

    lines.append(disk)
    lines.append("\n" + "─" * 40 + "\n")
    lines.append(memory)
    lines.append("\n" + "─" * 40 + "\n")
    lines.append(gpu)
    lines.append("\n" + "─" * 40 + "\n")
    lines.append(services)
    lines.append("\n" + "─" * 40 + "\n")
    lines.append(drivers)
    lines.append("\n" + "─" * 40 + "\n")
    lines.append(updates)

    return "\n".join(lines)
