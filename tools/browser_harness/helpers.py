"""Browser control via CDP. Read, edit, extend — this file is yours."""
from __future__ import annotations

import base64
import contextlib
import gzip
import json
import os
import socket
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _load_env():
    p = Path(__file__).parent / ".env"
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

NAME = os.environ.get("BU_NAME", "default")
SOCK = f"/tmp/bu-{NAME}.sock"
INTERNAL = ("chrome://", "chrome-untrusted://", "devtools://", "chrome-extension://", "about:")


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


def cdp(method: str, session_id: str | None = None, **params: Any) -> dict:
    return _send({"method": method, "params": params, "session_id": session_id}).get("result", {})


def drain_events() -> list[dict]:
    return _send({"meta": "drain_events"})["events"]


# --- navigation / page ---
def goto_url(url: str) -> dict:
    r = cdp("Page.navigate", url=url)
    d = Path(__file__).parent / "domain-skills" / (
        (urlparse(url).hostname or "").removeprefix("www.").split(".")[0]
    )
    return {**r, "domain_skills": sorted(p.name for p in d.rglob("*.md"))[:10]} if d.is_dir() else r


def page_info() -> dict:
    dialog = _send({"meta": "pending_dialog"}).get("dialog")
    if dialog:
        return {"dialog": dialog}
    r = cdp(
        "Runtime.evaluate",
        expression=(
            "JSON.stringify({url:location.href,title:document.title,"
            "w:innerWidth,h:innerHeight,sx:scrollX,sy:scrollY,"
            "pw:document.documentElement.scrollWidth,"
            "ph:document.documentElement.scrollHeight})"
        ),
        returnByValue=True,
    )
    return json.loads(r["result"]["value"])


# --- input ---
_debug_click_counter = 0


def click_at_xy(x: float, y: float, button: str = "left", clicks: int = 1) -> None:
    global _debug_click_counter
    if os.environ.get("BH_DEBUG_CLICKS"):
        try:
            from PIL import Image, ImageDraw  # type: ignore

            dpr = js("window.devicePixelRatio") or 1
            path = capture_screenshot(f"/tmp/debug_click_{_debug_click_counter}.png")
            img = Image.open(path)
            draw = ImageDraw.Draw(img)
            px, py = int(x * dpr), int(y * dpr)
            r = int(15 * dpr)
            draw.ellipse([px - r, py - r, px + r, py + r], outline="red", width=int(3 * dpr))
            draw.line(
                [px - r - int(5 * dpr), py, px + r + int(5 * dpr), py],
                fill="red",
                width=int(2 * dpr),
            )
            draw.line(
                [px, py - r - int(5 * dpr), px, py + r + int(5 * dpr)],
                fill="red",
                width=int(2 * dpr),
            )
            img.save(path)
            print(f"[debug_click] saved {path} (x={x}, y={y}, dpr={dpr})")
        except Exception as e:
            print(f"[debug_click] overlay failed: {e}")
        _debug_click_counter += 1
    cdp("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button=button, clickCount=clicks)
    cdp("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button=button, clickCount=clicks)


def type_text(text: str) -> None:
    cdp("Input.insertText", text=text)


_KEYS = {
    "Enter": (13, "Enter", "\r"),
    "Tab": (9, "Tab", "\t"),
    "Backspace": (8, "Backspace", ""),
    "Escape": (27, "Escape", ""),
    "Delete": (46, "Delete", ""),
    " ": (32, "Space", " "),
    "ArrowLeft": (37, "ArrowLeft", ""),
    "ArrowUp": (38, "ArrowUp", ""),
    "ArrowRight": (39, "ArrowRight", ""),
    "ArrowDown": (40, "ArrowDown", ""),
    "Home": (36, "Home", ""),
    "End": (35, "End", ""),
    "PageUp": (33, "PageUp", ""),
    "PageDown": (34, "PageDown", ""),
}


def press_key(key: str, modifiers: int = 0) -> None:
    vk, code, text = _KEYS.get(
        key, (ord(key[0]) if len(key) == 1 else 0, key, key if len(key) == 1 else "")
    )
    base = {
        "key": key,
        "code": code,
        "modifiers": modifiers,
        "windowsVirtualKeyCode": vk,
        "nativeVirtualKeyCode": vk,
    }
    cdp("Input.dispatchKeyEvent", type="keyDown", **base, **({"text": text} if text else {}))
    if text and len(text) == 1:
        cdp(
            "Input.dispatchKeyEvent",
            type="char",
            text=text,
            **{k: v for k, v in base.items() if k != "text"},
        )
    cdp("Input.dispatchKeyEvent", type="keyUp", **base)


def scroll(x: float, y: float, dy: float = -300, dx: float = 0) -> None:
    cdp("Runtime.evaluate", expression=f"window.scrollBy({x},{y})", returnByValue=True)


# --- visual ---
def capture_screenshot(path: str = "/tmp/shot.png", full: bool = False, max_dim: int | None = None) -> str:
    r = cdp("Page.captureScreenshot", format="png", captureBeyondViewport=full)
    with open(path, "wb") as f:
        f.write(base64.b64decode(r["data"]))
    if max_dim:
        from PIL import Image  # type: ignore

        img = Image.open(path)
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim))
            img.save(path)
    return path


