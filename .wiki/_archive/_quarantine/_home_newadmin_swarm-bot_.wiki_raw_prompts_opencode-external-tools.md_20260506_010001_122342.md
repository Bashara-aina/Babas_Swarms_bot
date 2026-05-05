---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/raw/prompts/opencode-external-tools.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-06T01:00:01.122376"
}
---

---
title: Opencode External Tools
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- prompts
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Wire gpt-researcher, Dify, and markitdown into Legion'
wikilinks: []
confidence: medium
source: research
---
# OPENCODE — EXTERNAL TOOLS INTEGRATION MASTER PROMPT
> Wire gpt-researcher, Dify, and markitdown into Legion
> Goal: Replace Perplexity + Claude Max with self-hosted open source
> Based on existing repo audit — requirements.txt and core/skills/ already read
> Paste this entire prompt into OpenCode with repo access open

---

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  LEGION — EXTERNAL TOOLS WIRING                                  ┃
┃  3 tools, 3 integrations, 1 session                              ┃
┃  Do NOT touch SOUL.md, CLAUDE.md, or LEGION_MASTER.md            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

CONTEXT: Legion already has these in requirements.txt (DO NOT re-add):
  crawl4ai, beautifulsoup4, aiohttp, mcp>=1.2.0,
  sentence-transformers, chromadb, langchain, langchain-community,
  pdfplumber, PyMuPDF, pytesseract, Pillow, python-docx

Existing skill files in core/skills/:
  __init__.py, registry.py, timer.py, code_review.py, builtin/

New files you will create in this session:
  core/skills/deep_research.py      ← gpt-researcher wrapper
  core/skills/dify_analysis.py      ← Dify API wrapper
  core/skills/doc_parser.py         ← markitdown wrapper
  core/integrations/__init__.py     ← new integrations package
  core/integrations/gptr_client.py  ← gpt-researcher MCP client
  core/integrations/dify_client.py  ← Dify HTTP client
  docker/dify-compose.yml           ← Dify self-hosted docker config
  scripts/setup_external_tools.sh   ← one-shot install script

══════════════════════════════════════════════════════════════════════
TOOL 1 — GPT-RESEARCHER (Replaces Perplexity deep research)
══════════════════════════════════════════════════════════════════════

REPO: https://github.com/assafelovic/gpt-researcher (26k stars)
MCP BRIDGE: https://github.com/assafelovic/gptr-mcp

WHAT IT DOES:
  - Autonomous multi-source web research for any topic
  - Returns long-form report with citations in markdown
  - Supports any LLM backend (use OpenRouter, already in Legion)
  - Has MCP server — means Legion can call it as a native skill

USE CASES FOR CEKWAJAR.ID:
  - "Research Mercer/KF salary data providers Indonesia"
  - "Research ATRBPN MoU precedents with Indonesian startups"
  - "Research political risk of emigration-content in Indonesian social media"
  - "Research B2B SaaS pricing benchmarks Indonesia"

STEP 1 — Install gpt-researcher as a package:

  Add to requirements.txt (after the last line):

    # === External Research Tools ===
    gpt-researcher>=0.11.0
    gptr-mcp>=0.1.0

STEP 2 — Create core/integrations/ package:

  mkdir -p core/integrations
  touch core/integrations/__init__.py

  core/integrations/__init__.py content:
    """External tool integrations: gpt-researcher, Dify, markitdown."""
    from .gptr_client import GPTResearcherClient
    from .dify_client import DifyClient

    __all__ = ["GPTResearcherClient", "DifyClient"]

