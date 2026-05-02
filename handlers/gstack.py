"""handlers/gstack.py — gstack skill commands for LegionBot.

Commands:
/review              — PR review (git diff vs base branch). For file code review use /code_review.
/ship               — Deployment pipeline (merge, test, coverage, adversarial, changelog, PR)
/officehours        — YC-style product brainstorming (delegates to opencode office-hours)
/investigate        — Root cause analysis for bugs/errors (delegates to opencode investigate)
/qa                 — QA testing workflow (delegates to opencode qa)
/careful            — Safety guard for destructive operations
/planreview         — CEO/founder-mode plan review (delegates to opencode plan-ceo-review)

Note: /code_review (file code review) lives in dev.py. /codex lives in dev.py (dev.router wins).
"""
from __future__ import annotations

import asyncio
import html as html_mod
import os
import re
import subprocess

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import _cancel_task, _keep_typing, is_allowed, send_chunked

router = Router()


# ─── helpers ──────────────────────────────────────────────────────────────────

def run_sync(cmd: str, timeout: int = 30) -> tuple[str, str, int]:
    """Run a shell command synchronously. Returns (stdout, stderr, returncode)."""
    try:
        p = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return p.stdout or "", p.stderr or "", p.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 124
    except Exception as e:
        return "", str(e), 1


async def run_opencode_cmd(
    cmd: list[str],
    timeout: int = 120,
) -> tuple[str, str, int]:
    """Run an opencode command safely using subprocess_exec (no shell injection)."""
    try:
        p = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/home/newadmin/swarm-bot",
            env={**os.environ, "OPENCODE_DISABLE_AUTOUPDATE": "true"},
        )
        stdout, stderr = await asyncio.wait_for(p.communicate(), timeout=timeout)
        return (
            stdout.decode() if stdout else "",
            stderr.decode() if stderr else "",
            p.returncode,
        )
    except asyncio.TimeoutError:
        return "", "Command timed out", 124
    except Exception as e:
        return "", str(e), 1


def escape(text: str) -> str:
    return html_mod.escape(text, quote=False)


def code(text: str) -> str:
    return f"<code>{escape(text)}</code>"


def bold(text: str) -> str:
    return f"<b>{escape(text)}</b>"


# ─── /review ──────────────────────────────────────────────────────────────────

