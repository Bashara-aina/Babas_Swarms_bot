"""computer_agent — Desktop control package for Legion.

Submodules:
    shell.py   — subprocess execution, app launchers, system maintenance
    display.py — display detection, screenshot, mouse/keyboard, window management
    tools.py   — LLM tool definitions and execute_tool() dispatcher

Backwards-compatible re-exports are maintained so existing callers
(`from computer_agent import take_screenshot`, etc.) continue to work.
"""

from __future__ import annotations

from computer_agent.display import (
    _detected_display,
    append_file,
    browser_navigate,
    close_browser_tab,
    detect_display,
    focus_window,
    get_active_window,
    get_clipboard,
    get_cursor_position,
    get_screen_size,
    keyboard_shortcut,
    keyboard_type,
    key_press,
    list_directory,
    list_windows,
    maximize_window,
    minimize_window,
    mouse_click,
    mouse_drag,
    mouse_move,
    new_browser_tab,
    open_folder_gui,
    read_file,
    screenshot_region,
    scroll_at,
    set_clipboard,
    take_screenshot,
    whatsapp_send_local,
    write_file,
)
from computer_agent.shell import (
    APP_MAP,
    BROWSER_APPS,
    install_packages,
    kill_process,
    list_processes,
    open_app,
    open_url,
    restart_bot,
    run_shell,
    upgrade_from_git,
)
from computer_agent.tools import (
    TOOL_DEFINITIONS,
    execute_tool,
)

__all__ = [
    "APP_MAP",
    "BROWSER_APPS",
    "_detected_display",
    "append_file",
    "browser_navigate",
    "close_browser_tab",
    "detect_display",
    "execute_tool",
    "focus_window",
    "get_active_window",
    "get_clipboard",
    "get_cursor_position",
    "get_screen_size",
    "install_packages",
    "key_press",
    "keyboard_shortcut",
    "keyboard_type",
    "kill_process",
    "list_directory",
    "list_processes",
    "list_windows",
    "maximize_window",
    "minimize_window",
    "mouse_click",
    "mouse_drag",
    "mouse_move",
    "new_browser_tab",
    "open_app",
    "open_folder_gui",
    "open_url",
    "read_file",
    "restart_bot",
    "run_shell",
    "screenshot_region",
    "scroll_at",
    "set_clipboard",
    "take_screenshot",
    "TOOL_DEFINITIONS",
    "upgrade_from_git",
    "whatsapp_send_local",
    "write_file",
]