STEP 3 — Create core/integrations/gptr_client.py:

  import os
  import asyncio
  import logging
  from typing import Optional

  logger = logging.getLogger(__name__)

  class GPTResearcherClient:
      """
      Wrapper around gpt-researcher library.
      Uses OpenRouter (already configured in Legion via OPENROUTER_API_KEY).
      Falls back to direct LLM call if gpt-researcher unavailable.
      """

      def __init__(self):
          self.available = self._check_available()
          # Use Legion's existing OpenRouter key
          self.llm_provider = os.getenv("GPTR_LLM_PROVIDER", "openai")
          self.llm_model = os.getenv("GPTR_LLM_MODEL", "openai/gpt-4o-mini")
          self.search_api = os.getenv("GPTR_SEARCH_API", "duckduckgo")
          # If Brave Search key exists in Legion env, use it
          if os.getenv("BRAVE_API_KEY"):
              self.search_api = "tavily"  # or "brave" if supported

      def _check_available(self) -> bool:
          try:
              import gpt_researcher
              return True
          except ImportError:
              logger.warning("gpt-researcher not installed. Run: pip install gpt-researcher")
              return False

      async def research(self, query: str,
                         report_type: str = "research_report",
                         max_sections: int = 5) -> dict:
          """
          Run deep research on a query.

          Args:
              query: Research question or topic
              report_type: "research_report" | "outline_report" | "custom_report"
              max_sections: Max sections in output report

          Returns:
              dict with keys: report (str), sources (list), cost_estimate (float)
          """
          if not self.available:
              return {
                  "report": f"gpt-researcher not available. Install with: pip install gpt-researcher",
                  "sources": [],
                  "cost_estimate": 0.0
              }

          try:
              from gpt_researcher import GPTResearcher

              # Set env vars gpt-researcher expects
              os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")
              os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
              os.environ["FAST_LLM"] = self.llm_model
              os.environ["SMART_LLM"] = os.getenv(
                  "GPTR_SMART_MODEL", "anthropic/claude-3-5-haiku"
              )
              os.environ["RETRIEVER"] = self.search_api

              researcher = GPTResearcher(
                  query=query,
                  report_type=report_type
              )
              await researcher.conduct_research()
              report = await researcher.write_report()
              sources = researcher.get_research_sources()

              logger.info(f"Research complete: {len(report)} chars, "
                          f"{len(sources)} sources")
              return {
                  "report": report,
                  "sources": sources,
                  "cost_estimate": self._estimate_cost(report)
              }

          except Exception as e:
              logger.error(f"GPT-Researcher error: {e}")
              return {
                  "report": f"Research failed: {str(e)}",
                  "sources": [],
                  "cost_estimate": 0.0
              }

      def _estimate_cost(self, report: str) -> float:
          """Rough token cost estimate in USD."""
          tokens = len(report.split()) * 1.3  # words to tokens estimate
          return round(tokens / 1000 * 0.0015, 4)  # gpt-4o-mini rate

      async def quick_search(self, query: str) -> str:
          """Fast single-source search. Returns plain text summary.
          Use when full research is overkill (< 3 second response needed)."""
          result = await self.research(query, report_type="outline_report", max_sections=2)
          return result["report"]

STEP 4 — Create core/skills/deep_research.py (Legion skill wrapper):

  import asyncio
  import logging
  from core.integrations.gptr_client import GPTResearcherClient

  logger = logging.getLogger(__name__)
  _client = GPTResearcherClient()

  SKILL_NAME = "deep_research"
  SKILL_DESCRIPTION = "Deep multi-source web research with citations. Use for: market research, competitor analysis, legal/regulatory research, data sourcing."
  TRIGGER_KEYWORDS = [
      "research", "riset", "cari tahu", "analisis pasar", "market research",
      "kompetitor", "regulasi", "investigate", "deep dive", "laporan"
  ]

  async def execute(query: str, report_type: str = "research_report") -> str:
      """
      Execute deep research skill.
      Called by Legion skill registry when research intent is detected.

      Args:
          query: Research topic or question
          report_type: Type of report (research_report / outline_report)

      Returns:
          Formatted markdown string for Telegram
      """
      logger.info(f"Deep research skill triggered: {query[:50]}")

      result = await _client.research(query, report_type=report_type)

      if not result["report"] or "failed" in result["report"].lower():
          return f"⚠️ Research gagal. Coba: /search {query}"

      # Format for Telegram (4096 char limit)
      report = result["report"]
      sources = result["sources"]

      # Truncate if needed
      max_len = 3500
      if len(report) > max_len:
          report = report[:max_len] + "\n\n_[Report dipotong. Full version tersimpan di memory.]_"

      source_lines = ""
      if sources:
          top_sources = sources[:3]
          source_lines = "\n\n📚 *Sources:*\n" + "\n".join(
              f"• {s.get('url', s) if isinstance(s, dict) else s}"
              for s in top_sources
          )

      cost_note = ""
      if result["cost_estimate"] > 0:
          cost_note = f"\n_~${result['cost_estimate']} API cost_"

      return f"🔬 *Deep Research: {query[:40]}*\n\n{report}{source_lines}{cost_note}"


  # Register with Legion skill registry
  SKILL_META = {
      "name": SKILL_NAME,
      "description": SKILL_DESCRIPTION,
      "triggers": TRIGGER_KEYWORDS,
      "execute": execute,
      "requires_internet": True,
      "avg_latency_seconds": 30,
      "cost_tier": "medium",
  }

