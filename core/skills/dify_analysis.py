import logging
from core.integrations.dify_client import DifyClient

logger = logging.getLogger(__name__)
_client = DifyClient()

SKILL_NAME = "dify_analysis"
SKILL_DESCRIPTION = "Long-form document analysis and drafting via Dify. Use for: legal drafting, complex analysis, document review, structured report generation."
TRIGGER_KEYWORDS = [
    "draft",
    "tulis",
    "buat dokumen",
    "analisis dokumen",
    "review kontrak",
    "legal",
    "compliance",
    "ToS",
    "disclaimer",
    "laporan panjang",
]

WORKFLOW_MAP = {
    "legal_draft": "",
    "doc_analysis": "",
    "report_draft": "",
    "default": "",
}


async def execute(task_type: str, content: str, workflow_id: str = "") -> str:
    if not _client.available:
        return (
            "⚠️ Dify belum disetup.\n"
            "Setup: `docker compose -f docker/dify-compose.yml up -d`\n"
            "Lalu set DIFY_API_KEY di .env"
        )
    wf_id = workflow_id or WORKFLOW_MAP.get(task_type, WORKFLOW_MAP["default"])
    if not wf_id:
        result = await _client.chat(app_id=WORKFLOW_MAP["default"], message=content)
        return result["answer"]
    result = await _client.run_workflow(workflow_id=wf_id, inputs={"content": content, "task_type": task_type})
    return result["output"]


SKILL_META = {
    "name": SKILL_NAME,
    "description": SKILL_DESCRIPTION,
    "triggers": TRIGGER_KEYWORDS,
    "execute": execute,
    "requires_internet": True,
    "avg_latency_seconds": 15,
    "cost_tier": "low",
}


def _register_dify_analysis_skill() -> None:
    from core.skills.registry import SKILL_REGISTRY, Skill

    SKILL_REGISTRY.register(
        Skill(
            name=SKILL_NAME,
            description=SKILL_DESCRIPTION,
            trigger_keywords=TRIGGER_KEYWORDS,
            handler=execute,
            required_env_keys=["DIFY_API_KEY"],
            category="general",
        )
    )


_register_dify_analysis_skill()
