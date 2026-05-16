---
name: memory
description: "Skill for the Memory area of swarm-bot. 142 symbols across 35 files."
---

# Memory

"142 symbols | 35 files | Cohesion: 65%"

## When to Use

- Working with code in `core/`
- Understanding how initialize, get_tool_schemas, test_identity_template_resolved_in_container_tag work
- Modifying memory-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `core/memory/observation_store.py` | _should_skip_path, get_stats, _ensure_connection, _init_db, search (+9) |
| `core/memory/temporal_graph.py` | _get_conn, _init_db, _seed_user, _add_fact_inner, add_fact (+5) |
| `ext/hermes-agent/tests/plugins/memory/test_hindsight_provider.py` | _make_mock_client, provider, _make, test_sync_turn_retains_metadata_rich_turn, test_sync_turn_parent_session_tag (+4) |
| `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | test_identity_template_resolved_in_container_tag, test_identity_template_default_profile, test_search_mode_config_passed_to_client, test_invalid_search_mode_falls_back_to_default, test_multi_container_enabled_adds_schema_param (+3) |
| `core/long_term_memory.py` | _get_embedder, _get_chroma_client, _get_or_create_collection, _semantic_search, _episodic_search (+2) |
| `core/memory/memory_manager.py` | validate_consistency, get_memory_stats, search, save, auto_extract_and_save (+2) |
| `core/memory/episodic_store.py` | store, recall, _supabase_recall, __init__, _init_supabase (+1) |
| `ext/hermes-agent/plugins/memory/__init__.py` | _get_user_plugins_dir, _is_memory_provider_dir, _iter_provider_dirs, find_provider_dir, _get_active_memory_provider (+1) |
| `core/memory/observation_capture.py` | _extract_files_from_tool, capture_tool_use, capture_command, capture_decision, register_observation_hooks |
| `core/memory/observation_queue.py` | enqueue, get_observation_queue, _drain_loop, _write_batch, _flush |

## Entry Points

Start here when exploring this area:

- **`initialize`** (Function) — `ext/hermes-agent/plugins/memory/supermemory/__init__.py:479`
- **`get_tool_schemas`** (Function) — `ext/hermes-agent/plugins/memory/supermemory/__init__.py:665`
- **`test_identity_template_resolved_in_container_tag`** (Function) — `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py:268`
- **`test_identity_template_default_profile`** (Function) — `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py:278`
- **`test_search_mode_config_passed_to_client`** (Function) — `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py:301`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `initialize` | Function | `ext/hermes-agent/plugins/memory/supermemory/__init__.py` | 479 |
| `get_tool_schemas` | Function | `ext/hermes-agent/plugins/memory/supermemory/__init__.py` | 665 |
| `test_identity_template_resolved_in_container_tag` | Function | `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | 268 |
| `test_identity_template_default_profile` | Function | `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | 278 |
| `test_search_mode_config_passed_to_client` | Function | `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | 301 |
| `test_invalid_search_mode_falls_back_to_default` | Function | `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | 312 |
| `test_multi_container_enabled_adds_schema_param` | Function | `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | 333 |
| `test_multi_container_tool_store_with_custom_tag` | Function | `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | 350 |
| `test_multi_container_rejects_unlisted_tag` | Function | `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | 369 |
| `test_multi_container_system_prompt_includes_instructions` | Function | `ext/hermes-agent/tests/plugins/memory/test_supermemory_provider.py` | 387 |
| `capture_tool_use` | Function | `core/memory/observation_capture.py` | 128 |
| `capture_command` | Function | `core/memory/observation_capture.py` | 182 |
| `capture_decision` | Function | `core/memory/observation_capture.py` | 202 |
| `enqueue` | Function | `core/memory/observation_queue.py` | 82 |
| `get_observation_queue` | Function | `core/memory/observation_queue.py` | 177 |
| `execute_nl_query` | Function | `skills/database_agent.py` | 120 |
| `check_booking_alerts` | Function | `tools/rumahlabuh_crew.py` | 165 |
| `execute` | Function | `core/integrations/prefect_integration.py` | 181 |
| `pipeline_flow` | Function | `core/integrations/prefect_integration.py` | 190 |
| `store` | Function | `core/memory/episodic_store.py` | 123 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `On_startup → Get_hermes_home` | cross_community | 9 |
| `On_startup → Write_txn` | cross_community | 9 |
| `On_startup → Add` | cross_community | 8 |
| `On_startup → _init_db` | cross_community | 7 |
| `On_startup → Total_count` | cross_community | 5 |
| `On_startup → Get_observation_store` | cross_community | 5 |
| `On_startup → All` | cross_community | 5 |
| `On_startup → Init_humanization_layer` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 13 calls |
| Platforms | 9 calls |
| Hermes_cli | 7 calls |
| Hindsight | 6 calls |
| Handlers | 4 calls |
| Scripts | 4 calls |
| Supermemory | 4 calls |
| Examples | 3 calls |

## How to Explore

1. `gitnexus_context({name: "initialize"})` — see callers and callees
2. `gitnexus_query({query: "memory"})` — find related execution flows
3. Read key files listed above for implementation details
