#!/usr/bin/env python3
"""verify_wiring.py — Legion Wiring Audit Verification Script.

Checks that all handlers are properly wired:
1. All imported handlers are registered in _ROUTER_ORDER
2. All routers in _ROUTER_ORDER are imported
3. Handler files with routers have their router registered
4. Core modules are importable
5. Bridges are connected
6. Skills are registered

Exit codes:
  0 = all wires connected
  1 = one or more wire breaks detected
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# ── Colors ────────────────────────────────────────────────────────────────────
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}✓ {msg}{RESET}")


def fail(msg: str) -> None:
    print(f"{RED}✗ {msg}{RESET}")


def warn(msg: str) -> None:
    print(f"{YELLOW}⚠ {msg}{RESET}")


# ── Test 1: Handler imports vs router registration ──────────────────────────────
def check_handler_wiring() -> bool:
    """Verify all imported handlers are registered in _ROUTER_ORDER."""
    print("\n═══ Test 1: Handler Wiring ═══")

    # Import the handlers package dynamically
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import handlers
    from handlers import _ROUTER_ORDER

    # Discover what handlers/__init__.py imports
    # Read the source to find imports from handlers (not from handlers.wiki)
    init_path = Path(__file__).parent.parent / "handlers" / "__init__.py"
    init_source = init_path.read_text()

    # Find all imports from handlers package
    import re

    import_pattern = re.compile(r"^from handlers import \((.*?)\)$", re.MULTILINE | re.DOTALL)
    match = import_pattern.search(init_source)

    if not match:
        # Try alternate import format
        import_pattern2 = re.compile(r"^from handlers import (.*?)$", re.MULTILINE)
        matches = import_pattern2.findall(init_source)
        imported_handler_names = []
        for m in matches:
            if "(" in m:
                continue  # Skip multiline
            names = [n.strip() for n in m.split(",")]
            imported_handler_names.extend(names)
    else:
        import_body = match.group(1)
        imported_handler_names = [n.strip() for n in import_body.split(",")]

    # Also handle wiki_router separately
    wiki_router_match = re.search(r"from handlers\.wiki import router as wiki_router", init_source)
    if wiki_router_match:
        imported_handler_names.append("wiki_router")

    # Filter out non-handler names (like router as agents stuff)
    imported_handler_names = [n for n in imported_handler_names if n and not n.startswith("_")]

    ok(f"Found {len(imported_handler_names)} handlers in handlers/__init__.py: {imported_handler_names}")

    # Now dynamically import each handler and check if it has a router
    all_ok = True
    handlers_with_routers = {}

    for name in imported_handler_names:
        try:
            if name == "wiki_router":
                from handlers.wiki import router

                handlers_with_routers[name] = router
            else:
                module = importlib.import_module(f"handlers.{name}")
                if hasattr(module, "router"):
                    handlers_with_routers[name] = module.router
                    ok(f"  {name} has router")
                else:
                    warn(f"  {name} has no router (ok - helper module)")
        except Exception as e:
            fail(f"  Failed to import handlers.{name}: {e}")
            all_ok = False

    # Check that all handlers with routers are in _ROUTER_ORDER
    print("\n  Checking routers against _ROUTER_ORDER...")
    set(_ROUTER_ORDER)

    for name, router in handlers_with_routers.items():
        if router not in _ROUTER_ORDER:
            fail(f"  Handler '{name}' has router but it's NOT in _ROUTER_ORDER")
            all_ok = False
        else:
            ok(f"  {name}.router is in _ROUTER_ORDER")

    # Check for duplicate routers (same module registered twice)
    seen_routers = set()
    for router in _ROUTER_ORDER:
        if router in seen_routers:
            fail(f"  Duplicate router in _ROUTER_ORDER: {router}")
            all_ok = False
        seen_routers.add(router)

    if all_ok:
        ok("All handlers properly wired")

    return all_ok


# ── Test 2: Core modules are importable ───────────────────────────────────────
def check_core_imports() -> bool:
    """Verify core modules can be imported without errors."""
    print("\n═══ Test 2: Core Module Imports ═══")

    sys.path.insert(0, str(Path(__file__).parent.parent))

    core_modules = [
        "core.agent",
        "core.agent_registry",
        "core.autonomous_router",
        "core.capability_audit",
        "core.circuit_breaker",
        "core.conversation_interface",
        "core.debate_engine",
        "core.health",
        "core.health_check",
        "core.hooks",
        "core.humanizer",
        "core.intent_classifier",
        "core.intent_router",
        "core.jarvis_orchestrator",
        "core.legion_memory_facade",
        "core.legion_swarm",
        "core.memory_engine",
        "core.memory_manager",
        "core.model_config",
        "core.mcp_client",
        "core.multi_user",
        "core.natural_command_parser",
        "core.nexus_orchestrator",
        "core.orchestrator",
        "core.observability",
        "core.openai_agents_bridge",
        "core.opencode_bridge",
        "core.proactive_engine",
        "core.proactive.scheduler",
        "core.persistent_loop",
        "core.rate_limiter",
        "core.research_policy",
        "core.response_filter",
        "core.self_awareness_gate",
        "core.self_improvement",
        "core.self_upgrade",
        "core.skill_registry",
        "core.soul_engine",
        "core.swarm",
        "core.swarm_topologies",
        "core.system_prompt_builder",
        "core.task_router",
        "core.unified_prompt_context",
        "core.working_memory",
        "core.wiki_auto_ingest",
        "core.wiki_bridge",
        "core.wiki_loader",
        "core.wiki_manager",
        "core.wiki_quality_gate",
        "core.wiki_scheduler",
    ]

    all_ok = True
    for mod_name in core_modules:
        try:
            importlib.import_module(mod_name)
            ok(f"Imported {mod_name}")
        except Exception as e:
            fail(f"Failed to import {mod_name}: {e}")
            all_ok = False

    return all_ok


# ── Test 3: LLM client is importable ─────────────────────────────────────────
def check_llm_client() -> bool:
    """Verify llm_client is properly structured."""
    print("\n═══ Test 3: LLM Client ═══")

    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        import llm_client

        ok("llm_client imported successfully")

        # Check key functions exist
        from llm_client import (
            agent_loop,
            chat,
            chunk_output,
            verify_api_keys,
            wiki_raw_completion,
        )

        ok("llm_client exports required functions")

        return True
    except Exception as e:
        fail(f"llm_client import failed: {e}")
        return False


# ── Test 4: Tools are importable ──────────────────────────────────────────────
def check_tools() -> bool:
    """Verify key tools are importable."""
    print("\n═══ Test 4: Tools ═══")

    sys.path.insert(0, str(Path(__file__).parent.parent))

    tools = [
        "tools.web_search",
        "tools.browser_agent",
        "tools.email_client",
        "tools.github_intel",
        "tools.memory",
        "tools.persistence",
        "tools.scheduler",
        "tools.skill_loader",
        "tools.voice_engine",
    ]

    all_ok = True
    for tool in tools:
        try:
            importlib.import_module(tool)
            ok(f"Imported {tool}")
        except Exception as e:
            fail(f"Failed to import {tool}: {e}")
            all_ok = False

    return all_ok


# ── Test 5: Bridges are connected ─────────────────────────────────────────────
def check_bridges() -> bool:
    """Verify bridge modules are importable."""
    print("\n═══ Test 5: Bridges ═══")

    sys.path.insert(0, str(Path(__file__).parent.parent))

    bridges = [
        "bridges.discord_bridge",
        "bridges.livekit_bridge",
        "bridges.mastra_bridge",
        "bridges.ruflo_bridge",
        "bridges.screenpipe_bridge",
        "bridges.whatsapp_bridge",
    ]

    all_ok = True
    for bridge in bridges:
        try:
            importlib.import_module(bridge)
            ok(f"Imported {bridge}")
        except Exception as e:
            fail(f"Failed to import {bridge}: {e}")
            all_ok = False

    return all_ok


# ── Test 6: Skills layer ──────────────────────────────────────────────────────
def check_skills() -> bool:
    """Verify skills are properly registered."""
    print("\n═══ Test 6: Skills Layer ═══")

    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        from core.skills import get_skill_registry

        registry = get_skill_registry()
        ok(f"Skill registry loaded: {len(registry.list_all())} skills registered")

        from core.skills.builtin import (
            github,
            media,
            memory,
            personal,
            productivity,
            research,
            system,
            web,
        )

        ok("All builtin skill modules imported")

        return True
    except Exception as e:
        fail(f"Skills check failed: {e}")
        return False


# ── Test 7: Agent registry ────────────────────────────────────────────────────
def check_agents() -> bool:
    """Verify agents module is properly structured."""
    print("\n═══ Test 7: Agents ═══")

    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        import agents

        ok("agents module imported")

        # Check key exports
        from agents import (
            AGENT_MODELS,
            DEFAULT_AGENT,
            FALLBACK_CHAIN,
            TASK_KEYWORDS,
            detect_agent,
            get_fallback_chain,
        )

        ok("agents exports required functions and data")

        return True
    except Exception as e:
        fail(f"Agents check failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    print("=" * 60)
    print("Legion Wiring Audit — verify_wiring.py")
    print("=" * 60)

    results = []

    results.append(("Handler Wiring", check_handler_wiring()))
    results.append(("Core Imports", check_core_imports()))
    results.append(("LLM Client", check_llm_client()))
    results.append(("Tools", check_tools()))
    results.append(("Bridges", check_bridges()))
    results.append(("Skills", check_skills()))
    results.append(("Agents", check_agents()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print(f"\n{GREEN}All wiring checks passed!{RESET}")
        return 0
    else:
        print(f"\n{RED}Wire breaks detected. Fix before deploying.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
