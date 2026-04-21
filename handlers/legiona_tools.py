"""
handlers/legiona_tools.py
Telegram command handlers wiring Legiona system tools to user commands.
All handlers are async, use is_allowed() auth, send_chunked() output.
SECURITY: File operations restricted to project directory. Destructive ops need confirm.
"""

from __future__ import annotations

import asyncio
import html
import re
import shlex
from typing import Optional

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed, send_chunked
from lib.legiona.tools import (
    fs_control,
    log_reader,
    system_monitor,
    desktop_control,
)


router = Router(name="legiona_tools")


# ─── Shell blocklist (from handlers/computer.py) ──────────────────────────────

SHELL_BLOCKLIST = [
    "rm -rf /", "rm -rf /*", "mkfs", "fork bomb", "dd if=/dev/zero of=/dev/",
    "chmod -R 777 /", "sudo rm -rf", "wget --no-check-certificate | bash",
    "curl -s | bash", "wget -O- | bash", "curl -O- | bash",
    ":(){:|:&};:", r"\.\/\.", r";.*;\s*rm\s",
    r"rm\s+-{1,2}[rRf]{1,2}", r"mv\s+/\s+", r"cat\s+/dev\/null.*>",
]

SHELL_BLOCKPAT = re.compile(
    "|".join(f"({p})" for p in SHELL_BLOCKLIST),
    re.IGNORECASE,
)


def _is_blocked(cmd: str) -> bool:
    return bool(SHELL_BLOCKPAT.search(cmd))


# ─── /logs — Log reading tools ───────────────────────────────────────────────

@router.message(Command("logs"))
async def cmd_logs(message: Message) -> None:
    """Tail, grep, or list system logs. Usage: /logs [tail|grep|list|errors|journal] [args]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=2)
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
    parts = args[2].split() if len(args) > 2 else []

    try:
        if subcmd == "tail":
            log_name = parts[0] if parts else "syslog"
            num = int(parts[1]) if len(parts) > 1 else 50
            result = await log_reader.tail_log(log_name, num_lines=num)

        elif subcmd == "grep":
            if len(parts) < 2:
                result = "ERROR: /logs grep [name] [pattern]"
            else:
                result = await log_reader.grep_log(parts[0], parts[1])

        elif subcmd == "list":
            result = await log_reader.list_all_logs()

        elif subcmd == "errors":
            log_name = parts[0] if parts else "syslog"
            num = int(parts[1]) if len(parts) > 1 else 30
            result = await log_reader.get_recent_errors(log_name, num_lines=num)

        elif subcmd == "journal":
            unit = parts[0] if parts else "systemd"
            num = int(parts[1]) if len(parts) > 1 else 50
            result = await log_reader.follow_journal(unit, num_lines=num)

        else:
            result = f"ERROR: unknown subcmd '{subcmd}'"

    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /ps — Process management ─────────────────────────────────────────────────

@router.message(Command("ps"))
async def cmd_ps(message: Message) -> None:
    """List top processes. Usage: /ps [cpu|mem] [top=20] [user=]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=3)
    sort_by = args[1] if len(args) > 1 else "cpu"
    top_n = int(args[2]) if len(args) > 2 else 20
    user = args[3] if len(args) > 3 else None

    if sort_by not in ("cpu", "mem", "pid", "time", "rss"):
        await message.answer("sort_by must be: cpu, mem, pid, time, or rss")
        return

    try:
        result = await system_monitor.list_processes(
            sort_by=sort_by, top_n=top_n, user=user
        )
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /kill — Kill a process ──────────────────────────────────────────────────

@router.message(Command("kill"))
async def cmd_kill(message: Message) -> None:
    """Kill a process. Usage: /kill [pid] [signal=TERM] [confirm=yes]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=4)
    if len(args) < 2:
        await message.answer(
            "Usage: /kill [pid] [signal=TERM] [confirm=yes]\n"
            "signals: TERM, KILL, HUP, INT, QUIT\n"
            "DANGER: confirm=yes required to actually send signal."
        )
        return

    try:
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

        result = await system_monitor.kill_process(pid, signal=signal, confirm=True)
    except ValueError:
        result = "ERROR: PID must be an integer"
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /sys — System stats ─────────────────────────────────────────────────────

@router.message(Command("sys"))
async def cmd_sys(message: Message) -> None:
    """System stats. Usage: /sys [stats|cpu|mem|disk|services|network]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=1)
    subcmd = args[1].lower() if len(args) > 1 else "stats"

    try:
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
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /ls — Directory listing ─────────────────────────────────────────────────

@router.message(Command("ls"))
async def cmd_ls(message: Message) -> None:
    """List directory contents. Usage: /ls [path=.] [depth=1]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=2)
    path = args[1] if len(args) > 1 else "."
    depth = int(args[2]) if len(args) > 2 else 1

    try:
        result = await fs_control.list_dir(path=path, depth=depth)
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /find — File search ─────────────────────────────────────────────────────

@router.message(Command("find"))
async def cmd_find(message: Message) -> None:
    """Search files. Usage: /find [pattern] [path=.] [type=f]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=3)
    if len(args) < 2:
        await message.answer(
            "Usage: /find [pattern] [path=.] [type=f|d]\n"
            "type: f=files, d=directories"
        )
        return

    pattern = args[1]
    path = args[2] if len(args) > 2 else "."
    filetype = args[3] if len(args) > 3 else "f"

    try:
        result = await fs_control.search_files(pattern=pattern, path=path, filetype=filetype)
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /grep — Grep in files ───────────────────────────────────────────────────

