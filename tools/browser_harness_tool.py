"""browser_harness_tool.py — Tool wrapper for browser-harness CDP control.

Provides async functions for agents to control the user's browser via CDP.
No firecrawl dependency — pure CDP via Unix socket daemon.

Usage:
    from tools.browser_harness_tool import (
        bh_goto, bh_screenshot, bh_click, bh_type, bh_scroll,
        bh_page_info, bh_wait, bh_new_tab, bh_list_tabs, bh_evaluate,
        bh_http_get, bh_upload_file,
    )
"""
from __future__ import annotations

import base64
import json
import logging
import os
import socket
import time
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

NAME = os.environ.get("BU_NAME", "default")
SOCK = f"/tmp/bu-{NAME}.sock"

# ── socket comms ─────────────────────────────────────────────────────────────


def _send(req: dict) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCK)
    s.sendall((json.dumps(req) + "\n").encode())
    data = b""
    while not data.endswith(b"\n"):
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        data += chunk
    s.close()
    r = json.loads(data)
    if "error" in r:
        raise RuntimeError(r["error"])
    return r


def _ensure_daemon() -> None:
    """Import and call ensure_daemon from admin module."""
    from tools.browser_harness.admin import ensure_daemon as _ensure
    _ensure()


# ── page navigation ───────────────────────────────────────────────────────────


def bh_goto(url: str) -> dict:
    """Navigate current tab to URL. Returns CDP result."""
    _ensure_daemon()
    r = _send({"method": "Page.navigate", "params": {"url": url}})
    return r.get("result", {})


def bh_new_tab(url: str = "about:blank") -> str:
    """Open new tab. For page-level WS uses window.open(); for browser-level uses Target.createTarget."""
    _ensure_daemon()
    try:
        tid = _send({"method": "Target.createTarget", "params": {"url": "about:blank"}})["result"]["targetId"]
        _send({"method": "Target.activateTarget", "params": {"targetId": tid}})
        sid = _send({"method": "Target.attachToTarget", "params": {"targetId": tid, "flatten": True}})["result"]["sessionId"]
        _send({"meta": "set_session", "session_id": sid})
        if url != "about:blank":
            _send({"method": "Page.navigate", "params": {"url": url}, "session_id": sid})
        return tid
    except RuntimeError:
        _send({"method": "Runtime.evaluate", "params": {
            "expression": f"window.open({json.dumps(url)!r}, '_blank')"
        }})
        return "js-opened"


def bh_wait(seconds: float = 1.0) -> None:
    time.sleep(seconds)


