"""Admin: daemon lifecycle, remote browsers, profile sync, doctor."""
from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


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
BU_API = "https://api.browser-use.com/api/v3"
GH_RELEASES = "https://api.github.com/repos/browser-use/browser-harness/releases/latest"
VERSION_CACHE = Path("/tmp/bu-version-cache.json")
VERSION_CACHE_TTL = 24 * 3600


def _paths(name: str | None = None):
    n = name or NAME
    return f"/tmp/bu-{n}.sock", f"/tmp/bu-{n}.pid"


def _log_tail(name: str | None = None) -> str | None:
    p = f"/tmp/bu-{name or NAME}.log"
    try:
        return Path(p).read_text().strip().splitlines()[-1]
    except (FileNotFoundError, IndexError):
        return None


def _needs_chrome_remote_debugging_prompt(msg: str | None) -> bool:
    lower = (msg or "").lower()
    return (
        "devtoolsactiveport not found" in lower
        or "enable chrome://inspect" in lower
        or "not live yet" in lower
        or (
            "ws handshake failed" in lower
            and (
                "403" in lower
                or "opening handshake" in lower
                or "timed out" in lower
                or "timeout" in lower
            )
        )
    )


def _is_local_chrome_mode(env: dict | None = None) -> bool:
    return not (env or {}).get("BU_CDP_WS") and not os.environ.get("BU_CDP_WS")


def daemon_alive(name: str | None = None) -> bool:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(_paths(name)[0])
        s.close()
        return True
    except (TimeoutError, FileNotFoundError, ConnectionRefusedError):
        return False


def _probe_cdp_ws() -> str | None:
    for port in (9222, 9223):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2) as r:
                for t in json.loads(r.read()):
                    if t.get("type") == "page":
                        return t["webSocketDebuggerUrl"]
        except Exception:
            pass
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:
                return json.loads(r.read())["webSocketDebuggerUrl"]
        except Exception:
            pass
    return None


