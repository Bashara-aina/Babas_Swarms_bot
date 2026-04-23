---
name: services
description: "Skill for the Services area of swarm-bot. 285 symbols across 41 files."
---

# Services

285 symbols | 41 files | Cohesion: 69%

## When to Use

- Working with code in `tools/`
- Understanding how get_locale, t, search_graph work
- Modifying services-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tools/mirofish/backend/app/services/report_agent.py` | __init__, log_planning_context, log_react_thought, log_error, _setup_file_handler (+30) |
| `tools/mirofish/backend/app/services/oasis_profile_generator.py` | __init__, save_profiles, _save_twitter_csv, _normalize_gender, _save_reddit_json (+19) |
| `tools/mirofish/backend/app/services/zep_tools.py` | __init__, search_graph, _local_search, match_score, get_all_nodes (+18) |
| `tools/mirofish/backend/app/api/simulation.py` | get_entities_by_type, create_simulation, _check_simulation_prepared, prepare_simulation, get_prepare_status (+17) |
| `tools/mirofish/backend/app/services/simulation_runner.py` | start_simulation, get_running_simulations, _load_run_state, get_env_status_detail, interview_all_agents (+12) |
| `tools/mirofish/backend/app/services/simulation_config_generator.py` | generate_config, report_progress, _build_context, _summarize_entities, _parse_time_config (+12) |
| `tools/mirofish/backend/app/api/report.py` | generate_report, get_generate_status, get_report, get_report_by_simulation, download_report (+9) |
| `ext/skills/gstack/browse/src/sidebar-agent.ts` | cancelFileForTab, isValidQueueEntry, getGitRoot, writeToInbox, refreshToken (+9) |
| `tools/mirofish/backend/app/services/zep_graph_memory_updater.py` | to_episode_text, _get_platform_display_name, _worker_loop, _send_batch_activities, _flush_remaining (+9) |
| `tools/mirofish/backend/app/services/simulation_manager.py` | to_dict, _save_simulation_state, create_simulation, get_simulation, to_simple_dict (+8) |

## Entry Points

Start here when exploring this area:

- **`get_locale`** (Function) — `tools/mirofish/backend/app/utils/locale.py:27`
- **`t`** (Function) — `tools/mirofish/backend/app/utils/locale.py:34`
- **`search_graph`** (Function) — `tools/mirofish/backend/app/services/zep_tools.py:463`
- **`match_score`** (Function) — `tools/mirofish/backend/app/services/zep_tools.py:576`
- **`get_all_nodes`** (Function) — `tools/mirofish/backend/app/services/zep_tools.py:649`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `get_locale` | Function | `tools/mirofish/backend/app/utils/locale.py` | 27 |
| `t` | Function | `tools/mirofish/backend/app/utils/locale.py` | 34 |
| `search_graph` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 463 |
| `match_score` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 576 |
| `get_all_nodes` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 649 |
| `get_all_edges` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 677 |
| `get_node_detail` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 715 |
| `get_node_edges` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 747 |
| `get_entities_by_type` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 779 |
| `get_entity_summary` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 807 |
| `get_graph_statistics` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 854 |
| `get_simulation_context` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 889 |
| `insight_forge` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 944 |
| `panorama_search` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 1144 |
| `quick_search` | Function | `tools/mirofish/backend/app/services/zep_tools.py` | 1236 |
| `start_simulation` | Function | `tools/mirofish/backend/app/services/simulation_runner.py` | 312 |
| `to_dict` | Function | `tools/mirofish/backend/app/services/simulation_manager.py` | 77 |
| `create_simulation` | Function | `tools/mirofish/backend/app/services/simulation_manager.py` | 193 |
| `get_simulation` | Function | `tools/mirofish/backend/app/services/simulation_manager.py` | 458 |
| `log_planning_context` | Function | `tools/mirofish/backend/app/services/report_agent.py` | 120 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → UpdateSendButton` | cross_community | 8 |
| `Generate_report → UpdateSendButton` | cross_community | 7 |
| `Chat_with_report_agent → UpdateSendButton` | cross_community | 7 |
| `Prepare_simulation → UpdateSendButton` | cross_community | 6 |
| `Start_simulation → UpdateSendButton` | cross_community | 6 |
| `Get_prepare_status → UpdateSendButton` | cross_community | 6 |
| `Get_simulation_history → UpdateSendButton` | cross_community | 6 |
| `Prepare_simulation → UpdateSendButton` | cross_community | 6 |
| `Interview_agents → UpdateSendButton` | cross_community | 6 |
| `Main → UpdateSendButton` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 8 calls |
| Test | 1 calls |
| Cluster_943 | 1 calls |
| Ui | 1 calls |

## How to Explore

1. `gitnexus_context({name: "get_locale"})` — see callers and callees
2. `gitnexus_query({query: "services"})` — find related execution flows
3. Read key files listed above for implementation details
