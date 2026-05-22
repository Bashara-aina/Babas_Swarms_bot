---
name: hermes-agent
description: "Skill for the Hermes-agent area of swarm-bot. 134 symbols across 29 files."
---

# Hermes-agent

"134 symbols | 29 files | Cohesion: 61%"

## When to Use

- Working with code in `ext/`
- Understanding how update_system_prompt, prune_empty_ghost_sessions, session_count work
- Modifying hermes-agent-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/mcp_serve.py` | start, stop, create_mcp_server, run_mcp_server, _run (+13) |
| `ext/hermes-agent/hermes_state.py` | _execute_write, update_system_prompt, prune_empty_ghost_sessions, session_count, export_all (+12) |
| `ext/hermes-agent/trajectory_compressor.py` | count_tokens, count_trajectory_tokens, count_turn_tokens, _extract_turn_content_for_summary, compress_trajectory (+10) |
| `ext/hermes-agent/batch_runner.py` | __init__, main, _normalize_tool_stats, _normalize_tool_error_counts, _process_single_prompt (+5) |
| `ext/hermes-agent/tests/test_hermes_state.py` | test_session_count_by_source, test_export_all_with_source, test_delete_message_row_does_not_crash, test_update_message_reindexes_tool_fields, test_schema_sql_is_source_of_truth (+4) |
| `ext/hermes-agent/utils.py` | _preserve_file_mode, _restore_file_mode, atomic_json_write, atomic_yaml_write, normalize_proxy_url (+3) |
| `ext/hermes-agent/toolsets.py` | get_toolset, resolve_toolset, _get_plugin_toolset_names, _get_registry_toolset_aliases, get_all_toolsets (+2) |
| `ext/hermes-agent/mini_swe_runner.py` | _create_env, _execute_command, run_task, run_batch, main (+1) |
| `ext/hermes-agent/model_tools.py` | get_tool_definitions, _compute_tool_definitions, _coerce_value, _schema_allows_null, _coerce_number (+1) |
| `ext/hermes-agent/toolset_distributions.py` | list_distributions, validate_distribution, print_distribution_info, get_distribution, sample_toolsets_from_distribution |

## Entry Points

Start here when exploring this area:

- **`update_system_prompt`** (Function) — `ext/hermes-agent/hermes_state.py:576`
- **`prune_empty_ghost_sessions`** (Function) — `ext/hermes-agent/hermes_state.py:690`
- **`session_count`** (Function) — `ext/hermes-agent/hermes_state.py:1954`
- **`export_all`** (Function) — `ext/hermes-agent/hermes_state.py:1988`
- **`delete_session`** (Function) — `ext/hermes-agent/hermes_state.py:2039`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `update_system_prompt` | Function | `ext/hermes-agent/hermes_state.py` | 576 |
| `prune_empty_ghost_sessions` | Function | `ext/hermes-agent/hermes_state.py` | 690 |
| `session_count` | Function | `ext/hermes-agent/hermes_state.py` | 1954 |
| `export_all` | Function | `ext/hermes-agent/hermes_state.py` | 1988 |
| `delete_session` | Function | `ext/hermes-agent/hermes_state.py` | 2039 |
| `prune_sessions` | Function | `ext/hermes-agent/hermes_state.py` | 2073 |
| `cmd_sessions` | Function | `ext/hermes-agent/hermes_cli/main.py` | 9672 |
| `test_session_count_by_source` | Function | `ext/hermes-agent/tests/test_hermes_state.py` | 1001 |
| `test_export_all_with_source` | Function | `ext/hermes-agent/tests/test_hermes_state.py` | 1080 |
| `test_delete_message_row_does_not_crash` | Function | `ext/hermes-agent/tests/test_hermes_state.py` | 2531 |
| `test_update_message_reindexes_tool_fields` | Function | `ext/hermes-agent/tests/test_hermes_state.py` | 2558 |
| `get_toolset` | Function | `ext/hermes-agent/toolsets.py` | 505 |
| `resolve_toolset` | Function | `ext/hermes-agent/toolsets.py` | 551 |
| `get_all_toolsets` | Function | `ext/hermes-agent/toolsets.py` | 670 |
| `get_toolset_names` | Function | `ext/hermes-agent/toolsets.py` | 695 |
| `get_toolset_info` | Function | `ext/hermes-agent/toolsets.py` | 762 |
| `get_registered_toolset_names` | Function | `ext/hermes-agent/tools/registry.py` | 188 |
| `test_unknown_returns_none` | Function | `ext/hermes-agent/tests/test_toolsets.py` | 34 |
| `start` | Function | `ext/hermes-agent/mcp_serve.py` | 207 |
| `stop` | Function | `ext/hermes-agent/mcp_serve.py` | 216 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Handle_msg_from_peer → Get_hermes_home` | cross_community | 9 |
| `POST → _patch_litellm_for_minimax` | cross_community | 9 |
| `POST → _patch_litellm_for_minimax` | cross_community | 9 |
| `_ → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 29 calls |
| Tools | 26 calls |
| Hermes_cli | 16 calls |
| Platforms | 7 calls |
| Gateway | 5 calls |
| Agent | 2 calls |
| Cli | 2 calls |
| Stress | 1 calls |

## How to Explore

1. `gitnexus_context({name: "update_system_prompt"})` — see callers and callees
2. `gitnexus_query({query: "hermes-agent"})` — find related execution flows
3. Read key files listed above for implementation details
