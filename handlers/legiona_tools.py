"""
handlers/legiona_tools.py
Telegram command handlers wiring Legiona system tools to user commands.
All handlers are async, use is_allowed() auth, send_chunked() output.
SECURITY: File operations restricted to project directory. Destructive ops need confirm.
"""

from __future__ import annotations

import contextlib
import html
import re

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message

from core.intent_classifier import classify_intent
from handlers.shared import is_allowed, send_chunked
from lib.legiona.tools import (
    desktop_control,
    fs_control,
    log_reader,
    system_monitor,
)
from tools.computer_use_agent import computer_use_loop

router = Router(name="legiona_tools")


# ─── Auto-route helper for system commands ─────────────────────────────────────

SYSTEM_COMMAND_PATTERNS = {
    "/logs": "tail log, grep log, list logs, check errors, journalctl",
    "/ps": "list processes, cpu usage, memory usage",
    "/kill": "kill process with signal",
    "/sys": "system stats, cpu, memory, disk, network, services",
    "/ls": "list directory contents",
    "/find": "search files by pattern",
    "/grep": "grep pattern in files",
    "/read": "read file contents",
    "/write": "write content to file",
    "/disk": "disk usage statistics",
    "/window": "list windows, switch, close, minimize, desktop info",
    "/screen": "take screenshot",
    "/clipboard": "get or set clipboard content",
    "/type": "type text on desktop",
    "/key": "press key combination",
    "/service": "service status, list failed services",
    "/tree": "process tree view",
}

SHELL_BLOCKLIST: list[str] = []

SHELL_BLOCKPAT = re.compile(
    "|".join(f"({p})" for p in SHELL_BLOCKLIST),
    re.IGNORECASE,
)


def _is_blocked(cmd: str) -> bool:
    return bool(SHELL_BLOCKPAT.search(cmd))


# ─── Intent routing helper for system commands ──────────────────────────────────

async def _route_via_intent(message: Message, cmd_name: str, cmd_args: str) -> bool:
    """Route system command through intent classifier to computer_use_loop.

    Returns True if routed (handled), False if should fall through to direct handler.
    """
    # Build natural language task description
    task_desc = f"{cmd_name} {cmd_args}".strip()

    # Classify the intent
    intent_result = classify_intent(task_desc)

    # Only route if it's a system_command intent detected with high confidence
    if intent_result.detected_intent == "system_command" and intent_result.confidence >= 0.7:
        status_msg = await message.answer("🔄 Routing through cognitive system...")

        try:
            result = await computer_use_loop(
                task=task_desc,
                max_steps=5,
            )

            await status_msg.delete()

            if result.success:
                summary = f"✅ {cmd_name} completed\n{result.final_state[:300]}"
                await send_chunked(message, summary)
            else:
                await message.answer(f"⚠️ {result.error or 'Task did not complete successfully'}")

            return True  # Handled via intent routing

        except Exception:
            await status_msg.delete()
            # Fall through to direct handler on routing failure
            return False

    # Not routed - fall through to direct handler
    return False


# ─── /logs — Log reading tools ───────────────────────────────────────────────