@router.message(Command("grep"))
async def cmd_grep(message: Message) -> None:
    """Grep pattern in files. Usage: /grep [pattern] [path=.] [context=2]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=3)
    if len(args) < 2:
        await message.answer("Usage: /grep [pattern] [path=.] [context=2]")
        return

    pattern = args[1]
    path = args[2] if len(args) > 2 else "."
    context = int(args[3]) if len(args) > 3 else 2

    try:
        result = await fs_control.grep_files(pattern=pattern, path=path, context=context)
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /read — Read file contents ───────────────────────────────────────────────

@router.message(Command("read"))
async def cmd_read(message: Message) -> None:
    """Read file. Usage: /read [path] [offset=0] [limit=500]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=3)
    if len(args) < 2:
        await message.answer("Usage: /read [path] [offset=0] [limit=500]")
        return

    path = args[1]
    offset = int(args[2]) if len(args) > 2 else 0
    limit = int(args[3]) if len(args) > 3 else 500

    try:
        result = await fs_control.read_file(path=path, offset=offset, limit=limit)
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)


# ─── /write — Write file (preview by default) ────────────────────────────────

@router.message(Command("write"))
async def cmd_write(message: Message) -> None:
    """Write file. Usage: /write [path] [content] [confirm=yes]\nDESTRUCTIVE: requires confirm=yes."""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=3)
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

    args = message.text.split(maxsplit=1)
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

    args = message.text.split(maxsplit=2)
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


# ─── /screen — Screenshot ────────────────────────────────────────────────────

@router.message(Command("screen"))
async def cmd_screen(message: Message) -> None:
    """Take a screenshot. Usage: /screen [base64=yes|no]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=1)
    base64_mode = args[1].lower() == "base64" if len(args) > 1 else False

    try:
        if base64_mode:
            b64 = await desktop_control.take_screenshot_base64()
            if b64.startswith("ERROR"):
                await message.answer(b64)
            else:
                await message.answer(
                    f"<code>{b64[:200]}</code>\n... (base64 PNG, {len(b64)} chars)",
                    parse_mode="HTML",
                )
        else:
            path = await desktop_control.take_screenshot()
            if path.startswith("ERROR"):
                await message.answer(path)
            else:
                await message.answer(
                    f"Screenshot saved:\n<code>{html.escape(path)}</code>",
                    parse_mode="HTML",
                )
    except Exception as exc:
        await message.answer(f"ERROR: {exc}")


# ─── /clipboard — Clipboard operations ──────────────────────────────────────

@router.message(Command("clipboard"))
async def cmd_clipboard(message: Message) -> None:
    """Get/set clipboard. Usage: /clipboard [get|set text]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=2)
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


# ─── /type — Type text (desktop) ───────────────────────────────────────────

@router.message(Command("type"))
async def cmd_type(message: Message) -> None:
    """Type text using xdotool. Usage: /type [text]\nWARNING: text visible in process args."""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /type [text]")
        return

    text = args[1]
    # Warning about sensitive text
    if any(k in text.lower() for k in ["password", "secret", "token", "key", "api"]):
        await message.answer(
            "⚠️ Warning: text appears to contain sensitive data.\n"
            "xdotool args are visible in process list.\n"
            "Still executing as requested..."
        )

    try:
        result = await desktop_control.type_text(text)
        if result.startswith("ERROR"):
            await message.answer(result)
        else:
            await message.answer(f"Typed: {html.escape(text[:100])}", parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"ERROR: {exc}")


# ─── /key — Press key combination ───────────────────────────────────────────

@router.message(Command("key"))
async def cmd_key(message: Message) -> None:
    """Press a key combo. Usage: /key [combo]\nExample: /key Alt+Tab, Ctrl+c, Super+d"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /key [combo]\nExample: Alt+Tab, Ctrl+c, Super+d")
        return

    combo = args[1]
    try:
        result = await desktop_control.key_press(combo)
        if result.startswith("ERROR"):
            await message.answer(result)
        else:
            await message.answer(f"Pressed: {html.escape(combo)}", parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"ERROR: {exc}")


# ─── /service — systemd service status ─────────────────────────────────────

@router.message(Command("service"))
async def cmd_service(message: Message) -> None:
    """Service management. Usage: /service [status|failed] [name]"""
    if not is_allowed(message):
        return

    args = message.text.split(maxsplit=2)
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

    args = message.text.split(maxsplit=1)
    pid = int(args[1]) if len(args) > 1 else 1

    try:
        result = await system_monitor.process_tree(pid=pid)
    except ValueError:
        await message.answer("ERROR: PID must be an integer")
    except Exception as exc:
        result = f"ERROR: {exc}"

    await send_chunked(message, result)