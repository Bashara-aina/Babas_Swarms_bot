"""Natural command parser — maps casual Indonesian/English phrases to internal commands.

Eliminates slash command dependency. Bashara types naturally and Legion acts.

Usage:
    from core.natural_command_parser import parse_natural_command
    result = parse_natural_command("cek rumahlabuh.com SEO-nya")
    # → {"intent": "web_audit", "action": "check_seo", "args": {"target": "rumahlabuh.com"}, "confidence": 0.9}

This module provides a thin NLP layer that maps casual phrases to internal
command names WITHOUT requiring slash prefix. It runs BEFORE slash-command
routing in the message handler.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class NaturalCommand:
    """Parsed result from natural language input."""

    intent: str  # e.g. "web_audit", "shell_exec", "chitchat"
    action: str  # e.g. "check_seo", "run_command"
    args: dict[str, str]
    confidence: float  # 0.0–1.0
    original: str  # original message


# ── Trigger patterns ──────────────────────────────────────────────────────────

# Intent → list of (regex_pattern, parser_fn) tuples
# Parser fn receives match groups, returns dict of args

_TRIGGERS: list[tuple[str, str, re.Pattern, callable]] = [
    # web_audit — SEO, speed, loading checks
    (
        "web_audit",
        "check_seo",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?(?:cek|check|buka|lihat)\s+)?"
            r"(?:seo|website|speed|loading|performance|page\s*speed|lighthouse)\s*(?:nya?|nya\s+(\S+))?",
            re.IGNORECASE,
        ),
        lambda m: {"target": m.group(1) or ""},
    ),
    (
        "web_audit",
        "check_seo",
        re.compile(
            r"(?i)^(?:tolong\s+)?(?:cek|check)\s+(?:rumahlabuh|www\.\S+|\S+\.(?:com|io|org|net|id))\s*(?:seo|speed|website|loading)?",
            re.IGNORECASE,
        ),
        lambda m: {"target": (m.group(1) or m.group(0)).strip()},
    ),
    (
        "web_audit",
        "check_site",
        re.compile(
            r"(?i)^(?:tolong\s+)?(?:cek|check|buka|lihat)\s+(?:website|site|web)\s*(?:nya|yang)?\s*(\S+)?",
            re.IGNORECASE,
        ),
        lambda m: {"target": m.group(1) or ""},
    ),
    # shell_exec — run commands
    (
        "shell_exec",
        "run_command",
        re.compile(
            r"(?i)^(?:tolong\s+)?(?:jalanin|execute|run|ketik|ketikkan|kerjain)\s+(?:di\s+)?(?:terminal|shell|cmd)?\s*[:\-]?\s*(.+)$",
            re.IGNORECASE,
        ),
        lambda m: {"command": m.group(1).strip()},
    ),
    (
        "shell_exec",
        "run_command",
        re.compile(
            r"(?i)^(?:sudo\s+)?(?:rm\s+|chmod\s+|chown\s+|systemctl\s+)",
            re.IGNORECASE,
        ),
        lambda m: {"command": m.group(0).strip(), "warning": "sudo"},
    ),
    # service_restart — restart bot or services
    (
        "service_restart",
        "restart",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:restart|reboot)\s*(?:legion|bot|nya|ulang)?$",
            re.IGNORECASE,
        ),
        lambda m: {},
    ),
    # screen_capture — screenshot
    (
        "screen_capture",
        "screenshot",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:screenshot|screen|tangkapan\s+(?:layar|hasil)|lihat\s+layar|capture)\s*$",
            re.IGNORECASE,
        ),
        lambda m: {},
    ),
    # screen_capture with analysis
    (
        "screen_capture",
        "analyze_screen",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:cek|check|analyze|lihat)\s+(?:layar|screen|desktop|display|apa\s+yang\s+(?:ada|terlihat|displayed))$",
            re.IGNORECASE,
        ),
        lambda m: {"analyze": "true"},
    ),
    # app_launch — open apps
    (
        "app_launch",
        "open_app",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:buka|open|launch)\s+(?:app\s+)?(\S+)(?:\s+(?:di|dengan|di\s+)?(\S+))?$",
            re.IGNORECASE,
        ),
        lambda m: {"app": m.group(1), "via": m.group(2) or ""},
    ),
    # api_key_check — check API keys
    (
        "api_key_check",
        "check_keys",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:(?:cek|check)\s+key(?:s|nya|api)?)$",
            re.IGNORECASE,
        ),
        lambda m: {},
    ),
    # web_scrape — scrape URL
    (
        "web_scrape",
        "scrape_url",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:scrape|crawl|ambil\s+(?:data|isi))\s+(?:dari\s+)?(.+)$",
            re.IGNORECASE,
        ),
        lambda m: {"url": m.group(1).strip()},
    ),
    # email_read — check email
    (
        "email_read",
        "check_email",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:(?:cek|check|read|baca)\s+)?(?:email|inbox|mail|kotak\s+surat)$",
            re.IGNORECASE,
        ),
        lambda m: {},
    ),
    # reminder — set reminder
    (
        "reminder",
        "set_reminder",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:ingatkan|remind|ingetin)\s+(?:aku|ku|saya)?\s*(?:pada|di|jam|pukul)?\s*(\d{1,2}[:\.]?\d{0,2}\s*(?:am|pm|jst|wib)?)",
            re.IGNORECASE,
        ),
        lambda m: {"time": m.group(1).strip()},
    ),
    # file_read — read file content
    (
        "file_read",
        "read_file",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:(?:baca|read|lihat)\s+(?:file|files|doc|dokumen|isi\s+file))\s+(.+)$",
            re.IGNORECASE,
        ),
        lambda m: {"path": m.group(1).strip()},
    ),
    # research — web research
    (
        "research",
        "research",
        re.compile(
            r"(?i)^(?:(?:tolong\s+)?)?(?:research|cari\s+(?:di\s+)?internet|telusuri)\s+(.+)$",
            re.IGNORECASE,
        ),
        lambda m: {"query": m.group(1).strip()},
    ),
    # git operations
    (
        "git",
        "git",
        re.compile(
            r"(?i)^(?:git\s+(?:commit|push|pull|status|log|diff|branch|stash|checkout))$",
            re.IGNORECASE,
        ),
        lambda m: {"command": m.group(0).strip()},
    ),
]


def parse_natural_command(message: str) -> NaturalCommand:
    """Parse a free-text message and extract intent + args.

    If no pattern matches, returns a CASUAL_CHAT result with confidence 0.0.

    Args:
        message: The raw user message (stripped, no leading /)

    Returns:
        NaturalCommand with parsed intent, action, args, and confidence
    """
    if not message or not message.strip():
        return NaturalCommand(
            intent="casual_chat",
            action="respond",
            args={},
            confidence=0.0,
            original=message,
        )

    msg = message.strip()

    # Try each trigger pattern
    for intent, action, pattern, parser in _TRIGGERS:
        match = pattern.match(msg)
        if match:
            try:
                args = parser(match)
            except Exception:
                args = {}
            return NaturalCommand(
                intent=intent,
                action=action,
                args=args,
                confidence=0.85,
                original=message,
            )

    # No match — casual chat
    return NaturalCommand(
        intent="casual_chat",
        action="respond",
        args={},
        confidence=0.0,
        original=message,
    )


def is_actionable(message: str, min_confidence: float = 0.6) -> bool:
    """Return True if the message should be routed to an action handler.

    Args:
        message: Raw user message
        min_confidence: Minimum confidence to consider actionable (default 0.6)
    """
    result = parse_natural_command(message)
    return result.confidence >= min_confidence and result.intent != "casual_chat"


def get_action(message: str) -> Optional[NaturalCommand]:
    """Get the parsed action for a message, or None if not actionable."""
    result = parse_natural_command(message)
    if result.confidence < 0.6 or result.intent == "casual_chat":
        return None
    return result