@router.message(Command("logs"))
async def cmd_logs(message: Message) -> None:
    """Tail, grep, or list system logs. Usage: /logs [tail|grep|list|errors|journal] [args]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/logs").strip()
    if await _route_via_intent(message, "/logs", raw):
        return

    args = message.text.split(maxsplit=2)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 2:
        await message.answer(
            "Usage:\n"
            "/logs tail [name=syslog] [n=50]    — tail last N lines\n"
            "/logs grep [name] [pattern]        — grep log\n"
            "/logs list                          — list known logs\n"
            "/logs errors [name=syslog]          — recent errors\n"
            "/logs journal [unit] [n=50]        — journalctl\n\n"
            "Known logs: auth, syslog, dmesg, kern, nginx_access, "
            "nginx_error, docker, telegram_bot, systemd"
        )
        return

    subcmd = args[1].lower()
    parts = args[2].split() if len(args) > 2 else []  # type: ignore[reportOptionalMemberAccess]

    # ── Progress tracking for long-running operations ───────────────────────
    status_msg: types.Message | None = None
    try:
        if subcmd == "tail":
            status_msg = await message.answer("📜 Tailing log...")
            log_name = parts[0] if parts else "syslog"
            num = int(parts[1]) if len(parts) > 1 else 50
            result = await log_reader.tail_log(log_name, num_lines=num)
            output = {"success": True, "data": result, "error": None}

        elif subcmd == "grep":
            if len(parts) < 2:
                output = {"success": False, "data": None, "error": "/logs grep [name] [pattern]"}
            else:
                status_msg = await message.answer(f"🔍 Grepping pattern in {parts[0]}...")
                result = await log_reader.grep_log(parts[0], parts[1])
                output = {"success": True, "data": result, "error": None}

        elif subcmd == "list":
            result = await log_reader.list_all_logs()
            output = {"success": True, "data": result, "error": None}

        elif subcmd == "errors":
            status_msg = await message.answer("🚨 Fetching recent errors...")
            log_name = parts[0] if parts else "syslog"
            num = int(parts[1]) if len(parts) > 1 else 30
            result = await log_reader.get_recent_errors(log_name, num_lines=num)
            output = {"success": True, "data": result, "error": None}

        elif subcmd == "journal":
            status_msg = await message.answer("📋 Following journal...")
            unit = parts[0] if parts else "systemd"
            num = int(parts[1]) if len(parts) > 1 else 50
            result = await log_reader.follow_journal(unit, num_lines=num)
            output = {"success": True, "data": result, "error": None}

        else:
            output = {"success": False, "data": None, "error": f"unknown subcmd '{subcmd}'"}

    except Exception as exc:
        output = {"success": False, "data": None, "error": str(exc)}

    # ── Cleanup progress message ─────────────────────────────────────────────
    if status_msg:
        with contextlib.suppress(Exception):
            await status_msg.delete()

    # ── Format structured output ───────────────────────────────────────────
    if output["success"]:
        await send_chunked(message, output["data"])
    else:
        await send_chunked(message, f"ERROR: {output['error']}")


# ─── /ps — Process management ─────────────────────────────────────────────────

@router.message(Command("ps"))
async def cmd_ps(message: Message) -> None:
    """List top processes. Usage: /ps [cpu|mem] [top=20] [user=]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/ps").strip()
    if await _route_via_intent(message, "/ps", raw):
        return

    args = message.text.split(maxsplit=3)  # type: ignore[reportOptionalMemberAccess]
    sort_by = args[1] if len(args) > 1 else "cpu"
    top_n = int(args[2]) if len(args) > 2 else 20
    user = args[3] if len(args) > 3 else None

    if sort_by not in ("cpu", "mem", "pid", "time", "rss"):
        await message.answer("sort_by must be: cpu, mem, pid, time, or rss")
        return

    status_msg: types.Message | None = None
    try:
        status_msg = await message.answer(f"📊 Fetching top {top_n} processes by {sort_by}...")
        result = await system_monitor.list_processes(
            sort_by=sort_by, top_n=top_n, user=user
        )
        output = {"success": True, "data": result, "error": None}
    except Exception as exc:
        output = {"success": False, "data": None, "error": str(exc)}

    if status_msg:
        with contextlib.suppress(Exception):
            await status_msg.delete()

    if output["success"]:
        await send_chunked(message, output["data"])
    else:
        await send_chunked(message, f"ERROR: {output['error']}")


# ─── /kill — Kill a process ──────────────────────────────────────────────────

