---
name: tests
description: "Skill for the Tests area of swarm-bot. 441 symbols across 96 files."
---

# Tests

441 symbols | 96 files | Cohesion: 85%

## When to Use

- Working with code in `tests/`
- Understanding how test_classify_computer_control, test_classify_code_generation, test_classify_code_review work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_intent_router.py` | test_classify_computer_control, test_classify_code_generation, test_classify_code_review, test_classify_web_research, test_classify_web_scrape (+24) |
| `tests/test_enterprise_layer.py` | test_record_basic, test_multiple_records, test_cost_alert, test_hourly_rate, test_format_dashboard (+20) |
| `tests/test_core_utils.py` | _strip, test_no_think_tags, test_single_think_block_removed, test_multiple_think_blocks_all_removed, test_nested_content_preserved (+15) |
| `ext/skills/ui-styling/scripts/tests/test_tailwind_config_gen.py` | test_add_fonts, test_add_spacing, test_add_breakpoints, test_recommend_plugins, test_recommend_plugins_nextjs (+14) |
| `tests/test_observation_store.py` | test_removes_special_chars, test_returns_star_for_empty, test_quotes_each_word, test_type_filter, test_decision_signal (+11) |
| `tests/test_legion_quality.py` | test_valid_response_pass, test_short_content_borderline, test_slop_content_rejection, test_guard_4_only_fires_borderline, test_filler_phrase_rejection (+10) |
| `tests/test_cost_router.py` | test_get_routing_stats_empty, test_get_routing_stats_after_routing, test_format_stats_html, test_select_model_returns_tuple, test_select_model_vision_agent (+8) |
| `tests/test_agent_registry.py` | test_detect_agent_math_keywords, test_detect_agent_debug_keywords, test_detect_agent_architect_keywords, test_detect_agent_coding_keywords, test_detect_agent_general_fallback (+7) |
| `tests/test_integration.py` | make_update, test_basic_nl_flow, test_soul_always_first, test_run_command, test_memory_recall_route (+5) |
| `tests/test_smoke.py` | test_rate_limiter_per_user_isolation, test_multi_limiter_types, test_admin_bypass_in_rate_limiter, test_multi_limiter_respects_separate_limits, test_soul_engine_build_soul_context (+4) |

## Entry Points

Start here when exploring this area:

- **`test_classify_computer_control`** (Function) — `tests/test_intent_router.py:9`
- **`test_classify_code_generation`** (Function) — `tests/test_intent_router.py:14`
- **`test_classify_code_review`** (Function) — `tests/test_intent_router.py:19`
- **`test_classify_web_research`** (Function) — `tests/test_intent_router.py:24`
- **`test_classify_web_scrape`** (Function) — `tests/test_intent_router.py:29`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `CookieImportError` | Class | `ext/skills/gstack/browse/src/cookie-import-browser.ts` | 82 |
| `test_classify_computer_control` | Function | `tests/test_intent_router.py` | 9 |
| `test_classify_code_generation` | Function | `tests/test_intent_router.py` | 14 |
| `test_classify_code_review` | Function | `tests/test_intent_router.py` | 19 |
| `test_classify_web_research` | Function | `tests/test_intent_router.py` | 24 |
| `test_classify_web_scrape` | Function | `tests/test_intent_router.py` | 29 |
| `test_classify_memory_search` | Function | `tests/test_intent_router.py` | 34 |
| `test_classify_schedule_task` | Function | `tests/test_intent_router.py` | 39 |
| `test_classify_translation` | Function | `tests/test_intent_router.py` | 44 |
| `test_classify_math_reasoning` | Function | `tests/test_intent_router.py` | 49 |
| `test_classify_creative_write` | Function | `tests/test_intent_router.py` | 54 |
| `test_classify_deep_reasoning` | Function | `tests/test_intent_router.py` | 59 |
| `test_classify_casual_chat` | Function | `tests/test_intent_router.py` | 66 |
| `test_classify_site_analysis` | Function | `tests/test_intent_router.py` | 71 |
| `test_classify_email_read` | Function | `tests/test_intent_router.py` | 76 |
| `test_classify_file_operation` | Function | `tests/test_intent_router.py` | 81 |
| `test_classify_memory_store` | Function | `tests/test_intent_router.py` | 86 |
| `test_classify_email_write` | Function | `tests/test_intent_router.py` | 91 |
| `test_classify_database_audit` | Function | `tests/test_intent_router.py` | 96 |
| `test_classify_weather_query` | Function | `tests/test_intent_router.py` | 101 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Gather_parallel_prompt_layers → _resolve` | cross_community | 5 |
| `Handle_nl → Build_sensei_system_prompt` | cross_community | 4 |
| `Get_layer_content → _path_for` | cross_community | 4 |
| `Get_layer_content → _default_state` | cross_community | 4 |
| `Run → Search_by_capability` | cross_community | 3 |
| `Gather_parallel_prompt_layers → Get_wiki_manager` | cross_community | 3 |
| `Route → Keyword_task_type` | cross_community | 3 |
| `Route → _llm_classify_task` | cross_community | 3 |
| `Get_layer_content → Build_soul_context` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Handlers | 10 calls |
| Tools | 6 calls |
| Scripts | 6 calls |
| Cluster_331 | 2 calls |
| Cluster_279 | 1 calls |
| Bridges | 1 calls |
| Llm_client | 1 calls |
| Services | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_classify_computer_control"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
