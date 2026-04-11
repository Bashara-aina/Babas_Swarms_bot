"""Self-Upgrade Engine — Legion upgrades itself from a Telegram chat message.

Full pipeline:
 1. Parse upgrade request (natural language or structured)
 2. LLM-powered GitHub trend scanner with pros/cons evaluator (NEW)
 3. Generate Python file(s) via LLM (coding agent)
 4. Validate syntax (ast.parse)
 5. Safety scan
 6. Write files to disk
 7. Extract + install new pip dependencies
 8. Hot-reload the handler module
 9. If hot-reload fails → zero-downtime restart via watchdog
10. Notify user when the new feature is live
11. Rollback on any failure
"""

from __future__ import annotations

import ast
import asyncio
import importlib
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Coroutine, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_BLOCKED_PATTERNS = [
    r"os\.system\s*\(",
    r"subprocess\.call\s*\(",
    r"__import__\s*\(['\"]os['\"]",
    r"rm\s+-rf",
    r"shutil\.rmtree\s*\(",
    r"open\s*\(.*['\"]w['\"].*\).*\\.\.\.",
    r"eval\s*\(",
    r"exec\s*\(",
]

_ALLOWED_INSTALL_PREFIX = (sys.executable,)


@dataclass
class RepoEvaluation:
    """LLM-powered evaluation of a trending GitHub repository."""

    repo_name: str
    description: str
    stars: int
    pros: List[str]
    cons: List[str]
    effort_estimate: str  # low | medium | high
    risk_level: str  # low | medium | high
    relevance_score: float  # 0.0 - 1.0
    recommendation: str  # integrate | monitor | skip
    integration_summary: str  # what would actually change in Legion


@dataclass
class UpgradeResult:
    success: bool
    feature_name: str
    files_written: List[str] = field(default_factory=list)
    deps_installed: List[str] = field(default_factory=list)
    reload_method: str = ""
    error: str = ""
    rollback_files: Dict[str, str] = field(default_factory=dict)