STEP 5 — Register in core/skills/registry.py:
  Open core/skills/registry.py.
  Find the dict or list where skills are registered.
  Add:
    from core.skills.deep_research import SKILL_META as deep_research_meta
    # In the registry initialization:
    registry.register(deep_research_meta)

STEP 6 — Wire /research Telegram command:
  In handlers/ directory, find the file handling user commands.
  Add:

    async def handle_research_command(update, context):
        query = " ".join(context.args) if context.args else ""
        if not query:
            await update.message.reply_text(
                "Usage: /research <topic>\nExample: /research salary benchmarks Indonesia 2025"
            )
            return
        await update.message.reply_text("🔬 Researching... (30-60 detik)")
        result = await deep_research.execute(query)
        await update.message.reply_text(result, parse_mode="Markdown")

    # In main.py:
    app.add_handler(CommandHandler("research", handle_research_command))

VERIFY TOOL 1:
  python -c "from core.skills.deep_research import execute; print('OK')"
  Send to bot: /research Mercer salary data Indonesia providers
  Expected: 30-60s, returns markdown report with sources

══════════════════════════════════════════════════════════════════════
TOOL 2 — DIFY (Replaces Claude Max for doc analysis + drafting)
══════════════════════════════════════════════════════════════════════

REPO: https://github.com/langgenius/dify (137k stars)
DOCS: https://docs.dify.ai

WHAT IT DOES:
  - Self-hosted AI workflow platform
  - RAG pipelines: ingest PDFs, legal docs, tax regulations
  - Long-context document analysis with ANY LLM backend
  - Workflow builder: chain research → draft → review → output
  - REST API — Legion calls it via HTTP

USE CASES FOR CEKWAJAR.ID:
  - Draft UU PDP / ToS / legal disclaimers (RAG over Indonesian legal PDFs)
  - Draft PPh21 test case documentation
  - Seed deck narrative drafting
  - KJPP disclaimer language generation
  - "Kabur" content legal copy review workflow

