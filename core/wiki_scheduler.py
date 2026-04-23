"""Background asyncio scheduler for wiki quality enforcement."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Coroutine

import pytz

logger = logging.getLogger(__name__)

# ── Schedule constants ────────────────────────────────────────────────────────

DAILY_HOUR = 1  # 1 AM JST (UTC-9 → 10:00 UTC)
WEEKLY_DAY = 6  # Sunday in Python weekday()
DEEP_SCAN_HOUR = 2  # 2 AM JST

# Quality thresholds
LOW_QUALITY_THRESHOLD = 0.3  # quarantine below this score on daily scan

# Rate limiting for LLM calls
LLM_CALL_DELAY = 1.0  # seconds between deep_gate calls

# Paths
WIKI_DIR = Path("/home/newadmin/swarm-bot/.wiki")
QUARANTINE_DIR = WIKI_DIR / "_archive" / "_quarantine"
QUALITY_REPORT_PATH = WIKI_DIR / "_quality_report.md"


def _jst_now() -> datetime:
    """Return current time in JST."""
    return datetime.now(pytz.timezone("Asia/Tokyo"))


# ── WikiQualityScheduler ──────────────────────────────────────────────────────


class WikiQualityScheduler:
    """Background asyncio scheduler for wiki quality enforcement.

    Runs two scheduled tasks:
    - Daily fast scan: 1 AM JST — heuristic scan, quarantine <0.3 score
    - Weekly deep scan: Sunday 2 AM JST — full LLM evaluation of all pages
    """

    def __init__(
        self,
        notify_cb: Callable[[str], Coroutine] | None = None,
        telegram_chat_id: int | None = None,
    ) -> None:
        self.notify = notify_cb
        self.chat_id = telegram_chat_id
        self._running = False
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        """Start background asyncio task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "[WikiQualityScheduler] started — daily scan at %d AM JST, weekly deep scan Sunday %d AM JST",
            DAILY_HOUR,
            DEEP_SCAN_HOUR,
        )

    def stop(self) -> None:
        """Stop background task."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("[WikiQualityScheduler] stopped")

    async def _loop(self) -> None:
        """Main scheduler loop — waits for next scheduled time then runs scans."""
        await asyncio.sleep(30)  # Grace period on startup

        while self._running:
            try:
                now = _jst_now()
                next_run = self._next_scheduled_time(now)
                wait_seconds = (next_run - now).total_seconds()
                if wait_seconds > 0:
                    logger.info(
                        "[WikiQualityScheduler] next run in %.1f seconds at %s JST",
                        wait_seconds,
                        next_run.strftime("%Y-%m-%d %H:%M"),
                    )
                    await asyncio.sleep(max(60, wait_seconds))  # re-check at least every minute

                if not self._running:
                    break

                now = _jst_now()
                await self._run_scheduled_tasks(now)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("[WikiQualityScheduler] loop error: %s", e)
                await asyncio.sleep(300)  # 5 min back-off on error

    def _next_scheduled_time(self, now: datetime) -> datetime:
        """Return next scheduled run time (daily or weekly deep scan)."""
        # Daily scan: today at DAILY_HOUR if not yet passed, else tomorrow
        next_daily = now.replace(hour=DAILY_HOUR, minute=0, second=0, microsecond=0)
        if next_daily <= now:
            next_daily = next_daily.replace(day=now.day + 1)

        # Weekly deep scan: next Sunday at DEEP_SCAN_HOUR
        days_until_sunday = (WEEKLY_DAY - now.weekday()) % 7
        if days_until_sunday == 0 and now.replace(hour=DEEP_SCAN_HOUR, minute=0, second=0, microsecond=0) <= now:
            days_until_sunday = 7
        next_weekly = now.replace(hour=DEEP_SCAN_HOUR, minute=0, second=0, microsecond=0)
        next_weekly = next_weekly.replace(day=now.day + days_until_sunday)

        return min(next_daily, next_weekly)

    async def _run_scheduled_tasks(self, now: datetime) -> None:
        """Run any tasks due at the current time."""
        # Daily fast scan at 1 AM JST
        if now.hour == DAILY_HOUR and now.minute < 5:
            await self._daily_scan()
            return

        # Weekly deep scan Sunday at 2 AM JST
        if now.weekday() == WEEKLY_DAY and now.hour == DEEP_SCAN_HOUR and now.minute < 5:
            await self._weekly_deep_scan()

    # ── Daily fast scan ─────────────────────────────────────────────────────────

    async def _daily_scan(self) -> None:
        """Daily fast heuristic scan at 1 AM JST. Quarantines content <0.3 score."""
        logger.info("[WikiQualityScheduler] starting daily fast scan")
        try:
            from core.wiki_quality_gate import fast_gate, quarantine_content

            quarantined: list[tuple[str, str, float]] = []
            scanned = 0

            for page_path in self._walk_wiki_pages():
                try:
                    content = await asyncio.to_thread(lambda: Path(page_path).read_text)
                    content_str = content if isinstance(content, str) else content()
                    result = fast_gate(content_str, page_path)
                    scanned += 1

                    if result.verdict == "REJECT" and result.score < LOW_QUALITY_THRESHOLD:
                        dest = await quarantine_content(
                            page_path=page_path,
                            content=content_str,
                            reason=f"daily_fast_scan: verdict=REJECT, score={result.score:.3f} < {LOW_QUALITY_THRESHOLD}",
                            score=result.score,
                        )
                        quarantined.append((page_path, str(dest), result.score))
                        logger.info("[WikiQualityScheduler] quarantined %s (score=%.3f)", page_path, result.score)
                    elif result.verdict == "NEEDS_IMPROVEMENT" and result.score < 0.1:
                        # Score of 0.0-0.1 is likely a scoring bug (not genuinely bad content)
                        # Route to deep_gate before quarantining — only quarantine if deep_gate agrees
                        from core.wiki_quality_gate import deep_gate

                        deep_result = await deep_gate(content_str, page_path)
                        if deep_result.verdict == "REJECT":
                            dest = await quarantine_content(
                                page_path=page_path,
                                content=content_str,
                                reason=f"daily_fast_scan: deep_gate REJECT, score={deep_result.score:.3f}",
                                score=deep_result.score,
                            )
                            quarantined.append((page_path, str(dest), deep_result.score))
                            logger.info(
                                "[WikiQualityScheduler] quarantined after deep_gate %s (score=%.3f)",
                                page_path,
                                deep_result.score,
                            )

                except Exception as e:
                    logger.warning("[WikiQualityScheduler] failed to scan %s: %s", page_path, e)

            summary = (
                f"🧹 <b>Daily Wiki Scan Complete</b>\n\nScanned: {scanned} pages\nQuarantined: {len(quarantined)}\n\n"
            )
            if quarantined:
                summary += "<b>Quarantined pages:</b>\n"
                for page, dest, score in quarantined[:10]:
                    summary += f"  • {Path(page).name} (score={score:.3f})\n"
                if len(quarantined) > 10:
                    summary += f"  ...and {len(quarantined) - 10} more\n"
            else:
                summary += "All pages above quality threshold ✅"

            logger.info(
                "[WikiQualityScheduler] daily scan complete: scanned=%d, quarantined=%d", scanned, len(quarantined)
            )
            if self.notify:
                await self.notify(summary)

        except Exception as e:
            logger.warning("[WikiQualityScheduler] daily scan failed: %s", e)

    # ── Weekly deep scan ───────────────────────────────────────────────────────

    async def _weekly_deep_scan(self) -> None:
        """Sunday 2 AM JST: Full LLM deep evaluation of all wiki pages."""
        logger.info("[WikiQualityScheduler] starting weekly deep scan")
        try:
            from core.wiki_quality_gate import deep_gate

            results: list[tuple[str, float, str]] = []
            scanned = 0

            for page_path in self._walk_wiki_pages():
                try:
                    content = await asyncio.to_thread(lambda: Path(page_path).read_text)
                    content_str = content if isinstance(content, str) else content()
                    result = await deep_gate(content_str, page_path)
                    scanned += 1
                    results.append((page_path, result.score, result.reason))
                    logger.info(
                        "[WikiQualityScheduler] scored %s: score=%.3f verdict=%s",
                        page_path,
                        result.score,
                        result.verdict,
                    )

                    # Rate limit LLM calls
                    await asyncio.sleep(LLM_CALL_DELAY)

                except Exception as e:
                    logger.warning("[WikiQualityScheduler] failed to deep-scan %s: %s", page_path, e)

            # Build quality report
            report = self._build_quality_report(results)
            await self._write_quality_report(report)

            # Summarize
            avg_score = sum(r[1] for r in results) / max(len(results), 1)
            low_score_pages = [(p, s) for p, s, _ in results if s < LOW_QUALITY_THRESHOLD]
            needs_improvement = [(p, s) for p, s, _ in results if 0.3 <= s < 0.7]

            summary = (
                f"📊 <b>Weekly Wiki Deep Scan Complete</b>\n\n"
                f"Scanned: {scanned} pages\n"
                f"Average score: {avg_score:.3f}\n\n"
                f"Low quality (<{LOW_QUALITY_THRESHOLD}): {len(low_score_pages)}\n"
                f"Needs improvement (0.3–0.7): {len(needs_improvement)}\n"
            )
            if low_score_pages:
                summary += "\n<b>Low quality pages:</b>\n"
                for page, score in low_score_pages[:5]:
                    summary += f"  • {Path(page).name} (score={score:.3f})\n"
                if len(low_score_pages) > 5:
                    summary += f"  ...and {len(low_score_pages) - 5} more\n"

            logger.info(
                "[WikiQualityScheduler] weekly deep scan complete: scanned=%d avg=%.3f low=%d",
                scanned,
                avg_score,
                len(low_score_pages),
            )
            if self.notify:
                await self.notify(summary)

        except Exception as e:
            logger.warning("[WikiQualityScheduler] weekly deep scan failed: %s", e)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _walk_wiki_pages(self) -> list[str]:
        """Walk .wiki/**/*.md, skipping _quarantine, _archive, index.md."""
        skip_dirs = {"_quarantine", "_archive", "_quality_report.md"}
        skip_files = {"index.md"}

        if not WIKI_DIR.exists():
            return []

        pages: list[str] = []
        for md_file in WIKI_DIR.rglob("*.md"):
            # Skip hidden dirs and special dirs
            if any(part in skip_dirs for part in md_file.parts):
                continue
            if md_file.name in skip_files:
                continue
            # Only process actual wiki content (not frontmatter-only files)
            if md_file.stat().st_size < 50:
                continue
            pages.append(str(md_file))

        return pages

    def _build_quality_report(self, results: list[tuple[str, float, str]]) -> str:
        """Build markdown quality report from scan results."""
        lines = [
            "# Wiki Quality Report",
            "",
            f"Generated: {_jst_now().strftime('%Y-%m-%d %H:%M JST')}",
            "",
            "## Summary",
            "",
        ]

        if not results:
            lines.append("No pages scanned.")
            return "\n".join(lines)

        avg_score = sum(r[1] for r in results) / len(results)
        lines.append(f"- Pages scanned: {len(results)}")
        lines.append(f"- Average score: {avg_score:.3f}")

        # Group by score band
        excellent = [(p, s, r) for p, s, r in results if s >= 0.7]
        needs_work = [(p, s, r) for p, s, r in results if 0.3 <= s < 0.7]
        low = [(p, s, r) for p, s, r in results if s < 0.3]

        lines.append(f"- Excellent (≥0.7): {len(excellent)}")
        lines.append(f"- Needs improvement (0.3–0.7): {len(needs_work)}")
        lines.append(f"- Low quality (<0.3): {len(low)}")
        lines.append("")

        # Detail tables
        for label, group in [("Excellent", excellent), ("Needs Improvement", needs_work), ("Low Quality", low)]:
            if not group:
                continue
            lines.append(f"## {label}")
            lines.append("")
            lines.append("| Page | Score | Reason |")
            lines.append("|------|-------|--------|")
            for page, score, reason in sorted(group, key=lambda x: x[1]):
                rel_path = Path(page).relative_to(WIKI_DIR)
                reason_short = reason[:80] + "..." if len(reason) > 80 else reason
                lines.append(f"| {rel_path} | {score:.3f} | {reason_short} |")
            lines.append("")

        return "\n".join(lines)

    async def _write_quality_report(self, report: str) -> None:
        """Write quality report to .wiki/_quality_report.md."""
        try:
            WIKI_DIR.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(lambda: Path(QUALITY_REPORT_PATH).write_text(report))
            logger.info("[WikiQualityScheduler] wrote quality report to %s", QUALITY_REPORT_PATH)
        except Exception as e:
            logger.warning("[WikiQualityScheduler] failed to write quality report: %s", e)
