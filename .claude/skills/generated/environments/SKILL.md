---
name: environments
description: "Skill for the Environments area of swarm-bot. 145 symbols across 23 files."
---

# Environments

"145 symbols | 23 files | Cohesion: 71%"

## When to Use

- Working with code in `ext/`
- Understanding how build_budget_config, collect_trajectory, cleanup work
- Modifying environments-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ext/hermes-agent/tools/environments/vercel_sandbox.py` | _snapshot_store_path, _load_snapshots, _save_snapshots, _get_snapshot_id, _store_snapshot (+22) |
| `ext/hermes-agent/tools/environments/base.py` | get_sandbox_dir, _pipe_stdin, _popen_bash, _load_json_store, _save_json_store (+12) |
| `ext/hermes-agent/tools/environments/modal.py` | _load_snapshots, _save_snapshots, _direct_snapshot_key, _get_snapshot_restore_candidate, _store_direct_snapshot (+7) |
| `ext/hermes-agent/tools/environments/singularity.py` | _find_singularity_executable, _ensure_singularity_available, _get_scratch_dir, _get_apptainer_cache_dir, _get_or_build_sif (+5) |
| `ext/hermes-agent/tools/environments/file_sync.py` | quoted_rm_command, iter_sync_files, _sha256_file, sync, _sync_back_once (+4) |
| `ext/hermes-agent/tools/environments/local.py` | _read_terminal_shell_init_config, _resolve_shell_init_files, _prepend_shell_init, _run_bash, _update_cwd (+2) |
| `ext/hermes-agent/environments/hermes_base_env.py` | build_budget_config, _resolve_tools_for_group, _use_managed_server, collect_trajectory, HermesAgentEnvConfig (+1) |
| `ext/hermes-agent/environments/tool_context.py` | cleanup, _run_tool_in_thread, terminal, upload_file, upload_dir (+1) |
| `ext/hermes-agent/environments/agentic_opd_env.py` | evaluate, compute_reward, collect_trajectories, _apply_opd_pipeline, _opd_for_sequence (+1) |
| `ext/hermes-agent/environments/web_research_env.py` | evaluate, compute_reward, _llm_judge, _parse_judge_json, _heuristic_score (+1) |

## Entry Points

Start here when exploring this area:

- **`build_budget_config`** (Function) — `ext/hermes-agent/environments/hermes_base_env.py:209`
- **`collect_trajectory`** (Function) — `ext/hermes-agent/environments/hermes_base_env.py:488`
- **`cleanup`** (Function) — `ext/hermes-agent/environments/tool_context.py:438`
- **`evaluate`** (Function) — `ext/hermes-agent/environments/agentic_opd_env.py:1007`
- **`evaluate`** (Function) — `ext/hermes-agent/environments/web_research_env.py:426`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `HermesAgentEnvConfig` | Class | `ext/hermes-agent/environments/hermes_base_env.py` | 77 |
| `TerminalBench2EvalConfig` | Class | `ext/hermes-agent/environments/benchmarks/terminalbench_2/terminalbench2_env.py` | 75 |
| `HermesAgentBaseEnv` | Class | `ext/hermes-agent/environments/hermes_base_env.py` | 220 |
| `TerminalBench2EvalEnv` | Class | `ext/hermes-agent/environments/benchmarks/terminalbench_2/terminalbench2_env.py` | 220 |
| `BaseEnvironment` | Class | `ext/hermes-agent/tools/environments/base.py` | 266 |
| `BaseModalExecutionEnvironment` | Class | `ext/hermes-agent/tools/environments/modal_utils.py` | 57 |
| `build_budget_config` | Function | `ext/hermes-agent/environments/hermes_base_env.py` | 209 |
| `collect_trajectory` | Function | `ext/hermes-agent/environments/hermes_base_env.py` | 488 |
| `cleanup` | Function | `ext/hermes-agent/environments/tool_context.py` | 438 |
| `evaluate` | Function | `ext/hermes-agent/environments/agentic_opd_env.py` | 1007 |
| `evaluate` | Function | `ext/hermes-agent/environments/web_research_env.py` | 426 |
| `kill_all` | Function | `ext/hermes-agent/tools/process_registry.py` | 1186 |
| `rollout_and_score_eval` | Function | `ext/hermes-agent/environments/benchmarks/terminalbench_2/terminalbench2_env.py` | 466 |
| `run_coroutine` | Function | `ext/hermes-agent/tools/environments/modal.py` | 133 |
| `stop` | Function | `ext/hermes-agent/tools/environments/modal.py` | 139 |
| `cleanup` | Function | `ext/hermes-agent/tools/environments/modal.py` | 423 |
| `get_sandbox_dir` | Function | `ext/hermes-agent/tools/environments/base.py` | 80 |
| `quoted_rm_command` | Function | `ext/hermes-agent/tools/environments/file_sync.py` | 77 |
| `exec_fn` | Function | `ext/hermes-agent/tools/environments/vercel_sandbox.py` | 604 |
| `terminal` | Function | `ext/hermes-agent/environments/tool_context.py` | 81 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run → Items` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Platforms | 24 calls |
| Tools | 22 calls |
| Hermes_cli | 7 calls |
| Cli | 4 calls |
| Hermes-agent | 2 calls |
| Integration | 2 calls |
| Run_agent | 2 calls |
| Honcho_plugin | 2 calls |

## How to Explore

1. `gitnexus_context({name: "build_budget_config"})` — see callers and callees
2. `gitnexus_query({query: "environments"})` — find related execution flows
3. Read key files listed above for implementation details