STEP 1 — Create docker/dify-compose.yml:

  Create file docker/dify-compose.yml with this content:

  ---
  version: "3.8"
  services:
    dify-api:
      image: langgenius/dify-api:latest
      restart: always
      environment:
        MODE: api
        SECRET_KEY: ${DIFY_SECRET_KEY:-change-me-in-env}
        DB_USERNAME: dify
        DB_PASSWORD: ${DIFY_DB_PASSWORD:-difypassword}
        DB_HOST: dify-db
        DB_PORT: 5432
        DB_DATABASE: dify
        REDIS_HOST: dify-redis
        STORAGE_TYPE: local
        OPENAI_API_KEY: ${OPENROUTER_API_KEY}
        OPENAI_API_BASE: https://openrouter.ai/api/v1
      ports:
        - "5001:5001"
      depends_on:
        - dify-db
        - dify-redis
      volumes:
        - dify-storage:/app/api/storage

    dify-worker:
      image: langgenius/dify-api:latest
      restart: always
      environment:
        MODE: worker
        SECRET_KEY: ${DIFY_SECRET_KEY:-change-me-in-env}
        DB_USERNAME: dify
        DB_PASSWORD: ${DIFY_DB_PASSWORD:-difypassword}
        DB_HOST: dify-db
        DB_PORT: 5432
        DB_DATABASE: dify
        REDIS_HOST: dify-redis
        STORAGE_TYPE: local
        OPENAI_API_KEY: ${OPENROUTER_API_KEY}
        OPENAI_API_BASE: https://openrouter.ai/api/v1
      depends_on:
        - dify-db
        - dify-redis
      volumes:
        - dify-storage:/app/api/storage

    dify-web:
      image: langgenius/dify-web:latest
      restart: always
      environment:
        NEXTAUTH_SECRET_KEY: ${DIFY_SECRET_KEY:-change-me-in-env}
        CONSOLE_API_URL: http://dify-api:5001
        APP_API_URL: http://dify-api:5001
      ports:
        - "3001:3000"

    dify-db:
      image: postgres:15-alpine
      restart: always
      environment:
        POSTGRES_USER: dify
        POSTGRES_PASSWORD: ${DIFY_DB_PASSWORD:-difypassword}
        POSTGRES_DB: dify
      volumes:
        - dify-db-data:/var/lib/postgresql/data

    dify-redis:
      image: redis:7-alpine
      restart: always
      volumes:
        - dify-redis-data:/data

  volumes:
    dify-storage:
    dify-db-data:
    dify-redis-data:
  ---

  NOTE: This runs on ports 5001 (API) and 3001 (Web UI).
  Dify Web UI will be at http://localhost:3001 for building workflows.
  Legion calls the API at http://localhost:5001.

STEP 2 — Add .env variables needed (append to .env.example):

  # Dify self-hosted
  DIFY_API_URL=http://localhost:5001
  DIFY_API_KEY=            # Get from Dify Web UI after first boot
  DIFY_SECRET_KEY=         # Random string, set before first boot
  DIFY_DB_PASSWORD=        # Strong password

  # GPT-Researcher
  GPTR_LLM_MODEL=openai/gpt-4o-mini
  GPTR_SMART_MODEL=anthropic/claude-3-5-haiku
  GPTR_SEARCH_API=duckduckgo

