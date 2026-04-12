"""Desktop and web automation tools for SwarmBot.

Provides three tool modules for interacting with the host system and web:

- vscode_bridge   — Workspace file read/write, shell commands, git status via
                    subprocess (works in both desktop and headless environments)
- computer_control — Desktop automation: screenshots, OCR, mouse/keyboard control,
                    window management, and vision-based screen analysis via pyautogui
                    (requires X11 display; gracefully degrades in headless mode)
- playwright_agent — Headless Chromium browser automation for web scraping and
                     full-page screenshots

All blocking operations are wrapped in async wrappers so the aiogram event loop
remains unblocked. Lazy imports are used throughout to avoid X11 display
connection errors when running in headless systemd services.
"""

from __future__ import annotations
