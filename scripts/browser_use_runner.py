"""
browser_use_runner — MiniMax-native browser-use execution layer.

All LLM calls go directly to MiniMax API (https://api.minimax.io/v1),
bypassing the LiteLLM proxy which has a known SDK-to-proxy bug.

Usage:
    python -m scripts.browser_use_runner --task "Find X on example.com" [--max-steps 20] [--headless]
    python -c "from scripts.browser_use_runner import run_browser_task; ..."
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── MiniMax-only LLM configuration ──────────────────────────────────────────

MINIMAX_API_BASE = os.environ.get("MINIMAX_API_BASE", "https://api.minimax.io/v1")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_MODEL = "minimax/MiniMax-M2.7"

_FORBIDDEN = {"claude", "anthropic", "gpt-4", "gpt-5", "openai", "gemini", "groq", "together", "o1-", "o3-", "o4-"}
if any(k in MINIMAX_MODEL.lower() for k in _FORBIDDEN):
    raise RuntimeError(f"[browser_use_runner] Forbidden model: {MINIMAX_MODEL!r}. Locked to MiniMax only.")

HEADLESS = os.environ.get("BROWSER_USE_HEADLESS", "true").lower() in ("true", "1", "yes")
TIMEOUT_MS = int(os.environ.get("BROWSER_USE_TIMEOUT_MS", "60000"))
MAX_OUTPUT = int(os.environ.get("BROWSER_USE_MAX_OUTPUT", "50000"))
MAX_STEPS_DEFAULT = 20


def _patch_litellm_for_minimax():
    """Patch ChatLiteLLM.ainvoke to call MiniMax API directly via litellm acompletion.

    browser-use's Agent checks llm.provider == 'browser-use' to identify its own adapter.
    ChatLiteLLM sets provider via litellm's get_llm_provider() which returns 'openai'
    for unknown model names. We patch ainvoke to call litellm.acompletion directly with
    the correct model, api_base, and api_key so LiteLLM's MiniMax integration handles it.
    """
    from browser_use.llm.litellm import ChatLiteLLM

    _original_ainvoke = ChatLiteLLM.ainvoke

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

        assert isinstance(raw_response, ModelResponse), f"Expected ModelResponse, got {type(raw_response)}"
        response: ModelResponse = raw_response
        choice = response.choices[0] if response.choices else None
        if choice is None:
            raise ModelProviderError(message="Empty response: no choices returned", status_code=502, model=self.name)
        content = choice.message.content or ""
        usage = self._parse_usage(response)
        stop_reason = choice.finish_reason
        thinking: str | None = None
        reasoning = getattr(choice.message, "reasoning_content", None)
        if reasoning:
            thinking = str(reasoning)
        if output_format is not None:
            if not content:
                raise ModelProviderError(message="Empty content for structured output", status_code=500, model=self.name)
            try:
                parsed = output_format.model_validate_json(content)
                return ChatInvokeCompletion(completion=parsed, thinking=thinking, usage=usage, stop_reason=stop_reason)
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
                return ChatInvokeCompletion(completion=parsed2, thinking=thinking, usage=usage, stop_reason=stop_reason)
            except Exception:
                pass
            import json
            import re
            json_match = re.search(r"\{[\s\S]*\}", content2)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    parsed3 = output_format.model_validate(data)
                    return ChatInvokeCompletion(completion=parsed3, thinking=thinking, usage=usage, stop_reason=stop_reason)
                except Exception:
                    pass
            raise ModelProviderError(
                message=f"MiniMax output incompatible with AgentOutput schema: {content2[:500]}",
                status_code=500,
                model=self.name,
            )
        return ChatInvokeCompletion(completion=content, thinking=thinking, usage=usage, stop_reason=stop_reason)

    ChatLiteLLM.ainvoke = ainvoke_patched


def _make_llm():
    """Build a browser-use ChatLiteLLM instance pointing at the MiniMax API directly."""
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


# ── Output / artifact paths ────────────────────────────────────────────────

OUTPUT_DIR = Path("./output")
LOG_DIR = Path("./.opencode/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Core browser task runner ──────────────────────────────────────────────


async def run_browser_task(
    task: str,
    max_steps: int = MAX_STEPS_DEFAULT,
    headless: bool = HEADLESS,
    allowed_domains: list[str] | None = None,
    prohibited_domains: list[str] | None = None,
    save_screenshot: bool = True,
    save_trace: bool = False,
) -> dict[str, Any]:
    """
    Run an autonomous browser task via browser-use, powered by MiniMax.

    Args:
        task: Natural language task (e.g. "Click login, fill credentials, submit")
        max_steps: Max browser action steps (default 20)
        headless: Run without visible GUI (default True)
        allowed_domains: Optional domain whitelist (e.g. ["example.com"])
        prohibited_domains: Optional domain blacklist
        save_screenshot: Save final screenshot to ./output/ (default True)
        save_trace: Save conversation trace to ./output/ (default False)

    Returns:
        dict with keys: success (bool), result (str), source (str), url (str),
                       screenshot_path (str), steps_completed (int), error (str?)
    """
    try:
        from browser_use import Agent
        from browser_use.browser.profile import BrowserProfile
        from browser_use.browser.session import BrowserSession
    except ImportError:
        return {
            "success": False,
            "error": "browser-use not installed. Run: pip install browser-use",
            "source": "browser_use_runner",
        }

    logging.getLogger("browser_use").setLevel(logging.ERROR)
    logging.getLogger("LiteLLM").setLevel(logging.ERROR)
    for _lib in ("httpx", "httpcore", " Playwright", "urllib3"):
        logging.getLogger(_lib).setLevel(logging.ERROR)

    llm = _make_llm()

    browser_profile = BrowserProfile(
        headless=headless,
        disable_security=False,
        extra_chromium_args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ],
    )
    browser = BrowserSession(browser_profile=browser_profile)

    agent_kwargs: dict[str, Any] = {
        "task": task,
        "llm": llm,
        "browser": browser,
        "max_actions_per_step": 5,
        "enable_planning": False,
        "use_thinking": False,
        "max_failures": 4,
    }
    if allowed_domains is not None:
        agent_kwargs["allowed_domains"] = allowed_domains
    if prohibited_domains is not None:
        agent_kwargs["prohibited_domains"] = prohibited_domains
    if save_trace:
        agent_kwargs["save_conversation_path"] = str(OUTPUT_DIR / "browser_trace.txt")

    agent = Agent(**agent_kwargs)

    start = time.monotonic()
    try:
        result = await agent.run(max_steps=max_steps)
        elapsed_ms = round((time.monotonic() - start) * 1000)
        final_result = (
            result.final_result()
            if hasattr(result, "final_result")
            else str(result)
        )
        # Truncate to MAX_OUTPUT
        if final_result and len(final_result) > MAX_OUTPUT:
            final_result = final_result[:MAX_OUTPUT] + f"... [truncated {len(final_result)-MAX_OUTPUT} chars]"

        screenshot_path = None
        if save_screenshot:
            try:
                screenshot_path = str(OUTPUT_DIR / f"screenshot_{int(time.time())}.png")
                page = await browser.get_current_page()
                if page:
                    await page.screenshot(path=screenshot_path)
                    logger.info("[browser_use_runner] screenshot saved: %s", screenshot_path)
                else:
                    screenshot_path = None
            except Exception as ss_err:
                logger.warning("[browser_use_runner] screenshot save failed: %s", ss_err)
                screenshot_path = None

        await browser.kill()

        return {
            "success": True,
            "result": final_result or "Task completed",
            "source": "browser_use",
            "elapsed_ms": elapsed_ms,
            "steps_completed": getattr(result, "steps_completed", max_steps),
            "screenshot_path": screenshot_path,
        }

    except Exception as exc:
        elapsed_ms = round((time.monotonic() - start) * 1000)
        await browser.kill()
        logger.warning("[browser_use_runner] browse_task failed: %s", exc)
        return {
            "success": False,
            "error": str(exc)[:300],
            "source": "browser_use",
            "elapsed_ms": elapsed_ms,
        }


# ── CLI interface ──────────────────────────────────────────────────────────


async def main():
    parser = argparse.ArgumentParser(description="browser-use runner (MiniMax-only)")
    parser.add_argument("--task", "-t", required=True, help="Natural language browser task")
    parser.add_argument("--max-steps", "-n", type=int, default=MAX_STEPS_DEFAULT)
    parser.add_argument("--headless", action="store_true", default=HEADLESS)
    parser.add_argument("--headed", dest="headless", action="store_false")
    parser.add_argument("--domain", "-d", action="append", dest="allowed_domains", help="Allow domain (can repeat)")
    parser.add_argument("--prohibit-domain", action="append", dest="prohibited_domains")
    parser.add_argument("--no-screenshot", dest="save_screenshot", action="store_false", default=True)
    parser.add_argument("--trace", dest="save_trace", action="store_true", default=False)
    parser.add_argument("--json", dest="json_output", action="store_true", default=False, help="Output JSON")
    args = parser.parse_args()

    result = await run_browser_task(
        task=args.task,
        max_steps=args.max_steps,
        headless=args.headless,
        allowed_domains=args.allowed_domains,
        prohibited_domains=args.prohibited_domains,
        save_screenshot=args.save_screenshot,
        save_trace=args.save_trace,
    )

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"✅ Browser task completed in {result.get('elapsed_ms', '?')}ms")
            print(f"   Steps: {result.get('steps_completed', '?')}/{args.max_steps}")
            if result.get("screenshot_path"):
                print(f"   Screenshot: {result['screenshot_path']}")
            print(f"\nResult:\n{result.get('result', '')}")
        else:
            print(f"❌ Browser task failed: {result.get('error', 'unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())