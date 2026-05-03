"""
lib/legiona/tools/desktop_control.py
Async wrappers for xdotool/wmctrl/scrot-based desktop control.
All functions are async, return str, have try/except guards.
"""

from __future__ import annotations

import asyncio
import base64
import shlex
from pathlib import Path


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
            return f"ERROR: {stderr.decode().strip() or 'command failed'}"
        return stdout.decode().strip() or "OK"
    except TimeoutError:
        return f"ERROR: timeout after {timeout}s"
    except Exception as exc:
        return f"ERROR: {exc}"


# ─── Screenshot ────────────────────────────────────────────────────────────────

async def take_screenshot(output_path: str | None = None) -> str:
    """
    Take a screenshot using scrot.
    Returns the path to the screenshot or an error message.
    """
    if output_path is None:
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/legiona_screenshot_{ts}.png"

    result = await _run(f"scrot {shlex.quote(output_path)}", timeout=10)
    if result.startswith("ERROR"):
        return result
    return output_path


async def take_screenshot_base64() -> str:
    """
    Take a screenshot and return it as a base64-encoded PNG string.
    Useful for returning directly to LLM vision.
    """
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    result = await _run(f"scrot {shlex.quote(tmp_path)}", timeout=10)
    if result.startswith("ERROR"):
        return result

    try:
        with open(tmp_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        Path(tmp_path).unlink(missing_ok=True)
        return b64
    except Exception as exc:
        return f"ERROR: {exc}"


# ─── Window management ─────────────────────────────────────────────────────────

async def list_windows() -> str:
    """
    List all open windows using xdotool.
    Returns window IDs and names, one per line.
    """
    return await _run("xdotool search --onlyvisible --name .", timeout=10)


async def get_active_window() -> str:
    """
    Get the currently active/focused window ID and name.
    """
    wid = await _run("xdotool getactivewindow", timeout=5)
    if wid.startswith("ERROR"):
        return wid
    name = await _run("xdotool getwindowname " + wid, timeout=5)
    return f"Window ID: {wid}\nName: {name}"


async def switch_window(window_id: str) -> str:
    """
    Switch to a window by its ID (from list_windows).
    """
    return await _run(f"xdotool windowactivate {window_id}", timeout=5)


async def close_window(window_id: str) -> str:
    """
    Close a window by its ID (SIGTERM).
    """
    return await _run(f"xdotool windowkill {window_id}", timeout=5)


async def minimize_window(window_id: str) -> str:
    """
    Minimize a window by its ID.
    """
    return await _run(f"xdotool windowminimize {window_id}", timeout=5)


async def switch_tab_next() -> str:
    """
    Switch to the next tab in the current window (Alt+Tab behavior).
    """
    return await _run("xdotool key Alt+Tab", timeout=5)


async def switch_tab_prev() -> str:
    """
    Switch to the previous tab in the current window.
    """
    return await _run("xdotool key Shift+Alt+Tab", timeout=5)


async def open_app(app_name: str) -> str:
    """
    Open an application by name (e.g. 'firefox', 'code').
    Uses xdg-open for GUI apps.
    """
    return await _run(f"xdg-open {shlex.quote(app_name)} &", timeout=10)


# ─── Keyboard / Mouse ─────────────────────────────────────────────────────────

async def type_text(text: str) -> str:
    """
    Type a string using xdotool type.
    WARNING: Use only for non-sensitive text; text is visible in process args.
    """
    safe = text.replace("\\", "\\\\").replace('"', '\\"')
    return await _run(f'xdotool type --delay 0 "{safe}"', timeout=10)


async def key_press(key_combo: str) -> str:
    """
    Press a key combination (e.g. 'Ctrl+c', 'Alt+F4', 'Super+d').
    Use '+' to combine, e.g. 'Alt+Tab'.
    """
    return await _run(f"xdotool key {key_combo.replace('+', '+')}", timeout=5)


async def mouse_click(x: int, y: int, button: str = "1") -> str:
    """
    Click at screen coordinates (x, y).
    button: 1=left, 2=middle, 3=right
    """
    return await _run(f"xdotool mousemove {x} {y} click {button}", timeout=5)


# ─── Active window info ────────────────────────────────────────────────────────

async def get_window_info() -> str:
    """
    Get information about the currently active window:
    PID, geometry, name, and desktop.
    """
    wid = await _run("xdotool getactivewindow", timeout=5)
    if wid.startswith("ERROR"):
        return wid

    pid = await _run(f"xdotool getwindowpid {wid}", timeout=5)
    geo = await _run(f"xdotool getwindowgeometry {wid}", timeout=5)
    name = await _run(f"xdotool getwindowname {wid}", timeout=5)

    return f"Window ID: {wid}\nPID: {pid}\nGeometry:\n{geo}\nName: {name}"


# ─── Clipboard ────────────────────────────────────────────────────────────────

async def get_clipboard() -> str:
    """Get current clipboard text using xclip."""
    return await _run("xclip -selection clipboard -o", timeout=5)


async def set_clipboard(text: str) -> str:
    """Set clipboard text using xclip."""
    safe = text.replace("\\", "\\\\").replace("'", "'")
    return await _run(
        f"xclip -selection clipboard -i <<< {shlex.quote(safe)}",
        timeout=5,
    )


# ─── Desktop info ─────────────────────────────────────────────────────────────

async def get_desktop_info() -> str:
    """
    Get current desktop number, number of desktops, and desktop names.
    """
    cur = await _run("xdotool get_desktop", timeout=5)
    count = await _run("xdotool get_num_desktops", timeout=5)

    names = await _run(
        "xdotool set_num_desktops $(xdotool get_num_desktops) 2>/dev/null; "
        "for i in $(seq 0 $(( $(xdotool get_num_desktops) - 1 ))); do "
        "xdotool get_desktop_name $i 2>/dev/null || echo 'desktop-$i'; done",
        timeout=10,
    )
    return f"Current desktop: {cur}\nTotal desktops: {count}\nNames:\n{names}"


async def switch_desktop(desktop: str) -> str:
    """
    Switch to a desktop number (0-indexed).
    """
    return await _run(f"xdotool set_desktop {desktop}", timeout=5)


async def get_screen_resolution() -> str:
    """
    Get current screen resolution.
    """
    return await _run(
        "xdotool getdisplaygeometry 2>/dev/null || "
        "xdpyinfo 2>/dev/null | grep dimensions",
        timeout=5,
    )
