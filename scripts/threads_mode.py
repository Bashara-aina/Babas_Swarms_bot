#!/usr/bin/env python3
"""CLI control for Threads campaign mode.

Usage:
  python scripts/threads_mode.py status
  python scripts/threads_mode.py on
  python scripts/threads_mode.py off
  python scripts/threads_mode.py toggle
  python scripts/threads_mode.py scheduler status
  python scripts/threads_mode.py scheduler generate --date 2026-04-24
  python scripts/threads_mode.py scheduler run --date 2026-04-24
  python scripts/threads_mode.py scheduler windows --date 2026-04-24
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.threads_mode_control import is_enabled, open_workspace, set_enabled, toggle
from tools.rumahlabuh_scheduler import Scheduler, AnalyticsStore


async def _run(action: str, open_browser: bool) -> int:
    if action == "status":
        state = "ON" if await is_enabled() else "OFF"
        print(f"threads_mode={state}")
        return 0

    if action == "toggle":
        enabled = await toggle()
    elif action == "on":
        enabled = True
        await set_enabled(True)
    elif action == "off":
        enabled = False
        await set_enabled(False)
    else:
        print(f"Unknown action: {action}")
        return 2

    state = "ON" if enabled else "OFF"
    print(f"threads_mode={state}")

    if enabled and open_browser:
        result = await open_workspace()
        print(result)
    return 0


async def _scheduler_status() -> int:
    """Show scheduler status."""
    scheduler = Scheduler()
    summary = scheduler.get_analytics_summary()
    print(f"Scheduler Status:")
    print(f"  Scheduled (7d): {summary['total_scheduled_7d']}")
    print(f"  Scored threads: {summary['scored_threads']}")
    print(f"  FYP candidates: {summary['fyp_candidate_count']}")
    print(f"  Last reevaluate: {summary['last_reevaluate'] or 'never'}")
    if summary["top_5_signatures"]:
        print(f"  Top signatures: {summary['top_5_signatures'][:3]}")
    return 0


async def _scheduler_generate(date_iso: str) -> int:
    """Generate schedule for a specific date."""
    scheduler = Scheduler()
    slots = scheduler.schedule_window(date_iso)
    print(f"Generated {len(slots)} slots for {date_iso}:")
    for slot in slots:
        print(
            f"  [{slot['slot_index']}] {slot['window_label']} "
            f"{slot['hour']:02d}:{slot['minute']:02d} — "
            f"post {slot['post_number']}/6 (seed={slot['thread_seed'][:8]})"
        )
    return 0


async def _scheduler_run(date_iso: str) -> int:
    """Run scheduler for a specific date (generate + log analytics)."""
    scheduler = Scheduler()
    slots = scheduler.schedule_window(date_iso)
    print(f"Running scheduler for {date_iso}:")
    print(f"  {len(slots)} slots scheduled")

    for slot in slots:
        result = scheduler.generate_thread_for_slot(slot)
        if result.get("success"):
            print(
                f"  [slot {slot['slot_index']}] "
                f"technique={result.get('technique')} "
                f"pronouns={'/'.join(result.get('pronouns', []))}"
            )
        else:
            print(f"  [slot {slot['slot_index']}] FAILED: {result.get('error', 'unknown')}")

    summary = scheduler.get_analytics_summary()
    print(f"\nAnalytics: {summary['total_scheduled_7d']} scheduled, "
          f"{summary['scored_threads']} scored")
    return 0


async def _scheduler_windows(date_iso: str) -> int:
    """Show scheduler windows for a specific date."""
    scheduler = Scheduler()
    config = scheduler.config

    print(f"Scheduler windows for {date_iso}:")
    print(f"  Total posts/day: {config.total_posts_per_day()}")
    print()

    for window in config.windows:
        window_duration = window.end_hour - window.start_hour
        interval = window_duration / window.post_count if window.post_count > 0 else 0

        print(f"  {window.label} ({window.name}):")
        print(f"    Hours: {window.start_hour:02d}:00 – {window.end_hour:02d}:00")
        print(f"    Posts: {window.post_count}")
        print(f"    Weight: {window.weight}")
        print(f"    Interval: {interval:.1f} hours between posts")
        print()

    # Show slots for this date
    slots = scheduler.schedule_window(date_iso)
    print(f"  Computed slots for {date_iso}:")
    for slot in slots:
        print(
            f"    [{slot['slot_index']}] {slot['window_label']} "
            f"{slot['hour']:02d}:{slot['minute']:02d} — "
            f"post {slot['post_number']}/6"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Toggle Threads campaign mode")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Legacy actions
    subparsers.add_parser("status", help="Show current threads mode status")
    subparsers.add_parser("on", help="Turn threads mode ON")
    subparsers.add_parser("off", help="Turn threads mode OFF")
    subparsers.add_parser("toggle", help="Toggle threads mode")

    # Scheduler subcommand
    scheduler_parser = subparsers.add_parser("scheduler", help="Scheduler commands")
    scheduler_subparsers = scheduler_parser.add_subparsers(
        dest="scheduler_action", help="Scheduler actions"
    )

    # scheduler status
    scheduler_subparsers.add_parser("status", help="Show scheduler status")

    # scheduler generate
    generate_parser = scheduler_subparsers.add_parser(
        "generate", help="Generate schedule for a date"
    )
    generate_parser.add_argument(
        "--date", required=True, help="Date in YYYY-MM-DD format"
    )

    # scheduler run
    run_parser = scheduler_subparsers.add_parser(
        "run", help="Run scheduler for a date"
    )
    run_parser.add_argument(
        "--date", required=True, help="Date in YYYY-MM-DD format"
    )

    # scheduler windows
    windows_parser = scheduler_subparsers.add_parser(
        "windows", help="Show scheduler windows for a date"
    )
    windows_parser.add_argument(
        "--date", required=True, help="Date in YYYY-MM-DD format"
    )

    args = parser.parse_args()

    # Handle scheduler subcommand
    if args.command == "scheduler":
        if args.scheduler_action == "status":
            return asyncio.run(_scheduler_status())
        elif args.scheduler_action == "generate":
            return asyncio.run(_scheduler_generate(args.date))
        elif args.scheduler_action == "run":
            return asyncio.run(_scheduler_run(args.date))
        elif args.scheduler_action == "windows":
            return asyncio.run(_scheduler_windows(args.date))
        else:
            scheduler_parser.print_help()
            return 1

    # Legacy actions (backward compatible)
    if args.command in ("status", "on", "off", "toggle"):
        open_browser = True
        if args.command == "status":
            return asyncio.run(_run("status", open_browser=False))
        elif args.command == "toggle":
            return asyncio.run(_run("toggle", open_browser=False))
        elif args.command == "on":
            return asyncio.run(_run("on", open_browser=False))
        elif args.command == "off":
            return asyncio.run(_run("off", open_browser=False))

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
