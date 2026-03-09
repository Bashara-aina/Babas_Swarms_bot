"""computer_agent.py — Full desktop control for Legion.

Capabilities:
  - Screenshot (auto-detects X display, multiple fallbacks)
  - Mouse: click, move, drag, scroll
  - Keyboard: type text, press shortcuts
  - Window management: list, focus, resize (wmctrl + xdotool)
  - App launcher: open any app by name, browser URLs
  - File ops: read, write, list directory, open folder in GUI
  - Self-upgrade: pip install + process restart
  - Clipboard: get/set

Requirements on the host machine:
    sudo apt install xdotool wmctrl scrot xclip
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

import logging
logger = logging.getLogger(__name__)


# ── Shell execution (blocking-safe async wrapper) ────────────────────────────

async def run_shell(cmd: str, timeout: int = 30, capture_stderr: bool = True) -> str:
    """Run a shell command asynchronously. Returns stdout+stderr as string."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE if capture_stderr else asyncio.subprocess.DEVNULL,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip() if stderr else ""
        if proc.returncode == 0:
            return out or "(done, no output)"
        return f"exit {proc.returncode}\nstdout: {out}\nstderr: {err}".strip()
    except asyncio.TimeoutError:
        return f"⏱ timed out after {timeout}s"
    except Exception as e:
        return f"run_shell error: {e}"


# ── Display detection ─────────────────────────────────────────────────────────

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

    # 1. Inherit from current process (most reliable)
    env_display = os.environ.get("DISPLAY", "")
    if env_display:
        _detected_display = env_display
        logger.info("DISPLAY from env: %s", env_display)
        return env_display

    # 2. Probe known display numbers
    for d in [":0", ":1", ":2"]:
        check = subprocess.run(
            ["bash", "-c", f"DISPLAY={d} xdpyinfo 2>/dev/null | head -1"],
            capture_output=True, timeout=3
        )
        if check.returncode == 0:
            _detected_display = d
            logger.info("DISPLAY probed: %s", d)
            return d

    # 3. Parse `who`
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


# ── Screenshot ────────────────────────────────────────────────────────────────

async def take_screenshot() -> Optional[str]:
    """Capture the full desktop. Returns file path on success, None on failure.

    Tries: scrot → imagemagick import → gnome-screenshot → xwd+convert
    """
    display = await detect_display()
    ts = int(time.time())
    path = f"/tmp/legion_{ts}.png"

    methods = [
        f"DISPLAY={display} scrot -z '{path}'",
        f"DISPLAY={display} import -window root '{path}'",
        f"DISPLAY={display} gnome-screenshot -f '{path}'",
        f"DISPLAY={display} xwd -root -silent 2>/dev/null | convert xwd:- '{path}'",
    ]

    last_error = ""
    for cmd in methods:
        result = await run_shell(cmd, timeout=10)
        if Path(path).exists() and Path(path).stat().st_size > 1000:
            logger.info("Screenshot OK via: %s", cmd.split()[1])
            return path
        last_error = result

    logger.error("All screenshot methods failed. Last: %s", last_error)
    return None


async def screenshot_region(x: int, y: int, w: int, h: int) -> Optional[str]:
    """Capture a region of the screen."""
    display = await detect_display()
    ts = int(time.time())
    path = f"/tmp/legion_region_{ts}.png"
    cmd = f"DISPLAY={display} scrot -a {x},{y},{w},{h} '{path}'"
    await run_shell(cmd, timeout=8)
    return path if Path(path).exists() else None


async def get_screen_size() -> tuple[int, int]:
    """Return (width, height) of primary monitor."""
    display = await detect_display()
    out = await run_shell(
        f"DISPLAY={display} xdpyinfo 2>/dev/null | grep dimensions",
        timeout=5
    )
    m = re.search(r"(\d+)x(\d+)", out)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 1920, 1080


# ── Mouse control ─────────────────────────────────────────────────────────────

async def mouse_click(x: int, y: int, button: str = "left") -> str:
    """Click at (x, y). button: left | right | double | middle"""
    display = await detect_display()
    btn_map = {"left": "1", "middle": "2", "right": "3"}
    btn = btn_map.get(button, "1")

    if button == "double":
        cmd = f"DISPLAY={display} xdotool mousemove --sync {x} {y} click --repeat 2 1"
    else:
        cmd = f"DISPLAY={display} xdotool mousemove --sync {x} {y} click {btn}"

    result = await run_shell(cmd, timeout=5)
    return f"clicked ({x},{y}) [{button}]: {result}"


