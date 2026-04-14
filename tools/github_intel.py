"""GitHub Trending Intelligence Engine — Legion v6.

Daily pipeline:
 1. Scrape github.com/trending (Python, JS, or any language) via Playwright
 2. LLM (architect) evaluates each repo for Legion relevance (score 0-10)
 3. Repos scoring ≥ 6 included in the daily report sent to the user
 4. Repos scoring ≥ 8 trigger skill self-discovery:
    a. LLM drafts a skills/{repo}.md file
    b. Sandbox smoke-test (pip install in /tmp, run import test)
    c. Only if smoke-test passes: write skill file + update skill_loader.py

Manual commands: /github_intel, /eval_repo <url>, /upgrade_from <url>
Scheduled: daily at 9:00 AM via main.py.
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Legion context injected into LLM relevance prompts
_LEGION_CONTEXT = (
    "Legion is a Telegram AI assistant running on Linux (Ubuntu, RTX 3060 12GB, 64GB RAM). "
    "It uses: Python 3.11, litellm, aiogram 3.x, Playwright, aiosqlite, mem0, Groq, Cerebras, Gemini, "
    "OpenRouter, Ollama (local vision), Supabase, aiohttp. "
    "It manages ML training (PyTorch WorkerNet), web scraping, email, desktop control, "
    "multi-agent orchestration, and business management for rumahlabuh.com. "
    "The owner (Bashara) is a Data Science MSc student in Tokyo specialising in pose estimation."
)


@dataclass
class TrendingRepo:
    name: str  # e.g. "owner/repo"
    url: str
    description: str
    stars: str
    language: str
    topics: list[str] = field(default_factory=list)


@dataclass
class RepoEvaluation:
    repo: TrendingRepo
    relevance_score: int  # 0-10
    pros: list[str]
    cons: list[str]
    use_case: str
    risk: str


class GitHubIntelEngine:
    """Scrapes GitHub trending, evaluates repos, and can trigger skill self-discovery."""

    # ── Scraping ─────────────────────────────────────────────────────────────

    async def fetch_trending(
        self,
        language: str = "",
        since: str = "daily",
    ) -> list[TrendingRepo]:
        """Scrape github.com/trending via Playwright. Returns up to 25 repos."""
        url = "https://github.com/trending"
        if language:
            url += f"/{language.lower()}"
        url += f"?since={since}"

        try:
            from tools.web_browser import browse_url

            html_content = await browse_url(url)
            return self._parse_trending_html(html_content)
        except Exception as exc:
            logger.warning("[GitHubIntel] Playwright scrape failed: %s — trying fallback", exc)
            return await self._fetch_trending_fallback(url)

    def _parse_trending_html(self, content: str) -> list[TrendingRepo]:
        """Parse raw HTML from github.com/trending into TrendingRepo objects."""
        repos: list[TrendingRepo] = []
        # Find repo name patterns: "owner/repo"
        name_pattern = re.compile(r'href="/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"')
        desc_pattern = re.compile(r'<p[^>]*class="[^"]*color-fg-muted[^"]*"[^>]*>\s*([^<]{10,300})\s*</p>')
        star_pattern = re.compile(r"([\d,]+)\s*stars?\s+today", re.IGNORECASE)

        names_found: list[str] = []
        for m in name_pattern.finditer(content):
            name = m.group(1)
            if name not in names_found and "/" in name and not name.startswith("github/"):
                names_found.append(name)
            if len(names_found) >= 25:
                break

        descriptions = [m.group(1).strip() for m in desc_pattern.finditer(content)]
        stars_list = [m.group(1) for m in star_pattern.finditer(content)]

        for i, name in enumerate(names_found):
            repos.append(
                TrendingRepo(
                    name=name,
                    url=f"https://github.com/{name}",
                    description=descriptions[i] if i < len(descriptions) else "",
                    stars=stars_list[i] if i < len(stars_list) else "?",
                    language="",
                )
            )
        return repos

    async def _fetch_trending_fallback(self, url: str) -> list[TrendingRepo]:
        """Fallback: use aiohttp raw GET + regex."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    content = await resp.text()
            return self._parse_trending_html(content)
        except Exception as exc:
            logger.error("[GitHubIntel] Fallback also failed: %s", exc)
            return []

    async def fetch_readme(self, repo_url: str) -> str:
        """Fetch the README for a repo (for /upgrade_from context)."""
        raw_url = repo_url.replace("https://github.com/", "https://raw.githubusercontent.com/")
        raw_url += "/refs/heads/main/README.md"
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(raw_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        return (await resp.text())[:6000]
        except Exception:
            pass
        # Try master branch
        raw_url_master = raw_url.replace("/main/README.md", "/master/README.md")
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(raw_url_master, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        return (await resp.text())[:6000]
        except Exception:
            pass
        return ""

    # ── Evaluation ───────────────────────────────────────────────────────────

    async def evaluate_relevance(self, repo: TrendingRepo) -> RepoEvaluation:
        """Ask LLM to score the repo's relevance to Legion (0-10) with pros/cons."""
        from llm_client import call_llm

        prompt = (
            f"You are evaluating a GitHub repository for relevance to an AI assistant called Legion.\n\n"
            f"Legion context: {_LEGION_CONTEXT}\n\n"
            f"Repository: {repo.name}\n"
            f"URL: {repo.url}\n"
            f"Description: {repo.description or 'No description'}\n"
            f"Language: {repo.language or 'Unknown'}\n"
            f"Stars today: {repo.stars}\n\n"
            "Rate relevance 0-10 (10 = extremely useful, 0 = completely irrelevant).\n"
            "Output JSON only:\n"
            '{"relevance_score": 7, "pros": ["..."], "cons": ["..."], '
            '"use_case": "How Legion could use this", "risk": "Any concerns"}'
        )
        try:
            raw = await call_llm(
                messages=[{"role": "user", "content": prompt}],
                model="groq/llama-3.3-70b-versatile",
                temperature=0.2,
                max_tokens=300,
            )
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_match:
                import json

                data = json.loads(json_match.group(0))
                return RepoEvaluation(
                    repo=repo,
                    relevance_score=int(data.get("relevance_score", 0)),
                    pros=data.get("pros", []),
                    cons=data.get("cons", []),
                    use_case=data.get("use_case", ""),
                    risk=data.get("risk", ""),
                )
        except Exception as exc:
            logger.warning("[GitHubIntel] evaluate failed for %s: %s", repo.name, exc)
        return RepoEvaluation(repo=repo, relevance_score=0, pros=[], cons=[], use_case="", risk="")

    async def evaluate_all(self, repos: list[TrendingRepo]) -> list[RepoEvaluation]:
        """Evaluate all repos in parallel (max 5 at a time to avoid rate limits)."""
        results: list[RepoEvaluation] = []
        chunk_size = 5
        for i in range(0, len(repos), chunk_size):
            chunk = repos[i : i + chunk_size]
            batch = await asyncio.gather(
                *[self.evaluate_relevance(r) for r in chunk],
                return_exceptions=True,
            )
            for r in batch:
                if isinstance(r, RepoEvaluation):
                    results.append(r)
            await asyncio.sleep(1)  # brief pause between batches
        return sorted(results, key=lambda e: e.relevance_score, reverse=True)

    # ── Report generation ─────────────────────────────────────────────────────

    async def generate_intel_report(self, evals: list[RepoEvaluation]) -> str:
        """Format top repos as a Telegram HTML message."""
        top = [e for e in evals if e.relevance_score >= 6][:5]
        if not top:
            return "No highly relevant repos in today's trending list. Check back tomorrow!"

        lines: list[str] = ["<b>GitHub Trending Intel — Top Picks for Legion</b>\n"]
        for e in top:
            score_emoji = "🔥" if e.relevance_score >= 8 else "⭐"
            lines.append(
                f"{score_emoji} <b>{html.escape(e.repo.name)}</b> "
                f"[{e.relevance_score}/10] ⭐{e.repo.stars}\n"
                f"<i>{html.escape(e.repo.description[:120])}</i>\n"
                f"<b>Use case:</b> {html.escape(e.use_case[:150])}\n"
                f"<b>Pros:</b> {html.escape(', '.join(e.pros[:2]))}\n"
                f"<b>Cons:</b> {html.escape(e.cons[0] if e.cons else 'none')}\n"
                f"<code>/upgrade_from {e.repo.url}</code>\n"
            )
        return "\n".join(lines)

    # ── Daily scan ────────────────────────────────────────────────────────────

    async def run_daily_scan(self, notify_fn: Any) -> None:
        """Full pipeline: fetch → evaluate → report → skill discovery for high scorers."""
        try:
            await notify_fn("Scanning GitHub trending for useful repos...")
            repos = await self.fetch_trending(language="python")
            if not repos:
                await notify_fn("GitHub trending scrape returned no repos. Will retry tomorrow.")
                return

            evals = await self.evaluate_all(repos)
            report = await self.generate_intel_report(evals)
            await notify_fn(report)

            # Trigger skill self-discovery for highly relevant repos
            high_value = [e for e in evals if e.relevance_score >= 8]
            for ev in high_value[:2]:  # max 2 auto-discoveries per run
                await self._discover_skill(ev, notify_fn)

        except Exception as exc:
            logger.error("[GitHubIntel] daily scan failed: %s", exc)
            try:
                await notify_fn(f"GitHub intel scan failed: {exc}")
            except Exception:
                pass

    # ── Skill self-discovery ──────────────────────────────────────────────────

    async def _discover_skill(self, ev: RepoEvaluation, notify_fn: Any) -> None:
        """Draft + sandbox-validate + write a skill file for a high-relevance repo."""
        repo_name = ev.repo.name.split("/")[-1].lower().replace("_", "-")
        skill_path = Path("skills") / f"{repo_name}.md"

        if skill_path.exists():
            return  # Already have a skill for this repo

        readme = await self.fetch_readme(ev.repo.url)
        skill_content = await self._draft_skill_file(ev, readme)
        if not skill_content:
            return

        # Sandbox validation
        pkg_name = repo_name.replace("-", "_")
        passed, error = await self._sandbox_smoke_test(pkg_name)
        if not passed:
            await notify_fn(
                f"Skill discovery for <b>{html.escape(ev.repo.name)}</b>: "
                f"smoke test failed — {html.escape(str(error)[:200])}. Skill file NOT written."
            )
            return

        skill_path.write_text(skill_content, encoding="utf-8")
        logger.info("[GitHubIntel] Wrote skill file: %s", skill_path)
        await notify_fn(
            f"✅ New skill discovered: <b>{html.escape(ev.repo.name)}</b>\n"
            f"Smoke test passed. Skill file written to <code>{skill_path}</code>"
        )

    async def _draft_skill_file(self, ev: RepoEvaluation, readme: str) -> str:
        """Ask LLM to generate a skill markdown file."""
        from llm_client import call_llm

        prompt = (
            f"Write a Legion skill file for this GitHub library:\n\n"
            f"Repo: {ev.repo.name}\n"
            f"Description: {ev.repo.description}\n"
            f"Use case for Legion: {ev.use_case}\n"
            f"README excerpt:\n{readme[:2000]}\n\n"
            "Format as markdown. Start with `# Skill: {repo name}`\n"
            "Include: when to use, how to import/call it, example code snippets, limitations."
        )
        try:
            raw = await call_llm(
                messages=[{"role": "user", "content": prompt}],
                model="groq/llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=800,
            )
        except Exception as exc:
            logger.warning("[GitHubIntel] skill draft failed: %s", exc)
            return ""

    async def _sandbox_smoke_test(self, package_name: str) -> tuple[bool, str]:
        """Install package in a temp dir and try to import it. Returns (passed, error)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Install
            install_result = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-m", "pip", "install", "--target", tmpdir, "--quiet", package_name],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if install_result.returncode != 0:
                return False, f"pip install failed: {install_result.stderr[:200]}"

            # Import test
            import_code = f"import sys; sys.path.insert(0, '{tmpdir}'); import {package_name}; print('ok')"
            test_result = await asyncio.to_thread(
                subprocess.run,
                [sys.executable, "-c", import_code],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if test_result.returncode == 0 and "ok" in test_result.stdout:
                return True, ""
            return False, test_result.stderr[:200] or test_result.stdout[:200]
