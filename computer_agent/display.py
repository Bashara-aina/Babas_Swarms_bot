"""computer_agent/display.py — Display detection, screenshot, input devices, window management."""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

import logging

logger = logging.getLogger(__name__)


def _resolve_tool_bin(name: str) -> Optional[str]:
    """Resolve a desktop tool binary even when systemd PATH is minimal."""
    from computer_agent.shell import run_shell as _run_shell

    path = shutil.which(name)
    if path:
        return path
    for candidate in (f"/usr/bin/{name}", f"/bin/{name}", f"/usr/local/bin/{name}"):
        if Path(candidate).exists():
            return candidate
    return None


_detected_display: Optional[str] = None


async def detect_display() -> str:
    """Auto-detect the active X display.

    Priority:
    1. DISPLAY env var (set if bot launched from a desktop terminal)
    2. Probe :0 → :1 → :2 with xdpyinfo
    3. Parse `who` output for :N
    4. Fall back to :0
    """
    global _detected_display
    if _detected_display:
        return _detected_display

    env_display = os.environ.get("DISPLAY", "")
    if env_display:
        _detected_display = env_display
        logger.info("DISPLAY from env: %s", env_display)
        return env_display

    for d in [":0", ":1", ":2"]:
        check = subprocess.run(
            ["bash", "-c", f"DISPLAY={d} xdpyinfo 2>/dev/null | head -1"],
            capture_output=True,
            timeout=3,
        )
        if check.returncode == 0:
            _detected_display = d
            logger.info("DISPLAY probed: %s", d)
            return d

    try:
        who_out = subprocess.check_output(["who"], text=True, timeout=3)
        m = re.search(r"\(:(\d+)\)", who_out)
        if m:
            _detected_display = f":{m.group(1)}"
            logger.info("DISPLAY from who: %s", _detected_display)
            return _detected_display
    except Exception:
        pass

    logger.warning("Could not detect DISPLAY, defaulting to :0")
    _detected_display = ":0"
    return ":0"


async def _display_env() -> dict[str, str]:
    """Return env dict with DISPLAY set correctly."""
    d = await detect_display()
    env = os.environ.copy()
    env["DISPLAY"] = d
    return env


async def take_screenshot() -> Optional[str]:
    """Capture the full desktop. Returns file path on success, None on failure.

    Tries: scrot → imagemagick import → gnome-screenshot → xwd+convert
    """
    from computer_agent.shell import run_shell as _run_shell

    detected = await detect_display()
    ts = int(time.time() * 1000)

    displays: list[str] = []
    for d in [detected, ":0", ":1", ":2"]:
        if d and d not in displays:
            displays.append(d)

    xauthority = os.environ.get("XAUTHORITY", "")
    if not xauthority:
        home = os.environ.get("HOME", "")
        if home:
            candidate = Path(home) / ".Xauthority"
            if candidate.exists():
                xauthority = str(candidate)

    def _resolve_bin(name: str) -> Optional[str]:
        path = shutil.which(name)
        if path:
            return path
        for candidate in (f"/usr/bin/{name}", f"/bin/{name}", f"/usr/local/bin/{name}"):
            if Path(candidate).exists():
                return candidate
        return None

    scrot_bin = _resolve_bin("scrot")
    import_bin = _resolve_bin("import")
    gs_bin = _resolve_bin("gnome-screenshot")
    xwd_bin = _resolve_bin("xwd")
    convert_bin = _resolve_bin("convert")

    errors: list[str] = []
    for display in displays:
        path = f"/tmp/legion_{ts}_{display.replace(':', '')}.png"
        env_prefix = f"DISPLAY={display}"
        if xauthority:
            env_prefix = f"XAUTHORITY='{xauthority}' {env_prefix}"

        methods: list[str] = []
        if scrot_bin:
            methods.append(f"{env_prefix} '{scrot_bin}' -z '{path}'")
        if import_bin:
            methods.append(f"{env_prefix} '{import_bin}' -window root '{path}'")
        if gs_bin:
            methods.append(f"{env_prefix} '{gs_bin}' -f '{path}'")
        if xwd_bin and convert_bin:
            methods.append(f"{env_prefix} '{xwd_bin}' -root -silent 2>/dev/null | '{convert_bin}' xwd:- '{path}'")

        if not methods:
            logger.error("No screenshot backend binaries found in PATH or standard locations")
            return None

        for cmd in methods:
            try:
                if Path(path).exists():
                    Path(path).unlink()
            except Exception:
                pass
            result = await _run_shell(cmd, timeout=12)
            for _ in range(12):
                if Path(path).exists() and Path(path).stat().st_size > 1000:
                    logger.info("Screenshot OK via display=%s method=%s", display, cmd.split()[1])
                    return path
                await asyncio.sleep(0.1)
            errors.append(f"display={display} method={cmd.split()[1]} -> {result[:160]}")

    logger.error(
        "All screenshot methods failed (detected=%s, xauth=%s). Attempts: %s",
        detected,
        xauthority or "(none)",
        " | ".join(errors[-6:]),
    )
    return None


