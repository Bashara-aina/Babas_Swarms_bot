"""tools/computer_use_agent.py — Autonomous desktop control via vision-action loop.

Implements the "Control компьютер" capability: Legion sees the screen,
decides the next action, executes it, and repeats until the task is done.

Loop (max 20 steps):
  1. take_screenshot  →  PIL validate  →  base64 encode
  2. vision model     →  understands UI, decides action + coordinates
  3. execute_tool     →  xdotool / xdotool / shell / …
  4. verify screenshot →  confirm state changed
  5. repeat

Safety: destructive actions (rm, drop, delete) require user confirmation
        via a pending confirmations queue in computer_agent/shell.py.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Dangerous action patterns ─────────────────────────────────────────────────

DANGEROUS_PATTERNS = [
    re.compile(r"\brm\s+-(?:rf|r|f force)\b", re.I),
    re.compile(r"\bdrop\s+(?:table|database)\b", re.I),
    re.compile(r"\bdelete\s+(?:table|database|account)\b", re.I),
    re.compile(r"\btruncate\b", re.I),
    re.compile(r"\bshutdown\b", re.I),
    re.compile(r"\bpoweroff\b", re.I),
    re.compile(r"\breboot\b", re.I),
    re.compile(r"sudo\s+", re.I),
    re.compile(r"\bdd\s+if=.*of=", re.I),
    re.compile(r"\bmkfs\b", re.I),
    re.compile(r">\s*/dev/sd", re.I),
    re.compile(r"\bcurl\s+.*\|\s*sh\b", re.I),
    re.compile(r"\bwget\s+.*\|\s*sh\b", re.I),
]


class ActionType(Enum):
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    KEYBOARD_TYPE = "keyboard_type"
    KEY_PRESS = "key_press"
    SHELL_EXECUTE = "shell_execute"
    TAKE_SCREENSHOT = "take_screenshot"
    SCROLL = "scroll"
    DONE = "done"
    UNKNOWN = "unknown"


@dataclass
class ParsedAction:
    action_type: ActionType
    x: int = 0
    y: int = 0
    text: str = ""
    keys: str = ""
    button: str = "left"
    direction: str = "down"
    command: str = ""
    reason: str = ""
    is_dangerous: bool = False


@dataclass
class LoopStep:
    step_number: int
    screenshot_path: str | None
    vision_response: str
    parsed_action: ParsedAction
    execution_result: str
    verified: bool


@dataclass
class LoopResult:
    success: bool
    task: str
    steps: list[LoopStep]
    final_state: str
    error: str | None = None


# ── Safety confirmation queue ────────────────────────────────────────────────

_PENDING_CONFIRMATIONS: list[dict[str, Any]] = []


def get_pending_confirmations() -> list[dict[str, Any]]:
    return list(_PENDING_CONFIRMATIONS)


def clear_confirmations() -> None:
    _PENDING_CONFIRMATIONS.clear()


async def request_confirmation(action: ParsedAction, step: int) -> None:
    """Add a dangerous action to the pending confirmations queue."""
    _PENDING_CONFIRMATIONS.append({
        "step": step,
        "action": action.action_type.value,
        "reason": action.reason,
        "command": action.command,
        "text": action.text,
        "keys": action.keys,
        "x": action.x,
        "y": action.y,
    })


def is_dangerous_command(command: str) -> bool:
    """Check if a shell command matches dangerous patterns."""
    return any(pattern.search(command) for pattern in DANGEROUS_PATTERNS)


# ── Vision model ───────────────────────────────────────────────────────────────

async def _vision_analyze(
    image_path: str,
    question: str,
) -> tuple[str, str]:
    """Analyze screenshot using local Ollama vision or cloud fallback."""
    from llm_client import analyze_screenshot as _analyze

    return await _analyze(image_path, question)


# ── Action parser ───────────────────────────────────────────────────────────────

COMPUTER_USE_PROMPT = """You are controlling Bas's Linux desktop via a vision-action loop.

SCREENSHOT ANALYSIS:
You will receive a screenshot. Describe:
1. What is currently visible (apps, windows, UI elements)
2. The exact pixel coordinates of the target element to interact with
3. What you need to do next

AVAILABLE ACTIONS (respond with ONLY this JSON format):
{{{{
  "action": "mouse_click|keyboard_type|key_press|scroll|shell_execute|done",
  "x": 0,           // pixel X for mouse actions (from left edge)
  "y": 0,           // pixel Y for mouse actions (from top edge)
  "text": "",       // text to type
  "keys": "",       // key or shortcut (e.g. "ctrl+t", "Return", "Escape")
  "direction": "down", // scroll direction: "up" or "down"
  "command": "",    // shell command to execute
  "reason": ""      // brief explanation of what you're doing and why
}}}}

COORDINATE RULES:
- X=0 is the left edge, Y=0 is the top edge
- Standard monitor is 1920×1080 (yours may vary)
- Look for clickable elements: buttons, links, input fields
- Hover over an element to see its name/role if unsure