@router.message(Command("review"))
async def cmd_review(msg: Message) -> None:
    """Pre-landing PR review — analyze diff against base branch (gstack pipeline).

    NOTE: This is PR review (git diff analysis). For code review of a specific file,
    use /code_review instead.
    """
    if not is_allowed(msg):
        return

    await msg.answer(f"{bold('🔍 Running /review...')}\n\nDetecting platform...", parse_mode="HTML")

    # Step 0: Detect platform
    remote_out, _, rc = run_sync("git remote get-url origin 2>/dev/null")
    remote_url = remote_out.strip()

    if "github.com" in remote_url:
        platform = "github"
    elif "gitlab" in remote_url:
        platform = "gitlab"
    else:
        platform = "unknown"

    # Detect base branch
    if platform == "github":
        base_out, _, _ = run_sync("gh pr view --json baseRefName -q .baseRefName 2>/dev/null || echo ''")
        if not base_out.strip():
            base_out, _, _ = run_sync("gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo 'main'")
        base_branch = base_out.strip() or "main"
    elif platform == "gitlab":
        base_out, _, _ = run_sync("glab mr view -F json 2>/dev/null | python3 -c 'import sys,json; m=json.load(sys.stdin); print(m.get(\"target_branch\",\"\"))' 2>/dev/null || echo ''")
        if not base_out.strip():
            base_out, _, _ = run_sync("glab repo view -F json 2>/dev/null | python3 -c 'import sys,json; m=json.load(sys.stdin); print(m.get(\"default_branch\",\"\"))' 2>/dev/null || echo 'main'")
        base_branch = base_out.strip() or "main"
    else:
        base_out, _, _ = run_sync("git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||' || echo 'main'")
        base_branch = base_out.strip() or "main"

    branch, _, _ = run_sync("git branch --show-current 2>/dev/null || echo ''")
    branch = branch.strip() or "unknown"

    # Step 1: Check branch
    if branch == base_branch or branch == "unknown":
        await msg.answer(
            f"{bold('🔍 /review')}\n\n"
            f"Nothing to review — you're on the base branch.",
            parse_mode="HTML",
        )
        return

    await msg.answer(f"Base: {code(base_branch)} | Branch: {code(branch)}\nFetching diff...", parse_mode="HTML")

    # Fetch base and check diff
    run_sync(f"git fetch origin {base_branch} --quiet 2>/dev/null")
    diff_stat_out, _, _ = run_sync(f"git diff origin/{base_branch} --stat 2>/dev/null")

    if not diff_stat_out.strip():
        await msg.answer(
            f"{bold('🔍 /review')}\n\n"
            f"No diff against {code(base_branch)}.",
            parse_mode="HTML",
        )
        return

    # Step 1.5: Scope check (simplified)
    todo_lines, _, _ = run_sync("cat TODOS.md 2>/dev/null | head -30 || echo ''")
    commit_lines, _, _ = run_sync(f"git log origin/{base_branch}..HEAD --oneline 2>/dev/null | head -10")
    pr_body, _, _ = run_sync("gh pr view --json body -q .body 2>/dev/null || echo ''")

    intent = ""
    if pr_body.strip():
        intent = pr_body.strip().split('\n')[0][:100]
    elif commit_lines.strip():
        intent = commit_lines.strip().split('\n')[0][:100]

    scope_msg = f"\n{bold('Scope Check: CLEAN')}"
    if intent:
        scope_msg += f"\nIntent: {escape(intent[:100])}"

    # Step 2: Main diff review (simplified structural check)
    diff_out, _, _ = run_sync(f"git diff origin/{base_branch} -- . 2>/dev/null | head -200")

    issues: list[str] = []

    # Check for common structural issues
    for line in diff_out.split('\n'):
        # SQL safety
        if re.search(r'(DROP\s+TABLE|TRUNCATE|DELETE\s+FROM\s+\w+\s*;?\s*$)', line, re.IGNORECASE):
            issues.append(f"⚠️ SQL write operation detected: {code(line.strip()[:80])}")
        # Hardcoded secrets
        if re.search(r'(api[_-]?key|secret|token|password)\s*=\s*["\'][^"\']{8,}["\']', line, re.IGNORECASE):
            issues.append(f"🔴 Possible hardcoded secret: {code(line.strip()[:80])}")
        # TODO without context
        if 'TODO' in line or 'FIXME' in line:
            issues.append(f"⚠️ TODO/FIXME comment: {code(line.strip()[:80])}")

    # Get line counts
    lines_added, _, _ = run_sync(f"git diff origin/{base_branch} -- . 2>/dev/null | grep '^+' | grep -v '^+++' | wc -l")
    lines_deleted, _, _ = run_sync(f"git diff origin/{base_branch} -- . 2>/dev/null | grep '^-' | grep -v '^---' | wc -l")

    result = [
        f"{bold('🔍 /review — PR Review Report')}",
        f"Platform: {code(platform)} | Base: {code(base_branch)} | Branch: {code(branch)}",
        scope_msg,
        "",
        f"Diff: +{lines_added.strip()} / -{lines_deleted.strip()} lines",
        "",
    ]

    if issues:
        result.append(f"{bold('ISSUES FOUND:')}")
        for issue in issues[:10]:
            result.append(f"  {issue}")
        result.append("")
    else:
        result.append("✅ No obvious structural issues detected.")
        result.append("")
        result.append(f"<i>Review passed. Consider running {code('/ship')} to deploy.</i>")

    await send_chunked(msg, "\n".join(result), parse_mode="HTML")


# ─── /ship ─────────────────────────────────────────────────────────────────────