def ensure_daemon(wait: float = 60.0, name: str | None = None, env: dict | None = None) -> None:
    if daemon_alive(name):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(_paths(name)[0])
            s.sendall(b'{"method":"Target.getTargets","params":{}}\n')
            data = b""
            while not data.endswith(b"\n"):
                chunk = s.recv(1 << 16)
                if not chunk:
                    break
                data += chunk
            if b'"result"' in data:
                return
        except Exception:
            pass
        restart_daemon(name)

    local = _is_local_chrome_mode(env)

    for attempt in (0, 1):
        e = {**os.environ, **({"BU_NAME": name} if name else {}), **(env or {})}
        if local and not e.get("BU_CDP_WS") and not e.get("BU_CDP_URL"):
            ws_url = _probe_cdp_ws()
            if ws_url:
                e["BU_CDP_WS"] = ws_url
        p = subprocess.Popen(
            ["python3", "-m", "tools.browser_harness.daemon"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=e,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        deadline = time.time() + wait
        while time.time() < deadline:
            if daemon_alive(name):
                return
            if p.poll() is not None:
                break
            time.sleep(0.2)
        msg = _log_tail(name) or ""
        if local and attempt == 0 and _needs_chrome_remote_debugging_prompt(msg):
            _open_chrome_inspect()
            print(
                "browser-harness: click Allow on chrome://inspect "
                "(and tick the checkbox if shown)",
                file=sys.stderr,
            )
            restart_daemon(name)
            continue
        raise RuntimeError(msg or f"daemon {name or NAME} didn't come up -- check /tmp/bu-{name or NAME}.log")


def stop_remote_daemon(name: str = "remote") -> None:
    restart_daemon(name)


def restart_daemon(name: str | None = None) -> None:
    import signal

    sock, pid_path = _paths(name)
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(sock)
        s.sendall(b'{"meta":"shutdown"}\n')
        s.recv(1024)
        s.close()
    except Exception:
        pass
    try:
        pid = int(open(pid_path).read())
    except (FileNotFoundError, ValueError):
        pid = None
    if pid:
        for _ in range(75):
            try:
                os.kill(pid, 0)
                time.sleep(0.2)
            except ProcessLookupError:
                break
        else:
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGTERM)
    for f in (sock, pid_path):
        with contextlib.suppress(FileNotFoundError):
            os.unlink(f)


def _browser_use(path: str, method: str, body: dict | None = None) -> dict:
    key = os.environ.get("BROWSER_USE_API_KEY")
    if not key:
        raise RuntimeError("BROWSER_USE_API_KEY missing -- see .env.example")
    req = urllib.request.Request(
        f"{BU_API}{path}",
        method=method,
        data=(json.dumps(body).encode() if body is not None else None),
        headers={"X-Browser-Use-API-Key": key, "Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read() or b"{}")


def _cdp_ws_from_url(cdp_url: str) -> str:
    return json.loads(urllib.request.urlopen(f"{cdp_url}/json/version", timeout=15).read())["webSocketDebuggerUrl"]


def _has_local_gui() -> bool:
    import platform
    system = platform.system()
    if system in ("Darwin", "Windows"):
        return True
    if system == "Linux":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return False


def _show_live_url(url: str | None) -> None:
    import webbrowser

    if not url:
        return
    print(url)
    if not _has_local_gui():
        print("(no local GUI — share the liveUrl with the user)", file=sys.stderr)
        return
    try:
        webbrowser.open(url, new=2)
        print("(opened liveUrl in your default browser)", file=sys.stderr)
    except Exception as e:
        print(f"(couldn't auto-open: {e} — share the liveUrl with the user)", file=sys.stderr)


def list_cloud_profiles() -> list[dict]:
    out, page = [], 1
    while True:
        listing = _browser_use(f"/profiles?pageSize=100&pageNumber={page}", "GET")
        items = listing.get("items") if isinstance(listing, dict) else listing
        if not items:
            break
        for p in items:
            detail = _browser_use(f"/profiles/{p['id']}", "GET")
            out.append({
                "id": detail["id"],
                "name": detail.get("name"),
                "userId": detail.get("userId"),
                "cookieDomains": detail.get("cookieDomains") or [],
                "lastUsedAt": detail.get("lastUsedAt"),
            })
        if isinstance(listing, dict) and len(out) >= listing.get("totalItems", len(out)):
            break
        page += 1
    return out


def _resolve_profile_name(profile_name: str) -> str:
    matches = [p for p in list_cloud_profiles() if p.get("name") == profile_name]
    if not matches:
        raise RuntimeError(f"no cloud profile named {profile_name!r} -- call list_cloud_profiles() or sync_local_profile() first")
    if len(matches) > 1:
        raise RuntimeError(f"{len(matches)} cloud profiles named {profile_name!r} -- pass profileId=<uuid> instead")
    return matches[0]["id"]


def start_remote_daemon(
    name: str = "remote",
    profileName: str | None = None,
    **create_kwargs: Any,
) -> dict:
    if daemon_alive(name):
        raise RuntimeError(f"daemon {name!r} already alive -- restart_daemon({name!r}) first")
    if profileName:
        if "profileId" in create_kwargs:
            raise RuntimeError("pass profileName OR profileId, not both")
        create_kwargs["profileId"] = _resolve_profile_name(profileName)
    browser = _browser_use("/browsers", "POST", create_kwargs)
    ensure_daemon(
        name=name,
        env={"BU_CDP_WS": _cdp_ws_from_url(browser["cdpUrl"]), "BU_BROWSER_ID": browser["id"]},
    )
    _show_live_url(browser.get("liveUrl"))
    return browser


def list_local_profiles() -> list[dict]:
    import json

    if not shutil.which("profile-use"):
        raise RuntimeError(
            "profile-use not installed -- "
            "curl -fsSL https://browser-use.com/profile.sh | sh"
        )
    return json.loads(
        subprocess.check_output(["profile-use", "list", "--json"], text=True)
    )


def sync_local_profile(
    profile_name: str,
    browser: str | None = None,
    cloud_profile_id: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> str:
    if not shutil.which("profile-use"):
        raise RuntimeError(
            "profile-use not installed -- "
            "curl -fsSL https://browser-use.com/profile.sh | sh"
        )
    if not os.environ.get("BROWSER_USE_API_KEY"):
        raise RuntimeError("BROWSER_USE_API_KEY missing")
    cmd = ["profile-use", "sync", "--profile", profile_name]
    if browser:
        cmd += ["--browser", browser]
    if cloud_profile_id:
        cmd += ["--cloud-profile-id", cloud_profile_id]
    for d in include_domains or []:
        cmd += ["--domain", d]
    for d in exclude_domains or []:
        cmd += ["--exclude-domain", d]
    r = subprocess.run(cmd, text=True, capture_output=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        raise RuntimeError(f"profile-use sync failed (exit {r.returncode})")
    if cloud_profile_id:
        return cloud_profile_id
    m = re.search(r"Profile created:\s+([0-9a-f-]{36})", r.stdout)
    if not m:
        raise RuntimeError(f"profile-use did not report a profile UUID (exit {r.returncode})")
    return m.group(1)


def _version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("browser-harness")
        except PackageNotFoundError:
            return ""
    except Exception:
        return ""


def _repo_dir() -> Path | None:
    p = Path(__file__).resolve().parent
    return p if (p / ".git").is_dir() else None


def _install_mode() -> str:
    if _repo_dir():
        return "git"
    return "pypi" if _version() else "unknown"


def _cache_read() -> dict:
    try:
        return json.loads(VERSION_CACHE.read_text())
    except (FileNotFoundError, ValueError):
        return {}


def _cache_write(data: dict) -> None:
    with contextlib.suppress(OSError):
        VERSION_CACHE.write_text(json.dumps(data))


def _latest_release_tag(force: bool = False) -> str | None:
    cache = _cache_read()
    now = time.time()
    if not force and cache.get("tag") and now - cache.get("fetched_at", 0) < VERSION_CACHE_TTL:
        return cache.get("tag")
    try:
        req = urllib.request.Request(GH_RELEASES, headers={"Accept": "application/vnd.github+json"})
        tag = json.loads(urllib.request.urlopen(req, timeout=5).read()).get("tag_name") or ""
    except Exception:
        return cache.get("tag")
    tag = tag.lstrip("v")
    _cache_write({**cache, "tag": tag, "fetched_at": now})
    return tag or None


def _version_tuple(v: str) -> tuple[int, ...]:
    parts = []
    for s in (v or "").split("."):
        m = ""
        for ch in s:
            if ch.isdigit():
                m += ch
            else:
                break
        parts.append(int(m) if m else 0)
    return tuple(parts)


def check_for_update() -> tuple[str, str | None, bool]:
    cur = _version()
    latest = _latest_release_tag()
    newer = bool(cur and latest and _version_tuple(latest) > _version_tuple(cur))
    return cur, latest, newer


def print_update_banner(out=None) -> None:
    import sys

    out = out or sys.stderr
    cache = _cache_read()
    today = time.strftime("%Y-%m-%d")
    if cache.get("banner_shown_on") == today:
        return
    cur, latest, newer = check_for_update()
    if not newer:
        return
    print(f"[browser-harness] update available: {cur} -> {latest}", file=out)
    print(
        "[browser-harness] agents: run `browser-harness --update -y` to upgrade and restart the daemon",
        file=out,
    )
    _cache_write({**cache, "banner_shown_on": today})


def _chrome_running() -> bool:
    import platform

    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.check_output(["tasklist"], text=True, timeout=5)
            names = ("chrome.exe", "msedge.exe")
        else:
            out = subprocess.check_output(["ps", "-A", "-o", "comm="], text=True, timeout=5)
            names = ("Google Chrome", "chrome", "chromium", "Microsoft Edge", "msedge")
        return any(n.lower() in out.lower() for n in names)
    except Exception:
        return False


def _open_chrome_inspect() -> None:
    import platform

    url = "chrome://inspect/#remote-debugging"
    if platform.system() == "Darwin":
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e", 'tell application "Google Chrome" to activate',
                    "-e", f'tell application "Google Chrome" to open location "{url}"',
                ],
                timeout=5,
                check=False,
            )
            return
        except Exception:
            pass
    try:
        import webbrowser

        webbrowser.open(url, new=2)
    except Exception:
        pass


def run_setup() -> int:
    print("browser-harness setup: attaching to your browser...")

    if daemon_alive():
        print("daemon already running; nothing to do.")
        return 0

    if not _chrome_running():
        print(
            "no Chrome/Edge process detected. "
            "please start your browser and rerun `browser-harness --setup`."
        )
        return 1

    try:
        ensure_daemon(wait=20.0)
        print("daemon is up.")
        return 0
    except RuntimeError as e:
        first_err = str(e)

    needs_inspect = _is_local_chrome_mode() and _needs_chrome_remote_debugging_prompt(first_err)
    if needs_inspect:
        print("chrome remote-debugging is not enabled on the current profile.")
        print("opening chrome://inspect/#remote-debugging -- in the tab that opens:")
        print("  1. if chrome shows the profile picker, pick your normal profile;")
        print("  2. tick 'Discover network targets' and click Allow if prompted.")
        _open_chrome_inspect()
    else:
        print(f"attach failed: {first_err}")
        print("retrying for up to 60s (chrome may still be starting up)...")

    deadline = time.time() + 60
    last = first_err
    while time.time() < deadline:
        try:
            ensure_daemon(wait=5.0)
            print("daemon is up.")
            return 0
        except RuntimeError as e:
            last = str(e)
            time.sleep(2)

    print(f"setup failed: {last}", file=sys.stderr)
    print("run `browser-harness --doctor` for diagnostics.", file=sys.stderr)
    return 1


def run_doctor() -> int:
    import platform

    cur = _version()
    mode = _install_mode()
    chrome = _chrome_running()
    daemon = daemon_alive()
    profile_use = shutil.which("profile-use") is not None
    api_key = bool(os.environ.get("BROWSER_USE_API_KEY"))
    latest = _latest_release_tag()
    newer = bool(cur and latest and _version_tuple(latest) > _version_tuple(cur))
    cur_display = cur or "(unknown)"

    def row(label: str, ok: bool, detail: str = "") -> None:
        mark = "ok  " if ok else "FAIL"
        print(f"  [{mark}] {label}{(' — ' + detail) if detail else ''}")

    print("browser-harness doctor")
    print(f"  platform          {platform.system()} {platform.release()}")
    print(f"  python            {sys.version.split()[0]}")
    print(f"  version           {cur_display} ({mode})")
    if latest:
        print(f"  latest release    {latest}" + (" (update available)" if newer else ""))
    else:
        print("  latest release    (could not reach github)")
    row("chrome running", chrome, "" if chrome else "start chrome/edge and rerun `browser-harness --setup`")
    row("daemon alive", daemon, "" if daemon else "run `browser-harness --setup` to attach")
    row(
        "profile-use installed",
        profile_use,
        "" if profile_use else "optional: curl -fsSL https://browser-use.com/profile.sh | sh",
    )
    row(
        "BROWSER_USE_API_KEY set",
        api_key,
        "" if api_key else "optional: needed only for cloud browsers / profile sync",
    )
    return 0 if (chrome and daemon) else 1


def _prompt_yes(question: str, default_yes: bool = True, yes: bool = False) -> bool:
    if yes:
        return True
    suffix = "[Y/n]" if default_yes else "[y/N]"
    try:
        ans = input(f"{question} {suffix} ").strip().lower()
    except EOFError:
        return default_yes
    if not ans:
        return default_yes
    return ans.startswith("y")


def run_update(yes: bool = False) -> int:
    cur, latest, newer = check_for_update()
    if cur and latest and not newer:
        print(f"browser-harness is up to date ({cur}).")
        return 0
    if cur and latest:
        print(f"updating browser-harness: {cur} -> {latest}")
    elif latest:
        print(f"installed version unknown; will try to update to {latest}.")
    else:
        print("could not reach github; will try to update anyway.")

    mode = _install_mode()
    if mode == "git":
        repo = _repo_dir()
        status = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True
        )
        if status.returncode != 0:
            print(f"git status failed: {status.stderr.strip()}", file=sys.stderr)
            return 1
        if status.stdout.strip():
            print(f"refusing to update: uncommitted changes in {repo}", file=sys.stderr)
            print(
                f"commit or stash them first, or run `git -C {repo} pull` yourself.",
                file=sys.stderr,
            )
            return 1
        r = subprocess.run(["git", "-C", str(repo), "pull", "--ff-only"])
        if r.returncode != 0:
            return r.returncode
    elif mode == "pypi":
        tool_upgrade = subprocess.run(["uv", "tool", "upgrade", "browser-harness"])
        if tool_upgrade.returncode != 0:
            pip = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "browser-harness"]
            )
            if pip.returncode != 0:
                return pip.returncode
    else:
        print("unknown install mode; can't auto-update.", file=sys.stderr)
        return 1

    cache = _cache_read()
    cache.pop("banner_shown_on", None)
    _cache_write(cache)

    if daemon_alive():
        if _prompt_yes(
            "restart the running daemon so it picks up the new code?",
            default_yes=True,
            yes=yes,
        ):
            restart_daemon()
            print("daemon stopped; it will auto-restart on next `browser-harness` call.")
        else:
            print(
                "daemon left running on old code. run `browser-harness` and it'll use the new code "
                "after the daemon recycles."
            )
    print("update complete.")
    return 0
