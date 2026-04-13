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

═════════════════════════════════════════════════════════════════════
TOOL 1 — GPT-RESEARCHER (Replaces Perplexity deep research)
═════════════════════════════════════════════════════════════════════

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
          self.llm_provider = os.getenv("GPTR_LLM_PROVIDER", "openai")
          self.llm_model = os.getenv("GPTR_LLM_MODEL", "openai/gpt-4o-mini")
          self.search_api = os.getenv("GPTR_SEARCH_API", "duckduckgo")

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
          if not self.available:
              return {"report": "gpt-researcher not available.", "sources": [], "cost_estimate": 0.0}
          try:
              from gpt_researcher import GPTResearcher
              os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")
              os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
              researcher = GPTResearcher(query=query, report_type=report_type)
              await researcher.conduct_research()
              report = await researcher.write_report()
              sources = researcher.get_research_sources()
              return {"report": report, "sources": sources, "cost_estimate": self._estimate_cost(report)}
          except Exception as e:
              logger.error(f"GPT-Researcher error: {e}")
              return {"report": f"Research failed: {str(e)}", "sources": [], "cost_estimate": 0.0}

      def _estimate_cost(self, report: str) -> float:
          tokens = len(report.split()) * 1.3
          return round(tokens / 1000 * 0.0015, 4)

      async def quick_search(self, query: str) -> str:
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
      logger.info(f"Deep research skill triggered: {query[:50]}")
      result = await _client.research(query, report_type=report_type)
      if not result["report"] or "failed" in result["report"].lower():
          return f"⚠️ Research gagal. Coba: /search {query}"
      report = result["report"]
      sources = result["sources"]
      max_len = 3500
      if len(report) > max_len:
          report = report[:max_len] + "\n\n_[Report dipotong. Full version tersimpan di memory.]_"
      source_lines = ""
      if sources:
          top_sources = sources[:3]
          source_lines = "\n\n📚 *Sources:*\n" + "\n".join(
              f"• {s.get('url', s) if isinstance(s, dict) else s}" for s in top_sources
          )
      cost_note = ""
      if result["cost_estimate"] > 0:
          cost_note = f"\n_~${result['cost_estimate']} API cost_"
      return f"🔬 *Deep Research: {query[:40]}*\n\n{report}{source_lines}{cost_note}"

  SKILL_META = {
      "name": SKILL_NAME,
      "description": SKILL_DESCRIPTION,
      "triggers": TRIGGER_KEYWORDS,
      "execute": execute,
      "requires_internet": True,
      "avg_latency_seconds": 30,
      "cost_tier": "medium",
  }

STEP 5 — Register in core/skills/registry.py
STEP 6 — Wire /research Telegram command
STEP 7 — Verify Tool 1

═════════════════════════════════════════════════════════════════════
TOOL 2 — DIFY (Replaces Claude Max for doc analysis + drafting)
═════════════════════════════════════════════════════════════════════

REPO: https://github.com/langgenius/dify (137k stars)
DOCS: https://docs.dify.ai

WHAT IT DOES:
  - Self-hosted AI workflow platform
  - RAG pipelines: ingest PDFs, legal docs, tax regulations
  - Long-context document analysis with ANY LLM backend
  - Workflow builder: chain research → draft → review → output
  - REST API — Legion calls it via HTTP

STEP 1 — Create docker/dify-compose.yml
STEP 2 — Add .env variables
STEP 3 — Create core/integrations/dify_client.py
STEP 4 — Create core/skills/dify_analysis.py
STEP 5 — Wire /draft Telegram command
STEP 6 — Verify Tool 2

═════════════════════════════════════════════════════════════════════
TOOL 3 — MARKITDOWN (Document → Markdown for any file format)
═════════════════════════════════════════════════════════════════════

REPO: https://github.com/microsoft/markitdown
INSTALL: pip install markitdown

WHAT IT DOES:
  - Converts ANY document to clean Markdown: PDF, DOCX, XLSX, PPTX, HTML,
    images (with OCR), audio (with transcription), EPUB, ZIP
  - Feeds output directly into LLM context or Dify RAG pipeline
  - Much better than pdfplumber for complex layouts

STEP 1 — Add to requirements.txt: markitdown[all]>=0.1.0
STEP 2 — Create core/skills/doc_parser.py
STEP 3 — Wire document handling in message handler
STEP 4 — Verify Tool 3

═════════════════════════════════════════════════════════════════════
FINAL STEP — Setup Script
═════════════════════════════════════════════════════════════════════

Create scripts/setup_external_tools.sh

═════════════════════════════════════════════════════════════════════
FINAL GATE — Run after all 3 tools implemented
═════════════════════════════════════════════════════════════════════

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

═════════════════════════════════════════════════════════════════════
HARD RULES
═════════════════════════════════════════════════════════════════════

1. Tool 1 (gpt-researcher) can work immediately — no Docker needed.
   Do this first as it has the most immediate value.
2. Tool 2 (Dify) requires Docker. If Docker not available: skip docker/dify-compose.yml. Still create dify_client.py (gracefully degrades when DIFY_API_KEY not set).
3. Tool 3 (markitdown) is pure Python. Do this after Tool 1.
4. Do NOT remove existing skills (web_search, arxiv, etc.). deep_research COMPLEMENTS web_search.
5. After each tool: run python scripts/verify_wiring.py
6. All new files must have: proper imports, async def, try/except, logger calls.
7. Every new env var must be added to .env.example with a comment.
```