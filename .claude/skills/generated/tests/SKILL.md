---
name: tests
description: "Skill for the Tests area of swarm-bot. 399 symbols across 78 files."
---

# Tests

"399 symbols | 78 files | Cohesion: 68%"

## When to Use

- Working with code in `ext/`
- Understanding how handle_request, dispatch, test_session_close_commits_memory_and_fires_finalize_hook work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/tests/test_hermes_state.py` | test_create_and_get_session, test_end_session, test_end_session_preserves_original_end_reason, test_end_session_after_reopen_allows_re_end, test_update_system_prompt (+71) |
| `ext/hermes-agent/tests/test_tui_gateway_server.py` | _session, test_session_close_commits_memory_and_fires_finalize_hook, test_session_title_queues_when_db_row_not_ready, test_session_title_clears_pending_after_persist, test_session_title_does_not_queue_noop_when_row_exists (+52) |
| `ext/hermes-agent/tests/test_yuanbao_pipeline.py` | make_adapter, make_ctx, test_new_message_passes, test_duplicate_stops_pipeline, test_self_message_stops (+16) |
| `ext/hermes-agent/tests/test_model_tools_async_bridge.py` | _get_current_loop, test_loop_not_closed_after_run_async, test_same_loop_reused_across_calls, test_cached_transport_survives_between_calls, _run_on_worker (+10) |
| `ext/hermes-agent/hermes_state.py` | create_session, end_session, reopen_session, get_session, message_count (+9) |
| `tests/test_self_evolution.py` | _engine, test_infer_agent_from_task_computer, test_infer_agent_from_task_coding, test_infer_agent_from_task_researcher, test_infer_agent_from_task_debug (+8) |
| `tests/test_feedback_learner.py` | _learner, test_register_and_record_positive, test_register_and_record_negative, test_score_accumulation, test_agent_weights_neutral_with_little_data (+4) |
| `ext/hermes-agent/tests/test_mcp_serve.py` | _create_test_db, test_poll_detects_new_messages, test_poll_skips_when_unchanged, test_poll_detects_new_message_after_db_write, test_poll_session_filter (+4) |
| `core/self_evolution.py` | _infer_agent_from_task, _write_hermes_skill, record_failure, record_decision, _read_failures (+3) |
| `tests/test_usage_tracker.py` | _tracker, test_record_free_model, test_record_paid_model, test_daily_limit_alert, test_unknown_model_no_crash (+2) |

## Entry Points

Start here when exploring this area:

- **`handle_request`** (Function) — `ext/hermes-agent/tui_gateway/server.py:456`
- **`dispatch`** (Function) — `ext/hermes-agent/tui_gateway/server.py:468`
- **`test_session_close_commits_memory_and_fires_finalize_hook`** (Function) — `ext/hermes-agent/tests/test_tui_gateway_server.py:442`
- **`test_session_title_queues_when_db_row_not_ready`** (Function) — `ext/hermes-agent/tests/test_tui_gateway_server.py:505`
- **`test_session_title_clears_pending_after_persist`** (Function) — `ext/hermes-agent/tests/test_tui_gateway_server.py:539`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `handle_request` | Function | `ext/hermes-agent/tui_gateway/server.py` | 456 |
| `dispatch` | Function | `ext/hermes-agent/tui_gateway/server.py` | 468 |
| `test_session_close_commits_memory_and_fires_finalize_hook` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 442 |
| `test_session_title_queues_when_db_row_not_ready` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 505 |
| `test_session_title_clears_pending_after_persist` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 539 |
| `test_session_title_does_not_queue_noop_when_row_exists` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 573 |
| `test_session_title_get_falls_back_to_pending_when_db_read_throws` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 606 |
| `test_session_title_get_retries_persist_for_pending_title` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 622 |
| `test_session_title_get_retries_pending_even_when_db_has_title` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 650 |
| `test_session_title_rejects_empty_title_with_specific_error_code` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 678 |
| `test_session_title_set_maps_valueerror_to_user_error` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 699 |
| `test_session_title_set_errors_when_row_lookup_fails_after_noop` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 727 |
| `test_config_set_yolo_toggles_session_scope` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 808 |
| `test_config_set_fast_updates_live_agent_and_config` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 837 |
| `test_config_set_fast_status_is_non_mutating` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 889 |
| `test_config_set_fast_rejects_unsupported_model` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 915 |
| `test_config_set_fast_rejects_missing_model` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 949 |
| `test_config_set_reasoning_updates_live_session_and_agent` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 1255 |
| `test_config_set_verbose_updates_session_mode_and_agent` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 1293 |
| `test_config_set_model_uses_live_switch_path` | Function | `ext/hermes-agent/tests/test_tui_gateway_server.py` | 1311 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Cmd_sessions → Items` | cross_community | 6 |
| `Run → _err` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Gateway | 29 calls |
| Tools | 22 calls |
| Cli | 20 calls |
| Hermes-agent | 15 calls |
| Handlers | 12 calls |
| Hermes_cli | 7 calls |
| Optimization | 6 calls |
| Skills | 3 calls |

## How to Explore

1. `gitnexus_context({name: "handle_request"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