STEP 3 — Create core/integrations/dify_client.py:

  import os
  import aiohttp
  import logging
  from typing import Optional

  logger = logging.getLogger(__name__)

  class DifyClient:
      """
      HTTP client for self-hosted Dify instance.
      Calls Dify workflows and chat apps via REST API.
      """

      def __init__(self):
          self.base_url = os.getenv("DIFY_API_URL", "http://localhost:5001")
          self.api_key = os.getenv("DIFY_API_KEY", "")
          self.available = bool(self.api_key)
          if not self.available:
              logger.warning(
                  "DIFY_API_KEY not set. Dify features disabled. "
                  "Set up Dify: docker compose -f docker/dify-compose.yml up -d"
              )

      async def run_workflow(self, workflow_id: str,
                             inputs: dict,
                             user_id: str = "legion") -> dict:
          """
          Run a Dify workflow.
          workflow_id: Get from Dify Web UI → Workflow → Publish → API
          inputs: dict of input variables defined in your workflow

          Returns: dict with 'output' key (str) and 'status'
          """
          if not self.available:
              return {"output": "Dify not configured.", "status": "unavailable"}

          url = f"{self.base_url}/v1/workflows/run"
          headers = {
              "Authorization": f"Bearer {self.api_key}",
              "Content-Type": "application/json"
          }
          payload = {
              "inputs": inputs,
              "response_mode": "blocking",
              "user": user_id
          }

          try:
              async with aiohttp.ClientSession() as session:
                  async with session.post(url, json=payload,
                                          headers=headers,
                                          timeout=aiohttp.ClientTimeout(total=120)) as resp:
                      if resp.status != 200:
                          error = await resp.text()
                          logger.error(f"Dify workflow error {resp.status}: {error}")
                          return {"output": f"Dify error: {resp.status}", "status": "error"}
                      data = await resp.json()
                      output = data.get("data", {}).get("outputs", {}).get("text", str(data))
                      return {"output": output, "status": "success"}
          except Exception as e:
              logger.error(f"Dify client error: {e}")
              return {"output": f"Dify unavailable: {str(e)}", "status": "error"}

      async def chat(self, app_id: str, message: str,
                     conversation_id: Optional[str] = None,
                     user_id: str = "legion") -> dict:
          """
          Send a message to a Dify chat app (with memory/history).
          Use for iterative document drafting sessions.
          Returns: dict with 'answer', 'conversation_id'
          """
          if not self.available:
              return {"answer": "Dify not configured.", "conversation_id": None}

          url = f"{self.base_url}/v1/chat-messages"
          headers = {
              "Authorization": f"Bearer {self.api_key}",
              "Content-Type": "application/json"
          }
          payload = {
              "inputs": {},
              "query": message,
              "response_mode": "blocking",
              "user": user_id,
          }
          if conversation_id:
              payload["conversation_id"] = conversation_id

          try:
              async with aiohttp.ClientSession() as session:
                  async with session.post(url, json=payload,
                                          headers=headers,
                                          timeout=aiohttp.ClientTimeout(total=120)) as resp:
                      data = await resp.json()
                      return {
                          "answer": data.get("answer", ""),
                          "conversation_id": data.get("conversation_id")
                      }
          except Exception as e:
              logger.error(f"Dify chat error: {e}")
              return {"answer": f"Dify unavailable: {e}", "conversation_id": None}

      async def health_check(self) -> bool:
          """Check if Dify instance is running."""
          try:
              async with aiohttp.ClientSession() as session:
                  async with session.get(
                      f"{self.base_url}/health",
                      timeout=aiohttp.ClientTimeout(total=5)
                  ) as resp:
                      return resp.status == 200
          except:
              return False

STEP 4 — Create core/skills/dify_analysis.py:

  import logging
  from core.integrations.dify_client import DifyClient

  logger = logging.getLogger(__name__)
  _client = DifyClient()

  SKILL_NAME = "dify_analysis"
  SKILL_DESCRIPTION = "Long-form document analysis and drafting via Dify. Use for: legal drafting, complex analysis, document review, structured report generation."
  TRIGGER_KEYWORDS = [
      "draft", "tulis", "buat dokumen", "analisis dokumen", "review kontrak",
      "legal", "compliance", "ToS", "disclaimer", "laporan panjang"
  ]

  # Map task types to Dify workflow IDs
  # You must create these workflows in Dify Web UI first, then get their IDs
  WORKFLOW_MAP = {
      "legal_draft":    "",  # Workflow: UU PDP / ToS / Disclaimer drafting
      "doc_analysis":   "",  # Workflow: Long document analysis
      "report_draft":   "",  # Workflow: Structured report generation
      "default":        "",  # Default chat app ID
  }

  async def execute(task_type: str, content: str,
                    workflow_id: str = "") -> str:
      """
      Execute Dify analysis skill.

      Args:
          task_type: "legal_draft" | "doc_analysis" | "report_draft"
          content: Document content or instruction
          workflow_id: Override workflow ID (optional)

      Returns:
          Formatted response string
      """
      if not _client.available:
          return (
              "⚠️ Dify belum disetup.\n"
              "Setup: `docker compose -f docker/dify-compose.yml up -d`\n"
              "Lalu set DIFY_API_KEY di .env"
          )

      wf_id = workflow_id or WORKFLOW_MAP.get(task_type, WORKFLOW_MAP["default"])

      if not wf_id:
          # Fall back to chat if no workflow configured yet
          result = await _client.chat(
              app_id=WORKFLOW_MAP["default"],
              message=content
          )
          return result["answer"]

      result = await _client.run_workflow(
          workflow_id=wf_id,
          inputs={"content": content, "task_type": task_type}
      )
      return result["output"]

  SKILL_META = {
      "name": SKILL_NAME,
      "description": SKILL_DESCRIPTION,
      "triggers": TRIGGER_KEYWORDS,
      "execute": execute,
      "requires_internet": False,  # self-hosted
      "avg_latency_seconds": 15,
      "cost_tier": "low",  # uses OpenRouter via Dify
  }

