"""Computer control handlers: /do /screen /open /click /type /key /cmd /install /upgrade."""

from __future__ import annotations

import asyncio
import html as html_mod
import re
from pathlib import Path
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

import computer_agent
import llm_client
from llm_client import run_shell_command
from tools.computer_use_agent import (
    computer_use_loop,
    confirm_command,
    get_pending_confirmations,
)

from .shared import (
    _keep_typing,
    _last_screenshot,
    _run_agent_loop,
    allowed_cb,
    is_allowed,
    screenshot_keyboard,
    send_chunked,
)

router = Router()


# ── /do — Agentic computer control ───────────────────────────────────────────

# Complexity indicators for planning gate
COMPLEXITY_CONNECTORS = [" and ", " then ", " after ", " before ", " also ", " plus ", ";", ", then", ", after"]
COMPLEXITY_PATTERNS = ["open", "click", "type", "send", "search", "go to", "navigate", "check", "find", "wait", "repeat"]


def _is_complex_task(task: str) -> bool:
    """Detect if a task requires planning (multi-step or ambiguous)."""
    task_lower = task.lower()
    word_count = len(task.split())

    # Multi-step detection: contains connectors indicating multiple actions
    has_connectors = any(conn in task_lower for conn in COMPLEXITY_CONNECTORS)

    # Length-based heuristic: longer tasks are more likely complex
    long_task = word_count > 12

    # Pattern-based: if it mentions multiple distinct action types
    action_mentions = sum(1 for p in COMPLEXITY_PATTERNS if p in task_lower)
    multi_action = action_mentions >= 2

    # Ambiguous task indicators: vague words like "it", "them", "the thing"
    # (used for future complexity scoring enhancement)

    return has_connectors or (long_task and multi_action) or (has_connectors and long_task)


async def _plan_task(task: str, max_iterations: int = 3) -> dict[str, Any]:
    """Generate a plan for complex tasks using LLM-based planning.

    Returns a dict with:
      - steps: list of step descriptions
      - expected_outcomes: what success looks like at each step
      - self_check_criteria: how to verify each step succeeded
      - iterations_used: number of planning iterations
    """
    from llm_client import chat

    planning_prompt = (
        "You are a task planning system. Create a structured plan for the following task.\n\n"
        "Your plan MUST include:\n"
        "1. STEP BREAKDOWN: Numbered steps (1, 2, 3...) the agent must execute in order\n"
        "2. EXPECTED OUTCOMES: What should be true after each step completes\n"
        "3. SELF-CHECK CRITERIA: How the agent should verify each step succeeded\n"
        "4. AMBIGUITY FLAGS: Any parts of the task that need clarification during execution\n\n"
        "Respond in this exact format (no other text):\n\n"
        "STEPS:\n1. [action description]\n2. [action description]\n\n"
        "OUTCOMES:\n1. [expected result after step 1]\n2. [expected result after step 2]\n\n"
        "CHECKS:\n1. [verification criteria for step 1]\n2. [verification criteria for step 2]\n\n"
        f"TASK: {task}"
    )

    iteration = 0
    plan_text = ""

    while iteration < max_iterations:
        result, _ = await chat(planning_prompt, agent_key="architect", user_id="0")
        plan_text = result.strip()

        # Basic validation: plan should contain STEPS, OUTCOMES, CHECKS sections
        has_all_sections = all(
            section in plan_text.upper()
            for section in ["STEPS:", "OUTCOMES:", "CHECKS:"]
        )

        if has_all_sections:
            break

        iteration += 1

    # Parse the plan into structured format
    steps = []
    outcomes = []
    checks = []

    current_section = None
    for line in plan_text.split("\n"):
        line = line.strip()
        if line.startswith("STEPS:", line.upper()) or line == "STEPS":
            current_section = "steps"
            continue
        elif line.startswith("OUTCOMES:", line.upper()) or line == "OUTCOMES":
            current_section = "outcomes"
            continue
        elif line.startswith("CHECKS:", line.upper()) or line == "CHECKS":
            current_section = "checks"
            continue
        elif line.startswith("AMBIGUITY"):
            current_section = "ambiguity"
            continue

        if current_section == "steps" and line:
            # Extract step number and description
            if line[0].isdigit() and "." in line[:3]:
                steps.append(line.split(".", 1)[1].strip() if "." in line else line)
            elif line.startswith("-"):
                steps.append(line[1:].strip())
        elif current_section == "outcomes" and line:
            if line[0].isdigit() and "." in line[:3]:
                outcomes.append(line.split(".", 1)[1].strip() if "." in line else line)
            elif line.startswith("-"):
                outcomes.append(line[1:].strip())
        elif current_section == "checks" and line:
            if line[0].isdigit() and "." in line[:3]:
                checks.append(line.split(".", 1)[1].strip() if "." in line else line)
            elif line.startswith("-"):
                checks.append(line[1:].strip())

    return {
        "steps": steps,
        "expected_outcomes": outcomes,
        "self_check_criteria": checks,
        "iterations_used": iteration + 1,
        "raw_plan": plan_text,
    }