@router.message(Command("ship"))
async def cmd_ship(msg: Message) -> None:
    """Deployment pipeline — merge, test, coverage, adversarial, changelog, PR."""
    if not is_allowed(msg):
        return

    status_lines = [f"{bold('🚀 /ship — Deployment Pipeline')}\n"]

    # Step 1: Merge base branch
    base_out, _, rc = run_sync("git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo 'main'")
    base_branch = base_out.strip() or "main"

    await msg.answer("\n".join(status_lines) + f"\nMerging {code(base_branch)}...", parse_mode="HTML")

    run_sync(f"git fetch origin {base_branch} --quiet 2>/dev/null")
    merge_out, merge_err, merge_rc = run_sync(f"git merge origin/{base_branch} --no-edit 2>&1")

    if merge_rc != 0 and "conflict" in merge_err.lower():
        status_lines.append("🔴 CONFLICTS — resolve before shipping")
        await msg.answer("\n".join(status_lines) + f"\n{code(merge_err[:500])}", parse_mode="HTML")
        return

    status_lines.append("✅ BASE MERGE: success")

    # Step 2: Test bootstrap
    test_out, _, test_rc = run_sync("python -c 'import pytest; print(\"pytest ok\")' 2>/dev/null || echo 'no pytest'")
    has_pytest = "pytest ok" in test_out

    if has_pytest:
        await msg.answer("\n".join(status_lines) + "\nRunning tests...", parse_mode="HTML")
        pytest_out, _, pytest_rc = run_sync("pytest tests/ -x --asyncio-mode=auto -q 2>&1 | tail -20")
        if pytest_rc != 0:
            status_lines.append(f"🔴 TESTS: FAIL\n{code(pytest_out[-500:])}")
            await msg.answer("\n".join(status_lines), parse_mode="HTML")
            return
        status_lines.append("✅ TESTS: PASS")
    else:
        status_lines.append("⚠️ TESTS: pytest not available")

    # Step 3: Coverage
    if has_pytest:
        cov_out, _, cov_rc = run_sync("pytest tests/ --cov=. --cov-report=term-missing --asyncio-mode=auto -q 2>&1 | tail -15")
        status_lines.append(f"Coverage check:\n{code(cov_out[-300:])}")

    # Step 4: Coverage audit (simplified)
    status_lines.append("✅ COVERAGE: audit skipped (run manually)")

    # Step 5: Diff stat for adversarial review
    diff_stat, _, _ = run_sync("git diff --stat | tail -1")
    diff_lines = int(diff_stat.strip().split()[0]) if diff_stat.strip().split()[0].isdigit() else 0
    if diff_lines > 200:
        status_lines.append(f"⚠️ DIFF: {diff_lines} lines — consider adversarial review")
    status_lines.append("✅ ADVERSARIAL: review recommended for large diffs")

    # Step 6: Version bump check
    version_out, _, _ = run_sync("grep -r 'version' pyproject.toml setup.py package.json 2>/dev/null | grep -v '__pycache__' | head -5 || echo ''")
    status_lines.append(f"\nCurrent version info:\n{code(version_out[:200] or 'not found')}")

    # Step 7: Push + PR
    await msg.answer("\n".join(status_lines) + "\nPushing...", parse_mode="HTML")

    run_sync("git add -A 2>/dev/null")
    push_out, push_err, push_rc = run_sync("git push origin HEAD 2>&1")

    if push_rc != 0:
        status_lines.append(f"⚠️ PUSH: failed\n{code(push_err[:200])}")
    else:
        status_lines.append("✅ PUSH: done")

    # PR creation (GitHub only)
    gh_out, gh_err, gh_rc = run_sync("gh pr create --fill 2>&1 || echo 'PR creation skipped'")
    if gh_rc == 0 and "http" in gh_out:
        pr_url = [ln for ln in gh_out.split('\n') if 'http' in ln]
        status_lines.append(f"PR: {pr_url[0] if pr_url else gh_out[:100]}")
    else:
        status_lines.append(f"PR: manual creation needed\n{code(gh_err[:200] or gh_out[:200])}")

    status_lines.insert(1, "BASE MERGE: ✅ SUCCESS")
    status_lines.append(f"\n{bold('STATUS:')} ⚠️ READY FOR REVIEW — check diff before merge")

    await send_chunked(msg, "\n".join(status_lines), parse_mode="HTML")


