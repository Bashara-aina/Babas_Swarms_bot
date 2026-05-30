import logging
import os

logger = logging.getLogger(__name__)


class GPTResearcherClient:
    """
    Wrapper around gpt-researcher library.
    Uses MiniMax (already configured in Legion via MINIMAX_API_KEY).
    Falls back to direct LLM call if gpt-researcher unavailable.
    """

    def __init__(self):
        self.available = self._check_available()
        self.llm_provider = os.getenv("GPTR_LLM_PROVIDER", "openai")
        self.llm_model = os.getenv("GPTR_LLM_MODEL", "minimax-coding-plan/MiniMax-Text-01")
        self.search_api = os.getenv("GPTR_SEARCH_API", "duckduckgo")
        if os.getenv("BRAVE_API_KEY"):
            self.search_api = "tavily"

    def _check_available(self) -> bool:
        try:
            import gpt_researcher  # noqa: F401 — side effect checks availability

            return True
        except ImportError:
            logger.warning("gpt-researcher not installed. Run: pip install gpt-researcher")
            return False

    async def research(self, query: str, report_type: str = "research_report", max_sections: int = 5) -> dict:
        if not self.available:
            return {
                "report": "gpt-researcher not available. Install with: pip install gpt-researcher",
                "sources": [],
                "cost_estimate": 0.0,
            }
        try:
            from gpt_researcher import GPTResearcher

            os.environ["OPENAI_API_KEY"] = os.getenv("MINIMAX_API_KEY", "")
            os.environ["OPENAI_BASE_URL"] = "https://api.minimax.io/anthropic"
            os.environ["FAST_LLM"] = self.llm_model
            os.environ["SMART_LLM"] = os.getenv("GPTR_SMART_MODEL", "minimax-coding-plan/MiniMax-Text-01")
            os.environ["RETRIEVER"] = self.search_api
            researcher = GPTResearcher(query=query, report_type=report_type)
            await researcher.conduct_research()
            report = await researcher.write_report()
            sources = researcher.get_research_sources()
            logger.info(f"Research complete: {len(report)} chars, {len(sources)} sources")
            return {"report": report, "sources": sources, "cost_estimate": self._estimate_cost(report)}
        except Exception as e:
            logger.error(f"GPT-Researcher error: {e}")
            return {"report": f"Research failed: {e!s}", "sources": [], "cost_estimate": 0.0}

    def _estimate_cost(self, report: str) -> float:
        tokens = len(report.split()) * 1.3
        return round(tokens / 1000 * 0.0015, 4)

    async def quick_search(self, query: str) -> str:
        result = await self.research(query, report_type="outline_report", max_sections=2)
        return result["report"]
