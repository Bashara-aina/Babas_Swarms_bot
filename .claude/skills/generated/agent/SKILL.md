---
name: agent
description: "Skill for the Agent area of swarm-bot. 828 symbols across 113 files."
---

# Agent

"828 symbols | 113 files | Cohesion: 64%"

## When to Use

- Working with code in `ext/`
- Understanding how has_credentials, select, load_pool work
- Modifying agent-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/agent/auxiliary_client.py` | _codex_cloudflare_headers, _to_openai_base_url, _select_pool_entry, _pool_runtime_api_key, _pool_runtime_base_url (+54) |
| `ext/hermes-agent/tests/agent/test_credential_pool.py` | _write_auth_store, test_fill_first_selection_skips_recently_exhausted_entry, test_select_clears_expired_exhaustion, test_round_robin_strategy_rotates_priorities, test_random_strategy_uses_random_choice (+36) |
| `ext/hermes-agent/tests/agent/test_memory_provider.py` | on_memory_write, test_get_provider_by_name, test_shutdown_all_reverse_order, test_tool_names_include_all_providers, test_on_memory_write_add (+32) |
| `ext/hermes-agent/agent/credential_pool.py` | has_credentials, select, load_pool, to_dict, current (+28) |
| `ext/hermes-agent/agent/model_metadata.py` | _infer_provider_from_url, _is_known_provider_base_url, _resolve_endpoint_context_length, _resolve_nous_context_length, get_model_context_length (+28) |
| `ext/hermes-agent/agent/anthropic_adapter.py` | _get_anthropic_sdk, _normalize_base_url_text, _is_third_party_anthropic_endpoint, _is_kimi_coding_endpoint, _requires_bearer_auth (+28) |
| `ext/hermes-agent/agent/curator.py` | apply_automatic_transitions, _render_candidate_list, run_curator_review, _llm_pass, _resolve_review_model (+22) |
| `ext/hermes-agent/agent/google_oauth.py` | _credentials_path, _lock_path, save_credentials, clear_credentials, get_valid_access_token (+17) |
| `ext/hermes-agent/agent/bedrock_adapter.py` | get_bedrock_context_length, _model_supports_tool_use, convert_tools_to_converse, _convert_content_to_converse, convert_messages_to_converse (+17) |
| `ext/hermes-agent/agent/display.py` | _diff_ansi, _diff_dim, _diff_file, _diff_hunk, _diff_minus (+15) |

## Entry Points

Start here when exploring this area:

- **`has_credentials`** (Function) — `ext/hermes-agent/agent/credential_pool.py:373`
- **`select`** (Function) — `ext/hermes-agent/agent/credential_pool.py:819`
- **`load_pool`** (Function) — `ext/hermes-agent/agent/credential_pool.py:1561`
- **`get_codex_auth_status`** (Function) — `ext/hermes-agent/hermes_cli/auth.py:3365`
- **`test_persist_nous_credentials_custom_label_survives_reseed`** (Function) — `ext/hermes-agent/tests/hermes_cli/test_auth_nous_provider.py:770`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `MemoryProvider` | Class | `ext/hermes-agent/agent/memory_provider.py` | 42 |
| `FakeMemoryProvider` | Class | `ext/hermes-agent/tests/agent/test_memory_provider.py` | 14 |
| `ContextEngine` | Class | `ext/hermes-agent/agent/context_engine.py` | 31 |
| `has_credentials` | Function | `ext/hermes-agent/agent/credential_pool.py` | 373 |
| `select` | Function | `ext/hermes-agent/agent/credential_pool.py` | 819 |
| `load_pool` | Function | `ext/hermes-agent/agent/credential_pool.py` | 1561 |
| `get_codex_auth_status` | Function | `ext/hermes-agent/hermes_cli/auth.py` | 3365 |
| `test_persist_nous_credentials_custom_label_survives_reseed` | Function | `ext/hermes-agent/tests/hermes_cli/test_auth_nous_provider.py` | 770 |
| `test_fill_first_selection_skips_recently_exhausted_entry` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 16 |
| `test_select_clears_expired_exhaustion` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 61 |
| `test_round_robin_strategy_rotates_priorities` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 94 |
| `test_random_strategy_uses_random_choice` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 138 |
| `test_exhausted_entry_resets_after_ttl` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 181 |
| `test_exhausted_402_entry_resets_after_one_hour` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 216 |
| `test_explicit_reset_timestamp_overrides_default_429_ttl` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 252 |
| `test_mark_exhausted_and_rotate_persists_status` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 290 |
| `test_load_pool_seeds_env_api_key` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 335 |
| `test_load_pool_prefers_dotenv_over_stale_os_environ` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 351 |
| `test_load_pool_falls_back_to_os_environ_when_dotenv_empty` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 384 |
| `test_load_pool_removes_stale_seeded_env_entry` | Function | `ext/hermes-agent/tests/agent/test_credential_pool.py` | 408 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Get_model_context_length → _patch_litellm_for_minimax` | cross_community | 7 |
| `Resolve_provider_client → Get_hermes_home` | cross_community | 6 |
| `Resolve_provider_client → Items` | cross_community | 6 |
| `Async_call_llm → Get_hermes_home` | cross_community | 6 |
| `Async_call_llm → Items` | cross_community | 6 |
| `Async_call_llm → Base_url_hostname` | cross_community | 6 |
| `Call_llm → Get_hermes_home` | cross_community | 6 |
| `Call_llm → Items` | cross_community | 6 |
| `Call_llm → Base_url_hostname` | cross_community | 6 |
| `Resolve_provider_client → _normalize_root_model_keys` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 98 calls |
| Hermes_cli | 91 calls |
| Platforms | 31 calls |
| Hermes-agent | 22 calls |
| Tests | 17 calls |
| Scripts | 15 calls |
| Cron | 10 calls |
| Acp | 9 calls |

## How to Explore

1. `gitnexus_context({name: "has_credentials"})` — see callers and callees
2. `gitnexus_query({query: "agent"})` — find related execution flows
3. Read key files listed above for implementation details
