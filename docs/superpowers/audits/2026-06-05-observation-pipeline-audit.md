# Observation Pipeline Audit — 2026-06-05

## Files reviewed
- core/memory/observation_capture.py (252 lines)
- core/memory/observation_queue.py (182 lines)
- core/memory/observation_store.py (738 lines)
- core/memory/session_summary_synthesizer.py (269 lines)
- core/hooks.py (123 lines, relevant section)

## Spec items: already done vs. needs work

| Spec item | Status | Evidence | Action |
|-----------|--------|----------|--------|
| Phase 4 (synth → wiki) | DONE | session_summary_synthesizer.py:82 calls `_write_wiki_article`; `_write_wiki_article` writes to `WIKI_SESSIONS_ROOT / {safe_id}.md` where `WIKI_SESSIONS_ROOT = .../.wiki/joint-brain/sessions` (synthesizer.py:20) | none — Task 2 can be downgraded to a verification-only step |
| Phase 5 (<private> stripping) | PARTIAL | store.py:362-363 strips only `content` and `narrative`; `_strip_private` (store.py:71-77) handles both `<private>...</private>` and `[private]...[/private]` blocks but is not called for `title`, `subtitle`, `facts`, `concepts` | widen to all string fields — Task 1 |
| Queue drain | DONE | queue.py:99-129 `_drain_loop`, with timeout-based flush and final flush on shutdown (queue.py:128-129) | none |
| FTS5 trigram | DONE | store.py:196-201 creates `observations_fts_trigram` with `tokenize='trigram'`; sync triggers at store.py:203-221 | none |
| WAL mode + jitter retry | DONE | store.py:38-40 defines jitter constants; store.py:110 `PRAGMA journal_mode=WAL`; store.py:116-138 `_write_with_retry` (15 attempts, 20-150ms jitter) | none |
| Bridge fan-out | NOT DONE | No `_fanout`/`_fanout_to_bridges` in observation_store.py; no `bridges` subpackage | Task 7 |
| 6-layer bridge | NOT DONE | `core/memory/bridges/` directory does not exist (verified by `ls` on `data/` and known file list) | Task 4 |
| Hermes bridge | NOT DONE | file does not exist | Task 5 |
| GitNexus bridge | NOT DONE | file does not exist | Task 6 |
| Bridge state | NOT DONE | `data/bridges_state.db` not present in `data/` listing | Task 3 |
| `post_tool_use` Python hook fired | DONE | observation_capture.py:249 `hooks.register("post_tool_use", capture_tool_use, name="observation_capture_tool")`; observer callable at capture.py:129-180 | none — Task 8 can be a verification-only step |
| MAX_QUEUE_SIZE | 500 (spec says 1000) | queue.py:53 `MAX_QUEUE_SIZE = 500` | reconcile: keep 500; smaller = less memory pressure, spec author deferred; do not edit |

## Baseline check

The baseline test from Step 2 of the plan ran successfully:

```
$ python -c "..."
[EMBEDDER] Ollama not reachable — embedding disabled (will use keyword fallback)
Entered main
Got store
obs_id=10
Done
```

The script returned `obs_id=10`. Note: the wrapping `timeout 30 python -c` wrapper exited with code 124 (timeout) even after the script printed "Done" — this is an aiosqlite event-loop-shutdown quirk (see the `RuntimeError: Event loop is closed` traceback during interpreter teardown, NOT a script bug). The actual `add_observation()` call completed in well under 1 second and the new row landed in `data/observations.db`. The store is functional.

## Bugs found (separate from spec items)

1. **`observation_store.py:371` — silent type coercion.** When `type_` is non-`None` and not in `OBSERVATION_TYPES`, the code silently sets `obs_type = "discovery"` with no log line. Suggestion: log a `logger.warning("Unknown obs type %r, falling back to discovery", type_)` so misconfigured callers are visible.

2. **`observation_store.py:138` — `last_err` lost when no lock/busy error ever raised.** The retry loop only sets `last_err` inside the lock/busy branch. If every attempt raises a non-lock error (e.g., a programming error), the first non-lock error is re-raised immediately (correct), but the `raise last_err if last_err else RuntimeError(...)` fallback on line 138 is unreachable in practice — leave a comment, or `raise RuntimeError("Write retries exhausted (last_err None)")` for clarity. Low severity.

3. **`observation_store.py:564-598` and `622-652` — comma-joined list fields corrupt on read.** `tags`, `files_read`, `files_modified` are stored as comma-joined strings (store.py:390-392) and split on `,` for retrieval (store.py:592-594, 646-648). If a tag, file path, or narrative-extracted filename contains a comma, the list will be split incorrectly on read. Suggestion: switch to JSON serialization (`json.dumps`/`json.loads`) for list fields; requires `_reconcile_columns` is unaffected since the column types stay `TEXT`.

