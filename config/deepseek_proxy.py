#!/usr/bin/env python3
"""Anthropic → OpenAI translation proxy for DeepSeek via OpenCode API.
Runs alongside LiteLLM on a separate port. Handles tool conversion."""

import json
import os
import sys
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

OPENCODE_API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
OPENCODE_BASE = "https://opencode.ai/zen/go/v1"

app = FastAPI()

def anthropic_to_openai(body: dict) -> dict:
    """Convert Anthropic format messages to OpenAI format."""
    oai_messages = []
    system_content = body.get("system", "")
    
    if system_content:
        text = system_content[0]["text"] if isinstance(system_content, list) else system_content
        oai_messages.append({"role": "system", "content": text})
    
    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg.get("content", "")
        if isinstance(content, list):
            text_parts = [c["text"] for c in content if c.get("type") == "text"]
            content = "\n".join(text_parts) if text_parts else ""
        oai_messages.append({"role": role, "content": content})
    
    # Convert Anthropic tools to OpenAI functions
    oai_tools = []
    for tool in body.get("tools", []):
        oai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {})
            }
        })
    
    oai_body = {
        "model": body.get("model", "deepseek-v4-flash"),
        "messages": oai_messages,
        "max_tokens": body.get("max_tokens", 4096),
        "stream": body.get("stream", False),
    }
    if oai_tools:
        oai_body["tools"] = oai_tools
    
    return oai_body

def openai_to_anthropic(response: dict) -> dict:
    """Convert OpenAI format response to Anthropic format."""
    choice = response.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = msg.get("content", "") or ""
    
    # Handle reasoning content from DeepSeek
    reasoning = msg.get("reasoning_content", "")
    
    anthro = {
        "id": response.get("id", ""),
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content}],
        "model": response.get("model", ""),
        "stop_reason": choice.get("finish_reason", "end_turn"),
        "usage": {
            "input_tokens": response.get("usage", {}).get("prompt_tokens", 0),
            "output_tokens": response.get("usage", {}).get("completion_tokens", 0),
        }
    }
    return anthro

@app.post("/v1/messages")
async def proxy_messages(request: Request):
    body = await request.json()
    model = body.get("model", "")
    
    # MiniMax: pass through to LiteLLM (Anthropic format)
    if "minimax" in model.lower():
        headers = {k: v for k, v in request.headers.items() 
                   if k.lower() in ("content-type", "x-api-key", "anthropic-version")}
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                "http://127.0.0.1:4001/v1/messages",
                json=body,
                headers=headers
            )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    
    # DeepSeek: translate Anthropic → OpenAI, send to OpenCode
    oai_body = anthropic_to_openai(body)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENCODE_API_KEY}"
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{OPENCODE_BASE}/chat/completions",
            json=oai_body,
            headers=headers
        )
    
    if resp.status_code != 200:
        return JSONResponse(
            status_code=resp.status_code,
            content={"error": {"message": resp.text, "type": "error"}}
        )
    
    anthro_resp = openai_to_anthropic(resp.json())
    return anthro_resp

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="127.0.0.1", port=port)