STEP 5 — Wire /draft Telegram command:

  async def handle_draft_command(update, context):
      args = context.args
      if not args:
          await update.message.reply_text(
              "Usage: /draft <type> <content>\n"
              "Types: legal, analysis, report\n"
              "Example: /draft legal UU PDP dual-checkbox consent for payslip upload"
          )
          return
      task_type = args[0] if args[0] in ["legal", "analysis", "report"] else "default"
      content = " ".join(args[1:] if args[0] in ["legal", "analysis", "report"] else args)
      await update.message.reply_text("✍️ Drafting...")
      result = await dify_analysis.execute(task_type, content)
      await update.message.reply_text(result[:4000], parse_mode="Markdown")

  # In main.py:
  app.add_handler(CommandHandler("draft", handle_draft_command))

VERIFY TOOL 2:
  # Step A: Start Dify
  docker compose -f docker/dify-compose.yml up -d
  # Step B: Open http://localhost:3001, create admin account
  # Step C: Get API key from Settings → API Keys
  # Step D: Set DIFY_API_KEY in .env
  # Step E:
  python -c "from core.integrations.dify_client import DifyClient; \
             import asyncio; c = DifyClient(); \
             print(asyncio.run(c.health_check()))"
  # Expected: True

══════════════════════════════════════════════════════════════════════
TOOL 3 — MARKITDOWN (Document → Markdown for any file format)
══════════════════════════════════════════════════════════════════════

REPO: https://github.com/microsoft/markitdown
INSTALL: pip install markitdown

WHAT IT DOES:
  - Converts ANY document to clean Markdown: PDF, DOCX, XLSX, PPTX, HTML,
    images (with OCR), audio (with transcription), EPUB, ZIP
  - Feeds output directly into LLM context or Dify RAG pipeline
  - Much better than pdfplumber for complex layouts

USE CASES FOR CEKWAJAR.ID:
  - Parse uploaded payslips (PDF → Markdown → PPh21 engine)
  - Parse Indonesian legal PDFs for Dify RAG knowledge base
  - Parse DJP regulation PDFs into structured text
  - Parse user-uploaded Excel salary tables

STEP 1 — Add to requirements.txt:
  markitdown[all]>=0.1.0

