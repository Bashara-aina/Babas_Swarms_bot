"""WAJAR_WATCH — orchestrator: main pipeline controller."""
from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot

from tools.wajar_watch.confidence_scorer import ConfidenceResult, score_confidence
from tools.wajar_watch.constants import (
    ROUTE_ALERT_HUMAN,
    ROUTE_ALERT_ONLY,
    ROUTE_AUTO_APPLY,
    ROUTE_BLOCK,
    ROUTE_SKIP,
    WATCHED_CONSTANTS,
)
from tools.wajar_watch.github_pr_writer import merge_pr, open_regulation_pr
from tools.wajar_watch.pdf_extractor import ExtractedConstant, extract_from_pdf
from tools.wajar_watch.regulation_diff import generate_diff
from tools.wajar_watch.scraper import scrape_all_sources
from tools.wajar_watch import supabase_writer
from tools.wajar_watch.telegram_alerter import (
    send_auto_applied_alert,
    send_critical_block_alert,
    send_low_confidence_alert,
    send_needs_approval_alert,
    send_pipeline_summary,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    run_id: str
    started_at: str = ""
    finished_at: str = ""
    trigger: str = "cron"
    sources_checked: int = 0
    changes_detected: int = 0
    auto_applied: int = 0
    alerted_human: int = 0
    blocked: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    pr_urls: list[str] = field(default_factory=list)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _match_candidates_to_watched(
    watched_key: str, candidates: list[ExtractedConstant]
) -> list[ExtractedConstant]:
    """Find candidates relevant to a watched constant key."""
    key_parts = watched_key.replace("_", " ").lower().split()
    relevant = []
    for c in candidates:
        name_lower = c.constant_name.lower().replace("_", " ")
        # Match if any 2+ key parts appear in the constant name
        matches = sum(1 for part in key_parts if part in name_lower)
        if matches >= 2:
            relevant.append(c)
    return relevant


def _extract_pdb_rate(candidates: list[ExtractedConstant]) -> float | None:
    """Try to find PDB growth rate from BPS data in candidates."""
    for c in candidates:
        name = c.constant_name.lower()
        if "pdb" in name or "gdp" in name or "pertumbuhan" in name:
            if c.unit == "rate_decimal" and 0 < c.value < 0.2:
                logger.info("Found PDB growth rate: %.4f from %s", c.value, c.source_url)
                return c.value
    return None


async def run_wajar_watch_pipeline(
    run_id: str | None = None,
    trigger: str = "cron",
    bot: "Bot | None" = None,
    alert_chat_id: int | None = None,
) -> PipelineResult:
    """Full WAJAR_WATCH pipeline.

    Steps:
    1. Log pipeline start
    2. Scrape all sources (parallel)
    3. For each changed source → extract PDFs
    4. Score confidence for each watched constant
    5. Route each change (auto_apply / alert_human / block / skip)
    6. Write results to Supabase
    7. Finalize and return
    """
    if run_id is None:
        run_id = f"{trigger}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"

    if alert_chat_id is None:
        alert_chat_id_str = os.getenv("WAJAR_WATCH_ALERT_CHAT_ID", "")
        alert_chat_id = int(alert_chat_id_str) if alert_chat_id_str else None

    result = PipelineResult(run_id=run_id, started_at=_utcnow_iso(), trigger=trigger)
    logger.info("[WAJAR_WATCH] Pipeline start: %s (trigger=%s)", run_id, trigger)

    # ── STEP 1: Log pipeline start ───────────────────────────────────────────
    try:
        await supabase_writer.start_pipeline_run(run_id, trigger)
    except Exception as e:
        logger.warning("Failed to log pipeline start: %s", e)

    # ── STEP 2: Scrape all sources ───────────────────────────────────────────
    try:
        scraper_results = await scrape_all_sources()
        result.sources_checked = len(scraper_results)
        logger.info("Scraped %d sources", result.sources_checked)
    except Exception as e:
        result.errors.append(f"Scraper fatal: {e}")
        logger.error("Scraper fatal error: %s", e)
        result.finished_at = _utcnow_iso()
        await supabase_writer.finish_pipeline_run(run_id, result)
        return result

    # Log scraper errors
    for sr in scraper_results:
        if sr.error:
            result.errors.append(f"Scraper [{sr.source_id}]: {sr.error}")

    # Check if this is a first run (all sources returned changed=False with old_hash=None)
    first_run = all(not sr.changed and sr.old_hash is None for sr in scraper_results if not sr.error)
    if first_run:
        logger.info("First run — baseline established. No extraction/scoring on day 1.")
        result.finished_at = _utcnow_iso()
        await supabase_writer.finish_pipeline_run(run_id, result)
        if bot and alert_chat_id:
            await send_pipeline_summary(
                bot, alert_chat_id, run_id,
                result.sources_checked, 0, result.errors,
            )
        return result

    # ── STEP 3: Extract from PDFs ────────────────────────────────────────────
    all_candidates: list[ExtractedConstant] = []
    for sr in scraper_results:
        if not sr.changed:
            continue
        for pdf_url in sr.pdf_urls:
            try:
                candidates = await extract_from_pdf(pdf_url)
                all_candidates.extend(candidates)
                logger.info("Extracted %d constants from %s", len(candidates), pdf_url)
            except Exception as e:
                result.errors.append(f"PDF {pdf_url}: {e}")
                logger.error("PDF extraction failed for %s: %s", pdf_url, e)

    if not all_candidates:
        logger.info("No constants extracted from any changed source")
        result.finished_at = _utcnow_iso()
        await supabase_writer.finish_pipeline_run(run_id, result)
        if bot and alert_chat_id:
            await send_pipeline_summary(
                bot, alert_chat_id, run_id,
                result.sources_checked, 0, result.errors,
            )
        return result

    # ── STEP 4: Extract PDB growth rate ──────────────────────────────────────
    pdb_growth_rate = _extract_pdb_rate(all_candidates)

    # ── STEP 5 & 6: Score and route each watched constant ────────────────────
    for watched in WATCHED_CONSTANTS:
        try:
            relevant = _match_candidates_to_watched(watched.key, all_candidates)
            if not relevant:
                continue

            confidence_result = score_confidence(watched, relevant, pdb_growth_rate)

            if confidence_result.routing == ROUTE_SKIP:
                result.skipped += 1
                continue

            result.changes_detected += 1

            # Route the change
            await _route_change(
                watched=watched,
                confidence_result=confidence_result,
                run_id=run_id,
                result=result,
                bot=bot,
                alert_chat_id=alert_chat_id,
            )

        except Exception as e:
            result.errors.append(f"Scoring [{watched.key}]: {e}")
            logger.error("Error scoring %s: %s", watched.key, e)

    # ── STEP 7: Finalize ─────────────────────────────────────────────────────
    result.finished_at = _utcnow_iso()
    await supabase_writer.finish_pipeline_run(run_id, result)

    if bot and alert_chat_id:
        await send_pipeline_summary(
            bot, alert_chat_id, run_id,
            result.sources_checked, result.changes_detected, result.errors,
        )

    logger.info(
        "[WAJAR_WATCH] Pipeline done: changes=%d auto=%d alert=%d block=%d skip=%d errors=%d",
        result.changes_detected, result.auto_applied, result.alerted_human,
        result.blocked, result.skipped, len(result.errors),
    )
    return result


async def _route_change(
    watched,
    confidence_result: ConfidenceResult,
    run_id: str,
    result: PipelineResult,
    bot,
    alert_chat_id: int | None,
) -> None:
    """Route a single confidence result to the appropriate action."""
    source_url = watched.legal_basis_url

    if confidence_result.routing == ROUTE_BLOCK:
        result.blocked += 1
        log_id = await supabase_writer.log_change(
            watched.key, watched.current_value, confidence_result.proposed_value,
            confidence_result, pr_url=None, pr_number=None, run_id=run_id,
        )
        if bot and alert_chat_id and log_id:
            await send_critical_block_alert(
                bot, alert_chat_id, log_id, watched, confidence_result, source_url,
            )

    elif confidence_result.routing == ROUTE_AUTO_APPLY:
        diff = await generate_diff(watched, confidence_result)
        if diff is None:
            result.errors.append(f"Diff generation failed for {watched.key}")
            return

        pr = await open_regulation_pr(diff, confidence_result.confidence)
        if pr.status == "error":
            result.errors.append(f"PR creation failed for {watched.key}: {pr.error}")
            # Safety Rule 3: alert on PR failure
            if bot and alert_chat_id:
                try:
                    await bot.send_message(
                        alert_chat_id,
                        f"⚠️ WAJAR_WATCH: PR creation failed for {watched.key}\n"
                        f"Error: {pr.error}",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            return

        log_id = await supabase_writer.log_change(
            watched.key, watched.current_value, confidence_result.proposed_value,
            confidence_result, pr_url=pr.pr_url, pr_number=pr.pr_number, run_id=run_id,
        )
        result.auto_applied += 1
        result.pr_urls.append(pr.pr_url)

        if bot and alert_chat_id:
            await send_auto_applied_alert(bot, alert_chat_id, watched, confidence_result, pr)

        # Auto-merge if env var allows (Safety Rule 2: default off)
        if os.getenv("WAJAR_WATCH_AUTO_MERGE_ENABLED", "false").lower() == "true":
            await merge_pr(pr.pr_number)
            if log_id:
                await supabase_writer.update_change_status(log_id, "auto_merged")

    elif confidence_result.routing == ROUTE_ALERT_HUMAN:
        diff = await generate_diff(watched, confidence_result)
        pr = None
        if diff:
            pr = await open_regulation_pr(diff, confidence_result.confidence)
            if pr.status == "error":
                result.errors.append(f"PR creation failed for {watched.key}: {pr.error}")
                pr = None

        log_id = await supabase_writer.log_change(
            watched.key, watched.current_value, confidence_result.proposed_value,
            confidence_result,
            pr_url=pr.pr_url if pr else None,
            pr_number=pr.pr_number if pr else None,
            run_id=run_id,
        )
        result.alerted_human += 1

        if bot and alert_chat_id and log_id and pr:
            await send_needs_approval_alert(
                bot, alert_chat_id, log_id, watched, confidence_result, pr,
            )

    elif confidence_result.routing == ROUTE_ALERT_ONLY:
        log_id = await supabase_writer.log_change(
            watched.key, watched.current_value, confidence_result.proposed_value,
            confidence_result, pr_url=None, pr_number=None, run_id=run_id,
        )
        result.alerted_human += 1

        if bot and alert_chat_id and log_id:
            await send_low_confidence_alert(
                bot, alert_chat_id, log_id, watched, confidence_result, source_url,
            )
