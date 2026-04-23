---
name: scripts
description: "Skill for the Scripts area of swarm-bot. 262 symbols across 42 files."
---

# Scripts

262 symbols | 42 files | Cohesion: 79%

## When to Use

- Working with code in `ext/`
- Understanding how route, get_agent, semantic_search work
- Modifying scripts-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/everything-claude-code/skills/continuous-learning-v2/scripts/test_parse_instinct.py` | test_load_from_empty_dir, test_load_from_nonexistent_dir, test_load_annotates_metadata, test_load_defaults_scope_from_label, test_load_preserves_explicit_scope (+36) |
| `ext/everything-claude-code/skills/continuous-learning-v2/scripts/instinct-cli.py` | _load_instincts_from_dir, _validate_instinct_id, _promote_auto, parse_instinct_file, detect_project (+23) |
| `tools/mirofish/backend/scripts/run_parallel_simulation.py` | get_agent_names_from_config, fetch_new_actions_from_db, create_model, get_active_agents_for_round, run_twitter_simulation (+17) |
| `ext/skills/design-system/scripts/slide_search_core.py` | tokenize, fit, score, _load_csv, _search_csv (+11) |
| `tools/mirofish/backend/scripts/run_twitter_simulation.py` | update_status, _get_profile_path, _get_db_path, _create_model, _get_active_agents_for_round (+8) |
| `tools/mirofish/backend/scripts/run_reddit_simulation.py` | update_status, _get_profile_path, _get_db_path, _create_model, _get_active_agents_for_round (+8) |
| `ext/skills/gstack/scripts/gen-skill-docs.ts` | extractNameAndDescription, extractVoiceTriggers, processVoiceTriggers, transformFrontmatter, processTemplate (+6) |
| `scripts/audit_cross_system_parity.py` | _sha256, _check_legiona_parity, _fix_legiona_parity, _check_copilot_contract, _fix_copilot_contract (+6) |
| `ext/skills/design-system/scripts/html-token-validator.py` | add_error, load_css_variables, validate_file, validate_directory, print_summary (+6) |
| `ext/skills/ui-styling/scripts/tailwind_config_gen.py` | generate_config_string, _generate_typescript, _generate_javascript, _format_plugins, _indent_json (+5) |

## Entry Points

Start here when exploring this area:

- **`route`** (Function) — `core/orchestrator.py:712`
- **`get_agent`** (Function) — `core/agent_registry.py:185`
- **`semantic_search`** (Function) — `core/agent_registry.py:253`
- **`select_team`** (Function) — `core/agent_registry.py:838`
- **`get_agent_names_from_config`** (Function) — `tools/mirofish/backend/scripts/run_parallel_simulation.py:632`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `route` | Function | `core/orchestrator.py` | 712 |
| `get_agent` | Function | `core/agent_registry.py` | 185 |
| `semantic_search` | Function | `core/agent_registry.py` | 253 |
| `select_team` | Function | `core/agent_registry.py` | 838 |
| `get_agent_names_from_config` | Function | `tools/mirofish/backend/scripts/run_parallel_simulation.py` | 632 |
| `fetch_new_actions_from_db` | Function | `tools/mirofish/backend/scripts/run_parallel_simulation.py` | 656 |
| `create_model` | Function | `tools/mirofish/backend/scripts/run_parallel_simulation.py` | 983 |
| `get_active_agents_for_round` | Function | `tools/mirofish/backend/scripts/run_parallel_simulation.py` | 1039 |
| `run_twitter_simulation` | Function | `tools/mirofish/backend/scripts/run_parallel_simulation.py` | 1100 |
| `run_reddit_simulation` | Function | `tools/mirofish/backend/scripts/run_parallel_simulation.py` | 1292 |
| `log_round_start` | Function | `tools/mirofish/backend/scripts/action_logger.py` | 67 |
| `log_round_end` | Function | `tools/mirofish/backend/scripts/action_logger.py` | 79 |
| `log_simulation_start` | Function | `tools/mirofish/backend/scripts/action_logger.py` | 91 |
| `log_simulation_end` | Function | `tools/mirofish/backend/scripts/action_logger.py` | 104 |
| `test_imports` | Function | `tests/test_main.py` | 12 |
| `test_handlers_registered` | Function | `tests/test_main.py` | 35 |
| `test_core_modules_exist` | Function | `tests/test_main.py` | 56 |
| `test_tools_available` | Function | `tests/test_main.py` | 67 |
| `fail` | Function | `scripts/verify_wiring.py` | 33 |
| `check_handler_wiring` | Function | `scripts/verify_wiring.py` | 42 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → UpdateSendButton` | cross_community | 8 |
| `Main → UpdateSendButton` | cross_community | 6 |
| `Main → Parse_instinct_file` | cross_community | 6 |
| `Main → _collect_pending_dirs` | cross_community | 4 |
| `Main → _parse_created_date` | cross_community | 4 |
| `GeneratePreamble → GetHostConfig` | cross_community | 3 |
| `Run → Search_by_capability` | cross_community | 3 |
| `Run → Semantic_search` | cross_community | 3 |
| `Run → Get_agent` | cross_community | 3 |
| `Main → Disable_oasis_logging` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 8 calls |
| Services | 7 calls |
| Handlers | 3 calls |
| Cluster_279 | 1 calls |
| Cluster_25 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "route"})` — see callers and callees
2. `gitnexus_query({query: "scripts"})` — find related execution flows
3. Read key files listed above for implementation details
