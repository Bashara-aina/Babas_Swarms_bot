#!/usr/bin/env python3
"""muse-responses-shim — translate OpenAI chat-completions <-> zen/go /responses.

Why: OpenCode Go serves muse-spark-1.3-contributor ONLY on the Responses API
(https://opencode.ai/zen/go/v1/responses per https://opencode.ai/docs/go/).
Our LiteLLM proxy speaks chat-completions upstream, which zen answers with
HTTP 500 for this model. This shim accepts chat-completions (JSON + SSE
streaming) on :4002 and forwards as Responses API with the required
x-opencode-session header, translating back.

Endpoints: POST /v1/chat/completions, GET /v1/models, GET /healthz
Stdlib only. Never logs secrets.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ZEN_RESPONSES_URL = "https://opencode.ai/zen/go/v1/responses"
SESSION_ID = os.environ.get("OPENCODE_GO_SESSION_ID", "8f599165-54d8-415c-b58b-60ba1f421a7c")
DEFAULT_EFFORT = "xhigh"
UPSTREAM_TIMEOUT = 300

# NOTE: read lazily so the process can start before .env is sourced elsewhere.
_API_KEY = {}


def api_key() -> str:
    if "k" not in _API_KEY:
        _API_KEY["k"] = os.environ.get("OPENCODE_GO_API_KEY", "")
    return _API_KEY["k"]


# ---------- chat -> responses ----------

def to_input_item(msg: dict) -> list:
    role = msg.get("role", "user")
    content = msg.get("content")
    if role == "system":
        role = "developer"
    if role == "assistant" and msg.get("tool_calls"):
        items = []
        text = content if isinstance(content, str) else ""
        if text:
            items.append({"type": "message", "role": "assistant",
                          "content": [{"type": "output_text", "text": text}]})
        for tc in msg["tool_calls"]:
            fn = tc.get("function", {})
            items.append({"type": "function_call", "call_id": tc.get("id", ""),
                          "name": fn.get("name", ""), "arguments": fn.get("arguments", "") or ""})
        return items
    if role == "tool":
        out = content if isinstance(content, str) else json.dumps(content)
        return [{"type": "function_call_output", "call_id": msg.get("tool_call_id", ""), "output": out}]
    if isinstance(content, list):  # multipart (text + images)
        parts = []
        for p in content:
            if p.get("type") == "image_url":
                parts.append({"type": "input_image",
                              "image_url": p["image_url"].get("url", "")})
            elif "text" in p:
                parts.append({"type": "input_text", "text": p["text"]})
        return [{"type": "message", "role": role, "content": parts}]
    return [{"type": "message", "role": role, "content": str(content or "")}]


def to_function_tool(t: dict) -> dict | None:
    if t.get("type") != "function":
        return None
    fn = t.get("function", {})
    return {"type": "function", "name": fn.get("name", ""),
            "description": (fn.get("description") or "")[:500],
            "parameters": fn.get("parameters") or {"type": "object", "properties": {}}}


def build_responses_body(chat: dict, stream: bool) -> dict:
    items: list = []
    for m in chat.get("messages", []):
        items.extend(to_input_item(m))
    body: dict = {"model": "muse-spark-1.3-contributor", "input": items, "stream": stream}
    tools = [ft for ft in (to_function_tool(t) for t in chat.get("tools", []) or []) if ft]
    if tools:
        body["tools"] = tools
    effort = chat.get("reasoning_effort") or DEFAULT_EFFORT
    if effort:
        body["reasoning"] = {"effort": effort}
    if chat.get("max_tokens") is not None:
        body["max_output_tokens"] = chat["max_tokens"]
    if chat.get("temperature") is not None:
        body["temperature"] = chat["temperature"]
    if chat.get("top_p") is not None:
        body["top_p"] = chat["top_p"]
    return body


def post_upstream(body: dict, stream: bool):
    req = urllib.request.Request(
        ZEN_RESPONSES_URL, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + api_key(),
                 "x-opencode-session": SESSION_ID,
                 "User-Agent": "oc-cc-proxy/1.0"})
    return urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT)


# ---------- responses -> chat ----------

def output_to_message(output: list) -> tuple[str, list]:
    text_parts, calls = [], []
    for item in output:
        t = item.get("type")
        if t == "message":
            for c in item.get("content", []):
                if c.get("type") in ("output_text", "text") and c.get("text"):
                    text_parts.append(c["text"])
        elif t == "function_call":
            calls.append({"id": item.get("call_id", ""), "type": "function",
                          "function": {"name": item.get("name", ""),
                                       "arguments": item.get("arguments", "") or ""}})
    return "".join(text_parts), calls


def chat_response(model: str, text: str, calls: list, usage: dict) -> dict:
    msg: dict = {"role": "assistant", "content": text}
    finish = "stop"
    if calls:
        msg["tool_calls"] = calls
        finish = "tool_calls"
    return {"id": "chatcmpl-shim-%d" % int(time.time() * 1000),
            "object": "chat.completion", "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "message": msg, "finish_reason": finish}],
            "usage": {"prompt_tokens": (usage or {}).get("input_tokens", 0),
                      "completion_tokens": (usage or {}).get("output_tokens", 0),
                      "total_tokens": (usage or {}).get("total_tokens", 0)}}


def sse_chunk(model: str, delta: dict, finish: str | None = None) -> bytes:
    return ("data: " + json.dumps(
        {"id": "chatcmpl-shim-s", "object": "chat.completion.chunk",
         "created": int(time.time()), "model": model,
         "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}) + "\n\n").encode()


class Handler(BaseHTTPRequestHandler):
    server_version = "muse-shim/1.0"

    def log_message(self, fmt, *args):  # quieter access log
        pass

    def _send(self, code: int, obj: dict):
        raw = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        if self.path == "/v1/models":
            return self._send(200, {"object": "list", "data": [
                {"id": "muse-spark-1.3-contributor", "object": "model"}]})
        return self._send(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            return self._send(404, {"error": {"message": "not found"}})
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            chat = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._send(400, {"error": {"message": "invalid JSON"}})
        model = chat.get("model", "muse-spark-1.3-contributor")
        stream = bool(chat.get("stream"))
        t0 = time.time()
        try:
            if not stream:
                try:
                    resp = post_upstream(build_responses_body(chat, False), False)
                    d = json.loads(resp.read().decode())
                except urllib.error.HTTPError as e:
                    return self._send(e.code, {"error": {"message": e.read().decode()[:500]}})
                text, calls = output_to_message(d.get("output", []))
                self._send(200, chat_response(model, text, calls, d.get("usage", {})))
                print(f"ok nonstream model={model} tools={len(calls)} ms={int((time.time()-t0)*1000)}", flush=True)
                return
            # streaming: translate responses SSE -> chat chunks
            try:
                resp = post_upstream(build_responses_body(chat, True), True)
            except urllib.error.HTTPError as e:
                return self._send(e.code, {"error": {"message": e.read().decode()[:500]}})
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            tool_index: dict = {}
            usage: dict = {}
            buf = b""
            for raw in resp:
                buf += raw
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line.startswith(b"data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == b"[DONE]":
                        continue
                    try:
                        ev = json.loads(payload)
                    except Exception:
                        continue
                    et = ev.get("type", "")
                    if et == "response.output_text.delta":
                        self.wfile.write(sse_chunk(model, {"content": ev.get("delta", "")}))
                    elif et == "response.function_call_arguments.delta":
                        idx = tool_index.setdefault(ev.get("item_id", "0"), len(tool_index))
                        self.wfile.write(sse_chunk(model, {"tool_calls": [
                            {"index": idx, "function": {"arguments": ev.get("delta", "")}}]}))
                    elif et == "response.output_item.done":
                        item = ev.get("item", {})
                        if item.get("type") == "function_call":
                            idx = tool_index.setdefault(item.get("id", "0"), len(tool_index))
                            self.wfile.write(sse_chunk(model, {"tool_calls": [
                                {"index": idx, "id": item.get("call_id", ""),
                                 "type": "function",
                                 "function": {"name": item.get("name", ""), "arguments": ""}}]}))
                    elif et == "response.completed":
                        usage = ((ev.get("response") or {}).get("usage")) or {}
                    elif et == "response.failed":
                        self.wfile.write(sse_chunk(model, {}, "error"))
            self.wfile.write(sse_chunk(model, {}, "stop"))
            self.wfile.write(b"data: [DONE]\n\n")
            print(f"ok stream model={model} tools={len(tool_index)} ms={int((time.time()-t0)*1000)}", flush=True)
        except BrokenPipeError:
            pass
        except Exception as e:  # noqa: BLE001 - translate to chat error
            try:
                self._send(500, {"error": {"message": f"shim: {str(e)[:300]}"}})
            except Exception:
                pass


if __name__ == "__main__":
    port = int(os.environ.get("MUSE_SHIM_PORT", "4002"))
    if not api_key():
        print("ERROR: OPENCODE_GO_API_KEY is not set.", flush=True)
        raise SystemExit(1)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"muse-responses-shim on http://127.0.0.1:{port} -> {ZEN_RESPONSES_URL}", flush=True)
    srv.serve_forever()
