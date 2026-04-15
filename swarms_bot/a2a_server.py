"""
A2A (Agent-to-Agent) protocol server for Legion Bot.
Exposes Legion's 84 agents as A2A-discoverable endpoints via FastAPI.

Based on google/a2a protocol spec.
Agent card published at /.well-known/agent.json.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class A2AMessage(BaseModel):
    """Incoming A2A JSON-RPC 2.0 message."""

    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any]
    id: str | None = None


class A2AResponse(BaseModel):
    """Outgoing A2A JSON-RPC 2.0 response."""

    jsonrpc: str = "2.0"
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    id: str | None = None


AGENT_CARD = {
    "name": "Legion",
    "description": (
        "Bashara's permanent AI coworker — 84 specialized agents across 9 departments. "
        "Handles coding, research, browser automation, debate, memory, communications, "
        "computer control, and more."
    ),
    "version": "1.0.0",
    "capabilities": {"streaming": True, "pushNotifications": False},
    "skills": [
        {
            "id": "coding",
            "name": "Coding Agent",
            "description": "Python, TypeScript, SQL generation and debugging",
        },
        {
            "id": "research",
            "name": "Research Agent",
            "description": "Academic research, arXiv papers, web research, citations",
        },
        {
            "id": "browser",
            "name": "Browser Agent",
            "description": "Autonomous web browsing via Playwright",
        },
        {
            "id": "debate",
            "name": "Debate Agent",
            "description": "Dialectical reasoning, structured debate on any topic",
        },
        {
            "id": "memory",
            "name": "Memory Agent",
            "description": "Semantic recall, episodic memory, preference learning",
        },
        {
            "id": "computer",
            "name": "Computer Control Agent",
            "description": "Desktop automation — screen, click, type, shell commands",
        },
    ],
    "authentication": {"type": "api_key", "api_key_field": "X-Legion-Key"},
    "endpoint": f"https://{os.getenv('DOMAIN', 'localhost')}:7835/a2a",
}

app = FastAPI(title="Legion A2A Server", version="1.0.0")


@app.get("/.well-known/agent.json", response_model=dict)
async def agent_card() -> dict:
    """Agent discovery endpoint — returns the public agent card."""
    return AGENT_CARD


@app.post("/a2a", response_model=A2AResponse)
async def a2a_endpoint(message: A2AMessage) -> A2AResponse:
    """
    Main A2A endpoint. Routes incoming tasks to the appropriate agent.
    """
    api_key = os.getenv("LEGION_A2A_API_KEY", "")
    # TODO: Validate X-Legion-Key header against LEGION_A2A_API_KEY

    try:
        skill_id = message.params.get("skill", "general")
        input_data = message.params.get("input", {})
        task = input_data.get("task", "")

        # Route through nexus orchestrator
        from core.nexus_orchestrator import NexusOrchestrator

        orchestrator = NexusOrchestrator()
        result = await orchestrator.route(
            agent_key=skill_id,
            task=task,
            context=input_data,
        )

        return A2AResponse(
            result={
                "status": "success",
                "agent": skill_id,
                "output": str(result)[:2000],
                "session_id": str(uuid.uuid4()),
            },
            id=message.id,
        )

    except Exception as e:
        return A2AResponse(
            error={"code": -32603, "message": str(e)},
            id=message.id,
        )


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "agents": len(AGENT_CARD["skills"])}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7835)
