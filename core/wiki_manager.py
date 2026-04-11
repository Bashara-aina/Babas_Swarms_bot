"""
LegionWikiManager — Karpathy LLM Wiki pattern for Legion.
Reads, writes, and maintains a git-tracked markdown wiki under wiki/.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import aiofiles

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / "wiki"

_wiki_singleton: WikiManager | None = None


def _now_jst() -> str:
    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M JST")


def _parse_wiki_plan(text: str) -> list[dict[str, str]]:
    """Parse PAGE:/ACTION:/CONTENT_SUMMARY: blocks from model output."""
    blocks = re.split(r"(?=^PAGE:\s*)", text, flags=re.MULTILINE)
    out: list[dict[str, str]] = []
    for block in blocks:
        block = block.strip()
        if not block.upper().startswith("PAGE:"):
            continue
        page = ""
        action = "update"
        summary = ""
        for line in block.splitlines():
            lu = line.strip()
            ul = lu.upper()
            if ul.startswith("PAGE:"):
                page = lu.split(":", 1)[1].strip()
            elif ul.startswith("ACTION:"):
                action = lu.split(":", 1)[1].strip().lower()
            elif ul.startswith("CONTENT_SUMMARY:"):
                summary = lu.split(":", 1)[1].strip()
        page = page.replace("wiki/", "").lstrip("/")
        if page and page not in ("SCHEMA.md",):
            out.append({"page": page, "action": action, "summary": summary})
        if len(out) >= 5:
            break
    return out


class WikiManager:
    """Persistent markdown wiki: ingest, query, lint."""

    def __init__(self, wiki_root: Path | None = None) -> None:
        self.wiki_dir = (wiki_root or WIKI_DIR).resolve()
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.wiki_dir / "INDEX.md"
        self.schema_path = self.wiki_dir / "SCHEMA.md"
        self._ensure_structure()

    def _resolve(self, rel: str) -> Path | None:
        rel = rel.strip().replace("\\", "/").lstrip("/")
        if ".." in rel.split("/"):
            return None
        base = self.wiki_dir.resolve()
        candidate = (self.wiki_dir / rel).resolve()
        try:
            candidate.relative_to(base)
        except ValueError:
            return None
        return candidate

    def _ensure_structure(self) -> None:
        subdirs = [
            "bashara",
            "legion",
            "rumahlabuh",
            "research",
            "research/papers",
            "tools",
            "tokyo",
            "conversations",
        ]
        for subdir in subdirs:
            (self.wiki_dir / subdir).mkdir(parents=True, exist_ok=True)

    async def _wiki_llm(
        self,
        user_prompt: str,
        *,
        system_prompt: str = ("You follow instructions precisely. Output only what is asked — no preamble."),
        model: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        from llm_client import wiki_raw_completion

        return await wiki_raw_completion(
            user_prompt,
            system_prompt=system_prompt,
            model=model,
            max_tokens=max_tokens,
        )

    async def read_index(self) -> str:
        if not self.index_path.exists():
            return "# Legion Wiki Index\n\nNo pages yet. Legion adds entries as it learns. See SCHEMA.md for rules.\n"
        async with aiofiles.open(self.index_path, encoding="utf-8", mode="r") as f:
            return await f.read()

    async def read_page(self, page_path: str) -> str:
        resolved = self._resolve(page_path)
        if resolved is None or not resolved.is_file():
            return f"Page {page_path} does not exist yet."
        async with aiofiles.open(resolved, encoding="utf-8", mode="r") as f:
            return await f.read()

    async def write_page(
        self,
        page_path: str,
        content: str,
        *,
        update_index: bool = True,
        skip_quality_gate: bool = False,
    ) -> None:
        from core.wiki_quality_gate import evaluate_before_write, quarantine_content

        resolved = self._resolve(page_path)
        if resolved is None:
            logger.warning("wiki write rejected (unsafe path): %s", page_path)
            return

        # Quality gate — evaluate BEFORE writing (skip for internal/index writes)
        if not skip_quality_gate:
            result = await evaluate_before_write(page_path, content)
            if result.verdict == "REJECT":
                logger.warning("Wiki write rejected: %s (score=%.2f)", page_path, result.score)
                await quarantine_content(page_path, content, result.reason, result.score)
                return
            if result.verdict == "NEEDS_IMPROVEMENT":
                logger.info("Wiki needs improvement: %s (score=%.2f)", page_path, result.score)
                content = f"⚠️ QUALITY NOTE: {result.reason}\n\n{content}"

        resolved.parent.mkdir(parents=True, exist_ok=True)
        stamp = _now_jst()
        if "_Last updated:" not in content and "_last updated:" not in content.lower():
            content = f"{content.rstrip()}\n\n---\n_Last updated: {stamp} by Legion_\n"
        async with aiofiles.open(resolved, encoding="utf-8", mode="w") as f:
            await f.write(content)
        logger.info("Wiki page written: %s", page_path)
        if update_index and page_path not in ("INDEX.md", "LINT_REPORT.md"):
            await self._update_index(page_path)

    async def _update_index(self, new_page_path: str) -> None:
        index_content = await self.read_index()
        schema_text = ""
        if self.schema_path.exists():
            async with aiofiles.open(self.schema_path, encoding="utf-8", mode="r") as f:
                schema_text = await f.read()

        prompt = f"""You are maintaining INDEX.md for Legion's wiki.
