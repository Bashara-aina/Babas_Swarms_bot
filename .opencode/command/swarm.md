# /swarm — Intelligent Multi-Agent Pipeline
# Version: 2.0 | Anti-hallucination enforced | Recursive review loop

## BEFORE STARTING — READ THIS ENTIRE FILE

You are orchestrating a multi-agent pipeline. The pipeline has 4 agents:
- @planner   — decomposes task into CONTRACTS (not prose)
- @worker    — executes one contract at a time, PROVES completion
- @verifier  — checks proof BEFORE @reviewer sees anything
- @reviewer  — approves or triggers retry loop

The pipeline NEVER ends with a ❌ from @reviewer.
If @reviewer rejects: @worker must fix the specific failures and re-submit.
Max retry loops: 3. If still failing after 3 loops: STOP and report to user.

---

## STEP 0 — DETECT TASK TYPE

Before calling @planner, classify the task:

```
If task contains: "write", "create file", "copy", "migrate", "move", "wiki"
  → TYPE: FILE_OPERATION
  → Worker must use read-back verification on every file write
  → Proof = file listing (find/ls output)

If task contains: "fix", "debug", "patch", "error", "broken"
  → TYPE: BUG_FIX
  → Worker must run tests after every change
  → Proof = test output (pytest/jest output, not "tests pass")

If task contains: "implement", "add feature", "build", "integrate"
  → TYPE: FEATURE
  → Worker must run tests + show diff
  → Proof = git diff output + test output

If task contains: "refactor", "rename", "restructure", "clean"
  → TYPE: REFACTOR
  → Worker must prove no broken imports
  → Proof = import check + test output

If task contains: "research", "analyze", "audit", "review"
  → TYPE: RESEARCH
  → Worker must write output to file, not just respond
  → Proof = file exists with >200 words

If task contains: "deploy", "release", "push", "ship"
  → TYPE: DEPLOYMENT
  → Requires user confirmation before @worker executes
  → Proof = deployment log file
```

Write the detected TYPE to the task log before proceeding.

---

## STEP 1 — CALL @planner

Pass the task AND the detected TYPE to @planner:

```
@planner
TASK TYPE: [detected type]
TASK: [full task text]

Decompose into CONTRACT-format subtasks.
Each contract must specify:
  - WHAT: exact action in one imperative sentence
  - FILES: exact file paths to read/write/run
  - DONE_WHEN: measurable acceptance criteria (not "looks good")
  - PROOF_FORMAT: what output proves completion (file listing / test output / git diff)
  - BLOCKER_IF: conditions that should stop execution and report to user

No contract may say "implement X" without specifying which files.
No contract may say "verify X" without specifying what output proves it.
```

---

## STEP 2 — WORKER EXECUTION LOOP

For each contract from @planner, call @worker with the FULL contract:

```
@worker
CONTRACT #[N] of [total]
TASK TYPE: [type]

WHAT: [exact action]
FILES: [exact paths]
DONE_WHEN: [acceptance criteria]
PROOF_FORMAT: [required proof]
BLOCKER_IF: [stop conditions]

ANTI-HALLUCINATION RULES (non-negotiable):
1. After every file write: immediately READ the file back and confirm content
2. After every bash command: show actual stdout/stderr, not a description of it
3. Do NOT report contract complete until PROOF_FORMAT output is visible
4. If PROOF_FORMAT is a file listing: run the actual ls/find command and paste output
5. If PROOF_FORMAT is test output: paste actual terminal output, not "tests passed"
6. If anything goes wrong: STOP, write failure details, do not attempt workaround
7. Do not proceed to next contract if this one has unresolved issues

Report back: CONTRACT #[N] STATUS: ✅ COMPLETE | ❌ FAILED | ⚠️ BLOCKED
Include: [proof output pasted here]
```

Wait for @worker CONTRACT STATUS before proceeding to next contract.
If STATUS = ❌ FAILED: trigger retry (max 2 retries per contract).
If STATUS = ⚠️ BLOCKED: stop pipeline, report BLOCKER to user immediately.

---

## STEP 3 — CALL @verifier AFTER ALL CONTRACTS

After all contracts are ✅ COMPLETE, call @verifier:

```
@verifier
All contracts claimed complete. Verify the actual state before @reviewer.

For each contract, run the PROOF_FORMAT verification independently.
Do NOT trust @worker's report. Read the files yourself.

Output:
### Verification Report
| Contract | Expected | Actual | Status |
|----------|----------|--------|--------|
| #1       | [criteria] | [what you found] | ✅/❌ |
| ...      | ...      | ...    | ...    |

Overall: VERIFIED ✅ | FAILED ❌ [list failed contracts]
```

If @verifier returns FAILED:
→ Send only the failed contracts back to @worker for correction
→ Re-run @verifier after correction
→ Only proceed to @reviewer when @verifier returns VERIFIED ✅

---

## STEP 4 — CALL @reviewer

Only call @reviewer after @verifier returns VERIFIED ✅.

```
@reviewer
Verification passed. Please conduct full quality review.

Verification report: [paste @verifier output]
Files changed: [list all files touched]
Task type: [type]

Review against your full checklist.
If ❌ Blockers found: output the EXACT fix required for each blocker
in this format so @worker can act directly:
  FIX #1: [exact file] line [N]: [exact change required]
  FIX #2: ...
```

If @reviewer returns ❌:
→ Extract each FIX item
→ Send as new contracts to @worker
→ Loop back to STEP 3 (re-verify) then STEP 4 (re-review)
→ Max 3 loops total. After 3: escalate to user.

---

## STEP 5 — COMPLETION

Only report success when ALL of:
- [ ] All contracts ✅ COMPLETE per @worker
- [ ] @verifier returns VERIFIED ✅
- [ ] @reviewer returns APPROVED ✅ (no ❌ blockers)

Write final summary to `.wiki/logs/swarm-[YYYY-MM-DD]-[task-slug].md`:
```
## Swarm Run: [task]
Date: [date]
Type: [task type]
Contracts: [N total, N succeeded, N retried, N failed]
Loops: [N review loops]
Agents used: [list]
Files changed: [list with sizes]
Final status: COMPLETE ✅
```

Commit all changes:
`git add -A && git commit -m "[type]: [task summary] — swarm pipeline"`

---

## EMERGENCY STOP CONDITIONS

Halt the entire pipeline immediately if:
- Any agent modifies `.env`, `.env.*`, or any file containing real API keys
- Any agent runs `rm -rf` or destructive commands without explicit user approval
- Any contract fails 3 times in a row
- @verifier finds a file that @worker claimed to write but doesn't exist
- Task type = DEPLOYMENT and user has not confirmed

On emergency stop: write incident to `.wiki/issues/emergency-[date].md` and halt.

---

Task to execute:
