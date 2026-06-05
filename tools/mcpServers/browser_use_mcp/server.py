#!/usr/bin/env python3
"""
browser-use MCP Server — MiniMax-native browser automation via browser-use.

Exposes stable browser operations to OpenCode's MCP layer:
  open, click, fill, scroll, wait, screenshot, get_text, get_html, close, run_task

All LLM calls route directly to MiniMax API (https://api.minimax.io/v1).
The LiteLLM proxy is NOT used due to a known SDK-to-proxy "No connected db" bug.
Forbidden models (Claude, OpenAI, Gemini, etc.) are rejected at startup.

Usage:
    python -m tools.mcpServers.browser_use_mcp.server
    python tools/mcpServers/browser_use_mcp/server.py
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import sys
from typing import Any

logging.getLogger("browser_use").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("liteLLM").setLevel(logging.ERROR)

try:
    from mcp.server import FastMCP
except ImportError:
    print("ERROR: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

APP_NAME = "browser-use-mcp"
VERSION = "1.26.0"

MINIMAX_API_BASE = os.environ.get("MINIMAX_API_BASE", "https://api.minimax.io/v1")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_MODEL = "minimax-coding-plan/MiniMax-M3"

_FORBIDDEN = {"claude", "anthropic", "gpt-4", "gpt-5", "openai", "gemini", "groq", "together"}
if any(k in MINIMAX_MODEL.lower() for k in _FORBIDDEN):
    raise RuntimeError(
        f"[browser_use_mcp] Forbidden model: {MINIMAX_MODEL!r}. "
        "This MCP server is locked to MiniMax only. Aborting."
    )

mcp = FastMCP(
    name=APP_NAME,
    instructions="MiniMax-native browser automation via browser-use. "
    "Open URLs, click elements, fill forms, scroll, screenshot, and run autonomous browser tasks. "
    "All LLM calls use minimax-coding-plan/MiniMax-M3 exclusively.",
)


def _patch_litellm_for_minimax():
    from browser_use.llm.litellm import ChatLiteLLM

    async def ainvoke_patched(self, messages, output_format=None, **kwargs):
        from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
        from browser_use.llm.litellm.serializer import LiteLLMMessageSerializer
        from browser_use.llm.schema import SchemaOptimizer
        from browser_use.llm.views import ChatInvokeCompletion
        from litellm import acompletion
        from litellm.exceptions import APIConnectionError, APIError, RateLimitError, Timeout
        from litellm.types.utils import ModelResponse

        litellm_messages = LiteLLMMessageSerializer.serialize(messages)
        params: dict[str, Any] = {
            "model": self.model,
            "messages": litellm_messages,
            "num_retries": self.max_retries,
        }
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.api_key:
            params["api_key"] = self.api_key
        if self.api_base:
            params["api_base"] = self.api_base
        if self.metadata:
            params["metadata"] = self.metadata
        if output_format is not None:
            schema = SchemaOptimizer.create_optimized_json_schema(output_format)
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "agent_output",
                    "strict": True,
                    "schema": schema,
                },
            }
        try:
            raw_response = await acompletion(**params)
        except RateLimitError as e:
            raise ModelRateLimitError(message=str(e), model=self.name) from e
        except Timeout as e:
            raise ModelProviderError(message=f"Request timed out: {e}", model=self.name) from e
        except APIConnectionError as e:
            raise ModelProviderError(message=str(e), model=self.name) from e
        except APIError as e:
            status = getattr(e, "status_code", 502) or 502
            raise ModelProviderError(message=str(e), status_code=status, model=self.name) from e
        except ModelProviderError:
            raise
        except Exception as e:
            raise ModelProviderError(message=str(e), model=self.name) from e

        assert isinstance(raw_response, ModelResponse)
        response: ModelResponse = raw_response
        choice = response.choices[0] if response.choices else None
        if choice is None:
            raise ModelProviderError(
                message="Empty response: no choices returned by the model",
                status_code=502,
                model=self.name,
            )
        content = choice.message.content or ""
        usage = self._parse_usage(response)
        stop_reason = choice.finish_reason
        thinking: str | None = None
        reasoning = getattr(choice.message, "reasoning_content", None)
        if reasoning:
            thinking = str(reasoning)
        if output_format is not None:
            if not content:
                raise ModelProviderError(
                    message="Empty response for structured output",
                    status_code=500,
                    model=self.name,
                )
            try:
                parsed = output_format.model_validate_json(content)
                return ChatInvokeCompletion(
                    completion=parsed,
                    thinking=thinking,
                    usage=usage,
                    stop_reason=stop_reason,
                )
            except Exception:
                pass
            retry_params = dict(params)
            retry_params.pop("response_format", None)
            raw_response2 = await acompletion(**retry_params)
            assert isinstance(raw_response2, ModelResponse)
            choice2 = raw_response2.choices[0] if raw_response2.choices else None
            if choice2 is None:
                raise ModelProviderError(message="Empty response on retry", status_code=502, model=self.name)
            content2 = choice2.message.content or ""
            if not content2:
                raise ModelProviderError(message="Empty content on retry", status_code=500, model=self.name)
            try:
                parsed2 = output_format.model_validate_json(content2)
                return ChatInvokeCompletion(
                    completion=parsed2,
                    thinking=thinking,
                    usage=usage,
                    stop_reason=stop_reason,
                )
            except Exception:
                pass
            import json as _json
            import re as _re
            json_match = _re.search(r"\{[\s\S]*\}", content2)
            if json_match:
                try:
                    data = _json.loads(json_match.group())
                    parsed3 = output_format.model_validate(data)
                    return ChatInvokeCompletion(
                        completion=parsed3,
                        thinking=thinking,
                        usage=usage,
                        stop_reason=stop_reason,
                    )
                except Exception:
                    pass
            raise ModelProviderError(
                message=f"MiniMax output incompatible with AgentOutput schema: {content2[:300]}",
                status_code=500,
                model=self.name,
            )
        return ChatInvokeCompletion(
            completion=content,
            thinking=thinking,
            usage=usage,
            stop_reason=stop_reason,
        )

    ChatLiteLLM.ainvoke = ainvoke_patched


def _make_llm():
    _patch_litellm_for_minimax()
    from browser_use.llm.litellm import ChatLiteLLM

    llm = ChatLiteLLM(
        model=MINIMAX_MODEL,
        api_key=MINIMAX_API_KEY,
        api_base=MINIMAX_API_BASE,
        temperature=0.3,
        max_retries=3,
    )
    object.__setattr__(llm, "_provider_name", "browser-use")
    return llm


class BrowserSessionWrapper:
    def __init__(self, name: str = "default", headless: bool = True):
        self.name = name
        self.headless = headless
        self._session = None
        self._agent = None
        self._initialized = False

    @staticmethod
    def _escape_css_selector(selector: str) -> str:
        """Escape CSS selector to prevent injection attacks."""
        result = []
        for ch in selector:
            code = ord(ch)
            if code < 0x20 or code >= 0x7f:
                # Non-ASCII or control char: escape as unicode
                result.append(f"\\{format(code, 'x')} ")
            elif ch == "\\":
                result.append("\\\\")
            elif ch == "'":
                result.append("\\'")
            elif ch == '"':
                result.append('\\"')
            elif ch == "]":
                result.append("]")  # ] closes [attr] selectors, re-escaped below
            elif ch in ("[", "]", "(", ")", "{", "}", ":"):
                result.append(f"\\{ch}")
            else:
                result.append(ch)
        s = "".join(result)
        # Escape closing ] for attribute selectors
        s = s.replace("]", "\\]")
        return s

    async def _ensure(self):
        if self._initialized:
            return
        from browser_use import Agent
        from browser_use.browser.profile import BrowserProfile
        from browser_use.browser.session import BrowserSession

        bp = BrowserProfile(
            headless=self.headless,
            disable_security=False,
            extra_chromium_args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self._session = BrowserSession(browser_profile=bp, is_local=True)
        llm = _make_llm()
        self._agent = Agent(
            task="placeholder",
            llm=llm,
            browser=self._session,
            max_actions_per_step=5,
            enable_planning=False,
            use_thinking=False,
            max_failures=3,
        )
        self._initialized = True

    async def open(self, url: str) -> dict[str, Any]:
        await self._ensure()
        await self._session.start()
        page = await self._session.new_page()
        await page.goto(url)
        await asyncio.sleep(0.3)
        return {"url": await page.get_url(), "title": await page.get_title()}

    async def _get_page(self):
        page = await self._session.get_current_page()
        if not page:
            return None
        return page

    async def click(self, selector: str) -> dict[str, Any]:
        await self._ensure()
        page = await self._get_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        escaped = self._escape_css_selector(selector)
        js = f"() => {{ const el = document.querySelector('{escaped}'); if (!el) return 'not_found'; el.click(); return 'clicked'; }}"
        result = await page.evaluate(js)
        if result == "not_found":
            return {"error": f"Element not found: {selector}"}
        return {"success": True, "selector": selector}

    async def fill(self, selector: str, value: str) -> dict[str, Any]:
        await self._ensure()
        page = await self._get_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        escaped_sel = self._escape_css_selector(selector)
        escaped_val = json.dumps(value)[1:-1]  # JSON.dumps quotes and escapes ALL special chars
        js = f"() => {{ const el = document.querySelector('{escaped_sel}'); if (!el) return 'not_found'; el.value = '{escaped_val}'; el.dispatchEvent(new Event('input', {{bubbles: true}})); return 'filled'; }}"
        result = await page.evaluate(js)
        if result == "not_found":
            return {"error": f"Element not found: {selector}"}
        return {"success": True, "selector": selector, "value": value}

    async def scroll(self, pixels: int = 300) -> dict[str, Any]:
        await self._ensure()
        page = await self._get_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        await page.evaluate(f"() => window.scrollBy(0, {pixels})")
        return {"success": True, "pixels": pixels}

    async def wait(self, seconds: float = 1.0) -> dict[str, Any]:
        await asyncio.sleep(seconds)
        return {"success": True, "waited": seconds}

    async def screenshot(self, path: str) -> dict[str, Any]:
        await self._ensure()
        page = await self._get_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        import base64

        # SECURITY: Validate path is within allowed directories
        allowed_base = os.environ.get("ALLOWED_SCREENSHOT_DIRS", "")
        if allowed_base:
            allowed_dirs = [os.path.abspath(d.strip()) for d in allowed_base.split(":") if d.strip()]
            target_abs = os.path.abspath(path)
            if not any(target_abs.startswith(d + os.sep) or target_abs == d for d in allowed_dirs):
                return {"error": f"Path outside allowed directories: {path}"}

        img_data = await page.screenshot()
        if isinstance(img_data, str):
            img_data = base64.b64decode(img_data)

        # Ensure parent directory exists
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(path, "wb") as f:
            f.write(img_data)
        return {"success": True, "path": path}

    async def get_text(self, selector: str = "body") -> dict[str, Any]:
        await self._ensure()
        page = await self._get_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        escaped = self._escape_css_selector(selector)
        js = f"() => document.querySelector('{escaped}')?.innerText || ''"
        text = await page.evaluate(js)
        return {"text": text, "selector": selector}

    async def get_html(self, selector: str = "body") -> dict[str, Any]:
        await self._ensure()
        page = await self._get_page()
        if not page:
            return {"error": "No active page. Call open() first."}
        escaped = self._escape_css_selector(selector)
        js = f"() => document.querySelector('{escaped}')?.innerHTML || ''"
        html = await page.evaluate(js)
        return {"html": html, "selector": selector}

    async def close(self) -> dict[str, Any]:
        if self._session:
            with contextlib.suppress(Exception):
                await self._session.kill()
            self._session = None
        self._initialized = False
        return {"success": True, "session": self.name}

    async def run_task(self, task: str, max_steps: int = 20) -> dict[str, Any]:
        await self._ensure()
        self._agent.task = task
        result = await self._agent.run(max_steps=max_steps)
        fr = result.final_result() if hasattr(result, "final_result") else str(result)
        return {"success": True, "result": fr or "Task completed", "steps": max_steps}


_sessions: dict[str, BrowserSessionWrapper] = {}


def _get_session(name: str = "default") -> BrowserSessionWrapper:
    if name not in _sessions:
        _sessions[name] = BrowserSessionWrapper(name=name)
    return _sessions[name]


@mcp.tool()
async def browser_open(url: str, session: str = "default") -> str:
    """Open a URL in the browser."""
    result = await _get_session(session).open(url)
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_click(selector: str, session: str = "default") -> str:
    """Click an element by CSS selector."""
    result = await _get_session(session).click(selector)
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_fill(selector: str, value: str, session: str = "default") -> str:
    """Fill an input field by CSS selector."""
    result = await _get_session(session).fill(selector, value)
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_scroll(pixels: int = 300, session: str = "default") -> str:
    """Scroll the page by pixels."""
    result = await _get_session(session).scroll(pixels)
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_wait(seconds: float = 1.0, session: str = "default") -> str:
    """Wait for seconds."""
    result = await _get_session(session).wait(seconds)
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_screenshot(path: str, session: str = "default") -> str:
    """Take a screenshot and save to path."""
    result = await _get_session(session).screenshot(path)
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_get_text(selector: str = "body", session: str = "default") -> str:
    """Get text from element or body."""
    result = await _get_session(session).get_text(selector)
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_get_html(selector: str = "body", session: str = "default") -> str:
    """Get inner HTML from element or body."""
    result = await _get_session(session).get_html(selector)
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_close(session: str = "default") -> str:
    """Close the browser session."""
    result = await _get_session(session).close()
    return json.dumps(result, indent=2)


@mcp.tool()
async def browser_run_task(task: str, max_steps: int = 20, session: str = "default") -> str:
    """Run autonomous browser task powered by MiniMax."""
    result = await _get_session(session).run_task(task, max_steps)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
