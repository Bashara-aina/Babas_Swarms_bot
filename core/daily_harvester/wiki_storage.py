"""WikiStorage — write, read, and maintain the daily harvester wiki."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_ROOT = REPO_ROOT / ".wiki" / "knowledge"

_TOPIC_PREFIXES: dict[str, str] = {
    "cekwajar_labor_law": "CW-",
    "cekwajar_market": "CW-",
    "cekwajar_engineering": "CW-",
    "cekwajar_tax": "CW-",
    "cekwajar_bpjs": "CW-",
    "cekwajar_business": "CW-",
    "popw": "POPW-",
    "ai_tools_llm": "AI-",
    "babas_bot_ai": "AI-",
    "personal": "PERS-",
    "indonesia_economy": "GEN-",
    "rumahlabuh_property": "GEN-",
    "surprise_discoveries": "GEN-",
    "general": "GEN-",
}

_TOPIC_SLUG_MAP: dict[str, str] = {
    "cekwajar_labor_law": "labor-law",
    "cekwajar_market": "market",
    "cekwajar_engineering": "engineering",
    "cekwajar_tax": "tax",
    "cekwajar_bpjs": "bpjs",
    "cekwajar_business": "business",
    "popw_ml_research": "research",
    "popw_experiments": "experiments",
    "popw_roadmap": "roadmap",
    "ai_tools_llm": "opencode",
    "babas_bot_ai": "swarms",
    "personal_life": "personal",
    "personal_relationships": "relationships",
    "personal_finance": "finance",
    "personal_japan_life": "japan-life",
    "indonesia_economy": "economy",
    "rumahlabuh_property": "property",
    "surprise_discoveries": "surprise",
    "general_technology": "technology",
    "general_economy": "economy",
}


def _slugify(title: str) -> str:
    """Convert a title into a short URL-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", title)
    slug = re.sub(r"\s+", "-", slug)
    return slug[:40].lower().rstrip("-")


def _topic_dir(topic: str) -> Path:
    """Return the wiki subdirectory for a topic."""
    # Try to find the subdirectory path
    for key, subpath in _TOPIC_SLUG_MAP.items():
        if topic.startswith(key) or key in topic:
            # Find the base category
            if "cekwajar" in topic:
                return WIKI_ROOT / "cekwajar" / subpath
            elif "popw" in topic:
                return WIKI_ROOT / "popw" / subpath
            elif "ai-tools" in topic or "ai_tools" in topic:
                return WIKI_ROOT / "ai-tools" / subpath
            elif "personal" in topic:
                return WIKI_ROOT / "personal" / subpath
            elif "general" in topic:
                return WIKI_ROOT / "general" / subpath
    return WIKI_ROOT / "general" / "technology"


def _topic_prefix(topic: str) -> str:
    """Return the file prefix for a topic (e.g. CW-, POPW-, AI-, PERS-, GEN-)."""
    for key, prefix in _TOPIC_PREFIXES.items():
        if key in topic:
            return prefix
    return "GEN-"


def _next_seq(dir_path: Path, prefix: str) -> int:
    """Find the next sequence number for a file in dir_path with given prefix."""
    if not dir_path.exists():
        return 1
    existing: list[int] = []
    for f in dir_path.glob(f"{prefix}*.md"):
        name = f.stem
        # Pattern: PREFIX-NNN-slug
        m = re.match(rf"^{re.escape(prefix)}(\d+)", name)
        if m:
            try:
                existing.append(int(m.group(1)))
            except ValueError:
                pass
    return max(existing, default=0) + 1


