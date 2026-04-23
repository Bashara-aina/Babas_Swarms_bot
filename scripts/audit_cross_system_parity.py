#!/usr/bin/env python3
"""Audit and optionally fix capability parity across Claude/OpenCode/Legion/Copilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

SHARED_AGENT_FILES = ("coding.md", "reviewer.md", "researcher.md", "README.md")

COPILOT_INSTRUCTIONS = """# Copilot Instructions — Legion/OpenCode/Claude Capability Parity

This repository uses one shared capability contract across **Copilot**, **Claude Code**,
**OpenCode**, and **LegionBot**.

## Source of Truth
1. Project engineering contract: `AGENTS.md`
2. Claude deep policy: `CLAUDE.md`
3. Shared agent definitions: `.claude/skills/legiona/`
4. OpenCode mirror of shared agents: `.opencode/agents/legiona/`
5. Legion skill registry: `skills/manifest.json` and `config/legion_skills.json`

## Parity Rules (mandatory)
1. Keep `.claude/skills/legiona/*.md` and `.opencode/agents/legiona/*.md` identical.
2. Do not introduce system-only capabilities unless they are intentionally host-specific.
3. All cross-system bridge logic must live in:
   - `core/opencode_bridge.py`
   - `core/claude_code_bridge.py`
   - `core/legion_callback_bridge.py`
4. For coding tasks, follow the same anti-hallucination guarantees used by `/swarm`.

## Capability Baseline
- Shared coding, reviewing, and research agents (`legiona`).
- Cross-system callback directives (`@claude`, `@legion`).
- Joint memory read/write via `core/joint_memory.py`.
- Telegram execution bridge for Legion via `core/opencode_bridge.py`.
- MCP web intelligence baseline:
  - `firecrawl` server (`firecrawl-mcp`)
  - `exa` server (`exa-mcp-server`)

## LLM Safety Notes for Config Editors
1. Do not delete or rewrite MCP server entries for `firecrawl` and `exa` unless the owner requests removal.
2. Keep secrets in environment variables only (`FIRECRAWL_API_KEY`, `EXA_API_KEY`).
3. Do not replace the MiniMax-through-Anthropic-compatible setup in `.claude/settings.json`.
"""


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _check_legiona_parity(root: Path) -> dict[str, Any]:
    claude = root / ".claude" / "skills" / "legiona"
    opencode = root / ".opencode" / "agents" / "legiona"
    report: dict[str, Any] = {"missing_in_opencode": [], "mismatched": [], "ok": []}

    for name in SHARED_AGENT_FILES:
        src = claude / name
        dst = opencode / name
        if not src.exists():
            report["mismatched"].append(f"missing-source:{src}")
            continue
        if not dst.exists():
            report["missing_in_opencode"].append(name)
            continue
        if _sha256(src) != _sha256(dst):
            report["mismatched"].append(name)
        else:
            report["ok"].append(name)
    return report


def _fix_legiona_parity(root: Path) -> None:
    claude = root / ".claude" / "skills" / "legiona"
    opencode = root / ".opencode" / "agents" / "legiona"
    opencode.mkdir(parents=True, exist_ok=True)
    for name in SHARED_AGENT_FILES:
        src = claude / name
        if src.exists():
            shutil.copy2(src, opencode / name)


def _check_legion_capability_registry(root: Path) -> dict[str, Any]:
    manifest = _load_json(root / "skills" / "manifest.json")
    registry = _load_json(root / "config" / "legion_skills.json")
    manifest_ids = {item.get("id") for item in manifest.get("skills", []) if item.get("id")}
    registry_names = {
        item.get("name") for item in registry.get("skills", []) if item.get("name")
    }

    missing_in_manifest = sorted(registry_names - manifest_ids)
    return {
        "manifest_count": len(manifest_ids),
        "registry_count": len(registry_names),
        "missing_in_manifest": missing_in_manifest,
    }


def _check_copilot_contract(root: Path) -> dict[str, Any]:
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return {"exists": False, "mentions_legiona": False}
    text = path.read_text(encoding="utf-8")
    return {
        "exists": True,
        "mentions_legiona": "legiona" in text.lower(),
        "mentions_mcp_baseline": "mcp web intelligence baseline" in text.lower(),
    }


def _extract_mcp_server_names(obj: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    mcp_servers = obj.get("mcpServers")
    if isinstance(mcp_servers, dict):
        names.update(str(k) for k in mcp_servers.keys())
    servers = obj.get("servers")
    if isinstance(servers, dict):
        names.update(str(k) for k in servers.keys())
    return names


def _check_mcp_parity(root: Path) -> dict[str, Any]:
    required = {"firecrawl", "exa"}
    claude = _load_json(root / ".claude" / "settings.json")
    opencode = _load_json(root / ".opencode" / "opencode.json")
    vscode = _load_json(root / ".vscode" / "mcp.json")

    claude_names = _extract_mcp_server_names(claude)
    opencode_names = _extract_mcp_server_names(opencode)
    vscode_names = _extract_mcp_server_names(vscode)

    return {
        "required": sorted(required),
        "claude_missing": sorted(required - claude_names),
        "opencode_missing": sorted(required - opencode_names),
        "copilot_missing": sorted(required - vscode_names),
    }


def _fix_copilot_contract(root: Path) -> None:
    path = root / ".github" / "copilot-instructions.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(COPILOT_INSTRUCTIONS, encoding="utf-8")


def run_audit(root: Path, fix: bool) -> dict[str, Any]:
    if fix:
        _fix_legiona_parity(root)
        _fix_copilot_contract(root)

    report = {
        "legiona_parity": _check_legiona_parity(root),
        "legion_registry": _check_legion_capability_registry(root),
        "copilot_contract": _check_copilot_contract(root),
        "mcp_parity": _check_mcp_parity(root),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--fix", action="store_true", help="Fix parity drift")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = run_audit(root, fix=args.fix)

    print(json.dumps(report, indent=2, sort_keys=True))

    parity = report["legiona_parity"]
    copilot = report["copilot_contract"]
    registry = report["legion_registry"]
    mcp = report["mcp_parity"]
    has_errors = bool(parity["missing_in_opencode"] or parity["mismatched"])
    has_errors = has_errors or not copilot["exists"] or not copilot["mentions_legiona"] or not copilot["mentions_mcp_baseline"]
    has_errors = has_errors or bool(registry["missing_in_manifest"])
    has_errors = has_errors or bool(mcp["claude_missing"] or mcp["opencode_missing"] or mcp["copilot_missing"])
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
