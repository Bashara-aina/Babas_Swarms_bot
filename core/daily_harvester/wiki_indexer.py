"""WikiIndexer — build and search the knowledge wiki index."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import aiofiles

from core.daily_harvester.types import WikiEntry

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_ROOT = REPO_ROOT / ".wiki" / "legion" / "harvester"


class WikiIndexer:
    """Build and query the wiki knowledge index."""

    def __init__(self, wiki_root: Path | None = None) -> None:
        self.wiki_root = (wiki_root or WIKI_ROOT).resolve()

    async def build_index(self, topic: str) -> dict[str, Any]:
        """
        Regenerate the INDEX.md for a topic directory.

        Returns a dict with keys: topic, entry_count, entries (list of file_id + title).
        """
        from core.daily_harvester.wiki_storage import _topic_dir

        dir_path = _topic_dir(topic)
        index_path = dir_path / "INDEX.md"

        if not dir_path.exists():
            return {"topic": topic, "entry_count": 0, "entries": []}

        entries: list[dict[str, str]] = []
        for f in sorted(dir_path.glob("*.md")):
            if f.name == "INDEX.md":
                continue
            async with aiofiles.open(f, encoding="utf-8", mode="r") as fh:
                text = await fh.read()
            lines = text.splitlines()
            title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), f.stem)
            preview = " ".join(text.replace("\n", " ").split())[:100]
            entries.append({"file_id": f.stem, "title": title, "preview": preview})

        now = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d")
        lines_out = [
            f"# {dir_path.name.replace('-', ' ').title()} — INDEX",
            "",
            f"_Last updated: {now} by Legion Daily Harvester_",
            "",
            "## Entries",
            "",
        ]
        if entries:
            for e in entries:
                lines_out.append(f"- [[{e['file_id']}]] — {e['title']}: {e['preview']}...")
        else:
            lines_out.append("No entries yet — harvested daily.")

        async with aiofiles.open(index_path, encoding="utf-8", mode="w") as f:
            await f.write("\n".join(lines_out))

        return {"topic": topic, "entry_count": len(entries), "entries": entries}

    async def search_by_topic(self, topic: str) -> list[WikiEntry]:
        """
        Search all wiki entries for a given topic.

        Returns a list of WikiEntry dicts.
        """
        from core.daily_harvester.wiki_storage import _topic_dir

        dir_path = _topic_dir(topic)
        results: list[WikiEntry] = []

        if not dir_path.exists():
            return results

        for f in sorted(dir_path.glob("*.md")):
            if f.name == "INDEX.md":
                continue
            async with aiofiles.open(f, encoding="utf-8", mode="r") as fh:
                text = await fh.read()
            lines = text.splitlines()
            title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), f.stem)

            # Extract tags from content
            tags_match = re.search(r"## Tags\n(.+?)\n", text, re.MULTILINE)
            tags_raw = tags_match.group(1) if tags_match else ""
            tags = [t.strip().strip("`") for t in tags_raw.split(",") if t.strip()]

            # Extract sources
            sources_match = re.search(r"## Sources\n(.+?)\n", text, re.MULTILINE)
            sources_raw = sources_match.group(1) if sources_match else ""
            sources = [
                s.strip().strip("- ").strip() for s in sources_raw.splitlines() if s.strip() and not s.startswith("_")
            ]

            # Extract veracity score
            veracity_match = re.search(r"_Veracity score_: ([\d.]+)", text)
            veracity = float(veracity_match.group(1)) if veracity_match else 0.5

            results.append(
                WikiEntry(
                    file_id=f.stem,
                    topic=topic,
                    title=title,
                    content=text,
                    tags=tags,
                    sources=sources,
                    created_at="",
                    veracity_score=veracity,
                    superseded_ids=[],
                )
            )

        return results

    async def search_by_tag(self, tag: str) -> list[WikiEntry]:
        """
        Search all wiki entries with a specific tag.

        Returns a list of WikiEntry dicts.
        """
        results: list[WikiEntry] = []

        for md_file in self.wiki_root.rglob("*.md"):
            if md_file.name == "INDEX.md" or md_file.name.startswith("_"):
                continue

            async with aiofiles.open(md_file, encoding="utf-8", mode="r") as fh:
                text = await fh.read()

            # Check tags section
            tags_match = re.search(r"## Tags\n(.+?)\n", text, re.MULTILINE)
            if not tags_match:
                continue

            tags_raw = tags_match.group(1).lower()
            if tag.lower() not in tags_raw:
                continue

            lines = text.splitlines()
            title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), md_file.stem)

            # Extract veracity score
            veracity_match = re.search(r"_Veracity score_: ([\d.]+)", text)
            veracity = float(veracity_match.group(1)) if veracity_match else 0.5

            # Extract date
            date_match = re.search(r"_Harvested_: ([\d-]+)", text)
            created_at = date_match.group(1) if date_match else ""

            # Find topic from path
            rel = md_file.parent.relative_to(self.wiki_root)
            topic = rel.parts[0] if rel.parts else "unknown"

            results.append(
                WikiEntry(
                    file_id=md_file.stem,
                    topic=topic,
                    title=title,
                    content=text,
                    tags=[t.strip().strip("`") for t in tags_match.group(1).split(",")],
                    sources=[],
                    created_at=created_at,
                    veracity_score=veracity,
                    superseded_ids=[],
                )
            )

        return results

    async def get_recent(self, days: int = 7, topic: str | None = None) -> list[WikiEntry]:
        """
        Get recent wiki entries from the last N days.

        Optionally filter by topic.
        """
        from datetime import timedelta

        cutoff = datetime.now(ZoneInfo("Asia/Jakarta")) - timedelta(days=days)
        results: list[WikiEntry] = []

        search_root = self.wiki_root / topic if topic else self.wiki_root

        for md_file in search_root.rglob("*.md"):
            if md_file.name == "INDEX.md" or md_file.name.startswith("_"):
                continue

            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
            if mtime < cutoff:
                continue

            async with aiofiles.open(md_file, encoding="utf-8", mode="r") as fh:
                text = await fh.read()

            lines = text.splitlines()
            title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), md_file.stem)

            veracity_match = re.search(r"_Veracity score_: ([\d.]+)", text)
            veracity = float(veracity_match.group(1)) if veracity_match else 0.5

            rel = md_file.parent.relative_to(self.wiki_root)
            entry_topic = rel.parts[0] if rel.parts else "unknown"

            results.append(
                WikiEntry(
                    file_id=md_file.stem,
                    topic=entry_topic,
                    title=title,
                    content=text,
                    tags=[],
                    sources=[],
                    created_at=mtime.strftime("%Y-%m-%d"),
                    veracity_score=veracity,
                    superseded_ids=[],
                )
            )

        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)