A page was created or updated: {new_page_path}

Wiki schema (excerpt):
{schema_text[:1200]}

Current INDEX.md:
{index_content[:6000]}

Update INDEX.md to list this page under the correct section with one concise line per page.
Return ONLY the full updated INDEX.md markdown, nothing else."""

        updated = await self._wiki_llm(
            prompt,
            max_tokens=2000,
            model=os.getenv("LEGION_WIKI_LLM_MODEL"),
        )
        if updated.strip():
            async with aiofiles.open(self.index_path, encoding="utf-8", mode="w") as f:
                await f.write(updated.strip() + "\n")
        else:
            async with aiofiles.open(self.index_path, encoding="utf-8", mode="a") as f:
                await f.write(f"\n- [[wiki/{new_page_path}]] — added by Legion\n")

    async def ingest(
        self,
        source: str,
        source_type: str = "conversation",
        context: str = "",
    ) -> list[str]:
        source = (source or "")[:8000]
        index = await self.read_index()
        schema = ""
        if self.schema_path.exists():
            async with aiofiles.open(self.schema_path, encoding="utf-8", mode="r") as f:
                schema = await f.read()

        planning_prompt = f"""You are Legion's wiki manager.

Wiki Schema:
{schema[:4000]}

Current Wiki Index:
{index[:4000]}

New source to ingest (type: {source_type}):
***
{source[:3000]}
***

{f"Context: {context}" if context else ""}

List wiki pages to CREATE or UPDATE (max 5). Use this exact format per page (blank line between pages):

PAGE: relative/path.md
ACTION: create
CONTENT_SUMMARY: one line describing what to write

Paths are relative to wiki/ (e.g. bashara/preferences.md), never use ... or absolute paths."""

        plan_response = await self._wiki_llm(planning_prompt, max_tokens=1200)
        pages_modified: list[str] = []
        for item in _parse_wiki_plan(plan_response):
            page_path = item["page"]
            action = item.get("action", "update")
            summary = item.get("summary", "")
            if not page_path.endswith(".md"):
                page_path = f"{page_path}.md"
            existing = await self.read_page(page_path)
            is_update = action == "update" and "does not exist" not in existing

            write_prompt = f"""Write the {"full" if not is_update else "updated"} markdown for wiki page: {page_path}

Schema rules (follow strictly):
{schema[:800]}

{"Existing page content:" if is_update else "New page."}
{existing[:2500] if is_update else ""}

Information to integrate:
{summary}

Source:
{source[:2000]}

Return ONLY complete markdown for the page. Use [[wiki/other/path.md]] for cross-links. Tag uncertainty with [uncertain] and sources with [source: ...]."""

            page_content = await self._wiki_llm(write_prompt, max_tokens=2500)
            if not page_content.strip():
                continue
            await self.write_page(page_path, page_content.strip())
            pages_modified.append(page_path)

        return pages_modified

    async def query(self, question: str, top_k: int = 3) -> str:
        index = await self.read_index()
        router_model = os.getenv("LEGION_WIKI_ROUTER_MODEL", "groq/llama-3.1-8b-instant")
        routing_prompt = f"""Wiki Index:
{index[:4000]}

