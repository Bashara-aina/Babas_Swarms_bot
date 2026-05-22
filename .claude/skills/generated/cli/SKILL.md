---
name: cli
description: "Skill for the Cli area of swarm-bot. 129 symbols across 44 files."
---

# Cli

"129 symbols | 44 files | Cohesion: 75%"

## When to Use

- Working with code in `ext/`
- Understanding how test_simple_history_shows_user_and_assistant, test_system_messages_hidden, test_tool_messages_hidden work
- Modifying cli-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/tests/cli/test_resume_display.py` | _make_cli, _simple_history, _tool_call_history, _capture_display, test_simple_history_shows_user_and_assistant (+27) |
| `ext/hermes-agent/tests/cli/test_worktree.py` | _setup_worktree, test_preserves_active_worktree_branch, _cleanup_worktree, test_clean_worktree_removed, test_dirty_worktree_cleaned_when_no_unpushed (+3) |
| `ext/hermes-agent/tests/cli/test_busy_input_mode_command.py` | _import_cli, _make_cli, test_no_args_shows_status, test_queue_argument_sets_queue_mode_and_saves, test_interrupt_argument_sets_interrupt_mode_and_saves (+2) |
| `ext/hermes-agent/tests/cli/test_worktree_security.py` | _force_remove_worktree, test_rejects_parent_directory_file_traversal, test_rejects_parent_directory_directory_traversal, test_rejects_symlink_that_resolves_outside_repo, test_allows_valid_file_include (+1) |
| `ext/hermes-agent/tests/cli/test_cli_skin_integration.py` | _make_cli_stub, test_default_prompt_fragments_use_default_symbol, test_ares_prompt_fragments_use_skin_symbol, test_secret_prompt_fragments_preserve_secret_state, test_build_tui_style_dict_uses_skin_overrides (+1) |
| `ext/hermes-agent/tests/cli/test_compress_focus.py` | _make_history, test_focus_topic_extracted_and_passed, test_no_focus_topic_when_bare_command, test_empty_focus_after_command_treated_as_none, test_focus_topic_printed_in_compression_banner (+1) |
| `ext/hermes-agent/tests/cli/test_fast_command.py` | _import_cli, _parse, test_no_args_shows_fast_when_enabled, _make_cli, test_no_args_shows_status (+1) |
| `ext/hermes-agent/tests/cli/test_manual_compress.py` | _make_history, test_manual_compress_reports_noop_without_success_banner, test_manual_compress_explains_when_token_estimate_rises, test_manual_compress_syncs_session_id_after_split, test_manual_compress_no_sync_when_session_id_unchanged |
| `ext/hermes-agent/tests/cli/test_quick_commands.py` | _printed_plain, _make_cli, test_exec_command_runs_and_prints_output, test_exec_command_uses_chat_console_when_tui_is_live, test_quick_command_takes_priority_over_skill_commands |
| `ext/hermes-agent/tests/cli/test_cli_background_tui_refresh.py` | _make_cli, test_invalidate_called_before_success_output, test_invalidate_called_before_error_output, test_no_crash_when_app_is_none |

## Entry Points

Start here when exploring this area:

- **`test_simple_history_shows_user_and_assistant`** (Function) — `ext/hermes-agent/tests/cli/test_resume_display.py:128`
- **`test_system_messages_hidden`** (Function) — `ext/hermes-agent/tests/cli/test_resume_display.py:139`
- **`test_tool_messages_hidden`** (Function) — `ext/hermes-agent/tests/cli/test_resume_display.py:146`
- **`test_tool_calls_shown_as_summary`** (Function) — `ext/hermes-agent/tests/cli/test_resume_display.py:155`
- **`test_long_user_message_truncated`** (Function) — `ext/hermes-agent/tests/cli/test_resume_display.py:164`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_simple_history_shows_user_and_assistant` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 128 |
| `test_system_messages_hidden` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 139 |
| `test_tool_messages_hidden` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 146 |
| `test_tool_calls_shown_as_summary` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 155 |
| `test_long_user_message_truncated` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 164 |
| `test_long_assistant_message_truncated` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 181 |
| `test_multiline_assistant_truncated` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 198 |
| `test_last_assistant_response_shown_in_full` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 217 |
| `test_last_assistant_multiline_shown_in_full` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 232 |
| `test_large_history_shows_truncation_indicator` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 247 |
| `test_multimodal_content_handled` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 257 |
| `test_empty_history_no_output` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 265 |
| `test_minimal_config_suppresses_display` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 272 |
| `test_panel_has_title` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 281 |
| `test_assistant_with_no_content_no_tools_skipped` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 288 |
| `test_only_system_messages_no_output` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 302 |
| `test_reasoning_scratchpad_stripped` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 311 |
| `test_pure_reasoning_message_skipped` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 330 |
| `test_think_tags_stripped` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 346 |
| `test_thinking_tags_stripped` | Function | `ext/hermes-agent/tests/cli/test_resume_display.py` | 363 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Hermes_cli | 3 calls |
| Tools | 3 calls |
| Gateway | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_simple_history_shows_user_and_assistant"})` — see callers and callees
2. `gitnexus_query({query: "cli"})` — find related execution flows
3. Read key files listed above for implementation details
