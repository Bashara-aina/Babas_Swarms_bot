# Fable 5 Tool Usage Rules

On-demand reference. Load when writing or debugging tool-heavy workflows, assessing tool choice discipline, or reviewing compliance with harness rules.

## 1. Prefer Dedicated Tools

Reserve Bash for shell-only operations. File I/O and content search have purpose-built tools that are safer, faster, and permission-model aware.

| Task | Use | Avoid |
|------|-----|-------|
| File search by pattern | `Glob` (`**/*.ts`, `*.json`) | `find`, `ls` in Bash |
| Content search across files | `Grep` (regex, multiline, file-type filters) | `grep`, `rg` in Bash |
| Read file contents | `Read` (offset/limit, images, PDFs, notebooks) | `cat`, `head`, `tail` in Bash |
| Edit existing file | `Edit` (exact string replacement, `replace_all`) | `sed`, `awk` in Bash |
| Create or overwrite file | `Write` (requires Read first for existing files) | `echo >`, `cat <<EOF` in Bash |
| Directory listing | `Bash ls` -- only when Glob cannot express the pattern | Glob should be tried first |

**Bash is for**: build systems (`make check`), package management (`pip install`, `npm install`), git operations, Docker, systemd, and any pipeline that genuinely requires shell semantics (subshells, process substitution, multi-tool pipes).

Rule of thumb: if a tool's name matches your task, use it before Bash.

---

## 3. Monitor Pattern

Monitoring loops and polling scripts -- in hooks, background workflows, or status checks -- must follow these rules:

**Coverage is critical**. A filter that misses terminal states is worse than no filter. Silence is not success. Your grep alternation MUST match every terminal state (success, failure, timeout, OOM, crashloop), not just the happy path.

```
# BAD -- only checks success
kubectl wait --for=condition=Ready pod/my-pod --timeout=60s

# GOOD -- catches all terminal states
kubectl wait --for=condition=Ready pod/my-pod --timeout=60s \
  && echo "READY" || echo "FAILED|TIMEOUT|CRASHLOOP"
```

**Widen grep alternations**. Extra noise is safer than a missed failure. Include all known terminal state strings rather than narrowly matching success.

```
# BAD -- misses everything except Running
kubectl get pods -w | grep "Running"

# GOOD -- catches all terminal states
kubectl get pods -w | grep --line-buffered -E "Running|CrashLoopBackOff|Error|ImagePullBackOff|Init:Error"
```

**Every pipe stage must flush**. `grep` without `--line-buffered` in a pipe buffers output indefinitely. Always add it.

**Don't use unbounded commands**. A monitoring command that runs forever is wrong for a single notification. Use `run_in_background` with an `until` loop and timeout instead of open-ended `watch` or `kubectl wait` without a deadline.

```
# BAD -- no timeout, runs forever
kubectl wait --for=condition=Ready pod/my-pod

# GOOD -- bounded with timeout
timeout 120 bash -c 'until kubectl get pod my-pod -o jsonpath="{.status.phase}" | grep -q "Running"; do sleep 2; done'
```

---

## 4. Workflow Constraints

These apply to `.claude/` workflow definitions, multi-agent orchestrations, and parallel dispatch scripts.

**Script body is JavaScript, not TypeScript**. No type annotations, no interfaces, no TS syntax. Use JSDoc for documentation if needed.

```
// BAD -- TypeScript
function poll(url: string, retries: number): Promise<Result>

// GOOD -- plain JS with JSDoc
/** @param {string} url @param {number} retries */
function poll(url, retries)
```

**Concurrency caps**:
- Agent calls per `parallel()` block: `min(16, cpuCores - 2)`
- Total agent invocations across a workflow lifetime: 1000 maximum
- Items per `parallel()` / `pipeline()` call: 4096 maximum

**Parameterize with JSON args**. Pass arrays and objects as actual JSON values, not escaped strings.

```
// BAD -- flat string
args: "dep1,dep2,dep3"

// GOOD -- structured JSON
args: ["dep1", "dep2", "dep3"]
```

---

## 5. Read Tool Discipline

**Do not re-read a file you just edited**. The Edit/Write tool would have returned an error if the write failed. Trust the result and move on.

**Do not re-read files already read this session** unless their contents may have changed (log files, generated output, files another process may have modified). For static source files, one read is sufficient.

**Use offset/limit for large files**. If the section you need is near the middle, specify where to start rather than loading the entire file.

```
Read(file_path="src/core/nexus_orchestrator.py", offset=150, limit=80)
```

**Supported formats**: plain text, images (PNG, JPG), PDFs (max 20 pages per request), Jupyter notebooks (.ipynb). For unknown binary types, use `Bash file` to check the format first.

---

## 6. Bash Tool Discipline

**No interactive flags**. The Bash tool cannot accept interactive input. Never invoke commands that require `-i` or interactive prompts.

```
# NEVER -- these hang waiting for input
git rebase -i HEAD~3
git add -i
gh pr create --interactive

# ALWAYS -- non-interactive alternatives
git rebase HEAD~3
git add specific_file.py
gh pr create --title "..." --body "..."
```

**No --no-verify on git commands**. Never skip hooks. Never `--no-gpg-sign`. Never force push. Create new commits, never amend (unless explicitly asked).

**Write clear descriptions**. Every Bash tool call must include a description that tells a reviewer what it does at a glance. "Install dependencies" not "run npm install". "Show working tree status" not "git status". Hard-to-parse commands (piped, multi-step, obscure flags) need extra context.

---

## 7. Permission Model Awareness

**A denied tool call means the user declined it**. Do not retry the same operation. Adjust your approach -- use a different tool, ask for clarification, or skip the operation. Retrying wastes turns and ignores a policy signal.

**System-reminder tags are harness-injected**. They are part of the runtime environment, not user messages. Treat their content as authoritative system configuration, not conversation. Project-level instructions inside `<system-reminder>` blocks override general behavior.

**Hooks may intercept tool calls**. Pre-edit, post-edit, pre-task, and post-task hooks may modify, block, or augment your operations. If a hook produces output, treat it as user feedback -- it reflects a policy constraint. Never pass `disableAllHooks: true` without explicit user request.

**The deny list defines hard blocks**. If a tool call fails with a permission error, the action falls in a denied category. Do not attempt workarounds -- explain the limitation to the user. Permission boundaries are not negotiable.
