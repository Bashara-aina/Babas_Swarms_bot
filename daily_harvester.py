#!/usr/bin/env python3
"""daily_harvester.py — CLI entry point for the Legion Daily Intelligence Harvester.

Usage:
    python daily_harvester.py              # Run full pipeline
    python daily_harvester.py --dry-run   # Test without LLM calls
    python daily_harvester.py --date 2026-04-11  # Override date
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_daily_harvest(dry_run: bool = False, date_override: str | None = None) -> None:
    """Run the daily harvest pipeline."""
    from core.daily_harvester import DailyHarvester

    date_str = date_override or datetime.utcnow().strftime("%Y-%m-%d")
    logger.info("Starting daily harvest for %s (dry_run=%s)", date_str, dry_run)

    if dry_run:
        logger.info("[DRY RUN] Skipping LLM calls — pipeline steps only")
        # Just test the pipeline structure without LLM calls
        from core.daily_harvester.topic_budget import detect_active_topics
        from core.daily_harvester.wiki_storage import WikiStorage

        budget = await detect_active_topics()
        ws = WikiStorage()
        await ws.append_harvest_log(0, 0, date_str)
        logger.info("[DRY RUN] Topic budget: %s", budget)
        logger.info("[DRY RUN] Pipeline structure OK")
        return

    harvester = DailyHarvester()
    result = await harvester.run()
    logger.info("Harvest complete: %s", result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Legion Daily Intelligence Harvester")
    parser.add_argument("--run-now", action="store_true", help="Trigger immediate run")
    parser.add_argument("--dry-run", action="store_true", help="Test without LLM calls")
    parser.add_argument("--date", type=str, help="Date override (YYYY-MM-DD)")
    args = parser.parse_args()

    asyncio.run(run_daily_harvest(dry_run=args.dry_run, date_override=args.date))


if __name__ == "__main__":
    main()
