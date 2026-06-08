---
name: gateway
description: "Skill for the Gateway area of swarm-bot."
---

# Gateway

"gateway area"

## When to Use

- Working with code in `ext/`
- Understanding how is_approved, list_approved, revoke work
- Modifying gateway-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/tests/gateway/test_stream_consumer.py` | test_stream_with_media_tag, test_segment_break_creates_new_message, test_segment_break_no_text_before, test_segment_break_removes_cursor, test_multiple_segment_breaks (+47) |
| `ext/hermes-agent/tests/gateway/test_signal.py` | _make_signal_adapter, _stub_rpc, test_fetch_attachment_uses_id_parameter, test_fetch_attachment_returns_none_on_empty, test_fetch_attachment_handles_dict_response (+41) |
| `ext/hermes-agent/tests/gateway/test_webhook_adapter.py` | _make_adapter, _create_app, test_event_filter_accepts_matching, test_event_filter_rejects_non_matching, test_event_filter_empty_allows_all (+28) |
| `ext/hermes-agent/gateway/status.py` | _get_pid_path, _get_gateway_lock_path, _looks_like_gateway_process, _read_pid_record, _read_gateway_lock_record (+27) |
| `ext/hermes-agent/tests/gateway/test_voice_command.py` | test_none_sentinel_flushes_buffer, test_stop_event_aborts_early, test_think_blocks_stripped, test_sentence_splitting, test_markdown_stripped_in_speech (+26) |
| `ext/hermes-agent/tests/gateway/test_signal_format.py` | _m2s, _find_style, test_snake_case_not_italic, test_multiple_snake_case, test_snake_case_path (+25) |
| `ext/hermes-agent/tests/gateway/test_telegram_network.py` | _doh_answer, _patch_doh, test_google_and_cloudflare_ips_collected, test_system_dns_ip_excluded, test_doh_results_deduplicated (+25) |
| `ext/hermes-agent/tests/gateway/test_unauthorized_dm_behavior.py` | _clear_auth_env, _make_event, _make_runner, test_whatsapp_lid_user_matches_phone_allowlist_via_session_mapping, test_star_wildcard_in_allowlist_authorizes_any_user (+24) |
| `ext/hermes-agent/tests/gateway/test_sms.py` | _make_adapter, test_strips_bold, test_strips_italic, test_strips_code_blocks, test_strips_inline_code (+23) |
| `ext/hermes-agent/gateway/session.py` | _generate_session_key, reset_session, _now, _is_session_expired, _should_reset (+22) |

## Entry Points

Start here when exploring this area:

- **`is_approved`** (Function) — `ext/hermes-agent/gateway/pairing.py:113`
- **`list_approved`** (Function) — `ext/hermes-agent/gateway/pairing.py:118`
- **`revoke`** (Function) — `ext/hermes-agent/gateway/pairing.py:137`
- **`generate_code`** (Function) — `ext/hermes-agent/gateway/pairing.py:150`
- **`approve_code`** (Function) — `ext/hermes-agent/gateway/pairing.py:193`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Database` | Class | `ext/hermes-agent/tests/gateway/test_matrix.py` | 216 |
| `CookieImportError` | Class | `ext/skills/gstack/browse/src/cookie-import-browser.ts` | 82 |
| `is_approved` | Function | `ext/hermes-agent/gateway/pairing.py` | 113 |
| `list_approved` | Function | `ext/hermes-agent/gateway/pairing.py` | 118 |
| `revoke` | Function | `ext/hermes-agent/gateway/pairing.py` | 137 |
| `generate_code` | Function | `ext/hermes-agent/gateway/pairing.py` | 150 |
| `approve_code` | Function | `ext/hermes-agent/gateway/pairing.py` | 193 |
| `list_pending` | Function | `ext/hermes-agent/gateway/pairing.py` | 219 |
| `clear_pending` | Function | `ext/hermes-agent/gateway/pairing.py` | 237 |
| `test_stores_pending_entry` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 71 |
| `test_rate_limit_expires` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 104 |
| `test_approve_valid_code` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 155 |
| `test_approved_user_is_approved` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 167 |
| `test_approve_removes_from_pending` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 179 |
| `test_approve_case_insensitive` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 187 |
| `test_approve_strips_whitespace` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 196 |
| `test_lockout_after_max_failures` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 218 |
| `test_lockout_expires` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 240 |
| `test_expired_codes_cleaned_up` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 261 |
| `test_expired_code_cannot_be_approved` | Function | `ext/hermes-agent/tests/gateway/test_pairing.py` | 275 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Get_or_create_session → Fileno` | cross_community | 8 |
| `Get_or_create_session → _read_file` | cross_community | 8 |
| `Get_or_create_session → _set_entries` | cross_community | 8 |
| `Get_or_create_session → _scan_memory_content` | cross_community | 8 |
| `Get_or_create_session → Get_hermes_home` | cross_community | 7 |
| `Get_or_create_session → Add` | cross_community | 6 |
| `Connect → _get_lock_dir` | cross_community | 5 |
| `Connect → _scope_hash` | cross_community | 5 |
| `Connect → _get_process_start_time` | cross_community | 5 |
| `Get_running_pid → Fileno` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Platforms | 133 calls |
| Tools | 85 calls |
| Tests | 45 calls |
| Hermes_cli | 38 calls |
| Cli | 22 calls |
| Integration | 22 calls |
| Run_agent | 12 calls |
| Honcho_plugin | 10 calls |

## How to Explore

1. `gitnexus_context({name: "is_approved"})` — see callers and callees
2. `gitnexus_query({query: "gateway"})` — find related execution flows
3. Read key files listed above for implementation details