@router.message(Command("do"))
async def cmd_do(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/do").strip()
    if not task:
        await msg.answer(
            "usage: <code>/do &lt;task&gt;</code>\n\n"
            "i'll autonomously:\n"
            "\u2022 take screenshots to see what's on screen\n"
            "\u2022 click, type, open apps, run commands\n"
            "\u2022 loop until the task is done\n\n"
            "examples:\n"
            "<code>/do open whatsapp and send 'hello' to the first chat</code>\n"
            "<code>/do open vscode with swarm-bot folder</code>\n"
            "<code>/do check supabase dashboard and tell me table sizes</code>",
            parse_mode="HTML",
        )
        return

    # Intent classification — replaces brute-force keyword matching
    from core.intent_classifier import classify_intent

    intent_result = classify_intent(task)
    agent_key = intent_result.agent_key

    # Route code/coding intent to run_code_agent
    if agent_key == "coding":
        try:
            from agents.code_agent import run_code_agent

            status = await msg.answer("⚙️ Detected coding intent — routing to code_exec agent…")
            result = await run_code_agent(task)
            await status.delete()
            payload = (
                "<b>Code</b>\n<pre>" + html_mod.escape(result.code[:3500]) + "</pre>\n"
                "<b>Stdout</b>\n<pre>" + html_mod.escape(result.stdout[:2500]) + "</pre>\n"
                "<b>Stderr</b>\n<pre>" + html_mod.escape(result.stderr[:1000]) + "</pre>\n"
                f"Exit: <code>{result.exit_code}</code>"
            )
            await send_chunked(msg, payload, model_used="code_exec")
            return
        except Exception:
            pass  # Fall through to _run_agent_loop on error

    # Planning gate for complex tasks
    if _is_complex_task(task):
        planning_msg = await msg.answer("📋 Analyzing task — creating execution plan…")

        try:
            plan = await _plan_task(task, max_iterations=3)
            await planning_msg.delete()

            # Display the plan to user
            plan_display = "🗺️ <b>Execution Plan</b>\n\n"

            for i, step in enumerate(plan["steps"][:10], 1):  # Cap at 10 steps
                outcome = plan["expected_outcomes"][i-1] if i-1 < len(plan["expected_outcomes"]) else ""
                check = plan["self_check_criteria"][i-1] if i-1 < len(plan["self_check_criteria"]) else ""

                plan_display += f"<b>Step {i}:</b> {html_mod.escape(step)}\n"
                if outcome:
                    plan_display += f"  ✓ Expected: {html_mod.escape(outcome)}\n"
                if check:
                    plan_display += f"  ⚑ Check: {html_mod.escape(check)}\n"
                plan_display += "\n"

            plan_display += f"<i>Planning iterations used: {plan['iterations_used']}/3</i>"
            await msg.answer(plan_display, parse_mode="HTML")

        except Exception as e:
            await planning_msg.edit_text(
                f"⚠️ Planning failed, proceeding with direct execution:\n"
                f"<code>{html_mod.escape(str(e)[:200])}</code>",
                parse_mode="HTML",
            )
            # Fall through to direct execution on planning failure

        # Execute complex task via computer_use_loop (vision-action-verify loop)
        status_msg = await msg.answer("\U0001f916 executing plan…")
        typing_task = asyncio.create_task(_keep_typing(msg))

        async def on_progress(step_num: int, description: str) -> None:
            try:
                await status_msg.edit_text(
                    f"<code>[{step_num}]</code> {html_mod.escape(description[:100])}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        try:
            result = await computer_use_loop(
                task,
                max_steps=20,
                progress_callback=on_progress,
            )
            typing_task.cancel()

            try:
                await status_msg.delete()
            except Exception:
                pass

            if get_pending_confirmations():
                pending = get_pending_confirmations()[0]
                await msg.answer(
                    "\u26a0\ufe0f <b>Confirmation required</b>\n\n"
                    f"Step {pending['step']}: dangerous action detected:\n"
                    f"<code>{html_mod.escape(pending['command'] or pending['keys'] or '?')}</code>\n\n"
                    f"Reason: {html_mod.escape(pending.get('reason', 'n/a'))}\n\n"
                    "To confirm, reply: <code>/confirm</code>",
                    parse_mode="HTML",
                )
                return

            if not result.success and result.error:
                await msg.answer(
                    f"\u274c <b>Execution error</b>\n\n<code>{html_mod.escape(result.error)}</code>",
                    parse_mode="HTML",
                )
                return

            # Send final report
            summary = (
                f"\u2705 <b>Task complete</b>\n\n"
                f"Task: <i>{html_mod.escape(result.task[:80])}</i>\n"
                f"Steps taken: <code>{len(result.steps)}</code>\n"
                f"Final state: {html_mod.escape(result.final_state[:200])}\n"
            )
            await send_chunked(msg, summary)

        except Exception as e:
            typing_task.cancel()
            from core.error_humanizer import humanize_error_for_display
            friendly = humanize_error_for_display(e, context="/do")
            try:
                await status_msg.edit_text(
                    f"{friendly}\n\n<code>{html_mod.escape(str(e)[:200])}</code>",
                    parse_mode="HTML",
                )
            except Exception:
                await msg.answer(
                    f"{friendly}\n\n<code>{html_mod.escape(str(e)[:200])}</code>",
                    parse_mode="HTML",
                )
        return

    # Simple task: direct to existing _run_agent_loop (backward compatible)
    await _run_agent_loop(msg, task)


# ── /autopilot — Vision-action loop for desktop automation ───────────────────
@router.message(Command("autopilot"))
async def cmd_autopilot(msg: Message) -> None:
    """Run the vision-action loop to autonomously automate desktop tasks.

    This takes screenshots, analyzes them with a vision model, decides actions,
    executes them via xdotool, and repeats until the task is done.
    """
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/autopilot").strip()
    if not task:
        await msg.answer(
            "usage: <code>/autopilot &lt;task&gt;</code>\n\n"
            "Legion will:\n"
            "\u2022 take screenshots to see the screen\n"
            "\u2022 analyze with vision model\n"
            "\u2022 click/type/open/command\n"
            "\u2022 verify results\n"
            "\u2022 repeat until done\n\n"
            "examples:\n"
            "<code>/autopilot open whatsapp and send 'test' to mom</code>\n"
            "<code>/autopilot open firefox and search for 'weather Tokyo'</code>\n"
            "<code>/autopilot open vscode with ~/swarm-bot</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("\U0001f916 autopilot engaging\u2026")
    typing_task = asyncio.create_task(_keep_typing(msg))

    async def on_progress(step_num: int, description: str) -> None:
        try:
            await status_msg.edit_text(
                f"<code>[{step_num}]</code> {html_mod.escape(description[:100])}",
                parse_mode="HTML",
            )
        except Exception:
            pass

    try:
        result = await computer_use_loop(
            task,
            max_steps=20,
            progress_callback=on_progress,
        )
        typing_task.cancel()

        try:
            await status_msg.delete()
        except Exception:
            pass

        if get_pending_confirmations():
            pending = get_pending_confirmations()[0]
            await msg.answer(
                "\u26a0\ufe0f <b>Confirmation required</b>\n\n"
                f"Step {pending['step']}: dangerous action detected:\n"
                f"<code>{html_mod.escape(pending['command'] or pending['keys'] or '?')}</code>\n\n"
                f"Reason: {html_mod.escape(pending.get('reason', 'n/a'))}\n\n"
                "To confirm, reply: <code>/confirm</code>",
                parse_mode="HTML",
            )
            return

        if not result.success and result.error:
            await msg.answer(
                f"\u274c <b>Autopilot error</b>\n\n<code>{html_mod.escape(result.error)}</code>",
                parse_mode="HTML",
            )
            return

        # Send final report
        summary = (
            f"\u2705 <b>Autopilot complete</b>\n\n"
            f"Task: <i>{html_mod.escape(result.task[:80])}</i>\n"
            f"Steps taken: <code>{len(result.steps)}</code>\n"
            f"Final state: {html_mod.escape(result.final_state[:200])}\n"
        )
        await send_chunked(msg, summary)

    except Exception as e:
        typing_task.cancel()
        from core.error_humanizer import humanize_error_for_display
        friendly = humanize_error_for_display(e, context="/autopilot")
        try:
            await status_msg.edit_text(
                f"{friendly}\n\n<code>{html_mod.escape(str(e)[:200])}</code>",
                parse_mode="HTML",
            )
        except Exception:
            await msg.answer(
                f"{friendly}\n\n<code>{html_mod.escape(str(e)[:200])}</code>",
                parse_mode="HTML",
            )


@router.message(Command("confirm"))
async def cmd_confirm(msg: Message) -> None:
    """Confirm the last dangerous action and retry."""
    if not is_allowed(msg):
        return
    pending = get_pending_confirmations()
    if not pending:
        await msg.answer("no pending confirmations")
        return
    cmd_to_confirm = (msg.text or "").removeprefix("/confirm").strip()
    if cmd_to_confirm:
        confirm_command(cmd_to_confirm)
        await msg.answer(f"\u2705 confirmed: <code>{html_mod.escape(cmd_to_confirm[:80])}</code>", parse_mode="HTML")
    else:
        # Confirm the most recent one
        latest = pending[-1]
        confirm_command(latest.get("command", ""))
        await msg.answer(
            f"\u2705 confirmed last pending action (step {latest['step']})",
            parse_mode="HTML",
        )


@router.message(Command("do_local"))
async def cmd_do_local(msg: Message) -> None:
    if not is_allowed(msg):
        return

    raw = (msg.text or "").removeprefix("/do_local").strip()
    if not raw:
        await msg.answer(
            "usage:\n"
            "<code>/do_local whatsapp | contact | message</code>\n"
            "or natural:\n"
            "<code>/do_local buka whatsapp, chat ke nama 'isi pesan'</code>",
            parse_mode="HTML",
        )
        return

    contact = ""
    message_text = ""

    if "|" in raw:
        parts = [p.strip() for p in raw.split("|", 2)]
        if len(parts) == 3 and parts[0].lower() == "whatsapp":
            contact, message_text = parts[1], parts[2]
    else:
        pattern = re.search(
            r"chat\s+ke\s+(.+?)\s+[\"'‘](.+?)[\"'’]\s*$",
            raw,
            flags=re.IGNORECASE,
        )
        if pattern:
            contact = pattern.group(1).strip()
            message_text = pattern.group(2).strip()
        else:
            plain = re.search(r"chat\s+ke\s+(.+)$", raw, flags=re.IGNORECASE)
            if plain:
                tail = plain.group(1).strip()
                tokens = tail.split()
                if len(tokens) >= 3:
                    msg_starters = {
                        "aku",
                        "i",
                        "hi",
                        "hello",
                        "sayang",
                        "dear",
                        "test",
                        "tes",
                        "tolong",
                        "please",
                        "maaf",
                        "kangen",
                        "love",
                    }
                    split_idx = -1
                    for i in range(2, len(tokens)):
                        if tokens[i].lower() in msg_starters:
                            split_idx = i
                            break
                    if split_idx == -1 and len(tokens) >= 5:
                        split_idx = len(tokens) - 3
                    if split_idx > 0:
                        contact = " ".join(tokens[:split_idx]).strip()
                        message_text = " ".join(tokens[split_idx:]).strip()

    if not contact or not message_text:
        await msg.answer(
            "couldn't parse local WhatsApp task.\n"
            "Use: <code>/do_local whatsapp | pwiti little hani | aku sayang kamu</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer("🖥 running local WhatsApp automation…")

    async def _progress_local(step_text: str) -> None:
        try:
            if step_text.startswith("💭"):
                await msg.answer(f"<i>{html_mod.escape(step_text)}</i>", parse_mode="HTML")
            else:
                await status_msg.edit_text(html_mod.escape(step_text))
        except Exception:
            pass

    result = await computer_agent.whatsapp_send_local(
        contact,
        message_text,
        _progress=_progress_local,
    )
    await status_msg.edit_text(html_mod.escape(result))

    try:
        shot = await computer_agent.take_screenshot()
        if shot and msg.from_user:
            _last_screenshot[msg.from_user.id] = shot
            await msg.answer_photo(
                photo=FSInputFile(shot),
                caption="📸 after /do_local",
                reply_markup=screenshot_keyboard(),
            )
    except Exception:
        pass


# ── /screen ───────────────────────────────────────────────────────────────────
@router.message(Command("screen"))
async def cmd_screen(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\U0001f4f8 grabbing screen\u2026")
    try:
        path = await computer_agent.take_screenshot()
        if not path:
            await status_msg.edit_text(
                "screenshot failed. run this to debug:\n"
                "<code>echo $DISPLAY; echo $XAUTHORITY</code>\n"
                "Then verify capture tools: <code>command -v scrot gnome-screenshot xwd</code>\n"
                "(If service runs on :1, set DISPLAY=:1 in systemd env.)\n\n"
                "Install deps: <code>sudo apt install scrot xdotool wmctrl xclip imagemagick</code>",
                parse_mode="HTML",
            )
            return

        await status_msg.delete()
        _last_screenshot[msg.from_user.id] = path

        await msg.answer_photo(
            photo=FSInputFile(path),
            caption="\U0001f5a5 desktop \u2014 tap Analyze or give me a task to do on screen",
            reply_markup=screenshot_keyboard(),
        )
    except Exception as e:
        await status_msg.edit_text(f"screenshot error: <code>{html_mod.escape(str(e))}</code>", parse_mode="HTML")


# ── /open ─────────────────────────────────────────────────────────────────────
@router.message(Command("open"))
async def cmd_open(msg: Message) -> None:
    if not is_allowed(msg):
        return
    target = (msg.text or "").removeprefix("/open").strip()
    if not target:
        await msg.answer(
            "usage: <code>/open &lt;app or url&gt;</code>\n\n"
            "e.g. <code>/open whatsapp</code>, <code>/open https://supabase.com</code>, "
            "<code>/open vscode</code>, <code>/open ~/projects</code>",
            parse_mode="HTML",
        )
        return
    status_msg = await msg.answer(f"opening {html_mod.escape(target)}\u2026")

    # FIX #15: Prepend https:// for www. URLs — open_url() needs a full valid URL
    if target.startswith("www."):
        target = "https://" + target

    if target.startswith("http"):
        result = await computer_agent.open_url(target)
    elif target.startswith("~/") or target.startswith("/"):
        result = await computer_agent.open_folder_gui(target)
    else:
        result = await computer_agent.open_app(target)
    await status_msg.edit_text(html_mod.escape(result))


# ── /click ────────────────────────────────────────────────────────────────────
@router.message(Command("click"))
async def cmd_click(msg: Message) -> None:
    if not is_allowed(msg):
        return
    parts = (msg.text or "").split()
    if len(parts) < 3:
        await msg.answer(
            "usage: <code>/click &lt;x&gt; &lt;y&gt; [left|right|double]</code>\nuse /screen first to find coordinates",
            parse_mode="HTML",
        )
        return
    try:
        x, y = int(parts[1]), int(parts[2])
        button = parts[3] if len(parts) > 3 else "left"
        result = await computer_agent.mouse_click(x, y, button)
        await msg.answer(f"\U0001f5b1 {html_mod.escape(result)}")
    except (ValueError, IndexError):
        await msg.answer("bad coordinates \u2014 use integers: <code>/click 500 300</code>", parse_mode="HTML")


# ── /type ─────────────────────────────────────────────────────────────────────
@router.message(Command("type"))
async def cmd_type(msg: Message) -> None:
    if not is_allowed(msg):
        return
    text_to_type = (msg.text or "").removeprefix("/type").strip()
    if not text_to_type:
        await msg.answer("usage: <code>/type &lt;text to type&gt;</code>", parse_mode="HTML")
        return
    result = await computer_agent.keyboard_type(text_to_type)
    await msg.answer(f"\u2328\ufe0f {html_mod.escape(result)}")


# ── /key ──────────────────────────────────────────────────────────────────────
@router.message(Command("key"))
async def cmd_key(msg: Message) -> None:
    if not is_allowed(msg):
        return
    combo = (msg.text or "").removeprefix("/key").strip()
    if not combo:
        await msg.answer(
            "usage: <code>/key &lt;combo&gt;</code>\n\n"
            "examples: <code>ctrl+t</code>  <code>alt+Tab</code>  "
            "<code>ctrl+shift+n</code>  <code>Return</code>  <code>super</code>",
            parse_mode="HTML",
        )
        return
    result = await computer_agent.key_press(combo)
    await msg.answer(f"\u2328\ufe0f {html_mod.escape(result)}")


# ── /cmd ──────────────────────────────────────────────────────────────────────
@router.message(Command("cmd"))
async def cmd_shell(msg: Message) -> None:
    if not is_allowed(msg):
        return
    cmd = (msg.text or "").removeprefix("/cmd").strip()
    if not cmd:
        await msg.answer(
            "usage: <code>/cmd &lt;shell command&gt;</code>\ne.g. <code>/cmd nvidia-smi</code>",
            parse_mode="HTML",
        )
        return

    # FIX #16: Expanded shell blocklist — original missed rm -rf ~, sudo rm, curl|bash, wget|bash
    blocked = [
        "rm -rf /",
        "rm -rf ~",
        "rm -rf *",
        "mkfs",
        ":(){:|:&};:",
        "> /dev/sda",
        "dd if=/dev/zero",
        "dd if=/dev/urandom",
        "chmod -R 777 /",
        "chmod -R 000 /",
        "sudo rm -rf",
        "wget -o- | bash",
        "wget -o- | sh",
        "curl | bash",
        "curl | sh",
        "| bash",
        "| sh",
    ]
    cmd_lower = cmd.lower()
    for b in blocked:
        if b in cmd_lower:
            await msg.answer(
                f"blocked dangerous pattern: <code>{html_mod.escape(b)}</code>",
                parse_mode="HTML",
            )
            return

    status_msg = await msg.answer(f"<code>$ {html_mod.escape(cmd[:100])}</code>", parse_mode="HTML")
    output = await run_shell_command(cmd, timeout=60)
    await status_msg.delete()
    await msg.answer(
        f"<code>$ {html_mod.escape(cmd[:100])}</code>\n\n<pre>{html_mod.escape(output[:3800])}</pre>",
        parse_mode="HTML",
    )


# ── /install ──────────────────────────────────────────────────────────────────
@router.message(Command("install"))
async def cmd_install(msg: Message) -> None:
    if not is_allowed(msg):
        return
    packages_str = (msg.text or "").removeprefix("/install").strip()
    if not packages_str:
        await msg.answer(
            "usage: <code>/install &lt;package1&gt; &lt;package2&gt; ...</code>\n"
            "e.g. <code>/install playwright httpx rich</code>\n\n"
            "bot will install then restart automatically.",
            parse_mode="HTML",
        )
        return

    packages = packages_str.split()
    status_msg = await msg.answer(
        f"\U0001f4e6 installing: <code>{html_mod.escape(', '.join(packages))}</code>\n(this may take a moment\u2026)",
        parse_mode="HTML",
    )

    result = await computer_agent.install_packages(packages)
    result_lower = result.lower()

    # FIX #7: Only restart if pip install actually succeeded — don't restart on failure
    install_ok = (
        "successfully installed" in result_lower
        or "already satisfied" in result_lower
        or "requirement already satisfied" in result_lower
    )

    if not install_ok:
        await status_msg.edit_text(
            f"\u26a0\ufe0f Install may have failed \u2014 NOT restarting.\n"
            f"<pre>{html_mod.escape(result[:2000])}</pre>\n\n"
            "Check the output and retry manually if needed.",
            parse_mode="HTML",
        )
        return

    await status_msg.edit_text(
        f"\U0001f4e6 install output:\n<pre>{html_mod.escape(result[:2000])}</pre>\n\n\U0001f504 restarting bot\u2026",
        parse_mode="HTML",
    )
    await asyncio.sleep(2)
    await msg.answer("back in a sec \U0001f44b")
    computer_agent.restart_bot()


# ── /upgrade ──────────────────────────────────────────────────────────────────
@router.message(Command("upgrade_git"))
async def cmd_upgrade(msg: Message) -> None:
    if not is_allowed(msg):
        return
    status_msg = await msg.answer("\u2b06\ufe0f pulling latest from GitHub\u2026")

    result = await computer_agent.upgrade_from_git()
    result_lower = result.lower()

    # FIX #2: Was always restarting even on git errors — now only restart on clean pull
    if "already up to date" in result_lower:
        await status_msg.edit_text(
            f"<b>git pull</b>\n<pre>{html_mod.escape(result)}</pre>\nalready up to date, no restart needed.",
            parse_mode="HTML",
        )
        return

    if "fatal" in result_lower or "error" in result_lower or "conflict" in result_lower:
        await status_msg.edit_text(
            f"\u26a0\ufe0f <b>git pull encountered an issue \u2014 NOT restarting.</b>\n"
            f"<pre>{html_mod.escape(result[:2000])}</pre>\n\n"
            "Please resolve manually before upgrading.",
            parse_mode="HTML",
        )
        return

    # Clean pull with actual changes — safe to restart
    await status_msg.edit_text(
        f"<b>git pull</b>\n<pre>{html_mod.escape(result)}</pre>\n\n\U0001f504 restarting\u2026",
        parse_mode="HTML",
    )
    await asyncio.sleep(2)
    await msg.answer("restarting with updates \U0001f504")
    computer_agent.restart_bot()


# ── /oi — Open Interpreter direct fallback ───────────────────────────────────
@router.message(Command("oi"))
async def cmd_oi_direct(msg: Message) -> None:
    if not is_allowed(msg):
        return
    task = (msg.text or "").removeprefix("/oi").strip()
    if not task:
        await msg.answer(
            "usage: <code>/oi &lt;task&gt;</code>\nexample: <code>/oi open firefox and go to github.com</code>",
            parse_mode="HTML",
        )
        return

    status = await msg.answer("🔄 Open Interpreter running...")
    try:
        from tools.oi_bridge import oi_execute

        result = await oi_execute(task)
        await status.edit_text(html_mod.escape(result[:3500]))
        chunks = llm_client.chunk_output(result)
        if len(chunks) > 1:
            for chunk in chunks[1:]:
                await msg.answer(chunk)
    except Exception as e:
        await status.edit_text(f"❌ OI error: {html_mod.escape(str(e))}")


# ── Keyboard button shortcuts ─────────────────────────────────────────────────
@router.message(F.text == "\U0001f5a5 Do task")
async def kbd_do_hint(msg: Message) -> None:
    if is_allowed(msg):
        await msg.answer(
            "tell me what to do on the computer:\n\n"
            "just type your task naturally, or use <code>/do &lt;task&gt;</code>\n\n"
            "examples:\n"
            "\u2022 open whatsapp\n"
            "\u2022 check what's in my swarm-bot folder\n"
            "\u2022 take a screenshot and tell me what's open\n"
            "\u2022 open supabase dashboard",
            parse_mode="HTML",
        )


@router.message(F.text == "\U0001f4f8 Screenshot")
async def kbd_screenshot(msg: Message) -> None:
    if is_allowed(msg):
        await cmd_screen(msg)


@router.message(F.text == "\u26a1 Shell")
async def kbd_shell_hint(msg: Message) -> None:
    if is_allowed(msg):
        await msg.answer(
            "type: <code>/cmd &lt;command&gt;</code>\ne.g. <code>/cmd nvidia-smi</code>",
            parse_mode="HTML",
        )


# ── Callbacks ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("fb:"))
async def cb_feedback(cb: CallbackQuery) -> None:
    action = cb.data.split(":")[1]
    responses = {
        "good": "\U0001f44d nice",
        "retry": "re-send your message to retry",
        "info": "provider shown in button label",
    }
    await cb.answer(responses.get(action, "ok"))


@router.callback_query(F.data == "screen:analyze")
async def cb_analyze_screenshot(cb: CallbackQuery) -> None:
    if not allowed_cb(cb):
        await cb.answer("not authorized")
        return

    # FIX #11: Use pop() to atomically claim the screenshot path — prevents race condition
    # on double-tap where second tap would see None and incorrectly say "screenshot expired"
    path = _last_screenshot.pop(cb.from_user.id, None)
    if not path or not Path(path).exists():
        await cb.answer("screenshot expired \u2014 grab a new one with /screen")
        return

    await cb.answer("analyzing\u2026")
    status_msg = await cb.message.answer("\U0001f50d analyzing screen\u2026")
    typing_task = asyncio.create_task(_keep_typing(cb.message))

    try:
        analysis, model_used = await llm_client.analyze_screenshot(
            path,
            question=(
                "Describe everything you see on this screen in detail: "
                "which applications are open, what content is visible, "
                "any errors/warnings, what the user appears to be working on."
            ),
        )
        typing_task.cancel()
        await status_msg.delete()
        await send_chunked(cb.message, analysis, model_used=model_used)

        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass
    except Exception as e:
        typing_task.cancel()
        await status_msg.edit_text(
            f"analysis failed: <code>{html_mod.escape(str(e))}</code>",
            parse_mode="HTML",
        )


@router.callback_query(F.data == "screen:do")
async def cb_screen_do(cb: CallbackQuery) -> None:
    if not allowed_cb(cb):
        await cb.answer("not authorized")
        return
    await cb.answer()
    await cb.message.answer(
        "what do you want me to do on screen?\n\njust reply with your task, or use <code>/do &lt;task&gt;</code>",
        parse_mode="HTML",
    )