async def screenshot_region(x: int, y: int, w: int, h: int) -> Optional[str]:
    """Capture a region of the screen."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    ts = int(time.time())
    path = f"/tmp/legion_region_{ts}.png"
    cmd = f"DISPLAY={display} scrot -a {x},{y},{w},{h} '{path}'"
    await _run_shell(cmd, timeout=8)
    return path if Path(path).exists() else None


async def get_screen_size() -> tuple[int, int]:
    """Return (width, height) of primary monitor."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    out = await _run_shell(
        f"DISPLAY={display} xdpyinfo 2>/dev/null | grep dimensions",
        timeout=5,
    )
    m = re.search(r"(\d+)x(\d+)", out)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 1920, 1080


async def mouse_click(x: int, y: int, button: str = "left") -> str:
    """Click at (x, y). button: left | right | double | middle"""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found. Install with: sudo apt install xdotool"
    btn_map = {"left": "1", "middle": "2", "right": "3"}
    btn = btn_map.get(button, "1")
    if button == "double":
        cmd = f"DISPLAY={display} '{xdotool_bin}' mousemove --sync {x} {y} click --repeat 2 1"
    else:
        cmd = f"DISPLAY={display} '{xdotool_bin}' mousemove --sync {x} {y} click {btn}"
    result = await _run_shell(cmd, timeout=5)
    return f"clicked ({x},{y}) [{button}]: {result}"


async def mouse_move(x: int, y: int) -> str:
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found. Install with: sudo apt install xdotool"
    return await _run_shell(f"DISPLAY={display} '{xdotool_bin}' mousemove {x} {y}", timeout=3)


async def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> str:
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found. Install with: sudo apt install xdotool"
    cmd = f"DISPLAY={display} '{xdotool_bin}' mousemove {x1} {y1} mousedown 1 mousemove {x2} {y2} mouseup 1"
    return await _run_shell(cmd, timeout=5)


