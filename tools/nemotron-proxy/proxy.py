#!/usr/bin/env python3
"""
Dual-model proxy: routes Anthropic /v1/messages to either:

  model=nemotron         → Anthropic→OpenAI translation → LiteLLM port 4000 → OpenRouter
  model=minimax/MiniMax-M3 → Passthrough to Headroom (api.minimax.io/anthropic)

Both streaming and non-streaming are supported.

Usage:
    python3 proxy.py [--port PORT]
"""
import argparse
import asyncio
import json
import logging
import os
import uuid

import aiohttp

# ── Configuration ────────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = int(os.environ.get("PROXY_PORT", "4001"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Upstream for Nemotron (LiteLLM OpenAI endpoint)
NEMOTRON_UPSTREAM = os.environ.get("NEMOTRON_UPSTREAM", "http://localhost:4000")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Upstream for MiniMax (Headroom Anthropic endpoint)
MINIMAX_API_URL = os.environ.get("MINIMAX_API_URL", "https://api.minimax.io/anthropic")
MINIMAX_KEY = os.environ.get("MINIMAX_API_KEY", "")

log = logging.getLogger("model-proxy")

# Models that use the Nemotron path (Anthropic→OpenAI translation)
NEMOTRON_MODELS = {"nemotron", "nvidia/nemotron-3-ultra-550b-a55b:free"}
# Models that use the MiniMax passthrough (Anthropic → Headroom)
MINIMAX_MODELS = {
    "minimax/MiniMax-M3", "MiniMax-M3",
    # Map common Claude Code model names → MiniMax
    "claude-sonnet-4-20250514", "claude-sonnet-4",
    "claude-3.5-sonnet", "claude-3-opus",
    "claude-opus-4-20250514", "claude-opus-4",
    "claude-haiku", "claude-3-haiku",
}


# ── Router ───────────────────────────────────────────────────────────────────

def get_route(model: str) -> str:
    """Return 'nemotron' or 'minimax' based on the model name."""
    if model in NEMOTRON_MODELS:
        return "nemotron"
    if model in MINIMAX_MODELS:
        return "minimax"
    # Default to MiniMax (useful one); explicitly use "nemotron" model for Nemotron
    return "minimax"


# ── Nemotron: Anthropic → OpenAI translation ─────────────────────────────────

def anthropic_request_to_openai(body: dict) -> dict:
    """Convert an Anthropic /v1/messages request to OpenAI /v1/chat/completions."""
    messages = []

    if "system" in body:
        system_text = body["system"]
        if isinstance(system_text, list):
            system_text = " ".join(b["text"] for b in system_text if b.get("type") == "text")
        messages.append({"role": "system", "content": system_text})

    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if block.get("type") == "text":
                    text_parts.append(block["text"])
                elif block.get("type") == "image":
                    log.warning("Image content blocks not supported, skipping")
            content = " ".join(text_parts)
        messages.append({"role": role, "content": content})

    oai_body = {
        "model": "nemotron",
        "messages": messages,
        "stream": body.get("stream", False),
        "max_tokens": body.get("max_tokens", 4096),
    }
    for key in ("temperature", "top_p", "stop"):
        if key in body:
            oai_body[key] = body[key]
    if "stop_sequences" in body:
        oai_body["stop"] = body["stop_sequences"]

    return oai_body


def make_anthropic_message_id() -> str:
    return f"msg_{uuid.uuid4().hex[:24]}"


async def nemotron_nonstream(request_json: dict) -> dict:
    """Non-streaming Nemotron: translate, call LiteLLM, translate back."""
    oai_body = anthropic_request_to_openai(request_json)
    oai_body["stream"] = False

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENROUTER_KEY}"}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{NEMOTRON_UPSTREAM}/v1/chat/completions",
            headers=headers, json=oai_body,
            timeout=aiohttp.ClientTimeout(total=300),
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                log.error(f"Nemotron upstream error {resp.status}: {error_text}")
                return {"type": "error", "error": {"type": "api_error", "message": f"Upstream returned {resp.status}"}}
            oai_result = await resp.json()

    choice = oai_result.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content_text = msg.get("content", "")
    finish = choice.get("finish_reason", "stop")
    usage = oai_result.get("usage", {})

    return {
        "id": make_anthropic_message_id(),
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content_text}],
        "model": request_json.get("model", "nemotron"),
        "stop_reason": "end_turn" if finish == "stop" else finish,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


