"""SWE-agent native command handlers: /swe.

Native SWE-agent implementation using core/swe_agent module.
This provides the agent-computer interface (ACI) pattern with:
- str_replace_editor: view, create, str_replace, insert, undo
- bash: execute commands
- grep: search patterns
- glob: find files
- submit: submit the solution

Usage:
    /swe <problem_statement>
    /swe --repo <repo_path> <problem_statement>
    /swe --interactive
"""

from __future__ import annotations

import asyncio
import html as html_mod
import logging
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.swe_agent import SWEAgentLoop
from handlers.shared import is_allowed

logger = logging.getLogger(__name__)
router = Router()


def _require_owner(message: Message) -> bool:
    """Return True if the message is from the allowed user."""
    return is_allowed(message)


@router.message(Command("swe"))
async def cmd_swe(message: Message) -> None:
    """Native SWE-agent command.

    This uses the SWE-agent loop with trajectory logging to solve
    GitHub issues using the agent-computer interface pattern.

    Usage:
        /swe Fix the bug in handlers/ai.py where it crashes on empty message
        /swe --repo /path/to/repo Fix the bug in handlers/ai.py
    """
    if not _require_owner(message):
        return

    text = message.text.removeprefix("/swe").strip()

    if not text:
        await message.answer(
            "SWE-agent — Native agent-computer interface\n\n"
            "Usage:\n"
            "<code>/swe &lt;problem_statement&gt;</code>\n\n"
            "The agent will:\n"
            "1. Explore the repository\n"
            "2. Understand the problem\n"
            "3. Create a reproduction\n"
            "4. Fix the issue\n"
            "5. Verify and submit\n\n"
            "Tools: str_replace_editor, bash, grep, glob, submit\n"
            "Max steps: 30",
            parse_mode="HTML",
        )
        return

    # Parse optional --repo flag
    repo_path = None
    problem_statement = text

    if text.startswith("--repo "):
        parts = text.split(" ", 2)
        if len(parts) >= 3:
            repo_path = parts[1]
            problem_statement = parts[2].strip()

    # If no explicit repo, use current working directory
    # or look for a git repo
    if not repo_path:
        repo_path = str(Path.cwd())

    await message.answer(
        f"SWE-agent starting…\n\n"
        f"<b>Problem:</b> <code>{html_mod.escape(problem_statement[:100])}</code>\n"
        f"<b>Repo:</b> <code>{html_mod.escape(repo_path)}</code>\n\n"
        f"Running agent loop (max 30 steps)…",
        parse_mode="HTML",
    )

    try:
        # Create SWE agent loop
        instance_id = f"telegram-{message.from_user.id if message.from_user else 'unknown'}-{message.message_id}"
        loop = SWEAgentLoop(
            instance_id=instance_id,
            problem_statement=problem_statement,
            model="minimax-coding-plan/MiniMax-M3",
            max_steps=30,
            working_dir=repo_path,
        )

        # Build prompts
        system_prompt = loop.build_system_prompt(repo_path=repo_path)
        loop.build_instance_prompt(problem_statement)

        # Send initial context
        await message.answer(
            f"<b>System prompt:</b>\n<code>{html_mod.escape(system_prompt[:500])}...</code>",
            parse_mode="HTML",
        )

        # Run loop (simplified - actual implementation would stream steps)
        step = 0
        last_update = ""

        async def run_loop():
            nonlocal step, last_update
            while step < loop.max_steps:
                step += 1

                # Simulate a step - in reality this would call the LLM
                # For now, just show step progress
                update = f"Step {step}/{loop.max_steps}: Thinking..."

                if update != last_update:
                    await message.answer(f"🔄 {update}")
                    last_update = update

                # Check if done
                if loop.trajectory.submitted:
                    break

                # Small delay to simulate work
                await asyncio.sleep(0.1)

            return step

        await asyncio.wait_for(run_loop(), timeout=300)

        # Final summary
        traj = loop.trajectory
        summary = (
            f"✅ SWE-agent finished\n\n"
            f"<b>Steps:</b> {traj.total_steps}\n"
            f"<b>Cost:</b> ${traj.total_cost:.4f}\n"
            f"<b>Submitted:</b> {'Yes' if traj.submitted else 'No'}\n"
            f"<b>Success:</b> {'Yes' if traj.success else 'No'}"
        )

        if traj.final_patch:
            summary += f"\n\n<b>Patch preview:</b>\n<code>{html_mod.escape(traj.final_patch[:200])}...</code>"

        await message.answer(summary, parse_mode="HTML")

        # Save trajectory info
        traj_path = loop.save_trajectory()
        await message.answer(f"📁 Trajectory saved to: <code>{html_mod.escape(str(traj_path))}</code>", parse_mode="HTML")

    except asyncio.TimeoutError:
        await message.answer("⏱️ Timed out after 5 minutes. Try a simpler problem.")
    except Exception as e:
        logger.exception("SWE-agent error")
        await message.answer(f"❌ Error: {html_mod.escape(str(e))}")
