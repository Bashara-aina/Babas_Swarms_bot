"""GitHub skills using the GitHub API."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def _github_pr_status_handler(text: str) -> str:
    """Check GitHub PR status for a repository."""
    # Extract repo from text
    repo_match = re.search(r"(?:repo|repository)[:/]?([\w\-]+/[\w\-]+)", text, re.IGNORECASE)
    if not repo_match:
        # Try to find owner/repo pattern
        repo_match = re.search(r"([\w\-]+)/([\w\-]+)", text)
        if repo_match:
            full_repo = f"{repo_match.group(1)}/{repo_match.group(2)}"
        else:
            return "Please provide a GitHub repository (e.g., 'owner/repo' or 'Check PR status for owner/repo')."
    else:
        full_repo = repo_match.group(1)

    token = os.getenv("GITHUB_TOKEN", os.getenv("GITHUB_API_TOKEN", ""))
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # Get open PRs
            async with session.get(
                f"https://api.github.com/repos/{full_repo}/pulls",
                headers=headers,
                params={"state": "open", "per_page": 10},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 404:
                    return f"❌ Repository not found: {full_repo}"
                if resp.status != 200:
                    return f"❌ GitHub API error: {resp.status}"
                prs = await resp.json()

        if not prs:
            return f"✅ No open PRs for {full_repo}"

        lines = [f"📋 Open PRs for {full_repo}:\n"]
        for pr in prs[:10]:
            title = pr.get("title", "No title")
            number = pr.get("number", "?")
            author = pr.get("user", {}).get("login", "unknown")
            draft = " [DRAFT]" if pr.get("draft") else ""
            lines.append(f"• #{number}: {title} by @{author}{draft}")
            lines.append(f"  {pr.get('html_url', '')}")

        # Also check recent merged/closed
        async with session.get(
            f"https://api.github.com/repos/{full_repo}/pulls",
            headers=headers,
            params={"state": "closed", "per_page": 5, "sort": "updated"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 200:
                closed_prs = await resp.json()
                if closed_prs:
                    lines.append("\nRecently closed PRs:")
                    for pr in closed_prs[:3]:
                        merged = "✅ merged" if pr.get("merged_at") else "❌ closed"
                        lines.append(f"• #{pr.get('number')}: {pr.get('title', '')} ({merged})")

        return "\n".join(lines)
    except Exception as exc:
        return f"❌ GitHub PR check failed: {exc}"


async def _github_commit_log_handler(text: str) -> str:
    """Get recent commit log for a repository."""
    repo_match = re.search(r"([\w\-]+)/([\w\-]+)", text)
    if not repo_match:
        return "Please provide a GitHub repository (e.g., 'owner/repo')."
    full_repo = f"{repo_match.group(1)}/{repo_match.group(2)}"

    # Check for branch specification
    branch_match = re.search(r"branch[:\s]+([\w\-]+)", text, re.IGNORECASE)
    branch = branch_match.group(1) if branch_match else "main"

    token = os.getenv("GITHUB_TOKEN", os.getenv("GITHUB_API_TOKEN", ""))
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.github.com/repos/{full_repo}/commits",
                headers=headers,
                params={"sha": branch, "per_page": 15},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 404:
                    return f"❌ Repository not found: {full_repo}"
                if resp.status != 200:
                    return f"❌ GitHub API error: {resp.status}"
                commits = await resp.json()

        if not commits:
            return f"No commits found for {full_repo} on branch {branch}."

        lines = [f"📜 Recent commits for {full_repo} ({branch}):\n"]
        for commit in commits[:12]:
            sha = commit.get("sha", "???")[:7]
            msg = commit.get("commit", {}).get("message", "No message").split("\n")[0][:80]
            author = commit.get("commit", {}).get("author", {}).get("name", "unknown")
            date = commit.get("commit", {}).get("author", {}).get("date", "")[:10]
            lines.append(f"• {sha} — {msg} ({author}, {date})")

        return "\n".join(lines)
    except Exception as exc:
        return f"❌ GitHub commit log failed: {exc}"


async def _code_review_handler(text: str) -> str:
    """Trigger a code review for a repository or diff."""
    # This skill delegates to the existing code review infrastructure
    repo_match = re.search(r"([\w\-]+)/([\w\-]+)", text)
    if not repo_match:
        return "Please provide a GitHub repository for code review (e.g., 'owner/repo')."

    # For now, return instructions on how to use the code review
    return (
        f"🔍 Code Review for {repo_match.group(0)}\n\n"
        "To perform a code review, use the /review or /code_review command with:\n"
        "- The repository URL or owner/repo\n"
        "- Specific files or PR number to review\n\n"
        "Example: /review owner/repo pull/123\n"
        "Or ask me to review specific code by pasting it here."
    )


def _register_github_skills() -> None:
    SKILL_REGISTRY.register(
        Skill(
            name="github_pr_status",
            description="Check GitHub Pull Request status for a repository",
            trigger_keywords=["pr status", "pull request", "github pr", "check pr", "open prs"],
            handler=_github_pr_status_handler,
            required_env_keys=["GITHUB_TOKEN"],
            category="github",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="github_commit_log",
            description="Get recent commit history for a GitHub repository",
            trigger_keywords=["commit log", "commits", "recent commits", "git log", "github commits"],
            handler=_github_commit_log_handler,
            required_env_keys=["GITHUB_TOKEN"],
            category="github",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="code_review",
            description="Perform a code review on a repository or pasted code",
            trigger_keywords=["code review", "review code", "audit code", "security review", "review this"],
            handler=_code_review_handler,
            required_env_keys=[],
            category="github",
        )
    )


_register_github_skills()