# --- tabs ---
def list_tabs(include_chrome: bool = True) -> list[dict]:
    out = []
    for base in (9222, 9223):
        try:
            import urllib.request
            with urllib.request.urlopen(f"http://127.0.0.1:{base}/json", timeout=2) as r:
                for t in json.loads(r.read()):
                    if t.get("type") != "page":
                        continue
                    url = t.get("url", "")
                    if not include_chrome and url.startswith(INTERNAL):
                        continue
                    out.append({"targetId": t.get("id", ""), "title": t.get("title", ""), "url": url})
                return out
        except Exception:
            pass
    for t in cdp("Target.getTargets")["targetInfos"]:
        if t["type"] != "page":
            continue
        url = t.get("url", "")
        if not include_chrome and url.startswith(INTERNAL):
            continue
        out.append({"targetId": t["targetId"], "title": t.get("title", ""), "url": url})
    return out


def current_tab() -> dict:
    r = cdp(
        "Runtime.evaluate",
        expression="JSON.stringify({targetId:window.__bh_tid||'',url:location.href,title:document.title})",
        returnByValue=True,
    )
    return json.loads(r.get("result", {}).get("value", "{}"))


def _mark_tab() -> None:
    with contextlib.suppress(Exception):
        cdp(
            "Runtime.evaluate",
            expression="if(!document.title.startsWith('\U0001F7E2'))document.title='\U0001F7E2 '+document.title",
        )


def _get_browser_session() -> str | None:
    return _send({"meta": "browser_session"}).get("session_id")


def switch_tab(target: Any) -> str:
    target_id = target.get("targetId") if isinstance(target, dict) else target
    browser_sid = _get_browser_session()
    if browser_sid:
        with contextlib.suppress(Exception):
            cdp(
                "Runtime.evaluate",
                expression="if(document.title.startsWith('\U0001F7E2 '))document.title=document.title.slice(2)",
            )
        cdp("Target.activateTarget", targetId=target_id, session_id=browser_sid)
        sid = cdp("Target.attachToTarget", targetId=target_id, flatten=True, session_id=browser_sid)["sessionId"]
        _send({"meta": "set_session", "session_id": sid})
        _mark_tab()
        return sid
    for base in (9222, 9223):
        try:
            import urllib.request
            with urllib.request.urlopen(f"http://127.0.0.1:{base}/json", timeout=2) as r:
                for t in json.loads(r.read()):
                    if t.get("id") == target_id and t.get("webSocketDebuggerUrl"):
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                else:
                    continue
                cdp(
                    "Runtime.evaluate",
                    expression=f"window.open({json.dumps(ws_url)}, '_blank')",
                )
                _send({"meta": "set_session", "session_id": None})
                return target_id
        except Exception:
            pass
    raise RuntimeError("switch_tab requires browser-level CDP session (page-level WS not supported for tab switching)")


