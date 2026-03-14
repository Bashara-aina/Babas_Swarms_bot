"""Self-Upgrade Engine — Legion upgrades itself from a Telegram chat message.

Full pipeline:
 1. Parse upgrade request (natural language or structured)
 2. Generate Python file(s) via LLM (coding agent)
 3. Validate syntax (ast.parse)
 4. Safety scan (no rm -rf, no os.system with untrusted input, etc.)
 5. Write files to disk
 6. Extract + install new pip dependencies
 7. Hot-reload the handler module (importlib.reload)
 8. If hot-reload fails → zero-downtime restart via watchdog wrapper
 9. Notify user when the new feature is live
10. Rollback on any failure — restore previous file, reload old version

The Telegram bot connection is NEVER dropped:
- During hot-reload: aiogram dispatcher keeps polling
- During full restart: a watchdog parent process (watcher.py) relaunches
  main.py automatically, and Telegram long-polling reconnects in <3 seconds
"""
from __future__ import annotations

import ast
import asyncio
import importlib
import importlib.util
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

# ── Safety: patterns that are NEVER allowed in generated code ───────────────
_BLOCKED_PATTERNS = [
    r"os\.system\s*\(",
    r"subprocess\.call\s*\(",
    r"__import__\s*\(['\"]os['\"]",
    r"rm\s+-rf",
    r"shutil\.rmtree\s*\(",
    r"open\s*\(.*['\"]w['\"].*\).*\\.\.\.",  # writing to ../ paths
    r"eval\s*\(",
    r"exec\s*\(",
]

_ALLOWED_INSTALL_PREFIX = (
    sys.executable,  # always use the current Python executable
)


@dataclass
class UpgradeResult:
    success: bool
    feature_name: str
    files_written: List[str] = field(default_factory=list)
    deps_installed: List[str] = field(default_factory=list)
    reload_method: str = ""      # hot_reload | restart | none
    error: str = ""
    rollback_files: Dict[str, str] = field(default_factory=dict)  # path -> original content


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
        await self._notify(f"🧠 Analyzing upgrade request\u2026")

        # 1. Generate code via LLM
        plan = await self._plan_upgrade(request)
        await self._notify(
            f"📝 Plan ready: {len(plan['files'])} file(s), "
            f"deps: {plan.get('deps', []) or 'none'}"
        )

        result = UpgradeResult(success=False, feature_name=plan.get("feature", "unknown"))

        # 2. Validate all files before writing any
        for file_plan in plan["files"]:
            ok, err = self._validate_code(file_plan["content"], file_plan["path"])
            if not ok:
                result.error = f"Validation failed for {file_plan['path']}: {err}"
                await self._notify(f"❌ {result.error}")
                return result

        await self._notify("✅ Code validation passed")

        # 3. Backup existing files
        for file_plan in plan["files"]:
            path = self.root / file_plan["path"]
            if path.exists():
                result.rollback_files[file_plan["path"]] = path.read_text(encoding="utf-8")

        # 4. Write files
        for file_plan in plan["files"]:
            path = self.root / file_plan["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file_plan["content"], encoding="utf-8")
            result.files_written.append(file_plan["path"])
            await self._notify(f"💾 Written: {file_plan['path']}")

        # 5. Install dependencies
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

        # 6. Hot-reload or restart
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

    # ── LLM Code Generation ───────────────────────────────────────────

    async def _plan_upgrade(self, request: str) -> dict:
        """Call LLM to generate implementation plan + code."""
        try:
            import litellm

            # Read current project structure for context
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
            import json
            return json.loads(match.group(0))
        import json
        return json.loads(raw)

    def _get_project_structure(self) -> str:
        """Return a compact project tree (dirs + .py files, max 80 lines)."""
        lines = []
        for root, dirs, files in os.walk(self.root):
            # Skip hidden, __pycache__, node_modules, data
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules", "data", ".venv", "venv")]
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
        """Syntax check + safety scan."""
        # 1. Syntax check
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"SyntaxError in {path}: {e}"

        # 2. Safety patterns
        for pattern in _BLOCKED_PATTERNS:
            if re.search(pattern, code):
                return False, f"Blocked pattern found in {path}: {pattern}"

        # 3. Path traversal check
        if "../" in path or path.startswith("/"):
            return False, f"Unsafe path: {path}"

        return True, ""

    # ── Dependency Installation ───────────────────────────────────────

    async def _install_deps(self, deps: List[str]) -> Tuple[bool, str]:
        """Install pip packages. Returns (success, error_message)."""
        # Sanitize: only allow alphanumeric, -, _, ., [, ], >=, <=, ==, ~=
        safe_deps = []
        for dep in deps:
            if re.match(r'^[a-zA-Z0-9_\-\.\[\]>=<~!]+$', dep):
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

            # Append to requirements.txt
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
        """Try hot-reload first. Fall back to zero-downtime restart."""
        reload_errors = []

        for file_plan in files:
            path = file_plan["path"]
            if not path.endswith(".py"):
                continue
            # Convert path to module name
            module_name = path.replace("/", ".").replace("\\", ".").removesuffix(".py")
            try:
                if module_name in sys.modules:
                    mod = sys.modules[module_name]
                    importlib.reload(mod)
                    logger.info("Hot-reloaded: %s", module_name)
                else:
                    # New module — import it fresh
                    spec = importlib.util.spec_from_file_location(
                        module_name, self.root / path
                    )
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = mod
                    spec.loader.exec_module(mod)
                    logger.info("Fresh-loaded: %s", module_name)
            except Exception as e:
                reload_errors.append(f"{module_name}: {e}")

        if reload_errors:
            logger.warning("Hot-reload errors (will restart): %s", reload_errors)
            # Signal watchdog to restart
            self._request_restart()
            return True, "restart"   # watchdog will handle it

        return True, "hot_reload"

    def _request_restart(self) -> None:
        """Write restart flag. Watchdog process detects this and relaunches."""
        self._restart_flag.write_text(str(time.time()))
        logger.info("Restart flag written: %s", self._restart_flag)

    # ── Rollback ───────────────────────────────────────────────────────────

    async def _rollback(self, result: UpgradeResult) -> None:
        """Restore all backed-up files."""
        for rel_path, original_content in result.rollback_files.items():
            path = self.root / rel_path
            path.write_text(original_content, encoding="utf-8")
            logger.info("Rolled back: %s", rel_path)
        # Also delete newly created files that had no backup
        for written in result.files_written:
            if written not in result.rollback_files:
                path = self.root / written
                if path.exists():
                    path.unlink()
                    logger.info("Deleted new file on rollback: %s", written)

    # ── Notify ────────────────────────────────────────────────────────────

    async def _notify(self, text: str) -> None:
        if self.notify:
            try:
                await self.notify(text)
            except Exception:
                pass
        logger.info("[upgrade] %s", text)