User question: {question}

Which {top_k} wiki pages are most relevant? List ONLY paths relative to wiki/, one per line (e.g. legion/architecture.md), most relevant first.
If nothing applies, reply exactly: NONE"""

        relevant_raw = await self._wiki_llm(
            routing_prompt,
            model=router_model,
            max_tokens=200,
        )
        if not relevant_raw or "NONE" in relevant_raw.upper().split("\n")[0]:
            return ""

        context_parts: list[str] = []
        seen: set[str] = set()
        for line in relevant_raw.strip().split("\n"):
            line = line.strip().strip("`").strip("-• ")
            if not line or line.upper() == "NONE":
                continue
            page_path = line.replace("wiki/", "").split()[0]
            if page_path in seen:
                continue
            seen.add(page_path)
            content = await self.read_page(page_path)
            if "does not exist" in content:
                continue
            context_parts.append(f"### From wiki/{page_path}:\n{content[:1500]}")
            if len(context_parts) >= top_k:
                break

        if not context_parts:
            return ""

        return "## LEGION WIKI KNOWLEDGE\n\n" + "\n\n---\n\n".join(context_parts)

    async def lint(self) -> str:
        all_pages: list[dict[str, str]] = []
        for path in sorted(self.wiki_dir.rglob("*.md")):
            rel = path.relative_to(self.wiki_dir)
            if rel.name.startswith("_"):
                continue
            text = await self.read_page(str(rel))
            preview = text.replace("\n", " ")[:120]
            all_pages.append({"path": str(rel), "preview": preview})

        pages_summary = "\n".join(f"- {p['path']}: {p['preview']}..." for p in all_pages)
        lint_prompt = f"""You are auditing Legion's knowledge wiki.

Pages:
{pages_summary[:12000]}

Report:
1. STALE
2. CONTRADICTIONS
3. ORPHANED
4. MISSING
5. RESEARCH_NEEDED

Be specific; name files."""

        report = await self._wiki_llm(lint_prompt, max_tokens=2000)
        header = f"# Legion Wiki Lint Report\n_Generated: {_now_jst()}_\n\n"
        report_full = header + (report or "(no output from model)")
        await self.write_page(
            "LINT_REPORT.md",
            report_full,
            update_index=False,
            skip_quality_gate=True,
        )
        return report_full

    async def sync_agents_md(self) -> str:
        """Regenerate AGENTS.md in the repo root from wiki knowledge.

        Scopes:
          - Recent ADRs → Architecture section
          - Recent session summaries → Agent system updates
          - Architecture pages → Directory guide updates
          - Recent decisions → Decisions log
        """
        import aiofiles

        repo_root = REPO_ROOT
        agents_md = repo_root / "AGENTS.md"

        adr_dir = WIKI_DIR / "decisions"
        session_dir = WIKI_DIR / "opencode" / "sessions"

        adr_files: list[Path] = []
        if adr_dir.exists():
            try:
                adr_files = sorted(adr_dir.glob("ADR-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            except OSError:
                adr_files = []

        session_files: list[Path] = []
        if session_dir.exists():
            try:
                session_files = sorted(session_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            except OSError:
                session_files = []

        adr_block = ""
        for adrf in adr_files[:10]:
            try:
                async with aiofiles.open(adrf, encoding="utf-8", mode="r") as f:
                    content = await f.read()
                lines = content.splitlines()
                title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), adrf.stem)
                date = next((ln.split("created: ")[-1].strip() for ln in lines if ln.startswith("created: ")), "")
                adr_block += f"- `{adrf.stem}` — {title} ({date})\n"
            except OSError:
                continue

        session_block = ""
        for sf in session_files[:5]:
            try:
                async with aiofiles.open(sf, encoding="utf-8", mode="r") as f:
                    content = await f.read()
                lines = content.splitlines()
                task = next((ln.replace("## Task", "").strip() for ln in lines if ln.startswith("## Task")), sf.stem)
                date = next((ln.split("created: ")[-1].strip() for ln in lines if ln.startswith("created: ")), "")
                session_block += f"- `{sf.stem}` — {task[:60]} ({date})\n"
            except OSError:
                continue

        wiki_pages: list[str] = []
        try:
            for md_file in sorted(self.wiki_dir.rglob("*.md")):
                rel = md_file.relative_to(self.wiki_dir)
                if rel.name.startswith("_") or rel.parts[0] in ("_archive", "_quarantine", ".obsidian"):
                    continue
                wiki_pages.append(str(rel))
        except OSError:
            wiki_pages = []

        schema = ""
        if self.schema_path.exists():
            async with aiofiles.open(self.schema_path, encoding="utf-8", mode="r") as f:
                schema = await f.read()

        sync_prompt = f"""You are regenerating AGENTS.md for the SwarmBot project.