async def scroll_at(direction: str = "down", amount: int = 3, x: int = 0, y: int = 0) -> str:
    """Scroll at current mouse position (or given x,y)."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found. Install with: sudo apt install xdotool"
    btn = "5" if direction == "down" else "4"
    if x and y:
        cmd = f"DISPLAY={display} '{xdotool_bin}' mousemove {x} {y} click --repeat {amount} {btn}"
    else:
        cmd = f"DISPLAY={display} '{xdotool_bin}' click --repeat {amount} {btn}"
    return await _run_shell(cmd, timeout=5)


async def get_cursor_position() -> tuple[int, int]:
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return 0, 0
    out = await _run_shell(
        f"DISPLAY={display} '{xdotool_bin}' mousemove --screen 0 getmouselocation 2>/dev/null",
        timeout=3,
    )
    m = re.search(r"x:(\d+) y:(\d+)", out)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


async def keyboard_type(text: str, delay_ms: int = 30) -> str:
    """Type text using xdotool."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found. Install with: sudo apt install xdotool"
    safe = text.replace("'", "'\\''")
    delay = delay_ms * 1000
    return await _run_shell(
        f"DISPLAY={display} '{xdotool_bin}' type --delay {delay} -- '{safe}'",
        timeout=max(5, len(text) * delay_ms // 1000 + 2),
    )


async def key_press(keys: str) -> str:
    """Send a single key press or combo (e.g. 'ctrl+s', 'alt+f4')."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found"
    return await _run_shell(
        f"DISPLAY={display} '{xdotool_bin}' key {' '.join(keys.split())}",
        timeout=3,
    )


async def keyboard_shortcut(keys: str) -> str:
    """Send a keyboard shortcut (alias for key_press)."""
    return await key_press(keys)


async def list_windows() -> str:
    """List open windows via wmctrl."""
    from computer_agent.shell import run_shell as _run_shell

    wmctrl_bin = _resolve_tool_bin("wmctrl")
    if not wmctrl_bin:
        return "wmctrl not found. Install with: sudo apt install wmctrl"
    out = await _run_shell(f"'{wmctrl_bin}' -l", timeout=5)
    lines = out.split("\n")
    result = [f"  {line}" for line in lines if line]
    return "\n".join(result) if result else "no windows found"


async def focus_window(pattern: str) -> str:
    """Focus a window matching pattern (via wmctrl)."""
    from computer_agent.shell import run_shell as _run_shell

    wmctrl_bin = _resolve_tool_bin("wmctrl")
    if not wmctrl_bin:
        return "wmctrl not found"
    out = await _run_shell(
        f"'{wmctrl_bin}' -a '{pattern}' 2>/dev/null || "
        f"DISPLAY={await detect_display()} '{_resolve_tool_bin('xdotool') or 'xdotool'}' search --name '{pattern}' | head -1",
        timeout=5,
    )
    return f"focus: {pattern} — {out[:100]}"


async def get_active_window() -> str:
    """Get the title of the currently focused window."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return ""
    return await _run_shell(
        f"DISPLAY={display} '{xdotool_bin}' getactivewindow getwindowname 2>/dev/null",
        timeout=3,
    )


async def minimize_window(pattern: str = "") -> str:
    """Minimize a window by name pattern, or current window if no pattern."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    if pattern:
        await focus_window(pattern)
        await asyncio.sleep(0.2)
    return await _run_shell(
        f"DISPLAY={display} '{_resolve_tool_bin('xdotool') or 'xdotool'}' getactivewindow windowminimize",
        timeout=3,
    )


async def maximize_window() -> str:
    """Maximize the current window."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    return await _run_shell(
        f"DISPLAY={display} '{_resolve_tool_bin('xdotool') or 'xdotool'}' getactivewindow windowmaximize",
        timeout=3,
    )


async def browser_navigate(url: str) -> str:
    """Navigate to URL — focuses existing browser or opens new."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    if not re.match(r"^https?://", url):
        url = f"https://{url}"
    await _run_shell(
        f"DISPLAY={display} xdotool search --class Chrome windowfocus 2>/dev/null || "
        f"DISPLAY={display} xdg-open '{url}' &",
        timeout=5,
    )
    await asyncio.sleep(1)
    return f"opened: {url}"


async def new_browser_tab(url: str = "") -> str:
    """Open a new browser tab."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found"
    if url:
        await _run_shell(
            f"DISPLAY={display} '{xdotool_bin}' key ctrl+t && "
            f"DISPLAY={display} '{xdotool_bin}' type --delay 100 "
            f"'\\n{url}\\n'",
            timeout=5,
        )
    else:
        await _run_shell(f"DISPLAY={display} '{xdotool_bin}' key ctrl+t", timeout=3)
    return f"new tab: {url or '(blank)'}"


async def switch_browser_tab(direction: str = "next") -> str:
    """Switch browser tabs. direction: next | prev."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found"
    key = "ctrl+Page_Down" if direction == "next" else "ctrl+Page_Up"
    return await _run_shell(f"DISPLAY={display} '{xdotool_bin}' key {key}", timeout=3)


async def close_browser_tab() -> str:
    """Close current browser tab."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    xdotool_bin = _resolve_tool_bin("xdotool")
    if not xdotool_bin:
        return "xdotool not found"
    return await _run_shell(
        f"DISPLAY={display} '{xdotool_bin}' key ctrl+w",
        timeout=3,
    )