async def mouse_move(x: int, y: int) -> str:
    display = await detect_display()
    return await run_shell(f"DISPLAY={display} xdotool mousemove {x} {y}", timeout=3)


async def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> str:
    display = await detect_display()
    cmd = (
        f"DISPLAY={display} xdotool mousemove {x1} {y1} "
        f"mousedown 1 mousemove {x2} {y2} mouseup 1"
    )
    return await run_shell(cmd, timeout=5)


async def scroll_at(direction: str = "down", amount: int = 3, x: int = 0, y: int = 0) -> str:
    """Scroll at current mouse position (or given x,y)."""
    display = await detect_display()
    btn = "5" if direction == "down" else "4"
    if x and y:
        cmd = f"DISPLAY={display} xdotool mousemove {x} {y} click --repeat {amount} {btn}"
    else:
        cmd = f"DISPLAY={display} xdotool click --repeat {amount} {btn}"
    return await run_shell(cmd, timeout=5)


async def get_cursor_position() -> tuple[int, int]:
    display = await detect_display()
    out = await run_shell(
        f"DISPLAY={display} xdotool getmouselocation --shell 2>/dev/null",
        timeout=3
    )
    x = re.search(r"X=(\d+)", out)
    y = re.search(r"Y=(\d+)", out)
    return int(x.group(1)) if x else 0, int(y.group(1)) if y else 0


# ── Keyboard control ──────────────────────────────────────────────────────────

