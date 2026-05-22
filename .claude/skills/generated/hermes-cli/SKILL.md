---
name: hermes-cli
description: "Skill for the Hermes_cli area of swarm-bot. 1802 symbols across 214 files."
---

# Hermes_cli

"1802 symbols | 214 files | Cohesion: 61%"

## When to Use

- Working with code in `ext/`
- Understanding how get_available_vision_backends, resolve_managed_tool_gateway, managed_nous_tools_enabled work
- Modifying hermes_cli-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/hermes_cli/gateway.py` | get_installed_systemd_scopes, has_conflicting_systemd_units, print_legacy_unit_warning, remove_legacy_hermes_units, print_systemd_scope_conflict_warning (+90) |
| `ext/hermes-agent/hermes_cli/main.py` | cmd_whatsapp, _clear_stale_openai_base_url, select_provider_and_model, _format_aux_current, _save_aux_choice (+83) |
| `ext/hermes-agent/hermes_cli/auth.py` | get_anthropic_key, get_provider_auth_state, get_qwen_auth_status, get_nous_auth_status, get_minimax_oauth_auth_status (+80) |
| `ext/hermes-agent/hermes_cli/web_server.py` | get_status, _resolve_provider_status, get_toolsets, set_model_assignment, set_dashboard_theme (+46) |
| `ext/hermes-agent/hermes_cli/models.py` | is_nous_free_tier, check_nous_free_tier, _resolve_nous_portal_url, get_nous_recommended_aux_model, normalize_copilot_model_id (+41) |
| `ext/hermes-agent/hermes_cli/config.py` | is_managed, managed_error, get_config_path, get_env_path, _secure_file (+39) |
| `ext/hermes-agent/hermes_cli/plugins_cmd.py` | _prompt_plugin_env_vars, _save_memory_provider, _save_context_engine, _toggle_plugin_toolset, _resolve_git_url (+38) |
| `ext/hermes-agent/hermes_cli/setup.py` | _get_credential_pool_strategies, _set_credential_pool_strategy, print_header, print_noninteractive_setup_guidance, prompt (+35) |
| `ext/hermes-agent/hermes_cli/kanban_db.py` | write_txn, release_stale_claims, set_workspace_path, detect_crashed_workers, _set_worker_pid (+33) |
| `ext/hermes-agent/hermes_cli/tools_config.py` | _toolset_allowed_for_platform, _get_effective_configurable_toolsets, _get_plugin_toolset_keys, _run_post_setup, _get_enabled_platforms (+29) |

## Entry Points

Start here when exploring this area:

- **`get_available_vision_backends`** (Function) — `ext/hermes-agent/agent/auxiliary_client.py:2540`
- **`resolve_managed_tool_gateway`** (Function) — `ext/hermes-agent/tools/managed_tool_gateway.py:131`
- **`managed_nous_tools_enabled`** (Function) — `ext/hermes-agent/tools/tool_backend_helpers.py:16`
- **`normalize_browser_cloud_provider`** (Function) — `ext/hermes-agent/tools/tool_backend_helpers.py:39`
- **`resolve_openai_audio_api_key`** (Function) — `ext/hermes-agent/tools/tool_backend_helpers.py:102`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Event` | Class | `ext/hermes-agent/hermes_cli/kanban_db.py` | 230 |
| `get_available_vision_backends` | Function | `ext/hermes-agent/agent/auxiliary_client.py` | 2540 |
| `resolve_managed_tool_gateway` | Function | `ext/hermes-agent/tools/managed_tool_gateway.py` | 131 |
| `managed_nous_tools_enabled` | Function | `ext/hermes-agent/tools/tool_backend_helpers.py` | 16 |
| `normalize_browser_cloud_provider` | Function | `ext/hermes-agent/tools/tool_backend_helpers.py` | 39 |
| `resolve_openai_audio_api_key` | Function | `ext/hermes-agent/tools/tool_backend_helpers.py` | 102 |
| `fal_key_is_configured` | Function | `ext/hermes-agent/tools/tool_backend_helpers.py` | 125 |
| `claw_command` | Function | `ext/hermes-agent/hermes_cli/claw.py` | 286 |
| `print_header` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 151 |
| `print_noninteractive_setup_guidance` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 176 |
| `prompt` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 195 |
| `prompt_choice` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 223 |
| `prompt_yes_no` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 266 |
| `prompt_checklist` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 290 |
| `setup_model_provider` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 765 |
| `setup_terminal_backend` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 1278 |
| `setup_agent_settings` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 1678 |
| `setup_gateway` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 2343 |
| `run_setup_wizard` | Function | `ext/hermes-agent/hermes_cli/setup.py` | 2968 |
| `get_anthropic_key` | Function | `ext/hermes-agent/hermes_cli/auth.py` | 423 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_msg_from_peer → Get_hermes_home` | cross_community | 9 |
| `On_startup → Get_hermes_home` | cross_community | 9 |
| `On_startup → Write_txn` | cross_community | 9 |
| `Setup_model_provider → Get_hermes_home` | cross_community | 9 |
| `On_startup → Add` | cross_community | 8 |
| `Web_crawl_tool → Get_hermes_home` | cross_community | 8 |
| `Run → Get_hermes_home` | cross_community | 7 |
| `POST → Get_hermes_home` | cross_community | 7 |
| `POST → Get_hermes_home` | cross_community | 7 |
| `_ → Get_hermes_home` | cross_community | 7 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 203 calls |
| Agent | 108 calls |
| Platforms | 24 calls |
| Scripts | 20 calls |
| Gateway | 19 calls |
| Tests | 17 calls |
| Hermes-agent | 15 calls |
| Session | 6 calls |

## How to Explore

1. `gitnexus_context({name: "get_available_vision_backends"})` — see callers and callees
2. `gitnexus_query({query: "hermes_cli"})` — find related execution flows
3. Read key files listed above for implementation details
