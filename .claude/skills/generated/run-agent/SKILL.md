---
name: run-agent
description: "Skill for the Run_agent area of swarm-bot. 200 symbols across 40 files."
---

# Run_agent

"200 symbols | 40 files | Cohesion: 68%"

## When to Use

- Working with code in `ext/`
- Understanding how coerce_tool_args, test_coerces_integer_arg, test_coerces_boolean_arg work
- Modifying run_agent-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/tests/run_agent/test_run_agent_codex_responses.py` | _patch_agent_bootstrap, _build_agent, _codex_request_kwargs, test_run_codex_stream_retries_when_completed_event_missing, test_run_codex_stream_falls_back_to_create_after_stream_completion_error (+33) |
| `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | _mock_schema, test_coerces_integer_arg, test_coerces_boolean_arg, test_coerces_number_arg, test_leaves_string_args_alone (+10) |
| `ext/hermes-agent/tests/run_agent/test_fallback_model.py` | _make_agent, _mock_resolve, test_activates_openrouter_fallback, test_activates_zai_fallback, test_fallback_uses_resolved_normalized_model (+10) |
| `ext/hermes-agent/tests/run_agent/test_tool_call_guardrail_runtime.py` | _mock_tool_call, _mock_response, _make_agent, _hard_stop_config, test_config_enabled_hard_stop_blocks_repeated_exact_failure_before_execution (+4) |
| `ext/hermes-agent/tests/run_agent/test_provider_parity.py` | _make_codex_agent, test_text_response, test_reasoning_summary_extracted, test_encrypted_content_captured, test_no_encrypted_content_when_missing (+4) |
| `ext/hermes-agent/tests/run_agent/test_compression_boundary.py` | _assistant_with_tools, test_boundary_at_clean_position, test_boundary_after_assistant_with_tools, test_boundary_with_consecutive_tool_groups, _tool_result (+4) |
| `ext/hermes-agent/tests/run_agent/test_anthropic_error_handling.py` | _make_agent_cls, _run_with_agent, test_429_rate_limit_is_retried_and_recovers, test_529_overloaded_is_retried_and_recovers, test_500_server_error_is_retried_and_recovers (+4) |
| `ext/hermes-agent/tests/run_agent/test_interrupt_propagation.py` | test_concurrent_interrupt_propagation, thread_a, thread_b, _make_bare_agent, test_parent_interrupt_sets_child_flag (+3) |
| `ext/hermes-agent/tests/run_agent/test_image_shrink_recovery.py` | _big_png_data_url, test_small_image_part_not_shrunk, test_oversized_input_image_string_shape_rewritten, test_shrink_that_makes_it_bigger_rejected, _make_agent (+3) |
| `ext/hermes-agent/agent/codex_responses_adapter.py` | _normalize_codex_response, _deterministic_call_id, _split_responses_tool_id, _chat_messages_to_responses_input, _preflight_codex_input_items (+1) |

## Entry Points

Start here when exploring this area:

- **`coerce_tool_args`** (Function) — `ext/hermes-agent/model_tools.py:502`
- **`test_coerces_integer_arg`** (Function) — `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py:179`
- **`test_coerces_boolean_arg`** (Function) — `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py:187`
- **`test_coerces_number_arg`** (Function) — `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py:194`
- **`test_leaves_string_args_alone`** (Function) — `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py:201`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `coerce_tool_args` | Function | `ext/hermes-agent/model_tools.py` | 502 |
| `test_coerces_integer_arg` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 179 |
| `test_coerces_boolean_arg` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 187 |
| `test_coerces_number_arg` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 194 |
| `test_leaves_string_args_alone` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 201 |
| `test_leaves_already_correct_types` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 208 |
| `test_preserves_non_string_values` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 227 |
| `test_coerces_stringified_array_arg` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 239 |
| `test_coerces_stringified_object_arg` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 249 |
| `test_coerces_string_null_for_nullable_object_arg` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 257 |
| `test_coerces_string_null_for_nullable_array_arg` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 272 |
| `test_invalid_json_array_preserved_as_string` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 286 |
| `test_extra_args_without_schema_left_alone` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 294 |
| `test_mixed_coercion` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 303 |
| `test_failed_coercion_preserves_original` | Function | `ext/hermes-agent/tests/run_agent/test_tool_arg_coercion.py` | 324 |
| `test_activates_openrouter_fallback` | Function | `ext/hermes-agent/tests/run_agent/test_fallback_model.py` | 88 |
| `test_activates_zai_fallback` | Function | `ext/hermes-agent/tests/run_agent/test_fallback_model.py` | 108 |
| `test_fallback_uses_resolved_normalized_model` | Function | `ext/hermes-agent/tests/run_agent/test_fallback_model.py` | 126 |
| `test_activates_kimi_fallback` | Function | `ext/hermes-agent/tests/run_agent/test_fallback_model.py` | 145 |
| `test_activates_minimax_fallback` | Function | `ext/hermes-agent/tests/run_agent/test_fallback_model.py` | 161 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Cli | 15 calls |
| Tools | 7 calls |
| Hermes_cli | 7 calls |
| Tests | 4 calls |
| Scripts | 3 calls |
| Agent | 3 calls |
| Honcho_plugin | 3 calls |
| Hermes-agent | 2 calls |

## How to Explore

1. `gitnexus_context({name: "coerce_tool_args"})` — see callers and callees
2. `gitnexus_query({query: "run_agent"})` — find related execution flows
3. Read key files listed above for implementation details
