"""Per-user working memory — short-lived focus, open threads, follow-ups.

Persists across restarts under ~/.legionswarm/working/{user_id}.json so routed
handlers and chat share continuity without slash commands.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ROOT = Path.home() / ".legionswarm" / "working"

_MAX_OPEN_THREADS = int(os.getenv("LEGION_WORKING_MEMORY_MAX_THREADS", "8"))
_MAX_THREAD_LEN = 220
_MAX_FOCUS_LEN = 300
_MAX_FOLLOWUPS = 5

_ACK_RE = re.compile(
    r"^(ok|okay|yep|yeah|thanks?|thank you|thx|sip|siap|mantap|got it|noted|boleh|"
    r"ya\s*udah|sudah|done|nice|perfect|works|clear|understood|paham|oke)\b",
    re.I | re.M,
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _path_for(user_id: str) -> Path:
    try:
        _ROOT.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    safe = re.sub(r"[^\w\-]", "_", str(user_id))[:64] or "default"
    return _ROOT / f"{safe}.json"


def _default_state() -> dict[str, Any]:
    return {
        "version": 2,
        "updated_at": "",
        "turn_count": 0,
        "current_focus": "",
        "open_threads": [],
        "pending_followups": [],
        "last_user_preview": "",
        "last_agent": "",
        "last_route": "",
    }


def _strip_html(text: str) -> str:
    t = _HTML_TAG_RE.sub(" ", text or "")
    return " ".join(t.split())


def _normalize_key(text: str) -> str:
    t = _strip_html(text).lower()
    t = re.sub(r"[^\w\s\u0080-\uFFFF]", " ", t)
    return " ".join(t.split())


def load_state(user_id: str) -> dict[str, Any]:
    p = _path_for(user_id)
    if not p.exists():
        return _default_state()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_state()
        out = _default_state()
        out.update(data)
        out.setdefault("open_threads", [])
        out.setdefault("pending_followups", [])
        out.setdefault("turn_count", 0)
        out.setdefault("last_route", "")
        if int(out.get("version", 1)) < 2:
            out["version"] = 2
        return out
    except Exception as e:
        logger.debug("[working_memory] load failed: %s", e)
        return _default_state()


def _save_state(user_id: str, state: dict[str, Any]) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        p = _path_for(user_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("[working_memory] save failed: %s", e)


def _infer_focus(user_text: str) -> str:
    t = " ".join((user_text or "").strip().split())
    if len(t) <= _MAX_FOCUS_LEN:
        return t
    return t[: _MAX_FOCUS_LEN - 1] + "…"


def _extract_questions(plain: str) -> list[str]:
    """Pull closing questions from assistant text (HTML-safe)."""
    plain = _strip_html(plain)
    out: list[str] = []
    for m in re.finditer(r"([^?.!]{8,180}\?)", plain[:2500]):
        q = m.group(1).strip()
        if q and q not in out:
            out.append(q[:_MAX_THREAD_LEN])
        if len(out) >= 3:
            break
    return out


def _dedupe_threads(threads: list[str], new_line: str) -> list[str]:
    nk = _normalize_key(new_line)
    if not nk:
        return threads
    kept: list[str] = []
    for t in threads:
        if nk in _normalize_key(t) or _normalize_key(t) in nk:
            continue
        kept.append(t)
    return kept


def build_prompt_block(user_id: str) -> str:
    """Compact block for system prompt (empty if disabled or empty state)."""
    if not user_id:
        return ""
    if os.getenv("LEGION_WORKING_MEMORY_ENABLED", "1").strip().lower() in (
        "0", "false", "no", "off",
    ):
        return ""
    st = load_state(user_id)
    parts: list[str] = ["[WORKING MEMORY — session continuity]"]
    tc = st.get("turn_count")
    if isinstance(tc, int) and tc > 0:
        parts.append(f"Exchange count this session (approx): {tc}")
    if st.get("current_focus"):
        parts.append(f"Current focus: {st['current_focus']}")
    threads = st.get("open_threads") or []
    if threads:
        parts.append("Open threads (newest first):")
        for th in threads[:_MAX_OPEN_THREADS]:
            parts.append(f"  • {th}")
    follow = st.get("pending_followups") or []
    if follow:
        parts.append("Your last reply asked them about:")
        for f in follow[:_MAX_FOLLOWUPS]:
            parts.append(f"  • {f}")
    meta: list[str] = []
    if st.get("last_agent"):
        meta.append(f"last agent: {st['last_agent']}")
    if st.get("last_route"):
        meta.append(f"last NL route: {st['last_route']}")
    if meta:
        parts.append("(" + " | ".join(meta) + ")")
    if len(parts) <= 1:
        return ""
    return "\n".join(parts)


def record_turn(
    user_id: str,
    user_message: str,
    assistant_snippet: str = "",
    agent_key: str = "",
    routing_hint: str = "",
) -> None:
    """Update working memory after a successful exchange (final assistant text)."""
    if not user_id:
        return
    if os.getenv("LEGION_WORKING_MEMORY_ENABLED", "1").strip().lower() in (
        "0", "false", "no", "off",
    ):
        return
    um = (user_message or "").strip()
    if len(um) < 2:
        return
    st = load_state(user_id)
    st["turn_count"] = int(st.get("turn_count") or 0) + 1
    st["last_user_preview"] = um[:220]
    st["current_focus"] = _infer_focus(um)
    if agent_key:
        st["last_agent"] = str(agent_key)[:80]
    if routing_hint:
        st["last_route"] = str(routing_hint)[:100]

    # Short acknowledgements — clear noise, don't stack threads
    um_one_line = um.split("\n")[0].strip()
    if len(um) < 90 and _ACK_RE.match(um_one_line):
        fol = list(st.get("pending_followups") or [])
        if fol:
            fol.pop(0)
        st["pending_followups"] = fol
        _save_state(user_id, st)
        return

    # Threads: substantive user turns
    word_n = len(um.split())
    if "?" in um or word_n > 12 or len(um) > 80:
        line = um.replace("\n", " ").strip()[:_MAX_THREAD_LEN]
        threads: list[str] = list(st.get("open_threads") or [])
        threads = _dedupe_threads(threads, line)
        if line:
            nk = _normalize_key(line)
            if not any(_normalize_key(t) == nk for t in threads):
                threads.insert(0, line)
        st["open_threads"] = threads[:_MAX_OPEN_THREADS]

    # Follow-ups from assistant (plain questions)
    asn = (assistant_snippet or "").strip()
    if asn:
        qs = _extract_questions(asn)
        fol = list(st.get("pending_followups") or [])
        for q in qs:
            if q and q not in fol:
                fol.insert(0, q)
        st["pending_followups"] = fol[:_MAX_FOLLOWUPS]

    _save_state(user_id, st)


def note_thread(user_id: str, thread_line: str) -> None:
    """Explicitly add an open thread (e.g. from a handler handoff)."""
    if not user_id or not thread_line.strip():
        return
    st = load_state(user_id)
    threads = list(st.get("open_threads") or [])
    line = thread_line.strip()[:_MAX_THREAD_LEN]
    threads = _dedupe_threads(threads, line)
    if line:
        nk = _normalize_key(line)
        if not any(_normalize_key(t) == nk for t in threads):
            threads.insert(0, line)
    st["open_threads"] = threads[:_MAX_OPEN_THREADS]
    _save_state(user_id, st)


def clear_session(user_id: str) -> None:
    """Reset working memory for a user (e.g. /newchat)."""
    if not user_id:
        return
    try:
        p = _path_for(user_id)
        if p.exists():
            p.unlink()
    except OSError as e:
        logger.debug("[working_memory] clear failed: %s", e)
