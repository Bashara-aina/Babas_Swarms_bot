# /home/newadmin/swarm-bot/computer_control.py
"""Desktop control: screenshot, OCR, visual click, screen analysis.

Designed for a headless-capable Linux desktop (DISPLAY=:0).
All blocking operations run sync; callers must use run_in_executor.

Safety rules:
- Max 1 screenshot per second (rate limited)
- Max 10 actions per command chain
- ESC failsafe: pyautogui.FAILSAFE = True (move mouse to corner to abort)
- All actions logged to swarm-bot.log
- Destructive commands (rm, sudo, etc.) require confirmation flag
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Ensure pyautogui can find the display (desktop PC, DISPLAY=:0)
os.environ.setdefault("DISPLAY", ":0")

# Safety constants
MAX_ACTIONS_PER_CHAIN = 10
SCREENSHOT_RATE_LIMIT_SEC = 1.0
_last_screenshot_time: float = 0.0

# Destructive command patterns requiring confirmation
DESTRUCTIVE_PATTERNS = [
    "rm ", "rm -", "rmdir", "sudo rm",
    "format", "mkfs", "dd if=",
    "git push --force", "git reset --hard",
    "DROP TABLE", "DROP DATABASE",
    "> /dev/", "truncate",
]


def _is_destructive(command: str) -> bool:
    """Return True if command matches any destructive pattern.

    Args:
        command: Shell command or action string to check.

    Returns:
        True if confirmation is required before execution.
    """
    cmd_lower = command.lower()
    return any(pat.lower() in cmd_lower for pat in DESTRUCTIVE_PATTERNS)


def _rate_limit_screenshot() -> None:
    """Block until screenshot rate limit has passed."""
    global _last_screenshot_time
    elapsed = time.monotonic() - _last_screenshot_time
    if elapsed < SCREENSHOT_RATE_LIMIT_SEC:
        time.sleep(SCREENSHOT_RATE_LIMIT_SEC - elapsed)
    _last_screenshot_time = time.monotonic()


class ComputerController:
    """Desktop control interface using pyautogui + pytesseract + PIL."""

    def __init__(self) -> None:
        """Initialize controller without loading GUI dependencies.

        Defers pyautogui import until first actual use to prevent X11
        connection errors when running in headless systemd service.
        """
        self._action_count: int = 0
        # Lazy-loaded dependencies (initialized on first GUI method call)
        self._pyautogui = None
        self._tesseract = None
        self._PIL_Image = None
        self._deps_loaded = False

    def _import_deps(self) -> None:
        """Lazy-import GUI dependencies only when actually needed.

        This prevents X11 DisplayConnectionError when running headless.
        Only called when a method requiring GUI access is invoked.

        The method is idempotent - safe to call multiple times.
        """
        if self._deps_loaded:
            return  # Already loaded, skip re-import

        # Attempt to import pyautogui (requires X11 display)
        try:
            import pyautogui
            pyautogui.FAILSAFE = True  # Emergency stop: move mouse to corner
            pyautogui.PAUSE = 0.3      # 300ms safety delay between actions
            self._pyautogui = pyautogui
            logger.info("✓ pyautogui loaded successfully (X11 display available)")
        except ImportError as e:
            logger.warning(f"pyautogui not installed: {e}")
            self._pyautogui = None
        except Exception as e:
            # Catch X11 DisplayConnectionError and other runtime failures
            logger.error(
                f"pyautogui import failed - likely running headless without X11: {e}"
            )
            self._pyautogui = None

        # Attempt to import OCR engine
        try:
            import pytesseract
            self._tesseract = pytesseract
            logger.debug("✓ pytesseract (OCR) loaded")
        except ImportError as e:
            logger.warning(f"pytesseract not installed: {e}")
            self._tesseract = None

        # Attempt to import image processing library
        try:
            from PIL import Image
            self._PIL_Image = Image
            logger.debug("✓ PIL (Pillow) loaded")
        except ImportError as e:
            logger.warning(f"Pillow not installed: {e}")
            self._PIL_Image = None

        self._deps_loaded = True

    def _ensure_gui_available(self) -> None:
        """Ensure GUI dependencies are loaded and available.

        Attempts to load pyautogui/pytesseract/PIL if not already loaded.
        Raises a helpful error if X11 display is unavailable (headless mode).

        This method should be called as the first line in any method that
        requires desktop automation capabilities.

        Raises:
            RuntimeError: If running in headless environment without X11 display.
        """
        # Trigger lazy import if not done yet
        if not self._deps_loaded:
            self._import_deps()

        # Check if pyautogui successfully loaded
        if self._pyautogui is None:
            raise RuntimeError(
                "❌ Desktop automation unavailable - running in headless mode.\n\n"
                "Computer control features (/desktop, /click, /screen) require "
                "a GUI environment with X11 display.\n\n"
                "💡 To use these features:\n"
                "  1. Run the bot in a desktop session (not systemd service), OR\n"
                "  2. Set up a virtual display with Xvfb\n\n"
                "✅ All other bot features work normally in headless mode."
            )

    def reset_action_count(self) -> None:
        """Reset action counter at start of each command chain."""
        self._action_count = 0

    def _check_action_limit(self) -> None:
        """Raise RuntimeError if action limit exceeded.

        Raises:
            RuntimeError: When MAX_ACTIONS_PER_CHAIN is reached.
        """
        self._action_count += 1
        if self._action_count > MAX_ACTIONS_PER_CHAIN:
            raise RuntimeError(
                f"Action limit reached ({MAX_ACTIONS_PER_CHAIN}). "
                "Start a new command to continue."
            )

    # ── Screenshots ────────────────────────────────────────────────────────

    def screenshot(self, region: Optional[tuple[int, int, int, int]] = None) -> bytes:
        """Take a screenshot of the full desktop or a region.

        Args:
            region: Optional (x, y, width, height) to capture a sub-region.

        Returns:
            PNG image bytes.

        Raises:
            RuntimeError: If pyautogui or PIL is not available.
        """
        self._ensure_gui_available()

        if self._pyautogui is None or self._PIL_Image is None:
            raise RuntimeError("pyautogui/Pillow not installed")

        _rate_limit_screenshot()
        self._check_action_limit()

        img = self._pyautogui.screenshot(region=region)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        logger.info("Screenshot taken (region=%s)", region)
        return buf.getvalue()

    def screenshot_to_file(self, path: str | Path, region: Optional[tuple] = None) -> Path:
        """Save screenshot to a file and return its path.

        Args:
            path: Destination file path.
            region: Optional (x, y, width, height).

        Returns:
            Path to the saved PNG file.
        """
        png_bytes = self.screenshot(region=region)
        out = Path(path)
        out.write_bytes(png_bytes)
        return out

    def screenshot_base64(self, region: Optional[tuple] = None) -> str:
        """Return screenshot as base64 string (for vision model input).

        Args:
            region: Optional (x, y, width, height).

        Returns:
            Base64-encoded PNG string.
        """
        return base64.b64encode(self.screenshot(region=region)).decode()

    # ── OCR ────────────────────────────────────────────────────────────────

    def read_screen_text(self, region: Optional[tuple] = None) -> str:
        """OCR text from the desktop or a region.

        Args:
            region: Optional (x, y, width, height) to read a sub-region.

        Returns:
            Extracted text string.

        Raises:
            RuntimeError: If pytesseract is not available.
        """
        self._ensure_gui_available()

        if self._tesseract is None:
            raise RuntimeError("pytesseract not installed")
        if self._PIL_Image is None:
            raise RuntimeError("Pillow not installed")

        png_bytes = self.screenshot(region=region)
        img = self._PIL_Image.open(io.BytesIO(png_bytes))
        text: str = self._tesseract.image_to_string(img)
        logger.info("OCR read %d chars from screen", len(text))
        return text.strip()

    def read_image_text(self, image_bytes: bytes) -> str:
        """OCR text from arbitrary image bytes (e.g. uploaded photo).

        Args:
            image_bytes: Raw image bytes (PNG, JPEG, etc.).

        Returns:
            Extracted text string.
        """
        if self._tesseract is None or self._PIL_Image is None:
            raise RuntimeError("pytesseract/Pillow not installed")

        img = self._PIL_Image.open(io.BytesIO(image_bytes))
        return self._tesseract.image_to_string(img).strip()

    # ── Element Finding ────────────────────────────────────────────────────

    def find_element(self, text: str) -> Optional[tuple[int, int]]:
        """Find a UI element by its visible text using OCR + bounding boxes.

        Args:
            text: Text to search for on screen.

        Returns:
            (x, y) center coordinates of the element, or None if not found.
        """
        self._ensure_gui_available()

        if self._tesseract is None or self._PIL_Image is None:
            raise RuntimeError("pytesseract/Pillow not installed")

        png_bytes = self.screenshot()
        img = self._PIL_Image.open(io.BytesIO(png_bytes))

        data = self._tesseract.image_to_data(
            img,
            output_type=self._tesseract.Output.DICT,
        )

        text_lower = text.lower()
        for i, word in enumerate(data["text"]):
            if text_lower in str(word).lower() and int(data["conf"][i]) > 30:
                x = data["left"][i] + data["width"][i] // 2
                y = data["top"][i] + data["height"][i] // 2
                logger.info("Found '%s' at (%d, %d)", text, x, y)
                return (x, y)

        logger.warning("Element not found on screen: '%s'", text)
        return None

    # ── Mouse Control ──────────────────────────────────────────────────────

    def click_element(self, text: str) -> bool:
        """Find text on screen via OCR and click its center.

        Args:
            text: Visible text of the element to click.

        Returns:
            True if element was found and clicked, False otherwise.
        """
        self._ensure_gui_available()

        if self._pyautogui is None:
            raise RuntimeError("pyautogui not installed")

        self._check_action_limit()
        coords = self.find_element(text)
        if coords is None:
            return False

        x, y = coords
        self._pyautogui.click(x, y)
        logger.info("Clicked '%s' at (%d, %d)", text, x, y)
        return True

    def click_at(self, x: int, y: int, button: str = "left") -> None:
        """Click at absolute screen coordinates.

        Args:
            x: X coordinate.
            y: Y coordinate.
            button: 'left', 'right', or 'middle'.
        """
        self._ensure_gui_available()

        if self._pyautogui is None:
            raise RuntimeError("pyautogui not installed")

        self._check_action_limit()
        self._pyautogui.click(x, y, button=button)
        logger.info("Clicked at (%d, %d) button=%s", x, y, button)

    def type_text(self, text: str, interval: float = 0.05) -> None:
        """Type text using keyboard simulation.

        Args:
            text: Text to type.
            interval: Seconds between keystrokes (default 50ms).
        """
        self._ensure_gui_available()

        if self._pyautogui is None:
            raise RuntimeError("pyautogui not installed")

        self._check_action_limit()
        self._pyautogui.typewrite(text, interval=interval)
        logger.info("Typed %d chars", len(text))

    def hotkey(self, *keys: str) -> None:
        """Press a keyboard shortcut.

        Args:
            *keys: Key names, e.g. hotkey('ctrl', 'c').
        """
        self._ensure_gui_available()

        if self._pyautogui is None:
            raise RuntimeError("pyautogui not installed")

        self._check_action_limit()
        self._pyautogui.hotkey(*keys)
        logger.info("Hotkey: %s", "+".join(keys))

    # ── Window Management ──────────────────────────────────────────────────

    def list_windows(self) -> list[str]:
        """List visible window titles using wmctrl.

        Returns:
            List of window title strings.
        """
        import subprocess
        try:
            out = subprocess.check_output(
                ["wmctrl", "-l"], text=True, env={**os.environ, "DISPLAY": ":0"}
            )
            titles = [line.split(None, 3)[-1] for line in out.strip().splitlines() if line]
            logger.info("Found %d windows", len(titles))
            return titles
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            logger.warning("wmctrl failed: %s", exc)
            return []

    def focus_window(self, name: str) -> bool:
        """Bring a window to the foreground by partial title match.

        Args:
            name: Partial window title to match.

        Returns:
            True if window was found and focused.
        """
        import subprocess
        try:
            subprocess.run(
                ["wmctrl", "-a", name],
                check=True,
                env={**os.environ, "DISPLAY": ":0"},
            )
            logger.info("Focused window: %s", name)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            logger.warning("focus_window failed for '%s': %s", name, exc)
            return False

    # ── Vision Analysis ────────────────────────────────────────────────────

    def analyze_screen_sync(
        self,
        question: str,
        region: Optional[tuple] = None,
    ) -> str:
        """Use vision agent (Ollama Gemma3) to answer a question about the screen.

        Captures a screenshot and sends it to Ollama's vision endpoint.
        Runs synchronously — call via run_in_executor from async context.

        Args:
            question: Question to ask about the screen content.
            region: Optional (x, y, width, height) to focus on a region.

        Returns:
            Vision model's answer string.
        """
        import requests

        png_bytes = self.screenshot(region=region)
        b64_img = base64.b64encode(png_bytes).decode()

        payload = {
            "model": "gemma3:12b",
            "prompt": question,
            "images": [b64_img],
            "stream": False,
        }

        try:
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            answer: str = resp.json().get("response", "No response")
            logger.info("Vision analysis complete (%d chars)", len(answer))
            return answer
        except requests.RequestException as exc:
            logger.exception("Vision analysis failed: %s", exc)
            return f"Vision analysis error: {exc}"


# ── Async wrappers ─────────────────────────────────────────────────────────────

# Lazy singleton - only instantiate when first used
# Prevents X11 connection attempt during module import in headless mode
_controller: Optional[ComputerController] = None


def _get_controller() -> ComputerController:
    """Get or create the singleton ComputerController instance.

    Uses lazy initialization to prevent X11 errors when importing this
    module in headless environments (systemd service).

    Returns:
        ComputerController: Singleton instance.
    """
    global _controller
    if _controller is None:
        _controller = ComputerController()
    return _controller


async def desktop_screenshot(region: Optional[tuple] = None) -> bytes:
    """Async wrapper: take desktop screenshot.

    Args:
        region: Optional (x, y, width, height).

    Returns:
        PNG image bytes.

    Raises:
        RuntimeError: If running headless without X11 display.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_controller().screenshot, region)


async def read_screen(region: Optional[tuple] = None) -> str:
    """Async wrapper: OCR the desktop screen.

    Args:
        region: Optional (x, y, width, height).

    Returns:
        OCR text from screen.

    Raises:
        RuntimeError: If running headless without X11 display.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_controller().read_screen_text, region)


async def analyze_screen(question: str, region: Optional[tuple] = None) -> str:
    """Async wrapper: ask vision model about the screen.

    Args:
        question: What to ask about the visible screen.
        region: Optional (x, y, width, height).

    Returns:
        Vision model answer.

    Raises:
        RuntimeError: If running headless without X11 display.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _get_controller().analyze_screen_sync, question, region
    )


async def click_on(text: str) -> bool:
    """Async wrapper: find text on screen and click it.

    Args:
        text: Visible text of the element to click.

    Returns:
        True if element was found and clicked.

    Raises:
        RuntimeError: If running headless without X11 display.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_controller().click_element, text)


def is_destructive(command: str) -> bool:
    """Public accessor for destructive command check.

    Args:
        command: Command string to evaluate.

    Returns:
        True if command requires user confirmation.
    """
    return _is_destructive(command)
