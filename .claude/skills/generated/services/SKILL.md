---
name: services
description: "Skill for the Services area of swarm-bot. 135 symbols across 23 files."
---

# Services

"135 symbols | 23 files | Cohesion: 57%"

## When to Use

- Working with code in `tools/`
- Understanding how progress_callback, get_report, download_report work
- Modifying services-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tools/mirofish/backend/app/services/zep_tools.py` | search_graph, _local_search, get_all_nodes, get_all_edges, get_node_edges (+15) |
| `tools/mirofish/backend/app/services/oasis_profile_generator.py` | generate_profile_from_entity, _generate_username, _search_zep_for_entity, _build_entity_context, _generate_profile_rule_based (+15) |
| `tools/mirofish/backend/app/services/report_agent.py` | __init__, log_start, log_planning_start, log_planning_complete, log_section_full_complete (+14) |
| `tools/mirofish/backend/app/services/simulation_config_generator.py` | _build_context, _summarize_entities, _generate_agent_configs_batch, _generate_agent_config_by_rule, generate_config (+7) |
| `tools/mirofish/backend/app/services/zep_graph_memory_updater.py` | add_activity_from_dict, _get_platform_display_name, _worker_loop, _send_batch_activities, _flush_remaining (+4) |
| `tools/mirofish/backend/app/api/simulation.py` | progress_callback, get_simulation_profiles_realtime, get_simulation_config_realtime, get_graph_entities, get_entity_detail (+2) |
| `tools/mirofish/backend/app/services/zep_entity_reader.py` | get_all_nodes, get_node_edges, filter_defined_entities, get_entity_with_context, get_entity_type (+1) |
| `tools/mirofish/backend/app/services/simulation_manager.py` | _get_simulation_dir, _load_simulation_state, prepare_simulation, get_profiles, get_run_instructions (+1) |
| `tools/mirofish/backend/app/services/graph_builder.py` | _wait_for_episodes, _build_graph_worker, create_graph, set_ontology, add_text_batches |
| `project/jwt_auth/services/auth.py` | get_user_by_email, get_user_by_username, authenticate_user, create_user, update_user |

## Entry Points

Start here when exploring this area:

- **`progress_callback`** (Function) — `tools/mirofish/backend/app/api/simulation.py:524`
- **`get_report`** (Function) — `tools/mirofish/backend/app/api/report.py:278`
- **`download_report`** (Function) — `tools/mirofish/backend/app/api/report.py:399`
- **`get_graph_statistics_tool`** (Function) — `tools/mirofish/backend/app/api/report.py:984`
- **`delete_project`** (Function) — `tools/mirofish/backend/app/api/graph.py:71`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `progress_callback` | Function | `tools/mirofish/backend/app/api/simulation.py` | 524 |
| `get_report` | Function | `tools/mirofish/backend/app/api/report.py` | 278 |
| `download_report` | Function | `tools/mirofish/backend/app/api/report.py` | 399 |
| `get_graph_statistics_tool` | Function | `tools/mirofish/backend/app/api/report.py` | 984 |
| `delete_project` | Function | `tools/mirofish/backend/app/api/graph.py` | 71 |
| `generate_ontology` | Function | `tools/mirofish/backend/app/api/graph.py` | 123 |
| `search_graph` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 463 |
| `get_all_nodes` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 649 |
| `get_all_edges` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 677 |
| `get_node_edges` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 747 |
| `get_entities_by_type` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 779 |
| `get_entity_summary` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 807 |
| `get_graph_statistics` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 854 |
| `get_simulation_context` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 889 |
| `panorama_search` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 1144 |
| `quick_search` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 1236 |
| `log_start` | Function | `tools/mirofish/backend/app/services/report_agent.py` | 100 |
| `log_planning_start` | Function | `tools/mirofish/backend/app/services/report_agent.py` | 113 |
| `log_planning_complete` | Function | `tools/mirofish/backend/app/services/report_agent.py` | 132 |
| `log_section_full_complete` | Function | `tools/mirofish/backend/app/services/report_agent.py` | 258 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Prepare_simulation → Get_locale` | cross_community | 4 |
| `Prepare_simulation → Items` | cross_community | 4 |
| `Prepare_simulation → _get_simulation_dir` | cross_community | 4 |
| `Run_prepare → Get_locale` | cross_community | 4 |
| `Run_prepare → Items` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 13 calls |
| Models | 6 calls |
| Api | 6 calls |
| Hermes_cli | 2 calls |
| Observability | 1 calls |
| Scripts | 1 calls |

## How to Explore

1. `gitnexus_context({name: "progress_callback"})` — see callers and callees
2. `gitnexus_query({query: "services"})` — find related execution flows
3. Read key files listed above for implementation details