async def nemotron_stream(request_json: dict, writer) -> None:
    """Streaming Nemotron: translate, stream from LiteLLM SSE, emit Anthropic SSE."""
    oai_body = anthropic_request_to_openai(request_json)
    oai_body["stream"] = True

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENROUTER_KEY}"}
    msg_id = make_anthropic_message_id()
    full_content = ""
    stop_reason = "end_turn"

    async def sse(data: str) -> None:
        writer.write(data.encode())
        await writer.drain()

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{NEMOTRON_UPSTREAM}/v1/chat/completions",
            headers=headers, json=oai_body,
            timeout=aiohttp.ClientTimeout(total=300),
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                log.error(f"Nemotron upstream error {resp.status}: {error_text}")
                await sse(f"event: error\ndata: {json.dumps({'error': {'message': f'Upstream error: {resp.status}'}})}\n\n")
                return

            # message_start
            await sse(f"event: message_start\ndata: {json.dumps({
                'type': 'message_start', 'message': {
                    'id': msg_id, 'type': 'message', 'role': 'assistant',
                    'content': [], 'model': request_json.get('model', 'nemotron'),
                    'stop_reason': None, 'stop_sequence': None,
                    'usage': {'input_tokens': 0, 'output_tokens': 0},
                },
            })}\n\n")

            # content_block_start
            await sse(f"event: content_block_start\ndata: {json.dumps({
                'type': 'content_block_start', 'index': 0,
                'content_block': {'type': 'text', 'text': ''},
            })}\n\n")

            # Stream chunks
            while True:
                line_bytes = await resp.content.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8").strip()
                if not line or line.startswith(":"):
                    continue
                if line == "data: [DONE]":
                    break
                if line.startswith("data: "):
                    try:
                        chunk = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    finish = choices[0].get("finish_reason")
                    if not content and not finish:
                        continue
                    if content:
                        full_content += content
                        await sse(f"event: content_block_delta\ndata: {json.dumps({
                            'type': 'content_block_delta', 'index': 0,
                            'delta': {'type': 'text_delta', 'text': content},
                        })}\n\n")
                    if finish:
                        stop_reason = "end_turn" if finish == "stop" else finish

            # content_block_stop
            await sse(f"event: content_block_stop\ndata: {json.dumps({
                'type': 'content_block_stop', 'index': 0,
            })}\n\n")

            # message_delta
            await sse(f"event: message_delta\ndata: {json.dumps({
                'type': 'message_delta', 'delta': {
                    'stop_reason': stop_reason, 'stop_sequence': None,
                },
                'usage': {'output_tokens': len(full_content.split())},
            })}\n\n")


# ── MiniMax: passthrough to Headroom ─────────────────────────────────────────

async def minimax_passthrough(body: dict, writer, is_stream: bool) -> None:
    """Passthrough Anthropic Messages API → Headroom (api.minimax.io/anthropic).

    Headroom already speaks Anthropic Messages API, so we just forward the
    request as-is and pass through the response unchanged (streaming or not).
    """
    upstream_url = f"{MINIMAX_API_URL}/v1/messages"
    upstream_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINIMAX_KEY}",
        "anthropic-version": "2023-06-01",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            upstream_url,
            headers=upstream_headers,
            json=body,
            timeout=aiohttp.ClientTimeout(total=300),
        ) as resp:
            if is_stream:
                if resp.status != 200:
                    error_text = await resp.text()
                    log.error(f"MiniMax upstream error {resp.status}: {error_text}")
                    await send_json_response(writer, resp.status, {
                        "error": {"message": f"MiniMax upstream error: {error_text[:200]}"}
                    })
                    return

                # Stream mode: pass through SSE events as-is
                response_headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/event-stream\r\n"
                    "Cache-Control: no-cache\r\n"
                    "Connection: keep-alive\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    "x-request-id: " + uuid.uuid4().hex + "\r\n"
                    "\r\n"
                ).encode()
                writer.write(response_headers)
                await writer.drain()

                async for line_bytes, _ in resp.content.iter_chunks():
                    writer.write(line_bytes)
                    await writer.drain()
            else:
                # Non-streaming: pass through JSON response as-is
                body_bytes = await resp.read()
                response = (
                    f"HTTP/1.1 {resp.status} {'OK' if resp.status == 200 else 'Error'}\r\n"
                    f"Content-Type: application/json\r\n"
                    f"Content-Length: {len(body_bytes)}\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    f"x-request-id: {uuid.uuid4().hex}\r\n"
                    "\r\n"
                ).encode() + body_bytes
                writer.write(response)
                await writer.drain()


