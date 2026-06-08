---
name: tools
description: "Skill for the Tools area of swarm-bot."
---

# Tools

"tools area"

## When to Use

- Working with code in `ext/`
- Understanding how confirm_action, list_pending, main work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/tools/mcp_tool.py` | _ensure_mcp_loop, shutdown_mcp_servers, _shutdown, discover_mcp_tools, session_kwargs (+63) |
| `ext/hermes-agent/tools/skills_hub.py` | search, _parse_index, _wrap_identifier, _featured_skills, _meta_from_search_item (+57) |
| `ext/hermes-agent/tools/browser_tool.py` | _start_browser_cleanup_thread, _get_session_info, _requires_real_termux_browser_install, _is_local_mode, _write_owner_pid (+45) |
| `ext/hermes-agent/tools/tts_tool.py` | _generate_openai_tts, _import_kittentts, _is_command_tts_voice_compatible, _has_ffmpeg, _convert_to_opus (+40) |
| `ext/hermes-agent/tests/tools/test_mcp_tool.py` | test_no_servers_safe, test_shutdown_clears_servers, test_shutdown_deregisters_registered_tools, test_shutdown_handles_errors, test_shutdown_is_parallel (+40) |
| `ext/hermes-agent/tools/web_tools.py` | _get_firecrawl_gateway_url, _has_env, _load_web_config, _get_backend, _is_backend_available (+35) |
| `ext/hermes-agent/tools/terminal_tool.py` | check_terminal_requirements, _check_disk_usage_warning, _check_all_guards, _validate_workdir, _handle_sudo_failure (+27) |
| `ext/hermes-agent/tests/tools/test_skill_manager_tool.py` | _skill_dir, _pin, test_edit_refuses_pinned, test_patch_refuses_pinned, test_patch_supporting_file_refuses_pinned (+27) |
| `ext/hermes-agent/tools/approval.py` | register_gateway_notify, unregister_gateway_notify, resolve_gateway_approval, has_blocking_approval, get_current_session_key (+25) |
| `ext/hermes-agent/tools/send_message_tool.py` | _handle_send, _get_cron_auto_delivery_target, _maybe_skip_cron_duplicate_send, _error, _send_to_platform (+23) |

## Entry Points

Start here when exploring this area:

- **`confirm_action`** (Function) — `task_orchestrator.py:151`
- **`list_pending`** (Function) — `task_orchestrator.py:208`
- **`main`** (Function) — `scripts/generate_prompts.py:17`
- **`fix_file`** (Function) — `scripts/fix_imports.py:70`
- **`main`** (Function) — `scripts/fix_imports.py:87`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `LoginRequest` | Class | `tools/scaffolder_auth.py` | 63 |
| `confirm_action` | Function | `task_orchestrator.py` | 151 |
| `list_pending` | Function | `task_orchestrator.py` | 208 |
| `main` | Function | `scripts/generate_prompts.py` | 17 |
| `fix_file` | Function | `scripts/fix_imports.py` | 70 |
| `main` | Function | `scripts/fix_imports.py` | 87 |
| `file_info` | Function | `tools/documents.py` | 473 |
| `explain_codebase` | Function | `tools/codebase_reader.py` | 156 |
| `detect_agent` | Function | `core/agent_registry.py` | 682 |
| `list_agents` | Function | `core/agent_registry.py` | 752 |
| `load_mcp_config` | Function | `core/mcp_client.py` | 18 |
| `check_server_health` | Function | `core/mcp_client.py` | 533 |
| `run_health_check` | Function | `core/health_check.py` | 12 |
| `summary` | Function | `core/app_context.py` | 33 |
| `list_pending` | Function | `core/orchestrator.py` | 185 |
| `format_debate_for_telegram` | Function | `core/orchestrator.py` | 477 |
| `cmd_om_stats` | Function | `handlers/brain.py` | 117 |
| `cmd_harvest_stats` | Function | `handlers/harvest_review.py` | 240 |
| `detect_agent` | Function | `agents/__init__.py` | 1682 |
| `route_task_complexity` | Function | `core/orchestrators/ag2_orchestrator.py` | 153 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_msg_from_peer → Get_hermes_home` | cross_community | 9 |
| `On_startup → Get_hermes_home` | cross_community | 9 |
| `On_startup → Write_txn` | cross_community | 9 |
| `POST → _patch_litellm_for_minimax` | cross_community | 9 |
| `POST → _patch_litellm_for_minimax` | cross_community | 9 |
| `_ → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Hermes_cli | 156 calls |
| Platforms | 121 calls |
| Handlers | 80 calls |
| Gateway | 55 calls |
| Spotify | 48 calls |
| Agent | 44 calls |
| Scripts | 25 calls |
| Run_agent | 18 calls |

## How to Explore

1. `gitnexus_context({name: "confirm_action"})` — see callers and callees
2. `gitnexus_query({query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