def new_tab(url: str = "about:blank") -> str:
    browser_sid = _get_browser_session()
    if browser_sid:
        tid = cdp("Target.createTarget", url="about:blank", session_id=browser_sid)["targetId"]
        switch_tab(tid)
        if url != "about:blank":
            goto_url(url)
        return tid
    import urllib.request
    for base in (9222, 9223):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{base}/json/new?url={urllib.parse.quote(url)}", timeout=5) as r:
                new_target = json.loads(r.read())
                _send({"meta": "set_session", "session_id": None})
                return new_target.get("id", "")
        except Exception:
            pass
    js(f"window.open({json.dumps(url)}, '_blank')")
    return ""


def ensure_real_tab() -> dict | None:
    tabs = list_tabs(include_chrome=False)
    if not tabs:
        return None
    try:
        cur = current_tab()
        if cur["url"] and not cur["url"].startswith(INTERNAL):
            return cur
    except Exception:
        pass
    switch_tab(tabs[0]["targetId"])
    return tabs[0]


def iframe_target(url_substr: str) -> str | None:
    for base in (9222, 9223):
        try:
            import urllib.request
            with urllib.request.urlopen(f"http://127.0.0.1:{base}/json", timeout=2) as r:
                for t in json.loads(r.read()):
                    if t.get("type") == "iframe" and url_substr in t.get("url", ""):
                        return t.get("id")
        except Exception:
            pass
    for t in cdp("Target.getTargets")["targetInfos"]:
        if t["type"] == "iframe" and url_substr in t.get("url", ""):
            return t["targetId"]
    return None


# --- utility ---
def wait(seconds: float = 1.0) -> None:
    time.sleep(seconds)


def wait_for_load(timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if js("document.readyState") == "complete":
            return True
        time.sleep(0.3)
    return False


def js(expression: str, target_id: str | None = None) -> Any:
    sid = (
        cdp("Target.attachToTarget", targetId=target_id, flatten=True)["sessionId"]
        if target_id
        else None
    )
    if "return " in expression and not expression.strip().startswith("("):
        expression = f"(function(){{{expression}}})()"
    r = cdp(
        "Runtime.evaluate",
        session_id=sid,
        expression=expression,
        returnByValue=True,
        awaitPromise=True,
    )
    return r.get("result", {}).get("value")


_KC = {
    "Enter": 13,
    "Tab": 9,
    "Escape": 27,
    "Backspace": 8,
    " ": 32,
    "ArrowLeft": 37,
    "ArrowUp": 38,
    "ArrowRight": 39,
    "ArrowDown": 40,
}


def dispatch_key(selector: str, key: str = "Enter", event: str = "keypress") -> None:
    kc = _KC.get(key, ord(key) if len(key) == 1 else 0)
    js(
        f"(()=>{{const e=document.querySelector({json.dumps(selector)});"
        f"if(e){{e.focus();e.dispatchEvent(new KeyboardEvent({json.dumps(event)},"
        f"{{key:{json.dumps(key)},code:{json.dumps(key)},keyCode:{kc},which:{kc},bubbles:true}}));}}}})()"
    )


def upload_file(selector: str, path: Any) -> None:
    doc = cdp("DOM.getDocument", depth=-1)
    nid = cdp("DOM.querySelector", nodeId=doc["root"]["nodeId"], selector=selector)["nodeId"]
    if not nid:
        raise RuntimeError(f"no element for {selector}")
    cdp(
        "DOM.setFileInputFiles",
        files=[path] if isinstance(path, str) else list(path),
        nodeId=nid,
    )


def http_get(url: str, headers: dict | None = None, timeout: float = 20.0) -> str:
    if os.environ.get("BROWSER_USE_API_KEY"):
        try:
            from fetch_use import fetch_sync  # type: ignore

            return fetch_sync(url, headers=headers, timeout_ms=int(timeout * 1000)).text
        except ImportError:
            pass
    h = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"}
    if headers:
        h.update(headers)
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=h), timeout=timeout
    ) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data.decode()
