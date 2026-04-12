"""Screen capture and analysis skills."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def _screenshot_handler(text: str) -> str:
    """Take a desktop screenshot."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = Path("/tmp/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / f"screenshot_{timestamp}.png"

    # Try different screenshot tools
    tools_to_try = [
        ["scrot", str(screenshot_path)],
        ["gnome-screenshot", "-f", str(screenshot_path)],
        ["import", "-window", "root", str(screenshot_path)],
        ["spectacle", "-b", "-n", "-o", str(screenshot_path)],
    ]

    for tool_cmd in tools_to_try:
        try:
            tool = tool_cmd[0]
            result = subprocess.run(
                tool_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and screenshot_path.exists():
                file_size = screenshot_path.stat().st_size
                return f"📸 Screenshot saved: {screenshot_path}\nSize: {file_size // 1024}KB"
        except FileNotFoundError:
            continue
        except Exception as exc:
            logger.debug("[MediaSkill] screenshot tool %s failed: %s", tool_cmd[0], exc)
            continue

    return "❌ Screenshot failed. No screenshot tool available (tried: scrot, gnome-screenshot, ImageMagick, spectacle)"


async def _analyze_screen_handler(text: str) -> str:
    """Take screenshot and analyze its content using LLM vision."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = Path("/tmp/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / f"screen_{timestamp}.png"

    # Take screenshot
    took_screenshot = False
    tools_to_try = [
        ["scrot", str(screenshot_path)],
        ["gnome-screenshot", "-f", str(screenshot_path)],
        ["import", "-window", "root", str(screenshot_path)],
    ]

    for tool_cmd in tools_to_try:
        try:
            result = subprocess.run(
                tool_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and screenshot_path.exists():
                took_screenshot = True
                break
        except Exception:
            continue

    if not took_screenshot or not screenshot_path.exists():
        return "❌ Failed to take screenshot for analysis."

    try:
        from core.llm_client import get_vision_model

        # Get vision-capable model
        model = get_vision_model()
        if not model:
            return "⚠️ Vision model not available for screen analysis."

        import base64

        with open(screenshot_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()

        # Build prompt
        query = text
        for kw in ["analyze", "screen", "screenshot", "what's on", "what is on", "describe"]:
            query = query.replace(kw, "", case=False).strip()
        if not query or query == "screen":
            query = "Describe what's on the screen in detail."

        prompt = f"Analyze this screenshot. {query}\n\nIf this is a code editor or terminal, include any visible code or errors."

        resp = await model.ainvoke(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
        )
        analysis = resp.content if hasattr(resp, "content") else str(resp)
        return f"🖥️ Screen Analysis:\n\n{analysis}"
    except Exception as exc:
        logger.warning("[MediaSkill] analyze_screen failed: %s", exc)
        return f"❌ Screen analysis failed: {exc}"


async def _screen_text_handler(text: str) -> str:
    """Extract text from screen using OCR."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = Path("/tmp/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / f"screen_ocr_{timestamp}.png"

    # Take screenshot
    took_screenshot = False
    tools_to_try = [
        ["scrot", str(screenshot_path)],
        ["gnome-screenshot", "-f", str(screenshot_path)],
        ["import", "-window", "root", str(screenshot_path)],
    ]

    for tool_cmd in tools_to_try:
        try:
            result = subprocess.run(
                tool_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and screenshot_path.exists():
                took_screenshot = True
                break
        except Exception:
            continue

    if not took_screenshot or not screenshot_path.exists():
        return "❌ Failed to take screenshot for OCR."

    # Try OCR with tesseract
    try:
        result = subprocess.run(
            ["tesseract", str(screenshot_path), "stdout", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            ocr_text = result.stdout.strip()[:2000]
            return f"📝 Screen Text (OCR):\n\n{ocr_text}"
        return "⚠️ No text detected in screenshot."
    except FileNotFoundError:
        return "❌ Tesseract OCR not installed (apt install tesseract-ocr)"
    except Exception as exc:
        return f"❌ OCR failed: {exc}"


def _register_media_skills() -> None:
    SKILL_REGISTRY.register(
        Skill(
            name="screenshot",
            description="Take a desktop screenshot",
            trigger_keywords=["screenshot", "take screenshot", "capture screen", "snapshot", "gambar layar"],
            handler=_screenshot_handler,
            required_env_keys=[],
            category="media",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="analyze_screen",
            description="Take screenshot and analyze its content using AI vision",
            trigger_keywords=[
                "analyze screen",
                "what's on screen",
                "screen analysis",
                "analyze this",
                "what do you see",
            ],
            handler=_analyze_screen_handler,
            required_env_keys=[],
            category="media",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="screen_text",
            description="Extract text from screen using OCR",
            trigger_keywords=["screen text", "ocr", "read screen", "extract text", "text from screen"],
            handler=_screen_text_handler,
            required_env_keys=["tesseract-ocr"],
            category="media",
        )
    )


_register_media_skills()