@router.message(Command("kill"))
async def cmd_kill(message: Message) -> None:
    """Kill a process. Usage: /kill [pid] [signal=TERM] [confirm=yes]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/kill").strip()
    if await _route_via_intent(message, "/kill", raw):
        return

    args = message.text.split(maxsplit=4)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 2:
        await message.answer(
            "Usage: /kill [pid] [signal=TERM] [confirm=yes]\n"
            "signals: TERM, KILL, HUP, INT, QUIT\n"
            "DANGER: confirm=yes required to actually send signal."
        )
        return

    pid = int(args[1])
    signal = args[2].upper() if len(args) > 2 else "TERM"
    confirm_raw = args[3].lower() if len(args) > 3 else "no"
    confirm = confirm_raw == "yes"

    if not confirm:
        await message.answer(
            f"PREVIEW — no signal sent yet:\n"
            f"Would send {signal} to PID {pid}.\n"
            f"Add 'confirm=yes' to execute."
        )
        return

    status_msg: types.Message | None = None
    output: dict[str, object] = {"success": False, "data": None, "error": None}
    try:
        status_msg = await message.answer(f"🔨 Sending {signal} to PID {pid}...")
        result = await system_monitor.kill_process(pid, signal=signal, confirm=True)
        output = {"success": True, "data": result, "error": None}
    except ValueError as exc:
        output = {"success": False, "data": None, "error": f"PID must be an integer: {exc}"}
    except Exception as exc:
        output = {"success": False, "data": None, "error": str(exc)}

    if status_msg:
        with contextlib.suppress(Exception):
            await status_msg.delete()

    if output["success"]:
        await send_chunked(message, output["data"])  # type: ignore[reportArgumentType]
    else:
        await send_chunked(message, f"ERROR: {output['error']}")


# ─── /sys — System stats ─────────────────────────────────────────────────────

@router.message(Command("sys"))
async def cmd_sys(message: Message) -> None:
    """System stats. Usage: /sys [stats|cpu|mem|disk|services|network]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/sys").strip()
    if await _route_via_intent(message, "/sys", raw):
        return

    args = message.text.split(maxsplit=1)  # type: ignore[reportOptionalMemberAccess]
    subcmd = args[1].lower() if len(args) > 1 else "stats"

    status_msg: types.Message | None = None
    output: dict[str, object] = {"success": False, "data": None, "error": None}
    try:
        status_msg = await message.answer(f"📡 Fetching system {subcmd}...")
        if subcmd == "stats":
            result = await system_monitor.system_stats()
        elif subcmd == "cpu":
            result = await system_monitor.cpu_usage_per_core()
        elif subcmd == "mem":
            result = await system_monitor.memory_usage()
        elif subcmd == "disk":
            result = await system_monitor.disk_io()
        elif subcmd == "services":
            result = await system_monitor.running_services()
        elif subcmd == "failed":
            result = await system_monitor.failed_services()
        elif subcmd == "network":
            result = await system_monitor.network_stats()
        elif subcmd == "connections":
            result = await system_monitor.network_connections()
        elif subcmd == "ports":
            result = await system_monitor.listening_ports()
        elif subcmd == "who":
            result = await system_monitor.who_is_logged_in()
        else:
            result = (
                "Usage: /sys [stats|cpu|mem|disk|services|failed|network|connections|ports|who]\n"
                "Default: stats"
            )
            output = {"success": False, "data": None, "error": result}
            raise ValueError("invalid subcmd")

        output = {"success": True, "data": result, "error": None}
    except ValueError as exc:
        # Only catch ValueError from invalid subcmd; re-raise if from kill_process
        if "invalid subcmd" not in str(exc):
            raise
        # Fall through to final output block
    except Exception as exc:
        output = {"success": False, "data": None, "error": str(exc)}

    if status_msg:
        with contextlib.suppress(Exception):
            await status_msg.delete()

    if output["success"]:
        await send_chunked(message, output["data"])  # type: ignore[reportArgumentType]
    else:
        await send_chunked(message, f"ERROR: {output['error']}")


# ─── /ls — Directory listing ─────────────────────────────────────────────────

@router.message(Command("ls"))
async def cmd_ls(message: Message) -> None:
    """List directory contents. Usage: /ls [path=.] [depth=1]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/ls").strip()
    if await _route_via_intent(message, "/ls", raw):
        return

    args = message.text.split(maxsplit=2)  # type: ignore[reportOptionalMemberAccess]
    path = args[1] if len(args) > 1 else "."
    depth = int(args[2]) if len(args) > 2 else 1

    status_msg: types.Message | None = None
    try:
        status_msg = await message.answer(f"📂 Listing {path} (depth={depth})...")
        result = await fs_control.list_dir(path=path, depth=depth)
        output = {"success": True, "data": result, "error": None}
    except Exception as exc:
        output = {"success": False, "data": None, "error": str(exc)}

    if status_msg:
        with contextlib.suppress(Exception):
            await status_msg.delete()

    if output["success"]:
        await send_chunked(message, output["data"])
    else:
        await send_chunked(message, f"ERROR: {output['error']}")


# ─── /find — File search ─────────────────────────────────────────────────────

@router.message(Command("find"))
async def cmd_find(message: Message) -> None:
    """Search files. Usage: /find [pattern] [path=.] [type=f]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/find").strip()
    if await _route_via_intent(message, "/find", raw):
        return

    args = message.text.split(maxsplit=3)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 2:
        await message.answer(
            "Usage: /find [pattern] [path=.] [type=f|d]\n"
            "type: f=files, d=directories"
        )
        return

    pattern = args[1]
    path = args[2] if len(args) > 2 else "."
    filetype = args[3] if len(args) > 3 else "f"

    status_msg: types.Message | None = None
    try:
        status_msg = await message.answer(f"🔎 Searching for '{pattern}' in {path}...")
        result = await fs_control.search_files(pattern=pattern, path=path, filetype=filetype)
        output = {"success": True, "data": result, "error": None}
    except Exception as exc:
        output = {"success": False, "data": None, "error": str(exc)}

    if status_msg:
        with contextlib.suppress(Exception):
            await status_msg.delete()

    if output["success"]:
        await send_chunked(message, output["data"])
    else:
        await send_chunked(message, f"ERROR: {output['error']}")