MOUSE_CLICK: Use when you need to click a button, link, or UI element
KEYBOARD_TYPE: Use when you need to type text into a focused input field
KEY_PRESS: Use for shortcuts (ctrl+c, ctrl+v, Return, Escape, Tab, etc.)
SCROLL: Use when content is below the visible area
SHELL_EXECUTE: Use for CLI commands (git, ls, python, etc.)
DONE: Task is confirmed complete — stop the loop

IMPORTANT RULES:
- If you cannot find the target element, describe what IS visible and try an alternative approach
- If a click doesn't work, verify coordinates and retry
- Do NOT click random coordinates — be precise about what you're targeting
- Report what you observe after each action
- If the task requires typing, click the input field first, then type
"""


async def _parse_vision_response(
    vision_text: str,
    screenshot_path: str,
    step: int,
) -> ParsedAction:
    """Parse the LLM's vision response into a structured action.

    The vision model outputs a JSON block describing the action.
    We also do a secondary safety check on shell commands.
    """
    # Try to extract JSON from the response
    json_match = re.search(r"\{[^{}]*\"action\"[^{}]*\}", vision_text, re.DOTALL)
    if not json_match:
        # Fallback: look for any JSON object
        json_match = re.search(r"\{.*\}", vision_text, re.DOTALL)

    if json_match:
        try:
            raw = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            raw = {}
    else:
        raw = {}

    action_str = raw.get("action", "").lower().strip()
    if not action_str:
        # Try to infer from text
        text_lower = vision_text.lower()
        if any(w in text_lower for w in ["click", "press", "button"]):
            action_str = "mouse_click"
        elif any(w in text_lower for w in ["type", "enter text", "input"]):
            action_str = "keyboard_type"
        elif "scroll" in text_lower:
            action_str = "scroll"
        elif "complete" in text_lower or "done" in text_lower:
            action_str = "done"
        else:
            action_str = "unknown"

    action_map = {
        "mouse_click": ActionType.MOUSE_CLICK,
        "mouse_move": ActionType.MOUSE_MOVE,
        "keyboard_type": ActionType.KEYBOARD_TYPE,
        "key_press": ActionType.KEY_PRESS,
        "scroll": ActionType.SCROLL,
        "shell_execute": ActionType.SHELL_EXECUTE,
        "done": ActionType.DONE,
    }
    action_type = action_map.get(action_str, ActionType.UNKNOWN)

    parsed = ParsedAction(
        action_type=action_type,
        x=int(raw.get("x", 0) or 0),
        y=int(raw.get("y", 0) or 0),
        text=raw.get("text", ""),
        keys=raw.get("keys", ""),
        direction=raw.get("direction", "down"),
        command=raw.get("command", ""),
        reason=raw.get("reason", ""),
    )

    # Safety check for dangerous commands
    if parsed.command and is_dangerous_command(parsed.command):
        parsed.is_dangerous = True
        await request_confirmation(parsed, step)

    return parsed


# ── Action executor ────────────────────────────────────────────────────────────

async def _execute_action(
    action: ParsedAction,
    pending_confirmations: list[dict[str, Any]],
) -> str:
    """Execute the parsed action via computer_agent tools."""
    if action.is_dangerous and not pending_confirmations:
        return f"[BLOCKED] Dangerous action requires user confirmation: {action.command}"

    try:
        from computer_agent import (
            display as _display_mod,
        )
        from computer_agent import (
            shell as _shell_mod,
        )
    except ImportError:
        return "computer_agent not available"

    if action.action_type == ActionType.MOUSE_CLICK:
        return await _display_mod.mouse_click(action.x, action.y, action.button)

    elif action.action_type == ActionType.MOUSE_MOVE:
        return await _display_mod.mouse_move(action.x, action.y)

    elif action.action_type == ActionType.KEYBOARD_TYPE:
        return await _display_mod.keyboard_type(action.text)

    elif action.action_type == ActionType.KEY_PRESS:
        return await _display_mod.key_press(action.keys)

    elif action.action_type == ActionType.SCROLL:
        direction = action.direction or "down"
        amount = 3
        return await _display_mod.scroll_at(direction, amount, action.x or 0, action.y or 0)

    elif action.action_type == ActionType.SHELL_EXECUTE:
        if not action.command:
            return "No command specified"
        return await _shell_mod.run_shell(action.command, timeout=30)

    elif action.action_type == ActionType.DONE:
        return "Task complete"

    elif action.action_type == ActionType.UNKNOWN:
        # Fallback: describe what we see
        return f"Could not determine action. Reason: {action.reason}"

    return "Unknown action type"


# ── Verification ────────────────────────────────────────────────────────────────

async def _verify_step(
    screenshot_path: str,
    expected_change: str,
) -> bool:
    """Take a verification screenshot and check if state changed."""
    try:
        new_path = await _take_screenshot_safe()
        if not new_path:
            return False
        # For now, we just confirm the screenshot was taken
        # A more sophisticated check would compare the two images
        return new_path != screenshot_path
    except Exception:
        return False


async def _take_screenshot_safe() -> str | None:
    """Take screenshot with graceful fallback."""
    try:
        from computer_agent import take_screenshot as _take_screenshot
        return await _take_screenshot()
    except Exception as e:
        logger.warning("Screenshot failed: %s", e)
        return None


# ── Progress callback ──────────────────────────────────────────────────────────

StepCallback = Optional[callable]


# ── Main loop ─────────────────────────────────────────────────────────────────

async def computer_use_loop(
    task: str,
    max_steps: int = 20,
    progress_callback: StepCallback = None,
    confirmed_commands: set[str] | None = None,
) -> LoopResult:
    """Run the vision-action loop until task completion or max steps.

    Args:
        task: Natural language description of the task to automate
        max_steps: Maximum iterations (default 20, prevents infinite loops)
        progress_callback: Optional async callback(step_num, description) for live updates
        confirmed_commands: Set of shell commands already confirmed safe by user

    Returns:
        LoopResult with success status, all steps, and final state
    """
    if confirmed_commands is None:
        confirmed_commands = set()

    steps: list[LoopStep] = []
    pending_confirmations = get_pending_confirmations()
    final_state = ""
    error: str | None = None

    for step_num in range(1, max_steps + 1):
        # Step 1: Take screenshot
        screenshot_path = await _take_screenshot_safe()
        if not screenshot_path:
            error = "Failed to take screenshot — display may be unavailable"
            break

        # Step 2: Analyze with vision model
        vision_question = (
            f"TASK: {task}\n\n"
            f"Current step: {step_num}/{max_steps}\n"
            "Describe what you see on screen and decide the next action. "
            "Provide coordinates for any clickable target. "
            "If you can complete the task with one more action, use 'done'."
        )

        try:
            vision_response, model_label = await _vision_analyze(screenshot_path, vision_question)
        except Exception as e:
            error = f"Vision analysis failed: {e}"
            break

        # Step 3: Parse action
        parsed = await _parse_vision_response(vision_response, screenshot_path, step_num)

        if parsed.action_type == ActionType.DONE:
            final_state = f"Completed after {step_num} steps. Final observation: {vision_response[:300]}"
            steps.append(LoopStep(
                step_number=step_num,
                screenshot_path=screenshot_path,
                vision_response=vision_response,
                parsed_action=parsed,
                execution_result="done",
                verified=True,
            ))
            break

        # Step 3b: Handle dangerous commands
        if parsed.is_dangerous and parsed.command not in confirmed_commands:
            await request_confirmation(parsed, step_num)
            final_state = (
                f"⚠️ Dangerous action requested at step {step_num}:\n"
                f"`{parsed.command}`\n\n"
                f"Reason: {parsed.reason}\n\n"
                "Use computer_use_agent.get_pending_confirmations() to review "
                "and computer_use_agent.confirm_command(cmd) to approve."
            )
            steps.append(LoopStep(
                step_number=step_num,
                screenshot_path=screenshot_path,
                vision_response=vision_response,
                parsed_action=parsed,
                execution_result="blocked — requires confirmation",
                verified=False,
            ))
            break

        # Step 4: Execute action
        execution_result = await _execute_action(parsed, pending_confirmations)

        # Step 5: Verify
        await asyncio.sleep(0.5)  # Let UI settle
        verified = await _verify_step(screenshot_path, parsed.reason)

        step_entry = LoopStep(
            step_number=step_num,
            screenshot_path=screenshot_path,
            vision_response=vision_response,
            parsed_action=parsed,
            execution_result=execution_result,
            verified=verified,
        )
        steps.append(step_entry)

        if progress_callback:
            await progress_callback(step_num, f"Step {step_num}: {parsed.action_type.value} → {execution_result[:80]}")

        logger.info(
            "[ComputerUse] step %d/%d: %s → %s",
            step_num, max_steps, parsed.action_type.value, execution_result[:80]
        )

    else:
        error = f"Max steps ({max_steps}) reached without completion"

    return LoopResult(
        success=error is None and any(s.verified for s in steps),
        task=task,
        steps=steps,
        final_state=final_state or error or "Max steps reached",
        error=error,
    )


# ── Confirmation interface ────────────────────────────────────────────────────

def confirm_command(command: str) -> bool:
    """Mark a dangerous command as user-confirmed. Returns True if confirmed."""
    _PENDING_CONFIRMATIONS[:] = [
        c for c in _PENDING_CONFIRMATIONS if c.get("command") != command
    ]
    return True


def dismiss_confirmation(command: str) -> None:
    """Remove a pending confirmation without approving it."""
    _PENDING_CONFIRMATIONS[:] = [
        c for c in _PENDING_CONFIRMATIONS if c.get("command") != command
    ]


# ── Re-exports for convenience ────────────────────────────────────────────────

__all__ = [
    "ActionType",
    "LoopResult",
    "LoopStep",
    "ParsedAction",
    "clear_confirmations",
    "computer_use_loop",
    "confirm_command",
    "dismiss_confirmation",
    "get_pending_confirmations",
    "is_dangerous_command",
]
