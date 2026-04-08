#!/usr/bin/env python3
"""CLI: query Screenpipe search API (requires SCREENPIPE_ENABLED=1 and local daemon)."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Ensure project root on path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


async def _run() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("query", nargs="?", default="recent activity")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--hours", type=int, default=24)
    args = p.parse_args()
    os.environ.setdefault("SCREENPIPE_ENABLED", "1")
    from tools.screenpipe_tool import get_screenpipe_tool

    sp = get_screenpipe_tool()
    out = await sp.search(args.query, limit=args.limit, hours_back=args.hours)
    print(out or "(no results or service down)")


if __name__ == "__main__":
    asyncio.run(_run())
