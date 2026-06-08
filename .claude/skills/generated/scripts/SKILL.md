---
name: scripts
description: "Skill for the Scripts area of swarm-bot."
---

# Scripts

"scripts area"

## When to Use

- Working with code in `ext/`
- Understanding how sha256_file, read_text, ensure_parent work
- Modifying scripts-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | sha256_file, read_text, ensure_parent, resolve_secret_input, load_yaml_file (+68) |
| `ext/hermes-agent/optional-skills/productivity/telephony/scripts/telephony.py` | _twilio_owned_numbers, _twilio_list_owned, _twilio_call_status, _bland_status, _vapi_status (+32) |
| `ext/everything-claude-code/skills/continuous-learning-v2/scripts/instinct-cli.py` | _yaml_quote, detect_project, parse_instinct_file, _load_instincts_from_dir, load_all_instincts (+17) |
| `ext/hermes-agent/skills/productivity/google-workspace/scripts/google_api.py` | main, _gws_binary, gmail_send, gmail_modify, calendar_create (+17) |
| `ext/hermes-agent/optional-skills/blockchain/base/scripts/base_client.py` | rpc_batch, wei_to_eth, wei_to_gwei, hex_to_int, print_json (+16) |
| `ext/hermes-agent/skills/productivity/maps/scripts/maps_client.py` | main, print_json, haversine_m, nominatim_search, geocode_single (+14) |
| `ext/hermes-agent/optional-skills/productivity/memento-flashcards/scripts/memento_cards.py` | _now, _iso, _parse_iso, _load, _save (+12) |
| `ext/hermes-agent/skills/creative/comfyui/scripts/_common.py` | is_link, iter_nodes, iter_model_deps, iter_embedding_refs, resolve_api_key (+12) |
| `ext/skills/ui-styling/scripts/tailwind_config_gen.py` | add_colors, add_fonts, add_spacing, add_breakpoints, add_plugins (+11) |
| `ext/hermes-agent/optional-skills/creative/meme-generation/scripts/generate_meme.py` | load_curated_templates, fetch_imgflip_templates, _slugify, resolve_template, get_template_image (+11) |

## Entry Points

Start here when exploring this area:

- **`sha256_file`** (Function) — `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py:305`
- **`read_text`** (Function) — `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py:313`
- **`ensure_parent`** (Function) — `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py:321`
- **`resolve_secret_input`** (Function) — `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py:325`
- **`load_yaml_file`** (Function) — `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py:348`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `sha256_file` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 305 |
| `read_text` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 313 |
| `ensure_parent` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 321 |
| `resolve_secret_input` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 325 |
| `load_yaml_file` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 348 |
| `dump_yaml_file` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 355 |
| `parse_env_file` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 365 |
| `save_env_file` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 378 |
| `backup_existing` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 384 |
| `record` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 809 |
| `migrate` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 887 |
| `run_if_selected` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 961 |
| `maybe_backup` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 1093 |
| `copy_file` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 1107 |
| `migrate_command_allowlist` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 1199 |
| `load_openclaw_config` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 1258 |
| `load_openclaw_env` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 1270 |
| `merge_env_values` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 1274 |
| `migrate_messaging_settings` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 1320 |
| `handle_secret_settings` | Function | `ext/hermes-agent/optional-skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py` | 1360 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `POST → _patch_litellm_for_minimax` | cross_community | 9 |
| `POST → _patch_litellm_for_minimax` | cross_community | 9 |
| `_ → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `GET → _patch_litellm_for_minimax` | cross_community | 9 |
| `Run → _patch_litellm_for_minimax` | cross_community | 9 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 74 calls |
| Gateway | 12 calls |
| Hermes_cli | 11 calls |
| Handlers | 7 calls |
| Platforms | 6 calls |
| Run_agent | 4 calls |
| Server | 3 calls |
| Stress | 3 calls |

## How to Explore

1. `gitnexus_context({name: "sha256_file"})` — see callers and callees
2. `gitnexus_query({query: "scripts"})` — find related execution flows
3. Read key files listed above for implementation details
