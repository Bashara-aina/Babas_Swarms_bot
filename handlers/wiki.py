"""Wiki audit commands: /wiki_audit /wiki_flush /wiki_restore /wiki_scan /wiki_stats."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed

logger = logging.getLogger(__name__)

router = Router()


# ── Auth helper ────────────────────────────────────────────────────────────────


def _auth(message: Message) -> bool:
    """Check if the message is from the allowed user."""
    return is_allowed(message)


# ── /wiki_audit ────────────────────────────────────────────────────────────────


@router.message(Command("wiki_audit"))
async def cmd_wiki_audit(message: Message) -> None:
    """Full quality report — runs weekly deep evaluation and sends the report."""
    if not _auth(message):
        return

    await message.answer("🔍 Starting full wiki deep evaluation (this may take a few minutes)...")

    try:
        from core.wiki_scheduler import WikiQualityScheduler

        scheduler = WikiQualityScheduler()

        # Run the weekly deep scan (same logic as scheduled)
        await scheduler._weekly_deep_scan()

        # Read and send the quality report
        from core.wiki_scheduler import QUALITY_REPORT_PATH

        if QUALITY_REPORT_PATH.exists():
            report = await asyncio.to_thread(lambda: QUALITY_REPORT_PATH.read_text())
            # Send in chunks if too long
            for i in range(0, len(report), 4000):
                await message.answer(report[i : i + 4000])
        else:
            await message.answer("⚠️ Quality report was not generated.")

    except Exception as e:
        logger.warning("wiki_audit failed: %s", e)
        await message.answer(f"❌ Wiki audit failed: {e}")


# ── /wiki_flush ─────────────────────────────────────────────────────────────────


@router.message(Command("wiki_flush"))
async def cmd_wiki_flush(message: Message) -> None:
    """Empty quarantine — delete all quarantined files permanently."""
    if not _auth(message):
        return

    await message.answer("🗑️ Flushing all quarantined wiki files...")

    try:
        from core.wiki_quality_gate import flush_quarantine

        count = await flush_quarantine()
        await message.answer(f"✅ Flushed {count} quarantined file(s).")

    except Exception as e:
        logger.warning("wiki_flush failed: %s", e)
        await message.answer(f"❌ Wiki flush failed: {e}")


# ── /wiki_restore ───────────────────────────────────────────────────────────────


@router.message(Command("wiki_restore"))
async def cmd_wiki_restore(message: Message) -> None:
    """Restore from quarantine — moves back, strips frontmatter, re-evaluates quality."""
    if not _auth(message):
        return

    # Expect user to reply with the page_path or we'll scan quarantine list
    try:
        from core.wiki_scheduler import QUARANTINE_DIR

        if not QUARANTINE_DIR.exists():
            await message.answer("✅ Quarantine is already empty.")
            return

        files = list(QUARANTINE_DIR.glob("*.md"))
        if not files:
            await message.answer("✅ Quarantine is already empty.")
            return

        # List quarantined files for user to choose from
        lines = ["<b>📦 Quarantined Files</b>\nSelect a file to restore by page_path:\n"]
        for f in files[:20]:
            lines.append(f"  • <code>{f.stem[:60]}</code>")
        if len(files) > 20:
            lines.append(f"\n...and {len(files) - 20} more. Flush to delete all.")

        lines.append("\n<i>Reply with the filename (or /wiki_flush to delete all)</i>")
        await message.answer("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.warning("wiki_restore list failed: %s", e)
        await message.answer(f"❌ Failed to list quarantine: {e}")


# ── /wiki_scan ──────────────────────────────────────────────────────────────────


@router.message(Command("wiki_scan"))
async def cmd_wiki_scan(message: Message) -> None:
    """On-demand quick scan NOW — fast heuristic only, no LLM."""
    if not _auth(message):
        return

    await message.answer("⚡ Running on-demand wiki quick scan...")

    try:
        from core.wiki_quality_gate import fast_gate
        from core.wiki_scheduler import WIKI_DIR

        if not WIKI_DIR.exists():
            await message.answer("⚠️ Wiki directory not found.")
            return

        results: list[tuple[str, float, str]] = []
        scanned = 0

        for page_path in _walk_wiki_pages():
            try:
                content = await asyncio.to_thread(lambda: Path(page_path).read_text)
                content_str = content if isinstance(content, str) else content()
                result = fast_gate(content_str, page_path)
                scanned += 1
                results.append((page_path, result.score, result.verdict))
            except Exception as e:
                logger.warning("fast_gate failed for %s: %s", page_path, e)

        if not results:
            await message.answer("No pages found to scan.")
            return

        avg_score = sum(r[1] for r in results) / len(results)
        low = [r for r in results if r[1] < 0.3]
        needs_work = [r for r in results if 0.3 <= r[1] < 0.7]
        good = [r for r in results if r[1] >= 0.7]

        lines = [
            f"⚡ <b>Wiki Quick Scan</b>\n\nScanned: {scanned} pages\nAvg score: {avg_score:.3f}\n",
            f"✅ Good (≥0.7): {len(good)}",
            f"⚠️ Needs work (0.3–0.7): {len(needs_work)}",
            f"❌ Low (<0.3): {len(low)}",
        ]

        if low:
            lines.append("\n<b>Low quality pages:</b>")
            for page, score, verdict in sorted(low, key=lambda x: x[1])[:5]:
                lines.append(f"  • {Path(page).name} ({score:.3f})")

        await message.answer("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.warning("wiki_scan failed: %s", e)
        await message.answer(f"❌ Wiki scan failed: {e}")


# ── /wiki_stats ─────────────────────────────────────────────────────────────────


@router.message(Command("wiki_stats"))
async def cmd_wiki_stats(message: Message) -> None:
    """Quality statistics — page count and avg score by directory."""
    if not _auth(message):
        return

    try:
        from core.wiki_quality_gate import fast_gate
        from core.wiki_scheduler import WIKI_DIR

        if not WIKI_DIR.exists():
            await message.answer("⚠️ Wiki directory not found.")
            return

        # Collect stats by directory
        dir_stats: dict[str, dict[str, int | float]] = {}
        scanned = 0

        for page_path in _walk_wiki_pages():
            try:
                content = await asyncio.to_thread(lambda: Path(page_path).read_text)
                content_str = content if isinstance(content, str) else content()
                result = fast_gate(content_str, page_path)
                scanned += 1

                rel = Path(page_path).relative_to(WIKI_DIR)
                parent = str(rel.parent) if rel.parent != Path(".") else "."

                if parent not in dir_stats:
                    dir_stats[parent] = {"count": 0, "total_score": 0.0}
                dir_stats[parent]["count"] += 1
                dir_stats[parent]["total_score"] += result.score
            except Exception as e:
                logger.warning("fast_gate failed for %s: %s", page_path, e)

        if not dir_stats:
            await message.answer("No pages found.")
            return

        # Build response
        lines = [f"📊 <b>Wiki Quality Stats</b>\n\nTotal pages: {scanned}\n"]
        lines.append("| Directory | Pages | Avg Score |")
        lines.append("|-----------|-------|-----------|")

        for directory, stats in sorted(dir_stats.items()):
            avg = stats["total_score"] / stats["count"]
            dir_label = directory if directory != "." else "(root)"
            score_bar = "🟢" if avg >= 0.7 else "🟡" if avg >= 0.3 else "🔴"
            lines.append(f"{score_bar} {dir_label} | {stats['count']} | {avg:.3f}")

        await message.answer("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.warning("wiki_stats failed: %s", e)
        await message.answer(f"❌ Wiki stats failed: {e}")


# ── Helpers ────────────────────────────────────────────────────────────────────


def _walk_wiki_pages() -> list[str]:
    """Walk .wiki/**/*.md, skipping _quarantine, _archive, index.md."""
    from core.wiki_scheduler import WIKI_DIR

    skip_dirs = {"_quarantine", "_archive"}
    skip_files = {"index.md"}

    if not WIKI_DIR.exists():
        return []

    pages: list[str] = []
    for md_file in WIKI_DIR.rglob("*.md"):
        if any(part in skip_dirs for part in md_file.parts):
            continue
        if md_file.name in skip_files:
            continue
        if md_file.stat().st_size < 50:
            continue
        pages.append(str(md_file))

    return pages
