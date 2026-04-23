import logging
import os
from typing import Optional

import aiohttp

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

    async def run_workflow(self, workflow_id: str, inputs: dict, user_id: str = "legion") -> dict:
        if not self.available:
            return {"output": "Dify not configured.", "status": "unavailable"}
        url = f"{self.base_url}/v1/workflows/run"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"inputs": inputs, "response_mode": "blocking", "user": user_id}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
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

    async def chat(
        self, app_id: str, message: str, conversation_id: Optional[str] = None, user_id: str = "legion"
    ) -> dict:
        if not self.available:
            return {"answer": "Dify not configured.", "conversation_id": None}
        url = f"{self.base_url}/v1/chat-messages"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
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
                async with session.post(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error(f"Dify chat error {resp.status}: {error}")
                        return {"answer": f"Dify error: {resp.status}", "conversation_id": None}
                    data = await resp.json()
                    return {"answer": data.get("answer", ""), "conversation_id": data.get("conversation_id")}
        except Exception as e:
            logger.error(f"Dify chat error: {e}")
            return {"answer": f"Dify unavailable: {e}", "conversation_id": None}

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return resp.status == 200
        except Exception:
            return False