async def keyboard_type(text: str, delay_ms: int = 30) -> str:
    """Type text character by character. Handles special chars."""
    display = await detect_display()
    # xdotool type handles most unicode but chokes on some special chars
    # Use --clearmodifiers to avoid shift/ctrl interference
    # Escape single quotes for shell
    safe_text = text.replace("\\", "\\\\").replace("'", "'\\''")
    cmd = (
        f"DISPLAY={display} xdotool type --clearmodifiers "
        f"--delay {delay_ms} -- '{safe_text}'"
    )
    result = await run_shell(cmd, timeout=max(30, len(text) // 5))
    return f"typed {len(text)} chars: {result}"


async def key_press(keys: str) -> str:
    """Press key or key combo.

    Examples:
        'ctrl+t'         → new tab
        'ctrl+shift+n'   → incognito / new window
        'alt+Tab'        → switch window
        'Return'         → Enter
        'Escape'         → Escape
        'ctrl+c'         → copy
        'ctrl+v'         → paste
        'ctrl+w'         → close tab
        'ctrl+l'         → address bar
        'F5'             → refresh
        'super'          → open app launcher
    """
    display = await detect_display()
    result = await run_shell(f"DISPLAY={display} xdotool key {keys}", timeout=5)
    return f"key {keys}: {result}"


async def keyboard_shortcut(keys: str) -> str:
    """Alias for key_press, more descriptive name."""
    return await key_press(keys)


# ── Window management ─────────────────────────────────────────────────────────

async def list_windows() -> str:
    """List all open windows with IDs and titles."""
    display = await detect_display()
    out = await run_shell(
        f"DISPLAY={display} wmctrl -l 2>/dev/null",
        timeout=5
    )
    if "wmctrl" in out and "not found" in out:
        return "wmctrl not installed. Run: sudo apt install wmctrl"
    return out or "no windows found"


async def focus_window(pattern: str) -> str:
    """Bring window matching pattern to front (case-insensitive)."""
    display = await detect_display()
    # Try wmctrl (matches by title)
    out = await run_shell(
        f"DISPLAY={display} wmctrl -a '{pattern}' 2>&1",
        timeout=5
    )
    if not out or "error" not in out.lower():
        return f"focused: {pattern}"
    # Try xdotool search
    out2 = await run_shell(
        f"DISPLAY={display} xdotool search --name '{pattern}' | head -1 | "
        f"xargs -I{{}} xdotool windowactivate {{}} 2>&1",
        timeout=5
    )
    return f"focused via xdotool: {pattern} ({out2})"


async def get_active_window() -> str:
    """Get the title of the currently focused window."""
    display = await detect_display()
    return await run_shell(
        f"DISPLAY={display} xdotool getactivewindow getwindowname 2>/dev/null",
        timeout=3
    )


async def minimize_window(pattern: str = "") -> str:
    display = await detect_display()
    if pattern:
        await focus_window(pattern)
        await asyncio.sleep(0.2)
    return await run_shell(
        f"DISPLAY={display} xdotool getactivewindow windowminimize",
        timeout=3
    )


async def maximize_window() -> str:
    display = await detect_display()
    return await run_shell(
        f"DISPLAY={display} xdotool getactivewindow windowmaximize",
        timeout=3
    )


# ── App & URL launchers ───────────────────────────────────────────────────────

# Map common names to launch commands
APP_MAP: dict[str, str] = {
    "whatsapp":       "google-chrome --app=https://web.whatsapp.com --new-window",
    "whatsapp web":   "google-chrome --app=https://web.whatsapp.com --new-window",
    "telegram":       "telegram-desktop",
    "vscode":         "code",
    "vs code":        "code",
    "code":           "code",
    "terminal":       "gnome-terminal",
    "konsole":        "konsole",
    "files":          "nautilus .",
    "file manager":   "nautilus .",
    "nautilus":       "nautilus .",
    "browser":        "google-chrome",
    "chrome":         "google-chrome",
    "google chrome":  "google-chrome",
    "firefox":        "firefox",
    "email":          "google-chrome --app=https://mail.google.com --new-window",
    "gmail":          "google-chrome --app=https://mail.google.com --new-window",
    "supabase":       "google-chrome --app=https://app.supabase.com --new-window",
    "github":         "google-chrome https://github.com",
    "slack":          "slack",
    "spotify":        "spotify",
    "discord":        "discord",
    "notion":         "google-chrome --app=https://notion.so --new-window",
    "youtube":        "google-chrome https://youtube.com",
    "calculator":     "gnome-calculator",
    "settings":       "gnome-control-center",
    "system monitor": "gnome-system-monitor",
    "htop":           "gnome-terminal -- htop",
    "nvidia-smi":     "gnome-terminal -- watch -n1 nvidia-smi",
    "jupyter":        "jupyter lab",
    "pycharm":        "pycharm",
    "obsidian":       "obsidian",
}

BROWSER_APPS = {
    "whatsapp":  "https://web.whatsapp.com",
    "gmail":     "https://mail.google.com",
    "supabase":  "https://app.supabase.com",
    "notion":    "https://notion.so",
    "github":    "https://github.com",
    "youtube":   "https://youtube.com",
}


async def open_app(app_name: str) -> str:
    """Open an application by name. Checks APP_MAP first, then tries directly."""
    display = await detect_display()
    key = app_name.lower().strip()

    # Look up in map
    if key in APP_MAP:
        cmd = f"DISPLAY={display} {APP_MAP[key]} &"
    else:
        # Try xdg-open (opens default app for file/url)
        cmd = f"DISPLAY={display} xdg-open '{key}' 2>/dev/null || DISPLAY={display} {key} &"

    await run_shell(cmd, timeout=5)
    await asyncio.sleep(1.5)  # give app time to open
    return f"opening {app_name}..."


async def open_url(url: str) -> str:
    """Open a URL in the default browser."""
    display = await detect_display()
    if not re.match(r"^https?://", url):
        url = f"https://{url}"
    await run_shell(f"DISPLAY={display} xdg-open '{url}' &", timeout=5)
    await asyncio.sleep(1)
    return f"opened: {url}"


async def browser_navigate(url: str) -> str:
    """Navigate to URL — focuses existing browser or opens new."""
    display = await detect_display()
    if not re.match(r"^https?://", url):
        url = f"https://{url}"
    # Try to find Chrome/Firefox and navigate via address bar
    focused = await get_active_window()
    is_browser = any(b in focused.lower() for b in ["chrome", "firefox", "chromium"])
    if is_browser:
        await key_press("ctrl+l")
        await asyncio.sleep(0.3)
        await keyboard_type(url)
        await key_press("Return")
        return f"navigating to: {url}"
    else:
        return await open_url(url)


async def new_browser_tab(url: str = "") -> str:
    """Open a new tab in the current browser window."""
    await key_press("ctrl+t")
    await asyncio.sleep(0.5)
    if url:
        if not re.match(r"^https?://", url):
            url = f"https://{url}"
        await keyboard_type(url)
        await key_press("Return")
    return f"new tab: {url or '(blank)'}"


async def switch_browser_tab(direction: str = "next") -> str:
    """Switch browser tab. direction: next | prev"""
    key = "ctrl+Tab" if direction == "next" else "ctrl+shift+Tab"
    return await key_press(key)


async def close_browser_tab() -> str:
    return await key_press("ctrl+w")


# ── File & folder ops ─────────────────────────────────────────────────────────

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
    expanded = str(Path(path).expanduser())
    return await run_shell(f"ls -la '{expanded}' 2>&1", timeout=10)


async def open_folder_gui(path: str = "~") -> str:
    """Open a folder in the file manager (Nautilus)."""
    display = await detect_display()
    expanded = str(Path(path).expanduser())
    await run_shell(f"DISPLAY={display} nautilus '{expanded}' &", timeout=3)
    return f"opened folder: {expanded}"


# ── Clipboard ─────────────────────────────────────────────────────────────────

async def get_clipboard() -> str:
    """Get current clipboard content."""
    display = await detect_display()
    out = await run_shell(
        f"DISPLAY={display} xclip -selection clipboard -o 2>/dev/null || "
        f"DISPLAY={display} xsel --clipboard --output 2>/dev/null || "
        "echo '(clipboard tools not installed: sudo apt install xclip)'",
        timeout=5
    )
    return out


async def set_clipboard(text: str) -> str:
    """Copy text to clipboard."""
    display = await detect_display()
    safe = text.replace("'", "'\\''")
    out = await run_shell(
        f"echo '{safe}' | DISPLAY={display} xclip -selection clipboard 2>/dev/null || "
        f"echo '{safe}' | DISPLAY={display} xsel --clipboard --input 2>/dev/null",
        timeout=5
    )
    return f"clipboard set ({len(text)} chars): {out}"


# ── Process management ────────────────────────────────────────────────────────

async def list_processes(filter_str: str = "") -> str:
    """List running processes, optionally filtered."""
    if filter_str:
        return await run_shell(f"ps aux | grep '{filter_str}' | grep -v grep", timeout=5)
    return await run_shell("ps aux --sort=-%cpu | head -20", timeout=5)


async def kill_process(process_name: str) -> str:
    """Kill a process by name."""
    return await run_shell(f"pkill -f '{process_name}' 2>&1 && echo 'killed' || echo 'not found'", timeout=5)


# ── Self-upgrade ──────────────────────────────────────────────────────────────

async def install_packages(packages: list[str]) -> str:
    """Install pip packages. Returns install output."""
    pkg_str = " ".join(f"'{p}'" for p in packages)
    logger.info("Installing packages: %s", pkg_str)
    result = await run_shell(
        f"{sys.executable} -m pip install {pkg_str} 2>&1",
        timeout=180
    )
    logger.info("Install result: %s", result[-200:])
    return result


async def upgrade_from_git(repo_dir: str = "~/swarm-bot") -> str:
    """git pull latest from remote."""
    expanded = str(Path(repo_dir).expanduser())
    return await run_shell(
        f"cd '{expanded}' && git pull origin main 2>&1",
        timeout=30
    )


def restart_bot(delay_seconds: float = 1.0) -> None:
    """Restart the bot process. Call AFTER sending Telegram notification.

    Uses os.execv to replace the current process, which means:
    - Same PID group
    - Fresh Python interpreter
    - Reloads all modules (picks up new pip packages)
    - Bot reconnects to Telegram automatically
    """
    logger.info("Bot restarting via os.execv...")
    time.sleep(delay_seconds)
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ── Tool definitions for LLM function calling ─────────────────────────────────
# These follow the OpenAI function-calling spec (works with Groq + litellm)

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "shell_execute",
            "description": (
                "Execute any bash/shell command on Bas's Linux PC. "
                "Use for: checking files, running scripts, git operations, "
                "system status, process management, installing software, anything CLI. "
                "Always use this when the user says 'cek', 'check', 'lihat', 'show me' "
                "something on the computer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Full bash command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max seconds to wait (default 30)"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": (
                "Take a screenshot of the current desktop. "
                "Call this to SEE what's on screen before clicking or interacting with UI. "
                "The image will be sent to Bas in Telegram automatically."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": (
                "Click at (x, y) pixel coordinates on screen. "
                "ALWAYS take a screenshot first to determine the correct coordinates."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Horizontal pixels from left"},
                    "y": {"type": "integer", "description": "Vertical pixels from top"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "double"],
                        "description": "Click type (default: left)"
                    }
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_type",
            "description": (
                "Type text using the keyboard. Use after clicking a text input field. "
                "For passwords or sensitive data, the user should type manually."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                    "delay_ms": {
                        "type": "integer",
                        "description": "Delay between keystrokes ms (default 30)"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "key_press",
            "description": (
                "Press a keyboard key or shortcut. "
                "Examples: 'ctrl+t' (new tab), 'ctrl+c' (copy), 'ctrl+v' (paste), "
                "'alt+Tab' (switch window), 'Return' (enter), 'Escape', 'ctrl+l' (address bar), "
                "'ctrl+shift+n' (incognito), 'F5' (refresh), 'super' (launcher), "
                "'ctrl+Tab' (next tab), 'ctrl+shift+Tab' (prev tab)"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {"type": "string", "description": "Key or combo, e.g. 'ctrl+t'"}
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": (
                "Open an application. Supported names: "
                "whatsapp, telegram, vscode, terminal, files, browser, chrome, firefox, "
                "email, gmail, supabase, github, slack, spotify, discord, notion, youtube, "
                "calculator, settings, system monitor, htop, jupyter, pycharm. "
                "Or any app by its binary name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "App name or binary"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the browser. Adds https:// automatically if missing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Navigate the currently focused browser to a URL (uses Ctrl+L shortcut). Falls back to open_url if browser not focused.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "new_browser_tab",
            "description": "Open a new browser tab, optionally navigating to a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open (optional)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "focus_window",
            "description": "Bring a window to focus by searching its title. Use list_windows first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Window title substring to match"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_windows",
            "description": "List all open windows on the desktop with their IDs and titles.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll_at",
            "description": "Scroll up or down on the current page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down"]},
                    "amount": {"type": "integer", "description": "Scroll steps (default 3)"}
                },
                "required": ["direction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file from Bas's filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path (supports ~/...)"},
                    "max_chars": {"type": "integer", "description": "Max chars to return (default 8000)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file on Bas's filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: ~)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_folder_gui",
            "description": "Open a folder in the graphical file manager (Nautilus).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Get current clipboard content.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Copy text to the clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "install_packages",
            "description": "Install Python packages via pip. Returns install output. Bot can be restarted after to load new packages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "packages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of pip package names"
                    }
                },
                "required": ["packages"]
            }
        }
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

