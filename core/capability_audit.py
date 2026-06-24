"""Capability Audit — monthly self-audit of Legion's capabilities and gaps.

Runs a monthly self-audit comparing available skills/agents against a benchmark
list of capabilities, identifies gaps, and sends a Telegram digest.

Usage:
    audit = CapabilityAudit()
    report = await audit.run_audit()
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Capability benchmark list ─────────────────────────────────────────────────

_CAPABILITY_BENCHMARK = [
    # Core capabilities
    ("Proactive scheduling", "core/proactive/scheduler.py"),
    ("Soul engine / personality", "core/soul_engine.py"),
    ("LLM client", "llm_client.py"),
    ("Intent routing", "core/intent_router.py"),
    ("Skill registry", "core/skill_registry.py"),
    # Business
    ("Booking monitor", "tools/rumahlabuh_crew.py"),
    ("Website uptime check", "tools/rumahlabuh_crew.py"),
    ("Business summary", "tools/rumahlabuh_crew.py"),
    # Intelligence
    ("Self-upgrade engine", "core/self_upgrade.py"),
    ("Web search", "skills/web_search.py"),
    ("Geo intelligence", "skills/geo_intelligence.py"),
    # Memory
    ("Memory engine", "core/memory_engine.py"),
    ("Episodic store", "core/memory/episodic_store.py"),
    ("User profile", "core/memory/user_profile.py"),
    # Tools
    ("GitHub intel", "tools/github_intel.py"),
    ("Email client", "tools/email_client.py"),
    ("Browser agent", "tools/browser_agent.py"),
]

from core.utils.datetime_utils import jst_now as _jst_now  # noqa: E402


class CapabilityAudit:
    """Monthly self-audit of available capabilities."""

    def __init__(self, bot_root: Path = Path(".")) -> None:
        self.root = bot_root.resolve()
        self._notify_cb: Any | None = None

    def set_notify(self, cb: Any) -> None:
        """Set a notify callback (async fn that takes HTML str)."""
        self._notify_cb = cb

    async def run_audit(self) -> dict[str, Any]:
        """
        Run the capability audit.

        Returns:
            dict with keys: timestamp, capabilities (list), gaps (list),
            coverage_pct, report_html
        """
        now = _jst_now()
        timestamp = now.strftime("%Y-%m-%d %H:%M JST")

        present: list[tuple[str, str]] = []
        missing: list[tuple[str, str]] = []

        for capability, file_path in _CAPABILITY_BENCHMARK:
            full = self.root / file_path
            if full.exists():
                present.append((capability, file_path))
            else:
                missing.append((capability, file_path))

        coverage_pct = round(len(present) / len(_CAPABILITY_BENCHMARK) * 100, 1)

        report_lines: list[str] = [
            "🛡️ <b>Legion Capability Audit</b>",
            f"📅 {timestamp}",
            f"📊 Coverage: <b>{coverage_pct}%</b> ({len(present)}/{len(_CAPABILITY_BENCHMARK)})",
            "",
            "✅ <b>Present</b>",
        ]
        for capability, path in present:
            report_lines.append(f"  ✅ {capability} — <code>{path}</code>")

        if missing:
            report_lines.extend(["", "⚠️ <b>Missing / Not Found</b>"])
            for capability, path in missing:
                report_lines.append(f"  ❌ {capability} — <code>{path}</code>")

        # LLM-generated gap analysis
        if missing:
            gap_summary = await self._llm_gap_summary(missing)
            if gap_summary:
                report_lines.extend(["", "🔍 <b>Gap Analysis</b>", gap_summary])

        report_lines.extend(
            [
                "",
                "<i>Run /audit for full deep-scan with test coverage.</i>",
            ]
        )

        report_html = "\n".join(report_lines)

        result: dict[str, Any] = {
            "timestamp": timestamp,
            "present": present,
            "missing": missing,
            "coverage_pct": coverage_pct,
            "report_html": report_html,
        }

        if self._notify_cb and callable(self._notify_cb):
            try:
                await self._notify_cb(report_html)  # type: ignore[reportGeneralTypeIssues]
            except Exception as e:
                logger.warning("[CapabilityAudit] notify failed: %s", e)

        logger.info(
            "[CapabilityAudit] Audit complete — %s/%s present (%.1f%% coverage)",
            len(present),
            len(_CAPABILITY_BENCHMARK),
            coverage_pct,
        )
        return result

    async def _llm_gap_summary(self, missing: list[tuple[str, str]]) -> str:
        """Use LLM to generate actionable summary of missing capabilities."""
        try:
            from llm_client import call_llm
        except ImportError:
            return ""

        capability_names = ", ".join(m[0] for m in missing)
        prompt = (
            f"You are Legion, a personal AI assistant running on Linux/Python/aiogram.\n"
            f"These capabilities are missing from your codebase:\n{capability_names}\n\n"
            "For each, give a 1-sentence recommendation: whether to build it now,\n"
            "defer, or find an existing open-source library.\n"
            "Keep it concise. Reply in Telegram HTML format (bullet points).\n"
        )
        try:
            content = await call_llm(
                messages=[{"role": "user", "content": prompt}],
                model=os.getenv("DEFAULT_MODEL", "opencode-go/minimax-m3"),
                temperature=0.3,
                max_tokens=512,
            )
            if isinstance(content, dict):
                return ""
            return content.strip()
        except Exception as e:
            logger.warning("[CapabilityAudit] LLM gap summary failed: %s", e)
            return ""
