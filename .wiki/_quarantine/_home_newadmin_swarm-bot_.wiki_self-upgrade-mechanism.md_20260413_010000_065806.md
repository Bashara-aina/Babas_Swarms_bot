---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/self-upgrade-mechanism.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.065828"
}
---

---
title: self-upgrade-mechanism
domain: git-version-control
impact_score: 8
last_updated: 2026-04-12
injects_into: core/self_upgrade.py, handlers/github_intel_handler.py
tokens_estimated: 530
---

# Self-Upgrade Mechanism

## ONE-LINE SUMMARY
How Legion generates, validates, writes, hot-reloads, and rolls back code upgrades triggered from Telegram.

## PIPELINE OVERVIEW

```
User → /upgrade_from <repo_url>
  → GitHubIntelEngine.fetch_readme()
  → SelfUpgradeEngine.upgrade(request)
    → _plan_upgrade()       [LLM generates file plan as JSON]
    → _validate_code()      [ast.parse + pattern blocklist]
    → _rollback backup      [save existing files]
    → write files to disk
    → _install_deps()       [pip install --quiet with timeout]
    → _reload_or_restart()  [hot-reload or watchdog restart]
    → rollback on failure
  → Telegram notification
```

## STEPS

### Step 1: Plan Generation (`_plan_upgrade`)
```python
prompt = f"""...Upgrade request: {request}...
Generate implementation. Output ONLY valid JSON:
{
  "feature": "short feature name",
  "description": "what this adds",
  "deps": ["pandas"],
  "files": [{"path": "handlers/dashboard.py", "content": "# full Python..."}],
  "handler_registration": "from handlers import dashboard\nrouter.include_router(dashboard.router)"
}"""
response = await litellm.acompletion(model="groq/llama-3.3-70b-versatile", ...)
return self._parse_plan_json(raw)
```
- LLM generates a full implementation plan as JSON
- Model: `groq/llama-3.3-70b-versatile` with `temperature=0.1`, `max_tokens=8192`
- Prompt includes current project structure (walked from root, truncated at 80 lines)
- Output MUST be valid JSON — extracted via regex `\{.*\}`

### Step 2: Validation (`_validate_code`)
```python
ast.parse(code)                        # Syntax check
re.search(pattern, code)               # Blocklist check
"../" in path or path.startswith("/")  # Path safety
```
**Blocklist patterns (`_BLOCKED_PATTERNS`)**:
- `os.system(`, `subprocess.call(` — shell escape
- `__import__('os')` — arbitrary module import
- `rm -rf`, `shutil.rmtree(` — destructive file ops
- `open(...'w'...).*\.` — arbitrary file write
- `eval(`, `exec(` — code execution

**Path validation**: Blocks paths with `../` (path traversal) or leading `/` (absolute path).

### Step 3: Rollback Backup
```python
for file_plan in plan["files"]:
    path = self.root / file_plan["path"]
    if path.exists():
        result.rollback_files[file_plan["path"]] = path.read_text(encoding="utf-8")
```
- Stores original content of all files that will be overwritten
- Used for `_rollback()` if any step fails

### Step 4: File Write
```python
for file_plan in plan["files"]:
    path = self.root / file_plan["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(file_plan["content"], encoding="utf-8")
```
- Creates parent directories if needed
- Writes full file content
- Tracks written files in `result.files_written`

### Step 5: Dependency Installation (`_install_deps`)
```python
cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + safe_deps
proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
```
- Safe dep names validated with regex: `^[a-zA-Z0-9_\-\.\[\]>=<~!]+$`
- Runs in `asyncio.create_subprocess_exec` — async, non-blocking
- Timeout: 120 seconds
- Updates `requirements.txt` with new deps (deduplicated)
- **NOT sandboxed** — runs with full pip permissions on the system Python

### Step 6: Hot-Reload or Restart (`_reload_or_restart`)
```python
if module_name in sys.modules:
    importlib.reload(mod)          # hot-reload if already loaded
else:
    spec = importlib.util.spec_from_file_location(...)
    spec.loader.exec_module(mod)   # initial load if not loaded
```
- **Hot-reload**: `importlib.reload()` on existing modules — zero downtime
- **Restart**: If hot-reload fails for ANY file → writes `data/.restart_requested` flag → watchdog handler restarts bot
- Restart flag checked by external watchdog (not in this file)

### Step 7: Rollback on Failure
```python
async def _rollback(self, result: UpgradeResult) -> None:
    for rel_path, original_content in result.rollback_files.items():
        path.write_text(original_content, encoding="utf-8")  # restore original
    for written in result.files_written:
        if written not in result.rollback_files:
            path.unlink()  # delete newly created files
```
- Restores all original files from backup
- Deletes any newly created files that weren't overwrites
- Returns `UpgradeResult` with `success=False, error="..."`

## VERIFICATION

| Check | Mechanism | Pass condition |
|-------|-----------|----------------|
| Syntax | `ast.parse(code)` | No `SyntaxError` |
| Dangerous code | Blocklist regex | No pattern match |
| Path safety | `../` and `/` check | Both negative |
| Import success | `importlib.reload()` | No exception |
| Dep install | `pip install` return code | `returncode == 0` |

**Smoke test**: `github_intel.py:_sandbox_smoke_test` does a separate sandbox validation for skill discovery (install to `/tmp`, import test). This is NOT used for general self-upgrade.

**No diff verification** — generated code is not compared against original before overwrite.

**No rollback verification** — rollback execution is not tested before deployment.

## THREAD SAFETY

- `SelfUpgradeEngine` is NOT thread-safe
- Single upgrade runs to completion before next upgrade can start (no locking)
- Concurrent upgrades could overwrite each other's files
- `notify_cb` is fire-and-forget with try/except/pass

## WHAT TRIGGERS RESTART

A restart is requested (via `_request_restart`) when:
1. Hot-reload fails for ANY file in the upgrade plan
2. File is not a `.py` file (non-Python files skip hot-reload check)

Restart method: writes timestamp to `data/.restart_requested` — external watchdog reads this and restarts the process.

## SKIP CONDITIONS

Files are NOT hot-reload attempted for:
- Non-`.py` files (e.g., config files, markdown) — these skip reload check
- Modules that error during `spec.loader.exec_module()`

## GAPS

1. **No diff review** — generated code not compared to original before overwrite
2. **No rollback test** — rollback not verified before being needed
3. **Pip install unsandboxed** — `_install_deps` runs with full system pip permissions
4. **Concurrent upgrades** — no locking, could corrupt files
5. **No code review gate** — code written directly to disk, no human review step
6. **Dep name regex too permissive** — allows brackets and complex specs that could be unsafe
7. **No version pinning** — new deps not pinned to specific versions in requirements.txt
8. **No rollback on restart loop** — if restart loop occurs, no circuit breaker
9. **notify_cb exceptions silenced** — `try/except/pass` means upgrade author gets no feedback on notification failure
