"""handlers/harvest_review.py — /harvest-review command for Legion.

Shows top pending candidates from the daily harvester and allows
one-tap accept/reject feedback. Feedback is written immediately to
.wiki/legion/harvester/harvest-log.md and updates the scoring bias.
"""

from __future__ import annotations

import html
import logging
import os
from typing import Any

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .shared import is_allowed

logger = logging.getLogger(__name__)
router = Router()

REASON_OPTIONS = [
    ("topic_drift", "Topic drift"),
    ("low_quality", "Low quality"),
    ("duplicate", "Duplicate"),
    ("not_relevant", "Not relevant"),
    ("outdated", "Outdated"),
    ("unreliable_source", "Bad source"),
]


def _build_candidate_card(c: dict[str, Any], index: int) -> str:
    """Build a compact Telegram HTML card for one candidate."""
    title = html.escape(c.get("title", "Untitled")[:80])
    url = c.get("url", "")
    score = c.get("relevance_score", c.get("score", 0.5))
    topic = html.escape(c.get("topic", "unknown"))
    tags = c.get("tags", [])
    tags_str = " ".join(f"#{t}" for t in tags[:4]) if tags else ""
    return (
        f"<b>{index}. {title}</b>\n"
        f"🔗 {url[:70]}…\n"
        f"📊 score=<code>{score:.2f}</code> | topic={topic} {tags_str}"
    )


