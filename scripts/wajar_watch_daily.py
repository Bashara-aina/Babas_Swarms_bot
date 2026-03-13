#!/usr/bin/env python3
"""WAJAR_WATCH daily pipeline entry point.

Called by GitHub Actions at 23:00 UTC (06:00 WIB).
Can also be triggered manually: python scripts/wajar_watch_daily.py
Or via Telegram: /wajar_check
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path (for running from scripts/ or CI)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


async def main():
    os.makedirs("logs", exist_ok=True)
    from tools.wajar_watch.orchestrator import run_wajar_watch_pipeline

    run_id = f"cron-{datetime.utcnow():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    print(f"[WAJAR_WATCH] run_id={run_id}")

    result = await run_wajar_watch_pipeline(run_id=run_id, trigger="cron")

    print(
        f"[WAJAR_WATCH] done | changes={result.changes_detected} "
        f"auto={result.auto_applied} alert={result.alerted_human} "
        f"errors={len(result.errors)}"
    )
    if result.errors:
        for e in result.errors:
            print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1 if result.errors else 0)


if __name__ == "__main__":
    asyncio.run(main())