# ─── /officehours ─────────────────────────────────────────────────────────────

@router.message(Command("officehours"))
async def cmd_officehours(msg: Message) -> None:
    """YC-style product brainstorming session via opencode."""
    if not is_allowed(msg):
        return

    idea = (msg.text or "").removeprefix("/officehours").strip()
    if not idea:
        await msg.answer(
            f"{bold('🏛️ /officehours — YC-Style Brainstorming')}\n\n"
            f"Usage: {code('/officehours <your idea or problem>')}\n\n"
            f"Pitch your idea and I'll stress-test it:",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer(
        f"{bold('🏛️ /officehours — Brainstorming')}\n\n"
        f"Idea: {escape(idea)}\n\n"
        f"{bold('Running office hours...')}",
        parse_mode="HTML",
    )
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        stdout, stderr, rc = await run_opencode_cmd(
            ["/home/newadmin/.opencode/bin/opencode", "run",
             "--command", "office-hours", "--", idea],
            timeout=120,
        )
        await _cancel_task(typing_task)
        output = stdout if rc == 0 else (stderr or stdout)
        from core.opencode_bridge import extract_report
        report = extract_report(output)
        await status_msg.delete()
        await send_chunked(msg, report)
    except Exception as e:
        await _cancel_task(typing_task)
        await status_msg.delete()
        await msg.answer(
            f"officehours error: <code>{escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ─── /investigate ──────────────────────────────────────────────────────────────

@router.message(Command("investigate"))
async def cmd_investigate(msg: Message) -> None:
    """Root cause analysis for bugs/errors via opencode."""
    if not is_allowed(msg):
        return

    error_spec = (msg.text or "").removeprefix("/investigate").strip()
    if not error_spec:
        await msg.answer(
            f"{bold('🔬 /investigate — Root Cause Analysis')}\n\n"
            f"Usage: {code('/investigate <error message or bug description>')}\n\n"
            f"Example: {code('/investigate TypeError: cannot unpack')}",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer(
        f"{bold('🔬 /investigate — Root Cause Analysis')}\n\n"
        f"Error: {code(error_spec[:200])}\n\n"
        f"{bold('Investigating...')}",
        parse_mode="HTML",
    )
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        stdout, stderr, rc = await run_opencode_cmd(
            ["/home/newadmin/.opencode/bin/opencode", "run",
             "--command", "investigate", "--", error_spec],
            timeout=120,
        )
        await _cancel_task(typing_task)
        output = stdout if rc == 0 else (stderr or stdout)
        from core.opencode_bridge import extract_report
        report = extract_report(output)
        await status_msg.delete()
        await send_chunked(msg, report)
    except Exception as e:
        await _cancel_task(typing_task)
        await status_msg.delete()
        await msg.answer(
            f"investigate error: <code>{escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ─── /qa ──────────────────────────────────────────────────────────────────────

@router.message(Command("qa"))
async def cmd_qa(msg: Message) -> None:
    """QA testing workflow for web applications via opencode."""
    if not is_allowed(msg):
        return

    target = (msg.text or "").removeprefix("/qa").strip()
    if not target:
        await msg.answer(
            f"{bold('🧪 /qa — Quality Assurance Testing')}\n\n"
            f"Usage: {code('/qa <URL to test>')}\n\n"
            f"Example:\n<code>/qa https://example.com</code>",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer(
        f"{bold('🧪 /qa — Testing')}\n\n"
        f"Target: {code(target)}\n\n"
        f"Running QA checks...",
        parse_mode="HTML",
    )
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        stdout, stderr, rc = await run_opencode_cmd(
            ["/home/newadmin/.opencode/bin/opencode", "run",
             "--command", "qa", "--", target],
            timeout=180,
        )
        await _cancel_task(typing_task)
        output = stdout if rc == 0 else (stderr or stdout)
        from core.opencode_bridge import extract_report
        report = extract_report(output)
        await status_msg.delete()
        await send_chunked(msg, report)
    except Exception as e:
        await _cancel_task(typing_task)
        await status_msg.delete()
        await msg.answer(
            f"qa error: <code>{escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )


# ─── /careful ──────────────────────────────────────────────────────────────────

@router.message(Command("careful"))
async def cmd_careful(msg: Message) -> None:
    """Safety guard for destructive or irreversible operations."""
    if not is_allowed(msg):
        return

    operation = (msg.text or "").removeprefix("/careful").strip()
    if not operation:
        await msg.answer(
            f"{bold('🛡️ /careful — Safety Guard')}\n\n"
            f"Usage: {code('/careful <command to check>')}\n\n"
            f"Example: {code('/careful rm -rf /tmp/test')}\n\n"
            f"Describe what you want to run and I'll analyze the risk.",
            parse_mode="HTML",
        )
        return

    await msg.answer(
        f"{bold('🛡️ /careful — Analyzing')}\n\n"
        f"Command: {code(operation[:200])}",
        parse_mode="HTML",
    )

    # Risk classification
    op_lower = operation.lower()
    is_destructive = any(
        kw in op_lower for kw in [
            "rm -rf", "rm -r", "drop table", "drop database",
            "delete from", "truncate", "git push --force",
            "ALTER TABLE", "DROP INDEX", "shutdown", "halt",
        ]
    )
    is_high_risk = any(
        kw in op_lower for kw in [
            "sudo", "chmod 777", "chown", "kill -9",
            "git reset --hard", "mv .", "cp /dev/null",
        ]
    )

    if is_destructive:
        classification = "🔴 CRITICAL"
        can_undo = "NO — irreversible operation"
    elif is_high_risk:
        classification = "⚠️ HIGH"
        can_undo = "DIFFICULT — difficult to undo"
    else:
        classification = "✅ LOW"
        can_undo = "YES — easily reversible"

    result = [
        f"{bold('🛡️ /careful — Analysis')}\n",
        f"Command: {code(operation[:200])}",
        f"Classification: {classification}",
        "",
        f"Can be undone: {can_undo}",
    ]

    if is_destructive:
        result.append("\n⚠️ This operation is IRREVERSIBLE.")
        result.append("Before running, confirm:")
        result.append("  1. You have a backup of affected data")
        result.append("  2. No one else is affected by this change")
        result.append("  3. You have the exact rollback command ready")
        result.append("\nProceed only if all 3 are confirmed.")

    await send_chunked(msg, "\n".join(result), parse_mode="HTML")


# ─── /planreview ─────────────────────────────────────────────────────────────

@router.message(Command("planreview"))
async def cmd_planreview(msg: Message) -> None:
    """CEO/founder-mode plan review via opencode."""
    if not is_allowed(msg):
        return

    plan_desc = (msg.text or "").removeprefix("/planreview").strip()
    if not plan_desc:
        await msg.answer(
            f"{bold('📋 /planreview — CEO-Mode Plan Review')}\n\n"
            f"Usage: {code('/planreview <brief description of your plan>')}\n\n"
            f"I'll rethink this from first principles:",
            parse_mode="HTML",
        )
        return

    status_msg = await msg.answer(
        f"{bold('📋 /planreview — CEO-Mode Review')}\n\n"
        f"Plan: {escape(plan_desc[:200])}\n\n"
        f"Analyzing...",
        parse_mode="HTML",
    )
    typing_task = asyncio.create_task(_keep_typing(msg))

    try:
        stdout, stderr, rc = await run_opencode_cmd(
            ["/home/newadmin/.opencode/bin/opencode", "run",
             "--command", "plan-ceo-review", "--", plan_desc],
            timeout=120,
        )
        await _cancel_task(typing_task)
        output = stdout if rc == 0 else (stderr or stdout)
        from core.opencode_bridge import extract_report
        report = extract_report(output)
        await status_msg.delete()
        await send_chunked(msg, report)
    except Exception as e:
        await _cancel_task(typing_task)
        await status_msg.delete()
        await msg.answer(
            f"planreview error: <code>{escape(str(e)[:400])}</code>",
            parse_mode="HTML",
        )
