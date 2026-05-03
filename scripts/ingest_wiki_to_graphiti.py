#!/usr/bin/env python3
"""
Phase 4: Ingest wiki history into Graphiti temporal knowledge graph.

Reads session logs from .wiki/logs/ and adds them to Graphiti
with correct timestamps for temporal queries.

Usage:
    python3 scripts/ingest_wiki_to_graphiti.py
    python3 scripts/ingest_wiki_to_graphiti.py --days 30  # only last 30 days
"""

import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("LEGION_GRAPHITI_ENABLED", "true")

from core.integrations.graphiti_integration import add_episode

LOGS_DIR = Path(__file__).parent.parent / ".wiki" / "logs"


def parse_session_log(log_path: Path) -> list[dict]:
    """Parse a session log file and extract episodes."""
    episodes = []

    try:
        content = log_path.read_text()
    except Exception as e:
        print(f"  ERROR reading {log_path}: {e}")
        return episodes

    header_pattern = re.compile(r"## \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2} JST)\] (\S+) \| (.*)")
    lines = content.split("\n")

    current_episode = None

    for line in lines:
        header_match = header_pattern.match(line)
        if header_match:
            if current_episode:
                episodes.append(current_episode)

            timestamp_str, agent, meta = header_match.groups()
            try:
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M JST")
                dt = dt.replace(year=2026)
            except ValueError:
                dt = datetime.utcnow()

            current_episode = {
                "timestamp": dt,
                "agent": agent,
                "metadata": meta,
                "content": [],
            }
        elif current_episode and line.startswith("- "):
            current_episode["content"].append(line[2:])

    if current_episode:
        episodes.append(current_episode)

    return episodes


async def ingest_log_file(log_path: Path) -> int:
    """Ingest a single log file into Graphiti."""
    episodes = parse_session_log(log_path)
    if not episodes:
        return 0

    count = 0
    for ep in episodes:
        content = "\n".join(ep["content"])[:2000]
        if not content.strip():
            continue

        result = await add_episode(
            content=f"[{ep['agent']}] {ep['metadata']}\n{content}",
            agent=ep["agent"],
            task=f"wiki_ingest:{log_path.name}",
            reference_time=ep["timestamp"],
        )
        if result:
            count += 1

    return count


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Ingest wiki logs into Graphiti")
    parser.add_argument("--days", type=int, default=90, help="Ingest logs from last N days")
    args = parser.parse_args()

    print(f"Graphiti Wiki Ingest — last {args.days} days")
    print("=" * 50)

    if not LOGS_DIR.exists():
        print(f"ERROR: {LOGS_DIR} does not exist")
        return 1

    log_files = sorted(LOGS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    print(f"Found {len(log_files)} log files")

    cutoff = datetime.now().timestamp() - (args.days * 86400)
    log_files = [f for f in log_files if f.stat().st_mtime > cutoff]
    print(f"Processing {len(log_files)} files from last {args.days} days")

    total_episodes = 0
    for log_file in log_files:
        count = await ingest_log_file(log_file)
        if count > 0:
            print(f"  {log_file.name}: {count} episodes")
            total_episodes += count

    print(f"\nIngest complete: {total_episodes} episodes added")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
