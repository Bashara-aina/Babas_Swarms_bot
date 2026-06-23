"""
SWE-agent bridge for swarm-bot.
Takes a GitHub issue URL, runs SWE-agent, streams output to Telegram.
Usage: /fix https://github.com/owner/repo/issues/123
"""

from __future__ import annotations

import asyncio
import os
import re
from urllib.parse import urlparse

SWE_AGENT_PATH = os.getenv("SWE_AGENT_PATH", "/home/newadmin/swe-agent")
AGENTS_TELEMETRY_ENDPOINT = os.getenv("AGENTS_TELEMETRY_ENDPOINT", "")


def parse_github_issue(url: str) -> tuple[str, str, int]:
    """Parse a GitHub issue URL into (owner, repo, issue_number)."""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    # Accept github.com and www.github.com
    if not (netloc == "github.com" or netloc == "www.github.com"):
        raise ValueError(f"Invalid GitHub issue URL: {url}")
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 4 and parts[2] == "issues":
        return parts[0], parts[1], int(parts[3])
    raise ValueError(f"Invalid GitHub issue URL: {url}")


class SWEBridge:
    """Async wrapper for SWE-agent CLI."""

    def __init__(self, swe_agent_path: str | None = None) -> None:
        self.swe_agent_path = swe_agent_path or SWE_AGENT_PATH
        self.telemetry_endpoint = AGENTS_TELEMETRY_ENDPOINT

    async def fix_issue(
        self,
        issue_url: str,
        *,
        model: str = "gpt-4o",
        open_pr: bool = True,
    ) -> str:
        """Run SWE-agent to fix a GitHub issue. Returns PR URL on success."""
        owner, repo, issue_num = parse_github_issue(issue_url)

        cmd = [
            "python", "-m", "swe_agent",
            "--repo", f"{owner}/{repo}",
            "--issue", str(issue_num),
            "--model", model,
        ]
        if open_pr:
            cmd.append("--open-pr")

        env = dict(os.environ)
        if self.telemetry_endpoint:
            env["AGENTS_TELEMETRY_ENDPOINT"] = self.telemetry_endpoint

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.swe_agent_path,
            env=env,
        )

        output_lines: list[str] = []
        async for line in proc.stdout:
            decoded = line.decode().strip()
            output_lines.append(decoded)

        await proc.wait()
        if proc.returncode == 0:
            pr_match = re.search(
                r"PR opened: (https://github\.com/.*)",
                "\n".join(output_lines),
            )
            return pr_match.group(1) if pr_match else "PR opened successfully"
        return f"SWE-agent failed with code {proc.returncode}"

    async def dry_run(self, issue_url: str, *, model: str = "gpt-4o") -> str:
        """Run SWE-agent in dry-run mode (no PR opened)."""
        owner, repo, issue_num = parse_github_issue(issue_url)

        cmd = [
            "python", "-m", "swe_agent",
            "--repo", f"{owner}/{repo}",
            "--issue", str(issue_num),
            "--model", model,
            "--dry-run",
        ]

        env = dict(os.environ)
        if self.telemetry_endpoint:
            env["AGENTS_TELEMETRY_ENDPOINT"] = self.telemetry_endpoint

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.swe_agent_path,
            env=env,
        )

        output_lines: list[str] = []
        async for line in proc.stdout:
            decoded = line.decode().strip()
            output_lines.append(decoded)

        await proc.wait()
        return "\n".join(output_lines)
