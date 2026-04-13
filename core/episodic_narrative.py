"""Episodic Narrative — converts isolated memory facts into coherent narrative context.

Instead of:
  "User said: RTX 3060"
  "User said: thesis deadline July"

Legion builds:
  "Last week Bashara was debugging the FiLM conditioning module
   in their thesis model. They were frustrated with overfitting.
   Their machine has an RTX 3060. Thesis deadline is July 2026."

This narrative is injected AFTER memory as a human-readable context summary.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

NARRATIVE_PATH = Path(os.path.expanduser("~/.legion/narrative.json"))
NARRATIVE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_narrative() -> dict:
    if NARRATIVE_PATH.exists():
        try:
            return json.loads(NARRATIVE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "current_focus": "",
        "recent_wins": [],
        "current_struggles": [],
        "ongoing_projects": {
            "legion_bot": "Babas_Swarms_bot — multi-agent Telegram bot, active development (RTX 3060 + systemd)",
            "thesis": (
                "WorkerNet IKEA: assembly action recognition in video — ResNet-50-FPN backbone, "
                "3 task heads (Detection + Pose + Activity), FiLM conditioning module, "
                "Kendall uncertainty weighting. Dataset: 685,516 frames, 254 videos, 33 actions. "
                "Deadline: July 2026, Shibaura Institute of Technology. "
                "Current status: Epoch 74+ (as of 2026-03-28). "
                "Known issue: FiLM gradient blocking prevents activity loss from improving pose quality."
            ),
            "cekwajar_id": (
                "Indonesian wage verification SaaS — Next.js + Supabase + Midtrans. "
                "Validates formal/informal worker wages against Indonesian wage standards. "
                "Managed externally (no local DB)."
            ),
            "rumahlabuh": (
                "Rental booking platform for Labuh Banyu & Labuh Biru properties (Koto City). "
                "Next.js + Supabase (rooms, bookings, payments, branches tables) + Midtrans payment gateway. "
                "Tracks tenant contracts, extensions, and payment status. "
                "Admin panel at /admin route."
            ),
        },
        "last_updated": 0,
        "conversation_count": 0,
    }


def build_narrative_context(query: str) -> str:
    """Build a narrative paragraph from stored episodic context."""
    n = _load_narrative()
    parts = []

    focus = n.get("current_focus", "")
    if focus:
        parts.append(f"Currently focused on: {focus}.")

    struggles = n.get("current_struggles", [])
    if struggles:
        parts.append(f"Recently dealing with: {', '.join(struggles[:2])}.")

    wins = n.get("recent_wins", [])
    if wins:
        parts.append(f"Recent wins: {', '.join(wins[:2])}.")

    projects = n.get("ongoing_projects", {})
    query_lower = query.lower()
    relevant_projects = []
    for name, desc in projects.items():
        keywords = name.replace("_", " ").split()
        if any(k in query_lower for k in keywords):
            relevant_projects.append(desc)
    if relevant_projects:
        parts.append(f"Relevant project: {relevant_projects[0]}.")

    if not parts:
        return ""

    return (
        "[Episodic context — what Legion knows about Bashara's current situation:]\n"
        + " ".join(parts)
        + "\n[End episodic context]"
    )


def update_narrative_from_conversation(user_msg: str, assistant_response: str) -> None:
    """Update narrative based on conversation. Called after each turn (non-blocking)."""
    n = _load_narrative()
    n["conversation_count"] = n.get("conversation_count", 0) + 1
    n["last_updated"] = time.time()

    msg = user_msg.lower()

    focus_signals = {
        "thesis": "thesis model development (ResNet-50 + FiLM, assembly action recognition)",
        "rumahlabuh": "rumahlabuh.com development",
        "cekwajar": "cekwajar.id development",
        "legion": "Legion bot development",
        "audit": "Legion bot audit and improvements",
        "deploy": "deployment and DevOps",
    }
    for keyword, focus_desc in focus_signals.items():
        if keyword in msg:
            n["current_focus"] = focus_desc
            break

    win_signals = ["it works", "berhasil", "fixed it", "done", "deployed", "shipped"]
    if any(w in msg for w in win_signals):
        win_entry = user_msg[:80].strip()
        wins = n.get("recent_wins", [])
        if win_entry not in wins:
            wins.insert(0, win_entry)
            n["recent_wins"] = wins[:5]

    struggle_signals = ["not working", "error", "bug", "broken", "help", "stuck"]
    if any(w in msg for w in struggle_signals):
        struggle = user_msg[:80].strip()
        struggles = n.get("current_struggles", [])
        if struggle not in struggles:
            struggles.insert(0, struggle)
            n["current_struggles"] = struggles[:5]

    NARRATIVE_PATH.write_text(json.dumps(n, indent=2))
