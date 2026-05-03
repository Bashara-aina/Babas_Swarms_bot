"""
lib/legiona/tools/system_monitor.py
Async system monitoring tools — processes, services, network, stats.
All functions are async, return str, have try/except guards.
SECURITY: list_processes and system_stats are unrestricted.
Destructive operations (kill_process) require explicit confirmation.
"""

from __future__ import annotations

import asyncio
import shlex

SHELL_TIMEOUT = 30


async def _run(cmd: str, timeout: int = 30) -> str:
    """Run a shell command async, return stdout or error message."""
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=timeout,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return f"ERROR: {stderr.decode(errors='replace').strip() or 'command failed'}"
        return stdout.decode(errors="replace") or "OK"
    except TimeoutError:
        return f"ERROR: timeout after {timeout}s"
    except Exception as exc:
        return f"ERROR: {exc}"


# ─── Process management ────────────────────────────────────────────────────────

async def list_processes(
    sort_by: str = "cpu",
    top_n: int = 20,
    user: str | None = None,
) -> str:
    """
    List top processes by CPU or memory usage.
    SECURITY: Unrestricted — shows all processes to owner only.
    """
    valid_sorts = {"cpu", "mem", "pid", "time", "rss"}
    if sort_by not in valid_sorts:
        return f"ERROR: sort_by must be one of {valid_sorts}"

    # Build ps command
    if user:
        cmd = f"ps aux --sort=-%{sort_by} -U {shlex.quote(user)} | head -n {top_n + 1}"
    else:
        cmd = f"ps aux --sort=-%{sort_by} | head -n {top_n + 1}"

    result = await _run(cmd, timeout=15)
    if result.startswith("ERROR"):
        return result

    lines = result.splitlines()
    if not lines:
        return "(no processes found)"

    header = lines[0] if lines else ""
    body = "\n".join(lines[1:top_n + 1]) if len(lines) > 1 else "(empty)"
    return f"=== Top {top_n} processes by {sort_by} ===\n{header}\n{body}"


async def kill_process(pid: int, signal: str = "TERM", confirm: bool = False) -> str:
    """
    Kill a process by PID. Set signal=9 for SIGKILL.
    SECURITY: Destructive. Requires confirm=True to actually send signal.
    """
    if not confirm:
        return (
            f"PREVIEW (confirm=False — no signal sent) for PID {pid}:\n"
            f"Would send {signal} to process {pid}.\n"
            f"Set confirm=True to execute."
        )

    valid_signals = {"TERM", "KILL", "HUP", "INT", "QUIT"}
    if signal not in valid_signals:
        return f"ERROR: signal must be one of {valid_signals}"

    cmd = f"kill -{signal} {pid}"
    result = await _run(cmd, timeout=10)
    if result.startswith("ERROR"):
        return f"Failed to kill PID {pid}: {result}"
    return f"OK: sent {signal} to PID {pid}"


async def process_tree(pid: int = 1) -> str:
    """
    Show process tree starting from PID (default: init).
    SECURITY: Unrestricted.
    """
    cmd = f"pstree -a -p {pid} 2>/dev/null || ps --forest -o pid,ppid,cmd -g {pid}"
    result = await _run(cmd, timeout=15)
    if result.startswith("ERROR"):
        return result
    return f"=== Process tree for PID {pid} ===\n{result}"


# ─── System stats ─────────────────────────────────────────────────────────────

async def system_stats() -> str:
    """
    Report CPU, memory, uptime, and load averages.
    SECURITY: Unrestricted.
    """
    stats = {}

    # CPU info
    cpu_result = await _run("cat /proc/cpuinfo | grep 'model name' | head -1", timeout=5)
    if not cpu_result.startswith("ERROR"):
        stats["cpu_model"] = cpu_result.strip()

    # Load average
    load_result = await _run("cat /proc/loadavg", timeout=5)
    if not load_result.startswith("ERROR"):
        parts = load_result.strip().split()
        if len(parts) >= 3:
            stats["load_1m"] = parts[0]
            stats["load_5m"] = parts[1]
            stats["load_15m"] = parts[2]

    # Memory
    mem_result = await _run("free -h", timeout=5)
    if not mem_result.startswith("ERROR"):
        stats["memory"] = mem_result

    # Uptime
    uptime_result = await _run("uptime", timeout=5)
    if not uptime_result.startswith("ERROR"):
        stats["uptime"] = uptime_result.strip()

    # Disk
    disk_result = await _run("df -h / /home 2>/dev/null", timeout=5)
    if not disk_result.startswith("ERROR"):
        stats["disk"] = disk_result

    # Build output
    lines = ["=== System Stats ==="]
    for key, value in stats.items():
        lines.append(f"\n--- {key.upper()} ---")
        lines.append(value)

    return "\n".join(lines) if lines else "ERROR: could not gather stats"