STEP 2 — Create core/skills/doc_parser.py:

  import os
  import logging
  import tempfile
  import aiofiles
  from pathlib import Path
  from typing import Union

  logger = logging.getLogger(__name__)

  def _check_markitdown() -> bool:
      try:
          from markitdown import MarkItDown
          return True
      except ImportError:
          logger.warning("markitdown not installed. Run: pip install 'markitdown[all]'")
          return False

  MARKITDOWN_AVAILABLE = _check_markitdown()

  async def parse_file(file_path: Union[str, Path],
                       use_llm_for_images: bool = False) -> dict:
      """
      Parse any document to Markdown using markitdown.
      Falls back to pdfplumber for PDFs if markitdown unavailable.

      Args:
          file_path: Path to the file (PDF, DOCX, XLSX, PPTX, image)
          use_llm_for_images: If True, uses LLM vision for image OCR (costs tokens)

      Returns:
          dict with keys: markdown (str), title (str), file_type (str), char_count (int)
      """
      file_path = Path(file_path)
      if not file_path.exists():
          return {"markdown": "", "title": "", "file_type": "",
                  "char_count": 0, "error": f"File not found: {file_path}"}

      file_type = file_path.suffix.lower()

      # Use markitdown if available
      if MARKITDOWN_AVAILABLE:
          try:
              from markitdown import MarkItDown

              md = MarkItDown(
                  llm_client=None,   # Set to OpenAI client if use_llm_for_images
                  llm_model=None
              )
              result = md.convert(str(file_path))
              markdown = result.text_content
              title = result.title or file_path.stem

              logger.info(f"Parsed {file_path.name}: {len(markdown)} chars via markitdown")
              return {
                  "markdown": markdown,
                  "title": title,
                  "file_type": file_type,
                  "char_count": len(markdown)
              }
          except Exception as e:
              logger.warning(f"markitdown failed for {file_path}: {e}. Trying fallback.")

      # Fallback: pdfplumber for PDFs (already in requirements.txt)
      if file_type == ".pdf":
          try:
              import pdfplumber
              text_parts = []
              with pdfplumber.open(file_path) as pdf:
                  for page in pdf.pages:
                      text = page.extract_text()
                      if text:
                          text_parts.append(text)
              markdown = "\n\n".join(text_parts)
              return {
                  "markdown": markdown,
                  "title": file_path.stem,
                  "file_type": ".pdf",
                  "char_count": len(markdown)
              }
          except Exception as e:
              return {"markdown": "", "title": "", "file_type": file_type,
                      "char_count": 0, "error": str(e)}

      return {"markdown": "", "title": "", "file_type": file_type,
              "char_count": 0, "error": f"Unsupported file type: {file_type}"}


  async def parse_telegram_document(bot, file_id: str,
                                     save_dir: str = "/tmp/legion_docs") -> dict:
      """
      Download a Telegram-sent document and parse it.
      Use this when user sends a file to the bot.

      Args:
          bot: Telegram bot instance
          file_id: Telegram file_id from the message
          save_dir: Local dir to save the file temporarily

      Returns:
          Same as parse_file()
      """
      os.makedirs(save_dir, exist_ok=True)

      try:
          file = await bot.get_file(file_id)
          filename = Path(file.file_path).name
          local_path = Path(save_dir) / filename

          await file.download_to_drive(local_path)
          logger.info(f"Downloaded Telegram file: {filename}")

          result = await parse_file(local_path)

          # Clean up temp file after parsing
          try:
              os.remove(local_path)
          except:
              pass

          return result

      except Exception as e:
          logger.error(f"Failed to download/parse Telegram file: {e}")
          return {"markdown": "", "title": "", "file_type": "",
                  "char_count": 0, "error": str(e)}

  SKILL_META = {
      "name": "doc_parser",
      "description": "Parse any document (PDF, DOCX, XLSX, PPTX, image) to Markdown.",
      "triggers": ["parse", "baca file", "ekstrak", "dokumen", "payslip", "upload"],
      "execute": parse_file,
      "requires_internet": False,
      "avg_latency_seconds": 3,
      "cost_tier": "free",
  }

STEP 3 — Wire document handling in message handler:
  Find the existing document/photo message handler in handlers/.
  Add doc_parser integration:

  from core.skills.doc_parser import parse_telegram_document

  async def handle_document(update, context):
      document = update.message.document
      if not document:
          return

      await update.message.reply_text("📄 Parsing dokumen...")

      result = await parse_telegram_document(
          bot=context.bot,
          file_id=document.file_id
      )

      if result.get("error"):
          await update.message.reply_text(f"⚠️ Parse gagal: {result['error']}")
          return

      markdown = result["markdown"]
      char_count = result["char_count"]

      # Store in memory for follow-up questions
      await long_term_memory.store(
          user_id=update.effective_user.id,
          content=markdown[:2000],  # store first 2000 chars
          tags=["document", result["file_type"], result["title"]]
      )

      # Respond with summary
      summary_prompt = f"Summarize this document in 3 bullet points:\n\n{markdown[:3000]}"
      summary = await call_llm(messages=[{"role": "user", "content": summary_prompt}])

      await update.message.reply_text(
          f"📄 *{result['title']}* ({char_count:,} chars)\n\n{summary}",
          parse_mode="Markdown"
      )

══════════════════════════════════════════════════════════════════════
FINAL STEP — Setup Script
══════════════════════════════════════════════════════════════════════