class WikiStorage:
    """Persistent wiki storage for daily harvester entries."""

    def __init__(self, wiki_root: Path | None = None) -> None:
        self.wiki_root = (wiki_root or WIKI_ROOT).resolve()
        self.rejected_log = self.wiki_root.parent / "harvest_rejected.md"
        self.conflict_log = self.wiki_root.parent / "harvest_conflicts.md"
        self.harvest_log = self.wiki_root.parent / "harvest_log.md"

    def _make_filename(self, topic: str, title: str, date: str) -> str:
        """Build a harvester entry filename: PREFIX-NNN-slug-YYYY-MM-DD.md."""
        prefix = _topic_prefix(topic)
        dir_path = _topic_dir(topic)
        seq = _next_seq(dir_path, prefix)
        slug = _slugify(title)
        return f"{prefix}{seq:03d}-{slug}-{date}.md"

    async def write_entry(self, entry: dict[str, Any]) -> str:
        """Write a wiki entry. Returns the file_id (filename without .md)."""
        topic = entry.get("topic", "general")
        title = entry.get("title", "Untitled")
        date = entry.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        if len(date) > 10:
            date = date[:10]  # just YYYY-MM-DD

        filename = self._make_filename(topic, title, date)
        dir_path = _topic_dir(topic)
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / filename

        content = entry.get("content", "")
        tags = entry.get("tags", [])
        sources = entry.get("sources", [])
        veracity = entry.get("veracity_score", 0.5)

        lines = [
            f"# {title}",
            "",
            f"_Topic_: {topic}",
            f"_Veracity score_: {veracity:.2f}",
            f"_Harvested_: {date}",
            "",
            "## Content",
            "",
            content,
            "",
            "## Tags",
            ", ".join(f"`{t}`" for t in tags) if tags else "_none_",
            "",
            "## Sources",
        ]
        if sources:
            for src in sources:
                lines.append(f"- {src}")
        else:
            lines.append("_none_")

        async with aiofiles.open(file_path, encoding="utf-8", mode="w") as f:
            await f.write("\n".join(lines))

        logger.info("WikiStorage wrote: %s", file_path)
        return filename.rstrip(".md")

    async def read_entry(self, file_id: str) -> dict[str, Any]:
        """Read a wiki entry by file_id."""
        # file_id may or may not include .md
        file_id_clean = file_id.rstrip(".md")
        # Search for the file
        for md_file in self.wiki_root.rglob(f"{file_id_clean}.md"):
            async with aiofiles.open(md_file, encoding="utf-8", mode="r") as f:
                content = await f.read()
            lines = content.splitlines()
            title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), file_id_clean)
            return {
                "file_id": file_id_clean,
                "content": content,
                "title": title,
            }
        return {"file_id": file_id_clean, "content": "", "title": "", "error": "not found"}

    async def update_index(self, topic: str) -> None:
        """Regenerate the INDEX.md for a topic directory."""
        dir_path = _topic_dir(topic)
        index_path = dir_path / "INDEX.md"
        if not dir_path.exists():
            return

        entries: list[dict[str, str]] = []
        for f in sorted(dir_path.glob("*.md")):
            if f.name == "INDEX.md":
                continue
            async with aiofiles.open(f, encoding="utf-8", mode="r") as fh:
                text = await fh.read()
            lines = text.splitlines()
            title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), f.stem)
            preview = " ".join(text.replace("\n", " ").split())[:100]
            entries.append({"file": f.name, "title": title, "preview": preview})

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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
                lines_out.append(f"- [[{e['file']}]] — {e['title']}: {e['preview']}...")
        else:
            lines_out.append("No entries yet — harvested daily.")

        async with aiofiles.open(index_path, encoding="utf-8", mode="w") as f:
            await f.write("\n".join(lines_out))

    async def append_rejected_log(self, candidate: dict[str, Any], reason: str) -> None:
        """Append a rejected candidate to the harvest_rejected.md log."""
        lines = [
            f"## {candidate.get('title', 'Untitled')} (rejected {datetime.now(timezone.utc).strftime('%Y-%m-%d')})",
            "",
            f"**Reason**: {reason}",
            "",
            f"**Topic**: {candidate.get('topic', 'unknown')}",
            "",
        ]
        async with aiofiles.open(self.rejected_log, encoding="utf-8", mode="a") as f:
            await f.write("\n".join(lines) + "\n")

    async def append_conflict_log(self, file_id1: str, file_id2: str, reason: str) -> None:
        """Append a conflict between two wiki entries to harvest_conflicts.md."""
        lines = [
            f"## Conflict: {file_id1} vs {file_id2} ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})",
            "",
            f"**Reason**: {reason}",
            "",
            f"**File 1**: {file_id1}",
            f"**File 2**: {file_id2}",
            "",
        ]
        async with aiofiles.open(self.conflict_log, encoding="utf-8", mode="a") as f:
            await f.write("\n".join(lines) + "\n")

    async def append_harvest_log(self, accepted_count: int, rejected_count: int, date: str) -> None:
        """Append a daily harvest summary to harvest_log.md."""
        line = f"- **{date}**: {accepted_count} accepted, {rejected_count} rejected"
        async with aiofiles.open(self.harvest_log, encoding="utf-8", mode="a") as f:
            await f.write(line + "\n")