Read the existing AGENTS.md below and update it with fresh knowledge from the wiki.

EXISTING AGENTS.md:
(do not include this in output)

WIKI KNOWLEDGE:
## Recent Decisions (from wiki/decisions/):
{adr_block or "- No decisions recorded yet"}

## Recent OpenCode Sessions (from wiki/opencode/sessions/):
{session_block or "- No sessions recorded yet"}

## Wiki Pages (from wiki/):
{chr(10).join(f"- {p}" for p in wiki_pages[:40])}

## Schema excerpt:
{schema[:800]}

Update the AGENTS.md file. Keep the coding standards, critical rules, commands, and directory guide intact.
Update the Architecture, Agent System, Wiki Auto-Ingest, and Directory Guide sections with new wiki knowledge.
Add a "## 🧠 Shared Brain (OpenCode ↔ Legion)" section summarizing how the two agents share the .wiki/ vault.
Return the COMPLETE updated AGENTS.md markdown. Start with the front-matter line."""

        updated = await self._wiki_llm(sync_prompt, max_tokens=3000)
        if not updated.strip():
            logger.warning("sync_agents_md: LLM returned empty")
            return ""

        try:
            async with aiofiles.open(agents_md, encoding="utf-8", mode="w") as f:
                await f.write(updated.strip() + "\n")
            logger.info("AGENTS.md synced from wiki")
        except OSError as exc:
            logger.warning("sync_agents_md: failed to write AGENTS.md: %s", exc)
            return ""

        return updated.strip()

    async def ingest_codebase(self, repo_path: str = ".") -> None:
        repo = Path(repo_path).resolve()
        key_files: list[Path] = []
        for py_file in repo.rglob("*.py"):
            s = str(py_file)
            if any(x in s for x in ("__pycache__", "test_", ".venv", "migrations")):
                continue
            if "tests" in py_file.parts:
                continue
            key_files.append(py_file)

        for i in range(0, len(key_files), 5):
            batch = key_files[i : i + 5]
            batch_content = ""
            for f in batch:
                try:
                    snippet = f.read_text(encoding="utf-8", errors="replace")[:1500]
                    batch_content += f"\n\n### {f.relative_to(repo)}\n```python\n{snippet}\n```"
                except OSError:
                    continue
            if batch_content.strip():
                await self.ingest(
                    source=batch_content,
                    source_type="codebase",
                    context=f"Babas_Swarms_bot batch {i // 5 + 1}",
                )
                await asyncio.sleep(1)
        logger.info("Codebase wiki ingest finished")


def get_wiki_manager() -> WikiManager:
    global _wiki_singleton
    if _wiki_singleton is None:
        _wiki_singleton = WikiManager()
    return _wiki_singleton


async def schedule_wiki_ingest_exchange(
    user_id: str,
    user_text: str,
    assistant_text: str,
) -> None:
    try:
        src = f"User: {user_text}\nLegion: {assistant_text}"
        await get_wiki_manager().ingest(
            source=src,
            source_type="conversation",
            context=f"Telegram user_id={user_id}",
        )
    except Exception as exc:
        logger.warning("wiki background ingest failed: %s", exc)