async def open_folder_gui(path: str = "~") -> str:
    """Open a folder in the file manager (Nautilus)."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    expanded = str(Path(path).expanduser())
    await _run_shell(f"DISPLAY={display} nautilus '{expanded}' &", timeout=3)
    return f"opened folder: {expanded}"


async def get_clipboard() -> str:
    """Get current clipboard content."""
    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    out = await _run_shell(
        f"DISPLAY={display} xclip -selection clipboard -o 2>/dev/null || "
        f"DISPLAY={display} xsel --clipboard --output 2>/dev/null || "
        "echo '(clipboard tools not installed: sudo apt install xclip)'",
        timeout=5,
    )
    return out


async def set_clipboard(text: str) -> str:
    """Copy text to clipboard. Uses shlex.quote for shell safety."""
    import shlex

    from computer_agent.shell import run_shell as _run_shell

    display = await detect_display()
    safe_text = shlex.quote(text)
    out = await _run_shell(
        f"echo {safe_text} | DISPLAY={display} xclip -selection clipboard 2>/dev/null || "
        "echo 'clipboard tool not installed'",
        timeout=5,
    )
    return out or "(done)"


async def whatsapp_send_local(
    contact: str,
    text: str,
    _progress: Any = None,
) -> str:
    """Open WhatsApp Web and send a message to a contact."""
    from computer_agent.shell import run_shell as _run_shell

    async def _prog(msg: str) -> None:
        if _progress:
            await _progress(msg)

    display = await detect_display()

    await _prog("🌐 opening WhatsApp Web...")
    whatsapp_url = "https://web.whatsapp.com"
    await _run_shell(
        f"DISPLAY={display} xdg-open '{whatsapp_url}' &",
        timeout=5,
    )
    await asyncio.sleep(4)

    await _prog("🔍 searching for contact...")
    search_cmd = f"DISPLAY={display} xdotool search --name WhatsApp | head -1"
    win_id = (await _run_shell(search_cmd, timeout=5)).strip()

    if win_id:
        await _run_shell(f"DISPLAY={display} xdotool windowfocus {win_id}", timeout=3)
        await asyncio.sleep(0.5)

    await _run_shell(
        f"DISPLAY={display} xdotool key ctrl+3 2>/dev/null; true",
        timeout=3,
    )
    await asyncio.sleep(2)

    await _prog("⌨️ typing contact name...")
    await _run_shell(
        f"DISPLAY={display} xdotool type --delay 100 '{contact}'",
        timeout=5,
    )
    await asyncio.sleep(1.5)

    await _run_shell(f"DISPLAY={display} xdotool key Return", timeout=3)
    await asyncio.sleep(2)

    await _prog("⌨️ typing message...")
    safe = text.replace("'", "'\\''").replace("\n", " \\n ")
    await _run_shell(
        f"DISPLAY={display} xdotool type --delay 50 '{safe}'",
        timeout=max(10, len(text) // 10 + 5),
    )
    await asyncio.sleep(0.5)

    await _run_shell(f"DISPLAY={display} xdotool key Return", timeout=3)
    await asyncio.sleep(1)

    await _prog("📸 confirming send result")
    return f"sent WhatsApp message to '{contact}' ({len(text)} chars)"


async def read_file(path: str, max_chars: int = 8000) -> str:
    """Read text file from disk."""
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return f"file not found: {path}"
        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > max_chars:
            half = max_chars // 2
            return (
                f"[File truncated — {len(content)} total chars, showing first {half} + last {half}]\n\n"
                f"{content[:half]}\n\n...[middle truncated]...\n\n{content[-half:]}"
            )
        return content
    except Exception as e:
        return f"read error: {e}"


async def write_file(path: str, content: str) -> str:
    """Write content to a file, creating directories as needed."""
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} chars → {p}"
    except Exception as e:
        return f"write error: {e}"


async def append_file(path: str, content: str) -> str:
    """Append content to a file."""
    try:
        p = Path(path).expanduser()
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
        return f"appended {len(content)} chars → {p}"
    except Exception as e:
        return f"append error: {e}"


async def list_directory(path: str = "~") -> str:
    """List directory contents."""
    from computer_agent.shell import run_shell as _run_shell

    expanded = str(Path(path).expanduser())
    return await _run_shell(f"ls -la '{expanded}' 2>&1", timeout=10)