async def execute_tool(name: str, args: dict[str, Any]) -> Any:
    """Dispatch a tool call. Returns string result or screenshot path."""
    dispatch = {
        "shell_execute":    lambda a: run_shell(a.get("command", "echo ''"), a.get("timeout", 30)),
        "take_screenshot":  lambda a: take_screenshot(),
        "mouse_click":      lambda a: mouse_click(a["x"], a["y"], a.get("button", "left")),
        "keyboard_type":    lambda a: keyboard_type(a["text"], a.get("delay_ms", 30)),
        "key_press":        lambda a: key_press(a["keys"]),
        "open_app":         lambda a: open_app(a["app_name"]),
        "open_url":         lambda a: open_url(a["url"]),
        "browser_navigate": lambda a: browser_navigate(a["url"]),
        "new_browser_tab":  lambda a: new_browser_tab(a.get("url", "")),
        "focus_window":     lambda a: focus_window(a["pattern"]),
        "list_windows":     lambda a: list_windows(),
        "scroll_at":        lambda a: scroll_at(a.get("direction", "down"), a.get("amount", 3)),
        "read_file":        lambda a: read_file(a["path"], a.get("max_chars", 8000)),
        "write_file":       lambda a: write_file(a["path"], a["content"]),
        "list_directory":   lambda a: list_directory(a.get("path", "~")),
        "open_folder_gui":  lambda a: open_folder_gui(a.get("path", "~")),
        "get_clipboard":    lambda a: get_clipboard(),
        "set_clipboard":    lambda a: set_clipboard(a["text"]),
        "install_packages": lambda a: install_packages(a["packages"]),
    }

    if name not in dispatch:
        return f"unknown tool: {name}"

    try:
        result = await dispatch[name](args)
        return result
    except KeyError as e:
        return f"missing required arg: {e}"
    except Exception as e:
        return f"tool error ({name}): {e}"
