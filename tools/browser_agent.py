"""Browser automation — autonomous web tasks and site health checks.

Two modes:
1. browse_task()      — uses browser-use library for LLM-driven autonomous browsing
2. check_site_health() — uses Playwright directly (no browser-use dep) for health checks

browser-use requires BROWSER_USE_MODEL env var (e.g. openrouter/google/gemini-flash-1.5)
Falls back gracefully if browser-use is not installed.
"""

from __future__ import annotations

import logging
import os
import re
import time
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)

# ── Prompt injection protection ─────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>.*?</iframe>",
    r"{{.*?}}",
    r"{%.*?%}",
    r"<additional_instruction",
    r"system prompt",
]


def sanitize_user_content(text: str) -> str:
    """Remove prompt injection patterns from user-provided text."""
    for pattern in INJECTION_PATTERNS:
        text = re.sub(pattern, "[BLOCKED]", text, flags=re.IGNORECASE | re.DOTALL)
    return text


# ── SSRF protection ────────────────────────────────────────────────────────────────

_PRIVATE_IP_PATTERNS = [
    re.compile(r"^10\."),
    re.compile(r"^172\.(1[6-9]|2[0-9]|3[0-1])\."),
    re.compile(r"^192\.168\."),
    re.compile(r"^127\."),
    re.compile(r"^localhost$", re.IGNORECASE),
    re.compile(r"^0\."),
    re.compile(r"^::1$"),
    re.compile(r"^fe80:"),
]


def _is_private_ip(host: str) -> bool:
    """Check if host is a private/internal IP."""
    for pattern in _PRIVATE_IP_PATTERNS:
        if pattern.match(host):
            return True
    return False


def validate_url(url: str) -> tuple[bool, str]:
    """Validate URL against SSRF allowlist.

    Returns (is_safe, error_message).
    """
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        host = parsed.netloc.lower().split(":")[0]

        # Block dangerous schemes
        if scheme in ("file", "ftp", "gopher"):
            return False, f"Disallowed scheme: {scheme}"

        if scheme not in ("http", "https"):
            return False, f"Disallowed scheme: {scheme}"

        # Block private IPs
        if _is_private_ip(host):
            return False, f"Private IP blocked: {host}"

        # Check against allowlist if configured
        allowed = os.getenv("BROWSER_ALLOWED_DOMAINS", "")
        if allowed:
            allowed_domains = {d.strip().lower() for d in allowed.split(",") if d.strip()}
            if allowed_domains and not any(host.endswith(d) or host == d for d in allowed_domains):
                return False, f"Domain not in allowlist: {host}"

        return True, ""

    except Exception as exc:
        return False, f"URL parse error: {exc}"


# ── Site health check (Playwright direct, no browser-use needed) ──────────────

RUMAHLABUH_URL = os.getenv("RUMAHLABUH_URL", "https://rumahlabuh.com")


