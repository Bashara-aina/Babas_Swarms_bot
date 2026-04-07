from __future__ import annotations

import importlib.util
import os
import subprocess
from typing import Any

FEATURE_FLAGS: dict[str, dict[str, Any]] = {
    "openai_agents": {"pkg": "agents", "env": None, "enabled": False},
    "owl": {"pkg": "camel", "env": None, "enabled": False},
    "ag2": {"pkg": "autogen", "env": None, "enabled": False},
    "smolagents": {"pkg": "smolagents", "env": None, "enabled": False},
    "pydantic_ai": {"pkg": "pydantic_ai", "env": None, "enabled": False},
    "agentops": {"pkg": "agentops", "env": "AGENTOPS_API_KEY", "enabled": False},
    "mirofish": {"pkg": None, "env": None, "enabled": False},
    "ruflo": {"pkg": None, "env": "OPENROUTER_API_KEY", "enabled": False},
    "gemma4_local": {"pkg": None, "env": None, "enabled": False},
}


def run_health_check() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for feature, cfg in FEATURE_FLAGS.items():
        available = True
        reason = "OK"

        pkg = cfg.get("pkg")
        if pkg and importlib.util.find_spec(str(pkg)) is None:
            available = False
            reason = f"pip package '{pkg}' not installed"

        env_name = cfg.get("env")
        if env_name and available and not os.getenv(str(env_name)):
            available = False
            reason = f"env var '{env_name}' not set (optional feature)"

        if feature == "gemma4_local":
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
                available = "gemma4:e4b" in result.stdout
                reason = "OK" if available else "Run: ollama pull gemma4:e4b"
            except Exception:
                available = False
                reason = "Ollama not running or not installed"

        if feature == "mirofish":
            available = os.path.exists("tools/mirofish")
            reason = "OK" if available else "tools/mirofish not found"

        if feature == "ruflo":
            ruflo_js = os.path.exists("tools/ruflo/server.js")
            available = available and ruflo_js
            if not ruflo_js:
                reason = "tools/ruflo/server.js not found"

        FEATURE_FLAGS[feature]["enabled"] = bool(available)
        results[feature] = {"available": bool(available), "reason": reason}

    return results


def print_health_report(results: dict[str, dict[str, Any]]) -> None:
    print("\n" + "=" * 60)
    print("  LEGIONSWARM v5 — STARTUP HEALTH CHECK")
    print("=" * 60)
    for feature, status in results.items():
        icon = "✅" if status.get("available") else "⚠️ "
        print(f"  {icon} {feature:<22} {status.get('reason', '')}")
    print("=" * 60 + "\n")
