"""handlers/skills.py — /skill and /skills commands.

/skills         — list all available skills
/skill <name>   — show content of a specific skill
/skill_reload   — hot-reload the skill cache (owner only)
"""
from __future__ import annotations

import html as html_mod

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed, send_chunked
from tools.skill_loader import get_skill_content, invalidate_cache, list_skills

router = Router()


@router.message(Command("skills"))
async def cmd_skills_list(msg: Message) -> None:
    """List all available skills."""
    if not is_allowed(msg):
        return
    skills = list_skills()
    if not skills:
        await msg.answer(
            "No skills found. Add <code>.md</code> files to the <code>skills/</code> directory.",
            parse_mode="HTML",
        )
        return

    lines = [f"<b>\U0001f9e0 Available Skills ({len(skills)})</b>\n"]
    for s in skills:
        lines.append(f"  • <code>/skill {s}</code>")
    lines.append("\n<i>Use /skill &lt;name&gt; to view a skill's content.</i>")
    await msg.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("skill"))
async def cmd_skill_view(msg: Message) -> None:
    """Show content of a specific skill by name."""
    if not is_allowed(msg):
        return
    name = (msg.text or "").removeprefix("/skill").strip()
    if not name:
        await msg.answer(
            "Usage: <code>/skill &lt;name&gt;</code>\n"
            "List all with: <code>/skills</code>",
            parse_mode="HTML",
        )
        return

    content = get_skill_content(name)
    if not content:
        skills = list_skills()
        available = ", ".join(f"<code>{s}</code>" for s in skills[:15])
        await msg.answer(
            f"Skill <code>{html_mod.escape(name)}</code> not found.\n\n"
            f"Available: {available}",
            parse_mode="HTML",
        )
        return

    header = f"<b>\U0001f4cb Skill: {html_mod.escape(name)}</b>\n\n"
    # Convert markdown to HTML-safe plain text for Telegram
    safe_content = html_mod.escape(content)
    await send_chunked(msg, header + "<pre>" + safe_content[:3500] + "</pre>")


@router.message(Command("skill_reload"))
async def cmd_skill_reload(msg: Message) -> None:
    """Hot-reload skill cache (owner only)."""
    if not is_allowed(msg):
        return
    invalidate_cache()
    skills = list_skills()
    await msg.answer(
        f"\u2705 Skill cache cleared. {len(skills)} skills available.",
        parse_mode="HTML",
    )