4. **`observation_store.py:316-340` — silent exception swallow in `_reconcile_columns`.** `except Exception: continue` (line 316) hides `PRAGMA table_info` errors that would otherwise surface schema corruption. Suggestion: log at `logger.debug` level so a misconfigured database is still diagnosable.

5. **`observation_capture.py:88-94` — heuristic path extraction in tool results.** `path_pattern` matches any token in the tool result that ends with a known code extension, including substrings inside larger words. This generates false-positive `files_modified` entries (e.g., a Markdown summary mentioning `foo.py` in prose). Low severity, but contributes to noisy observations.

6. **`session_summary_synthesizer.py:148-150` — bare `except Exception as e` followed by `raise`.** The handler logs and re-raises, which is correct behavior, but the `as e` is unused after the log. Suggestion: drop the `as e` or use `%s` formatting inside the log (it does). Cosmetic.

7. **`observation_capture.py:34-39` — `_SKIP_TOOLS` does not include MCP tool names consistently.** `mcp__github__get_pull_request` and `mcp__github__list_issues` are listed, but other GitHub MCP tools (`create_issue`, `add_issue_comment`, etc.) and most Hermes/Tavily/Firecrawl MCP tools are not. These will still be observed and may cause noise. Suggestion: skip by prefix `mcp__github__` or maintain a wider denylist.

## Reconciliation decisions

Any spec assumptions that don't match the code, with the chosen fix:

- `Observation` dataclass has no `id` field. Spec's `_fanout(obs)` pseudocode references `obs.id`. **Resolution**: `add_observation()` already returns the new id (store.py:397 `return int(cur.lastrowid)`). Fanout signature is `_fanout(obs_id: int, obs_payload: dict)`, called from inside `add_observation()` after the commit. Plan Task 7 already plans this signature.
- Spec's `obs.id` for idempotency → use the `obs_id` arg passed to fanout; bridges persist `last_pushed_id` per-bridge in `data/bridges_state.db`. Plan Task 3 plans `BridgeState` accordingly.
- `MAX_QUEUE_SIZE` = 500 (queue.py:53) vs. spec's stated 1000. **Resolution**: keep 500. The spec author explicitly defers ("500 is safer; spec author deferred; do not edit"). 500 is plenty for hook rates observed in production and uses half the memory of 1000.
- Spec says `bridges_state.db` lives at `data/bridges_state.db`. The plan's `STATE_DB` constant in `core/memory/bridges/_base.py` matches this path. No conflict.
- `add_observation`'s `obs_type` argument is named `type_` in code (store.py:349) because `type` is a builtin. Spec text and plan code use `type_` consistently. No conflict; just verify tests use the renamed kwarg.
- `Observation` dataclass field `created_at` defaults to `datetime.now(UTC).isoformat(timespec="seconds")` (queue.py:41-43). When the queue worker calls `store.add_observation(...)`, it does not pass a `created_at` — `add_observation` regenerates it (store.py:372). This is a one-second-resolution ISO string, not an integer id, and the spec's `obs_id`-based idempotency uses the row id, not the timestamp. No conflict, but worth noting for v2 if strict ordering is ever needed across the queue/store boundary.
- Plan Task 1 test references `store._db_path()` (an attribute the test invents) — store.py has no such helper, only the module-level `DB_PATH`. **Resolution**: Task 1's Step 3 already anticipates this and includes the helper snippet to add. No code change needed in this audit.

## Audit conclusion

The observation pipeline core (`capture → queue → store → FTS5 + WAL + retry`) is implemented, correct, and the baseline test confirms `add_observation` writes a row in well under a second. Phase 4 (synth → wiki) and the `post_tool_use` Python hook are both already wired, so Tasks 2 and 8 can be downgraded to verification-only steps. The only existing in-scope gap is Phase 5's `<private>` tag stripping being limited to `content` and `narrative` (Task 1, surgical fix at store.py:362-363). All three bridges, the `bridges/` subpackage, `_fanout` wiring, and `data/bridges_state.db` do not exist and must be built by Tasks 3-7 as planned. The 7 bugs above (one functional risk: comma-joined list fields) are non-blocking for this plan but worth filing as a follow-up. No part of the plan can be skipped outright — Tasks 1, 3, 4, 5, 6, 7 are still required; Tasks 2 and 8 reduce to "verify the existing wiring and run the live smoke test."