class SelfUpgradeEngine:
    """Generates, validates, writes, and hot-reloads new bot features."""

    def __init__(
        self,
        bot_root: Path = Path("."),
        notify_cb: Optional[Callable[[str], Coroutine]] = None,
    ):
        self.root = bot_root.resolve()
        self.notify = notify_cb
        self._restart_flag = self.root / "data" / ".restart_requested"
        self._restart_flag.parent.mkdir(parents=True, exist_ok=True)

    # ── Public API ───────────────────────────────────────────────────

    async def upgrade(self, request: str, user_id: int = 0) -> UpgradeResult:
        """Full upgrade pipeline from natural-language request."""
        await self._notify("🧠 Analyzing upgrade request…")
        plan = await self._plan_upgrade(request)
        await self._notify(f"📝 Plan ready: {len(plan['files'])} file(s), deps: {plan.get('deps', []) or 'none'}")
        result = UpgradeResult(success=False, feature_name=plan.get("feature", "unknown"))

        for file_plan in plan["files"]:
            ok, err = self._validate_code(file_plan["content"], file_plan["path"])
            if not ok:
                result.error = f"Validation failed for {file_plan['path']}: {err}"
                await self._notify(f"❌ {result.error}")
                return result

        await self._notify("✅ Code validation passed")

        for file_plan in plan["files"]:
            path = self.root / file_plan["path"]
            if path.exists():
                result.rollback_files[file_plan["path"]] = path.read_text(encoding="utf-8")

        for file_plan in plan["files"]:
            path = self.root / file_plan["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file_plan["content"], encoding="utf-8")
            result.files_written.append(file_plan["path"])
            await self._notify(f"💾 Written: {file_plan['path']}")

        deps = plan.get("deps", [])
        if deps:
            await self._notify(f"📦 Installing: {', '.join(deps)}")
            ok, err = await self._install_deps(deps)
            if not ok:
                await self._rollback(result)
                result.error = f"pip install failed: {err}"
                await self._notify(f"❌ {result.error} — rolled back")
                return result
            result.deps_installed = deps
            await self._notify(f"✅ Installed: {', '.join(deps)}")

        reload_ok, method = await self._reload_or_restart(plan["files"])
        result.reload_method = method

        if not reload_ok:
            await self._rollback(result)
            result.error = "Hot-reload failed, rollback complete"
            await self._notify(f"❌ {result.error}")
            return result

        result.success = True
        files_str = ", ".join(f"`{f}`" for f in result.files_written)
        await self._notify(
            f"🚀 <b>Upgrade complete!</b>\n"
            f"Feature: <b>{result.feature_name}</b>\n"
            f"Files: {files_str}\n"
            f"Deps: {', '.join(result.deps_installed) or 'none'}\n"
            f"Method: {method}"
        )
        return result

    # ── GitHub Trending Intelligence (NEW) ───────────────────────────

    async def scan_github_trending(
        self,
        topic: str = "ai-agent",
        limit: int = 10,
    ) -> List[RepoEvaluation]:
        """Fetch trending GitHub repos and evaluate each with LLM pros/cons analysis.

        Returns a list of RepoEvaluation sorted by relevance_score DESC.
        """
        await self._notify(f"🔍 Scanning GitHub trending repos for topic: <code>{topic}</code>")

        repos = await self._fetch_trending_repos(topic, limit)
        if not repos:
            await self._notify("⚠️ No trending repos found (check GITHUB_TOKEN)")
            return []

        await self._notify(f"📦 Found {len(repos)} repos — running LLM evaluation...")
        evaluations: List[RepoEvaluation] = []

        for repo in repos:
            try:
                eval_result = await self._llm_evaluate_repo(repo)
                evaluations.append(eval_result)
            except Exception as e:
                logger.warning("[SelfUpgrade] Repo eval failed for %s: %s", repo.get("name"), e)

        evaluations.sort(key=lambda x: x.relevance_score, reverse=True)
        return evaluations

    async def _fetch_trending_repos(self, topic: str, limit: int) -> List[dict]:
        """Fetch trending repos from GitHub API."""
        try:
            import aiohttp

            token = os.getenv("GITHUB_TOKEN", "")
            headers = {"Accept": "application/vnd.github.v3+json"}
            if token:
                headers["Authorization"] = f"token {token}"

            query = f"topic:{topic} stars:>100"
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={limit}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.warning("[SelfUpgrade] GitHub API returned %d", resp.status)
                        return []
                    data = await resp.json()
                    items = data.get("items", [])
                    return [
                        {
                            "name": r["full_name"],
                            "description": r.get("description") or "",
                            "stars": r.get("stargazers_count", 0),
                            "url": r.get("html_url", ""),
                            "language": r.get("language") or "unknown",
                            "topics": r.get("topics", []),
                        }
                        for r in items
                    ]
        except Exception as e:
            logger.warning("[SelfUpgrade] GitHub trending fetch failed: %s", e)
            return []

    async def _llm_evaluate_repo(self, repo: dict) -> RepoEvaluation:
        """Use LLM to evaluate a repo with structured pros/cons/risk/effort."""
        import litellm

        structure = self._get_project_structure()
        prompt = f"""
You are evaluating whether a GitHub repository is worth integrating into Legion,
a personal AI assistant Telegram bot for a data scientist (Bashara) running on
Linux with RTX 3060, Python 3.13, aiogram 3.x, litellm.

Current Legion project structure (compact):
{structure[:1500]}

Repository to evaluate:
  Name: {repo["name"]}
  Description: {repo["description"]}
  Stars: {repo["stars"]:,}
  Language: {repo["language"]}
  Topics: {", ".join(repo.get("topics", []))}
  URL: {repo["url"]}

Task: Evaluate this repo for integration into Legion. Output ONLY valid JSON:
{{
  "pros": ["specific benefit 1", "specific benefit 2"],
  "cons": ["specific drawback 1"],
  "effort_estimate": "low|medium|high",
  "risk_level": "low|medium|high",
  "relevance_score": 0.0,
  "recommendation": "integrate|monitor|skip",
  "integration_summary": "one sentence: what would actually change in Legion if integrated"
}}

Scoring guide:
  relevance_score 0.8-1.0: directly improves Legion's core capabilities
  relevance_score 0.5-0.8: useful addition, moderate effort
  relevance_score 0.0-0.5: not relevant or too risky

Output ONLY the JSON.
"""
        resp = await litellm.acompletion(
            model="groq/llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"```(?:json)?\n?", "", raw).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        parsed = json.loads(match.group(0) if match else raw)

        return RepoEvaluation(
            repo_name=repo["name"],
            description=repo["description"],
            stars=repo["stars"],
            pros=parsed.get("pros", []),
            cons=parsed.get("cons", []),
            effort_estimate=parsed.get("effort_estimate", "medium"),
            risk_level=parsed.get("risk_level", "medium"),
            relevance_score=float(parsed.get("relevance_score", 0.0)),
            recommendation=parsed.get("recommendation", "skip"),
            integration_summary=parsed.get("integration_summary", ""),
        )

    def format_evaluations_for_telegram(self, evals: List[RepoEvaluation]) -> str:
        """Format repo evaluations as a Telegram HTML message."""
        if not evals:
            return "No evaluations available."

        lines = ["🔬 <b>GitHub Trending — Legion Self-Upgrade Analysis</b>\n"]
        for ev in evals[:8]:
            rec_icon = {"integrate": "✅", "monitor": "👀", "skip": "❌"}.get(ev.recommendation, "❓")
            score_bar = "█" * round(ev.relevance_score * 10) + "░" * (10 - round(ev.relevance_score * 10))
            lines.append(
                f"{rec_icon} <b>{ev.repo_name}</b> ⭐{ev.stars:,}\n"
                f"  <i>{ev.description[:80]}</i>\n"
                f"  Relevance: <code>{score_bar}</code> {ev.relevance_score:.1f}\n"
                f"  Effort: {ev.effort_estimate} | Risk: {ev.risk_level}\n"
            )
            if ev.pros:
                lines.append("  ✅ " + " | ".join(ev.pros[:2]))
            if ev.cons:
                lines.append("  ⚠️ " + " | ".join(ev.cons[:2]))
            lines.append(f"  → {ev.integration_summary}")
            lines.append("")

        integrate_count = sum(1 for e in evals if e.recommendation == "integrate")
        lines.append(
            f"<b>Summary:</b> {integrate_count} repo(s) recommended for integration. "
            "Reply with the repo name to proceed."
        )
        return "\n".join(lines)

    # ── Weekly Trending Digest ────────────────────────────────────────────────

    async def scan_weekly_trends(
        self,
        topics: list[str] | None = None,
        limit_per_topic: int = 5,
    ) -> str:
        """
        Fetch top trending repos across multiple topics and return a Telegram digest.

        Args:
            topics: List of GitHub topic strings (default: ["ai-agent", "llm", "telegram-bot"])
            limit_per_topic: Max repos per topic (default 5)

        Returns:
            Telegram HTML formatted digest string.
        """
        if topics is None:
            topics = ["ai-agent", "llm", "telegram-bot"]

        await self._notify("📊 <b>Weekly GitHub Trend Digest</b> — scanning…")

        all_evals: list[RepoEvaluation] = []
        for topic in topics:
            evals = await self.scan_github_trending(topic=topic, limit=limit_per_topic)
            all_evals.extend(evals)

        if not all_evals:
            return "📊 <b>Weekly GitHub Trend Digest</b>\nNo trending repos found — check GITHUB_TOKEN."

        # Sort by relevance
        all_evals.sort(key=lambda x: x.relevance_score, reverse=True)

        # Deduplicate by repo_name
        seen: set[str] = set()
        unique_evals = [e for e in all_evals if e.repo_name not in seen and not seen.add(e.repo_name)]

        digest = self.format_evaluations_for_telegram(unique_evals[:10])
        return digest

    # ── LLM Code Generation ───────────────────────────────────────────

    async def _plan_upgrade(self, request: str) -> dict:
        try:
            import litellm

            structure = self._get_project_structure()
            prompt = f"""
You are upgrading a Telegram AI bot (Legion). The bot uses:
- aiogram 3.x for Telegram
- litellm for LLM calls
- Python 3.11+
- Project root: handlers/ tools/ core/ swarms_bot/

Current project structure:
{structure}

Upgrade request: {request}

Generate implementation. Output ONLY valid JSON:
{{
  "feature": "short feature name",
  "description": "what this adds",
  "deps": ["pandas", "plotly"],
  "files": [
    {{
      "path": "handlers/dashboard.py",
      "description": "Telegram handler for /dashboard command",
      "content": "# full Python file content here"
    }}
  ],
  "handler_registration": "from handlers import dashboard\nrouter.include_router(dashboard.router)",
  "notes": "Register router in main.py on_startup"
}}

Rules:
- All paths relative to project root
- New Telegram commands go in handlers/
- Utility/logic goes in tools/ or core/
- Use async/await throughout
- Import from existing modules (llm_client, agents, etc.) where possible
- No hardcoded secrets — read from os.environ
- No os.system(), eval(), exec()
- Respond with ONLY the JSON
"""
            response = await litellm.acompletion(
                model="groq/llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=8192,
            )
            raw = response.choices[0].message.content or ""
            return self._parse_plan_json(raw)
        except Exception as e:
            logger.error("LLM plan generation failed: %s", e)
            raise

    def _parse_plan_json(self, raw: str) -> dict:
        raw = re.sub(r"```(?:json)?\n?", "", raw).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(raw)

    def _get_project_structure(self) -> str:
        lines = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in ("__pycache__", "node_modules", "data", ".venv", "venv")
            ]
            rel = Path(root).relative_to(self.root)
            indent = "  " * len(rel.parts)
            lines.append(f"{indent}{rel}/")
            for f in files:
                if f.endswith(".py"):
                    lines.append(f"{indent}  {f}")
            if len(lines) > 80:
                lines.append("  ... (truncated)")
                break
        return "\n".join(lines)

    # ── Validation ──────────────────────────────────────────────────

    def _validate_code(self, code: str, path: str) -> Tuple[bool, str]:
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"SyntaxError in {path}: {e}"
        for pattern in _BLOCKED_PATTERNS:
            if re.search(pattern, code):
                return False, f"Blocked pattern found in {path}: {pattern}"
        if "../" in path or path.startswith("/"):
            return False, f"Unsafe path: {path}"
        return True, ""

    # ── Dependency Installation ───────────────────────────────────────

    async def _install_deps(self, deps: List[str]) -> Tuple[bool, str]:
        safe_deps = []
        for dep in deps:
            if re.match(r"^[a-zA-Z0-9_\-\.\[\]>=<~!]+$", dep):
                safe_deps.append(dep)
            else:
                return False, f"Unsafe dependency name: {dep}"
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + safe_deps
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            if proc.returncode != 0:
                return False, stderr.decode()[:500]
            req_path = self.root / "requirements.txt"
            if req_path.exists():
                existing = req_path.read_text()
                new_deps = [d for d in safe_deps if d.split("[")[0] not in existing]
                if new_deps:
                    with open(req_path, "a") as f:
                        f.write("\n" + "\n".join(new_deps) + "\n")
            return True, ""
        except asyncio.TimeoutError:
            return False, "pip install timed out (120s)"
        except Exception as e:
            return False, str(e)

    # ── Hot-reload / Restart ───────────────────────────────────────────

    async def _reload_or_restart(self, files: List[dict]) -> Tuple[bool, str]:
        reload_errors = []
        for file_plan in files:
            path = file_plan["path"]
            if not path.endswith(".py"):
                continue
            module_name = path.replace("/", ".").replace("\\", ".").removesuffix(".py")
            try:
                if module_name in sys.modules:
                    mod = sys.modules[module_name]
                    importlib.reload(mod)
                else:
                    spec = importlib.util.spec_from_file_location(module_name, self.root / path)
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = mod
                    spec.loader.exec_module(mod)
            except Exception as e:
                reload_errors.append(f"{module_name}: {e}")
        if reload_errors:
            self._request_restart()
            return True, "restart"
        return True, "hot_reload"

    def _request_restart(self) -> None:
        self._restart_flag.write_text(str(time.time()))

    async def _rollback(self, result: UpgradeResult) -> None:
        for rel_path, original_content in result.rollback_files.items():
            path = self.root / rel_path
            path.write_text(original_content, encoding="utf-8")
        for written in result.files_written:
            if written not in result.rollback_files:
                path = self.root / written
                if path.exists():
                    path.unlink()

    async def _notify(self, text: str) -> None:
        if self.notify:
            try:
                await self.notify(text)
            except Exception:
                pass
        logger.info("[upgrade] %s", text)