def bh_wait_for_load(timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    session_id = _send({"meta": "session"}).get("session_id")
    while time.time() < deadline:
        r = _send({
            "method": "Runtime.evaluate",
            "params": {"expression": "document.readyState", "returnByValue": True},
            "session_id": session_id,
        })
        val = r.get("result", {}).get("result", {}).get("value")
        if val == "complete":
            return True
        time.sleep(0.3)
    return False


def bh_page_info() -> dict:
    """Returns {url, title, w, h, sx, sy, pw, ph} or {dialog: {...}} if modal open."""
    session_id = _send({"meta": "session"}).get("session_id")
    dialog = _send({"meta": "pending_dialog"}).get("dialog")
    if dialog:
        return {"dialog": dialog}
    r = _send({
        "method": "Runtime.evaluate",
        "params": {
            "expression": (
                "JSON.stringify({url:location.href,title:document.title,"
                "w:innerWidth,h:innerHeight,sx:scrollX,sy:scrollY,"
                "pw:document.documentElement.scrollWidth,"
                "ph:document.documentElement.scrollHeight})"
            ),
            "returnByValue": True,
        },
        "session_id": session_id,
    })
    return json.loads(r["result"]["result"]["value"])


# ── input ──────────────────────────────────────────────────────────────────────


def bh_click_at_xy(x: float, y: float, button: str = "left", clicks: int = 1) -> None:
    """Click at coordinates. Works through iframes, shadow DOM, cross-origin."""
    _ensure_daemon()
    _send({"method": "Input.dispatchMouseEvent", "params": {
        "type": "mousePressed", "x": x, "y": y, "button": button, "clickCount": clicks,
    }})
    _send({"method": "Input.dispatchMouseEvent", "params": {
        "type": "mouseReleased", "x": x, "y": y, "button": button, "clickCount": clicks,
    }})


def bh_type_text(text: str) -> None:
    _ensure_daemon()
    _send({"method": "Input.insertText", "params": {"text": text}})


_KEYS = {
    "Enter": (13, "Enter"), "Tab": (9, "Tab"), "Backspace": (8, "Backspace"),
    "Escape": (27, "Escape"), "Delete": (46, "Delete"), " ": (32, "Space"),
    "ArrowLeft": (37, "ArrowLeft"), "ArrowUp": (38, "ArrowUp"),
    "ArrowRight": (39, "ArrowRight"), "ArrowDown": (40, "ArrowDown"),
    "Home": (36, "Home"), "End": (35, "End"), "PageUp": (33, "PageUp"), "PageDown": (34, "PageDown"),
}


def bh_press_key(key: str, modifiers: int = 0) -> None:
    _ensure_daemon()
    vk, code = _KEYS.get(key, (ord(key[0]) if len(key) == 1 else 0, key))
    base = {"key": key, "code": code, "modifiers": modifiers,
            "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
    _send({"method": "Input.dispatchKeyEvent", "params": {**base, "type": "keyDown", **({"text": key} if len(key) == 1 else {})}})
    if len(key) == 1:
        _send({"method": "Input.dispatchKeyEvent", "params": {**base, "type": "char", "text": key}})
    _send({"method": "Input.dispatchKeyEvent", "params": {**base, "type": "keyUp"}})


def bh_scroll(x: float, y: float, dy: float = -300, dx: float = 0) -> None:
    _ensure_daemon()
    _send({"method": "Input.dispatchMouseEvent", "params": {
        "type": "mouseWheel", "x": x, "y": y, "deltaX": dx, "deltaY": dy,
    }})


# ── visual ─────────────────────────────────────────────────────────────────────


def bh_screenshot(path: str = "/tmp/bh_shot.png", full: bool = False) -> str:
    """Capture screenshot as PNG. Returns path."""
    _ensure_daemon()
    r = _send({"method": "Page.captureScreenshot", "params": {"format": "png", "captureBeyondViewport": full}})
    open(path, "wb").write(base64.b64decode(r["result"]["data"]))
    return path


# ── tabs ──────────────────────────────────────────────────────────────────────


def bh_list_tabs(include_chrome: bool = True) -> list[dict]:
    _ensure_daemon()
    targets = _send({"method": "Target.getTargets"})["result"]["targetInfos"]
    internal = ("chrome://", "chrome-untrusted://", "devtools://", "chrome-extension://", "about:")
    out = []
    for t in targets:
        if t["type"] != "page":
            continue
        url = t.get("url", "")
        if not include_chrome and url.startswith(internal):
            continue
        out.append({"targetId": t["targetId"], "title": t.get("title", ""), "url": url})
    return out


def bh_current_tab() -> dict:
    t = _send({"method": "Target.getTargetInfo"})["result"]["targetInfo"]
    return {"targetId": t.get("targetId"), "url": t.get("url", ""), "title": t.get("title", "")}


def bh_switch_tab(target: Any) -> str:
    target_id = target.get("targetId") if isinstance(target, dict) else target
    _send({"method": "Target.activateTarget", "params": {"targetId": target_id}})
    sid = _send({"method": "Target.attachToTarget", "params": {"targetId": target_id, "flatten": True}})["result"]["sessionId"]
    _send({"meta": "set_session", "session_id": sid})
    return sid


def bh_ensure_real_tab() -> dict | None:
    """Switch to first non-internal tab. Returns tab dict or None."""
    tabs = bh_list_tabs(include_chrome=False)
    if not tabs:
        return None
    try:
        cur = bh_current_tab()
        if cur["url"] and not cur["url"].startswith(("chrome://", "chrome-untrusted://", "devtools://", "chrome-extension://", "about:")):
            return cur
    except Exception:
        pass
    bh_switch_tab(tabs[0]["targetId"])
    return tabs[0]


# ── JS / DOM ──────────────────────────────────────────────────────────────────


def bh_evaluate(expression: str, target_id: str | None = None) -> Any:
    """Run JavaScript in the current tab (or iframe target). Returns value."""
    _ensure_daemon()
    sid = None
    if target_id:
        sid = _send({"method": "Target.attachToTarget", "params": {"targetId": target_id, "flatten": True}})["result"]["sessionId"]
    else:
        sid = _send({"meta": "session"}).get("session_id")
    if "return " in expression and not expression.strip().startswith("("):
        expression = f"(function(){{{expression}}})()"
    r = _send({
        "method": "Runtime.evaluate",
        "params": {"expression": expression, "returnByValue": True, "awaitPromise": True},
        "session_id": sid,
    })
    return r.get("result", {}).get("result", {}).get("value")


def bh_dispatch_key(selector: str, key: str = "Enter") -> None:
    """Fire DOM KeyboardEvent on matched element."""
    _KC = {"Enter": 13, "Tab": 9, "Escape": 27, "Backspace": 8, " ": 32,
           "ArrowLeft": 37, "ArrowUp": 38, "ArrowRight": 39, "ArrowDown": 40}
    kc = _KC.get(key, ord(key) if len(key) == 1 else 0)
    bh_evaluate(
        f"(()=>{{const e=document.querySelector({json.dumps(selector)});"
        f"if(e){{e.focus();e.dispatchEvent(new KeyboardEvent('keypress',"
        f"{{key:{json.dumps(key)},code:{json.dumps(key)},keyCode:{kc},which:{kc},bubbles:true}}));}}}})()"
    )


def bh_upload_file(selector: str, path: Any) -> None:
    """Set files on `<input type=file>` element."""
    _ensure_daemon()
    session_id = _send({"meta": "session"}).get("session_id")
    doc = _send({"method": "DOM.getDocument", "params": {"depth": -1}, "session_id": session_id})
    root = doc["result"]["root"]["nodeId"]
    nid = _send({"method": "DOM.querySelector", "params": {"nodeId": root, "selector": selector}, "session_id": session_id})["nodeId"]
    if not nid:
        raise RuntimeError(f"no element for {selector}")
    files = [path] if isinstance(path, str) else list(path)
    _send({"method": "DOM.setFileInputFiles", "params": {"files": files, "nodeId": nid}, "session_id": session_id})


# ── HTTP ───────────────────────────────────────────────────────────────────────


def bh_http_get(url: str, headers: dict | None = None, timeout: float = 20.0) -> str:
    """Pure HTTP GET — no browser. For static pages and APIs."""
    import gzip
    h = {"User-Agent": "LegionSwarmBot/1.0", "Accept-Encoding": "gzip"}
    if headers:
        h.update(headers)
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data.decode()


# ── scrape (replaces firecrawl) ───────────────────────────────────────────────


async def bh_scrape_url(url: str, max_chars: int = 10000) -> tuple[str, str]:
    """Scrape URL using browser-harness (CDP) or fallback to HTTP.

    Returns (content, source) where source is 'cdp', 'http', or 'error'.
    """
    try:
        _ensure_daemon()
        # Use HTTP GET first (static pages)
        content = bh_http_get(url, timeout=20.0)
        if content:
            return content[:max_chars], "http"
    except Exception:
        pass

    # Try browser-based extraction for JS-rendered pages
    try:
        _ensure_daemon()
        _send({"meta": "session"}).get("session_id")  # ensure daemon running
        bh_new_tab(url)
        bh_wait_for_load(15.0)
        result = bh_evaluate(
            "JSON.stringify({"
            "title: document.title,"
            "body: document.body ? document.body.innerText.slice(0, 8000) : ''"
            "})"
        )
        data = json.loads(result) if result else {}
        text = f"# {data.get('title', '')}\n\n{data.get('body', '')}"
        return text[:max_chars], "cdp"
    except Exception as exc:
        logger.warning("browser-harness scrape failed: %s", exc)
        return f"Scrape error: {exc}", "error"


# ── high-level tasks ──────────────────────────────────────────────────────────


async def bh_browse_and_click(url: str, click_text: str, wait_after: float = 1.0) -> dict[str, Any]:
    """Navigate to URL, find element by text, click it, return page state."""
    _ensure_daemon()
    bh_new_tab(url)
    bh_wait_for_load()
    # Find element by text
    expr = (
        f"(() => {{"
        f"const el = Array.from(document.querySelectorAll('a, button, [role=button]'))."
        f"find(e => e.innerText.includes({json.dumps(click_text)}));"
        f"if (!el) return null;"
        f"const r = el.getBoundingClientRect();"
        f"return {{x: r.left + r.width/2, y: r.top + r.height/2, text: el.innerText}};"
        f"}})()"
    )
    result = bh_evaluate(expr)
    if result and result.get("x"):
        bh_click_at_xy(result["x"], result["y"])
        bh_wait(wait_after)
    info = bh_page_info()
    text = bh_evaluate("document.body ? document.body.innerText.slice(0, 2000) : ''")
    return {"title": info.get("title", ""), "url": info.get("url", url), "text": text or ""}


async def bh_deep_scrape(url: str, max_chars: int = 15000) -> str:
    """Extract main content from URL using browser (JS-rendered)."""
    _ensure_daemon()
    bh_new_tab(url)
    bh_wait_for_load(10.0)
    content = bh_evaluate(
        "(() => {"
        "const el = document.querySelector('main, article, [role=main], body');"
        "return el ? el.innerText.slice(0, 15000) : document.body.innerText.slice(0, 15000);"
        "})()"
    )
    return content or ""


def bh_full_page_screenshot(path: str = "/tmp/bh_full.png") -> str:
    """Capture full page (not just viewport)."""
    return bh_screenshot(path, full=True)


# ── admin ────────────────────────────────────────────────────────────────────


def bh_restart_daemon() -> None:
    from tools.browser_harness.admin import restart_daemon as _restart
    _restart()


def bh_daemon_alive() -> bool:
    from tools.browser_harness.admin import daemon_alive as _alive
    return _alive()


def bh_run_setup() -> int:
    from tools.browser_harness.admin import run_setup as _setup
    return _setup()


def bh_run_doctor() -> int:
    from tools.browser_harness.admin import run_doctor as _doctor
    return _doctor()
