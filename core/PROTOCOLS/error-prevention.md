# Error Accumulation Prevention — Drift Detection

Today's LLM failures in long agentic runs are NOT intelligence failures — they are ERROR ACCUMULATION.

## Drift Checkpoint — Run Every 5 Tool Calls

1. **ORIGINAL GOAL**: [restate exactly]
2. **CURRENT STATE**: [what is actually true]
3. **DELTA CHECK**: [is current state moving toward original goal?]

## Red Flags That Trigger ABORT

- ✗ Work no longer connects to original task
- ✗ "Temporary fix" has become the permanent approach
- ✗ Scope has silently expanded beyond original request
- ✗ An assumption made early has been invalidated by new information
- ✗ The solution is more complex than the problem requires

## Usage

```python
from core.drift_detector import DriftDetector

detector = DriftDetector()
detector.set_goal("Add /budget command to show API spend")
detector.add_state("Modified handlers/admin.py — added BudgetHandler")
detector.increment_tool_calls()  # call after each tool
report = detector.check_drift()
if detector.should_abort():
    detector.raise_abort()  # raises DriftAbortError
```

## Verbatim Log Protocol

**NEVER paraphrase error messages, stack traces, test failures, or logs.**

- ✅ DO: Paste exact error text in full.
- ❌ NEVER: "There was an error about X" — paste the exact error.

**NEVER truncate stack traces.** The 17th line of the trace is the diagnostic signal.
**NEVER say "the output was something like"** — paste the actual output.

This matters because: subtle clues in exact error text are diagnostic signals that point to root cause. Paraphrasing kills the signal.

## Self-Evolution Feedback Pipeline

After every failed attempt — record it. After 5+ failures — build regression tests.

### Recording Failures

```python
from core.self_evolution import get_self_evolution_engine

engine = get_self_evolution_engine("/home/newadmin/swarm-bot")
await engine.record_failure(
    task="Adding /budget command",
    approach="Used sync sqlite3 in async handler",
    failure_mode="SQLite busy error under concurrent requests",
    root_cause="sync sqlite3 in async context blocks event loop",
    fix="Switched to aiosqlite with connection pool",
    prevention="Never use sync DB in async handlers",
)
```

After 5+ failures in FAILURES.md:
```python
count = await engine.build_eval_set_from_failures()
# Returns number of test cases added to EVAL_SET.md
```

### Getting Adversarial Challenges

```python
challenges = engine.get_adversarial_challenges("Add /budget command")
# Returns list of Critic-style questions from past failure history
```

### Recording Decisions

```python
await engine.record_decision(
    title="Use aiosqlite over sync sqlite3 for async handlers",
    context="BudgetHandler runs in async context, concurrent requests cause SQLite busy errors",
    decision="Replace all sync sqlite3 calls with aiosqlite + connection pool",
    rationale="aiosqlite is already in requirements.txt, provides async-native DB access",
    alternatives=["Use Redis for volatile data", "Use JSON file with file locking"],
    consequences={"more dependencies": "aiosqlite already present, no new dep added"},
)
```

## Dynamic Tool Search Protocol

When stuck or needing a capability not obvious from context — search before assuming.

**SEARCH ORDER:**
1. `~/.claude/skills/` — what skills are installed and what do they cover?
2. `which <tool>` — verify CLI tools are available
3. `cat requirements.txt / pip list` — verify Python packages
4. `grep -r "something" . --include="*.py"` — search codebase for similar patterns

**PROPOSE RATHER THAN ASSUME:**
- Never say "X is not available." Instead: "I need X — install Y or use Z alternative?"
- Never install a package without stating why it solves the problem.
- Never assume a CLI tool isn't there without running `which`.

## Ambiguity Threshold Rule

**STOP AND ASK** when one of these is true:
- Task could be interpreted 2+ fundamentally different ways
- Correct answer depends on a business decision not stated
- Proceeding requires assumptions about auth/data/infra not visible in context
- Task implies modifying something that could break production
- Scope is completely unclear

**HOW TO CLARIFY:**
> "Option A: [interpretation] — means [consequence] / Option B: [interpretation] — means [consequence] / Which, or a third option?"

This is not weakness. Clarifying before implementing is faster than rolling back.

## Loop-Aligned Reasoning Template

For multi-file refactors — reason per component, track state explicitly.

**PER-FILE EXECUTION TEMPLATE:**
```
FOR each component:
  STATE: current behavior → TARGET: desired behavior → DELTA: changes → RISKS → VERIFY
```

**EXPLICIT STATE TRACKING:**
> "After modifying file A: [what is now true about the system]. This means file B must now [change]. After modifying file B: [new system state]. Verify with [test/assertion]."

If you can't state what changed and why in 2 sentences — the change is too complex. Break it up.