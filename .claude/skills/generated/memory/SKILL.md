---
name: memory
description: "Skill for the Memory area of swarm-bot. 118 symbols across 29 files."
---

# Memory

118 symbols | 29 files | Cohesion: 83%

## When to Use

- Working with code in `core/`
- Understanding how test_session_summary_upsert, test_get_session_observations, synthesize_session work
- Modifying memory-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `core/memory/user_profile.py` | add_known_fact, add_pattern, get_user_profile, __init__, _init_supabase (+8) |
| `core/memory/temporal_graph.py` | _get_conn, _init_db, _seed_user, _ensure_entity, _add_fact_inner (+6) |
| `core/memory/episodic_store.py` | build_context_block, auto_extract_and_store, _fmt_ts, __init__, _init_supabase (+5) |
| `core/memory/tiers.py` | all, total_count, _save, set, delete (+3) |
| `core/memory/observation_queue.py` | enqueue, get_observation_queue, start, stop, _drain_loop (+2) |
| `core/memory/semantic_cache.py` | _load_model, _embed, _cosine_similarity, _evict_oldest, get (+2) |
| `core/memory/session_summary_synthesizer.py` | synthesize_session, _build_digest, _llm_synthesize, _parse_synthesis_response, _raw_digest_summary (+1) |
| `core/memory/observation_capture.py` | _extract_files_from_tool, _classify_from_context, capture_tool_use, capture_command, capture_decision (+1) |
| `core/memory/memory_manager.py` | get_memory_stats, save, auto_extract_and_save, search, progressive_search (+1) |
| `core/memory/consolidator.py` | promote_important, _tokenise, _tfidf_vector, _cosine, deduplicate (+1) |

## Entry Points

Start here when exploring this area:

- **`test_session_summary_upsert`** (Function) — `tests/test_observation_store.py:137`
- **`test_get_session_observations`** (Function) — `tests/test_observation_store.py:161`
- **`synthesize_session`** (Function) — `core/memory/session_summary_synthesizer.py:33`
- **`get_session_summary`** (Function) — `core/memory/observation_store.py:440`
- **`get_session_observations`** (Function) — `core/memory/observation_store.py:462`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `UserProfileStore` | Class | `core/memory/user_profile.py` | 81 |
| `UserProfile` | Class | `core/memory/user_profile.py` | 220 |
| `test_session_summary_upsert` | Function | `tests/test_observation_store.py` | 137 |
| `test_get_session_observations` | Function | `tests/test_observation_store.py` | 161 |
| `synthesize_session` | Function | `core/memory/session_summary_synthesizer.py` | 33 |
| `get_session_summary` | Function | `core/memory/observation_store.py` | 440 |
| `get_session_observations` | Function | `core/memory/observation_store.py` | 462 |
| `enqueue` | Function | `core/memory/observation_queue.py` | 84 |
| `get_observation_queue` | Function | `core/memory/observation_queue.py` | 179 |
| `capture_tool_use` | Function | `core/memory/observation_capture.py` | 130 |
| `capture_command` | Function | `core/memory/observation_capture.py` | 184 |
| `capture_decision` | Function | `core/memory/observation_capture.py` | 204 |
| `test_stats` | Function | `tests/test_observation_store.py` | 171 |
| `init_humanization_layer` | Function | `llm_client/__init__.py` | 211 |
| `cmd_memory_stats` | Function | `handlers/memory_commands.py` | 16 |
| `all` | Function | `core/memory/tiers.py` | 63 |
| `total_count` | Function | `core/memory/tiers.py` | 216 |
| `get_stats` | Function | `core/memory/observation_store.py` | 494 |
| `get_memory_stats` | Function | `core/memory/memory_manager.py` | 192 |
| `promote_important` | Function | `core/memory/consolidator.py` | 224 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Synthesize_session → UpdateSendButton` | cross_community | 6 |
| `On_startup → Total_count` | cross_community | 5 |
| `On_startup → Get_observation_store` | cross_community | 5 |
| `On_startup → All` | cross_community | 5 |
| `On_startup → Init_humanization_layer` | cross_community | 4 |
| `Get_layer_content → Get_user_profile` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tools | 9 calls |
| Handlers | 3 calls |
| Llm_client | 3 calls |
| Tests | 2 calls |
| Proactive | 2 calls |
| Cluster_359 | 1 calls |
| Reflection | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_session_summary_upsert"})` — see callers and callees
2. `gitnexus_query({query: "memory"})` — find related execution flows
3. Read key files listed above for implementation details