# ─── /grep — Grep in files ───────────────────────────────────────────────────

@router.message(Command("grep"))
async def cmd_grep(message: Message) -> None:
    """Grep pattern in files. Usage: /grep [pattern] [path=.] [context=2]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/grep").strip()
    if await _route_via_intent(message, "/grep", raw):
        return

    args = message.text.split(maxsplit=3)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 2:
        await message.answer("Usage: /grep [pattern] [path=.] [context=2]")
        return

    pattern = args[1]
    path = args[2] if len(args) > 2 else "."
    context = int(args[3]) if len(args) > 3 else 2

    status_msg: types.Message | None = None
    try:
        status_msg = await message.answer(f"🔍 Grepping '{pattern}' in {path}...")
        result = await fs_control.grep_files(pattern=pattern, path=path, context=context)
        output = {"success": True, "data": result, "error": None}
    except Exception as exc:
        output = {"success": False, "data": None, "error": str(exc)}

    if status_msg:
        with contextlib.suppress(Exception):
            await status_msg.delete()

    if output["success"]:
        await send_chunked(message, output["data"])
    else:
        await send_chunked(message, f"ERROR: {output['error']}")


# ─── /read — Read file contents ───────────────────────────────────────────────

@router.message(Command("read"))
async def cmd_read(message: Message) -> None:
    """Read file. Usage: /read [path] [offset=0] [limit=500]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/read").strip()
    if await _route_via_intent(message, "/read", raw):
        return

    args = message.text.split(maxsplit=3)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 2:
        await message.answer("Usage: /read [path] [offset=0] [limit=500]")
        return

    path = args[1]
    offset = int(args[2]) if len(args) > 2 else 0
    limit = int(args[3]) if len(args) > 3 else 500

    status_msg: types.Message | None = None
    try:
        status_msg = await message.answer(f"📖 Reading {path}...")
        result = await fs_control.read_file(path=path, offset=offset, limit=limit)
        output = {"success": True, "data": result, "error": None}
    except Exception as exc:
        output = {"success": False, "data": None, "error": str(exc)}

    if status_msg:
        with contextlib.suppress(Exception):
            await status_msg.delete()

    if output["success"]:
        await send_chunked(message, output["data"])
    else:
        await send_chunked(message, f"ERROR: {output['error']}")


# ─── /write — Write file (preview by default) ────────────────────────────────

@router.message(Command("write"))
async def cmd_write(message: Message) -> None:
    """Write file. Usage: /write [path] [content] [confirm=yes]\nDESTRUCTIVE: requires confirm=yes."""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/write").strip()
    if await _route_via_intent(message, "/write", raw):
        return

    args = message.text.split(maxsplit=3)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 3:
        await message.answer(
            "Usage: /write [path] [content] [confirm=yes]\n"
            "WARNING: confirm=yes is required to actually write.\n"
            "Without confirm, shows preview only."
        )
        return

    path = args[1]
    content = args[2]
    confirm_raw = args[3].lower() if len(args) > 3 else "no"
    confirm = confirm_raw == "yes"

    if not confirm:
        preview = content[:500] + ("..." if len(content) > 500 else "")
        await message.answer(
            f"PREVIEW — no write occurred for:\n<code>{html.escape(path)}</code>\n"
            f"--- first 500 chars ---\n{html.escape(preview)}\n\n"
            f"Add 'confirm=yes' to write.",
            parse_mode="HTML",
        )
        return

    try:
        result = await fs_control.write_file(path=path, content=content, confirm=True)
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /disk — Disk usage ───────────────────────────────────────────────────────