# ── HTTP Handler ─────────────────────────────────────────────────────────────

async def handle_request(reader, writer):
    """Handle a single HTTP connection."""
    try:
        request_data = await read_http_request(reader)
        if not request_data:
            return

        method, path, headers, body_bytes = request_data

        if path == "/v1/messages" and method == "POST":
            await handle_messages(body_bytes, headers, writer)
        elif path == "/health" and method == "GET":
            await send_json_response(writer, 200, {"status": "healthy", "proxy": "model-proxy"})
        elif path == "/v1/models" and method == "GET":
            await send_json_response(writer, 200, {
                "data": [
                    {"id": "MiniMax-M3", "object": "model", "created": 1677610602, "owned_by": "minimax"},
                    {"id": "minimax/MiniMax-M3", "object": "model", "created": 1677610602, "owned_by": "minimax"},
                    {"id": "nemotron", "object": "model", "created": 1677610602, "owned_by": "openrouter"},
                ]
            })
        else:
            await send_json_response(writer, 404, {"error": {"message": "Not found"}})
    except Exception as e:
        log.exception(f"Request handler error: {e}")
        try:
            await send_json_response(writer, 500, {"error": {"message": f"Internal error: {str(e)}"}})
        except Exception:
            pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle_messages(body_bytes: bytes, headers: dict, writer):
    """Route POST /v1/messages to the correct backend based on model."""
    try:
        body = json.loads(body_bytes)
    except json.JSONDecodeError:
        await send_json_response(writer, 400, {"error": {"message": "Invalid JSON"}})
        return

    model = body.get("model", "nemotron")
    route = get_route(model)
    is_stream = body.get("stream", False)

    log.info(f"Routing model={model!r} route={route} stream={is_stream}")

    if route == "minimax":
        # MiniMax → passthrough to Headroom
        body["model"] = "minimax/MiniMax-M3"
        await minimax_passthrough(body, writer, is_stream)
        return

    # Nemotron → Anthropic→OpenAI translation
    if is_stream:
        response_headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/event-stream\r\n"
            "Cache-Control: no-cache\r\n"
            "Connection: keep-alive\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "x-request-id: " + uuid.uuid4().hex + "\r\n"
            "\r\n"
        ).encode()
        writer.write(response_headers)
        await writer.drain()
        await nemotron_stream(body, writer)
        await writer.drain()
    else:
        result = await nemotron_nonstream(body)
        body_json = json.dumps(result)
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: " + str(len(body_json)) + "\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "x-request-id: " + uuid.uuid4().hex + "\r\n"
            "\r\n"
            + body_json
        )
        writer.write(response.encode())
        await writer.drain()


# ── Low-level HTTP parsing ───────────────────────────────────────────────────

async def read_http_request(reader):
    """Read an HTTP/1.1 request from the stream."""
    request_line = await read_line(reader)
    if not request_line:
        return None
    parts = request_line.split(" ")
    if len(parts) < 2:
        return None
    method = parts[0]
    path = parts[1]

    headers = {}
    while True:
        line = await read_line(reader)
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
        elif not line:
            break

    content_length = int(headers.get("content-length", 0))
    body = b""
    if content_length > 0:
        body = await reader.readexactly(content_length)

    return method, path, headers, body


async def read_line(reader):
    """Read a line from the stream."""
    data = b""
    while True:
        ch = await reader.read(1)
        if not ch:
            break
        if ch == b"\r":
            await reader.read(1)
            break
        if ch == b"\n":
            break
        data += ch
    return data.decode("utf-8", errors="replace")


async def send_json_response(writer, status_code: int, data: dict):
    """Send an HTTP JSON response."""
    body = json.dumps(data)
    status_text = {200: "OK", 400: "Bad Request", 404: "Not Found", 500: "Internal Server Error"}.get(status_code, "Unknown")
    response = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        f"x-request-id: {uuid.uuid4().hex}\r\n"
        "\r\n"
        f"{body}"
    )
    writer.write(response.encode())
    await writer.drain()


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Dual-model proxy for Nemotron + MiniMax")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port to listen on (default: {PORT})")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s %(levelname)s %(message)s")

    server = await asyncio.start_server(handle_request, HOST, args.port)
    addr = server.sockets[0].getsockname()
    log.info(f"Model proxy listening on {addr[0]}:{addr[1]}")
    log.info(f"  Nemotron upstream: {NEMOTRON_UPSTREAM}")
    log.info(f"  MiniMax upstream:  {MINIMAX_API_URL}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