def _build_review_keyboard(candidate_id: str, index: int) -> InlineKeyboardMarkup:
    """Build accept/reject/skip/reason picker keyboard for one candidate."""
    rows = [
        [
            InlineKeyboardButton(
                text="✅ Accept",
                callback_data=f"hr_acp_{candidate_id}",
            ),
            InlineKeyboardButton(
                text="❌ Reject",
                callback_data=f"hr_rej_{candidate_id}",
            ),
            InlineKeyboardButton(
                text="⏭ Skip",
                callback_data=f"hr_skp_{candidate_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="topic_drift",
                callback_data=f"hr_rsn_topic_drift_{candidate_id}",
            ),
            InlineKeyboardButton(
                text="low_quality",
                callback_data=f"hr_rsn_low_quality_{candidate_id}",
            ),
            InlineKeyboardButton(
                text="not_relevant",
                callback_data=f"hr_rsn_not_relevant_{candidate_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="duplicate",
                callback_data=f"hr_rsn_duplicate_{candidate_id}",
            ),
            InlineKeyboardButton(
                text="outdated",
                callback_data=f"hr_rsn_outdated_{candidate_id}",
            ),
            InlineKeyboardButton(
                text="bad_source",
                callback_data=f"hr_rsn_unreliable_source_{candidate_id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _get_pending_candidates() -> list[dict[str, Any]]:
    """Load pending candidates from data/harvest/pending_candidates.jsonl."""
    import json
    from pathlib import Path

    pending_file = Path(__file__).resolve().parent.parent.parent / "data" / "harvest" / "pending_candidates.jsonl"
    if not pending_file.exists():
        return []
    candidates: list[dict[str, Any]] = []
    with open(pending_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    candidates.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return [c for c in candidates if not c.get("reviewed", False)]


async def _mark_reviewed(
    candidate_id: str,
    decision: str,
    reason: str,
) -> bool:
    """Mark a candidate as reviewed in pending_candidates.jsonl."""
    import json
    from pathlib import Path

    pending_file = Path(__file__).resolve().parent.parent.parent / "data" / "harvest" / "pending_candidates.jsonl"
    if not pending_file.exists():
        return False

    pending = []
    found = False
    with open(pending_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            if c.get("candidate_id") == candidate_id:
                c["decision"] = decision
                c["reason"] = reason
                c["reviewed"] = True
                found = True
            pending.append(c)

    if found:
        with open(pending_file, encoding="utf-8", mode="w") as f:
            for c in pending:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")

    return found


async def _load_harvest_stats() -> dict[str, Any]:
    """Compute harvest statistics from the harvest log."""
    import re
    from datetime import datetime, timezone, timedelta

    wiki_root = Path(__file__).resolve().parent.parent.parent / ".wiki" / "legion" / "harvester"
    log_file = wiki_root / "harvest-log.md"
    if not log_file.exists():
        return {"total": 0, "by_source": {}, "top_reasons": [], "bias": {}}

    try:
        content = log_file.read_text(encoding="utf-8")
    except OSError:
        return {"total": 0, "by_source": {}, "top_reasons": [], "bias": {}}

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    total = 0
    accepted = 0
    rejected = 0
    by_source: dict[str, dict[str, int]] = {}
    reason_counts: dict[str, int] = {}

    json_blocks = re.findall(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    for block in json_blocks:
        block = block.strip()
        if not block:
            continue
        try:
            entry = json.loads(block)
        except json.JSONDecodeError:
            continue

        entry_date_str = entry.get("date", "")
        try:
            entry_date = datetime.fromisoformat(entry_date_str).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        if entry_date < cutoff:
            continue

        for candidate in entry.get("candidates_reviewed", []):
            total += 1
            decision = candidate.get("decision", "")
            source = candidate.get("source", "unknown")
            reason = candidate.get("reason", "unknown")

            # Normalize source label
            if "arxiv" in source:
                src_label = "arxiv"
            elif "github" in source:
                src_label = "github"
            else:
                src_label = "web"

            if src_label not in by_source:
                by_source[src_label] = {"accepted": 0, "rejected": 0}

            if decision == "accepted":
                accepted += 1
                by_source[src_label]["accepted"] += 1
            elif decision == "rejected":
                rejected += 1
                by_source[src_label]["rejected"] += 1
                if reason:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1

    top_reasons = sorted(reason_counts.items(), key=lambda x: -x[1])[:5]

    # Load current bias
    from core.daily_harvester.scorer import Scorer

    scorer = Scorer()
    bias = scorer.get_bias()

    return {
        "total": total,
        "accepted": accepted,
        "rejected": rejected,
        "by_source": by_source,
        "top_reasons": top_reasons,
        "bias": bias,
    }


@router.message(Command("harvest_stats"))
async def cmd_harvest_stats(message: Message) -> None:
    """Show harvest quality statistics."""
    if not is_allowed(message):
        return

    stats = await _load_harvest_stats()
    total = stats["total"]

    if total == 0:
        await message.answer(
            "📊 <b>Harvest Stats</b>\n\nNo harvest review data in the last 30 days.\n"
            "Run /harvest_review after a daily harvest cycle to start collecting feedback.",
            parse_mode="HTML",
        )
        return

    accepted = stats["accepted"]
    rejected = stats["rejected"]
    acceptance_rate = (accepted / total * 100) if total > 0 else 0

    lines = [
        f"📊 <b>Harvest Stats</b> (last 30 days)\n",
        f"Total reviewed: {total} | ✅ {accepted} | ❌ {rejected} | "
        f"Accept rate: <b>{acceptance_rate:.0f}%</b>\n",
        "<b>By source:</b>",
    ]

    for src, counts in stats["by_source"].items():
        src_total = counts["accepted"] + counts["rejected"]
        src_rate = (counts["accepted"] / src_total * 100) if src_total > 0 else 0
        lines.append(f"  {src}: {src_total} reviewed, {src_rate:.0f}% accept")

    if stats["top_reasons"]:
        lines.append("\n<b>Top rejection reasons:</b>")
        for reason, count in stats["top_reasons"]:
            lines.append(f"  <code>{reason}</code>: {count}")

    lines.append("\n<b>Current scorer bias:</b>")
    bias = stats["bias"]
    active_bias = {k: v for k, v in sorted(bias.items(), key=lambda x: -abs(x[1]))[:8] if abs(v) >= 0.01}
    if active_bias:
        for k, v in active_bias.items():
            arrow = "▲" if v > 0 else "▼"
            lines.append(f"  {arrow} <code>{k}</code>: {v:+.2f}")
    else:
        lines.append("  (no active bias adjustments)")

    await message.answer("\n".join(lines), parse_mode="HTML")


async def _write_feedback_to_log(
    candidate: dict[str, Any],
    decision: str,
    reason: str,
) -> None:
    """Append feedback entry to the harvest-log.md."""
    import json
    from datetime import datetime, timezone
    from pathlib import Path

    wiki_root = Path(__file__).resolve().parent.parent.parent / ".wiki" / "legion" / "harvester"
    wiki_root.mkdir(parents=True, exist_ok=True)
    log_file = wiki_root / "harvest-log.md"

    now = datetime.now(timezone.utc)
    session_id = now.strftime("%Y%m%d%H%M%S")

    entry = {
        "date": now.strftime("%Y-%m-%d"),
        "session_id": session_id,
        "candidates_reviewed": [
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "source": candidate.get("source", ""),
                "title": candidate.get("title", ""),
                "url": candidate.get("url", ""),
                "score": candidate.get("relevance_score", 0.5),
                "decision": decision,
                "reason": reason,
                "reason_detail": "",
                "tags": candidate.get("tags", []),
            }
        ],
        "metadata": {
            "candidates_found": 1,
            "candidates_reviewed": 1,
            "pending": 0,
            "review_mode": "telegram",
        },
    }

    with open(log_file, encoding="utf-8", mode="a") as f:
        f.write(f"---\n")
        f.write(f"title: harvest-review-{session_id}\n")
        f.write("type: timeline\n")
        f.write("status: active\n")
        f.write("tags: [legion, harvester, harvest-review]\n")
        f.write(f"created: {now.strftime('%Y-%m-%d')}\n")
        f.write(f"updated: {now.strftime('%Y-%m-%d')}\n")
        f.write(f"summary: Telegram review — {decision} / {reason}\n")
        f.write("wikilinks: []\n")
        f.write("confidence: high\n")
        f.write("source: telegram-review\n")
        f.write("---\n\n")
        f.write(f"# Harvest Review Session\n\n")
        f.write(f"**Date**: {now.strftime('%Y-%m-%d %H:%M')} UTC\n")
        f.write(f"**Decision**: <b>{decision.upper()}</b> | **Reason**: <code>{reason}</code>\n\n")
        f.write("```json\n")
        f.write(json.dumps(entry, indent=2, ensure_ascii=False))
        f.write("\n```\n\n")


async def _update_scorer_bias(decision: str, reason: str) -> None:
    """Trigger scorer bias update from a single feedback entry."""
    try:
        from core.daily_harvester.scorer import Scorer

        scorer = Scorer()
        await scorer.update_from_feedback([{"decision": decision, "reason": reason}])
    except Exception as e:
        logger.warning("Could not update scorer bias: %s", e)


@router.message(Command("harvest_review"))
async def cmd_harvest_review(message: Message) -> None:
    """Show pending harvest candidates for review."""
    if not is_allowed(message):
        return

    pending = await _get_pending_candidates()

    if not pending:
        await message.answer(
            "📭 <b>No pending harvest candidates.</b>\n"
            "Run /harvest-review after the next daily harvest cycle.",
            parse_mode="HTML",
        )
        return

    # Show top 5
    shown = pending[:5]
    remaining = len(pending) - len(shown)

    header = (
        f"🔍 <b>Harvest Review</b> — {len(pending)} pending\n"
        f"Showing top {len(shown)}"
        + (f" ({remaining} more)" if remaining else "")
        + "\n"
        "One-tap feedback closes the loop → better candidates next time.\n"
    )
    await message.answer(header, parse_mode="HTML")

    for i, c in enumerate(shown, 1):
        card = _build_candidate_card(c, i)
        keyboard = _build_review_keyboard(c["candidate_id"], i)
        await message.answer(card, parse_mode="HTML", reply_markup=keyboard)


# ---------------------------------------------------------------------------
# Callback handlers
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith("hr_acp_"))
async def cb_accept(call: CallbackQuery) -> None:
    """Handle accept callback."""
    if not is_allowed(call.message):
        await call.answer("Unauthorized.", show_alert=True)
        return

    candidate_id = call.data[7:]  # strip "hr_acp_"
    pending = await _get_pending_candidates()
    candidate = next((c for c in pending if c.get("candidate_id") == candidate_id), None)

    if not candidate:
        await call.answer("Candidate not found — may have already been reviewed.", show_alert=True)
        return

    await _mark_reviewed(candidate_id, "accepted", "accepted")
    await _write_feedback_to_log(candidate, "accepted", "accepted")
    await _update_scorer_bias("accepted", "accepted")

    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        f"✅ <b>Accepted:</b> {html.escape(candidate.get('title', 'Untitled')[:60])}",
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("hr_rej_"))
async def cb_reject(call: CallbackQuery) -> None:
    """Handle reject callback — prompt for reason via reason picker."""
    if not is_allowed(call.message):
        await call.answer("Unauthorized.", show_alert=True)
        return

    candidate_id = call.data[7:]  # strip "hr_rej_"
    pending = await _get_pending_candidates()
    candidate = next((c for c in pending if c.get("candidate_id") == candidate_id), None)

    if not candidate:
        await call.answer("Candidate not found.", show_alert=True)
        return

    await _mark_reviewed(candidate_id, "rejected", "low_quality")
    await _write_feedback_to_log(candidate, "rejected", "low_quality")
    await _update_scorer_bias("rejected", "low_quality")

    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        f"❌ <b>Rejected:</b> {html.escape(candidate.get('title', 'Untitled')[:60])}",
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("hr_skp_"))
async def cb_skip(call: CallbackQuery) -> None:
    """Handle skip callback."""
    if not is_allowed(call.message):
        await call.answer("Unauthorized.", show_alert=True)
        return

    candidate_id = call.data[7:]  # strip "hr_skp_"
    pending = await _get_pending_candidates()
    candidate = next((c for c in pending if c.get("candidate_id") == candidate_id), None)

    if candidate:
        await _mark_reviewed(candidate_id, "skipped", "skipped")
        await _write_feedback_to_log(candidate, "skipped", "skipped")

    await call.message.edit_reply_markup(reply_markup=None)
    if candidate:
        await call.message.answer(
            f"⏭ <b>Skipped:</b> {html.escape(candidate.get('title', 'Untitled')[:60])}",
            parse_mode="HTML",
        )
    await call.answer()


@router.callback_query(F.data.startswith("hr_rsn_"))
async def cb_reason(call: CallbackQuery) -> None:
    """Handle reason tag picker — extract reason + candidate_id from callback data."""
    if not is_allowed(call.message):
        await call.answer("Unauthorized.", show_alert=True)
        return

    # Format: hr_rsn_<reason>_<candidate_id>
    parts = call.data.split("_", 3)  # ["hr", "rsn", "reason", "candidate_id"]
    if len(parts) < 4:
        await call.answer("Invalid callback data.", show_alert=True)
        return

    reason = parts[2]
    candidate_id = parts[3]

    pending = await _get_pending_candidates()
    candidate = next((c for c in pending if c.get("candidate_id") == candidate_id), None)

    if candidate:
        await _mark_reviewed(candidate_id, "rejected", reason)
        await _write_feedback_to_log(candidate, "rejected", reason)
        await _update_scorer_bias("rejected", reason)

    await call.message.edit_reply_markup(reply_markup=None)
    if candidate:
        await call.message.answer(
            f"❌ <b>Rejected</b> (<code>{reason}</code>): {html.escape(candidate.get('title', 'Untitled')[:60])}",
            parse_mode="HTML",
        )
    await call.answer()
