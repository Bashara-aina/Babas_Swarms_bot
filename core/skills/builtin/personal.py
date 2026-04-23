"""Personal project tracking skills."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime

from core.skills.registry import SKILL_REGISTRY, Skill

logger = logging.getLogger(__name__)


async def _rumahlabuh_status_handler(text: str) -> str:
    """Check rumahlabuh.com site status."""
    try:
        from tools.browser_agent import check_site_health

        result = await check_site_health("https://rumahlabuh.com")
        if "error" in result and result.get("status") == "unreachable":
            return f"❌ Rumah Labuh site is unreachable: {result.get('error', 'unknown')}"
        status = result.get("status", "unknown")
        load = result.get("load_time_ms", "?")
        http = result.get("http_status", "?")
        title = result.get("title", "N/A")
        icon = {"ok": "✅", "degraded": "⚠️", "unreachable": "❌"}.get(status, "❓")
        return f"{icon} Rumah Labuh Status\nStatus: {status.upper()}\nLoad: {load}ms\nHTTP: {http}\nTitle: {title}"
    except Exception as exc:
        return f"❌ Rumah Labuh check failed: {exc}"


async def _thesis_status_handler(text: str) -> str:
    """Get thesis progress status."""
    # Check if thesis checkpoint file exists
    checkpoint_path = os.path.expanduser("~/.swarm-bot/thesis_checkpoint.md")
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, "r") as f:
                content = f.read()
            return f"📚 Thesis Progress:\n\n{content[:500]}"
        except Exception:
            pass

    # Default status message
    return (
        "📚 Thesis Status\n\n"
        "No checkpoint file found. I can help you track thesis progress.\n"
        "Use /remember to save thesis milestones, or ask me to 'check thesis status' "
        "after setting up a checkpoint file."
    )


async def _cekwajar_status_handler(text: str) -> str:
    """Check CEKWAJAR scholarship status."""
    # This is a placeholder that returns instructions
    return (
        "🎓 CEKWAJAR Scholarship Status\n\n"
        "Current application status: Unknown\n"
        "Last checked: Never\n\n"
        "To track CEKWAJAR status:\n"
        "1. Check your email for updates\n"
        "2. Visit the CEKWAJAR portal\n"
        "3. Ask me to 'remember that CEKWAJAR status is [status]'"
    )


async def _gpu_training_status_handler(text: str) -> str:
    """Check GPU training job status."""
    # Try to find training logs
    log_paths = [
        "/home/newadmin/training_logs/latest.log",
        "/tmp/training.log",
        os.path.expanduser("~/training_logs/status.txt"),
    ]

    for log_path in log_paths:
        if os.path.exists(log_path):
            try:
                with open(log_path, "r") as f:
                    lines = f.readlines()
                    recent = "".join(lines[-50:])
                return f"🚀 GPU Training Status\n\n{recent[-1000:]}"
            except Exception:
                pass

    # Check if any training processes are running
    try:
        import subprocess

        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        training_procs = [
            line
            for line in result.stdout.split("\n")
            if "python" in line and ("train" in line.lower() or "gpu" in line.lower() or "model" in line.lower())
        ]
        if training_procs:
            lines = ["🚀 GPU Training - Active processes:\n"]
            for p in training_procs[:5]:
                lines.append(f"• {p[:150]}")
            return "\n".join(lines)
    except Exception:
        pass

    return "🚀 GPU Training Status\n\nNo active training jobs found.\nNo recent training logs detected."


async def _adb_scholarship_handler(text: str) -> str:
    """Check ADB scholarship status."""
    return (
        "🎓 ADB Scholarship Status\n\n"
        "Last checked: Unknown\n\n"
        "ADB Scholarship tracking requires:\n"
        "- Checking ADB portal for application updates\n"
        "- Verifying deadline status\n"
        "- Confirming document submission\n\n"
        "Ask me to 'remember that ADB status is [status]' to track manually."
    )


def _register_personal_skills() -> None:
    SKILL_REGISTRY.register(
        Skill(
            name="rumahlabuh_status",
            description="Check rumahlabuh.com site health and status",
            trigger_keywords=["rumahlabuh", "rumah labuh", "rumahlabuh.com", "site status"],
            handler=_rumahlabuh_status_handler,
            required_env_keys=[],
            category="personal",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="thesis_status",
            description="Get thesis progress and checkpoint status",
            trigger_keywords=["thesis", "thesis status", "research progress", "dissertation"],
            handler=_thesis_status_handler,
            required_env_keys=[],
            category="personal",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="cekwajar_status",
            description="Check CEKWAJAR scholarship application status",
            trigger_keywords=["cekwajar", "cek wajar", "scholarship status"],
            handler=_cekwajar_status_handler,
            required_env_keys=[],
            category="personal",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="gpu_training_status",
            description="Check GPU training job status and logs",
            trigger_keywords=["gpu training", "training status", "model training", "deep learning status"],
            handler=_gpu_training_status_handler,
            required_env_keys=[],
            category="personal",
        )
    )
    SKILL_REGISTRY.register(
        Skill(
            name="adb_scholarship",
            description="Check ADB scholarship application status",
            trigger_keywords=["adb", "adb scholarship", "asian development bank"],
            handler=_adb_scholarship_handler,
            required_env_keys=[],
            category="personal",
        )
    )


_register_personal_skills()