Create scripts/setup_external_tools.sh:

  #!/bin/bash
  set -e

  echo "=== Legion External Tools Setup ==="
  echo ""

  echo "[1/4] Installing Python packages..."
  pip install "gpt-researcher>=0.11.0" "markitdown[all]>=0.1.0" gptr-mcp
  echo "✅ Python packages installed"

  echo "[2/4] Checking Docker..."
  if ! command -v docker &> /dev/null; then
      echo "⚠️  Docker not found. Install Docker to use Dify."
      echo "    https://docs.docker.com/get-docker/"
  else
      echo "✅ Docker found: $(docker --version)"
  fi

  echo "[3/4] Checking .env for required variables..."
  MISSING=""
  for var in OPENROUTER_API_KEY BRAVE_API_KEY; do
      if [ -z "${!var}" ]; then
          MISSING="$MISSING $var"
      fi
  done

  if [ -n "$MISSING" ]; then
      echo "⚠️  Missing env vars:$MISSING"
      echo "    Add them to .env before proceeding"
  else
      echo "✅ Required env vars found"
  fi

  echo "[4/4] Testing imports..."
  python -c "
  results = []
  try:
      from core.skills.deep_research import SKILL_META
      results.append('✅ deep_research')
  except Exception as e:
      results.append(f'❌ deep_research: {e}')

  try:
      from core.skills.doc_parser import parse_file
      results.append('✅ doc_parser')
  except Exception as e:
      results.append(f'❌ doc_parser: {e}')

  try:
      from core.integrations.dify_client import DifyClient
      results.append('✅ dify_client')
  except Exception as e:
      results.append(f'❌ dify_client: {e}')

  for r in results:
      print(r)
  "

  echo ""
  echo "=== Dify Setup (optional but recommended) ==="
  echo "Run: docker compose -f docker/dify-compose.yml up -d"
  echo "Then open: http://localhost:3001"
  echo "Create admin account → Settings → API Keys → copy to .env as DIFY_API_KEY"
  echo ""
  echo "=== New Legion Commands After Setup ==="
  echo "/research <topic>  — deep web research with citations"
  echo "/draft <type> <content>  — AI document drafting via Dify"
  echo "[send any file]  — auto-parse to markdown + summary"
  echo ""
  echo "✅ Setup complete."

  chmod +x scripts/setup_external_tools.sh

══════════════════════════════════════════════════════════════════════
FINAL GATE — Run after all 3 tools implemented
══════════════════════════════════════════════════════════════════════

  # 1. Import check
  python -c "
  from core.skills.deep_research import SKILL_META as r1
  from core.skills.dify_analysis import SKILL_META as r2
  from core.skills.doc_parser import SKILL_META as r3
  from core.integrations import GPTResearcherClient, DifyClient
  print('All 3 tool integrations import OK ✅')
  "

  # 2. Run setup script
  bash scripts/setup_external_tools.sh

  # 3. Verify wiring
  python scripts/verify_wiring.py

  # 4. Live test (bot must be running)
  # Send to Telegram: /research PPh21 TER regulation Indonesia 2024
  # Expected: 30-60s response with research report and sources
  # Send any PDF to bot
  # Expected: auto-parse + 3-bullet summary

══════════════════════════════════════════════════════════════════════
HARD RULES
══════════════════════════════════════════════════════════════════════

1. Tool 1 (gpt-researcher) can work immediately — no Docker needed.
   Do this first as it has the most immediate value.
2. Tool 2 (Dify) requires Docker. If Docker not available on this machine:
   Skip docker/dify-compose.yml creation. Still create dify_client.py
   (it gracefully degrades when DIFY_API_KEY is not set).
3. Tool 3 (markitdown) is pure Python. Do this after Tool 1.
4. Do NOT remove existing skills (web_search, arxiv, etc.).
   deep_research COMPLEMENTS web_search — different use cases:
     web_search  = fast, single query, 8 results (already works)
     deep_research = slow, multi-source synthesis, full report (new)
5. After each tool: run python scripts/verify_wiring.py
6. All new files must have: proper imports, async def, try/except, logger calls.
7. Every new env var must be added to .env.example with a comment.
```