async def cpu_usage_per_core() -> str:
    """
    Report per-core CPU usage from /proc/stat.
    SECURITY: Unrestricted.
    """
    cmd = "top -bn1 | grep 'Cpu(s)' || mpstat 1 1 || cat /proc/stat | grep ^cpu"
    result = await _run(cmd, timeout=10)
    if result.startswith("ERROR"):
        return result
    return f"=== Per-Core CPU ===\n{result}"


async def memory_usage() -> str:
    """
    Report detailed memory usage.
    SECURITY: Unrestricted.
    """
    cmd = "free -h && echo '--- /proc/meminfo ---' && cat /proc/meminfo | head -20"
    result = await _run(cmd, timeout=10)
    if result.startswith("ERROR"):
        return result
    return f"=== Memory Usage ===\n{result}"


# ─── Services ─────────────────────────────────────────────────────────────────

async def running_services() -> str:
    """
    List running systemd services.
    SECURITY: Unrestricted.
    """
    cmd = "systemctl list-units --type=service --state=running --no-pager --no-legend"
    result = await _run(cmd, timeout=15)
    if result.startswith("ERROR"):
        return f"ERROR: {result}\n(May need sudo: try journalctl access)"
    if not result.strip():
        return "(no running services found)"
    lines = result.strip().splitlines()
    formatted = ["=== Running Services ==="]
    for line in lines[:50]:
        parts = line.split(maxsplit=4)
        if len(parts) >= 4:
            name = parts[0].replace(".service", "")
            state = parts[3]
            desc = parts[4] if len(parts) > 4 else ""
            formatted.append(f"  {state:8} {name:40} {desc}")
    return "\n".join(formatted)


async def service_status(service_name: str) -> str:
    """
    Get status of a specific systemd service.
    SECURITY: Unrestricted.
    """
    safe_name = shlex.quote(service_name)
    cmd = f"systemctl status {safe_name} --no-pager"
    result = await _run(cmd, timeout=15)
    if result.startswith("ERROR"):
        return f"ERROR: {result}\n(May need sudo for detailed status)"
    return f"=== Service: {service_name} ===\n{result}"


async def failed_services() -> str:
    """
    List failed systemd services.
    SECURITY: Unrestricted.
    """
    cmd = "systemctl list-units --type=service --state=failed --no-pager --no-legend"
    result = await _run(cmd, timeout=15)
    if result.startswith("ERROR"):
        return f"ERROR: {result}"
    if not result.strip():
        return "(no failed services)"
    return f"=== Failed Services ===\n{result.strip()}"


# ─── Network ───────────────────────────────────────────────────────────────────

async def network_connections() -> str:
    """
    Show active network connections (ss -tunap).
    SECURITY: Unrestricted.
    """
    cmd = "ss -tunap 2>/dev/null || netstat -tunap 2>/dev/null || ss -tunp"
    result = await _run(cmd, timeout=15)
    if result.startswith("ERROR"):
        return f"ERROR: {result}"
    lines = result.strip().splitlines()
    if not lines:
        return "(no connections found)"
    return f"=== Active Connections ({len(lines)-1} entries) ===\n" + "\n".join(lines[:50])


async def listening_ports() -> str:
    """
    Show listening ports and their processes.
    SECURITY: Unrestricted.
    """
    cmd = "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null"
    result = await _run(cmd, timeout=15)
    if result.startswith("ERROR"):
        return f"ERROR: {result}"
    lines = result.strip().splitlines()
    if not lines:
        return "(no listening ports found)"
    return "=== Listening Ports ===\n" + "\n".join(lines)


async def who_is_logged_in() -> str:
    """
    Show who is currently logged in and their activity.
    SECURITY: Unrestricted.
    """
    commands = [
        "who",
        "w",
        "lastlog | tail -10",
    ]
    results = []
    for cmd in commands:
        result = await _run(cmd, timeout=10)
        if not result.startswith("ERROR"):
            results.append(f"--- {cmd} ---\n{result}")

    if not results:
        return "ERROR: could not get login info"
    return "=== Logged-in Users ===\n\n" + "\n\n".join(results)


async def network_stats() -> str:
    """
    Show network interface statistics.
    SECURITY: Unrestricted.
    """
    cmd = "ip -s link && echo '--- /proc/net/dev ---' && cat /proc/net/dev"
    result = await _run(cmd, timeout=10)
    if result.startswith("ERROR"):
        return f"ERROR: {result}"
    return f"=== Network Stats ===\n{result}"


# ─── Disk I/O ────────────────────────────────────────────────────────────────

async def disk_io() -> str:
    """
    Show disk I/O statistics using iostat or /proc/diskstats.
    SECURITY: Unrestricted.
    """
    cmd = "iostat -x 1 2 2>/dev/null || cat /proc/diskstats"
    result = await _run(cmd, timeout=15)
    if result.startswith("ERROR"):
        return f"ERROR: {result}"
    return f"=== Disk I/O ===\n{result}"