async def check_site_health(url: str | None = None) -> dict[str, Any]:
    """
    Check website health using Playwright.
    Returns: {url, status, load_time_ms, title, error (optional)}
    """
    target = url or RUMAHLABUH_URL

    is_safe, err = validate_url(target)
    if not is_safe:
        return {
            "url": target,
            "status": "blocked",
            "error": f"SSRF check failed: {err}",
            "source": "browser_agent",
        }

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"url": target, "error": "playwright not installed", "status": "unknown"}

    start = time.monotonic()
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            page = await browser.new_page()
            try:
                response = await page.goto(
                    target,
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
                load_ms = round((time.monotonic() - start) * 1000)
                title = await page.title()
                http_status = response.status if response else None

                # Quick content check — look for obvious error indicators
                content = await page.content()
                has_error = any(
                    phrase in content.lower()
                    for phrase in ["error 500", "application error", "503 service", "502 bad gateway"]
                )

                return {
                    "url": target,
                    "status": "degraded" if has_error else "ok",
                    "http_status": http_status,
                    "load_time_ms": load_ms,
                    "title": title[:100] if title else "",
                    "source": "playwright",
                }
            finally:
                await browser.close()
    except Exception as exc:
        load_ms = round((time.monotonic() - start) * 1000)
        logger.warning("[BrowserAgent] Site health check failed for %s: %s", target, exc)
        return {
            "url": target,
            "status": "unreachable",
            "load_time_ms": load_ms,
            "error": str(exc)[:200],
            "source": "playwright",
        }


# ── Autonomous browsing via browser-use ──────────────────────────────────────


async def browse_task(task: str, max_steps: int = 20) -> dict[str, Any]:
    """
    Perform an autonomous browser task using the browser-use library.

    Requires: pip install browser-use
    Requires env var: BROWSER_USE_MODEL (e.g. openrouter/google/gemini-flash-1.5)

    Falls back to a Playwright-only scrape if browser-use is not available.
    """
    # Sanitize user input to prevent prompt injection
    user_text = sanitize_user_content(task)
    model_str = os.getenv("BROWSER_USE_MODEL", "")

    # Extract and validate URL before browsing
    url_match = re.search(r"https?://[^\s'\"]+", task)
    if url_match:
        url_to_check = url_match.group(0).rstrip(".,)")
        is_safe, err = validate_url(url_to_check)
        if not is_safe:
            return {
                "success": False,
                "error": f"SSRF check failed: {err}",
                "source": "browser_agent",
            }

    try:
        from browser_use import Agent as BrowserAgent
        from browser_use.browser.browser import Browser, BrowserConfig
        from langchain_openai import ChatOpenAI

        # browser-use uses LangChain-compatible LLMs
        # Support openrouter or openai-compatible providers via BROWSER_USE_MODEL
        if "/" in model_str:
            # e.g. "openrouter/google/gemini-flash-1.5" → use OpenAI-compatible client
            provider, model_id = model_str.split("/", 1)
            if provider == "openrouter":
                llm = ChatOpenAI(
                    model=model_id,
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENROUTER_API_KEY", ""),
                )
            else:
                # Generic OpenAI-compatible endpoint
                llm = ChatOpenAI(model=model_str)
        else:
            # Default: use whatever OPENAI_API_KEY is set
            llm = ChatOpenAI(model=model_str or "gpt-4o-mini")

        # Build domain restriction lists for autonomous navigation
        # When a URL is explicitly provided, restrict browser to that domain only
        allowed_domains: list[str] | None = None
        prohibited_domains: list[str] | None = None

        if url_match:
            # User gave an explicit URL — lock browser to just that domain
            extracted = url_match.group(0).rstrip(".,)")
            parsed = urllib.parse.urlparse(extracted)
            if parsed.hostname:
                allowed_domains = [parsed.hostname]
        else:
            # No explicit URL — respect BROWSER_ALLOWED_DOMAINS if set
            allowed_cfg = os.getenv("BROWSER_ALLOWED_DOMAINS", "")
            if allowed_cfg:
                allowed_domains = [d.strip() for d in allowed_cfg.split(",") if d.strip()]

        prohibited_cfg = os.getenv("BROWSER_PROHIBITED_DOMAINS", "")
        if prohibited_cfg:
            prohibited_domains = [d.strip() for d in prohibited_cfg.split(",") if d.strip()]

        browser = Browser(
            config=BrowserConfig(
                headless=True,
                disable_security=False,
            )
        )

        agent_kwargs: dict[str, Any] = {
            "task": user_text,
            "llm": llm,
            "browser": browser,
            "max_actions_per_step": 5,
        }
        if allowed_domains is not None:
            agent_kwargs["allowed_domains"] = allowed_domains
        if prohibited_domains is not None:
            agent_kwargs["prohibited_domains"] = prohibited_domains

        agent = BrowserAgent(**agent_kwargs)

        result = await agent.run(max_steps=max_steps)
        final_result = result.final_result() if hasattr(result, "final_result") else str(result)
        return {
            "success": True,
            "result": final_result or "Task completed (no text result)",
            "source": "browser_use",
        }

    except ImportError:
        logger.info("[BrowserAgent] browser-use not installed — falling back to Playwright scrape")
        return await _playwright_fallback(user_text)
    except Exception as exc:
        logger.warning("[BrowserAgent] browse_task failed: %s", exc)
        return {"success": False, "error": str(exc)[:300], "source": "browser_use"}


async def _playwright_fallback(task: str) -> dict[str, Any]:
    """
    Lightweight fallback using Crawl4AI (preferred) or Playwright.
    Crawl4AI provides AI-friendly extracted content.
    """
    import re

    # Sanitize input for defense-in-depth
    task = sanitize_user_content(task)
    url_match = re.search(r'https?://[^\s\'"]+', task)
    if not url_match:
        return {
            "success": False,
            "error": "browser-use not installed and no URL found in task for Crawl4AI/Playwright fallback",
            "source": "playwright_fallback",
        }

    url = url_match.group(0).rstrip(".,)")

    # SSRF validation before browsing
    is_safe, err = validate_url(url)
    if not is_safe:
        return {
            "success": False,
            "error": f"SSRF check failed: {err}",
            "url": url,
            "source": "playwright_fallback",
        }

    # Try Crawl4AI first
    try:
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url)
            if result and result.get("markdown"):
                return {
                    "success": True,
                    "result": result["markdown"][:4000],
                    "url": url,
                    "source": "crawl4ai",
                }
    except Exception as exc:
        logger.debug("[BrowserAgent] Crawl4AI fallback failed for %s: %s", url, exc)

    # Fall back to Playwright
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"success": False, "error": "playwright not installed", "source": "playwright_fallback"}

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                text = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('h1, h2, h3, p, li, td, th');
                        return Array.from(elements)
                            .map(el => el.innerText?.trim())
                            .filter(t => t && t.length > 10)
                            .slice(0, 80)
                            .join('\\n');
                    }
                """)
                return {
                    "success": True,
                    "result": text[:3000],
                    "url": url,
                    "source": "playwright_fallback",
                    "note": "browser-use not installed; raw page text returned — no autonomous interaction",
                }
            finally:
                await browser.close()
    except Exception as exc:
        return {"success": False, "error": str(exc)[:200], "url": url, "source": "playwright_fallback"}


def format_health_for_prompt(health: dict[str, Any]) -> str:
    """Format site health result for system-prompt injection."""
    if "error" in health and health.get("status") == "unreachable":
        return f"[Site Health — {health['url']}]: UNREACHABLE — {health.get('error', '')[:80]}"
    status_icon = {"ok": "✅", "degraded": "⚠️", "unreachable": "❌"}.get(health.get("status", ""), "❓")
    return (
        f"[Site Health — {health.get('url', 'unknown')}]: "
        f"{status_icon} {health.get('status', 'unknown').upper()} | "
        f"HTTP {health.get('http_status', '?')} | "
        f"Load {health.get('load_time_ms', '?')}ms | "
        f"Title: {health.get('title', 'N/A')}"
    )