@router.message(Command("disk"))
async def cmd_disk(message: Message) -> None:
    """Disk usage. Usage: /disk [path=/]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/disk").strip()
    if await _route_via_intent(message, "/disk", raw):
        return

    args = message.text.split(maxsplit=1)  # type: ignore[reportOptionalMemberAccess]
    path = args[1] if len(args) > 1 else "/"

    try:
        result = await fs_control.disk_usage(path=path)
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /window — Window management ─────────────────────────────────────────────

@router.message(Command("window"))
async def cmd_window(message: Message) -> None:
    """Window management. Usage: /window [list|active|switch|id|info|close|min] [id]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/window").strip()
    if await _route_via_intent(message, "/window", raw):
        return

    args = message.text.split(maxsplit=2)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 2:
        await message.answer(
            "Usage:\n"
            "/window list              — list all windows\n"
            "/window active            — current window info\n"
            "/window switch [id]       — switch to window\n"
            "/window close [id]        — close window\n"
            "/window min [id]          — minimize window\n"
            "/window desktop           — desktop info\n"
            "/window resolution        — screen resolution"
        )
        return

    subcmd = args[1].lower()
    wid = args[2] if len(args) > 2 else None

    try:
        if subcmd == "list":
            result = await desktop_control.list_windows()

        elif subcmd == "active":
            result = await desktop_control.get_active_window()

        elif subcmd == "switch":
            if not wid:
                result = "ERROR: /window switch [id] — id required"
            else:
                result = await desktop_control.switch_window(wid)

        elif subcmd == "close":
            if not wid:
                result = "ERROR: /window close [id] — id required"
            else:
                result = await desktop_control.close_window(wid)

        elif subcmd == "min":
            if not wid:
                result = "ERROR: /window min [id] — id required"
            else:
                result = await desktop_control.minimize_window(wid)

        elif subcmd == "info":
            result = await desktop_control.get_window_info()

        elif subcmd == "desktop":
            result = await desktop_control.get_desktop_info()

        elif subcmd == "resolution":
            result = await desktop_control.get_screen_resolution()

        else:
            result = f"ERROR: unknown subcmd '{subcmd}'"

    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /clipboard — Clipboard operations ──────────────────────────────────────

@router.message(Command("clipboard"))
async def cmd_clipboard(message: Message) -> None:
    """Get/set clipboard. Usage: /clipboard [get|set text]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/clipboard").strip()
    if await _route_via_intent(message, "/clipboard", raw):
        return

    args = message.text.split(maxsplit=2)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 2:
        await message.answer("Usage:\n/clipboard get\n/clipboard set [text]")
        return

    subcmd = args[1].lower()

    try:
        if subcmd == "get":
            result = await desktop_control.get_clipboard()
            if result.startswith("ERROR"):
                await message.answer(result)
            else:
                await message.answer(
                    f"Clipboard:\n<code>{html.escape(result[:500])}</code>",
                    parse_mode="HTML",
                )

        elif subcmd == "set":
            if len(args) < 3:
                await message.answer("Usage: /clipboard set [text]")
            else:
                text = args[2]
                result = await desktop_control.set_clipboard(text)
                await message.answer(result)

        else:
            await message.answer("Usage:\n/clipboard get\n/clipboard set [text]")

    except Exception as exc:
        await message.answer(f"ERROR: {exc}")


# ─── /service — systemd service status ─────────────────────────────────────

@router.message(Command("service"))
async def cmd_service(message: Message) -> None:
    """Service management. Usage: /service [status|failed] [name]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/service").strip()
    if await _route_via_intent(message, "/service", raw):
        return

    args = message.text.split(maxsplit=2)  # type: ignore[reportOptionalMemberAccess]
    if len(args) < 2:
        await message.answer(
            "Usage:\n"
            "/service status [name]    — service status\n"
            "/service failed            — list failed services"
        )
        return

    subcmd = args[1].lower()

    try:
        if subcmd == "status":
            if len(args) < 3:
                await message.answer("Usage: /service status [name]")
            else:
                name = args[2]
                result = await system_monitor.service_status(name)
                await send_chunked(message, result)

        elif subcmd == "failed":
            result = await system_monitor.failed_services()
            await send_chunked(message, result)

        else:
            await message.answer(
                "Usage:\n"
                "/service status [name]\n"
                "/service failed"
            )

    except Exception as exc:
        await message.answer(f"ERROR: {exc}")


# ─── /tree — Process tree ────────────────────────────────────────────────────

@router.message(Command("tree"))
async def cmd_tree(message: Message) -> None:
    """Process tree. Usage: /tree [pid=1]"""
    if not is_allowed(message):
        return

    # Auto-route through intent classifier for cognitive routing
    raw = (message.text or "").removeprefix("/tree").strip()
    if await _route_via_intent(message, "/tree", raw):
        return

    args = message.text.split(maxsplit=1)  # type: ignore[reportOptionalMemberAccess]
    pid = int(args[1]) if len(args) > 1 else 1

    try:
        result = await system_monitor.process_tree(pid=pid)
    except ValueError:
        await message.answer("ERROR: PID must be an integer")
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)  # type: ignore[reportPossiblyUnboundVariable]
